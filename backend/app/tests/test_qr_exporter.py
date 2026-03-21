"""QR exporter tests."""
import json

import pytest
from app.exporters.qr_exporter import export_case_to_qr


def test_export_case_to_qr_returns_string(sample_case):
    """Export returns string for QR encoding."""
    result = export_case_to_qr(sample_case)
    assert isinstance(result, str)


def test_export_case_to_qr_empty_case():
    """Export handles empty case — returns compact JSON."""
    result = export_case_to_qr({})
    assert isinstance(result, str)
    assert "id" in result


def test_export_case_to_qr_includes_march_notes():
    """QR payload exposes compact MARCH notes block."""
    result = export_case_to_qr({
        "id": "case-1",
        "march_notes": {
            "m_notes": "m note",
            "a_notes": "a note",
            "r_notes": "r note",
            "c_notes": "c note",
            "h_notes": "h note",
        },
    })
    parsed = json.loads(result)
    assert "mn" in parsed
    assert parsed["mn"] == {
        "m": "m note",
        "a": "a note",
        "r": "r note",
        "c": "c note",
        "h": "h note",
    }
