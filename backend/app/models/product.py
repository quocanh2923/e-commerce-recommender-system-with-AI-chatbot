from typing import Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from bson import ObjectId

# --- Xử lý ObjectId cho Pydantic V2 ---
# Chuyển đổi ObjectId thành string để frontend đọc được
PyObjectId = Annotated[str, BeforeValidator(str)]

class Product(BaseModel):
    # Field id sẽ map với "_id" của MongoDB
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(..., title="Tên sản phẩm")
    price: float = Field(..., title="Giá tiền")
    description: Optional[str] = Field(None, title="Mô tả sản phẩm")
    image_url: Optional[str] = Field(None, title="Link ảnh sản phẩm")
    category: str = Field(..., title="Danh mục (VD: Ao, Quan)")
    rating: Optional[float] = Field(0.0, title="Điểm đánh giá (0-5)")
    stock: Optional[int] = Field(0, title="Số lượng tồn kho")

    # Cấu hình Model (Thay cho class Config cũ)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "Áo Thun AI",
                "price": 150000,
                "description": "Áo thun cotton co giãn 4 chiều",
                "image_url": "https://example.com/ao.jpg",
                "category": "Ao"
            }
        }
    )