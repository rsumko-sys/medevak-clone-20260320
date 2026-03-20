"""Vitals Observations model."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Float
from app.core.database import Base


class VitalsObservation(Base):
    __tablename__ = "vitals_observations"
    
    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    heart_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    systolic_bp = Column(Integer, nullable=True)
    diastolic_bp = Column(Integer, nullable=True)
    spo2_percent = Column(Integer, nullable=True)
    temperature_celsius = Column(Float, nullable=True)
    
    gcs_total = Column(Integer, nullable=True)
    avpu = Column(String, nullable=True)
    pain_score = Column(Integer, nullable=True)
    
    measured_at = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    voided = Column(Boolean, default=False)
