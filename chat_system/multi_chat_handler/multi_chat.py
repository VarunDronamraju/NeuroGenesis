from fastapi import FastAPI, Depends, WebSocket
from typing import Dict, List
import redis
import json
import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class MultiChatHandler:
    def __init__(self):
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str, user_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)
        self.redis.subscribe(f"chat:{conversation_id}")

    async def disconnect(self, websocket: WebSocket, conversation_id: str):
        self.active_connections[conversation_id].remove(websocket)
        if not self.active_connections[conversation_id]:
            del self.active_connections[conversation_id]

    async def broadcast(self, conversation_id: str, message: str):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                await connection.send_text(message)
        self.redis.publish(f"chat:{conversation_id}", message)

@app.websocket("/ws/chat/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str, token: str):
    from user_management.authentication.auth import get_current_user
    db = SessionLocal()
    try:
        user = await get_current_user(token, db)
        handler = MultiChatHandler()
        await handler.connect(websocket, conversation_id, user.id)
        try:
            while True:
                data = await websocket.receive_text()
                await handler.broadcast(conversation_id, json.dumps({
                    "user_id": user.id,
                    "message": data,
                    "timestamp": datetime.utcnow().isoformat()
                }))
        except:
            await handler.disconnect(websocket, conversation_id)
    finally:
        db.close()