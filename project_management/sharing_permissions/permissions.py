from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, ProjectPermission
from typing import List
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class PermissionCreate(BaseModel):
    user_id: str
    role: str  # "read", "write", "admin"

class PermissionManager:
    def __init__(self):
        pass

    async def add_permission(self, project_id: str, owner_id: str, permission: PermissionCreate, db: Session):
        project_path = Path(r"E:\Neurogenesis\projects") / owner_id / project_id
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        db_permission = ProjectPermission(
            project_id=project_id,
            user_id=permission.user_id,
            role=permission.role,
            owner_id=owner_id
        )
        db.add(db_permission)
        db.commit()
        return {"project_id": project_id, "user_id": permission.user_id, "role": permission.role}

    async def get_permissions(self, project_id: str, owner_id: str, db: Session) -> List[Dict]:
        permissions = db.query(ProjectPermission).filter(
            ProjectPermission.project_id == project_id,
            ProjectPermission.owner_id == owner_id
        ).all()
        return [
            {"user_id": p.user_id, "role": p.role, "created_at": p.created_at}
            for p in permissions
        ]

@app.post("/projects/{project_id}/permissions")
async def add_project_permission(
    project_id: str,
    permission: PermissionCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = PermissionManager()
    return await manager.add_permission(project_id, user.id, permission, db)

@app.get("/projects/{project_id}/permissions")
async def get_project_permissions(
    project_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = PermissionManager()
    return await manager.get_permissions(project_id, user.id, db)
