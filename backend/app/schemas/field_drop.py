"""Field-drop logistics schemas."""
from datetime import datetime
from typing import Literal, Optional

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

        finalized_at: Optional[str] = None
        finalized_by: Optional[str] = None
        finalize_method: Optional[str] = None
        finalize_note: Optional[str] = None


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


class FieldAppliedRow(BaseModel):
    position_id: Optional[str] = None
    position: Optional[str] = None
    item_name: str
    qty: int
    distance_km: Optional[float] = None
    eta_min: Optional[int] = None
    status: Literal["APPLIED", "SKIPPED", "FAILED"]


class FieldShortage(BaseModel):
    item_name: str
    missing_qty: int = Field(ge=0)


class FieldCommitResponse(BaseModel):
    request_id: str
    ok: bool
    already_committed: bool
    request_status: str
    committed_at: Optional[datetime] = None
    applied: list[FieldAppliedRow]
    shortages: list[FieldShortage] = Field(default_factory=list)
    messages: list[str]
    logs_created: int = 0
    log_ids: list[str] = Field(default_factory=list)


    class FieldFinalizePayload(BaseModel):
        result: Literal["completed"]
        method: Literal["RADIO", "DISCORD", "VOICE", "MANUAL"]
        note: Optional[str] = None


    class FieldFinalizeResponse(BaseModel):
        request_id: str
        ok: bool
        previous_status: str
        request_status: str
        finalized_at: Optional[str] = None
        finalized_by: Optional[str] = None
        method: str
        note: Optional[str] = None
