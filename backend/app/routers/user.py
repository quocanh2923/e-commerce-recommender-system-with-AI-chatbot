from fastapi import APIRouter, HTTPException, status, Body, Depends
from app.models.user import UserRegister, UserLogin, UserResponse, TokenResponse, UserUpdate, PasswordChange
from app.core.config import db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from bson import ObjectId

router = APIRouter()


# 1. Đăng ký tài khoản mới
@router.post("/register", response_description="Đăng ký người dùng mới", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegister = Body(...)):
    # Kiểm tra email đã tồn tại
    if await db.get_db()["users"].find_one({"email": user.email}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã được sử dụng")

    # Kiểm tra username đã tồn tại
    if await db.get_db()["users"].find_one({"username": user.username}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username đã được sử dụng")

    user_dict = {
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password),  # Hash trước khi lưu
        "full_name": user.full_name,
        "role": "user",
    }

    result = await db.get_db()["users"].insert_one(user_dict)
    created = await db.get_db()["users"].find_one({"_id": result.inserted_id})
    created["_id"] = str(created["_id"])
    return created


# 2. Đăng nhập — trả về JWT token
@router.post("/login", response_description="Đăng nhập", response_model=TokenResponse)
async def login_user(login_data: UserLogin = Body(...)):
    user = await db.get_db()["users"].find_one({"email": login_data.email})

    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai email hoặc mật khẩu",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.get("is_blocked"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên.",
        )

    access_token = create_access_token(data={"sub": str(user["_id"])})

    user["_id"] = str(user["_id"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


# 3. Lấy thông tin user đang đăng nhập (route được bảo vệ)
@router.get("/me", response_description="Thông tin user hiện tại", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


# 4. Cập nhật thông tin cá nhân
@router.put("/me", response_description="Cập nhật thông tin cá nhân", response_model=UserResponse)
async def update_profile(data: UserUpdate = Body(...), current_user: dict = Depends(get_current_user)):
    update_fields = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="Không có dữ liệu để cập nhật")

    await db.get_db()["users"].update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": update_fields}
    )
    updated = await db.get_db()["users"].find_one({"_id": ObjectId(current_user["_id"])})
    updated["_id"] = str(updated["_id"])
    return updated


# 5. Đổi mật khẩu
@router.put("/me/password", response_description="Đổi mật khẩu")
async def change_password(data: PasswordChange = Body(...), current_user: dict = Depends(get_current_user)):
    user = await db.get_db()["users"].find_one({"_id": ObjectId(current_user["_id"])})
    if not verify_password(data.current_password, user["password"]):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng")

    await db.get_db()["users"].update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": {"password": hash_password(data.new_password)}}
    )
    return {"message": "Đổi mật khẩu thành công"}

