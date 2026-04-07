from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from app.core.config import db
from app.routers import product
from app.routers import user
from app.routers import interaction
from app.routers import cart
from app.routers import order
from app.routers import recommend
from app.routers import chat
from app.routers import admin
from app.routers import notification
from app.routers import paypal

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        db.connect()
        yield
    finally:
        db.close()

app = FastAPI(title="Shop AI Backend", version="1.0.0", lifespan=lifespan)

# 👇 CORS – cho phép frontend React gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👇 Gắn router vào ứng dụng
app.include_router(product.router, prefix="/products", tags=["products"])
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(interaction.router, prefix="/interactions", tags=["interactions"])
app.include_router(cart.router, prefix="/cart", tags=["cart"])
app.include_router(order.router, prefix="/orders", tags=["orders"])
app.include_router(recommend.router, prefix="/recommend", tags=["recommend"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(notification.router, prefix="/notifications", tags=["notifications"])
app.include_router(paypal.router, prefix="/paypal", tags=["paypal"])

# Serve uploaded images
_upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(_upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_upload_dir), name="uploads")

@app.get("/")
async def root():
    return {"message": "Xin chào! Backend đã kết nối Database ngon lành."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)