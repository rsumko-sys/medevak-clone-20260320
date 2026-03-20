"""Medication administration schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MedicationAdministrationBase(BaseModel):
    """Base schema for medication administration."""

    medication_code: Optional[str] = None
    dose_value: Optional[float] = None
    dose_unit_code: Optional[str] = None
    time_administered: Optional[datetime] = Field(
        default=None,
        serialization_alias="administered_at",
    )


class MedicationAdministrationCreate(MedicationAdministrationBase):
    """Schema for creating a medication administration."""

    case_id: str


class MedicationAdministrationResponse(MedicationAdministrationBase):
    """Schema for medication administration response."""

    id: str
    case_id: str
    time_administered: Optional[datetime] = Field(
        default=None,
        serialization_alias="administered_at",
    )

    model_config = {"from_attributes": True, "populate_by_name": True}
