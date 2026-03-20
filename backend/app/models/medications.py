"""Medications model."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from app.core.database import Base


class MedicationAdministration(Base):
    __tablename__ = "medication_administrations"
    
    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    medication_code = Column(String, nullable=False)
    dose_value = Column(String, nullable=True)
    dose_unit_code = Column(String, nullable=True)
    route = Column(String, nullable=True)
    
    time_administered = Column(DateTime, nullable=True)
    indication = Column(String, nullable=True)
    status = Column(String, default="COMPLETED")
    
    notes = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    voided = Column(Boolean, default=False)
