from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class MessageCreate(BaseModel):
    content: str

class ConversationManager:
    def __init__(self):
        self.client = MongoClient(MONGO_URL)
        self.db = self.client["neurogenesis"]
        self.conversations = self.db["conversations"]

    async def create_conversation(self, user_id: str) -> str:
        conversation = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "messages": []
        }
        result = self.conversations.insert_one(conversation)
        return str(result.inserted_id)

    async def add_message(self, conversation_id: str, user_id: str, content: str, is_user: bool):
        message = {
            "content": content,
            "is_user": is_user,
            "timestamp": datetime.utcnow()
        }
        self.conversations.update_one(
            {"_id": conversation_id, "user_id": user_id},
            {"$push": {"messages": message}}
        )

    async def get_conversation(self, conversation_id: str, user_id: str) -> Dict:
        conversation = self.conversations.find_one({"_id": conversation_id, "user_id": user_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation

@app.post("/conversations")
async def start_conversation(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = ConversationManager()
    conversation_id = await manager.create_conversation(user.id)
    return {"conversation_id": conversation_id}

@app.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    message: MessageCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = ConversationManager()
    await manager.add_message(conversation_id, user.id, message.content, True)
    return {"message": "Message added"}

@app.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = ConversationManager()
    conversation = await manager.get_conversation(conversation_id, user.id)
    return conversation