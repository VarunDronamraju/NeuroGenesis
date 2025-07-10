from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class DocumentShare(BaseModel):
    team_id: str
    description: str

class DocumentSharing:
    async def share_document(self, user_id: str, team_id: str, file: UploadFile, description: str) -> Dict:
        document_id = f"doc_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        document_path = Path("E:/Neurogenesis/documents") / user_id / f"{document_id}_{file.filename}"
        document_path.parent.mkdir(parents=True, exist_ok=True)
        with open(document_path, "wb") as f:
            f.write(await file.read())
        return {
            "document_id": document_id,
            "team_id": team_id,
            "filename": file.filename,
            "description": description,
            "shared_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/documents/share")
async def share_document(team_id: str, description: str, file: UploadFile = File(...), token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    sharing = DocumentSharing()
    return await sharing.share_document(user.id, team_id, file, description)
