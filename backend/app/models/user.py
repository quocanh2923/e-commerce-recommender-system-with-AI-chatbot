from typing import Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator, EmailStr

# --- Xử lý ObjectId cho Pydantic V2 ---
PyObjectId = Annotated[str, BeforeValidator(str)]


class User(BaseModel):
    """Model lưu vào MongoDB (có password hash)."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str = Field(..., title="Tên người dùng")
    email: EmailStr = Field(..., title="Email")
    password: str = Field(..., title="Mật khẩu đã hash")
    full_name: Optional[str] = Field(None, title="Tên đầy đủ")
    phone: Optional[str] = Field(None, title="Số điện thoại")
    address: Optional[str] = Field(None, title="Địa chỉ")
    role: str = Field(default="user", title="Vai trò: user | admin")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class UserRegister(BaseModel):
    """Schema nhận dữ liệu đăng ký từ client."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepassword123",
                "full_name": "John Doe"
            }
        }
    )


class UserLogin(BaseModel):
    """Schema nhận dữ liệu đăng nhập từ client."""
    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john@example.com",
                "password": "securepassword123"
            }
        }
    )


class UserResponse(BaseModel):
    """Schema trả về cho client (không có password)."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    role: str

    model_config = ConfigDict(populate_by_name=True)


class UserUpdate(BaseModel):
    """Schema cập nhật thông tin cá nhân."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema đổi mật khẩu."""
    current_password: str
    new_password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """Schema trả về JWT token sau đăng nhập."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
