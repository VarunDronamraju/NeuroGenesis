from fastapi import FastAPI, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Notification
from typing import List
import redis
import json
import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class NotificationCreate(BaseModel):
    message: str
    recipient_id: int
    type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str, db: Session):
    from user_management.authentication.auth import get_current_user
    return await get_current_user(token, db)

def send_push_notification(user_id: str, message: str):
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.publish(f"notifications:{user_id}", json.dumps({"message": message}))

@app.post("/notifications")
async def create_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(token, db)
    db_notification = Notification(
        user_id=notification.recipient_id,
        message=notification.message,
        type=notification.type,
        sender_id=user.id
    )
    db.add(db_notification)
    db.commit()
    background_tasks.add_task(send_push_notification, str(notification.recipient_id), notification.message)
    return {"message": "Notification created"}

@app.get("/notifications")
async def get_notifications(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(token, db)
    notifications = db.query(Notification).filter(Notification.user_id == user.id).all()
    return [
        {
            "id": n.id,
            "message": n.message,
            "type": n.type,
            "created_at": n.created_at
        } for n in notifications
    ]