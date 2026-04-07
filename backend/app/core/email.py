"""
app/core/email.py
=================
Gui email bat dong bo qua Gmail SMTP (App Password).
Dung smtplib stdlib + asyncio.to_thread → khong can thu vien ngoai.

Bien moi truong can trong .env:
    EMAIL_HOST     = smtp.gmail.com
    EMAIL_PORT     = 587
    EMAIL_USERNAME = your-email@gmail.com
    EMAIL_PASSWORD = xxxx xxxx xxxx xxxx   ← Gmail App Password (16 ky tu)
    EMAIL_FROM     = your-email@gmail.com  (co the giong EMAIL_USERNAME)
"""

import os
import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _send_email_sync(to: str, subject: str, html: str) -> None:
    """Ham dong bo gui email — chay trong thread rieng de khong block event loop."""
    host     = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    port     = int(os.getenv("EMAIL_PORT", "587"))
    username = os.getenv("EMAIL_USERNAME", "")
    password = os.getenv("EMAIL_PASSWORD", "")
    from_    = os.getenv("EMAIL_FROM", username)

    # Neu chua cau hinh thi bo qua (khong nem loi de khong gay crash chinh)
    if not username or not password:
        print(f"[EMAIL] Chua cau hinh EMAIL_USERNAME / EMAIL_PASSWORD — bo qua gui email toi {to}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"ShopAI <{from_}>"
    msg["To"]      = to
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(username, password)
            smtp.sendmail(from_, [to], msg.as_bytes())
        print(f"[EMAIL] Da gui email toi {to} — {subject}")
    except Exception as e:
        # Khong nen crash app vi email that bai
        print(f"[EMAIL] Loi gui email toi {to}: {e}")


async def send_email(to: str, subject: str, html: str) -> None:
    """Async wrapper — goi trong FastAPI ma khong block."""
    await asyncio.to_thread(_send_email_sync, to, subject, html)


# ─────────────────────────────────────────────────────────────
# Template 1: Xac nhan dat hang
# ─────────────────────────────────────────────────────────────
def build_order_confirmation_email(order: dict, username: str) -> str:
    """Tao noi dung HTML email xac nhan don hang."""
    order_code = order["_id"][-8:].upper()
    items_html = "".join(
        f"""<tr>
              <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0">{item['name']}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:center">×{item['quantity']}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right">
                {(item['price'] * item['quantity']):,.0f} ₫
              </td>
            </tr>"""
        for item in order.get("items", [])
    )

    addr = order.get("shipping_address", {})
    addr_text = f"{addr.get('full_name', '')} — {addr.get('phone', '')}<br>{addr.get('address', '')}"

    subtotal = order.get("subtotal", 0)
    shipping = order.get("shipping", 0)
    total    = order.get("total", 0)

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:20px;background:#f7f7f7;font-family:Arial,sans-serif">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08)">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px 28px;text-align:center">
      <h1 style="margin:0;color:#fff;font-size:24px">🛍️ ShopAI</h1>
      <p style="margin:8px 0 0;color:rgba(255,255,255,.85);font-size:15px">Order Confirmation</p>
    </div>

    <!-- Body -->
    <div style="padding:28px">
      <p style="margin:0 0 16px;color:#333;font-size:15px">
        Hi <strong>{username}</strong>, your order has been placed successfully!
      </p>

      <!-- Order ID -->
      <div style="background:#f3f0ff;border-radius:8px;padding:14px 18px;margin-bottom:20px">
        <span style="color:#6366f1;font-size:13px;font-weight:600">ORDER ID</span><br>
        <span style="font-size:20px;font-weight:700;color:#333">#{order_code}</span>
      </div>

      <!-- Items table -->
      <table style="width:100%;border-collapse:collapse;margin-bottom:16px">
        <thead>
          <tr style="background:#f8f8f8">
            <th style="padding:10px 12px;text-align:left;font-size:13px;color:#666">Product</th>
            <th style="padding:10px 12px;text-align:center;font-size:13px;color:#666">Qty</th>
            <th style="padding:10px 12px;text-align:right;font-size:13px;color:#666">Price</th>
          </tr>
        </thead>
        <tbody>{items_html}</tbody>
      </table>

      <!-- Summary -->
      <div style="border-top:2px solid #f0f0f0;padding-top:14px">
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;display:table;width:100%">
          <span style="display:table-cell;color:#666;font-size:14px">Subtotal</span>
          <span style="display:table-cell;text-align:right;font-size:14px">{subtotal:,.0f} ₫</span>
        </div>
        <div style="display:table;width:100%;margin-bottom:10px">
          <span style="display:table-cell;color:#666;font-size:14px">Shipping</span>
          <span style="display:table-cell;text-align:right;font-size:14px">{shipping:,.0f} ₫</span>
        </div>
        <div style="display:table;width:100%;border-top:1px solid #e0e0e0;padding-top:10px">
          <span style="display:table-cell;font-weight:700;font-size:16px">Total</span>
          <span style="display:table-cell;text-align:right;font-weight:700;font-size:18px;color:#e74c3c">{total:,.0f} ₫</span>
        </div>
      </div>

      <!-- Shipping address -->
      <div style="background:#f8f7ff;border:1px solid #ede9fe;border-radius:8px;padding:14px 18px;margin-top:20px">
        <p style="margin:0 0 6px;font-size:13px;font-weight:700;color:#7c3aed">📦 SHIPPING ADDRESS</p>
        <p style="margin:0;font-size:14px;color:#333;line-height:1.6">{addr_text}</p>
      </div>

      <p style="margin:24px 0 0;font-size:14px;color:#666">
        We will process your order as soon as possible. You can track the status in the
        <a href="http://localhost:5173/orders" style="color:#6366f1">My Orders</a> page.
      </p>
    </div>

    <!-- Footer -->
    <div style="background:#f8f8f8;padding:16px 28px;text-align:center">
      <p style="margin:0;font-size:12px;color:#999">© 2026 ShopAI — Thank you for shopping with us!</p>
    </div>
  </div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# Template 2: Cap nhat trang thai don hang
# ─────────────────────────────────────────────────────────────
STATUS_INFO = {
    "pending":    {"label": "Pending",    "icon": "⏳", "color": "#f59e0b", "desc": "Your order is awaiting confirmation."},
    "processing": {"label": "Processing", "icon": "⚙️",  "color": "#3b82f6", "desc": "We are preparing your order."},
    "shipped":    {"label": "Shipped",    "icon": "🚚", "color": "#8b5cf6", "desc": "Your order is on its way!"},
    "delivered":  {"label": "Delivered",  "icon": "✅", "color": "#10b981", "desc": "Your order has been delivered. Enjoy!"},
    "cancelled":  {"label": "Cancelled",  "icon": "❌", "color": "#ef4444", "desc": "Your order has been cancelled."},
}

def build_status_update_email(order: dict, username: str, new_status: str) -> str:
    """Tao noi dung HTML email khi trang thai don hang thay doi."""
    order_code = order["_id"][-8:].upper()
    info = STATUS_INFO.get(new_status, {"label": new_status, "icon": "📦", "color": "#6366f1", "desc": ""})
    total = order.get("total", 0)

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:20px;background:#f7f7f7;font-family:Arial,sans-serif">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08)">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px 28px;text-align:center">
      <h1 style="margin:0;color:#fff;font-size:24px">🛍️ ShopAI</h1>
      <p style="margin:8px 0 0;color:rgba(255,255,255,.85);font-size:15px">Order Status Update</p>
    </div>

    <!-- Body -->
    <div style="padding:28px">
      <p style="margin:0 0 20px;color:#333;font-size:15px">
        Hi <strong>{username}</strong>, there is an update to your order.
      </p>

      <!-- Order ID -->
      <div style="background:#f3f0ff;border-radius:8px;padding:14px 18px;margin-bottom:20px">
        <span style="color:#6366f1;font-size:13px;font-weight:600">ORDER ID</span><br>
        <span style="font-size:20px;font-weight:700;color:#333">#{order_code}</span>
      </div>

      <!-- Status badge -->
      <div style="text-align:center;padding:24px 0">
        <span style="font-size:40px">{info['icon']}</span>
        <div style="margin-top:10px">
          <span style="display:inline-block;background:{info['color']}20;color:{info['color']};
                       font-weight:700;font-size:18px;padding:8px 24px;border-radius:20px;
                       border:2px solid {info['color']}">
            {info['label']}
          </span>
        </div>
        <p style="margin:14px 0 0;color:#666;font-size:14px">{info['desc']}</p>
      </div>

      <!-- Total -->
      <div style="background:#f8f8f8;border-radius:8px;padding:14px 18px;text-align:center">
        <span style="color:#666;font-size:13px">Order Total: </span>
        <span style="font-weight:700;font-size:16px;color:#333">{total:,.0f} ₫</span>
      </div>

      <p style="margin:24px 0 0;font-size:14px;color:#666">
        Track your order at:
        <a href="http://localhost:5173/orders/{order['_id']}" style="color:#6366f1">
          View Order Details →
        </a>
      </p>
    </div>

    <!-- Footer -->
    <div style="background:#f8f8f8;padding:16px 28px;text-align:center">
      <p style="margin:0;font-size:12px;color:#999">© 2026 ShopAI — Thank you for shopping with us!</p>
    </div>
  </div>
</body>
</html>"""
