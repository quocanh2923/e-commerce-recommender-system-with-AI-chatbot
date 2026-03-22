from typing import Optional, Annotated, List
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator

PyObjectId = Annotated[str, BeforeValidator(str)]


class CartItem(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int = Field(default=1, ge=1)
    image_url: Optional[str] = None


class Cart(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    items: List[CartItem] = []

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
