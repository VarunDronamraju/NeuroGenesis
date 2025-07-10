from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from pathlib import Path
import json

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class APIDocRequest(BaseModel):
    endpoint: str
    description: str

class APIDocGenerator:
    async def generate_api_doc(self, user_id: str, request: APIDocRequest) -> Dict:
        doc_id = f"api_doc_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        doc_path = Path("E:/Neurogenesis/docs/api") / user_id / f"{doc_id}.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        content = f"# API Documentation\n\n## Endpoint: {request.endpoint}\n\n{request.description}\n\nGenerated at: {datetime.utcnow()}"
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "doc_id": doc_id,
            "endpoint": request.endpoint,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api_docs")
async def generate_api_doc(request: APIDocRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    generator = APIDocGenerator()
    return await generator.generate_api_doc(user.id, request)
