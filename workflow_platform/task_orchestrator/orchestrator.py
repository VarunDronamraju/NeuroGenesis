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

class TaskWorkflow(BaseModel):
    name: str
    tasks: List[Dict[str, str]]

class TaskOrchestrator:
    async def create_workflow(self, user_id: str, workflow: TaskWorkflow) -> Dict:
        workflow_id = f"workflow_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        workflow_path = Path(r"E:\Neurogenesis\workflows") / user_id / f"{workflow_id}.json"
        workflow_path.parent.mkdir(parents=True, exist_ok=True)

        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump({
                "name": workflow.name,
                "tasks": workflow.tasks,
                "created_at": datetime.utcnow().isoformat()
            }, f)

        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "task_count": len(workflow.tasks),
            "created_at": datetime.utcnow()
        }

    async def execute_workflow(self, user_id: str, workflow_id: str) -> Dict:
        workflow_path = Path(r"E:\Neurogenesis\workflows") / user_id / f"{workflow_id}.json"
        if not workflow_path.exists():
            raise HTTPException(status_code=404, detail="Workflow not found")

        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        results = [{"task_id": task["task_id"], "status": "completed"} for task in workflow["tasks"]]
        return {
            "workflow_id": workflow_id,
            "results": results,
            "executed_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/workflows")
async def create_workflow(workflow: TaskWorkflow, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    orchestrator = TaskOrchestrator()
    return await orchestrator.create_workflow(user.id, workflow)

@app.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    orchestrator = TaskOrchestrator()
    return await orchestrator.execute_workflow(user.id, workflow_id)
