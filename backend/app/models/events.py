"""Events/Timeline model."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.sqlite import JSON
from app.core.database import Base


class Event(Base):
    __tablename__ = "events"
    
    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(String, nullable=False) # SYSTEM, USER, INTEGRATION
    event_time = Column(DateTime, default=datetime.utcnow)
    actor_id = Column(String, nullable=True)
    
    payload = Column(JSON, nullable=True)
    
    recorded_at = Column(DateTime, default=datetime.utcnow)
    voided = Column(Boolean, default=False)
