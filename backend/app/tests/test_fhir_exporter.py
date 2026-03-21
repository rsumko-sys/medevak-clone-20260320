"""FHIR exporter tests — minimal stub."""
import pytest
from app.exporters.fhir_exporter import export_case_to_fhir


def test_export_case_to_fhir_returns_bundle(sample_case):
    """Export returns FHIR Bundle structure."""
    result = export_case_to_fhir(sample_case)
    assert result["resourceType"] == "Bundle"
    assert "entry" in result


def test_export_case_to_fhir_includes_march_notes_observation(sample_case):
    """MARCH notes are exposed as an Observation in FHIR bundle."""
    case = {
        **sample_case,
        "march_notes": {
            "m_notes": "m note",
            "a_notes": "a note",
            "r_notes": "r note",
            "c_notes": "c note",
            "h_notes": "h note",
        },
    }
    result = export_case_to_fhir(case)
    assert result["resourceType"] == "Bundle"

    # If FHIR resources are unavailable in environment, exporter returns fallback bundle.
    if result.get("error"):
        assert result["error"] == "FHIR resources not available"
        return

    notes_entries = [
        e for e in result.get("entry", [])
        if e.get("resource", {}).get("resourceType") == "Observation"
        and e.get("resource", {}).get("code", {}).get("text") == "MARCH Notes"
    ]
    assert len(notes_entries) == 1
    value = notes_entries[0]["resource"].get("valueString", "")
    assert "m_notes: m note" in value
    assert "a_notes: a note" in value
    assert "r_notes: r note" in value
    assert "c_notes: c note" in value
    assert "h_notes: h note" in value


def test_export_case_to_fhir_includes_form100_canonical_observations(sample_case):
    case = {
        **sample_case,
        "form_100": {
            "document_number": "F100-FHIR-01",
            "stub": {"urgent_care_flag": True},
            "front_side": {"triage_markers": {"red_urgent_care": True}},
            "back_side": {"stage_log": [{"stage_name": "ROLE_1"}]},
            "meta_legal_rules": {"continuity_required": True},
        },
    }
    result = export_case_to_fhir(case)
    assert result["resourceType"] == "Bundle"

    if result.get("error"):
        assert result["error"] == "FHIR resources not available"
        return

    code_texts = {
        e.get("resource", {}).get("code", {}).get("text")
        for e in result.get("entry", [])
        if e.get("resource", {}).get("resourceType") == "Observation"
    }
    assert "Form100 Stub" in code_texts
    assert "Form100 Front Side" in code_texts
    assert "Form100 Back Side" in code_texts
    assert "Form100 Meta Legal Rules" in code_texts
