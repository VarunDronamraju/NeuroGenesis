from fastapi import FastAPI, Depends, HTTPException
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

class CollaborationNotification(BaseModel):
    team_id: str
    message: str
    channel: str

class NotificationCollaboration:
    def __init__(self):
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    async def send_notification(self, user_id: str, notification: CollaborationNotification) -> Dict:
        notification_id = f"collab_notif_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.redis.publish(f"collab_notifications:{notification.team_id}", json.dumps({
            "notification_id": notification_id,
            "message": notification.message,
            "channel": notification.channel,
            "created_at": datetime.utcnow().isoformat()
        }))
        return {
            "notification_id": notification_id,
            "team_id": notification.team_id,
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

@app.post("/collab_notifications")
async def send_notification(notification: CollaborationNotification, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    collab = NotificationCollaboration()
    return await collab.send_notification(user.id, notification)
