from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
import json
import os
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class PublicationCreate(BaseModel):
    title: str
    content: Dict
    workspace_id: str

class PublicationManager:
    async def create_publication(self, user_id: str, publication: PublicationCreate) -> Dict:
        publication_id = f"pub_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        publication_path = Path("E:/Neurogenesis/publications") / user_id / publication_id
        publication_path.mkdir(parents=True, exist_ok=True)

        with open(publication_path / "publication.json", "w") as f:
            json.dump({
                "title": publication.title,
                "content": publication.content,
                "workspace_id": publication.workspace_id,
                "created_at": datetime.utcnow().isoformat()
            }, f)

        return {
            "publication_id": publication_id,
            "title": publication.title,
            "workspace_id": publication.workspace_id,
            "created_at": datetime.utcnow()
        }

    async def list_publications(self, user_id: str) -> List[Dict]:
        publication_dir = Path("E:/Neurogenesis/publications") / user_id
        publications = []
        if publication_dir.exists():
            for pub in publication_dir.iterdir():
                if pub.is_dir():
                    with open(pub / "publication.json", "r") as f:
                        data = json.load(f)
                    publications.append({
                        "publication_id": pub.name,
                        "title": data["title"],
                        "workspace_id": data["workspace_id"],
                        "created_at": datetime.fromisoformat(data["created_at"])
                    })
        return publications

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/publications")
async def create_publication(
    publication: PublicationCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = PublicationManager()
    return await manager.create_publication(user.id, publication)

@app.get("/publications")
async def list_publications(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = PublicationManager()
    return await manager.list_publications(user.id)
