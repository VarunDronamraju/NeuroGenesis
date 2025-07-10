from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from sqlalchemy.orm import Session
from models import Task

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TaskCreate(BaseModel):
    team_id: str
    title: str
    description: str
    assignees: List[str]

class TaskCollaboration:
    async def create_task(self, user_id: str, task: TaskCreate, db: Session) -> Dict:
        db_task = Task(
            team_id=task.team_id,
            title=task.title,
            description=task.description,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        for assignee_id in task.assignees:
            db.execute("INSERT INTO task_assignees (task_id, user_id) VALUES (:task_id, :user_id)",
                      {"task_id": db_task.id, "user_id": assignee_id})
        db.commit()
        return {
            "task_id": db_task.id,
            "team_id": task.team_id,
            "title": task.title,
            "assignee_count": len(task.assignees),
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/tasks")
async def create_task(task: TaskCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    collaboration = TaskCollaboration()
    return await collaboration.create_task(user.id, task, db)
