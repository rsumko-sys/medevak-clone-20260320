"""Case documents model."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey

from app.core.database import Base


class CaseDocument(Base):
    __tablename__ = "case_documents"
    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    filename = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
