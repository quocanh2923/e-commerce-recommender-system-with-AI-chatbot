from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import db
# 👇 1. Import router sản phẩm
from app.routers import product
# 👇 Import router người dùng
from app.routers import user
# 👇 Import router hành vi
from app.routers import interaction 

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

# 👇 2. Gắn router vào ứng dụng
app.include_router(product.router, prefix="/products", tags=["products"])
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(interaction.router, prefix="/interactions", tags=["interactions"])

@app.get("/")
async def root():
    return {"message": "Xin chào! Backend đã kết nối Database ngon lành."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)