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

class ProgressUpdate(BaseModel):
    workflow_id: str
    task_id: str
    status: str

class ProgressTracker:
    async def update_progress(self, user_id: str, update: ProgressUpdate) -> Dict:
        workflow_path = Path(r"E:\Neurogenesis\workflows") / user_id / f"{update.workflow_id}.json"
        if not workflow_path.exists():
            raise HTTPException(status_code=404, detail="Workflow not found")

        progress_id = f"progress_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        progress_path = Path(r"E:\Neurogenesis\progress") / user_id / f"{progress_id}.json"
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump({
                "workflow_id": update.workflow_id,
                "task_id": update.task_id,
                "status": update.status,
                "updated_at": datetime.utcnow().isoformat()
            }, f)

        return {
            "progress_id": progress_id,
            "workflow_id": update.workflow_id,
            "task_id": update.task_id,
            "status": update.status,
            "updated_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/progress")
async def update_progress(update: ProgressUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    tracker = ProgressTracker()
    return await tracker.update_progress(user.id, update)
