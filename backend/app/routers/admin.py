from fastapi import APIRouter, HTTPException, status, Depends, Query, Body, UploadFile, File
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import os, uuid, shutil
from app.core.config import db
from app.core.dependencies import get_current_admin
from app.models.product import Product
from app.routers.notification import create_notification

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), admin=Depends(get_current_admin)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Chi chap nhan anh: {', '.join(ALLOWED_EXT)}")
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File anh khong duoc qua 5MB")

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"image_url": f"http://127.0.0.1:8000/uploads/{filename}"}


# ── 1. Dashboard Stats ───────────────────────────────────────────────────────
@router.get("/stats")
async def get_stats(admin=Depends(get_current_admin)):
    db_ = db.get_db()
    total_products = await db_["products"].count_documents({})
    total_users    = await db_["users"].count_documents({})
    total_orders   = await db_["orders"].count_documents({})

    revenue_pipeline = [
        {"$match": {"status": "delivered"}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ]
    rev_result = await db_["orders"].aggregate(revenue_pipeline).to_list(1)
    total_revenue = rev_result[0]["total"] if rev_result else 0

    recent_orders = await db_["orders"].find().sort("created_at", -1).to_list(5)
    for o in recent_orders:
        o["_id"] = str(o["_id"])

    orders_by_status_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    status_result = await db_["orders"].aggregate(orders_by_status_pipeline).to_list(None)
    orders_by_status = {r["_id"]: r["count"] for r in status_result}

    return {
        "total_products": total_products,
        "total_users": total_users,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "recent_orders": recent_orders,
        "orders_by_status": orders_by_status,
    }


# ── 1b. Chart Data ────────────────────────────────────────────────────────────
@router.get("/chart-data")
async def get_chart_data(admin=Depends(get_current_admin)):
    db_ = db.get_db()

    # Doanh thu 7 ngày gần đây (chỉ đơn delivered)
    # Dùng naive UTC để khớp với cách Motor lưu datetime trong MongoDB
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    revenue_by_day = []
    for i in range(6, -1, -1):
        day_start = today - timedelta(days=i)
        day_end   = day_start + timedelta(days=1)
        pipe = [
            {"$match": {"status": "delivered", "created_at": {"$gte": day_start, "$lt": day_end}}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}},
        ]
        result = await db_["orders"].aggregate(pipe).to_list(1)
        revenue_by_day.append({
            "date": day_start.strftime("%d/%m"),
            "revenue": result[0]["total"] if result else 0,
            "orders": result[0]["count"] if result else 0,
        })

    # Top 5 danh mục bán chạy (theo số lượng sản phẩm bán trong đơn delivered)
    category_pipeline = [
        {"$match": {"status": "delivered"}},
        {"$unwind": "$items"},
        {"$lookup": {
            "from": "products",
            "let": {"pid": "$items.product_id"},
            "pipeline": [
                {"$match": {"$expr": {"$eq": [{"$toString": "$_id"}, "$$pid"]}}}
            ],
            "as": "product"
        }},
        {"$unwind": {"path": "$product", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$product.category",
            "quantity": {"$sum": "$items.quantity"},
            "revenue": {"$sum": {"$multiply": ["$items.price", "$items.quantity"]}},
        }},
        {"$sort": {"quantity": -1}},
        {"$limit": 5},
    ]
    cat_result = await db_["orders"].aggregate(category_pipeline).to_list(None)
    top_categories = [
        {"category": r["_id"] or "Khác", "quantity": r["quantity"], "revenue": r["revenue"]}
        for r in cat_result
    ]

    return {
        "revenue_by_day": revenue_by_day,
        "top_categories": top_categories,
    }


# ── 2. Products CRUD ─────────────────────────────────────────────────────────
@router.get("/products")
async def admin_list_products(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin=Depends(get_current_admin),
):
    db_ = db.get_db()
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}

    skip = (page - 1) * limit
    total = await db_["products"].count_documents(query)
    products = await db_["products"].find(query).skip(skip).limit(limit).to_list(limit)
    for p in products:
        p["_id"] = str(p["_id"])

    return {"total": total, "page": page, "limit": limit, "products": products}


@router.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
async def admin_create_product(product: Product = Body(...), admin=Depends(get_current_admin)):
    db_ = db.get_db()
    product_dict = product.model_dump(by_alias=True, exclude={"id"})
    result = await db_["products"].insert_one(product_dict)
    created = await db_["products"].find_one({"_id": result.inserted_id})
    created["_id"] = str(created["_id"])
    return created


