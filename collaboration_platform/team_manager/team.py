from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from sqlalchemy.orm import Session
from models import Team

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TeamCreate(BaseModel):
    name: str
    members: List[str]

class TeamManager:
    async def create_team(self, user_id: str, team: TeamCreate, db: Session) -> Dict:
        db_team = Team(name=team.name, owner_id=user_id, created_at=datetime.utcnow())
        db.add(db_team)
        db.commit()
        db.refresh(db_team)
        for member_id in team.members:
            db.execute("INSERT INTO team_members (team_id, user_id) VALUES (:team_id, :user_id)",
                      {"team_id": db_team.id, "user_id": member_id})
        db.commit()
        return {
            "team_id": db_team.id,
            "name": team.name,
            "member_count": len(team.members),
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/teams")
async def create_team(team: TeamCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = TeamManager()
    return await manager.create_team(user.id, team, db)
