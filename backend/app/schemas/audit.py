"""Audit log schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AuditLogBase(BaseModel):
    """Base schema for audit log entry."""

    table: str = Field(..., serialization_alias="table_name")
    record_id: Optional[str] = None
    action: str
    changes: Optional[dict[str, Any]] = None
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None


class AuditLogResponse(AuditLogBase):
    """Schema for audit log response."""

    id: str
    table: str = Field(..., serialization_alias="table_name")

    model_config = {"from_attributes": True, "populate_by_name": True}
