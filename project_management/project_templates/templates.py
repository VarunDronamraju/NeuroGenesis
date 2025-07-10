from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from pathlib import Path
from git import Repo
from typing import List, Dict
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
import shutil

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TemplateCreate(BaseModel):
    name: str
    description: str
    source_project_id: str

class TemplateManager:
    def __init__(self, repo_path: str = r"E:\Neurogenesis"):
        self.repo_path = Path(repo_path)
        self.repo = Repo(self.repo_path)

    async def create_template(self, user_id: str, template: TemplateCreate) -> Dict:
        source_path = self.repo_path / "projects" / user_id / template.source_project_id
        template_path = self.repo_path / "templates" / user_id / template.name
        if not source_path.exists():
            raise HTTPException(status_code=404, detail="Source project not found")

        shutil.copytree(source_path, template_path)
        self.repo.index.add([str(template_path)])
        self.repo.index.commit(f"Created template {template.name} from {template.source_project_id}")

        return {
            "template_id": template.name,
            "description": template.description,
            "created_at": datetime.utcnow()
        }

    async def list_templates(self, user_id: str) -> List[Dict]:
        template_dir = self.repo_path / "templates" / user_id
        templates = []
        if template_dir.exists():
            for template in template_dir.iterdir():
                if template.is_dir():
                    templates.append({
                        "template_id": template.name,
                        "last_modified": datetime.fromtimestamp(template.stat().st_mtime)
                    })
        return templates

@app.post("/templates")
async def create_template(
    template: TemplateCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = TemplateManager()
    return await manager.create_template(user.id, template)

@app.get("/templates")
async def list_templates(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = TemplateManager()
    return await manager.list_templates(user.id)
