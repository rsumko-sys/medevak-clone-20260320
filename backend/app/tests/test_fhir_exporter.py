"""FHIR exporter tests — minimal stub."""
import pytest
from app.core.fhir_integration import FHIRMapper, FHIR_AVAILABLE
from app.exporters.fhir_exporter import export_case_to_fhir, validate_fhir_bundle
from app.models.vitals import VitalsObservation


def test_export_case_to_fhir_returns_bundle(sample_case):
    """Export returns FHIR Bundle structure."""
    result = export_case_to_fhir(sample_case)
    assert result["resourceType"] == "Bundle"
    assert "entry" in result


def test_validate_fhir_bundle_checks_resource_types(sample_case):
    result = export_case_to_fhir(sample_case)
    errors = validate_fhir_bundle(result)
    assert errors == []


def test_vitals_map_to_loinc_coded_observations():
    if not FHIR_AVAILABLE:
        pytest.skip("fhir.resources is not available in current environment")

    obs = VitalsObservation(
        id="obs-1",
        case_id="case-1",
        heart_rate=110,
        respiratory_rate=22,
        systolic_bp=95,
        diastolic_bp=60,
        spo2_percent=93,
        temperature_celsius=36.8,
        gcs_total=14,
        pain_score=6,
        avpu="V",
    )
    mapped = FHIRMapper.observations_to_observations([obs])
    loinc_observations = []
    for item in mapped:
        code = item.dict(exclude_none=True).get("code", {})
        coding = code.get("coding", []) if isinstance(code, dict) else []
        if any(c.get("system") == "http://loinc.org" for c in coding if isinstance(c, dict)):
            loinc_observations.append(item)
    assert len(loinc_observations) >= 6
