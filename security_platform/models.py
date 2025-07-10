from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class AccessRule(Base):
    __tablename__ = "access_rules"
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String, index=True)
    resource_type = Column(String, index=True)
    user_id = Column(String, index=True)
    permission = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
