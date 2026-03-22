from fastapi import APIRouter, HTTPException, status, Depends, Query, Body
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timezone
from app.core.config import db
from app.core.dependencies import get_current_admin
from app.models.product import Product

router = APIRouter()


# ── 1. Dashboard Stats ───────────────────────────────────────────────────────
@router.get("/stats")
async def get_stats(admin=Depends(get_current_admin)):
    db_ = db.get_db()
    total_products = await db_["products"].count_documents({})
    total_users    = await db_["users"].count_documents({})
    total_orders   = await db_["orders"].count_documents({})

    revenue_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total"}}}]
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
    for o in orders:
        o["_id"] = str(o["_id"])

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
    return updated


# ── 4. Users list ────────────────────────────────────────────────────────────
@router.get("/users")
async def admin_list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin=Depends(get_current_admin),
):
    db_ = db.get_db()
    skip = (page - 1) * limit
    total = await db_["users"].count_documents({})
    users = await db_["users"].find().skip(skip).limit(limit).to_list(limit)
    for u in users:
        u["_id"] = str(u["_id"])
        u.pop("password", None)

    return {"total": total, "page": page, "limit": limit, "users": users}
