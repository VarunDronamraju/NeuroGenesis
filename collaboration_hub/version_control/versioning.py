from fastapi import FastAPI, Depends, HTTPException
from git import Repo
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class VersionControl:
    def __init__(self, repo_path: str = "E:/Neurogenesis"):
        self.repo_path = Path(repo_path)
        self.repo = Repo(self.repo_path)

    async def commit_changes(self, workspace_id: str, user_id: str, message: str) -> Dict:
        workspace_path = self.repo_path / "workspaces" / user_id / workspace_id
        if not workspace_path.exists():
            raise HTTPException(status_code=404, detail="Workspace not found")

        self.repo.index.add([str(workspace_path)])
        commit = self.repo.index.commit(f"{message} by {user_id}")
        return {
            "commit_id": commit.hexsha,
            "message": message,
            "timestamp": commit.committed_datetime
        }

    async def get_history(self, workspace_id: str, user_id: str) -> List[Dict]:
        workspace_path = self.repo_path / "workspaces" / user_id / workspace_id
        if not workspace_path.exists():
            raise HTTPException(status_code=404, detail="Workspace not found")

        commits = list(self.repo.iter_commits(paths=str(workspace_path)))
        return [
            {
                "commit_id": commit.hexsha,
                "message": commit.message,
                "timestamp": commit.committed_datetime,
                "author": commit.author.name
            } for commit in commits
        ]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/workspaces/{workspace_id}/commit")
async def commit_workspace(
    workspace_id: str,
    message: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    vc = VersionControl()
    return await vc.commit_changes(workspace_id, user.id, message)

@app.get("/workspaces/{workspace_id}/history")
async def get_workspace_history(
    workspace_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    vc = VersionControl()
    return await vc.get_history(workspace_id, user.id)
