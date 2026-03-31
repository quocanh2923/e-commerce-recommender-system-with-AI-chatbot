from fastapi import APIRouter, HTTPException, status, Depends, Body
from typing import List
from datetime import datetime, timezone
from bson import ObjectId
from app.models.order import Order, OrderItem, OrderCreate
from app.core.config import db
from app.core.dependencies import get_current_user
from app.routers.notification import create_notification

router = APIRouter()


# 1. Tạo đơn hàng từ giỏ hàng hiện tại
@router.post("/", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreate = Body(...), current_user: dict = Depends(get_current_user)):
    user_id = current_user["_id"]

    cart = await db.get_db()["carts"].find_one({"user_id": user_id})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Giỏ hàng trống")

    items = cart["items"]

    # Kiểm tra và giữ stock (atomic)
    for item in items:
        product = await db.get_db()["products"].find_one({"_id": ObjectId(item["product_id"])})
        if not product:
            raise HTTPException(status_code=404, detail=f"Sản phẩm '{item['name']}' không tồn tại")
        if product.get("stock", 0) < item["quantity"]:
            avail = product.get("stock", 0)
            raise HTTPException(
                status_code=400,
                detail=f"Sản phẩm '{item['name']}' chỉ còn {avail} sản phẩm"
            )

    # Trừ stock
    for item in items:
        await db.get_db()["products"].update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$inc": {"stock": -item["quantity"]}}
        )

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
        "shipping_address": order_data.shipping_address.model_dump(),
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

    # Thong bao cho tat ca admin
    admins = await db.get_db()["users"].find({"role": "admin"}).to_list(None)
    order_code = created["_id"][-8:].upper()
    for adm in admins:
        await create_notification(
            user_id=str(adm["_id"]),
            title="Don hang moi",
            message=f"Don hang #{order_code} vua duoc dat - {total:,.0f}d",
            ntype="order",
            link=f"/admin/orders",
            target="admin",
        )

    # Thong bao cho user
    await create_notification(
        user_id=user_id,
        title="Dat hang thanh cong",
        message=f"Don hang #{order_code} da duoc tiep nhan. Chung toi se xu ly som nhat!",
        ntype="order",
        link=f"/orders/{created['_id']}",
    )

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


# 4. Huỷ đơn hàng (chỉ khi status là pending)
@router.delete("/{order_id}", status_code=200)
async def cancel_order(order_id: str, current_user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

    order = await db.get_db()["orders"].find_one({
        "_id": oid,
        "user_id": current_user["_id"]
    })
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

    if order["status"] != "pending":
        raise HTTPException(status_code=400, detail="Chỉ có thể huỷ đơn hàng đang chờ xác nhận")

    await db.get_db()["orders"].update_one(
        {"_id": oid},
        {"$set": {"status": "cancelled"}}
    )

    # Hoàn lại stock
    for item in order.get("items", []):
        await db.get_db()["products"].update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$inc": {"stock": item["quantity"]}}
        )

    # Thông báo cho admin
    order_code = order_id[-8:].upper()
    admins = await db.get_db()["users"].find({"role": "admin"}).to_list(None)
    for adm in admins:
        await create_notification(
            user_id=str(adm["_id"]),
            title="Đơn hàng bị huỷ",
            message=f"Đơn hàng #{order_code} đã bị khách huỷ",
            ntype="order",
            link="/admin/orders",
            target="admin",
        )

    return {"message": "Đã huỷ đơn hàng thành công"}
