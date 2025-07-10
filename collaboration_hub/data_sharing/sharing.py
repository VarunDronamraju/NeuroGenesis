from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from sqlalchemy.orm import Session
from models import DataShare

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class DataShareCreate(BaseModel):
    dataset_id: str
    recipient_id: str
    permissions: str  # "read", "write"

class DataShareManager:
    async def share_dataset(self, user_id: str, share: DataShareCreate, db: Session) -> Dict:
        db_share = DataShare(
            dataset_id=share.dataset_id,
            owner_id=user_id,
            recipient_id=share.recipient_id,
            permissions=share.permissions,
            created_at=datetime.utcnow()
        )
        db.add(db_share)
        db.commit()
        db.refresh(db_share)
        return {
            "share_id": db_share.id,
            "dataset_id": db_share.dataset_id,
            "recipient_id": db_share.recipient_id,
            "permissions": db_share.permissions
        }

    async def list_shares(self, user_id: str, db: Session) -> List[Dict]:
        shares = db.query(DataShare).filter(DataShare.owner_id == user_id).all()
        return [
            {
                "share_id": s.id,
                "dataset_id": s.dataset_id,
                "recipient_id": s.recipient_id,
                "permissions": s.permissions,
                "created_at": s.created_at
            } for s in shares
        ]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/data_shares")
async def share_dataset(
    share: DataShareCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = DataShareManager()
    return await manager.share_dataset(user.id, share, db)

@app.get("/data_shares")
async def list_shares(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = DataShareManager()
    return await manager.list_shares(user.id, db)
