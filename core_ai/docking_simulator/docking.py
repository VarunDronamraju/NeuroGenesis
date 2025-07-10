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

class DockingRequest(BaseModel):
    molecule_id: str
    target_id: str

class DockingSimulator:
    async def run_docking(self, user_id: str, request: DockingRequest) -> Dict:
        docking_id = f"docking_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        output_path = Path("E:/Neurogenesis/dockings") / user_id / f"{docking_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        docking_data = {
            "docking_id": docking_id,
            "molecule_id": request.molecule_id,
            "target_id": request.target_id,
            "score": 0.0
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(docking_data, f)
        return {
            "docking_id": docking_id,
            "molecule_id": request.molecule_id,
            "target_id": request.target_id,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/dockings")
async def run_docking(request: DockingRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    simulator = DockingSimulator()
    return await simulator.run_docking(user.id, request)