@router.put("/products/{product_id}", response_model=Product)
async def admin_update_product(
    product_id: str,
    product: Product = Body(...),
    admin=Depends(get_current_admin),
):
    db_ = db.get_db()
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID khong hop le")

    update_data = {k: v for k, v in product.model_dump(by_alias=True, exclude={"id"}).items() if v is not None}
    result = await db_["products"].update_one({"_id": oid}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Khong tim thay san pham")

    updated = await db_["products"].find_one({"_id": oid})
    updated["_id"] = str(updated["_id"])
    return updated


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_product(product_id: str, admin=Depends(get_current_admin)):
    db_ = db.get_db()
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID khong hop le")

    result = await db_["products"].delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Khong tim thay san pham")


# ── 3. Orders Management ─────────────────────────────────────────────────────
@router.get("/orders")
async def admin_list_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin=Depends(get_current_admin),
):
    db_ = db.get_db()
    query = {}
    if status_filter:
        query["status"] = status_filter

    skip = (page - 1) * limit
    total = await db_["orders"].count_documents(query)
    orders = await db_["orders"].find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    # Lấy tên người dùng cho mỗi đơn hàng
    user_ids = list({o["user_id"] for o in orders if o.get("user_id")})
    users = await db_["users"].find(
        {"_id": {"$in": [ObjectId(uid) for uid in user_ids]}}
    ).to_list(len(user_ids))
    user_map = {str(u["_id"]): u.get("username", "") for u in users}

    for o in orders:
        o["_id"] = str(o["_id"])
        o["username"] = user_map.get(o.get("user_id", ""), "")

    return {"total": total, "page": page, "limit": limit, "orders": orders}


@router.put("/orders/{order_id}/status")
async def admin_update_order_status(
    order_id: str,
    body: dict = Body(...),
    admin=Depends(get_current_admin),
):
    db_ = db.get_db()
    new_status = body.get("status")
    valid = ["pending", "processing", "shipped", "delivered", "cancelled"]
    if new_status not in valid:
        raise HTTPException(status_code=400, detail="Trang thai khong hop le")

    try:
        oid = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID khong hop le")

    result = await db_["orders"].update_one({"_id": oid}, {"$set": {"status": new_status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Khong tim thay don hang")

    updated = await db_["orders"].find_one({"_id": oid})
    updated["_id"] = str(updated["_id"])

    # Thong bao cho user khi admin cap nhat trang thai
    status_text = {
        "pending": "Cho xac nhan",
        "processing": "Dang xu ly",
        "shipped": "Dang giao hang",
        "delivered": "Da giao thanh cong",
        "cancelled": "Da bi huy",
    }
    order_code = updated["_id"][-8:].upper()
    await create_notification(
        user_id=updated["user_id"],
        title="Cap nhat don hang",
        message=f"Don hang #{order_code}: {status_text.get(new_status, new_status)}",
        ntype="order",
        link=f"/orders/{updated['_id']}",
        target="user",
    )

    return updated


# ── 4. Admin: Lấy đánh giá cho 1 đơn hàng ───────────────────────────────────
@router.get("/orders/{order_id}/reviews")
async def get_order_reviews(order_id: str, admin=Depends(get_current_admin)):
    reviews = await db.get_db()["reviews"].find({
        "order_id": order_id,
    }).to_list(100)
    return {
        r["product_id"]: {
            "rating": r["rating"],
            "feedback": r.get("feedback", ""),
            "username": r.get("username", ""),
        }
        for r in reviews
    }


# ── 5. Users list ────────────────────────────────────────────────────────────
@router.get("/users")
async def admin_list_users(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin=Depends(get_current_admin),
):
    db_ = db.get_db()
    query = {}
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}},
        ]
    skip = (page - 1) * limit
    total = await db_["users"].count_documents(query)
    users = await db_["users"].find(query).skip(skip).limit(limit).to_list(limit)
    for u in users:
        u["_id"] = str(u["_id"])
        u.pop("password", None)

    return {"total": total, "page": page, "limit": limit, "users": users}


# ── 6. Block / Unblock user ──────────────────────────────────────────────────
@router.put("/users/{user_id}/block")
async def admin_toggle_block_user(
    user_id: str,
    body: dict = Body(...),
    admin=Depends(get_current_admin),
):
    db_ = db.get_db()
    is_blocked = body.get("is_blocked", True)
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID khong hop le")

    # Không cho phép khóa chính mình
    if str(admin["_id"]) == user_id:
        raise HTTPException(status_code=400, detail="Khong the khoa chinh minh")

    result = await db_["users"].update_one({"_id": oid}, {"$set": {"is_blocked": is_blocked}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Khong tim thay user")

    return {"ok": True, "is_blocked": is_blocked}
