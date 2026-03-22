"""Revoked refresh tokens — server-side JWT revocation list."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.core.database import Base


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    jti = Column(String, primary_key=True, index=True)  # JWT ID (unique token identifier)
    expires_at = Column(DateTime, nullable=False)         # Auto-purge when expired
    revoked_at = Column(DateTime, default=datetime.utcnow)
