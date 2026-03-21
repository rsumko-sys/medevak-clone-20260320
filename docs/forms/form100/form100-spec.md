# Form 100 Official Specification

## Source of Truth

- Original document: docs/forms/form100/form100-original.docx
- Artifact name: Form 100 / Первинна медична картка (ПМК)

## Purpose and Legal Meaning

Form 100 is a legal medical document, not an optional note.

Non-negotiable legal semantics:
- Officially records injury/illness and continuity of care.
- Applied to casualties who are out of action for at least 24 hours.
- Stub/root and front side are initiated at the first EME stage.
- Back side continues records across subsequent EME stages.
- Colored edge markers are operational signals, not visual decoration.

## Logical Structure

### 1) Stub / Root (Корінець)

Captures issuance and operational markers at first registration.

Core semantics:
- Unique issuance context.
- Immediate marker flags relevant to routing and care.

Representative fields:
- issued_at
- isolation_flag
- urgent_care_flag
- sanitary_processing_flag

### 2) Front Side: Identity and Administrative Block

Identifies casualty and service context.

Representative fields:
- rank
- unit_name
- full_name
- identity_document
- personal_number
- sex

### 3) Front Side: Injury/Illness Block

Captures primary incident and clinical baseline.

Representative fields:
- injury_or_illness_datetime
- sanitary_loss_type
- injury_category_codes
- tourniquet_applied_at
- diagnosis
- body_diagram_marks

### 4) Front Side: Treatment Block

Must preserve administered substances/interventions and dose semantics where applicable.

Representative fields:
- antibiotic
- serum_pps_pgs
- anatoxin
- antidote
- painkiller
- blood_transfusion
- blood_substitutes
- immobilization
- bandaging
- sanitary_processing_type

### 5) Front Side: Evacuation Block

Captures evacuation routing semantics.

Representative fields:
- evacuation_transport
- evacuation_destination
- evacuation_position
- evacuation_priority

### 6) Front Side: Triage/Edge Indicators Block

Operational coded markers (colored edges) that must be retained as first-class values.

Markers:
- red_urgent_care
- yellow_sanitary_processing
- black_isolation
- blue_radiation_measures

### 7) Front Side: Body Diagram Semantics

Body diagram/wound marks are not free text only. Must preserve:
- mark location context
- mark type/category semantics
- traceability to injury block

If full graphic model is unavailable, use an explicit placeholder structure with TODO, never silent omission.

### 8) Back Side: Repeated Stage Log

This is a repeatable sequence of care-stage entries across EME chain.

Each stage entry includes:
- arrived_at
- stage_name
- physician_notes
- refined_diagnosis
- self_exited
- carried_by
- care_provided
- time_after_injury
- first_aid_provided
- evacuate_to_when
- result

### 9) Back Side: Signature/Outcome Block

Must preserve accountability and legal closure data.

Representative fields:
- physician_name
- physician_signature
- signed_at

## Preservation Rules

1. Do not collapse official structure into summary-only schema.
2. Preserve stub/root, front side, and back side as distinct logical parts.
3. Preserve coded markers and evacuation semantics.
4. Preserve treatment and dosage semantics.
5. Preserve repeatable back-side stage continuity.
6. Preserve legal meaning as a first-class requirement.
