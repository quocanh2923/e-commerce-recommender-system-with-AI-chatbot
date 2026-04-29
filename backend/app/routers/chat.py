"""
routers/chat.py
===============
POST /chat/  - AI Chatbot
  Priority: Groq (llama-3.3-70b) -> Gemini (fallback) -> Rule-based (final fallback)
"""

import os
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import re
from groq import AsyncGroq

from app.core.config import db

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[list[ChatMessage]] = []


class ChatResponse(BaseModel):
    reply: str
    products: Optional[list[dict]] = []


# ── Helper: Tim san pham theo ten va danh muc ─────────────────
#
# Categories trong DB:
#   - H&M-derived (300sp): tieng Viet (Áo, Quần, Giày, Phụ kiện,
#     Đồ lót, Đồ bơi, Vớ - xem CATEGORY_MAP trong seed.py)
#   - Extras (25sp): tieng Anh (Bags, Watches, Dresses, Bottoms, Shoes)
# Moi keyword cluster trả về CA HAI dang để query khớp được cả hai.

_VI_TO_EN_CAT: list[tuple[list[str], list[str]]] = [
    # Tops – chi ao mac tren nguoi
    (["áo phông", "áo thun", "áo sơ mi", "áo linen", "áo hoodie",
      "áo blazer", "áo tank", "áo khoác", "áo len", "áo công sở",
      "áo nam", "áo nữ", "hoodie", "blouse", "tanktop", "sweater"],
     ["Áo", "Tops"]),

    # Bottoms – quan
    (["quần jeans", "quần tây", "quần short", "quần thể thao",
      "quần leggings", "quần jogger", "quần âu", "quần kaki",
      "quần nam", "quần nữ",
      "jeans", "leggings", "jogger", "trousers", "shorts"],
     ["Quần", "Bottoms"]),

    # Dresses – vay, dam (rieng, khong trung Tops)
    (["váy", "đầm", "chân váy", "váy maxi", "váy công sở",
      "váy hoa", "váy ngắn", "váy dài", "đầm dạ hội",
      "đầm maxi", "đầm hoa", "đầm dự tiệc",
      "dress", "skirt", "maxi dress"],
     ["Váy", "Dresses"]),

    # Shoes – giay, dep
    (["giày", "dép", "sandal", "sneaker", "boot",
      "giày thể thao", "giày cao gót", "giày tây", "giày sandal",
      "giày nữ", "giày nam", "giày bệt", "giày lười",
      "chelsea", "loafer", "heels", "giầy"],
     ["Giày", "Shoes"]),

    # Bags – tui, balo, vi
    (["túi", "balo", "túi xách", "túi đeo vai", "túi đeo chéo",
      "túi clutch", "túi tote", "ví", "bóp", "túi du lịch",
      "bag", "backpack", "handbag", "tote", "clutch",
      "fanny pack", "bucket bag", "wallet"],
     ["Túi", "Bags"]),

    # Accessories – phu kien (bao gom dong ho, vong, vi, that lung, mu, kinh,
    # khan, kep toc...) - H&M dataset khong co category Watches rieng
    (["phụ kiện", "kẹp tóc", "thắt lưng", "băng đô", "khăn quàng",
      "kính mắt", "kính râm", "mũ", "nón", "khăn",
      "đồng hồ", "smartwatch", "watch", "watches",
      "necklace", "bracelet", "belt", "claw", "headband",
      "scarf", "sunglasses", "hat", "cap", "ring"],
     ["Phụ kiện", "Accessories"]),

    # Swimwear – do boi
    (["đồ bơi", "áo tắm", "bikini", "đi biển", "tắm biển",
      "bơi lội", "đồ tắm", "bộ bơi",
      "swimwear", "swimsuit", "bikini set"],
     ["Đồ bơi", "Swimwear"]),

    # Socks – tat, vo
    (["tất", "vớ", "tất chân", "vớ chân", "tất cao cổ",
      "quần tất", "tất thể thao",
      "socks", "stockings", "tights"],
     ["Vớ", "Socks"]),

    # Underwear – do lot, do ngu
    (["đồ lót", "đồ ngủ", "nội y", "quần lót", "áo ngực",
      "pyjama", "bra",
      "underwear", "lingerie", "bralette", "pyjamas"],
     ["Đồ lót", "Underwear"]),
]


