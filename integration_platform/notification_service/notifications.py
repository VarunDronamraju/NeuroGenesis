from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
import redis
from datetime import datetime
import os
from dotenv import load_dotenv
import json

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class NotificationCreate(BaseModel):
    recipient_id: str
    message: str
    channel: str  # e.g., "email", "in-app"

class NotificationService:
    def __init__(self):
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    async def send_notification(self, user_id: str, notification: NotificationCreate) -> Dict:
        notification_id = f"notif_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.redis.publish(f"notifications:{notification.recipient_id}", json.dumps({
            "notification_id": notification_id,
            "message": notification.message,
            "channel": notification.channel,
            "created_at": datetime.utcnow().isoformat()
        }))
        return {
            "notification_id": notification_id,
            "recipient_id": notification.recipient_id,
            "message": notification.message,
            "channel": notification.channel,
            "sent_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/notifications")
async def send_notification(
    notification: NotificationCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    service = NotificationService()
    return await service.send_notification(user.id, notification)
