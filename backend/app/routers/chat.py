"""
routers/chat.py
===============
POST /chat/  - AI Chatbot
  Priority: Groq (llama-3.3-70b) -> Gemini (fallback) -> Rule-based (final fallback)
"""

import os
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import re
from groq import AsyncGroq

from app.core.config import db

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


# ── Helper: Tim san pham theo tu khoa hoac danh muc ──────────
async def _search_products_for_context(query: str) -> list[dict]:
    """
    Tim toi da 5 san pham lien quan den query.
    Dung regex search tren name va category.
    """
    if not query or len(query.strip()) < 2:
        return []

    collection = db.get_db()["products"]

    # Trich xuat tu khoa don gian (bo stopwords tieng Viet)
    stopwords = {"cho", "toi", "ban", "co", "khong", "muon", "can", "tim", "mua", "gia"}
    words = [w for w in re.split(r"\s+", query.strip().lower()) if w not in stopwords and len(w) > 1]
    if not words:
        return []

    # Tao regex OR tu cac tu khoa
    pattern = "|".join(re.escape(w) for w in words[:5])

    cursor = collection.find(
        {"$or": [
            {"name": {"$regex": pattern, "$options": "i"}},
            {"category": {"$regex": pattern, "$options": "i"}},
            {"description": {"$regex": pattern, "$options": "i"}},
        ]},
        {"_id": 1, "name": 1, "price": 1, "category": 1, "image_url": 1, "rating": 1}
    ).limit(5)

    docs = await cursor.to_list(5)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


def _build_product_context(products: list[dict]) -> str:
    if not products:
        return ""
    lines = ["San pham lien quan trong cua hang:"]
    for p in products:
        price_str = f"{p.get('price', 0):,.0f}".replace(",", ".") + " VND"
        lines.append(f"- {p['name']} ({p.get('category', '')}) - {price_str}, danh gia: {p.get('rating', 0):.1f}/5")
    return "\n".join(lines)


# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """Ban la tro ly AI chuyen tu van mua sam thoi trang.
Ten ban la "ShopBot".
Nhiem vu cua ban:
- Tu van san pham thoi trang, phu kien, giay dep
- Giai dap thac mac ve don hang, giao hang, doi tra hang
- Goi y san pham phu hop voi nhu cau va ngan sach khach hang
- Luon tra loi bang tieng Viet, than thien va chuyen nghiep
- Neu co san pham lien quan duoc cung cap, hay de cap den chung cu the

Quy tac:
- Khong phat ngon ve chinh tri, ton giao
- Neu khach hoi gia, hay goi y kiem tra tren trang san pham
- Tra loi ngan gon, ro rang, toi da 3-4 cau tru khi duoc yeu cau chi tiet"""


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

    # Tim san pham lien quan
    related_products = await _search_products_for_context(request.message)
    product_context = _build_product_context(related_products)

    # Ghep context san pham vao message neu co
    user_content = request.message
    if product_context:
        user_content = f"{request.message}\n\n[Context]\n{product_context}"

    # Xay dung lich su hoi thoai (OpenAI-compatible format dung cho Groq)
    groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in (request.history or []):
        role = "user" if msg.role == "user" else "assistant"
        groq_messages.append({"role": role, "content": msg.content})
    groq_messages.append({"role": "user", "content": user_content})

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
            return ChatResponse(reply=reply_text, products=related_products)
        except Exception as e:
            err_str = str(e)
            if "rate_limit" not in err_str.lower() and "429" not in err_str and "quota" not in err_str.lower():
                raise HTTPException(status_code=500, detail=f"Loi Groq: {err_str[:200]}")
            # Het rate limit Groq -> thu Gemini

    # ── Thu Gemini thu hai (secondary) ──
    if gemini_key:
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
                gtypes.Content(role="user", parts=[gtypes.Part(text=user_content)])
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
            return ChatResponse(reply=reply_text, products=related_products)
        except Exception:
            pass  # Gemini that bai -> dung fallback

    # ── Rule-based fallback cuoi cung ──
    fallback = _fallback_response(request.message)
    return ChatResponse(reply=fallback, products=related_products)
