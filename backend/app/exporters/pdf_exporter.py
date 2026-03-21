"""PDF exporter — real PDF bytes via ReportLab."""
from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.mappers.form100 import build_form100, validate_form100_minimum


def export_case_to_pdf(case: dict[str, Any]) -> bytes:
    """Export case to PDF bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("MEDEVAK — Combat Casualty Record", styles["Title"]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(f"<b>Case ID:</b> {case.get('id', '—')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Triage:</b> {case.get('triage_code', '—')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Mechanism:</b> {case.get('mechanism_of_injury') or case.get('mechanism') or '—'}", styles["Normal"]))
    story.append(Paragraph(f"<b>Notes:</b> {case.get('notes', '—')}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

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

    form100 = build_form100(case)
    form100_errors = validate_form100_minimum(form100)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Form 100 Canonical Summary", styles["Heading2"]))
    form100_data = [
        ["Standard", str(form100.get("standard", "—"))],
        ["Version", str(form100.get("version", "—"))],
        ["Case ID", str(form100.get("identity", {}).get("case_id") or "—")],
        ["Triage", str(form100.get("triage", {}).get("category") or "—")],
        ["Mechanism", str(form100.get("incident", {}).get("mechanism") or "—")],
        ["Validation", "OK" if not form100_errors else "; ".join(form100_errors)],
    ]
    form100_table = Table(form100_data, colWidths=[5 * cm, 10 * cm])
    form100_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), "#f2f2f2"),
                ("GRID", (0, 0), (-1, -1), 0.5, "#ccc"),
            ]
        )
    )
    story.append(form100_table)

    doc.build(story)
    return buffer.getvalue()
