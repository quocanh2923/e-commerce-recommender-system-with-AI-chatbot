from fastapi import APIRouter, HTTPException, Body, Query
from typing import List, Optional
from bson import ObjectId
from bson.errors import InvalidId
from app.models.product import Product
from app.core.config import db

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