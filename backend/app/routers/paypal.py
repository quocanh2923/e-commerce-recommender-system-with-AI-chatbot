"""
app/routers/paypal.py
=====================
Tích hợp PayPal Checkout (Sandbox) với 2 endpoint:

  POST /paypal/create-order   → Tạo PayPal order, trả về paypal_order_id
  POST /paypal/capture-order  → Capture payment, tạo order trong DB

Flow:
  1. Frontend validate địa chỉ giao hàng
  2. Gọi POST /paypal/create-order  → nhận paypal_order_id
  3. PayPal JS SDK hiển thị popup, user approve
  4. Gọi POST /paypal/capture-order → backend capture PayPal → tạo đơn hàng DB
"""

import os
import httpx
from fastapi import APIRouter, HTTPException, Depends, Body, BackgroundTasks
from bson import ObjectId
from datetime import datetime, timezone
from app.core.config import db
from app.core.dependencies import get_current_user
from app.routers.notification import create_notification
from app.core.email import send_email, build_order_confirmation_email

router = APIRouter()

PAYPAL_BASE   = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
CLIENT_ID     = os.getenv("PAYPAL_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")

# USD rate (dùng để quy đổi VND → USD cho PayPal vì sandbox chỉ hỗ trợ USD)
VND_TO_USD = 25000


async def _get_access_token() -> str:
    """Lấy OAuth2 access token từ PayPal."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(CLIENT_ID, CLIENT_SECRET),
            headers={"Accept": "application/json"},
            timeout=15,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"PayPal auth failed: {resp.text}")
    return resp.json()["access_token"]


async def refund_paypal_capture(capture_id: str) -> dict:
    """
    Hoàn tiền toàn bộ một capture trên PayPal.
    Trả về dict response từ PayPal (chứa id, status, ...).
    """
    if not capture_id:
        raise HTTPException(status_code=400, detail="Thiếu paypal_capture_id")

    token = await _get_access_token()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v2/payments/captures/{capture_id}/refund",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"PayPal refund failed: {resp.text}")

    data = resp.json()
    if data.get("status") not in ("COMPLETED", "PENDING"):
        raise HTTPException(status_code=502, detail=f"PayPal refund status: {data.get('status')}")
    return data


# ─────────────────────────────────────────────────────────────
# 1. Tạo PayPal order
# ─────────────────────────────────────────────────────────────
@router.post("/create-order")
async def create_paypal_order(
    body: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Body: { shipping_address: { full_name, phone, address } }
    Returns: { paypal_order_id: str }
    """
    shipping_address = body.get("shipping_address")
    if not shipping_address:
        raise HTTPException(status_code=400, detail="Thiếu shipping_address")

    # Lấy giỏ hàng
    cart = await db.get_db()["carts"].find_one({"user_id": current_user["_id"]})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Giỏ hàng trống")

    items = cart["items"]

    # Kiểm tra stock
    for item in items:
        product = await db.get_db()["products"].find_one({"_id": ObjectId(item["product_id"])})
        if not product:
            raise HTTPException(status_code=404, detail=f"Sản phẩm '{item['name']}' không tồn tại")
        if product.get("stock", 0) < item["quantity"]:
            avail = product.get("stock", 0)
            raise HTTPException(
                status_code=400,
                detail=f"Sản phẩm '{item['name']}' chỉ còn {avail} sản phẩm",
            )

    subtotal = sum(i["price"] * i["quantity"] for i in items)
    shipping = 30000
    total_vnd = subtotal + shipping
    total_usd = round(total_vnd / VND_TO_USD, 2)

    # Tạo PayPal order
    token = await _get_access_token()
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "USD",
                    "value": str(total_usd),
                },
                "description": f"ShopAI Order — {len(items)} item(s)",
            }
        ],
        "application_context": {
            "brand_name": "ShopAI",
            "user_action": "PAY_NOW",
        },
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v2/checkout/orders",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"PayPal create order failed: {resp.text}")

    paypal_order = resp.json()
    return {
        "paypal_order_id": paypal_order["id"],
        "total_usd": total_usd,
        "total_vnd": total_vnd,
    }


