from fastapi import FastAPI, Depends, HTTPException
from git import Repo
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class VersionControl:
    def __init__(self, repo_path: str = r"E:\Neurogenesis"):
        self.repo_path = Path(repo_path)
        self.repo = Repo(self.repo_path)

    async def commit_changes(self, project_id: str, user_id: str, message: str) -> Dict:
        project_path = self.repo_path / "projects" / user_id / project_id
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        self.repo.index.add([str(project_path)])
        commit = self.repo.index.commit(f"{message} by {user_id}")
        return {
            "commit_id": commit.hexsha,
            "message": message,
            "timestamp": commit.committed_datetime
        }

    async def get_history(self, project_id: str, user_id: str) -> List[Dict]:
        project_path = self.repo_path / "projects" / user_id / project_id
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        commits = list(self.repo.iter_commits(paths=str(project_path)))
        return [
            {
                "commit_id": commit.hexsha,
                "message": commit.message,
                "timestamp": commit.committed_datetime,
                "author": commit.author.name
            } for commit in commits
        ]

@app.post("/projects/{project_id}/commit")
async def commit_project(
    project_id: str,
    message: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    vc = VersionControl()
    return await vc.commit_changes(project_id, user.id, message)

@app.get("/projects/{project_id}/history")
async def get_project_history(
    project_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    vc = VersionControl()
    return await vc.get_history(project_id, user.id)
