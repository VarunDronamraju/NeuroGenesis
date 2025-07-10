from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from typing import Optional
from jose import jwt
from models import User

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    organization: Optional[str] = None
    bio: Optional[str] = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/profile")
async def update_profile(
    profile: UserProfileUpdate,
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="token")),
    db: Session = Depends(get_db)
):
    user = await get_current_user(token, db)
    if profile.full_name:
        user.full_name = profile.full_name
    if profile.organization:
        user.organization = profile.organization
    if profile.bio:
        user.bio = profile.bio
    db.commit()
    db.refresh(user)
    return {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "organization": user.organization,
        "bio": user.bio
    }

@app.get("/users/profile")
async def get_profile(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="token")),
    db: Session = Depends(get_db)
):
    user = await get_current_user(token, db)
    return {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "organization": user.organization,
        "bio": user.bio
    }