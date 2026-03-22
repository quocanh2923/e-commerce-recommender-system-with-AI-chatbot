"""
routers/recommend.py
====================
3 endpoints:
  GET /recommend/popular              - San pham pho bien (fallback, khong can dang nhap)
  GET /recommend/for-you              - Goi y ca nhan (Collaborative Filtering) - can dang nhap
  GET /recommend/similar/{product_id} - San pham tuong tu (Content-based Filtering)

Thuat toan:
  - Popular     : Dem so lan xuat hien trong interactions (co trong so: purchase=5, add_to_cart=2, view=1)
  - For-You (CF): User-Item matrix + Cosine Similarity giua cac user
                  → Tim k user tuong tu → gop cac san pham ho da mua/them vao gio
  - Similar (CB): Cosine Similarity tren vector [category_encoded, price_normalized, rating_normalized]
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from bson import ObjectId
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder

from app.core.config import db
from app.core.dependencies import get_current_user

router = APIRouter()

# ── Trong so hanh vi (de tinh muc do quan tam) ──
ACTION_WEIGHTS = {"purchase": 5, "add_to_cart": 2, "view": 1}


# ═══════════════════════════════════════════════════
# Helper: lay product list dang dict co _id la string
# ═══════════════════════════════════════════════════
async def _get_products_by_ids(product_ids: list[str]) -> list[dict]:
    """Lay nhieu san pham theo danh sach id, giu nguyen thu tu."""
    obj_ids = []
    for pid in product_ids:
        try:
            obj_ids.append(ObjectId(pid))
        except Exception:
            pass
    if not obj_ids:
        return []
    docs = await db.get_db()["products"].find({"_id": {"$in": obj_ids}}).to_list(len(obj_ids))
    # Sap xep theo thu tu product_ids goc
    id_to_doc = {str(d["_id"]): d for d in docs}
    result = []
    for pid in product_ids:
        if pid in id_to_doc:
            doc = id_to_doc[pid]
            doc["_id"] = str(doc["_id"])
            result.append(doc)
    return result


def _serialize(product: dict) -> dict:
    product["_id"] = str(product["_id"])
    return product


# ═══════════════════════════════════════════════════
# 1. POPULAR — San pham pho bien
# ═══════════════════════════════════════════════════
@router.get("/popular")
async def get_popular_products(limit: int = Query(10, ge=1, le=50)):
    """
    Tinh diem pho bien dua tren interactions:
      score = sum(weight * count) voi weight: purchase=5, add_to_cart=2, view=1
    """
    pipeline = [
        {"$group": {
            "_id": "$product_id",
            "score": {"$sum": {
                "$switch": {
                    "branches": [
                        {"case": {"$eq": ["$action_type", "purchase"]},    "then": 5},
                        {"case": {"$eq": ["$action_type", "add_to_cart"]}, "then": 2},
                    ],
                    "default": 1
                }
            }}
        }},
        {"$sort": {"score": -1}},
        {"$limit": limit},
    ]
    results = await db.get_db()["interactions"].aggregate(pipeline).to_list(limit)
    product_ids = [r["_id"] for r in results]
    products = await _get_products_by_ids(product_ids)

    # Neu chua du limit, bo sung san pham moi nhat
    if len(products) < limit:
        existing_ids = {p["_id"] for p in products}
        extra = await db.get_db()["products"].find(
            {"_id": {"$nin": [ObjectId(pid) for pid in existing_ids if len(pid) == 24]}}
        ).sort("_id", -1).limit(limit - len(products)).to_list(limit)
        products += [_serialize(p) for p in extra]

    return products[:limit]


# ═══════════════════════════════════════════════════
# 2. FOR-YOU — Collaborative Filtering
# ═══════════════════════════════════════════════════
@router.get("/for-you")
async def get_recommendations_for_user(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """
    User-based Collaborative Filtering:
    1. Xay dung User-Item matrix (score = weighted sum of actions)
    2. Tinh Cosine Similarity giua current_user va cac user khac
    3. Lay top-K user tuong tu
    4. Gop san pham ho da tuong tac (ma current_user chua tuong tac)
    5. Sap xep theo weighted score cua neighbor users
    """
    user_id = str(current_user["_id"])

    # Lay tat ca interactions
    all_interactions = await db.get_db()["interactions"].find({}).to_list(10000)

    if not all_interactions:
        return await get_popular_products(limit)

    # Xay dung user-item score matrix
    # score[user][product] = sum of action weights
    user_item: dict[str, dict[str, float]] = {}
    for inter in all_interactions:
        uid = str(inter["user_id"])
        pid = str(inter["product_id"])
        weight = ACTION_WEIGHTS.get(inter["action_type"], 1)
        user_item.setdefault(uid, {})
        user_item[uid][pid] = user_item[uid].get(pid, 0) + weight

    # Neu user chua co interaction → tra ve popular
    if user_id not in user_item:
        return await get_popular_products(limit)

    # Lay danh sach tat ca user va product
    all_users = list(user_item.keys())
    all_products = list({pid for scores in user_item.values() for pid in scores})

    if len(all_users) < 2:
        return await get_popular_products(limit)

    # Tao matrix numpy (users x products)
    user_idx = {u: i for i, u in enumerate(all_users)}
    prod_idx = {p: i for i, p in enumerate(all_products)}

    matrix = np.zeros((len(all_users), len(all_products)), dtype=np.float32)
    for uid, scores in user_item.items():
        for pid, score in scores.items():
            matrix[user_idx[uid], prod_idx[pid]] = score

    # Tinh cosine similarity
    target_idx = user_idx[user_id]
    target_vec = matrix[target_idx].reshape(1, -1)
    sims = cosine_similarity(target_vec, matrix)[0]  # shape: (n_users,)

    # Top-K neighbors (bo qua chinh minh)
    K = min(5, len(all_users) - 1)
    sims[target_idx] = -1  # loai current user
    neighbor_indices = np.argsort(sims)[::-1][:K]

    # San pham current user da tuong tac
    seen_products = set(user_item[user_id].keys())

    # Gop san pham tu neighbors
    candidate_scores: dict[str, float] = {}
    for ni in neighbor_indices:
        sim_score = float(sims[ni])
        if sim_score <= 0:
            continue
        neighbor_uid = all_users[ni]
        for pid, item_score in user_item[neighbor_uid].items():
            if pid not in seen_products:
                candidate_scores[pid] = candidate_scores.get(pid, 0) + sim_score * item_score

    if not candidate_scores:
        return await get_popular_products(limit)

    # Sap xep theo score giam dan
    ranked = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
    top_ids = [pid for pid, _ in ranked[:limit]]

    products = await _get_products_by_ids(top_ids)

    # Neu chua du limit, bo sung popular
    if len(products) < limit:
        extra = await get_popular_products(limit * 2)
        seen = {p["_id"] for p in products}
        for p in extra:
            if p["_id"] not in seen and len(products) < limit:
                products.append(p)

    return products[:limit]


# ═══════════════════════════════════════════════════
# 3. SIMILAR — Content-based Filtering
# ═══════════════════════════════════════════════════
@router.get("/similar/{product_id}")
async def get_similar_products(
    product_id: str,
    limit: int = Query(8, ge=1, le=20),
):
    """
    Content-based Filtering dua tren:
      - category (one-hot encoding)
      - price (normalized 0-1)
      - rating (normalized 0-1)
    Tinh Cosine Similarity → tra ve top-N san pham tuong tu nhat (tru san pham hien tai)
    """
    # Lay tat ca san pham
    all_products = await db.get_db()["products"].find({}).to_list(2000)
    if len(all_products) < 2:
        return []

    # Tim san pham hien tai
    target = None
    for p in all_products:
        if str(p["_id"]) == product_id:
            target = p
            break

    if not target:
        return []

    # ── Encode features ──────────────────────────────
    categories = [p.get("category", "") for p in all_products]
    le = LabelEncoder()
    cat_encoded = le.fit_transform(categories)  # int array

    prices  = np.array([p.get("price", 0) for p in all_products], dtype=np.float32)
    ratings = np.array([p.get("rating", 0) for p in all_products], dtype=np.float32)

    # Normalize 0-1
    def _norm(arr):
        mn, mx = arr.min(), arr.max()
        return (arr - mn) / (mx - mn + 1e-9)

    prices_n  = _norm(prices)
    ratings_n = _norm(ratings)

    # One-hot cho category
    n_cats = len(le.classes_)
    cat_onehot = np.zeros((len(all_products), n_cats), dtype=np.float32)
    for i, c in enumerate(cat_encoded):
        cat_onehot[i, c] = 1.0

    # Feature weights: category quan trong nhat (x3), price (x1.5), rating (x1)
    feature_matrix = np.hstack([
        cat_onehot * 3.0,
        prices_n.reshape(-1, 1) * 1.5,
        ratings_n.reshape(-1, 1) * 1.0,
    ])

    # Tim index cua target
    target_idx = next(i for i, p in enumerate(all_products) if str(p["_id"]) == product_id)

    # Tinh cosine similarity
    target_vec = feature_matrix[target_idx].reshape(1, -1)
    sims = cosine_similarity(target_vec, feature_matrix)[0]

    # Sap xep giam dan, bo qua chinh no
    sims[target_idx] = -1
    top_indices = np.argsort(sims)[::-1][:limit]

    result = []
    for i in top_indices:
        p = all_products[i]
        p["_id"] = str(p["_id"])
        result.append(p)

    return result
