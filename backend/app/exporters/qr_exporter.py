"""QR exporter — compact payload for QR encoding."""
from typing import Any

from app.mappers.case_to_qr import map_case_to_qr_payload


def export_case_to_qr(case: dict[str, Any]) -> str:
    """Export case to QR-encodable string (compact JSON)."""
    return map_case_to_qr_payload(case)
