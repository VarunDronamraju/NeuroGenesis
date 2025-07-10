from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

class RoleAssignment(BaseModel):
    user_id: str
    role: str

class AuthManager:
    async def assign_role(self, current_user_id: str, assignment: RoleAssignment, db):
        from user_management.models import User
        user = db.query(User).filter(User.id == assignment.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.role = assignment.role
        db.commit()
        return {
            "user_id": assignment.user_id,
            "role": assignment.role,
            "assigned_at": datetime.utcnow()
        }

    async def generate_token(self, user_id: str) -> Dict:
        payload = {"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=24)}
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return {"token": token}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/auth/assign_role")
async def assign_role(assignment: RoleAssignment, token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    manager = AuthManager()
    return await manager.assign_role(user.id, assignment, db)

@app.post("/auth/token")
async def generate_token(user_id: str, db=Depends(get_db)):
    manager = AuthManager()
    return await manager.generate_token(user_id)
