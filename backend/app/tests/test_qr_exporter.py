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


def test_export_case_to_qr_includes_form100_canonical_block():
    result = export_case_to_qr({
        "id": "case-2",
        "form_100": {
            "document_number": "F100-QR-01",
            "stub": {"urgent_care_flag": True},
            "front_side": {"triage_markers": {"red_urgent_care": True}},
            "back_side": {"stage_log": [{"stage_name": "ROLE_1"}]},
            "meta_legal_rules": {"continuity_required": True},
        },
    })
    parsed = json.loads(result)
    assert "f100" in parsed
    assert parsed["f100"]["dn"] == "F100-QR-01"
    assert parsed["f100"]["s"]["urgent_care_flag"] is True
    assert parsed["f100"]["fs"]["triage_markers"]["red_urgent_care"] is True
