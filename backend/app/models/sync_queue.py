"""Sync queue table (outbox pattern)."""
from datetime import datetime
from sqlalchemy import Column, Index, String, Text, DateTime, Integer

from app.core.database import Base


class SyncQueue(Base):
    __tablename__ = "sync_queue"
    __table_args__ = (Index("ix_sync_queue_status", "status"),)
    id = Column(String, primary_key=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)  # create, update, delete
    payload = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending, synced, failed
    retries = Column(Integer, nullable=False, default=0)
    device_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
