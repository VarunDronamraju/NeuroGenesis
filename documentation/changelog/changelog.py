from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ChangelogEntry(BaseModel):
    version: str
    changes: str

class ChangelogManager:
    async def add_changelog(self, user_id: str, entry: ChangelogEntry) -> Dict:
        changelog_id = f"changelog_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        changelog_path = Path("E:/Neurogenesis/docs/changelogs") / user_id / f"{changelog_id}.md"
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        content = f"# Changelog {entry.version}\n\n{entry.changes}\n\nAdded at: {datetime.utcnow()}"
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "changelog_id": changelog_id,
            "version": entry.version,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/changelogs")
async def add_changelog(entry: ChangelogEntry, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = ChangelogManager()
    return await manager.add_changelog(user.id, entry)