def _word_match(keyword: str, text: str) -> bool:
    """Kiem tra keyword co xuat hien trong text duoi dang tu doc lap.
    Da tu: phrase match. Don tu: word boundary match.
    """
    if " " in keyword:
        return keyword in text
    # Boundary: khong lien ke voi chu cai tien Viet hoac Latin
    boundary = r'(?<![^\s,\.!?;:()\-])'
    return bool(re.search(boundary + re.escape(keyword) + r'(?![^\s,\.!?;:()\-])', text))


async def _search_products(user_msg: str, ai_reply: str) -> list[dict]:
    """
    Tim san pham theo category va ten san pham.
    Uu tien keyword trong user_msg hon ai_reply.
    Fallback: san pham rating cao nhat.
    """
    user_lower = user_msg.lower().strip()
    reply_lower = ai_reply.lower().strip()
    collection = db.get_db()["products"]

    # 1. Tim category tu user_msg truoc
    matched_categories: set[str] = set()
    for keywords, cats in _VI_TO_EN_CAT:
        if any(_word_match(kw, user_lower) for kw in keywords):
            matched_categories.update(cats)

    # 2. Neu chua tim duoc thi moi xet ai_reply
    if not matched_categories:
        for keywords, cats in _VI_TO_EN_CAT:
            if any(_word_match(kw, reply_lower) for kw in keywords):
                matched_categories.update(cats)

    # 3. Neu khong co category, tim tu tieng Anh thuan tu USER MSG
    #    de match ten san pham. KHONG dung tu reply (de tranh nhieu
    #    tu tieng Viet khong dau bi nham la tu tieng Anh).
    stopwords = {
        # tieng Anh thong dung
        "the", "and", "for", "with", "you", "can", "our", "are", "this",
        "that", "have", "will", "your", "from", "they", "what", "when",
        "how", "also", "some", "more", "very", "well", "not", "but",
        "like", "than", "here", "just", "want", "need", "show", "give",
        "find", "look", "tell", "know", "make", "take", "good", "best",
        # tieng Viet khong dau (tranh nham la English) - cac tu pho bien
        "thanh", "danh", "trang", "theo", "sach", "giao", "phai", "minh",
        "ban", "toi", "shop", "shopbot", "suggest", "recommend",
    }

    # 4. Build MongoDB query - strict: uu tien category neu co
    query: dict | None = None
    if matched_categories:
        query = {"category": {"$in": list(matched_categories)}}
    else:
        en_words = [
            w.strip(".,!?:;\"'*()-")
            for w in re.split(r"\s+", user_lower)
            if re.match(r'^[a-z]{4,}$', w.strip(".,!?:;\"'*()-"))
            and w.strip(".,!?:;\"'*()-") not in stopwords
        ]
        if en_words:
            words_sorted = sorted(set(en_words), key=len, reverse=True)[:3]
            name_pattern = "|".join(re.escape(w) for w in words_sorted)
            query = {"name": {"$regex": name_pattern, "$options": "i"}}

    if query is not None:
        cursor = collection.find(
            query,
            {"_id": 1, "name": 1, "price": 1, "category": 1, "image_url": 1, "rating": 1}
        ).sort("rating", -1).limit(4)
        docs = await cursor.to_list(4)
        if docs:
            for d in docs:
                d["_id"] = str(d["_id"])
            return docs

    # 5. Fallback: san pham duoc danh gia cao nhat
    cursor = collection.find(
        {},
        {"_id": 1, "name": 1, "price": 1, "category": 1, "image_url": 1, "rating": 1}
    ).sort("rating", -1).limit(4)
    docs = await cursor.to_list(4)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs




# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """Ban la tro ly AI chuyen tu van mua sam thoi trang.
Ten ban la "ShopBot".
Nhiem vu cua ban:
- Tu van san pham thoi trang, phu kien, giay dep
- Giai dap thac mac ve don hang, giao hang, doi tra hang
- Goi y san pham phu hop voi nhu cau va ngan sach khach hang
- Luon tra loi bang tieng Viet, than thien va chuyen nghiep

Quy tac:
- Khong phat ngon ve chinh tri, ton giao
- Neu khach hoi gia, hay goi y kiem tra tren trang san pham
- Tra loi ngan gon, ro rang, toi da 3-4 cau
- Chi goi y dung loai san pham khach dang hoi, KHONG goi y san pham khac loai
- Vi du: khach hoi ao thi chi goi y ao, khach hoi khan thi chi goi y khan"""


# ── Fallback khi Gemini khong kha dung ───────────────────────
_FALLBACK_RULES = [
    (["ao", "shirt", "blouse", "thun", "somi"], "Chúng tôi có nhiều mẫu áo đẹp! Bạn có thể vào trang Sản phẩm và lọc theo danh mục 'Áo' để xem toàn bộ. Có mẫu nào bạn quan tâm về màu sắc hoặc phong cách không?"),
    (["quan", "jeans", "trouser", "short"], "Bạn muốn tìm quần? Chúng tôi có quần jeans, quần tây, quần short đa dạng. Vào mục Sản phẩm → lọc 'Quần' để xem nhé!"),
    (["giay", "sneaker", "boot", "sandal", "dep"], "Chúng tôi có nhiều dòng giày thể thao và giày thời trang. Ghé mục Sản phẩm → lọc 'Giày' để xem các mẫu mới nhất!"),
    (["vay", "dam", "dress", "skirt"], "Bộ sưu tập váy đầm của chúng tôi rất đa dạng! Tìm trong danh mục 'Váy' hoặc 'Đầm' trên trang sản phẩm nhé."),
    (["tui", "bag", "balo", "backpack", "clutch"], "Chúng tôi có túi xách, balo, clutch nhiều mẫu đẹp. Xem tại danh mục 'Túi' trên trang sản phẩm!"),
    (["dong ho", "watch"], "Xem các mẫu đồng hồ thời trang tại danh mục 'Đồng hồ' trên trang sản phẩm nhé!"),
    (["gia", "price", "bao nhieu", "cost"], "Giá sản phẩm được hiển thị trực tiếp trên trang sản phẩm. Bạn có thể dùng bộ lọc giá ở trang danh sách để tìm sản phẩm phù hợp ngân sách!"),
    (["giao hang", "delivery", "ship", "van chuyen"], "Chúng tôi giao hàng toàn quốc. Thời gian giao hàng từ 2-5 ngày làm việc. Đơn hàng trên 500.000đ được miễn phí ship!"),
    (["doi tra", "return", "hoan tien", "refund"], "Chính sách đổi trả: trong vòng 7 ngày nếu sản phẩm lỗi. Liên hệ hotline để được hỗ trợ đổi trả nhanh nhất!"),
    (["don hang", "order", "trang thai"], "Bạn có thể theo dõi đơn hàng trong mục 'Đơn mua' sau khi đăng nhập. Nếu cần hỗ trợ thêm, hãy liên hệ hotline nhé!"),
    (["khuyen mai", "sale", "giam gia", "discount"], "Các chương trình khuyến mãi được cập nhật thường xuyên. Theo dõi trang chủ để không bỏ lỡ ưu đãi!"),
    (["da hoi", "formal", "trang trong", "su kien"], "Cho dạ hội/sự kiện trang trọng, tôi gợi ý bạn xem danh mục Váy đầm hoặc tìm từ khóa 'formal' trên trang sản phẩm. Chọn màu tối hoặc pastel sẽ rất phù hợp!"),
    (["di bien", "beach", "bo bien", "he"], "Cho chuyến đi biển, bạn cần: áo phông thoáng mát, quần short, dép sandal và kính mát! Xem các danh mục tương ứng trên trang sản phẩm nhé."),
    (["the thao", "sport", "gym", "chay bo"], "Cho thể thao/gym, chúng tôi có áo thun thể thao, quần legging, giày sneaker chuyên dụng. Tìm trong danh mục tương ứng!"),
]

def _fallback_response(message: str) -> str:
    """Tra loi don gian khi Gemini khong kha dung."""
    import unicodedata
    msg_lower = message.lower()
    # Bo dau tieng Viet: NFD + xoa combining marks + thay d-gach
    msg_no_accent = "".join(
        c for c in unicodedata.normalize("NFD", msg_lower)
        if unicodedata.category(c) != "Mn"
    ).replace("đ", "d").replace("Đ", "D")

    for keywords, response in _FALLBACK_RULES:
        if any(re.search(r'\b' + re.escape(kw) + r'\b', msg_no_accent) for kw in keywords):
            return response

    # Default
    return ("Xin chào! Tôi là ShopBot 🤖 Hiện tại tôi đang hoạt động ở chế độ giới hạn. "
            "Bạn có thể:\n"
            "• Tìm sản phẩm qua thanh tìm kiếm ở trên\n"
            "• Lọc theo danh mục trên trang Sản phẩm\n"
            "• Hoặc hỏi tôi về: áo, quần, giày, váy, túi, chính sách đổi trả, giao hàng!")


# ── Endpoint ──────────────────────────────────────────────────
@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not groq_key and not gemini_key:
        raise HTTPException(status_code=503, detail="Chua cau hinh API key (GROQ_API_KEY hoac GEMINI_API_KEY)")

    # Xay dung lich su hoi thoai (KHONG inject san pham vao prompt)
    groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in (request.history or []):
        role = "user" if msg.role == "user" else "assistant"
        groq_messages.append({"role": role, "content": msg.content})
    groq_messages.append({"role": "user", "content": request.message})

    reply_text = None

    # ── Thu Groq truoc (primary) ──
    if groq_key:
        try:
            client = AsyncGroq(api_key=groq_key)
            completion = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=groq_messages,
                max_tokens=512,
                temperature=0.7,
            )
            reply_text = completion.choices[0].message.content or "Xin loi, toi khong the tra loi."
        except Exception as e:
            logger.warning("Groq API failed: %s: %s", type(e).__name__, e)

    # ── Thu Gemini thu hai (secondary) ──
    if reply_text is None and gemini_key:
        try:
            from google import genai as gai
            from google.genai import types as gtypes
            gclient = gai.Client(api_key=gemini_key)
            history_contents = []
            for msg in (request.history or []):
                role = "user" if msg.role == "user" else "model"
                history_contents.append(
                    gtypes.Content(role=role, parts=[gtypes.Part(text=msg.content)])
                )
            contents = history_contents + [
                gtypes.Content(role="user", parts=[gtypes.Part(text=request.message)])
            ]
            response = gclient.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=gtypes.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=512,
                    temperature=0.7,
                )
            )
            reply_text = response.text or "Xin loi, toi khong the tra loi."
        except Exception as e:
            logger.warning("Gemini API failed: %s: %s", type(e).__name__, e)

    # ── Rule-based fallback cuoi cung ──
    if reply_text is None:
        logger.warning("All AI providers failed - using rule-based fallback")
        reply_text = _fallback_response(request.message)

    # Tim san pham dua tren user message VA AI reply
    related_products = await _search_products(request.message, reply_text)
    return ChatResponse(reply=reply_text, products=related_products)


@router.get("/debug-search")
async def debug_search(msg: str = "", reply: str = ""):
    """Endpoint debug: test _search_products truc tiep."""
    combined = f"{msg} {reply}".lower().strip()
    matched_cats = set()
    for keywords, cats in _VI_TO_EN_CAT:
        for kw in keywords:
            if _word_match(kw, combined):
                matched_cats.update(cats)
                break
    products = await _search_products(msg, reply)
    return {
        "combined_preview": combined[:300],
        "matched_categories": list(matched_cats),
        "products": [{"name": p["name"], "category": p["category"]} for p in products],
    }
