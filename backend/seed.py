# ==============================================================
# seed.py  —  Chay: python seed.py
# Yeu cau: dat file articles.csv va customers.csv vao thu muc
#          backend/data/ truoc khi chay
# ==============================================================
import asyncio
import csv
import os
import random
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows console default cp1252 khong in duoc tieng Viet -> ep utf-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

load_dotenv()

MONGO_URL    = os.getenv("MONGO_URL")
DB_NAME      = os.getenv("DB_NAME", "shop_ai_db")
BACKEND_URL  = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATA_DIR        = Path(__file__).parent / "data"
CUSTOMERS_CSV   = DATA_DIR / "customers.csv"
IMG_DEST_DIR    = Path(__file__).parent / "uploads" / "products"   # copy anh ra day de FastAPI serve

from data_utils import (
    ARTICLES_CSV, IMG_DIR as IMG_SOURCE_DIR,
    CATEGORIES, PER_CATEGORY,
    categorize_article, article_image_path,
)

# ── Khoang gia theo category VN (VND) ───────────────────
PRICE_RANGES = {
    "Áo":       (150_000, 800_000),
    "Quần":     (200_000, 900_000),
    "Váy":      (250_000, 1_200_000),
    "Giày":     (300_000, 2_000_000),
    "Túi":      (400_000, 3_000_000),
    "Phụ kiện": (100_000, 500_000),
    "Đồ lót":   (100_000, 400_000),
    "Đồ bơi":   (200_000, 600_000),
    "Vớ":       (50_000, 200_000),
}

DEFAULT_PRICE_RANGE = (100_000, 1_000_000)

# ── 4 nhom nguoi dung voi so thich khac nhau (de train CF) ───
# Moi nhom: (ten_nhom, danh_sach_category_uu_tien VN, khoang_gia_max, rating_min)
USER_SEGMENTS = [
    ("budget",  ["Áo", "Quần", "Vớ"],          500_000,  3.0),
    ("fashion", ["Váy", "Túi", "Phụ kiện"],   3_000_000,  4.0),
    ("sport",   ["Giày", "Áo", "Phụ kiện"],   1_000_000,  3.5),
    ("luxury",  ["Túi", "Giày", "Phụ kiện"],  5_000_000,  4.5),
]

NUM_USERS             = 20  # 20 nguoi dung fake (5 user moi segment)
INTERACTIONS_PER_USER = 30  # moi user tuong tac khoang 30 san pham


# ═══════════════════════════════════════════════════════════════
# Doc CSV
# ═══════════════════════════════════════════════════════════════

def _copy_article_image(article_id: str) -> bool:
    """
    Copy anh san pham H&M tu data/images/{prefix}/{article_id}.jpg
    sang uploads/products/{article_id}.jpg.
    Tra ve True neu copy thanh cong (anh ton tai), False neu khong co anh.
    """
    if not article_id:
        return False
    src = article_image_path(article_id)
    if not src.exists():
        return False
    dst = IMG_DEST_DIR / f"{article_id}.jpg"
    if not dst.exists():  # idempotent
        shutil.copy2(src, dst)
    return True


