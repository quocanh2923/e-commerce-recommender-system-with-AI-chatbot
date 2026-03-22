from fastapi import APIRouter, HTTPException, Body, Query, Depends
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import BaseModel, Field
from app.models.product import Product
from app.core.config import db
from app.core.dependencies import get_current_user, get_current_admin
from app.routers.notification import create_notification

router = APIRouter()

# 1. API Tạo sản phẩm mới
@router.post("/", response_description="Thêm sản phẩm mới", response_model=Product)
async def create_product(product: Product = Body(...)):
    # Chuyển đổi dữ liệu từ dạng Model sang dạng từ điển (dict) để lưu MongoDB
    product_dict = product.dict(by_alias=True)
    
    # Bỏ trường id đi để MongoDB tự tạo _id mới
    if "_id" in product_dict:
        del product_dict["_id"]

    # Lưu vào Collection tên là "products"
    new_product = await db.get_db()["products"].insert_one(product_dict)
    
    # Tìm lại sản phẩm vừa tạo để trả về cho người dùng xem
    created_product = await db.get_db()["products"].find_one({"_id": new_product.inserted_id})
    return created_product

# 2. API Lấy danh sách sản phẩm với filter/search/sort
@router.get("/", response_description="Lấy danh sách sản phẩm", response_model=List[Product])
async def list_products(
    search: Optional[str] = Query(None, description="Tìm theo tên sản phẩm"),
    category: Optional[str] = Query(None, description="Lọc theo danh mục"),
    min_price: Optional[float] = Query(None, ge=0, description="Giá tối thiểu"),
    max_price: Optional[float] = Query(None, ge=0, description="Giá tối đa"),
    sort_by: Optional[str] = Query("newest", description="newest | price_asc | price_desc | rating"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    query: dict = {}

    if search:
        query["name"] = {"$regex": search, "$options": "i"}

    if category:
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}

    if min_price is not None or max_price is not None:
        price_filter: dict = {}
        if min_price is not None:
            price_filter["$gte"] = min_price
        if max_price is not None:
            price_filter["$lte"] = max_price
        query["price"] = price_filter

    sort_map = {
        "newest": [("_id", -1)],
        "price_asc": [("price", 1)],
        "price_desc": [("price", -1)],
        "rating": [("rating", -1)],
    }
    sort_order = sort_map.get(sort_by, [("_id", -1)])

    products = (
        await db.get_db()["products"]
        .find(query)
        .sort(sort_order)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )
    return products


# 3. API Lấy chi tiết một sản phẩm theo id
@router.get("/{id}", response_description="Lấy chi tiết sản phẩm", response_model=Product)
async def get_product(id: str):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID format không hợp lệ")

    product = await db.get_db()["products"].find_one({"_id": obj_id})
    if product is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    return product


# 4. API Cập nhật sản phẩm
@router.put("/{id}", response_description="Cập nhật sản phẩm", response_model=Product)
async def update_product(id: str, product: Product = Body(...)):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID format không hợp lệ")

    update_data = {k: v for k, v in product.dict(by_alias=True).items() if v is not None}
    if "_id" in update_data:
        del update_data["_id"]

    if update_data:
        result = await db.get_db()["products"].update_one({"_id": obj_id}, {"$set": update_data})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm để cập nhật")
    # trả về bản ghi mới nhất
    updated = await db.get_db()["products"].find_one({"_id": obj_id})
    return updated


# 5. API Xóa sản phẩm
@router.delete("/{id}", response_description="Xóa sản phẩm")
async def delete_product(id: str):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID format không hợp lệ")

    result = await db.get_db()["products"].delete_one({"_id": obj_id})
    if result.deleted_count == 1:
        return {"message": "Xóa sản phẩm thành công"}
    else:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm để xóa")


# 6. API Đánh giá sản phẩm (chỉ người dùng đã mua & đơn delivered)
class RatingBody(BaseModel):
    rating: float = Field(..., ge=1, le=5)
    order_id: str
    feedback: Optional[str] = None


@router.post("/{id}/rate")
async def rate_product(id: str, body: RatingBody, current_user: dict = Depends(get_current_user)):
    try:
        product_oid = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID san pham khong hop le")

    try:
        order_oid = ObjectId(body.order_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID don hang khong hop le")

    db_ = db.get_db()

    # Kiểm tra đơn hàng thuộc user và đã giao
    order = await db_["orders"].find_one({
        "_id": order_oid,
        "user_id": current_user["_id"],
        "status": "delivered",
    })
    if not order:
        raise HTTPException(status_code=403, detail="Ban chi co the danh gia khi don hang da giao")

    # Kiểm tra sản phẩm có trong đơn hàng
    product_in_order = any(item["product_id"] == id for item in order.get("items", []))
    if not product_in_order:
        raise HTTPException(status_code=400, detail="San pham khong co trong don hang nay")

    # Kiểm tra đã đánh giá chưa
    existing = await db_["reviews"].find_one({
        "user_id": current_user["_id"],
        "product_id": id,
        "order_id": body.order_id,
    })
    if existing:
        raise HTTPException(status_code=400, detail="Ban da danh gia san pham nay trong don hang nay roi")

    # Lưu review
    review_doc = {
        "user_id": current_user["_id"],
        "product_id": id,
        "order_id": body.order_id,
        "rating": body.rating,
        "feedback": (body.feedback or "").strip() if body.feedback else "",
        "username": current_user.get("username", ""),
        "created_at": datetime.now(timezone.utc),
    }
    await db_["reviews"].insert_one(review_doc)

    # Tính lại rating trung bình cho sản phẩm
    pipeline = [
        {"$match": {"product_id": id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]
    result = await db_["reviews"].aggregate(pipeline).to_list(1)
    new_avg = round(result[0]["avg"], 1) if result else body.rating
    await db_["products"].update_one({"_id": product_oid}, {"$set": {"rating": new_avg}})

    return {"message": "Danh gia thanh cong", "new_rating": new_avg}


# 7b. Gửi 1 thông báo gộp cho admin sau khi user đánh giá batch
class ReviewNotifyBody(BaseModel):
    order_id: str
    count: int = Field(..., ge=1)

@router.post("/reviews/notify")
async def notify_admin_reviews(body: ReviewNotifyBody, current_user: dict = Depends(get_current_user)):
    db_ = db.get_db()
    username = current_user.get("username", "Nguoi dung")
    order_code = body.order_id[-8:].upper()
    admins = await db_["users"].find({"role": "admin"}).to_list(100)
    for adm in admins:
        await create_notification(
            user_id=str(adm["_id"]),
            title="Danh gia moi",
            message=f"{username} da danh gia {body.count} san pham trong don #{order_code}",
            ntype="review",
            link=f"/admin/orders?review={body.order_id}",
            target="admin",
        )
    return {"ok": True}


# 7. Lấy danh sách đánh giá của user cho 1 đơn hàng
@router.get("/reviews/{order_id}")
async def get_reviews_for_order(order_id: str, current_user: dict = Depends(get_current_user)):
    reviews = await db.get_db()["reviews"].find({
        "user_id": current_user["_id"],
        "order_id": order_id,
    }).to_list(100)
    # Trả về dict { product_id: { rating, feedback } }
    return {
        r["product_id"]: {
            "rating": r["rating"],
            "feedback": r.get("feedback", ""),
        }
        for r in reviews
    }