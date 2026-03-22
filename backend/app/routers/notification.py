from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.core.config import db
from app.core.dependencies import get_current_user, get_current_admin

router = APIRouter()


# ── Helper: tao thong bao ──────────────────────────────────────
async def create_notification(
    user_id: str,
    title: str,
    message: str,
    ntype: str = "info",
    link: Optional[str] = None,
    target: str = "user",
):
    """
    ntype: 'order' | 'review' | 'info' | 'admin'
    target: 'user' | 'admin'
    """
    doc = {
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": ntype,
        "link": link,
        "target": target,
        "is_read": False,
        "created_at": datetime.now(timezone.utc),
    }
    await db.get_db()["notifications"].insert_one(doc)


# ── User: lay thong bao cua minh ──────────────────────────────
@router.get("/")
async def get_my_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    db_ = db.get_db()
    user_id = current_user["_id"]
    skip = (page - 1) * limit

    q = {"user_id": user_id, "target": {"$ne": "admin"}}
    total = await db_["notifications"].count_documents(q)
    unread = await db_["notifications"].count_documents({**q, "is_read": False})
    items = await (
        db_["notifications"]
        .find(q)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )
    for n in items:
        n["_id"] = str(n["_id"])

    return {"total": total, "unread": unread, "notifications": items}


# ── User: danh dau da doc 1 thong bao ─────────────────────────
@router.put("/{noti_id}/read")
async def mark_read(noti_id: str, current_user: dict = Depends(get_current_user)):
    db_ = db.get_db()
    try:
        oid = ObjectId(noti_id)
    except Exception:
        return {"ok": False}
    await db_["notifications"].update_one(
        {"_id": oid, "user_id": current_user["_id"]},
        {"$set": {"is_read": True}},
    )
    return {"ok": True}


# ── User: danh dau tat ca da doc ──────────────────────────────
@router.put("/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    db_ = db.get_db()
    result = await db_["notifications"].update_many(
        {"user_id": current_user["_id"], "is_read": False},
        {"$set": {"is_read": True}},
    )
    return {"ok": True, "updated": result.modified_count}


# ── Admin: lay thong bao cua admin ────────────────────────────
@router.get("/admin")
async def get_admin_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    admin=Depends(get_current_admin),
):
    db_ = db.get_db()
    admin_id = admin["_id"]
    skip = (page - 1) * limit

    q = {"user_id": admin_id, "target": "admin"}
    total = await db_["notifications"].count_documents(q)
    unread = await db_["notifications"].count_documents({**q, "is_read": False})
    items = await (
        db_["notifications"]
        .find(q)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )
    for n in items:
        n["_id"] = str(n["_id"])

    return {"total": total, "unread": unread, "notifications": items}
