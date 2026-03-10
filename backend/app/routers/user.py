from fastapi import APIRouter, HTTPException, status, Body
from typing import List
from app.models.user import User, UserLogin
from app.core.config import db

router = APIRouter()


# 1. API Đăng ký người dùng mới
@router.post("/register", response_description="Đăng ký người dùng mới", response_model=User)
async def register_user(user: User = Body(...)):
    """
    Đăng ký tài khoản mới.
    Kiểm tra email và username không được trùng.
    """
    # Kiểm tra email đã tồn tại
    existing_email = await db.get_db()["users"].find_one({"email": user.email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được sử dụng"
        )
    
    # Kiểm tra username đã tồn tại
    existing_username = await db.get_db()["users"].find_one({"username": user.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username đã được sử dụng"
        )

    # Chuyển đổi dữ liệu từ dạng Model sang dict để lưu MongoDB
    user_dict = user.dict(by_alias=True)
    
    # Bỏ trường id đi để MongoDB tự tạo _id mới
    if "_id" in user_dict:
        del user_dict["_id"]

    # Lưu vào Collection tên là "users"
    new_user = await db.get_db()["users"].insert_one(user_dict)
    
    # Tìm lại người dùng vừa tạo để trả về
    created_user = await db.get_db()["users"].find_one({"_id": new_user.inserted_id})
    
    # Xóa password trước khi trả về cho an toàn
    del created_user["password"]
    return created_user


# 2. API Đăng nhập
@router.post("/login", response_description="Đăng nhập người dùng")
async def login_user(login_data: UserLogin = Body(...)):
    """
    Đăng nhập bằng email và password.
    """
    # Tìm user theo email và password
    user = await db.get_db()["users"].find_one({
        "email": login_data.email,
        "password": login_data.password
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai email hoặc mật khẩu"
        )
    
    # Xóa password trước khi trả về
    del user["password"]
    user["_id"] = str(user["_id"])
    return {
        "message": "Đăng nhập thành công",
        "user": user
    }
