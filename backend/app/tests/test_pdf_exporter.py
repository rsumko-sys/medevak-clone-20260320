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


def test_export_case_to_pdf_renders_form100_canonical_sections():
    result = export_case_to_pdf({
        "id": "case-2",
        "form_100": {
            "id": "f100-1",
            "document_number": "F100-PDF-01",
            "injury_datetime": "2026-03-21T10:15:00Z",
            "injury_location": "Sector C",
            "injury_mechanism": "BLAST",
            "diagnosis_summary": "Polytrauma",
            "documented_by": "Medic-03",
            "stub": {"urgent_care_flag": True},
            "front_side": {"triage_markers": {"red_urgent_care": True}},
            "back_side": {"stage_log": [{"stage_name": "ROLE_1"}]},
            "meta_legal_rules": {"continuity_required": True},
        },
    })
    assert isinstance(result, bytes)
    assert b"Form 100 Canonical Sections" in result
