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


# ── FORM 100 ─────────────────────────────────────────────────────────────
class Form100Stub(BaseModel):
    issued_at: Optional[datetime] = None
    isolation_flag: Optional[bool] = False
    urgent_care_flag: Optional[bool] = False
    sanitary_processing_flag: Optional[bool] = False


class Form100FrontSideIdentity(BaseModel):
    rank: Optional[str] = None
    unit_name: Optional[str] = None
    full_name: Optional[str] = None
    identity_document: Optional[str] = None
    personal_number: Optional[str] = None
    sex: Optional[str] = None


class Form100BodyDiagramMark(BaseModel):
    wound_mark_type: Optional[str] = None
    wound_mark_location: Optional[str] = None
    wound_mark_notes: Optional[str] = None


class Form100FrontSideBodyDiagram(BaseModel):
    body_diagram_marks: List[Form100BodyDiagramMark] = Field(default_factory=list)
    placeholder_model: Optional[str] = None


class Form100FrontSideInjury(BaseModel):
    injury_or_illness_datetime: Optional[datetime] = None
    sanitary_loss_type: Optional[str] = None
    injury_category_codes: List[str] = Field(default_factory=list)
    tourniquet_applied_at: Optional[datetime] = None
    diagnosis: Optional[str] = None
    # Legacy compatibility field preserved for summary payloads.
    injury_mechanism: Optional[str] = None
    body_diagram_marks: List[Form100BodyDiagramMark] = Field(default_factory=list)


class Form100FrontSideTreatment(BaseModel):
    antibiotic: Optional[str] = None
    serum_pps_pgs: Optional[str] = None
    anatoxin: Optional[str] = None
    antidote: Optional[str] = None
    painkiller: Optional[str] = None
    blood_transfusion: Optional[str] = None
    blood_substitutes: Optional[str] = None
    immobilization: Optional[str] = None
    bandaging: Optional[str] = None
    sanitary_processing_type: Optional[str] = None
    treatment_notes: Optional[str] = None


class Form100FrontSideEvacuation(BaseModel):
    evacuation_transport: Optional[str] = None
    evacuation_destination: Optional[str] = None
    evacuation_position: Optional[str] = None
    evacuation_priority: Optional[str] = None
    recommendation_notes: Optional[str] = None


class Form100FrontSideTriageMarkers(BaseModel):
    red_urgent_care: Optional[bool] = False
    yellow_sanitary_processing: Optional[bool] = False
    black_isolation: Optional[bool] = False
    blue_radiation_measures: Optional[bool] = False


class Form100FrontSide(BaseModel):
    identity: Optional[Form100FrontSideIdentity] = None
    injury: Optional[Form100FrontSideInjury] = None
    treatment: Optional[Form100FrontSideTreatment] = None
    evacuation: Optional[Form100FrontSideEvacuation] = None
    triage_markers: Optional[Form100FrontSideTriageMarkers] = None
    body_diagram: Optional[Form100FrontSideBodyDiagram] = None


class Form100BackSideStageEntry(BaseModel):
    arrived_at: Optional[datetime] = None
    stage_name: Optional[str] = None
    physician_notes: Optional[str] = None
    refined_diagnosis: Optional[str] = None
    self_exited: Optional[bool] = False
    carried_by: Optional[str] = None
    care_provided: Optional[str] = None
    time_after_injury: Optional[str] = None
    first_aid_provided: Optional[str] = None
    evacuate_to_when: Optional[str] = None
    result: Optional[str] = None


class Form100BackSideSignature(BaseModel):
    physician_name: Optional[str] = None
    physician_signature: Optional[str] = None
    signed_at: Optional[datetime] = None


class Form100BackSide(BaseModel):
    stage_log: List[Form100BackSideStageEntry] = Field(default_factory=list)
    signature: Optional[Form100BackSideSignature] = None


class Form100MetaLegalRules(BaseModel):
    legal_status: Optional[str] = None
    first_eme_completed: Optional[bool] = False
    continuity_required: Optional[bool] = False
    commander_notified: Optional[bool] = None
    additional_notes: Optional[str] = None


