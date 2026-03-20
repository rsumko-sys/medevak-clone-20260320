"""Case model."""
from datetime import datetime
from sqlalchemy import Column, Index, String, Text, DateTime, Float, Boolean, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (Index("ix_cases_created_at", "created_at"),)
    
    id = Column(String, primary_key=True)
    case_number = Column(String, nullable=True)
    
    # Patient identity
    callsign = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    rank = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    sex = Column(String, nullable=True)
    approx_age = Column(Integer, nullable=True)
    blood_type = Column(String, nullable=True)
    dob = Column(String, nullable=True)
    allergies = Column(Text, nullable=True)
    
    # Incident
    incident_time = Column(String, nullable=True)
    incident_location = Column(String, nullable=True)
    geo_lat = Column(Float, nullable=True)
    geo_lon = Column(Float, nullable=True)
    
    # Medical Baseline
    mechanism_of_injury = Column(String, nullable=True)
    mechanism = Column(Text, nullable=True)
    triage_code = Column(String, nullable=True)  # IMMEDIATE, DELAYED...
    case_status = Column(String, nullable=True, default="ACTIVE")
    notes = Column(Text, nullable=True)
    
    # TQ
    tourniquet_applied = Column(Boolean, default=False)
    tourniquet_time = Column(String, nullable=True)
    
    # Sync metadata
    sync_state = Column(String, nullable=True, default="NEW")
    server_version = Column(Integer, default=1)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)

    # Relationships are handled dynamically or by explicit queries
