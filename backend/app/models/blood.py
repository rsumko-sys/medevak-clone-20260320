"""Blood inventory and transaction models."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String

from app.core.database import Base


class BloodInventory(Base):
    __tablename__ = "blood_inventory"
    __table_args__ = (
        Index("ix_blood_inventory_unit", "unit"),
        Index("ix_blood_inventory_unit_type", "unit", "blood_type", unique=True),
    )

    id = Column(String, primary_key=True)
    unit = Column(String, nullable=False)
    blood_type = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BloodTransaction(Base):
    __tablename__ = "blood_transactions"
    __table_args__ = (
        Index("ix_blood_transactions_unit", "unit"),
        Index("ix_blood_transactions_created_at", "created_at"),
    )

    id = Column(String, primary_key=True)
    unit = Column(String, nullable=False)
    blood_type = Column(String, nullable=False)
    delta = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    case_id = Column(String, ForeignKey("cases.id"), nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)