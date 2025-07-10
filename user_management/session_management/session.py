from redis import Redis
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from jose import jwt
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

class SessionManager:
    def __init__(self):
        self.redis = Redis.from_url(REDIS_URL, decode_responses=True)

    async def create_session(self, user_id: str, token: str):
        session_key = f"session:{user_id}"
        self.redis.setex(
            session_key,
            timedelta(days=7),
            token
        )
        return session_key

    async def validate_session(self, user_id: str, token: str):
        session_key = f"session:{user_id}"
        stored_token = self.redis.get(session_key)
        if not stored_token or stored_token != token:
            raise HTTPException(status_code=401, detail="Invalid session")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def end_session(self, user_id: str):
        session_key = f"session:{user_id}"
        self.redis.delete(session_key)

    async def extend_session(self, user_id: str):
        session_key = f"session:{user_id}"
        if self.redis.exists(session_key):
            self.redis.expire(session_key, timedelta(days=7))