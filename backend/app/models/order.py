from typing import Optional, Annotated, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator

PyObjectId = Annotated[str, BeforeValidator(str)]


class OrderItem(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int


class Order(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    items: List[OrderItem]
    subtotal: float
    shipping: float = 30000
    total: float
    status: Literal["pending", "processing", "shipped", "delivered", "cancelled"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
