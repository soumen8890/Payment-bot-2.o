import hashlib
import base64
import json
import requests
from config import config

class PhonePePayment:
    def __init__(self):
        self.base_url = "https://api.phonepe.com/apis/hermes"
        self.merchant_id = config.PHONEPE_MERCHANT_ID
        self.salt_key = config.PHONEPE_SALT_KEY
        self.salt_index = config.PHONEPE_SALT_INDEX

    def generate_payment_link(self, user_id: int, amount: int, plan: str):
        transaction_id = f"TXN{user_id}{int(datetime.now().timestamp())}"
        
        payload = {
            "merchantId": self.merchant_id,
            "merchantTransactionId": transaction_id,
            "amount": amount,
            "merchantUserId": str(user_id),
            "redirectUrl": f"https://yourdomain.com/callback?user_id={user_id}",
            "callbackUrl": f"https://yourdomain.com/callback?user_id={user_id}",
            "paymentInstrument": {"type": "PAY_PAGE"}
        }

        # Generate X-VERIFY header
        base64_payload = base64.b64encode(json.dumps(payload).encode()).decode()
        string_to_hash = f"{base64_payload}/pg/v1/pay{self.salt_key}"
        sha256_hash = hashlib.sha256(string_to_hash.encode()).hexdigest()
        checksum = f"{sha256_hash}###{self.salt_index}"

        headers = {"X-VERIFY": checksum, "Content-Type": "application/json"}
        
        response = requests.post(
            f"{self.base_url}/pg/v1/pay",
            headers=headers,
            json={"request": base64_payload}
        )
        
        return response.json().get("data", {}).get("instrumentResponse", {}).get("redirectInfo", {}).get("url")
