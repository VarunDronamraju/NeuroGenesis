from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserGuideRequest(BaseModel):
    title: str
    content: str

class UserGuideGenerator:
    async def generate_guide(self, user_id: str, request: UserGuideRequest) -> Dict:
        guide_id = f"guide_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        guide_path = Path("E:/Neurogenesis/docs/guides") / user_id / f"{guide_id}.md"
        guide_path.parent.mkdir(parents=True, exist_ok=True)
        content = f"# User Guide: {request.title}\n\n{request.content}\n\nGenerated at: {datetime.utcnow()}"
        with open(guide_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "guide_id": guide_id,
            "title": request.title,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/user_guides")
async def generate_guide(request: UserGuideRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    generator = UserGuideGenerator()
    return await generator.generate_guide(user.id, request)
