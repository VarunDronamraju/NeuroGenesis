from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
import logging
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuditLog(BaseModel):
    action: str
    resource_id: str
    resource_type: str

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("AuditLogger")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("E:/Neurogenesis/logs/audit.log")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(handler)

    async def log_action(self, user_id: str, log: AuditLog):
        log_entry = f"User {user_id} performed {log.action} on {log.resource_type} {log.resource_id}"
        self.logger.info(log_entry)
        return {
            "log_id": f"log_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "action": log.action,
            "resource_id": log.resource_id,
            "resource_type": log.resource_type,
            "logged_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/audit/log")
async def log_action(log: AuditLog, token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    logger = AuditLogger()
    return await logger.log_action(user.id, log)
