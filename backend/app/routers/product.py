from fastapi import APIRouter, HTTPException, Body
from typing import List
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

# 2. API Lấy danh sách tất cả sản phẩm
@router.get("/", response_description="Lấy danh sách sản phẩm", response_model=List[Product])
async def list_products():
    products = await db.get_db()["products"].find().to_list(1000)
    return products