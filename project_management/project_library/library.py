from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from git import Repo
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from database import SessionLocal
import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ProjectCreate(BaseModel):
    name: str
    description: str

class ProjectManager:
    def __init__(self, repo_path: str = r"E:\Neurogenesis"):
        self.repo_path = Path(repo_path)
        self.repo = Repo.init(self.repo_path, mkdir=False)

    async def create_project(self, user_id: str, project: ProjectCreate) -> Dict:
        project_path = self.repo_path / "projects" / user_id / project.name
        project_path.mkdir(parents=True, exist_ok=True)

        with open(project_path / "README.md", "w") as f:
            f.write(f"# {project.name}\n{project.description}\n\nCreated by {user_id}")

        self.repo.index.add([str(project_path)])
        self.repo.index.commit(f"Created project {project.name} for {user_id}")

        return {
            "project_id": project.name,
            "path": str(project_path),
            "created_at": datetime.utcnow(),
            "description": project.description
        }

    async def list_projects(self, user_id: str) -> List[Dict]:
        project_dir = self.repo_path / "projects" / user_id
        projects = []
        if project_dir.exists():
            for project in project_dir.iterdir():
                if project.is_dir():
                    projects.append({
                        "project_id": project.name,
                        "path": str(project),
                        "last_modified": datetime.fromtimestamp(project.stat().st_mtime),
                        "description": self._get_project_description(project)
                    })
        return projects

    def _get_project_description(self, project_path: Path) -> str:
        readme_path = project_path / "README.md"
        if readme_path.exists():
            with open(readme_path, "r") as f:
                lines = f.read().split("\n")
                return lines[1] if len(lines) > 1 else ""
        return ""

@app.post("/projects")
async def create_project(
    project: ProjectCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = ProjectManager()
    project_data = await manager.create_project(user.id, project)
    return project_data

@app.get("/projects")
async def list_projects(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = ProjectManager()
    return await manager.list_projects(user.id)
