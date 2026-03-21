"""Canonical Form 100 mapper and validation helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


def _value(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _to_dict_list(items: list[Any] | None, fields: tuple[str, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items or []:
        row = {field: _value(item, field) for field in fields}
        if any(v is not None and v != "" for v in row.values()):
            rows.append(row)
    return rows


def build_form100(case: Any) -> dict[str, Any]:
    """Build canonical Form 100 structure from a case-like object or dict."""
    generated_at = datetime.utcnow().isoformat()

    form100 = {
        "standard": "MEDEVAK-FORM-100",
        "version": "1.0",
        "generated_at": generated_at,
        "identity": {
            "case_id": _value(case, "id"),
            "case_number": _value(case, "case_number"),
            "callsign": _value(case, "callsign"),
            "full_name": _value(case, "full_name"),
            "rank": _value(case, "rank"),
            "unit": _value(case, "unit"),
            "sex": _value(case, "sex"),
            "approx_age": _value(case, "approx_age"),
            "blood_type": _value(case, "blood_type"),
            "allergies": _value(case, "allergies"),
        },
        "incident": {
            "time": _value(case, "incident_time"),
            "location": _value(case, "incident_location"),
            "geo": {
                "lat": _value(case, "geo_lat"),
                "lon": _value(case, "geo_lon"),
            },
            "mechanism": _value(case, "mechanism_of_injury") or _value(case, "mechanism"),
        },
        "triage": {
            "category": _value(case, "triage_code"),
            "status": _value(case, "case_status"),
        },
        "clinical": {
            "injuries": _to_dict_list(
                _value(case, "injuries") or [],
                ("body_region", "injury_type", "severity", "laterality", "notes", "icd10_code"),
            ),
            "vitals": _to_dict_list(
                _value(case, "observations") or [],
                (
                    "heart_rate",
                    "respiratory_rate",
                    "systolic_bp",
                    "diastolic_bp",
                    "spo2_percent",
                    "temperature_celsius",
                    "gcs_total",
                    "avpu",
                    "pain_score",
                    "measured_at",
                ),
            ),
            "procedures": _to_dict_list(
                _value(case, "procedures") or [],
                ("procedure_code", "site", "laterality", "performed_at", "success_status", "notes"),
            ),
            "medications": _to_dict_list(
                (_value(case, "medications") or _value(case, "sub_medications") or []),
                (
                    "medication_code",
                    "dose_value",
                    "dose_unit_code",
                    "route",
                    "time_administered",
                    "indication",
                    "status",
                    "notes",
                ),
            ),
            "tourniquet": {
                "applied": bool(_value(case, "tourniquet_applied", False)),
                "time": _value(case, "tourniquet_time"),
            },
            "notes": _value(case, "notes"),
        },
        "evacuation": {
            "priority": _value(_value(case, "evacuation"), "evacuation_priority"),
            "transport_type": _value(_value(case, "evacuation"), "transport_type"),
            "destination": _value(_value(case, "evacuation"), "destination"),
            "nine_line_sent": _value(_value(case, "evacuation"), "nine_line_sent"),
            "handoff_to": _value(_value(case, "evacuation"), "handoff_to"),
            "departed_at": _value(_value(case, "evacuation"), "departed_at"),
            "arrived_at": _value(_value(case, "evacuation"), "arrived_at"),
            "mist_summary": _value(_value(case, "evacuation"), "mist_summary"),
        },
    }

    return form100


def validate_form100_minimum(form100: dict[str, Any]) -> list[str]:
    """Validate minimum required fields for operational Form 100 exchange."""
    errors: list[str] = []
    identity = form100.get("identity", {})
    incident = form100.get("incident", {})
    triage = form100.get("triage", {})

    if not identity.get("case_id"):
        errors.append("identity.case_id is required")
    if not triage.get("category"):
        errors.append("triage.category is required")
    if not incident.get("mechanism"):
        errors.append("incident.mechanism is required")

    return errors