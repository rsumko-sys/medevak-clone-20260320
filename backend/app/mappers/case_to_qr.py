"""Case to QR payload mapper — compact JSON for QR encoding."""
from typing import Any
import json

from app.mappers.form100 import build_form100


def map_case_to_qr_payload(case: dict[str, Any]) -> str:
    """Map case to compact JSON string for QR code."""
    form100 = build_form100(case)
    payload = {
        "id": case.get("id", ""),
        "m": case.get("mechanism_of_injury") or case.get("mechanism") or "",
        "t": case.get("triage_code", ""),
        "n": case.get("notes", ""),
        "o": [{"t": o.get("observation_type"), "v": o.get("value")} for o in (case.get("observations") or [])],
        "med": [{"c": m.get("medication_code"), "d": m.get("dose_value"), "u": m.get("dose_unit_code")} for m in (case.get("medications") or [])],
        "p": [{"c": p.get("procedure_code"), "n": p.get("notes")} for p in (case.get("procedures") or [])],
        "f100": {
            "std": form100.get("standard"),
            "v": form100.get("version"),
            "triage": form100.get("triage", {}).get("category"),
            "incident": form100.get("incident", {}).get("mechanism"),
        },
    }
    return json.dumps(payload, ensure_ascii=False)