class Form100Create(BaseModel):
    # Mandatory fields
    document_number: Optional[str] = Field(default=None, min_length=1, max_length=STR_SHORT)
    injury_datetime: Optional[datetime] = None
    injury_location: Optional[str] = Field(default=None, min_length=1, max_length=500)
    injury_mechanism: Optional[str] = Field(default=None, min_length=1, max_length=500)
    diagnosis_summary: Optional[str] = Field(default=None, min_length=1, max_length=STR_LONG)
    documented_by: Optional[str] = Field(default=None, min_length=1, max_length=STR_SHORT)

    # Optional fields
    treatment_summary: Optional[str] = Field(default=None, max_length=STR_LONG)
    evacuation_recommendation: Optional[str] = Field(default=None, max_length=STR_LONG)
    commander_notified: Optional[bool] = False
    notes: Optional[str] = Field(default=None, max_length=STR_LONG)

    # Canonical official structure
    stub: Optional[Form100Stub] = None
    front_side: Optional[Form100FrontSide] = None
    back_side: Optional[Form100BackSide] = None
    meta_legal_rules: Optional[Form100MetaLegalRules] = None

    @model_validator(mode="after")
    def ensure_legacy_required_fields(self):
        injury = self.front_side.injury if self.front_side else None
        if injury:
            if self.injury_datetime is None and injury.injury_or_illness_datetime is not None:
                self.injury_datetime = injury.injury_or_illness_datetime
            if self.diagnosis_summary is None and injury.diagnosis:
                self.diagnosis_summary = injury.diagnosis
            if self.injury_mechanism is None and injury.injury_mechanism:
                self.injury_mechanism = injury.injury_mechanism
            if self.injury_location is None:
                first_mark = next((m for m in injury.body_diagram_marks if m.wound_mark_location), None)
                if first_mark is not None:
                    self.injury_location = first_mark.wound_mark_location

        treatment = self.front_side.treatment if self.front_side else None
        if self.treatment_summary is None and treatment and treatment.treatment_notes:
            self.treatment_summary = treatment.treatment_notes

        evacuation = self.front_side.evacuation if self.front_side else None
        if self.evacuation_recommendation is None and evacuation and evacuation.recommendation_notes:
            self.evacuation_recommendation = evacuation.recommendation_notes

        signature = self.back_side.signature if self.back_side else None
        if self.documented_by is None and signature and signature.physician_name:
            self.documented_by = signature.physician_name

        required = {
            "document_number": self.document_number,
            "injury_datetime": self.injury_datetime,
            "injury_location": self.injury_location,
            "injury_mechanism": self.injury_mechanism,
            "diagnosis_summary": self.diagnosis_summary,
            "documented_by": self.documented_by,
        }
        missing = [field for field, value in required.items() if value in (None, "")]
        if missing:
            raise ValueError(f"Missing required Form100 fields: {', '.join(missing)}")
        return self


class Form100Update(BaseModel):
    document_number: Optional[str] = Field(default=None, min_length=1, max_length=STR_SHORT)
    injury_datetime: Optional[datetime] = None
    injury_location: Optional[str] = Field(default=None, min_length=1, max_length=500)
    injury_mechanism: Optional[str] = Field(default=None, min_length=1, max_length=500)
    diagnosis_summary: Optional[str] = Field(default=None, min_length=1, max_length=STR_LONG)
    documented_by: Optional[str] = Field(default=None, min_length=1, max_length=STR_SHORT)
    treatment_summary: Optional[str] = Field(default=None, max_length=STR_LONG)
    evacuation_recommendation: Optional[str] = Field(default=None, max_length=STR_LONG)
    commander_notified: Optional[bool] = None
    notes: Optional[str] = Field(default=None, max_length=STR_LONG)
    stub: Optional[Form100Stub] = None
    front_side: Optional[Form100FrontSide] = None
    back_side: Optional[Form100BackSide] = None
    meta_legal_rules: Optional[Form100MetaLegalRules] = None


class Form100Response(BaseModel):
    document_number: str
    injury_datetime: datetime
    injury_location: str
    injury_mechanism: str
    diagnosis_summary: str
    documented_by: str
    treatment_summary: Optional[str] = None
    evacuation_recommendation: Optional[str] = None
    commander_notified: Optional[bool] = False
    notes: Optional[str] = None

    stub: Optional[Form100Stub] = None
    front_side: Optional[Form100FrontSide] = None
    back_side: Optional[Form100BackSide] = None
    meta_legal_rules: Optional[Form100MetaLegalRules] = None

    id: str
    case_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
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
    form100: Optional[Form100Response] = None
    evacuation: Optional[EvacuationResponse] = None
    events: List[EventResponse] = []
