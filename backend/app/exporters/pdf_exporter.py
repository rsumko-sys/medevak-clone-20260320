"""PDF exporter — compact A4 battle format with Ukrainian labels."""
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


FIELD_LABELS_UA = {
    "value": "Значення",
    "issued_at": "Дата/час видачі",
    "isolation_flag": "Ізоляція",
    "urgent_care_flag": "Термінова допомога",
    "sanitary_processing_flag": "Санітарна обробка",
    "identity": "Ідентифікація",
    "rank": "Звання",
    "unit_name": "Підрозділ",
    "full_name": "ПІБ",
    "identity_document": "Документ",
    "personal_number": "Особистий номер",
    "sex": "Стать",
    "injury": "Травма",
    "injury_or_illness_datetime": "Дата/час травми",
    "sanitary_loss_type": "Тип санітарних втрат",
    "injury_category_codes": "Коди категорії травми",
    "tourniquet_applied_at": "Час накладання турнікета",
    "diagnosis": "Діагноз",
    "injury_mechanism": "Механізм травми",
    "body_diagram_marks": "Мітки на схемі тіла",
    "wound_mark_type": "Тип мітки",
    "wound_mark_location": "Локалізація мітки",
    "wound_mark_notes": "Нотатки мітки",
    "treatment": "Лікування",
    "antibiotic": "Антибіотик",
    "serum_pps_pgs": "Сироватка PPS/PGS",
    "anatoxin": "Анатоксин",
    "antidote": "Антидот",
    "painkiller": "Знеболювальне",
    "blood_transfusion": "Переливання крові",
    "blood_substitutes": "Кровозамінники",
    "immobilization": "Іммобілізація",
    "bandaging": "Перев'язка",
    "sanitary_processing_type": "Тип санітарної обробки",
    "treatment_notes": "Нотатки лікування",
    "evacuation": "Евакуація",
    "evacuation_transport": "Транспорт евакуації",
    "evacuation_destination": "Пункт евакуації",
    "evacuation_position": "Положення пораненого",
    "evacuation_priority": "Пріоритет евакуації",
    "recommendation_notes": "Нотатки рекомендацій",
    "triage_markers": "Сортувальні маркери",
    "red_urgent_care": "Червоний: термінова допомога",
    "yellow_sanitary_processing": "Жовтий: санітарна обробка",
    "black_isolation": "Чорний: ізоляція",
    "blue_radiation_measures": "Синій: радіаційні заходи",
    "body_diagram": "Схема тіла",
    "placeholder_model": "Модель схеми",
    "stage_log": "Журнал етапів",
    "arrived_at": "Час прибуття",
    "stage_name": "Етап",
    "physician_notes": "Нотатки лікаря",
    "refined_diagnosis": "Уточнений діагноз",
    "self_exited": "Самовільно вибув",
    "carried_by": "Супровід",
    "care_provided": "Надана допомога",
    "time_after_injury": "Час після травми",
    "first_aid_provided": "Надана перша допомога",
    "evacuate_to_when": "Куди евакуювати далі",
    "result": "Результат",
    "signature": "Підпис",
    "physician_name": "ПІБ лікаря",
    "physician_signature": "Підпис лікаря",
    "signed_at": "Час підпису",
    "legal_status": "Правовий статус",
    "first_eme_completed": "1-й етап ЕМД завершено",
    "continuity_required": "Потрібна спадкоємність",
    "commander_notified": "Командира сповіщено",
    "additional_notes": "Додаткові нотатки",
}


