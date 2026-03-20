"""Normalized Data Schemas."""
from datetime import datetime
from typing import Optional, List, Any, Literal
from pydantic import BaseModel, Field, StrictBool, model_validator

from app.core.config import ALLOW_GPS

STR_SHORT = 100
STR_MED = 200
STR_LONG = 4000


# ── INJURIES ─────────────────────────────────────────────────────────────
class InjuryCreate(BaseModel):
    body_region: str
    injury_type: str
    severity: Optional[str] = None
    laterality: Optional[str] = None
    mechanism: Optional[str] = None
    penetrating: Optional[bool] = False
    view: Optional[str] = None
    notes: Optional[str] = None
    icd10_code: Optional[str] = None


class InjuryResponse(InjuryCreate):
    id: str
    case_id: str
    created_at: datetime
    voided: bool

    class Config:
        from_attributes = True


# ── PROCEDURES ───────────────────────────────────────────────────────────
class ProcedureCreate(BaseModel):
    procedure_code: str
    site: Optional[str] = None
    laterality: Optional[str] = None
    performed_at: Optional[datetime] = None
    success_status: Optional[str] = "SUCCESS"
    notes: Optional[str] = None


class ProcedureResponse(ProcedureCreate):
    id: str
    case_id: str
    created_at: datetime
    voided: bool

    class Config:
        from_attributes = True


# ── MEDICATIONS ──────────────────────────────────────────────────────────
class MedicationCreate(BaseModel):
    medication_code: str
    dose_value: Optional[str] = None
    dose_unit_code: Optional[str] = None
    route: Optional[str] = None
    time_administered: Optional[datetime] = None
    indication: Optional[str] = None
    status: Optional[str] = "COMPLETED"
    notes: Optional[str] = None


class MedicationResponse(MedicationCreate):
    id: str
    case_id: str
    created_at: datetime
    voided: bool

    class Config:
        from_attributes = True


# ── VITALS ───────────────────────────────────────────────────────────────
class VitalsCreate(BaseModel):
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    spo2_percent: Optional[int] = None
    temperature_celsius: Optional[float] = None
    gcs_total: Optional[int] = None
    avpu: Optional[str] = None
    pain_score: Optional[int] = None
    measured_at: Optional[datetime] = None


class VitalsResponse(VitalsCreate):
    id: str
    case_id: str
    created_at: datetime
    voided: bool

    class Config:
        from_attributes = True


# ── MARCH ────────────────────────────────────────────────────────────────
class MarchCreate(BaseModel):
    assessed_at: Optional[datetime] = None
    m_massive_bleeding: Optional[bool] = False
    m_tourniquets_applied: Optional[int] = 0
    m_hemostatic_agent: Optional[bool] = False
    m_notes: Optional[str] = None
    a_airway_open: Optional[bool] = False
    a_airway_intervention: Optional[str] = None
    a_notes: Optional[str] = None
    r_breathing_rate: Optional[int] = None
    r_chest_seal_applied: Optional[bool] = False
    r_needle_d_performed: Optional[bool] = False
    r_chest_tube: Optional[bool] = False
    r_notes: Optional[str] = None
    c_radial_pulse: Optional[str] = None
    c_capillary_refill_time: Optional[str] = None
    c_pelvic_binder: Optional[bool] = False
    c_tibial_io: Optional[bool] = False
    c_sternal_io: Optional[bool] = False
    c_iv_access: Optional[bool] = False
    c_notes: Optional[str] = None
    h_hypothermia_prevented: Optional[bool] = False
    h_blanket_applied: Optional[bool] = False
    h_active_warming: Optional[bool] = False
    h_notes: Optional[str] = None


class MarchResponse(MarchCreate):
    id: str
    case_id: str
    created_at: datetime
    voided: bool

    class Config:
        from_attributes = True


# ── EVENTS ───────────────────────────────────────────────────────────────
class EventCreate(BaseModel):
    event_type: str
    event_time: Optional[datetime] = None
    actor_id: Optional[str] = None
    payload: Optional[Any] = None


class EventResponse(EventCreate):
    id: str
    case_id: str
    recorded_at: datetime
    voided: bool

    class Config:
        from_attributes = True


# ── EVACUATION ───────────────────────────────────────────────────────────
class EvacuationCreate(BaseModel):
    evacuation_priority: Optional[str] = None
    transport_type: Optional[str] = None
    destination: Optional[str] = None
    nine_line_sent: Optional[bool] = False
    handoff_to: Optional[str] = None
    mist_summary: Optional[str] = None
    departed_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None


class EvacuationResponse(EvacuationCreate):
    id: str
    case_id: str
    created_at: datetime
    voided: bool

    class Config:
        from_attributes = True


