from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from app.core.database import Base

class IdempotencyRecord(Base):
    """Tracks idempotent requests to prevent duplicate operations."""
    __tablename__ = "idempotency_records"
    
    key = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    request_path = Column(String)
    response_code = Column(String)
    response_body = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, index=True)
