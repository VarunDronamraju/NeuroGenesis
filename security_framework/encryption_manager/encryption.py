from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from cryptography.fernet import Fernet
from pathlib import Path
from sqlalchemy.orm import Session

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class EncryptionRequest(BaseModel):
    data: str
    key_id: str

class EncryptionManager:
    async def encrypt_data(self, user_id: str, request: EncryptionRequest) -> Dict:
        key_path = Path("E:/Neurogenesis/keys") / user_id / f"{request.key_id}.key"
        if not key_path.exists():
            key_path.parent.mkdir(parents=True, exist_ok=True)
            key = Fernet.generate_key()
            with open(key_path, "wb") as f:
                f.write(key)
        else:
            with open(key_path, "rb") as f:
                key = f.read()

        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(request.data.encode())
        output_path = Path("E:/Neurogenesis/encrypted") / user_id / f"encrypted_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.bin"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(encrypted_data)

        return {
            "encryption_id": f"enc_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "key_id": request.key_id,
            "encrypted_path": str(output_path),
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/encrypt")
async def encrypt_data(request: EncryptionRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = EncryptionManager()
    return await manager.encrypt_data(user.id, request)
