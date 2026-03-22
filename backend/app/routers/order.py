from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime, timezone
from bson import ObjectId
from app.models.order import Order, OrderItem
from app.core.config import db
from app.core.dependencies import get_current_user

router = APIRouter()


# 1. Tạo đơn hàng từ giỏ hàng hiện tại
@router.post("/", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(current_user: dict = Depends(get_current_user)):
    user_id = current_user["_id"]

    cart = await db.get_db()["carts"].find_one({"user_id": user_id})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Giỏ hàng trống")

    items = cart["items"]
    subtotal = sum(i["price"] * i["quantity"] for i in items)
    shipping = 30000
    total = subtotal + shipping

    order_dict = {
        "user_id": user_id,
        "items": items,
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total,
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
    }

    result = await db.get_db()["orders"].insert_one(order_dict)

    # Xoá giỏ sau khi đặt hàng
    await db.get_db()["carts"].update_one({"user_id": user_id}, {"$set": {"items": []}})

    # Ghi interaction "purchase" cho từng sản phẩm
    for item in items:
        await db.get_db()["interactions"].insert_one({
            "user_id": user_id,
            "product_id": item["product_id"],
            "action_type": "purchase",
            "timestamp": datetime.now(timezone.utc),
        })

    created = await db.get_db()["orders"].find_one({"_id": result.inserted_id})
    created["_id"] = str(created["_id"])
    return created


# 2. Lấy danh sách đơn hàng của user
@router.get("/", response_model=List[Order])
async def get_my_orders(current_user: dict = Depends(get_current_user)):
    orders = await db.get_db()["orders"].find(
        {"user_id": current_user["_id"]}
    ).sort("created_at", -1).to_list(100)
    for o in orders:
        o["_id"] = str(o["_id"])
    return orders


# 3. Lấy chi tiết 1 đơn hàng
@router.get("/{order_id}", response_model=Order)
async def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    try:
        order = await db.get_db()["orders"].find_one({
            "_id": ObjectId(order_id),
            "user_id": current_user["_id"]
        })
    except Exception:
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

    order["_id"] = str(order["_id"])
    return order
