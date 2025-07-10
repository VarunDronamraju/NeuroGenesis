from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from cryptography.fernet import Fernet
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class EncryptionRequest(BaseModel):
    data: str
    file_path: str

class EncryptionService:
    def __init__(self):
        key_path = Path("E:/Neurogenesis/keys/encryption_key.key")
        if not key_path.exists():
            key = Fernet.generate_key()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(key_path, "wb") as f:
                f.write(key)
        with open(key_path, "rb") as f:
            self.fernet = Fernet(f.read())

    async def encrypt_data(self, user_id: str, request: EncryptionRequest):
        encrypted_data = self.fernet.encrypt(request.data.encode())
        encrypted_path = Path(f"E:/Neurogenesis/encrypted/{user_id}/{request.file_path}")
        encrypted_path.parent.mkdir(parents=True, exist_ok=True)
        with open(encrypted_path, "wb") as f:
            f.write(encrypted_data)
        return {
            "file_path": str(encrypted_path),
            "encrypted_at": datetime.utcnow()
        }

    async def decrypt_data(self, user_id: str, file_path: str):
        encrypted_path = Path(f"E:/Neurogenesis/encrypted/{user_id}/{file_path}")
        if not encrypted_path.exists():
            raise HTTPException(status_code=404, detail="Encrypted file not found")
        with open(encrypted_path, "rb") as f:
            encrypted_data = f.read()
        decrypted_data = self.fernet.decrypt(encrypted_data).decode()
        return {
            "file_path": str(encrypted_path),
            "decrypted_data": decrypted_data,
            "decrypted_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/encrypt")
async def encrypt_data(request: EncryptionRequest, token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    service = EncryptionService()
    return await service.encrypt_data(user.id, request)

@app.get("/decrypt/{file_path:path}")
async def decrypt_data(file_path: str, token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    service = EncryptionService()
    return await service.decrypt_data(user.id, file_path)
