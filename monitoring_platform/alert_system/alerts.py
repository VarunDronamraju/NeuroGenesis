from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
import redis
import os
import json
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AlertCreate(BaseModel):
    resource_id: str
    resource_type: str
    message: str
    severity: str

class AlertSystem:
    def __init__(self):
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    async def create_alert(self, user_id: str, alert: AlertCreate) -> Dict:
        alert_id = f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.redis.publish(f"alerts:{user_id}", json.dumps({
            "alert_id": alert_id,
            "resource_id": alert.resource_id,
            "resource_type": alert.resource_type,
            "message": alert.message,
            "severity": alert.severity,
            "created_at": datetime.utcnow().isoformat()
        }))
        return {
            "alert_id": alert_id,
            "resource_id": alert.resource_id,
            "resource_type": alert.resource_type,
            "message": alert.message,
            "severity": alert.severity,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/alerts")
async def create_alert(
    alert: AlertCreate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    system = AlertSystem()
    return await system.create_alert(user.id, alert)
