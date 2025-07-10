from fastapi import FastAPI, Depends, HTTPException
from pymongo import MongoClient
from typing import List, Dict
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
app = FastAPI()

class SearchQuery(BaseModel):
    query: str
    limit: int = 10

class SearchHistory:
    def __init__(self):
        self.client = MongoClient(MONGO_URL)
        self.db = self.client["neurogenesis"]
        self.conversations = self.db["conversations"]

    async def search_conversations(self, user_id: str, query: str, limit: int) -> List[Dict]:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$unwind": "$messages"},
            {"$match": {"messages.content": {"$regex": query, "$options": "i"}}},
            {
                "$group": {
                    "_id": "$_id",
                    "created_at": {"$first": "$created_at"},
                    "messages": {"$push": "$messages"}
                }
            },
            {"$limit": limit}
        ]
        results = list(self.conversations.aggregate(pipeline))
        return [
            {
                "conversation_id": str(result["_id"]),
                "created_at": result["created_at"],
                "messages": result["messages"]
            } for result in results
        ]

@app.post("/conversations/search")
async def search_conversation_history(
    search: SearchQuery,
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="token")),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    searcher = SearchHistory()
    results = await searcher.search_conversations(user.id, search.query, search.limit)
    return results