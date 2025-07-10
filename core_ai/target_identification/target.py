from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from pathlib import Path
import json

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TargetRequest(BaseModel):
    disease: str
    criteria: Dict

class TargetIdentifier:
    async def identify_target(self, user_id: str, request: TargetRequest) -> Dict:
        target_id = f"target_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        output_path = Path("E:/Neurogenesis/targets") / user_id / f"{target_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        target_data = {
            "target_id": target_id,
            "disease": request.disease,
            "targets": ["protein_X", "protein_Y"],
            "criteria": request.criteria
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(target_data, f)
        return {
            "target_id": target_id,
            "disease": request.disease,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/targets")
async def identify_target(request: TargetRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    identifier = TargetIdentifier()
    return await identifier.identify_target(user.id, request)
