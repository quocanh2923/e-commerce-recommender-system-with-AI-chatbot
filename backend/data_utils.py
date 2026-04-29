"""
data_utils.py
=============
Logic phan loai san pham H&M dung chung cho seed.py va download_hm_images.py.

Mapping dung product_type_name (chi tiet) lam chinh, fallback sang
product_group_name. Khong dung garment_group_name vi nhieu san pham
bi gan nham nhom (vi du Connor pants -> Jersey Basic -> Áo).
"""

from pathlib import Path

DATA_DIR     = Path(__file__).parent / "data"
ARTICLES_CSV = DATA_DIR / "articles.csv"
IMG_DIR      = DATA_DIR / "images"

# Cac category trong DB (tieng Viet, dong bo voi chat.py va frontend)
CATEGORIES = [
    "Áo", "Quần", "Váy", "Giày", "Túi",
    "Phụ kiện", "Đồ lót", "Đồ bơi", "Vớ",
]

PER_CATEGORY = 30  # so san pham target moi category


PRODUCT_TYPE_TO_CATEGORY: dict[str, str] = {
    # --- Áo (Tops) ---
    "T-shirt": "Áo", "Top": "Áo", "Vest top": "Áo",
    "Blouse": "Áo", "Shirt": "Áo", "Polo shirt": "Áo",
    "Sweater": "Áo", "Cardigan": "Áo", "Hoodie": "Áo",
    "Jacket": "Áo", "Coat": "Áo", "Blazer": "Áo",
    "Bodysuit": "Áo", "Tailored Waistcoat": "Áo",

    # --- Quần (Bottoms) ---
    "Trousers": "Quần", "Shorts": "Quần",
    "Leggings/Tights": "Quần",

    # --- Váy (Dresses + Skirts + Jumpsuits) ---
    "Dress": "Váy", "Skirt": "Váy",
    "Jumpsuit/Playsuit": "Váy", "Dungarees": "Váy",
    "Garment Set": "Váy",

    # --- Giày (Shoes) ---
    "Sneakers": "Giày", "Boots": "Giày", "Sandals": "Giày",
    "Ballerinas": "Giày", "Slippers": "Giày", "Other shoe": "Giày",
    "Heels": "Giày", "Flat shoe": "Giày", "Flip flop": "Giày",
    "Pumps": "Giày", "Wedge": "Giày", "Heeled sandals": "Giày",

    # --- Túi (Bags) ---
    "Bag": "Túi", "Backpack": "Túi",

    # --- Đồ lót (Underwear/Nightwear) ---
    "Underwear bottom": "Đồ lót", "Bra": "Đồ lót",
    "Underwear set": "Đồ lót", "Underwear body": "Đồ lót",
    "Pyjama set": "Đồ lót", "Pyjama jumpsuit/playsuit": "Đồ lót",
    "Nightgown": "Đồ lót", "Robe": "Đồ lót",
    "Long John": "Đồ lót", "Sleep Bag": "Đồ lót",
    "Underdress": "Đồ lót",

    # --- Đồ bơi (Swimwear) ---
    "Swimwear bottom": "Đồ bơi", "Bikini top": "Đồ bơi",
    "Swimsuit": "Đồ bơi", "Swimwear set": "Đồ bơi",
    "Swimwear top": "Đồ bơi",

    # --- Vớ (Socks & Tights) ---
    "Socks": "Vớ", "Underwear Tights": "Vớ", "Leg warmers": "Vớ",

    # --- Phụ kiện (Accessories) ---
    "Hat/beanie": "Phụ kiện", "Earring": "Phụ kiện",
    "Other accessories": "Phụ kiện", "Scarf": "Phụ kiện",
    "Hair/alice band": "Phụ kiện", "Sunglasses": "Phụ kiện",
    "Necklace": "Phụ kiện", "Cap/peaked": "Phụ kiện",
    "Belt": "Phụ kiện", "Hat/brim": "Phụ kiện",
    "Gloves": "Phụ kiện", "Hair clip": "Phụ kiện",
    "Ring": "Phụ kiện", "Bracelet": "Phụ kiện",
    "Tie": "Phụ kiện", "Other Hair clip": "Phụ kiện",
    "Hair string": "Phụ kiện", "Hair ties": "Phụ kiện",
    "Watch": "Phụ kiện", "Wallet": "Phụ kiện",
    "Bumbag": "Phụ kiện", "Umbrella": "Phụ kiện",
    "Hairband": "Phụ kiện",
}


PRODUCT_GROUP_TO_CATEGORY: dict[str, str] = {
    # Fallback khi product_type_name khong co trong mapping above.
    # KHONG bao gom 'Accessories' o day - de cho Bag/Belt/Sunglasses
    # phan loai chinh xac qua product_type_name.
    "Garment Upper body": "Áo",
    "Garment Lower body": "Quần",
    "Garment Full body":  "Váy",
    "Underwear":          "Đồ lót",
    "Underwear/nightwear":"Đồ lót",
    "Nightwear":          "Đồ lót",
    "Shoes":              "Giày",
    "Swimwear":           "Đồ bơi",
    "Socks & Tights":     "Vớ",
}


def categorize_article(row: dict) -> str | None:
    """
    Tra ve category VN cho 1 dong articles.csv, hoac None neu khong
    nam trong scope (vd Cosmetic, Furniture, Stationery).
    """
    pt = row.get("product_type_name", "").strip()
    if pt in PRODUCT_TYPE_TO_CATEGORY:
        return PRODUCT_TYPE_TO_CATEGORY[pt]
    pg = row.get("product_group_name", "").strip()
    return PRODUCT_GROUP_TO_CATEGORY.get(pg)


def article_image_path(article_id: str) -> Path:
    """Duong dan local cho anh san pham."""
    return IMG_DIR / article_id[:3] / f"{article_id}.jpg"
