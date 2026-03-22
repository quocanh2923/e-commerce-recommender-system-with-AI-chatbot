from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from bson.errors import InvalidId
from app.models.cart import Cart, CartItem
from app.core.config import db
from app.core.dependencies import get_current_user

router = APIRouter()


async def _get_or_create_cart(user_id: str) -> dict:
    cart = await db.get_db()["carts"].find_one({"user_id": user_id})
    if not cart:
        new = {"user_id": user_id, "items": []}
        result = await db.get_db()["carts"].insert_one(new)
        cart = await db.get_db()["carts"].find_one({"_id": result.inserted_id})
    cart["_id"] = str(cart["_id"])
    return cart


# 1. Lấy giỏ hàng
@router.get("/", response_model=Cart)
async def get_cart(current_user: dict = Depends(get_current_user)):
    return await _get_or_create_cart(current_user["_id"])


# 2. Thêm sản phẩm vào giỏ
@router.post("/items", response_model=Cart)
async def add_to_cart(item: CartItem, current_user: dict = Depends(get_current_user)):
    user_id = current_user["_id"]
    cart = await _get_or_create_cart(user_id)

    items = cart["items"]
    for existing in items:
        if existing["product_id"] == item.product_id:
            existing["quantity"] += item.quantity
            break
    else:
        items.append(item.dict())

    await db.get_db()["carts"].update_one(
        {"user_id": user_id}, {"$set": {"items": items}}
    )
    return await _get_or_create_cart(user_id)


# 3. Cập nhật số lượng 1 item
@router.put("/items/{product_id}", response_model=Cart)
async def update_cart_item(
    product_id: str,
    quantity: int,
    current_user: dict = Depends(get_current_user)
):
    if quantity < 1:
        raise HTTPException(status_code=400, detail="Số lượng phải >= 1")

    user_id = current_user["_id"]
    cart = await _get_or_create_cart(user_id)
    items = cart["items"]

    for item in items:
        if item["product_id"] == product_id:
            item["quantity"] = quantity
            break

    await db.get_db()["carts"].update_one(
        {"user_id": user_id}, {"$set": {"items": items}}
    )
    return await _get_or_create_cart(user_id)


# 4. Xoá 1 sản phẩm khỏi giỏ
@router.delete("/items/{product_id}", response_model=Cart)
async def remove_cart_item(product_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["_id"]
    cart = await _get_or_create_cart(user_id)
    items = [i for i in cart["items"] if i["product_id"] != product_id]

    await db.get_db()["carts"].update_one(
        {"user_id": user_id}, {"$set": {"items": items}}
    )
    return await _get_or_create_cart(user_id)


# 5. Xoá toàn bộ giỏ (sau khi checkout)
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(current_user: dict = Depends(get_current_user)):
    await db.get_db()["carts"].update_one(
        {"user_id": current_user["_id"]}, {"$set": {"items": []}}
    )
