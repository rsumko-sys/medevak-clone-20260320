"""Injuries model."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from app.core.database import Base


class Injury(Base):
    __tablename__ = "injuries"
    
    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    body_region = Column(String, nullable=False)
    injury_type = Column(String, nullable=False)
    severity = Column(String, nullable=True)
    laterality = Column(String, nullable=True) # left / right / bilateral
    mechanism = Column(String, nullable=True)
    penetrating = Column(Boolean, default=False)
    view = Column(String, nullable=True) # front / back
    
    notes = Column(String, nullable=True)
    icd10_code = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    voided = Column(Boolean, default=False)
