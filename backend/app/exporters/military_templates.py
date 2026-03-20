"""
Військові шаблони документів - стандартизовані форми для ЗС
MEDEVAK Military Document Templates
"""
from io import BytesIO
from typing import Any, Dict, List, Optional
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.colors import black, white, grey, lightgrey, red


def generate_casualty_report(case_data: Dict[str, Any], member_data: Dict[str, Any] = None) -> bytes:
    """Звіт про бойову травму (Casualty Report) - DD Form 1380."""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=1.5*cm, leftMargin=1.5*cm,
                          topMargin=1.5*cm, bottomMargin=1.5*cm)
    
    styles = getSampleStyleSheet()
    
    # Кастомні стилі
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=black
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=15,
        alignment=TA_CENTER,
        textColor=red
    )
    
    story = []
    
    # Заголовок
    story.append(Paragraph("ЗВІТ ПРО БОЙОВУ ТРАВМУ", title_style))
    story.append(Paragraph("DD FORM 1380", header_style))
    story.append(Spacer(1, 0.3*cm))
    
    # Інформація про пацієнта
    patient_data = [
        ["ПІБ:", f"{case_data.get('full_name', '—')}"],
        ["Військовий номер:", member_data.get('service_number', '—') if member_data else "—"],
        ["Звання:", member_data.get('rank', '—') if member_data else "—"],
        ["Підрозділ:", member_data.get('unit', '—') if member_data else "—"],
        ["Група крові:", member_data.get('blood_type', '—') if member_data else case_data.get('blood_type', '—')],
        ["Алергії:", member_data.get('allergies', '—') if member_data else "—"],
    ]
    
    table = Table(patient_data, colWidths=[3*cm, 7*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))
    
    # Інформація про травму
    injury_data = [
        ["Дата/час травми:", _format_datetime(case_data.get('incident_time'))],
        ["Локація травми:", case_data.get('incident_location', '—')],
        ["Механізм травми:", case_data.get('mechanism_of_injury', '—')],
        ["Тріаж:", case_data.get('triage_code', '—')],
        ["Статус евакуації:", case_data.get('evac_status', '—')],
    ]
    
    table = Table(injury_data, colWidths=[3*cm, 7*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))
    
    # MIST дані
    story.append(Paragraph("MIST - MECHANISM, INJURIES, SIGNS, TREATMENT", styles['Heading2']))
    
    # Mechanism
    mechanism = case_data.get('mechanism_of_injury', '—')
    story.append(Paragraph(f"<b>Mechanism:</b> {mechanism}", styles['Normal']))
    story.append(Spacer(1, 0.2*cm))
    
    # Injuries
    injuries = case_data.get('injuries_json', [])
    if injuries:
        story.append(Paragraph("<b>Injuries:</b>", styles['Normal']))
        for injury in injuries:
            story.append(Paragraph(f"• {injury}", styles['Normal']))
        story.append(Spacer(1, 0.2*cm))
    
    # Signs
    vitals = case_data.get('vitals_json', [])
    if vitals:
        story.append(Paragraph("<b>Vital Signs:</b>", styles['Normal']))
        for vital in vitals[-3:]:  # Останні 3 показники
            story.append(Paragraph(f"• {vital}", styles['Normal']))
        story.append(Spacer(1, 0.2*cm))
    
    # Treatment
    treatments = case_data.get('treatments_json', [])
    if treatments:
        story.append(Paragraph("<b>Treatment Provided:</b>", styles['Normal']))
        for treatment in treatments:
            story.append(Paragraph(f"• {treatment}", styles['Normal']))
        story.append(Spacer(1, 0.2*cm))
    
    # Підписи
    story.append(Spacer(1, 2*cm))
    
    signature_data = [
        ["Медик, що надав допомогу:", "____________________"],
        ["Дата/час:", _format_datetime(datetime.utcnow())],
        ["Підпис:", "____________________"],
        ["", ""],
        ["Свідчення (якщо є):", "____________________"],
        ["Підпис:", "____________________"],
    ]
    
    table = Table(signature_data, colWidths=[5*cm, 5*cm])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    story.append(table)
    
    doc.build(story)
    return buffer.getvalue()


