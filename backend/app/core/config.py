import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

class Database:
    client: AsyncIOMotorClient = None

    def connect(self):
        mongo_url = os.getenv("MONGO_URL")
        if not mongo_url:
            print("[ERROR] Chua cau hinh MONGO_URL trong file .env")
            return
            
        self.client = AsyncIOMotorClient(mongo_url)
        print("[OK] Da ket noi toi MongoDB thanh cong!")

    def close(self):
        if self.client:
            self.client.close()
            print("[OK] Da dong ket noi MongoDB.")

    def get_db(self):
        db_name = os.getenv("DB_NAME", "test_db")
        return self.client[db_name]

db = Database()