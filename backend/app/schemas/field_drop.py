"""Field-drop logistics schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InventorySnapshot(BaseModel):
    hemostatic: int = Field(default=0, ge=0)
    bandage: int = Field(default=0, ge=0)
    tourniquet: int = Field(default=0, ge=0)
    meds: dict[str, int] = Field(default_factory=dict)


class FieldPositionCreate(BaseModel):
    name: str
    x: float
    y: float
    inventory: InventorySnapshot = Field(default_factory=InventorySnapshot)


class FieldPositionResponse(BaseModel):
    id: str
    name: str
    x: float
    y: float
    updated_at: datetime
    inventory: InventorySnapshot

    model_config = ConfigDict(from_attributes=True)


class FieldNeedCreate(BaseModel):
    item_name: str
    qty: int = Field(ge=1)


class FieldRequestCreate(BaseModel):
    x: float
    y: float
    urgency: str = "high"
    radius_km: float = 5.0
    required: list[FieldNeedCreate] = Field(default_factory=list)


class FieldRequestResponse(BaseModel):
    id: str
    x: float
    y: float
    urgency: str
    radius_km: float
    status: str
    created_at: datetime
    required: list[FieldNeedCreate]

    model_config = ConfigDict(from_attributes=True)


class FieldRecommendationRow(BaseModel):
    position_id: Optional[str] = None
    position: Optional[str] = None
    item_name: str
    qty: int
    distance_km: Optional[float] = None
    score: Optional[float] = None
    eta_min: Optional[int] = None
    status: str = "RECOMMENDED"


class FieldRecommendationResponse(BaseModel):
    request_id: str
    urgency: str
    eta_min: Optional[int] = None
    eta_max: Optional[int] = None
    actions: list[FieldRecommendationRow]


class FieldCommitResponse(BaseModel):
    ok: bool
    applied: list[FieldRecommendationRow]
    messages: list[str]
