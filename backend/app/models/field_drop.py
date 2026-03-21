"""Field-drop logistics models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FieldPosition(Base):
    __tablename__ = "field_positions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_field_positions_name", "name"),
    )


class FieldInventoryItem(Base):
    __tablename__ = "field_inventory_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    position_id: Mapped[str] = mapped_column(String, ForeignKey("field_positions.id"), nullable=False)
    item_name: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_field_inventory_items_item_name", "item_name"),
        Index("ix_field_inventory_items_position_item", "position_id", "item_name"),
    )


class FieldSupplyRequest(Base):
    __tablename__ = "field_supply_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    urgency: Mapped[str] = mapped_column(String, default="high", nullable=False)
    radius_km: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    status: Mapped[str] = mapped_column(String, default="ACTIVE", nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

        finalized_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
        finalized_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
        finalize_method: Mapped[Optional[str]] = mapped_column(String, nullable=True)
        finalize_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix_field_supply_requests_created_at", "created_at"),)


class FieldSupplyNeed(Base):
    __tablename__ = "field_supply_needs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    request_id: Mapped[str] = mapped_column(String, ForeignKey("field_supply_requests.id"), nullable=False)
    item_name: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (Index("ix_field_supply_needs_request_id", "request_id"),)


class FieldDispatchLog(Base):
    __tablename__ = "field_dispatch_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    request_id: Mapped[str] = mapped_column(String, ForeignKey("field_supply_requests.id"), nullable=False)
    position_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("field_positions.id"), nullable=True)
    position_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    item_name: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eta_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, default="RECOMMENDED", nullable=False)
    request_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    dispatched_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("ix_field_dispatch_logs_created_at", "created_at"),)