def read_articles_balanced() -> list[dict]:
    """
    Quet articles.csv, lay toi da PER_CATEGORY san pham moi category.
    Chi nhan san pham CO anh local (loai bo nhung san pham khong co anh
    de tranh dung picsum/placeholder).
    """
    if not IMG_SOURCE_DIR.exists():
        print(f"[ERROR] Khong tim thay {IMG_SOURCE_DIR}")
        print(f"        Chay 'python download_hm_images.py' truoc de tai anh.")
        return []

    IMG_DEST_DIR.mkdir(parents=True, exist_ok=True)

    products_by_cat: dict[str, list[dict]] = {c: [] for c in CATEGORIES}
    skipped_no_image = 0
    skipped_no_category = 0

    with open(ARTICLES_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Stop som neu tat ca category da day
            if all(len(products_by_cat[c]) >= PER_CATEGORY for c in CATEGORIES):
                break

            cat = categorize_article(row)
            if cat is None:
                skipped_no_category += 1
                continue
            if len(products_by_cat[cat]) >= PER_CATEGORY:
                continue

            article_id = row.get("article_id", "").strip()
            if not _copy_article_image(article_id):
                skipped_no_image += 1
                continue

            lo, hi = PRICE_RANGES.get(cat, DEFAULT_PRICE_RANGE)
            price  = round(random.randint(lo, hi) / 1000) * 1000
            rating = round(random.uniform(2.8, 5.0), 1)
            stock  = random.randint(5, 200)

            name = row.get("prod_name", "").strip() or f"San pham {article_id}"
            desc = row.get("detail_desc", "").strip() or "San pham chat luong cao."
            image_url = f"{BACKEND_URL}/uploads/products/{article_id}.jpg"

            products_by_cat[cat].append({
                "name":        name,
                "price":       float(price),
                "description": desc,
                "image_url":   image_url,
                "category":    cat,
                "rating":      rating,
                "stock":       stock,
                "article_id":  article_id,
            })

    products = [p for cat_list in products_by_cat.values() for p in cat_list]

    print(f"    -> Phan bo theo category:")
    for cat in CATEGORIES:
        n = len(products_by_cat[cat])
        flag = "OK" if n >= PER_CATEGORY else f"THIEU - chay download_hm_images.py de tai them"
        print(f"       {cat:12s}: {n:3d}/{PER_CATEGORY}  [{flag}]")
    if skipped_no_image > 0:
        print(f"    -> Bo qua {skipped_no_image} san pham khong co anh trong images/")
    if skipped_no_category > 0:
        print(f"    -> Bo qua {skipped_no_category} san pham ngoai pham vi (Cosmetic/Furniture/Stationery...)")

    return products



def read_customers(limit: int) -> list[dict]:
    """Lay thong tin co ban tu customers.csv de tao username."""
    customers = []
    with open(CUSTOMERS_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break
            customers.append({
                "raw_id": row.get("customer_id", f"user_{i}")[:8],
                "age":    int(float(row["age"])) if row.get("age") else random.randint(18, 50),
            })
    return customers


# ═══════════════════════════════════════════════════════════════
# Tao du lieu insert
# ═══════════════════════════════════════════════════════════════

def build_users(customers: list[dict]) -> list[dict]:
    users = []
    default_password = pwd_context.hash("password123")

    for i, c in enumerate(customers):
        segment_idx = i // (NUM_USERS // len(USER_SEGMENTS))
        segment_idx = min(segment_idx, len(USER_SEGMENTS) - 1)
        segment_name = USER_SEGMENTS[segment_idx][0]

        username = f"user_{segment_name}_{i+1:02d}"
        email    = f"{username}@demo.com"

        users.append({
            "username":        username,
            "email":           email,
            "hashed_password": default_password,
            "role":            "user",
            "segment":         segment_name,   # dung cho phan tich, khong hien thi
            "created_at":      datetime.now(timezone.utc),
        })

    return users


def build_interactions(user_docs: list[dict], product_docs: list[dict]) -> list[dict]:
    """
    Tao interactions co pattern ro rang:
    - Moi segment uu tien category rieng va khoang gia rieng
    - Action weights: view > add_to_cart > purchase
    """
    interactions = []

    # Index san pham theo category
    by_category: dict[str, list[dict]] = {}
    for p in product_docs:
        cat = p["category"]
        by_category.setdefault(cat, []).append(p)

    random.seed(42)  # de tao lai ket qua giong nhau

    for user in user_docs:
        segment_name = user["segment"]
        # Tim segment config
        seg_cfg = next(s for s in USER_SEGMENTS if s[0] == segment_name)
        _, preferred_cats, price_max, rating_min = seg_cfg

        # Uu tien lay san pham trong category yeu thich
        preferred_pool = []
        for cat in preferred_cats:
            preferred_pool.extend(by_category.get(cat, []))

        # Loc theo gia va rating
        preferred_pool = [
            p for p in preferred_pool
            if p["price"] <= price_max and p["rating"] >= rating_min
        ]

        # Neu pool qua nho, them san pham ngau nhien
        fallback_pool = [
            p for p in product_docs
            if p not in preferred_pool
        ]
        random.shuffle(preferred_pool)
        random.shuffle(fallback_pool)

        # Lay 70% tu preferred, 30% tu fallback
        n_preferred = int(INTERACTIONS_PER_USER * 0.7)
        n_fallback  = INTERACTIONS_PER_USER - n_preferred

        chosen = preferred_pool[:n_preferred] + fallback_pool[:n_fallback]
        # Dam bao du so luong
        while len(chosen) < INTERACTIONS_PER_USER and fallback_pool:
            extra = [p for p in fallback_pool if p not in chosen]
            if not extra:
                break
            chosen.append(random.choice(extra))

        user_id = str(user["_id"])

        for product in chosen:
            product_id = str(product["_id"])

            # Moi san pham: chac chan view, co the add_to_cart, it khi purchase
            action_types = ["view"]
            if random.random() < 0.4:
                action_types.append("add_to_cart")
            if random.random() < 0.15:
                action_types.append("purchase")

            for action in action_types:
                interactions.append({
                    "user_id":    user_id,
                    "product_id": product_id,
                    "action_type": action,
                    "timestamp":  datetime.now(timezone.utc),
                })

    return interactions


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

async def main():
    # --- Kiem tra file CSV ---
    missing = []
    if not ARTICLES_CSV.exists():
        missing.append(str(ARTICLES_CSV))
    if not CUSTOMERS_CSV.exists():
        missing.append(str(CUSTOMERS_CSV))

    if missing:
        print("\n[ERROR] Khong tim thay file CSV:")
        for f in missing:
            print(f"  - {f}")
        print("\nHuong dan:")
        print("  1. Tao thu muc: backend/data/")
        print("  2. Tai tu Kaggle: kaggle.com/competitions/h-and-m-personalized-fashion-recommendations")
        print("     - articles.csv  (~35MB)")
        print("     - customers.csv (~200MB)")
        print("  3. Tai anh chon loc: python download_hm_images.py")
        print("     (chi tai ~270 anh ~40MB, KHONG can tai images.zip 25GB)")
        print("  4. Chay lai: python seed.py")
        return

    # --- Ket noi MongoDB ---
    print("[1/5] Ket noi MongoDB...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # --- Xoa du lieu cu ---
    print("[2/5] Xoa du lieu cu (products, users fake, interactions, anh san pham)...")
    await db["products"].delete_many({})
    await db["users"].delete_many({"role": "user"})   # giu admin neu co
    await db["interactions"].delete_many({})
    await db["carts"].delete_many({})

    # Xoa anh san pham cu de tranh tich tu file rac
    if IMG_DEST_DIR.exists():
        shutil.rmtree(IMG_DEST_DIR)
    IMG_DEST_DIR.mkdir(parents=True, exist_ok=True)

    # --- Doc va insert products ---
    target_total = PER_CATEGORY * len(CATEGORIES)
    print(f"[3/5] Doc articles.csv (target ~{target_total} san pham, {PER_CATEGORY}/category)...")
    raw_products = read_articles_balanced()
    if not raw_products:
        print("[ERROR] Khong co san pham nao duoc nap. Dung seed.")
        client.close()
        return
    product_result = await db["products"].insert_many(raw_products)
    inserted_ids  = product_result.inserted_ids
    product_docs  = await db["products"].find(
        {"_id": {"$in": inserted_ids}}
    ).to_list(len(inserted_ids))
    print(f"    -> Da them {len(product_docs)} san pham")

    # --- Doc va insert users ---
    print(f"[4/5] Doc va tao {NUM_USERS} users fake...")
    if CUSTOMERS_CSV.exists():
        raw_customers = read_customers(NUM_USERS)
    else:
        raw_customers = [{"raw_id": f"u{i}", "age": random.randint(18, 50)} for i in range(NUM_USERS)]

    user_list  = build_users(raw_customers)
    user_result = await db["users"].insert_many(user_list)
    user_ids    = user_result.inserted_ids
    user_docs   = await db["users"].find(
        {"_id": {"$in": user_ids}}
    ).to_list(NUM_USERS)
    print(f"    -> Da them {len(user_docs)} users")
    print("       (password mac dinh cho tat ca: password123)")

    # In thi du user moi segment
    for seg in USER_SEGMENTS:
        sample = next((u for u in user_docs if u.get("segment") == seg[0]), None)
        if sample:
            print(f"       Segment [{seg[0]}]: username={sample['username']}")

    # --- Tao va insert interactions ---
    print("[5/5] Tao interactions co pattern...")
    interactions = build_interactions(user_docs, product_docs)
    if interactions:
        await db["interactions"].insert_many(interactions)
    print(f"    -> Da them {len(interactions)} interactions")

    # --- Thong ke ---
    print("\n======= HOAN THANH =======")
    print(f"  Products    : {await db['products'].count_documents({})}")
    print(f"  Users (fake): {await db['users'].count_documents({'role': 'user'})}")
    print(f"  Interactions: {await db['interactions'].count_documents({})}")
    print("")
    print("  Phan bo interactions theo action_type:")
    for action in ["view", "add_to_cart", "purchase"]:
        count = await db["interactions"].count_documents({"action_type": action})
        print(f"    {action:15s}: {count}")
    print("")
    print("  Phan bo san pham theo category:")
    categories = await db["products"].distinct("category")
    for cat in sorted(categories):
        count = await db["products"].count_documents({"category": cat})
        print(f"    {cat:15s}: {count}")

    client.close()
    print("\n[DONE] Seed thanh cong! Khoi dong lai uvicorn de reload.\n")


if __name__ == "__main__":
    asyncio.run(main())
