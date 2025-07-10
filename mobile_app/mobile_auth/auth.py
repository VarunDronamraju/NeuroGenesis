from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from pathlib import Path
import json
from sqlalchemy.orm import Session

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class MobileLogin(BaseModel):
    username: str
    password: str

class MobileAuth:
    async def mobile_login(self, user_id: str, login: MobileLogin, db: Session) -> Dict:
        log_path = Path("E:/Neurogenesis/mobile_logs") / user_id / f"login_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump({
                "username": login.username,
                "login_at": datetime.utcnow().isoformat()
            }, f)
        return {
            "user_id": user_id,
            "login_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/mobile/login")
async def mobile_login(login: MobileLogin, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    auth = MobileAuth()
    return await auth.mobile_login(user.id, login, db)
