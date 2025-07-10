from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class WorkspaceCreate(BaseModel):
    name: str
    description: str

class WorkspaceManager:
    def __init__(self, base_path: str = "E:/Neurogenesis"):
        self.base_path = Path(base_path)

    async def create_workspace(self, user_id: str, workspace: WorkspaceCreate) -> Dict:
        workspace_path = self.base_path / "workspaces" / user_id / workspace.name
        workspace_path.mkdir(parents=True, exist_ok=True)

        with open(workspace_path / "README.md", "w") as f:
            f.write(f"# {workspace.name}\n{workspace.description}\n\nCreated by {user_id}")

        return {
            "workspace_id": workspace.name,
            "path": str(workspace_path),
            "description": workspace.description,
            "created_at": datetime.utcnow()
        }

    async def list_workspaces(self, user_id: str) -> List[Dict]:
        workspace_dir = self.base_path / "workspaces" / user_id
        workspaces = []
        if workspace_dir.exists():
            for ws in workspace_dir.iterdir():
                if ws.is_dir():
                    workspaces.append({
                        "workspace_id": ws.name,
                        "path": str(ws),
                        "last_modified": datetime.fromtimestamp(ws.stat().st_mtime)
                    })
        return workspaces

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/workspaces")
async def create_workspace(
    workspace: WorkspaceCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = WorkspaceManager()
    return await manager.create_workspace(user.id, workspace)

@app.get("/workspaces")
async def list_workspaces(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = WorkspaceManager()
    return await manager.list_workspaces(user.id)