# ── CASES ────────────────────────────────────────────────────────────────
class CaseCreate(BaseModel):
    case_number: Optional[str] = Field(default=None, max_length=STR_SHORT)
    callsign: Optional[str] = Field(default=None, min_length=1, max_length=STR_SHORT)
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=STR_MED)
    rank: Optional[str] = Field(default=None, max_length=STR_SHORT)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=STR_SHORT)
    sex: Optional[str] = None
    approx_age: Optional[int] = Field(default=None, ge=0, le=120)
    blood_type: Optional[str] = Field(default=None, max_length=10)
    dob: Optional[str] = Field(default=None, max_length=20)
    allergies: Optional[str] = Field(default=None, max_length=STR_LONG)
    incident_time: Optional[str] = Field(default=None, max_length=50)
    incident_location: Optional[str] = Field(default=None, max_length=500)
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None
    mechanism_of_injury: Optional[str] = Field(default=None, max_length=500)
    mechanism: Optional[str] = Field(default=None, max_length=500)
    triage_code: Optional[Literal["IMMEDIATE", "DELAYED", "MINIMAL", "EXPECTANT", "DECEASED"]] = None
    case_status: Optional[Literal["ACTIVE", "STABILIZING", "AWAITING_EVAC", "IN_TRANSPORT", "HANDED_OFF", "CLOSED", "DECEASED", "VOIDED"]] = "ACTIVE"
    notes: Optional[str] = Field(default=None, max_length=STR_LONG)
    tourniquet_applied: Optional[StrictBool] = False
    tourniquet_time: Optional[str] = Field(default=None, max_length=50)
    # Optional batch injuries for transactional save
    injuries: Optional[List['InjuryCreate']] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_gps_policy(self):
        if not ALLOW_GPS and (self.geo_lat is not None or self.geo_lon is not None):
            raise ValueError("GPS coordinates are disabled by policy")
        return self


class CaseUpdate(BaseModel):
    case_number: Optional[str] = Field(default=None, max_length=STR_SHORT)
    callsign: Optional[str] = Field(default=None, min_length=1, max_length=STR_SHORT)
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=STR_MED)
    rank: Optional[str] = Field(default=None, max_length=STR_SHORT)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=STR_SHORT)
    sex: Optional[str] = None
    approx_age: Optional[int] = Field(default=None, ge=0, le=120)
    blood_type: Optional[str] = Field(default=None, max_length=10)
    dob: Optional[str] = Field(default=None, max_length=20)
    allergies: Optional[str] = Field(default=None, max_length=STR_LONG)
    incident_time: Optional[str] = Field(default=None, max_length=50)
    incident_location: Optional[str] = Field(default=None, max_length=500)
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None
    mechanism_of_injury: Optional[str] = Field(default=None, max_length=500)
    mechanism: Optional[str] = Field(default=None, max_length=500)
    triage_code: Optional[Literal["IMMEDIATE", "DELAYED", "MINIMAL", "EXPECTANT", "DECEASED"]] = None
    case_status: Optional[Literal["ACTIVE", "STABILIZING", "AWAITING_EVAC", "IN_TRANSPORT", "HANDED_OFF", "CLOSED", "DECEASED", "VOIDED"]] = None
    notes: Optional[str] = Field(default=None, max_length=STR_LONG)
    tourniquet_applied: Optional[StrictBool] = None
    tourniquet_time: Optional[str] = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def validate_gps_policy(self):
        if not ALLOW_GPS and (self.geo_lat is not None or self.geo_lon is not None):
            raise ValueError("GPS coordinates are disabled by policy")
        return self


class CaseResponse(BaseModel):
    id: str
    case_number: Optional[str] = None
    callsign: Optional[str] = None
    full_name: Optional[str] = None
    rank: Optional[str] = None
    unit: Optional[str] = None
    sex: Optional[str] = None
    approx_age: Optional[int] = None
    blood_type: Optional[str] = None
    dob: Optional[str] = None
    allergies: Optional[str] = None
    incident_time: Optional[str] = None
    incident_location: Optional[str] = None
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None
    mechanism_of_injury: Optional[str] = None
    mechanism: Optional[str] = None
    triage_code: Optional[str] = None
    case_status: Optional[str] = None
    notes: Optional[str] = None
    tourniquet_applied: Optional[bool] = False
    tourniquet_time: Optional[str] = None
    sync_state: Optional[str] = None
    server_version: int = 1
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class CaseDetailResponse(CaseResponse):
    injuries: List[InjuryResponse] = []
    procedures: List[ProcedureResponse] = []
    sub_medications: List[MedicationResponse] = []
    observations: List[VitalsResponse] = []  # Vitals
    march_assessments: List[MarchResponse] = []
    evacuation: Optional[EvacuationResponse] = None
    events: List[EventResponse] = []
