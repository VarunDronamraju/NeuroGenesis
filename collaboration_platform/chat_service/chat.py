from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ChatMessage(BaseModel):
    conversation_id: str
    content: str

class ChatService:
    def __init__(self):
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    async def send_message(self, user_id: str, message: ChatMessage) -> Dict:
        message_id = f"msg_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.redis.rpush(f"chat:{message.conversation_id}", json.dumps({
            "message_id": message_id,
            "user_id": user_id,
            "content": message.content,
            "timestamp": datetime.utcnow().isoformat()
        }))
        return {
            "message_id": message_id,
            "conversation_id": message.conversation_id,
            "content": message.content,
            "sent_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/chat")
async def send_message(message: ChatMessage, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    service = ChatService()
    return await service.send_message(user.id, message)
