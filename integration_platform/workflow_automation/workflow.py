from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
import json
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class WorkflowCreate(BaseModel):
    name: str
    steps: List[Dict]

class WorkflowManager:
    async def create_workflow(self, user_id: str, workflow: WorkflowCreate) -> Dict:
        workflow_id = f"workflow_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        workflow_path = Path(f"E:/Neurogenesis/workflows/{user_id}/{workflow_id}.json")
        workflow_path.parent.mkdir(parents=True, exist_ok=True)

        with open(workflow_path, "w") as f:
            json.dump({
                "name": workflow.name,
                "steps": workflow.steps,
                "created_at": datetime.utcnow().isoformat()
            }, f)

        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "steps_count": len(workflow.steps),
            "created_at": datetime.utcnow()
        }

    async def execute_workflow(self, user_id: str, workflow_id: str) -> Dict:
        workflow_path = Path(f"E:/Neurogenesis/workflows/{user_id}/{workflow_id}.json")
        if not workflow_path.exists():
            raise HTTPException(status_code=404, detail="Workflow not found")

        with open(workflow_path, "r") as f:
            workflow = json.load(f)

        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "executed_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/workflows")
async def create_workflow(
    workflow: WorkflowCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = WorkflowManager()
    return await manager.create_workflow(user.id, workflow)

@app.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = WorkflowManager()
    return await manager.execute_workflow(user.id, workflow_id)
