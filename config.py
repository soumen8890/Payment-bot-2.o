import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        # Telegram Configuration
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")  # From @BotFather
        self.API_ID = int(os.getenv("API_ID"))   # From my.telegram.org
        self.API_HASH = os.getenv("API_HASH")    # From my.telegram.org
        
        # MongoDB Configuration
        self.MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.DB_NAME = os.getenv("DB_NAME", "PremiumBotDB")
        
        # PhonePe Payment Gateway
        self.PHONEPE_MERCHANT_ID = os.getenv("PHONEPE_MERCHANT_ID")
        self.PHONEPE_SALT_KEY = os.getenv("PHONEPE_SALT_KEY")
        self.PHONEPE_SALT_INDEX = int(os.getenv("PHONEPE_SALT_INDEX", 1))
        
        # Pricing Plans (in paise)
        self.PLANS = {
            "weekly": 300,    # ₹3
            "monthly": 1000,  # ₹10
            "yearly": 9900    # ₹99
        }
        
        # Group Management
        self.PREMIUM_GROUP_ID = int(os.getenv("PREMIUM_GROUP_ID", -1001234567890))
        self.PREMIUM_GROUP_LINK = os.getenv("PREMIUM_GROUP_LINK", "https://t.me/your_group")
        
        # Owner ID
        self.OWNER_ID = int(os.getenv("OWNER_ID", 123456789))

config = Config()
