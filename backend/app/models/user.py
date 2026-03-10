from typing import Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from bson import ObjectId

# --- Xử lý ObjectId cho Pydantic V2 ---
# Chuyển đổi ObjectId thành string để frontend đọc được
PyObjectId = Annotated[str, BeforeValidator(str)]

class User(BaseModel):
    # Field id sẽ map với "_id" của MongoDB
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str = Field(..., title="Tên người dùng")
    email: str = Field(..., title="Email")
    password: str = Field(..., title="Mật khẩu")
    full_name: Optional[str] = Field(None, title="Tên đầy đủ")
    role: str = Field(default="user", title="Vai trò")

    # Cấu hình Model (Thay cho class Config cũ)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepassword123",
                "full_name": "John Doe",
                "role": "user"
            }
        }
    )


class UserLogin(BaseModel):
    email: str = Field(..., title="Email")
    password: str = Field(..., title="Mật khẩu")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john@example.com",
                "password": "securepassword123"
            }
        }
    )
