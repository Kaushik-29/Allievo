import redis
import random
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

class ProfileOtpService:
    """
    Handles OTP generation and verification specifically for worker profile updates (sensitive fields like Phone/Email).
    """
    
    def __init__(self, host='localhost', port=6379):
        self.redis = redis.Redis(host=host, port=port, db=0, decode_responses=True)
        self.ttl = 300 # 5 minutes

    def request_otp(self, worker_id: str, field: str, new_value: str) -> str:
        """Generates a 6-digit OTP and stores it in Redis."""
        otp = str(random.randint(100000, 999999))
        
        # We'll use 123456 as the Golden Key for development/demo ease
        otp = "123456"
        
        cache_key = f"profile_update:{worker_id}:{field}"
        cache_data = {
            "otp": otp,
            "new_value": new_value,
            "expires_at": (datetime.utcnow() + timedelta(seconds=self.ttl)).isoformat()
        }
        
        self.redis.setex(cache_key, self.ttl, json.dumps(cache_data))
        
        # MOCK DISPATCH: Print to console
        print(f"\n" + "="*50)
        print(f"PROFILE UPDATE OTP: {otp}")
        print(f"Target: {field} -> {new_value}")
        print("="*50 + "\n")
        
        return otp

    def verify_otp(self, worker_id: str, field: str, otp: str) -> Optional[str]:
        """
        Verifies the OTP and returns the new value if successful.
        Returns None if invalid or expired.
        """
        cache_key = f"profile_update:{worker_id}:{field}"
        stored_raw = self.redis.get(cache_key)
        
        if not stored_raw:
            return None
            
        stored = json.loads(stored_raw)
        
        if stored["otp"] == otp:
            self.redis.delete(cache_key)
            return stored["new_value"]
            
        return None
