from pymongo import MongoClient
from typing import List, Dict
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
app = FastAPI()

class ContextManager:
    def __init__(self):
        self.client = MongoClient(MONGO_URL)
        self.db = self.client["neurogenesis"]
        self.contexts = self.db["contexts"]

    async def save_context(self, conversation_id: str, user_id: str, context: Dict):
        self.contexts.update_one(
            {"conversation_id": conversation_id, "user_id": user_id},
            {"$set": {"context": context, "updated_at": datetime.utcnow()}},
            upsert=True
        )

    async def get_context(self, conversation_id: str, user_id: str) -> Dict:
        context = self.contexts.find_one({"conversation_id": conversation_id, "user_id": user_id})
        if not context:
            return {}
        return context["context"]

    async def update_context(self, conversation_id: str, user_id: str, updates: Dict):
        self.contexts.update_one(
            {"conversation_id": conversation_id, "user_id": user_id},
            {"$set": {"context": updates, "updated_at": datetime.utcnow()}},
            upsert=True
        )

@app.post("/conversations/{conversation_id}/context")
async def save_conversation_context(
    conversation_id: str,
    context: Dict,
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="token")),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = ContextManager()
    await manager.save_context(conversation_id, user.id, context)
    return {"message": "Context saved"}

@app.get("/conversations/{conversation_id}/context")
async def get_conversation_context(
    conversation_id: str,
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="token")),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = ContextManager()
    context = await manager.get_context(conversation_id, user.id)
    return context