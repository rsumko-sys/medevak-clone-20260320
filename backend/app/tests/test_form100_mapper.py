"""Form100 mapper tests."""

from app.mappers.form100 import build_form100, validate_form100_minimum


def test_form100_build_contains_canonical_sections(sample_case):
    form100 = build_form100(sample_case)
    assert form100["standard"] == "MEDEVAK-FORM-100"
    assert form100["identity"]["case_id"] == sample_case["id"]
    assert form100["triage"]["category"] == "IMMEDIATE"
    assert form100["incident"]["mechanism"] == "BLAST"


def test_form100_minimum_validation_detects_missing_fields():
    form100 = {
        "identity": {"case_id": None},
        "triage": {"category": None},
        "incident": {"mechanism": None},
    }
    errors = validate_form100_minimum(form100)
    assert "identity.case_id is required" in errors
    assert "triage.category is required" in errors
    assert "incident.mechanism is required" in errors