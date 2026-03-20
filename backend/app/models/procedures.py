"""Procedures model."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from app.core.database import Base


class Procedure(Base):
    __tablename__ = "procedures"
    
    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    procedure_code = Column(String, nullable=False)
    site = Column(String, nullable=True)
    laterality = Column(String, nullable=True)
    
    performed_at = Column(DateTime, nullable=True)
    success_status = Column(String, default="SUCCESS")
    
    notes = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    voided = Column(Boolean, default=False)