def _to_display(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Так" if value else "Ні"
    return str(value)


def _flatten_payload(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []

    if isinstance(value, dict):
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten_payload(nested, path))
        return rows

    if isinstance(value, list):
        if not value:
            rows.append((prefix or "value", "[]"))
            return rows
        for idx, item in enumerate(value, start=1):
            path = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
            rows.extend(_flatten_payload(item, path))
        return rows

    rows.append((prefix or "value", _to_display(value)))
    return rows


def _localize_path(path: str) -> str:
    if not path:
        return FIELD_LABELS_UA["value"]

    localized_parts: list[str] = []
    for raw_part in path.split("."):
        if "[" in raw_part:
            base, tail = raw_part.split("[", 1)
            localized_base = FIELD_LABELS_UA.get(base, base)
            localized_parts.append(f"{localized_base} [{tail}")
        else:
            localized_parts.append(FIELD_LABELS_UA.get(raw_part, raw_part))
    return " / ".join(localized_parts)


def _rows_from_payload(payload: Any) -> list[tuple[str, str]]:
    return [(_localize_path(k), v) for k, v in _flatten_payload(payload)]


def _append_key_value_table(
    story: list[Any],
    title: str,
    rows: list[tuple[str, str]],
    col_widths: list[float],
    heading_style: ParagraphStyle,
    cell_style: ParagraphStyle,
) -> None:
    if not rows:
        return
    if title:
        story.append(Paragraph(escape(title), heading_style))

    table_data = [
        [Paragraph("<b>Поле</b>", cell_style), Paragraph("<b>Значення</b>", cell_style)],
        *[[Paragraph(escape(k), cell_style), Paragraph(escape(v), cell_style)] for k, v in rows],
    ]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), "#e0e0e0"),
                ("GRID", (0, 0), (-1, -1), 0.5, "#ccc"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.15 * cm))


