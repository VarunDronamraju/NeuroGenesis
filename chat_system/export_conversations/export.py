from fastapi import FastAPI, Depends, HTTPException
from pymongo import MongoClient
from typing import List
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
app = FastAPI()

class ConversationExporter:
    def __init__(self):
        self.client = MongoClient(MONGO_URL)
        self.db = self.client["neurogenesis"]
        self.conversations = self.db["conversations"]

    async def export_conversation(self, conversation_id: str, user_id: str) -> str:
        conversation = self.conversations.find_one({"_id": conversation_id, "user_id": user_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        export_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "created_at": conversation["created_at"].isoformat(),
            "messages": [
                {
                    "content": msg["content"],
                    "is_user": msg["is_user"],
                    "timestamp": msg["timestamp"].isoformat()
                } for msg in conversation["messages"]
            ]
        }
        
        export_path = f"exports/conversation_{conversation_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)
        return export_path

@app.get("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="token")),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    exporter = ConversationExporter()
    export_path = await exporter.export_conversation(conversation_id, user.id)
    return {"export_path": export_path}