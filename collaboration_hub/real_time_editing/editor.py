from fastapi import FastAPI, WebSocket, Depends, HTTPException
from typing import Dict, List
import redis
import json
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class RealTimeEditor:
    def __init__(self):
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, document_id: str, user_id: str):
        await websocket.accept()
        if document_id not in self.active_connections:
            self.active_connections[document_id] = []
        self.active_connections[document_id].append(websocket)
        self.redis.subscribe(f"document:{document_id}")

    async def disconnect(self, websocket: WebSocket, document_id: str):
        self.active_connections[document_id].remove(websocket)
        if not self.active_connections[document_id]:
            del self.active_connections[document_id]

    async def broadcast_edit(self, document_id: str, edit: Dict):
        if document_id in self.active_connections:
            for connection in self.active_connections[document_id]:
                await connection.send_json(edit)
        self.redis.publish(f"document:{document_id}", json.dumps(edit))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.websocket("/ws/document/{document_id}")
async def websocket_document(websocket: WebSocket, document_id: str, token: str):
    from user_management.authentication.auth import get_current_user
    db = SessionLocal()
    try:
        user = await get_current_user(token, db)
        editor = RealTimeEditor()
        await editor.connect(websocket, document_id, user.id)
        try:
            while True:
                data = await websocket.receive_json()
                edit = {
                    "user_id": user.id,
                    "edit": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await editor.broadcast_edit(document_id, edit)
        except:
            await editor.disconnect(websocket, document_id)
    finally:
        db.close()
