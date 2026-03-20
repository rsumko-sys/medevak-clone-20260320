"""Field-drop logistics models."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String

from app.core.database import Base


class FieldPosition(Base):
    __tablename__ = "field_positions"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class FieldInventoryItem(Base):
    __tablename__ = "field_inventory_items"
    __table_args__ = (
        Index("ix_field_inventory_items_item_name", "item_name"),
        Index("ix_field_inventory_items_position_item", "position_id", "item_name"),
    )

    id = Column(String, primary_key=True)
    position_id = Column(String, ForeignKey("field_positions.id"), nullable=False)
    item_name = Column(String, nullable=False)
    qty = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class FieldSupplyRequest(Base):
    __tablename__ = "field_supply_requests"
    __table_args__ = (Index("ix_field_supply_requests_created_at", "created_at"),)

    id = Column(String, primary_key=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    urgency = Column(String, default="high", nullable=False)
    radius_km = Column(Float, default=5.0, nullable=False)
    status = Column(String, default="ACTIVE", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FieldSupplyNeed(Base):
    __tablename__ = "field_supply_needs"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("field_supply_requests.id"), nullable=False)
    item_name = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)


class FieldDispatchLog(Base):
    __tablename__ = "field_dispatch_logs"
    __table_args__ = (Index("ix_field_dispatch_logs_created_at", "created_at"),)

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("field_supply_requests.id"), nullable=False)
    position_id = Column(String, ForeignKey("field_positions.id"), nullable=True)
    position_name = Column(String, nullable=True)
    item_name = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    distance_km = Column(Float, nullable=True)
    eta_min = Column(Integer, nullable=True)
    status = Column(String, default="RECOMMENDED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
