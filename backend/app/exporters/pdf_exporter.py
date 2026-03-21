"""PDF exporter — real PDF bytes via ReportLab."""
from io import BytesIO
import json
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def export_case_to_pdf(case: dict[str, Any]) -> bytes:
    """Export case to PDF bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        pageCompression=0,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("MEDEVAK — Combat Casualty Record", styles["Title"]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(f"<b>Case ID:</b> {case.get('id', '—')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Triage:</b> {case.get('triage_code', '—')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Mechanism:</b> {case.get('mechanism_of_injury') or case.get('mechanism') or '—'}", styles["Normal"]))
    story.append(Paragraph(f"<b>Notes:</b> {case.get('notes', '—')}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    form_100 = case.get("form_100") or {}
    if form_100.get("id"):
        story.append(Paragraph("Form 100 (Official Injury Record)", styles["Heading2"]))
        form_data = [
            ["Document #", str(form_100.get("document_number") or "—")],
            ["Injury Datetime", str(form_100.get("injury_datetime") or "—")],
            ["Injury Location", str(form_100.get("injury_location") or "—")],
            ["Injury Mechanism", str(form_100.get("injury_mechanism") or "—")],
            ["Diagnosis", str(form_100.get("diagnosis_summary") or "—")],
            ["Documented By", str(form_100.get("documented_by") or "—")],
        ]
        t = Table(form_data, colWidths=[4 * cm, 11 * cm])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, "#ccc")]))
        story.append(t)
        story.append(Spacer(1, 0.3 * cm))

        canonical_rows = []
        if form_100.get("stub"):
            canonical_rows.append(["Stub", json.dumps(form_100.get("stub"), ensure_ascii=False)])
        if form_100.get("front_side"):
            canonical_rows.append(["Front Side", json.dumps(form_100.get("front_side"), ensure_ascii=False)])
        if form_100.get("back_side"):
            canonical_rows.append(["Back Side", json.dumps(form_100.get("back_side"), ensure_ascii=False)])
        if form_100.get("meta_legal_rules"):
            canonical_rows.append(["Meta Legal Rules", json.dumps(form_100.get("meta_legal_rules"), ensure_ascii=False)])

        if canonical_rows:
            story.append(Paragraph("Form 100 Canonical Sections", styles["Heading3"]))
            t2 = Table([["Section", "Payload"], *canonical_rows], colWidths=[4 * cm, 11 * cm])
            t2.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), "#e0e0e0"), ("GRID", (0, 0), (-1, -1), 0.5, "#ccc")]))
            story.append(t2)
            story.append(Spacer(1, 0.3 * cm))

    march_notes = case.get("march_notes") or {}
    march_rows = [
        ["M", str(march_notes.get("m_notes") or "—")],
        ["A", str(march_notes.get("a_notes") or "—")],
        ["R", str(march_notes.get("r_notes") or "—")],
        ["C", str(march_notes.get("c_notes") or "—")],
        ["H", str(march_notes.get("h_notes") or "—")],
    ]
    if any(row[1] != "—" for row in march_rows):
        story.append(Paragraph("MARCH Notes", styles["Heading2"]))
        t = Table([["Block", "Notes"], *march_rows])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), "#e0e0e0"), ("GRID", (0, 0), (-1, -1), 0.5, "#ccc")]))
        story.append(t)
        story.append(Spacer(1, 0.3 * cm))

    obs = case.get("observations") or []
    if obs:
        story.append(Paragraph("Observations", styles["Heading2"]))
        data = [["Type", "Value"]] + [[str(o.get("observation_type", "—")), str(o.get("value", "—"))] for o in obs]
        t = Table(data)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), "#e0e0e0"), ("GRID", (0, 0), (-1, -1), 0.5, "#ccc")]))
        story.append(t)
        story.append(Spacer(1, 0.3 * cm))

    meds = case.get("medications") or []
    if meds:
        story.append(Paragraph("Medications", styles["Heading2"]))
        data = [["Code", "Dose", "Unit"]] + [
            [str(m.get("medication_code", "—")), str(m.get("dose_value", "—")), str(m.get("dose_unit_code", "—"))]
            for m in meds
        ]
        t = Table(data)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), "#e0e0e0"), ("GRID", (0, 0), (-1, -1), 0.5, "#ccc")]))
        story.append(t)
        story.append(Spacer(1, 0.3 * cm))

    procs = case.get("procedures") or []
    if procs:
        story.append(Paragraph("Procedures", styles["Heading2"]))
        data = [["Code", "Notes"]] + [[str(p.get("procedure_code", "—")), str(p.get("notes", "—"))] for p in procs]
        t = Table(data)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), "#e0e0e0"), ("GRID", (0, 0), (-1, -1), 0.5, "#ccc")]))
        story.append(t)

    doc.build(story)
    return buffer.getvalue()
