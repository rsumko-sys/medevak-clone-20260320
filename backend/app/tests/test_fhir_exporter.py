"""FHIR exporter tests — minimal stub."""
import pytest
from app.exporters.fhir_exporter import export_case_to_fhir


def test_export_case_to_fhir_returns_bundle(sample_case):
    """Export returns FHIR Bundle structure."""
    result = export_case_to_fhir(sample_case)
    assert result["resourceType"] == "Bundle"
    assert "entry" in result
