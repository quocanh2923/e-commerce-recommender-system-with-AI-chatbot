from fastapi import APIRouter, Body, Depends
from typing import List, Literal
from datetime import datetime, timezone
from app.models.interaction import Interaction
from app.core.config import db
from app.core.dependencies import get_current_user

router = APIRouter()


class InteractionCreate(Interaction.__bases__[0]):
    pass


# 1. API Lưu hành vi mới (yêu cầu đăng nhập)
@router.post("/", response_description="Lưu hành vi người dùng", response_model=Interaction)
async def create_interaction(
    product_id: str,
    action_type: Literal["view", "add_to_cart", "purchase"],
    current_user: dict = Depends(get_current_user)
):
    interaction_dict = {
        "user_id": current_user["_id"],
        "product_id": product_id,
        "action_type": action_type,
        "timestamp": datetime.now(timezone.utc),
    }
    result = await db.get_db()["interactions"].insert_one(interaction_dict)
    created = await db.get_db()["interactions"].find_one({"_id": result.inserted_id})
    created["_id"] = str(created["_id"])
    return created


# 2. API Lấy lịch sử hành vi của 1 người dùng
@router.get("/user/{user_id}", response_description="Lấy lịch sử hành vi người dùng", response_model=List[Interaction])
async def get_user_interactions(user_id: str):
    """
    Lấy tất cả lịch sử hành vi của một người dùng.
    Sắp xếp theo timestamp giảm dần (mới nhất lên trước).
    """
    interactions = await db.get_db()["interactions"].find(
        {"user_id": user_id}
    ).sort("timestamp", -1).to_list(None)
    
    # Convert _id sang string cho từng record
    for interaction in interactions:
        interaction["_id"] = str(interaction["_id"])
    
    return interactions
