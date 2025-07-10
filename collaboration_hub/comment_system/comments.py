from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from sqlalchemy.orm import Session
from models import Comment

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class CommentCreate(BaseModel):
    document_id: str
    content: str
    parent_id: str = None

class CommentManager:
    async def create_comment(self, user_id: str, comment: CommentCreate, db: Session) -> Dict:
        db_comment = Comment(
            document_id=comment.document_id,
            user_id=user_id,
            content=comment.content,
            parent_id=comment.parent_id,
            created_at=datetime.utcnow()
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        return {
            "comment_id": db_comment.id,
            "document_id": db_comment.document_id,
            "content": db_comment.content,
            "created_at": db_comment.created_at
        }

    async def get_comments(self, document_id: str, db: Session) -> List[Dict]:
        comments = db.query(Comment).filter(Comment.document_id == document_id).all()
        return [
            {
                "comment_id": c.id,
                "document_id": c.document_id,
                "user_id": c.user_id,
                "content": c.content,
                "parent_id": c.parent_id,
                "created_at": c.created_at
            } for c in comments
        ]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/comments")
async def create_comment(
    comment: CommentCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = CommentManager()
    return await manager.create_comment(user.id, comment, db)

@app.get("/comments/{document_id}")
async def get_comments(
    document_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = CommentManager()
    return await manager.get_comments(document_id, db)
