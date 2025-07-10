from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Team, TeamMember
from typing import List
from jose import jwt
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

class TeamCreate(BaseModel):
    name: str
    description: str

class TeamInvite(BaseModel):
    username: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/teams")
async def create_team(
    team: TeamCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(token, db)
    db_team = Team(name=team.name, description=team.description, owner_id=user.id)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    db_member = TeamMember(team_id=db_team.id, user_id=user.id, role="owner")
    db.add(db_member)
    db.commit()
    return {"team_id": db_team.id, "name": db_team.name, "description": db_team.description}

@app.post("/teams/{team_id}/invite")
async def invite_to_team(
    team_id: int,
    invite: TeamInvite,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(token, db)
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == user.id).first()
    if not team:
        raise HTTPException(status_code=403, detail="Not authorized")
    invited_user = db.query(User).filter(User.username == invite.username).first()
    if not invited_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_member = TeamMember(team_id=team_id, user_id=invited_user.id, role="member")
    db.add(db_member)
    db.commit()
    return {"message": f"Invited {invite.username} to team {team_id}"}

@app.get("/teams")
async def list_teams(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(token, db)
    teams = db.query(Team).join(TeamMember).filter(TeamMember.user_id == user.id).all()
    return [{"id": team.id, "name": team.name, "description": team.description} for team in teams]