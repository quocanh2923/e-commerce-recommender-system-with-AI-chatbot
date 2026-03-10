from typing import Optional, Annotated, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from bson import ObjectId

# --- Xử lý ObjectId cho Pydantic V2 ---
# Chuyển đổi ObjectId thành string để frontend đọc được
PyObjectId = Annotated[str, BeforeValidator(str)]

class Interaction(BaseModel):
    # Field id sẽ map với "_id" của MongoDB
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str = Field(..., title="ID người dùng")
    product_id: str = Field(..., title="ID sản phẩm")
    action_type: Literal["view", "add_to_cart", "purchase"] = Field(..., title="Loại hành vi")
    timestamp: datetime = Field(default_factory=datetime.utcnow, title="Thời gian hành vi")

    # Cấu hình Model (Thay cho class Config cũ)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "product_id": "507f1f77bcf86cd799439012",
                "action_type": "view",
                "timestamp": "2026-03-10T10:30:00"
            }
        }
    )
