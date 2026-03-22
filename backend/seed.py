# ==============================================================
# seed.py  —  Chay: python seed.py
# Yeu cau: dat file articles.csv va customers.csv vao thu muc
#          backend/data/ truoc khi chay
# ==============================================================
import asyncio
import csv
import os
import random
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME   = os.getenv("DB_NAME", "shop_ai_db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATA_DIR        = Path(__file__).parent / "data"
ARTICLES_CSV    = DATA_DIR / "articles.csv"
CUSTOMERS_CSV   = DATA_DIR / "customers.csv"

# ── Ánh xạ garment_group_name → danh muc tieng Viet ──────────
CATEGORY_MAP = {
    # Upper body / shirts / tops
    "Jersey Basic":        "Áo",
    "Jersey Fancy":        "Áo",
    "Knitwear":            "Áo",
    "Blouses":             "Áo",
    "Shirts":              "Áo",
    "Sweater":             "Áo",
    "Jacket & Waistcoat":  "Áo",
    "Outdoor":             "Áo",
    # Lower body / bottoms
    "Trousers Denim":      "Quần",
    "Trousers":            "Quần",
    "Shorts":              "Quần",
    "Skirts":              "Quần",
    # Full body / dresses
    "Dresses Ladies":      "Váy",
    "Dresses Girls":       "Váy",
    "Dressed":             "Váy",
    "Dresses/Skirts girls":"Váy",
    "Jumpsuit":            "Váy",
    # Shoes
    "Shoes":               "Giày",
    "Shoe":                "Giày",
    # Bags (H&M khong co, them thu cong)
    "Bags":                "Túi",
    "Bag":                 "Túi",
    # Accessories
    "Accessories":         "Phụ kiện",
    "Hat/beanie":          "Phụ kiện",
    "Gloves":              "Phụ kiện",
    "Scarf":               "Phụ kiện",
    "Belt":                "Phụ kiện",
    "Sunglasses":          "Phụ kiện",
    "Watches":             "Đồng hồ",
    # Underwear / nightwear
    "Under-, Nightwear":   "Đồ lót",
    "Underwear":           "Đồ lót",
    "Nightwear":           "Đồ lót",
    "Lingerie":            "Đồ lót",
    # Swimwear
    "Swimwear":            "Đồ bơi",
    # Socks
    "Socks and Tights":    "Vớ",
    "Socks & Tights":      "Vớ",
}

# ── Khoang gia theo danh muc (VND) ───────────────────────────
PRICE_RANGES = {
    "Áo":           (150_000, 800_000),
    "Quần":         (200_000, 900_000),
    "Giày":         (300_000, 2_000_000),
    "Túi":          (400_000, 3_000_000),
    "Phụ kiện":    (100_000, 500_000),
    "Váy":          (250_000, 1_200_000),
    "Đồng hồ":     (500_000, 5_000_000),
    "Đồ lót":      (100_000, 400_000),
    "Đồ bơi":      (200_000, 600_000),
    "Vớ":           (50_000, 200_000),
}

DEFAULT_PRICE_RANGE = (100_000, 1_000_000)

# ── 4 nhom nguoi dung voi sở thich khac nhau (de train CF) ───
# Moi nhom: (ten_nhom, danh_sach_category_uu_tien, khoang_gia_max, rating_min)
USER_SEGMENTS = [
    ("budget",  ["Áo", "Quần", "Vớ"],                500_000,  3.0),
    ("fashion", ["Váy", "Túi", "Phụ kiện"],        3_000_000,  4.0),
    ("sport",   ["Giày", "Áo", "Phụ kiện"],        1_000_000,  3.5),
    ("luxury",  ["Đồng hồ", "Túi", "Giày"],        5_000_000,  4.5),
]

NUM_PRODUCTS   = 300  # lay 300 san pham dau tu articles.csv
NUM_USERS      = 20   # 20 nguoi dung fake (5 user moi segment)
INTERACTIONS_PER_USER = 30  # moi user tuong tac khoang 30 san pham


# ═══════════════════════════════════════════════════════════════
# Doc CSV
# ═══════════════════════════════════════════════════════════════

def read_articles(limit: int) -> list[dict]:
    products = []
    with open(ARTICLES_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break

            raw_group = row.get("garment_group_name", "").strip()
            category  = CATEGORY_MAP.get(raw_group, "Phụ kiện")

            lo, hi  = PRICE_RANGES.get(category, DEFAULT_PRICE_RANGE)
            price   = round(random.randint(lo, hi) / 1000) * 1000

            rating  = round(random.uniform(2.8, 5.0), 1)
            stock   = random.randint(5, 200)

            name = row.get("prod_name", f"San pham {i+1}").strip()
            desc = row.get("detail_desc", "").strip() or "San pham chat luong cao."

            img_seed  = (i + 1) * 7
            image_url = f"https://picsum.photos/seed/{img_seed}/400/400"

            products.append({
                "name":        name,
                "price":       float(price),
                "description": desc,
                "image_url":   image_url,
                "category":    category,
                "rating":      rating,
                "stock":       stock,
            })

    # ── Them san pham Tui va Dong ho thu cong (H&M khong co) ──
    extra_products = [
        {"name": "Túi Xách Tay Da Thật", "price": 850_000.0, "description": "Túi xách tay da bò thật, thiết kế sang trọng.", "image_url": "https://picsum.photos/seed/501/400/400", "category": "Túi", "rating": 4.5, "stock": 30},
        {"name": "Túi Đeo Chéo Nữ Mini", "price": 320_000.0, "description": "Túi đeo chéo nhỏ gọn, phù hợp đi chơi.", "image_url": "https://picsum.photos/seed/502/400/400", "category": "Túi", "rating": 4.2, "stock": 50},
        {"name": "Túi Tote Canvas Unisex", "price": 250_000.0, "description": "Túi vải canvas rộng rãi, đa năng.", "image_url": "https://picsum.photos/seed/503/400/400", "category": "Túi", "rating": 4.0, "stock": 80},
        {"name": "Túi Xách Công Sở Cao Cấp", "price": 1_200_000.0, "description": "Túi da công sở thanh lịch, có ngăn laptop.", "image_url": "https://picsum.photos/seed/504/400/400", "category": "Túi", "rating": 4.7, "stock": 20},
        {"name": "Túi Clutch Dạ Tiệc", "price": 450_000.0, "description": "Túi cầm tay dạ tiệc, đính đá lấp lánh.", "image_url": "https://picsum.photos/seed/505/400/400", "category": "Túi", "rating": 4.3, "stock": 35},
        {"name": "Balo Thời Trang Nữ", "price": 380_000.0, "description": "Balo nhỏ thời trang, chống nước.", "image_url": "https://picsum.photos/seed/506/400/400", "category": "Túi", "rating": 4.1, "stock": 60},
        {"name": "Túi Bucket Thổ Cẩm", "price": 290_000.0, "description": "Túi bucket họa tiết thổ cẩm độc đáo.", "image_url": "https://picsum.photos/seed/507/400/400", "category": "Túi", "rating": 3.9, "stock": 45},
        {"name": "Túi Chain Bag Xích Kim Loại", "price": 550_000.0, "description": "Túi dây xích kim loại, phong cách Hàn Quốc.", "image_url": "https://picsum.photos/seed/508/400/400", "category": "Túi", "rating": 4.4, "stock": 25},
        {"name": "Túi Đeo Hông Fanny Pack", "price": 180_000.0, "description": "Túi đeo hông tiện lợi cho hoạt động ngoài trời.", "image_url": "https://picsum.photos/seed/509/400/400", "category": "Túi", "rating": 3.8, "stock": 70},
        {"name": "Túi Hộp Vuông PU Leather", "price": 420_000.0, "description": "Túi hộp vuông da PU sang trọng.", "image_url": "https://picsum.photos/seed/510/400/400", "category": "Túi", "rating": 4.2, "stock": 40},
        {"name": "Đồng Hồ Nam Dây Da Nâu", "price": 1_500_000.0, "description": "Đồng hồ cơ nam dây da nâu, mặt số trắng.", "image_url": "https://picsum.photos/seed/521/400/400", "category": "Đồng hồ", "rating": 4.6, "stock": 15},
        {"name": "Đồng Hồ Nữ Dây Kim Loại", "price": 980_000.0, "description": "Đồng hồ nữ dây kim loại vàng rose, mặt tròn nhỏ.", "image_url": "https://picsum.photos/seed/522/400/400", "category": "Đồng hồ", "rating": 4.4, "stock": 20},
        {"name": "Đồng Hồ Thông Minh Smartwatch", "price": 2_500_000.0, "description": "Smartwatch theo dõi sức khỏe, thông báo điện thoại.", "image_url": "https://picsum.photos/seed/523/400/400", "category": "Đồng hồ", "rating": 4.8, "stock": 10},
        {"name": "Đồng Hồ Đôi Couple", "price": 1_200_000.0, "description": "Set đồng hồ đôi nam nữ phong cách tối giản.", "image_url": "https://picsum.photos/seed/524/400/400", "category": "Đồng hồ", "rating": 4.3, "stock": 18},
        {"name": "Đồng Hồ Thể Thao Chống Nước", "price": 750_000.0, "description": "Đồng hồ thể thao chống nước 50m, dây silicone.", "image_url": "https://picsum.photos/seed/525/400/400", "category": "Đồng hồ", "rating": 4.2, "stock": 25},
        {"name": "Đồng Hồ Cơ Skeleton Lộ Máy", "price": 3_200_000.0, "description": "Đồng hồ cơ skeleton lộ máy, thiết kế nghệ thuật.", "image_url": "https://picsum.photos/seed/526/400/400", "category": "Đồng hồ", "rating": 4.7, "stock": 8},
        {"name": "Đồng Hồ Dạ Quang Vintage", "price": 650_000.0, "description": "Đồng hồ phong cách vintage, kim dạ quang.", "image_url": "https://picsum.photos/seed/527/400/400", "category": "Đồng hồ", "rating": 4.0, "stock": 30},
        {"name": "Váy Maxi Hoa Nhí Mùa Hè", "price": 380_000.0, "description": "Váy maxi dài hoa nhí nhẹ nhàng, mặc mùa hè.", "image_url": "https://picsum.photos/seed/531/400/400", "category": "Váy", "rating": 4.3, "stock": 45},
        {"name": "Váy Công Sở A-Line", "price": 450_000.0, "description": "Váy A-line công sở thanh lịch, chất liệu linen.", "image_url": "https://picsum.photos/seed/532/400/400", "category": "Váy", "rating": 4.5, "stock": 35},
        {"name": "Váy Len Ôm Body Mùa Đông", "price": 520_000.0, "description": "Váy len ôm body ấm áp phong cách Hàn Quốc.", "image_url": "https://picsum.photos/seed/533/400/400", "category": "Váy", "rating": 4.2, "stock": 40},
        {"name": "Quần Jean Skinny Nữ", "price": 350_000.0, "description": "Quần jean skinny ôm dáng, co giãn 4 chiều.", "image_url": "https://picsum.photos/seed/541/400/400", "category": "Quần", "rating": 4.4, "stock": 60},
        {"name": "Quần Tây Nam Công Sở", "price": 420_000.0, "description": "Quần tây nam mặc công sở, dáng slim fit.", "image_url": "https://picsum.photos/seed/542/400/400", "category": "Quần", "rating": 4.3, "stock": 40},
        {"name": "Giày Sneaker Trắng Unisex", "price": 650_000.0, "description": "Giày sneaker trắng cổ thấp, đế êm.", "image_url": "https://picsum.photos/seed/551/400/400", "category": "Giày", "rating": 4.6, "stock": 55},
        {"name": "Giày Cao Gót Mũi Nhọn", "price": 480_000.0, "description": "Giày cao gót 7cm mũi nhọn màu đen.", "image_url": "https://picsum.photos/seed/552/400/400", "category": "Giày", "rating": 4.2, "stock": 30},
        {"name": "Giày Sandal Đế Bằng", "price": 280_000.0, "description": "Giày sandal đế bằng thoáng mát mùa hè.", "image_url": "https://picsum.photos/seed/553/400/400", "category": "Giày", "rating": 4.0, "stock": 70},
    ]
    products.extend(extra_products)
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
        print("     - articles.csv  (khoang 35MB)")
        print("     - customers.csv (khoang 200MB)")
        print("  3. Giai nen va dat vao backend/data/")
        print("  4. Chay lai: python seed.py")
        return

    # --- Ket noi MongoDB ---
    print("[1/5] Ket noi MongoDB...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # --- Xoa du lieu cu ---
    print("[2/5] Xoa du lieu cu (products, users fake, interactions)...")
    await db["products"].delete_many({})
    await db["users"].delete_many({"role": "user"})   # giu admin neu co
    await db["interactions"].delete_many({})
    await db["carts"].delete_many({})

    # --- Doc va insert products ---
    print(f"[3/5] Doc {NUM_PRODUCTS} san pham tu articles.csv...")
    raw_products = read_articles(NUM_PRODUCTS)
    product_result = await db["products"].insert_many(raw_products)
    # Lay lai voi _id thuc te
    inserted_ids  = product_result.inserted_ids
    product_docs  = await db["products"].find(
        {"_id": {"$in": inserted_ids}}
    ).to_list(NUM_PRODUCTS)
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
