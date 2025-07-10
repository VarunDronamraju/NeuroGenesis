from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base
from datetime import datetime

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, index=True)
    user_id = Column(String, index=True)
    content = Column(String)
    parent_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DataShare(Base):
    __tablename__ = "data_shares"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String, index=True)
    owner_id = Column(String, ForeignKey("users.id"))
    recipient_id = Column(String)
    permissions = Column(String)  # read, write
    created_at = Column(DateTime, default=datetime.utcnow)
