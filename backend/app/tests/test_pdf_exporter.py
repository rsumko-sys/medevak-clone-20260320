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


def test_export_case_to_pdf_renders_march_notes_section():
    """PDF export includes MARCH notes section when notes are provided."""
    result = export_case_to_pdf({
        "id": "case-1",
        "march_notes": {
            "m_notes": "m note",
            "a_notes": "a note",
            "r_notes": "r note",
            "c_notes": "c note",
            "h_notes": "h note",
        },
    })
    assert isinstance(result, bytes)
    # ReportLab output contains plain text tokens for headings.
    assert b"MARCH Notes" in result
