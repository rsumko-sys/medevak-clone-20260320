"""Events model — domain event store."""
import uuid
from sqlalchemy import Column, String, DateTime, func, Index, JSON
from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)            # CASE_CREATED, BLOOD_USED…
    entity_type = Column(String, nullable=False)     # case | blood | evac
    entity_id = Column(String, nullable=False, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    unit = Column(String, index=True, nullable=False)
    created_by = Column(String, nullable=True)       # user id (sub)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_events_unit_created_at", "unit", "created_at"),
    )
