"""Audit log model."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.sqlite import JSON

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(String, primary_key=True)
    table_name = Column(String, nullable=False)
    row_id = Column(String, nullable=True)
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE
    
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    user_id = Column(String, nullable=True)
    device_id = Column(String, nullable=True)  # device making the change
    client_ip = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
