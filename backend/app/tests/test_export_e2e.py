"""Export E2E tests — minimal stub."""
import pytest
from app.exporters.fhir_exporter import export_case_to_fhir
from app.exporters.pdf_exporter import export_case_to_pdf
from app.exporters.qr_exporter import export_case_to_qr


def test_export_e2e_all_formats(sample_case):
    """All exporters accept sample case without error."""
    fhir = export_case_to_fhir(sample_case)
    assert fhir["resourceType"] == "Bundle"

    pdf = export_case_to_pdf(sample_case)
    assert isinstance(pdf, bytes)

    qr = export_case_to_qr(sample_case)
    assert isinstance(qr, str)