def export_case_to_pdf(case: dict[str, Any]) -> bytes:
    """Export case to compact A4 PDF bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.3 * cm,
        leftMargin=1.3 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        pageCompression=0,
    )

    styles = getSampleStyleSheet()
    compact_title = ParagraphStyle("CompactTitle", parent=styles["Title"], fontSize=16, leading=18)
    compact_heading = ParagraphStyle(
        "CompactHeading",
        parent=styles["Heading4"],
        fontSize=10,
        leading=12,
        spaceAfter=2,
        spaceBefore=3,
    )
    compact_cell = ParagraphStyle("CompactCell", parent=styles["Normal"], fontSize=8, leading=9)

    story: list[Any] = []

    # ─────────────────────────────────────────────────────
    # СТОРІНКА 1 — КРИТИЧНІ ПОЛЯ (одним поглядом)
    # ─────────────────────────────────────────────────────
    story.append(Paragraph("MEDEVAK — Картка бойового поранення", compact_title))
    story.append(Paragraph("FORM 100 (ОФІЦІЙНИЙ ОБЛІК ПОРАНЕННЯ)", styles["Heading3"]))
    story.append(Spacer(1, 0.25 * cm))

    form_100 = case.get("form_100") or {}
    front_side_p1 = (form_100.get("front_side") or {})
    identity_p1   = (front_side_p1.get("identity") or {})
    injury_p1     = (front_side_p1.get("injury") or {})
    treatment_p1  = (front_side_p1.get("treatment") or {})
    evacuation_p1 = (front_side_p1.get("evacuation") or {})
    march_p1      = (case.get("march_notes") or {})

    critical_rows: list[tuple[str, str]] = [
        ("━━ ІДЕНТИФІКАЦІЯ", ""),
        ("ПІБ",             str(identity_p1.get("full_name") or "—")),
        ("Звання",          str(identity_p1.get("rank") or "—")),
        ("Підрозділ",       str(identity_p1.get("unit_name") or "—")),
        ("Особистий №",     str(identity_p1.get("personal_number") or "—")),
        ("Тріаж",           str(case.get("triage_code", "—"))),
        ("ID кейсу",        str(case.get("id", "—"))),
        ("━━ ТРАВМА", ""),
        ("Дата/час травми", str(injury_p1.get("injury_or_illness_datetime") or "—")),
        ("Механізм",        str(injury_p1.get("injury_mechanism") or case.get("mechanism_of_injury") or "—")),
        ("Діагноз",         str(injury_p1.get("diagnosis") or form_100.get("diagnosis_summary") or "—")),
        ("━━ ЛІКУВАННЯ", ""),
        ("Антибіотик",      _to_display(treatment_p1.get("antibiotic"))),
        ("Знеболювальне",   _to_display(treatment_p1.get("painkiller"))),
        ("Турнікет о",      str(injury_p1.get("tourniquet_applied_at") or "—")),
        ("━━ ЕВАКУАЦІЯ", ""),
        ("Транспорт",       str(evacuation_p1.get("evacuation_transport") or "—")),
        ("Пункт",           str(evacuation_p1.get("evacuation_destination") or "—")),
        ("Пріоритет",       str(evacuation_p1.get("evacuation_priority") or "—")),
        ("━━ MARCH", ""),
        ("M (Масивна кровотеча)", str(march_p1.get("m_notes") or "—")),
        ("A (Дихальні шляхи)",   str(march_p1.get("a_notes") or "—")),
        ("R (Дихання)",          str(march_p1.get("r_notes") or "—")),
        ("C (Кровообіг)",        str(march_p1.get("c_notes") or "—")),
        ("H (Гіпотермія)",       str(march_p1.get("h_notes") or "—")),
    ]

    # render critical summary — section headers (━━ rows) get a shaded style
    crit_title_style = ParagraphStyle(
        "CritTitle", parent=compact_cell, fontSize=8, textColor="#444444", leading=10
    )
    crit_table_data = [
        [Paragraph("<b>Поле</b>", compact_cell), Paragraph("<b>Значення</b>", compact_cell)]
    ]
    section_rows_idx: list[int] = []
    for label, val in critical_rows:
        if label.startswith("━━"):
            section_rows_idx.append(len(crit_table_data))
            crit_table_data.append([
                Paragraph(f"<b>{escape(label)}</b>", crit_title_style),
                Paragraph("", crit_title_style),
            ])
        else:
            crit_table_data.append([
                Paragraph(escape(label), compact_cell),
                Paragraph(escape(val), compact_cell),
            ])

    crit_table = Table(crit_table_data, colWidths=[5.2 * cm, 12.2 * cm])
    crit_style = [
        ("BACKGROUND", (0, 0), (-1, 0), "#e0e0e0"),
        ("GRID", (0, 0), (-1, -1), 0.5, "#ccc"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    for idx in section_rows_idx:
        crit_style.append(("BACKGROUND", (0, idx), (-1, idx), "#d0dce8"))
        crit_style.append(("SPAN", (0, idx), (-1, idx)))
    crit_table.setStyle(TableStyle(crit_style))

    story.append(Paragraph("КРИТИЧНІ ПОЛЯ — СТР. 1", compact_heading))
    story.append(crit_table)
    story.append(Spacer(1, 0.2 * cm))

    # ─────────────────────────────────────────────────────
    # СТОРІНКА 2+ — ПОВНИЙ ДЕТАЛІЗОВАНИЙ ЗВІТ
    # ─────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("MEDEVAK — Деталізований звіт", compact_title))
    story.append(Spacer(1, 0.2 * cm))

    _append_key_value_table(
        story,
        "Загальна інформація",
        [
            ("ID кейсу", str(case.get("id", "—"))),
            ("Тріаж", str(case.get("triage_code", "—"))),
            ("Механізм", str(case.get("mechanism_of_injury") or case.get("mechanism") or "—")),
            ("Примітки", str(case.get("notes", "—"))),
        ],
        [5.2 * cm, 12.2 * cm],
        compact_heading,
        compact_cell,
    )

    if form_100.get("id"):
        _append_key_value_table(
            story,
            "Форма 100 — основні поля",
            [
                ("Номер документа", str(form_100.get("document_number") or "—")),
                ("Дата/час травми", str(form_100.get("injury_datetime") or "—")),
                ("Локація травми", str(form_100.get("injury_location") or "—")),
                ("Механізм травми", str(form_100.get("injury_mechanism") or "—")),
                ("Діагноз", str(form_100.get("diagnosis_summary") or "—")),
                ("Хто документував", str(form_100.get("documented_by") or "—")),
            ],
            [5.2 * cm, 12.2 * cm],
            compact_heading,
            compact_cell,
        )

        section_map = [
            ("Stub", form_100.get("stub")),
            ("Front Side", form_100.get("front_side")),
            ("Back Side", form_100.get("back_side")),
            ("Meta Legal Rules", form_100.get("meta_legal_rules")),
        ]
        canonical_rows = [(name, "Включено") for name, payload in section_map if payload]
        if canonical_rows:
            story.append(Paragraph("Form 100 Canonical Sections", styles["Heading3"]))
            _append_key_value_table(
                story,
                "Індексація секцій",
                canonical_rows,
                [5.2 * cm, 12.2 * cm],
                compact_heading,
                compact_cell,
            )

        front_side = front_side_p1  # already resolved above
        _append_key_value_table(story, "Корінець (Stub)", _rows_from_payload(form_100.get("stub") or {}), [6.5 * cm, 10.9 * cm], compact_heading, compact_cell)
        _append_key_value_table(story, "Лицьова сторона — Ідентифікація", _rows_from_payload(front_side.get("identity") or {}), [6.5 * cm, 10.9 * cm], compact_heading, compact_cell)
        _append_key_value_table(story, "Лицьова сторона — Травма", _rows_from_payload(front_side.get("injury") or {}), [6.5 * cm, 10.9 * cm], compact_heading, compact_cell)
        _append_key_value_table(story, "Лицьова сторона — Лікування", _rows_from_payload(front_side.get("treatment") or {}), [6.5 * cm, 10.9 * cm], compact_heading, compact_cell)
        _append_key_value_table(story, "Лицьова сторона — Евакуація", _rows_from_payload(front_side.get("evacuation") or {}), [6.5 * cm, 10.9 * cm], compact_heading, compact_cell)
        _append_key_value_table(story, "Лицьова сторона — Сортувальні маркери", _rows_from_payload(front_side.get("triage_markers") or {}), [6.5 * cm, 10.9 * cm], compact_heading, compact_cell)
        _append_key_value_table(story, "Лицьова сторона — Схема тіла", _rows_from_payload(front_side.get("body_diagram") or {}), [6.5 * cm, 10.9 * cm], compact_heading, compact_cell)

        back_side = form_100.get("back_side") or {}
        _append_key_value_table(story, "Зворотня сторона — Журнал етапів", _rows_from_payload(back_side.get("stage_log") or []), [6.5 * cm, 10.9 * cm], compact_heading, compact_cell)
        _append_key_value_table(story, "Зворотня сторона — Підпис", _rows_from_payload(back_side.get("signature") or {}), [6.5 * cm, 10.9 * cm], compact_heading, compact_cell)
        _append_key_value_table(story, "Мета/Юридичні правила", _rows_from_payload(form_100.get("meta_legal_rules") or {}), [6.5 * cm, 10.9 * cm], compact_heading, compact_cell)

    march_notes = case.get("march_notes") or {}
    march_rows = [
        ("M", str(march_notes.get("m_notes") or "—")),
        ("A", str(march_notes.get("a_notes") or "—")),
        ("R", str(march_notes.get("r_notes") or "—")),
        ("C", str(march_notes.get("c_notes") or "—")),
        ("H", str(march_notes.get("h_notes") or "—")),
    ]
    if any(value != "—" for _, value in march_rows):
        # Keep legacy English token for existing PDF tests and downstream parsers.
        story.append(Paragraph("MARCH Notes", compact_heading))
        _append_key_value_table(story, "MARCH Нотатки", march_rows, [5.2 * cm, 12.2 * cm], compact_heading, compact_cell)

    obs = case.get("observations") or []
    if obs:
        _append_key_value_table(
            story,
            "Спостереження",
            [(str(o.get("observation_type", "—")), str(o.get("value", "—"))) for o in obs],
            [5.2 * cm, 12.2 * cm],
            compact_heading,
            compact_cell,
        )

    meds = case.get("medications") or []
    if meds:
        _append_key_value_table(
            story,
            "Медикаменти",
            [(str(m.get("medication_code", "—")), f"{m.get('dose_value', '—')} {m.get('dose_unit_code', '—')}") for m in meds],
            [5.2 * cm, 12.2 * cm],
            compact_heading,
            compact_cell,
        )

    procs = case.get("procedures") or []
    if procs:
        _append_key_value_table(
            story,
            "Процедури",
            [(str(p.get("procedure_code", "—")), str(p.get("notes", "—"))) for p in procs],
            [5.2 * cm, 12.2 * cm],
            compact_heading,
            compact_cell,
        )

    doc.build(story)
    return buffer.getvalue()
