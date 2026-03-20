"""PDF exporter tests."""
import pytest
from app.exporters.pdf_exporter import export_case_to_pdf


def test_export_case_to_pdf_returns_bytes(sample_case):
    """Export returns bytes."""
    result = export_case_to_pdf(sample_case)
    assert isinstance(result, bytes)


def test_export_case_to_pdf_empty_case():
    """Export handles empty case (returns valid PDF)."""
    result = export_case_to_pdf({})
    assert isinstance(result, bytes)
    assert result.startswith(b"%PDF")
