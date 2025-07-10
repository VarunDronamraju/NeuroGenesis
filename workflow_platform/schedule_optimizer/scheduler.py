from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
import pandas as pd
from pathlib import Path
import json

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ScheduleRequest(BaseModel):
    workflow_id: str
    constraints: Dict[str, float]

class ScheduleOptimizer:
    async def optimize_schedule(self, user_id: str, request: ScheduleRequest) -> Dict:
        workflow_path = Path(r"E:\Neurogenesis\workflows") / user_id / f"{request.workflow_id}.json"
        if not workflow_path.exists():
            raise HTTPException(status_code=404, detail="Workflow not found")

        schedule = {
            "workflow_id": request.workflow_id,
            "tasks": [{"task_id": f"t{i}", "start_time": datetime.utcnow().isoformat()} for i in range(1, 4)],
            "constraints": request.constraints
        }
        schedule_path = Path(r"E:\Neurogenesis\schedules") / user_id / f"{request.workflow_id}_schedule.json"
        schedule_path.parent.mkdir(parents=True, exist_ok=True)
        with open(schedule_path, "w", encoding="utf-8") as f:
            json.dump(schedule, f)

        return {
            "schedule_id": f"schedule_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "workflow_id": request.workflow_id,
            "constraints": request.constraints,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/schedules")
async def optimize_schedule(request: ScheduleRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    optimizer = ScheduleOptimizer()
    return await optimizer.optimize_schedule(user.id, request)
