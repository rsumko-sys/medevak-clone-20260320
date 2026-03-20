"""Evacuation model."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from app.core.database import Base


class EvacuationRecord(Base):
    __tablename__ = "evacuation_records"
    
    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    evacuation_priority = Column(String, nullable=True) # URGENT, PRIORITY, ROUTINE
    transport_type = Column(String, nullable=True) # Ground, Air
    destination = Column(String, nullable=True)
    nine_line_sent = Column(Boolean, default=False)
    
    handoff_to = Column(String, nullable=True)
    mist_summary = Column(String, nullable=True)
    
    departed_at = Column(DateTime, nullable=True)
    arrived_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    voided = Column(Boolean, default=False)
