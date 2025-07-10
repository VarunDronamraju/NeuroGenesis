from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from sqlalchemy.orm import Session
from models import AccessRule

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AccessRuleCreate(BaseModel):
    resource_id: str
    resource_type: str
    user_id: str
    permission: str

class AccessControl:
    async def create_access_rule(self, user_id: str, rule: AccessRuleCreate, db: Session):
        db_rule = AccessRule(
            resource_id=rule.resource_id,
            resource_type=rule.resource_type,
            user_id=rule.user_id,
            permission=rule.permission,
            created_at=datetime.utcnow()
        )
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        return {
            "rule_id": db_rule.id,
            "resource_id": rule.resource_id,
            "resource_type": rule.resource_type,
            "user_id": rule.user_id,
            "permission": rule.permission
        }

    async def check_access(self, user_id: str, resource_id: str, resource_type: str, db: Session):
        rule = db.query(AccessRule).filter(
            AccessRule.resource_id == resource_id,
            AccessRule.resource_type == resource_type,
            AccessRule.user_id == user_id
        ).first()
        return {
            "access": bool(rule),
            "permission": rule.permission if rule else None,
            "checked_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/access/rules")
async def create_access_rule(rule: AccessRuleCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    control = AccessControl()
    return await control.create_access_rule(user.id, rule, db)

@app.get("/access/check/{resource_type}/{resource_id}")
async def check_access(resource_type: str, resource_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    control = AccessControl()
    return await control.check_access(user.id, resource_id, resource_type, db)
