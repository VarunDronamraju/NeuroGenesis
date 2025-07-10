from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base
from datetime import datetime

class ProjectPermission(Base):
    __tablename__ = "project_permissions"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, index=True)
    user_id = Column(String, index=True)
    owner_id = Column(String, ForeignKey("users.id"))
    role = Column(String)  # read, write, admin
    created_at = Column(DateTime, default=datetime.utcnow)
