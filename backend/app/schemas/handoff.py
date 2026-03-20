"""Handoff schemas."""
from pydantic import BaseModel


class HandoffUpdateRequest(BaseModel):
    mist_summary: str | None = None


class HandoffConfirmRequest(BaseModel):
    confirmed_by: str | None = None
