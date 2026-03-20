"""QR exporter tests."""
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
