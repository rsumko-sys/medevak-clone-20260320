"""Form 100 model."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from app.core.database import Base


class Form100Record(Base):
    __tablename__ = "form_100_records"

    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    # Mandatory business fields
    document_number = Column(String, nullable=False)
    injury_datetime = Column(DateTime, nullable=False)
    injury_location = Column(String, nullable=False)
    injury_mechanism = Column(String, nullable=False)
    diagnosis_summary = Column(Text, nullable=False)
    documented_by = Column(String, nullable=False)

    # Optional details
    treatment_summary = Column(Text, nullable=True)
    evacuation_recommendation = Column(Text, nullable=True)
    commander_notified = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    voided = Column(Boolean, default=False)
