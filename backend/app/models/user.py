"""User model for auth."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean

from app.core.database import Base

VALID_ROLES = {"admin", "medic", "viewer"}


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    device_id = Column(String, nullable=True)
    role = Column(String, nullable=False, default="medic")
    unit = Column(String, nullable=True)  # Assigned unit for ABAC
    is_active = Column(Boolean, default=True)  # Session validation
    created_at = Column(DateTime, default=datetime.utcnow)

