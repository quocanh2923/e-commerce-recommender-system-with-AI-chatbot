import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

class Database:
    client: AsyncIOMotorClient = None

    def connect(self):
        mongo_url = os.getenv("MONGO_URL")
        if not mongo_url:
            print("❌ Lỗi: Chưa cấu hình MONGO_URL trong file .env")
            return
            
        self.client = AsyncIOMotorClient(mongo_url)
        print("✅ Đã kết nối tới MongoDB thành công!")

    def close(self):
        if self.client:
            self.client.close()
            print("🔒 Đã đóng kết nối MongoDB.")

    def get_db(self):
        db_name = os.getenv("DB_NAME", "test_db")
        return self.client[db_name]

db = Database()