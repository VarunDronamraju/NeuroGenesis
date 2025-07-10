from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from git import Repo
from pathlib import Path
from datetime import datetime
from typing import Dict
import shutil
import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class BackupManager:
    def __init__(self, repo_path: str = r"E:\Neurogenesis"):
        self.repo_path = Path(repo_path)
        self.backup_path = self.repo_path / "backups"
        self.repo = Repo(self.repo_path)

    async def create_backup(self, user_id: str, project_id: str) -> Dict:
        project_path = self.repo_path / "projects" / user_id / project_id
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        backup_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        backup_dest = self.backup_path / user_id / project_id / backup_id
        shutil.copytree(project_path, backup_dest)

        self.repo.index.add([str(backup_dest)])
        self.repo.index.commit(f"Backup for project {project_id} by {user_id}")

        return {"backup_id": backup_id, "created_at": datetime.utcnow()}

    async def restore_backup(self, user_id: str, project_id: str, backup_id: str) -> Dict:
        backup_path = self.backup_path / user_id / project_id / backup_id
        project_path = self.repo_path / "projects" / user_id / project_id
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup not found")

        shutil.rmtree(project_path, ignore_errors=True)
        shutil.copytree(backup_path, project_path)

        self.repo.index.add([str(project_path)])
        self.repo.index.commit(f"Restored backup {backup_id} for {project_id}")

        return {"project_id": project_id, "restored_from": backup_id}

@app.post("/projects/{project_id}/backup")
async def create_project_backup(
    project_id: str,
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = BackupManager()
    return await manager.create_backup(user.id, project_id)

@app.post("/projects/{project_id}/restore/{backup_id}")
async def restore_project_backup(
    project_id: str,
    backup_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = BackupManager()
    return await manager.restore_backup(user.id, project_id, backup_id)