# ─────────────────────────────────────────────────────────────
# 2. Capture PayPal order → tạo đơn hàng trong DB
# ─────────────────────────────────────────────────────────────
@router.post("/capture-order")
async def capture_paypal_order(
    background_tasks: BackgroundTasks,
    body: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Body: { paypal_order_id: str, shipping_address: { full_name, phone, address } }
    Returns: Order object (same as POST /orders/)
    """
    paypal_order_id  = body.get("paypal_order_id")
    shipping_address = body.get("shipping_address")
    if not paypal_order_id or not shipping_address:
        raise HTTPException(status_code=400, detail="Thiếu paypal_order_id hoặc shipping_address")

    # Capture payment
    token = await _get_access_token()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v2/checkout/orders/{paypal_order_id}/capture",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"PayPal capture failed: {resp.text}")

    capture_data = resp.json()
    capture_status = capture_data.get("status")
    if capture_status != "COMPLETED":
        raise HTTPException(status_code=400, detail=f"PayPal payment not completed: {capture_status}")

    # Lấy giỏ hàng lần 2 (đảm bảo vẫn còn)
    user_id = current_user["_id"]
    cart = await db.get_db()["carts"].find_one({"user_id": user_id})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Giỏ hàng đã trống")

    items = cart["items"]

    # Trừ stock
    for item in items:
        await db.get_db()["products"].update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$inc": {"stock": -item["quantity"]}},
        )

    subtotal = sum(i["price"] * i["quantity"] for i in items)
    shipping_fee = 30000
    total = subtotal + shipping_fee

    # Lấy capture ID từ PayPal response
    try:
        capture_id = (
            capture_data["purchase_units"][0]["payments"]["captures"][0]["id"]
        )
    except (KeyError, IndexError):
        capture_id = paypal_order_id

    order_dict = {
        "user_id": user_id,
        "items": items,
        "subtotal": subtotal,
        "shipping": shipping_fee,
        "total": total,
        "status": "pending",
        "shipping_address": shipping_address,
        "payment_method": "paypal",
        "paypal_order_id": paypal_order_id,
        "paypal_capture_id": capture_id,
        "created_at": datetime.now(timezone.utc),
    }

    result = await db.get_db()["orders"].insert_one(order_dict)

    # Xóa giỏ hàng
    await db.get_db()["carts"].update_one({"user_id": user_id}, {"$set": {"items": []}})

    # Ghi interaction "purchase"
    for item in items:
        await db.get_db()["interactions"].insert_one({
            "user_id": user_id,
            "product_id": item["product_id"],
            "action_type": "purchase",
            "timestamp": datetime.now(timezone.utc),
        })

    created = await db.get_db()["orders"].find_one({"_id": result.inserted_id})
    created["_id"] = str(created["_id"])

    order_code = created["_id"][-8:].upper()

    # Thông báo admin
    admins = await db.get_db()["users"].find({"role": "admin"}).to_list(None)
    for adm in admins:
        await create_notification(
            user_id=str(adm["_id"]),
            title="Don hang moi (PayPal)",
            message=f"Don hang #{order_code} da thanh toan qua PayPal - {total:,.0f}d",
            ntype="order",
            link="/admin/orders",
            target="admin",
        )

    # Thông báo user
    await create_notification(
        user_id=user_id,
        title="Payment Successful",
        message=f"Don hang #{order_code} da duoc thanh toan qua PayPal. Cam on ban!",
        ntype="order",
        link=f"/orders/{created['_id']}",
    )

    # Gửi email xác nhận
    user_email = current_user.get("email", "")
    if user_email:
        background_tasks.add_task(
            send_email,
            to=user_email,
            subject=f"Order Confirmed #{order_code} — ShopAI",
            html=build_order_confirmation_email(created, current_user.get("username", "")),
        )

    return created
