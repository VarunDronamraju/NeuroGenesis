from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

load_dotenv()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class SecurityCheck(BaseModel):
    resource_id: str
    resource_type: str

class SecurityMonitor:
    def __init__(self):
        self.logger = logging.getLogger("SecurityMonitor")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("E:/Neurogenesis/logs/security.log")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(handler)

    async def check_security(self, user_id: str, check: SecurityCheck) -> Dict:
        status = "secure" if hash(user_id + check.resource_id) % 2 == 0 else "issue_detected"
        self.logger.info(f"Security check for {check.resource_type} {check.resource_id} by {user_id}: {status}")
        return {
            "check_id": f"check_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "resource_id": check.resource_id,
            "resource_type": check.resource_type,
            "status": status,
            "checked_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/security/check")
async def check_security(
    check: SecurityCheck,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    monitor = SecurityMonitor()
    return await monitor.check_security(user.id, check)
