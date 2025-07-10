from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class DataAccessRequest(BaseModel):
    dataset_id: str

class MobileDataAccess:
    async def access_data(self, user_id: str, request: DataAccessRequest) -> Dict:
        dataset_path = Path("E:/Neurogenesis/datasets") / user_id / f"{request.dataset_id}.csv"
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")
        df = pd.read_csv(dataset_path)
        return {
            "dataset_id": request.dataset_id,
            "row_count": len(df),
            "columns": list(df.columns),
            "accessed_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/mobile/data")
async def access_data(request: DataAccessRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    access = MobileDataAccess()
    return await access.access_data(user.id, request)
