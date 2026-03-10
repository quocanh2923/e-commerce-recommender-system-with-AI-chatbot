from fastapi import APIRouter, Body
from typing import List
from app.models.interaction import Interaction
from app.core.config import db

router = APIRouter()


# 1. API Lưu hành vi mới
@router.post("/", response_description="Lưu hành vi người dùng mới", response_model=Interaction)
async def create_interaction(interaction: Interaction = Body(...)):
    """
    Lưu hành vi (interaction) của người dùng.
    Các hành vi hỗ trợ: view, add_to_cart, purchase
    """
    # Chuyển đổi dữ liệu từ dạng Model sang dict để lưu MongoDB
    interaction_dict = interaction.dict(by_alias=True)
    
    # Bỏ trường _id đi để MongoDB tự tạo _id mới
    if "_id" in interaction_dict:
        del interaction_dict["_id"]

    # Lưu vào Collection tên là "interactions"
    new_interaction = await db.get_db()["interactions"].insert_one(interaction_dict)
    
    # Tìm lại hành vi vừa tạo để trả về
    created_interaction = await db.get_db()["interactions"].find_one({"_id": new_interaction.inserted_id})
    
    # Convert _id sang string
    created_interaction["_id"] = str(created_interaction["_id"])
    return created_interaction


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
