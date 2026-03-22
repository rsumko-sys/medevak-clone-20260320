"""Blood inventory schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


BLOOD_TYPES = (
    "O+",
    "O-",
    "A+",
    "A-",
    "B+",
    "B-",
    "AB+",
    "AB-",
    "LTOWB",
)


def normalize_blood_type(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in BLOOD_TYPES:
        raise ValueError("Unsupported blood type")
    return normalized


class BloodInventoryResponse(BaseModel):
    blood_type: str
    quantity: int
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BloodInventoryAdjustRequest(BaseModel):
    delta: int = Field(..., ge=-1000, le=1000, description="Positive or negative inventory change")
    reason: str = Field(..., min_length=1, max_length=100)
    case_id: Optional[str] = Field(default=None, max_length=100)

    @field_validator("delta")
    @classmethod
    def validate_delta(cls, value: int) -> int:
        if value == 0:
            raise ValueError("delta cannot be zero")
        return value

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        return value.strip()