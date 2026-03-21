"""Case to QR payload mapper — compact JSON for QR encoding."""
from typing import Any
import json


def map_case_to_qr_payload(case: dict[str, Any]) -> str:
    """Map case to compact JSON string for QR code."""
    march_notes = case.get("march_notes") or {}
    payload = {
        "id": case.get("id", ""),
        "m": case.get("mechanism_of_injury") or case.get("mechanism") or "",
        "t": case.get("triage_code", ""),
        "n": case.get("notes", ""),
        "mn": {
            "m": march_notes.get("m_notes") or "",
            "a": march_notes.get("a_notes") or "",
            "r": march_notes.get("r_notes") or "",
            "c": march_notes.get("c_notes") or "",
            "h": march_notes.get("h_notes") or "",
        },
        "o": [{"t": o.get("observation_type"), "v": o.get("value")} for o in (case.get("observations") or [])],
        "med": [{"c": m.get("medication_code"), "d": m.get("dose_value"), "u": m.get("dose_unit_code")} for m in (case.get("medications") or [])],
        "p": [{"c": p.get("procedure_code"), "n": p.get("notes")} for p in (case.get("procedures") or [])],
    }
    return json.dumps(payload, ensure_ascii=False)
