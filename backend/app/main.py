from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import db
# 👇 1. Import router sản phẩm
from app.routers import product 

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        db.connect()
        yield
    finally:
        db.close()

app = FastAPI(title="Shop AI Backend", version="1.0.0", lifespan=lifespan)

# 👇 2. Gắn router vào ứng dụng
app.include_router(product.router, prefix="/products", tags=["products"])

@app.get("/")
async def root():
    return {"message": "Xin chào! Backend đã kết nối Database ngon lành."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)