def generate_medical_evacuation_form(case_data: Dict[str, Any], member_data: Dict[str, Any] = None) -> bytes:
    """Медична форма евакуації (Medical Evacuation Form)."""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=1.5*cm, leftMargin=1.5*cm,
                          topMargin=1.5*cm, bottomMargin=1.5*cm)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=black
    )
    
    story = []
    
    # Заголовок
    story.append(Paragraph("МЕДИЧНА ФОРМА ЄВАКУАЦІЇ", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Секція 1: Інформація про пацієнта
    story.append(Paragraph("1. ІНФОРМАЦІЯ ПРО ПАЦІЄНТА", styles['Heading2']))
    
    patient_info = [
        ["Прізвище:", case_data.get('last_name', '—')],
        ["Ім'я:", case_data.get('first_name', '—')],
        ["По батькові:", case_data.get('middle_name', '—')],
        ["Військовий номер:", member_data.get('service_number', '—') if member_data else "—"],
        ["Звання:", member_data.get('rank', '—') if member_data else "—"],
        ["Підрозділ:", member_data.get('unit', '—') if member_data else "—"],
        ["Вік:", _calculate_age(member_data.get('date_of_birth')) if member_data else "—"],
        ["Стать:", "—"],
        ["Група крові:", member_data.get('blood_type', '—') if member_data else case_data.get('blood_type', '—')],
        ["Алергії:", member_data.get('allergies', '—') if member_data else "—"],
    ]
    
    table = Table(patient_info, colWidths=[2.5*cm, 7.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))
    
    # Секція 2: Інформація про травму
    story.append(Paragraph("2. ІНФОРМАЦІЯ ПРО ТРАВМУ", styles['Heading2']))
    
    injury_info = [
        ["Дата/час травми:", _format_datetime(case_data.get('incident_time'))],
        ["Місце травми:", case_data.get('incident_location', '—')],
        ["Механізм травми:", case_data.get('mechanism_of_injury', '—')],
        ["Тип травми:", "—"],
        ["Анатомічна локалізація:", "—"],
        ["Тріаж:", case_data.get('triage_code', '—')],
        ["Стабільний:", "Так" if case_data.get('triage_code') in ['200', '300', '400'] else "Ні"],
    ]
    
    table = Table(injury_info, colWidths=[3*cm, 7*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))
    
    # Секція 3: Вітальні показники
    story.append(Paragraph("3. ВІТАЛЬНІ ПОКАЗНИКИ", styles['Heading2']))
    
    vitals = case_data.get('vitals_json', [])
    if vitals and len(vitals) > 0:
        latest_vital = vitals[-1]
        vital_info = [
            ["Частота серцевих скорочень:", latest_vital.get('pulse', '—')],
            ["Тиск (систолічний/діастолічний):", "—"],
            ["Частота дихання:", "—"],
            ["Сатурація киснем:", latest_vital.get('spo2', '—')],
            ["Температура:", "—"],
            ["Шкала коми:", "—"],
            ["Біль (0-10):", "—"],
        ]
    else:
        vital_info = [["Показники відсутні", ""]]
    
    table = Table(vital_info, colWidths=[4*cm, 6*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))
    
    # Секція 4: Надана медична допомога
    story.append(Paragraph("4. НАДАНА МЕДИЧНА ДОПОМОГА", styles['Heading2']))
    
    treatments = case_data.get('treatments_json', [])
    if treatments:
        treatment_info = [[str(i+1), treatment] for i, treatment in enumerate(treatments)]
        treatment_info.insert(0, ["#", "Опис"])
        
        table = Table(treatment_info, colWidths=[1*cm, 9*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('TEXTCOLOR', (0, 1), (-1, -1), black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("Допомога не надавалась", styles['Normal']))
    
    story.append(Spacer(1, 1*cm))
    
    # Секція 5: Рекомендації
    story.append(Paragraph("5. РЕКОМЕНДАЦІЇ", styles['Heading2']))
    story.append(Paragraph("_________________________________________________________", styles['Normal']))
    story.append(Spacer(1, 2*cm))
    
    # Підписи
    signature_info = [
        ["Медик, що заповнив форму:", "____________________"],
        ["Підпис:", "____________________"],
        ["Дата:", _format_datetime(datetime.utcnow())],
        ["", ""],
        ["Лікар, що прийняв пацієнта:", "____________________"],
        ["Підпис:", "____________________"],
        ["Дата:", "____________________"],
    ]
    
    table = Table(signature_info, colWidths=[5*cm, 5*cm])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    story.append(table)
    
    doc.build(story)
    return buffer.getvalue()


def generate_treatment_summary(case_data: Dict[str, Any], member_data: Dict[str, Any] = None) -> bytes:
    """Звіт про лікування (Treatment Summary)."""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=2*cm, leftMargin=2*cm,
                          topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=black
    )
    
    story = []
    
    # Заголовок
    story.append(Paragraph("ЗВІТ ПРО ЛІКУВАННЯ", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Пацієнт
    patient_name = f"{member_data.get('rank', '')} {member_data.get('last_name', '')} {member_data.get('first_name', '')}".strip() if member_data else case_data.get('full_name', '—')
    story.append(Paragraph(f"<b>Пацієнт:</b> {patient_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Військовий номер:</b> {member_data.get('service_number', '—') if member_data else '—'}", styles['Normal']))
    story.append(Paragraph(f"<b>Підрозділ:</b> {member_data.get('unit', '—') if member_data else '—'}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Інформація про травму
    story.append(Paragraph("<b>ІНФОРМАЦІЯ ПРО ТРАВМУ</b>", styles['Heading2']))
    story.append(Paragraph(f"<b>Дата травми:</b> {_format_datetime(case_data.get('incident_time'))}", styles['Normal']))
    story.append(Paragraph(f"<b>Механізм:</b> {case_data.get('mechanism_of_injury', '—')}", styles['Normal']))
    story.append(Paragraph(f"<b>Локація:</b> {case_data.get('incident_location', '—')}", styles['Normal']))
    story.append(Paragraph(f"<b>Початковий тріаж:</b> {case_data.get('triage_code', '—')}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Лікування
    story.append(Paragraph("<b>НАДАНЕ ЛІКУВАННЯ</b>", styles['Heading2']))
    
    treatments = case_data.get('treatments_json', [])
    if treatments:
        for i, treatment in enumerate(treatments, 1):
            story.append(Paragraph(f"{i}. {treatment}", styles['Normal']))
    else:
        story.append(Paragraph("Лікування не задокументовано", styles['Normal']))
    
    story.append(Spacer(1, 0.5*cm))
    
    # Результати
    story.append(Paragraph("<b>РЕЗУЛЬТАТИ ЛІКУВАННЯ</b>", styles['Heading2']))
    story.append(Paragraph(f"<b>Статус:</b> {case_data.get('evac_status', '—')}", styles['Normal']))
    story.append(Paragraph(f"<b>Рекомендации:</b>", styles['Normal']))
    story.append(Paragraph("_________________________________________________________", styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
    # Підпис
    story.append(Paragraph("<b>Лікар, що провів лікування:</b> ____________________", styles['Normal']))
    story.append(Paragraph("<b>Підпис:</b> ____________________", styles['Normal']))
    story.append(Paragraph(f"<b>Дата:</b> {_format_datetime(datetime.utcnow())}", styles['Normal']))
    
    doc.build(story)
    return buffer.getvalue()


def _format_datetime(dt_obj: Any) -> str:
    """Форматування дати та часу."""
    if not dt_obj:
        return "—"
    
    if isinstance(dt_obj, str):
        try:
            dt_obj = datetime.fromisoformat(dt_obj.replace('Z', '+00:00'))
        except:
            return str(dt_obj)
    
    if isinstance(dt_obj, datetime):
        return dt_obj.strftime('%d.%m.%Y %H:%M')
    
    return str(dt_obj)


def _calculate_age(birth_date: Any) -> str:
    """Розрахунок віку."""
    if not birth_date:
        return "—"
    
    try:
        if isinstance(birth_date, str):
            birth_date = datetime.fromisoformat(birth_date.replace('Z', '+00:00'))
        
        if isinstance(birth_date, datetime):
            today = datetime.utcnow()
            age = today.year - birth_date.year
            
            # Коригуємо якщо день народження ще не був цього року
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1
            
            return f"{age} років"
    except:
        pass
    
    return "—"
