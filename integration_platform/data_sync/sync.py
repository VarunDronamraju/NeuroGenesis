from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class DataSyncRequest(BaseModel):
    source_collection: str
    target_collection: str
    filters: Dict = {}

class DataSynchronizer:
    def __init__(self):
        self.client = MongoClient(MONGO_URL)
        self.db = self.client["neurogenesis"]

    async def sync_data(self, user_id: str, request: DataSyncRequest) -> Dict:
        source = self.db[request.source_collection]
        target = self.db[request.target_collection]

        data = source.find(request.filters)
        synced_count = 0
        for doc in data:
            target.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
            synced_count += 1

        return {
            "sync_id": f"sync_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "source": request.source_collection,
            "target": request.target_collection,
            "synced_count": synced_count,
            "synced_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/data/sync")
async def sync_data(
    request: DataSyncRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    synchronizer = DataSynchronizer()
    return await synchronizer.sync_data(user.id, request)
