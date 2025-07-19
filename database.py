from pymongo import MongoClient
from datetime import datetime, timedelta
from config import config

class Database:
    def __init__(self):
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client[config.DB_NAME]
        self.users = self.db["users"]
        self.transactions = self.db["transactions"]

    def add_user(self, user_id: int, plan: str):
        expiry = {
            "weekly": datetime.now() + timedelta(days=7),
            "monthly": datetime.now() + timedelta(days=30),
            "yearly": datetime.now() + timedelta(days=365)
        }.get(plan, datetime.now() + timedelta(days=30))

        self.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "user_id": user_id,
                "plan": plan,
                "expiry_date": expiry,
                "joined_at": datetime.now()
            }},
            upsert=True
        )

    def check_expiry(self):
        expired_users = self.users.find({
            "expiry_date": {"$lt": datetime.now()}
        })
        return list(expired_users)
