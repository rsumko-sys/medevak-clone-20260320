"""
Personnel Records Exporter - експорт військових особових справ
Підтримує PDF, FHIR, JSON формати
"""
from io import BytesIO
from typing import Any, Dict, List, Optional
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.colors import black, white, grey, lightgrey

from app.models.personnel import ServiceMember, PersonnelRecord, MedicalRecord, DeploymentRecord


def export_service_record_pdf(member: Dict[str, Any], 
                             records: List[Dict[str, Any]] = None,
                             medical_records: List[Dict[str, Any]] = None,
                             deployments: List[Dict[str, Any]] = None) -> bytes:
    """Експорт військової особової справи в PDF формат."""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=2*cm, leftMargin=2*cm,
                          topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    
    # Кастомні стилі
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=black
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=12,
        spaceBefore=20,
        textColor=black
    )
    
    story = []
    
    # Заголовок
    story.append(Paragraph("ОСОБОВА СПРАВА ВІЙСЬКОВОСЛУЖБОВЦЯ", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Основна інформація
    story.append(Paragraph("ОСНОВНА ІНФОРМАЦІЯ", heading_style))
    
    personal_data = [
        ["Військовий номер:", member.get('service_number', '—')],
        ["ПІБ:", f"{member.get('last_name', '')} {member.get('first_name', '')} {member.get('middle_name', '')}".strip() or '—'],
        ["Дата народження:", _format_date(member.get('date_of_birth'))],
        ["Місце народження:", member.get('place_of_birth', '—')],
        ["Громадянство:", member.get('citizenship', '—')],
    ]
    
    military_data = [
        ["Звання:", member.get('rank', '—')],
        ["Спеціальність:", member.get('specialty', '—')],
        ["Підрозділ:", member.get('unit', '—')],
        ["Посада:", member.get('position', '—')],
        ["Вислуга років:", str(member.get('years_of_service', '—'))],
    ]
    
    service_data = [
        ["Дата призову/контракту:", _format_date(member.get('enlistment_date'))],
        ["Початок служби:", _format_date(member.get('service_start_date'))],
        ["Кінець контракту:", _format_date(member.get('contract_end_date'))],
        ["Статус:", member.get('status', '—')],
        ["На розгортанні:", "Так" if member.get('is_deployed') else "Ні"],
    ]
    
    # Таблиці з даними
    for table_data in [personal_data, military_data, service_data]:
        table = Table(table_data, colWidths=[4*cm, 10*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # Медична інформація
    story.append(Paragraph("МЕДИЧНА ІНФОРМАЦІЯ", heading_style))
    
    medical_data = [
        ["Група крові:", member.get('blood_type', '—')],
        ["Алергії:", member.get('allergies', '—')],
        ["Хронічні захворювання:", member.get('medical_conditions', '—')],
        ["Постійні ліки:", member.get('medications', '—')],
        ["Останній медогляд:", _format_date(member.get('last_physical_date'))],
    ]
    
    table = Table(medical_data, colWidths=[3*cm, 11*cm])
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
    
    # Медичні записи
    if medical_records:
        story.append(Paragraph("МЕДИЧНІ ЗАПИСИ", heading_style))
        
        med_headers = ["Дата", "Тип", "Діагноз", "Лікування", "Результат"]
        med_data = [med_headers]
        
        for record in medical_records:
            med_data.append([
                _format_date(record.get('encounter_date')),
                record.get('record_type', '—'),
                record.get('diagnosis', '—'),
                record.get('treatment', '—')[:50] + '...' if len(record.get('treatment', '')) > 50 else record.get('treatment', '—'),
                record.get('outcome', '—')
            ])
        
        table = Table(med_data, colWidths=[2.5*cm, 2.5*cm, 3*cm, 4*cm, 2*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('TEXTCOLOR', (0, 1), (-1, -1), black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.5*cm))
    
    story.append(PageBreak())
    
    # Розгортання
    if deployments:
        story.append(Paragraph("РОЗГОРТАННЯ/ДЕПЛОЙМЕНТИ", heading_style))
        
        deploy_headers = ["Операція", "Локація", "Початок", "Кінець", "Тривалість", "Роль"]
        deploy_data = [deploy_headers]
        
        for deployment in deployments:
            duration = deployment.get('duration_days', '—')
            if isinstance(duration, (int, float)):
                duration = f"{int(duration)} днів"
            
            deploy_data.append([
                deployment.get('operation_name', '—'),
                deployment.get('location', '—'),
                _format_date(deployment.get('start_date')),
                _format_date(deployment.get('end_date')),
                duration,
                deployment.get('role', '—')
            ])
        
        table = Table(deploy_data, colWidths=[3*cm, 2.5*cm, 2*cm, 2*cm, 2*cm, 2*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('TEXTCOLOR', (0, 1), (-1, -1), black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.5*cm))
    
    # Записи в особовій справі
    if records:
        story.append(Paragraph("ЗАПИСИ В ОСОБОВІЙ СПРАВІ", heading_style))
        
        record_headers = ["Дата", "Тип", "Опис", "Статус"]
        record_data = [record_headers]
        
        for record in records:
            record_data.append([
                _format_date(record.get('effective_date')),
                record.get('record_type', '—'),
                record.get('description', '—')[:40] + '...' if len(record.get('description', '')) > 40 else record.get('description', '—'),
                record.get('status', '—')
            ])
        
        table = Table(record_data, colWidths=[2.5*cm, 2.5*cm, 5*cm, 2*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('TEXTCOLOR', (0, 1), (-1, -1), black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(table)
    
    # Нотатки
    story.append(PageBreak())
    story.append(Paragraph("НОТАТКИ", heading_style))
    story.append(Paragraph(
        f"Звіт згенеровано: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"ID військовослужбовця: {member.get('id', '—')}\n"
        f"Система: MEDEVAK Combat Casualty Record Module",
        styles["Normal"]
    ))
    
    doc.build(story)
    return buffer.getvalue()


def export_personnel_summary(member: Dict[str, Any]) -> Dict[str, Any]:
    """Експорт короткої довідки про військовослужбовця."""
    
    return {
        "service_member": {
            "id": member.get('id'),
            "service_number": member.get('service_number'),
            "name": f"{member.get('rank', '')} {member.get('last_name', '')} {member.get('first_name', '')} {member.get('middle_name', '')}".strip(),
            "unit": member.get('unit'),
            "specialty": member.get('specialty'),
            "status": member.get('status'),
            "is_deployed": member.get('is_deployed'),
            "years_of_service": member.get('years_of_service'),
            "blood_type": member.get('blood_type'),
            "combat_experience": member.get('combat_experience'),
        },
        "contact": {
            "phone": member.get('phone'),
            "email": member.get('email'),
            "address": member.get('address'),
        },
        "medical": {
            "blood_type": member.get('blood_type'),
            "allergies": member.get('allergies'),
            "medical_conditions": member.get('medical_conditions'),
            "last_physical": member.get('last_physical_date'),
        },
        "service": {
            "enlistment_date": member.get('enlistment_date'),
            "contract_end_date": member.get('contract_end_date'),
            "rank": member.get('rank'),
            "position": member.get('position'),
        },
        "generated_at": datetime.utcnow().isoformat()
    }


def export_medical_summary(medical_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Експорт медичної довідки."""
    
    if not medical_records:
        return {"error": "No medical records found"}
    
    # Групування за типом записів
    injuries = [r for r in medical_records if r.get('record_type') == 'INJURY']
    treatments = [r for r in medical_records if r.get('record_type') == 'TREATMENT']
    examinations = [r for r in medical_records if r.get('record_type') == 'EXAMINATION']
    
    # Останні записи
    latest_injury = max(injuries, key=lambda x: x.get('encounter_date'), default=None)
    latest_treatment = max(treatments, key=lambda x: x.get('encounter_date'), default=None)
    
    return {
        "summary": {
            "total_records": len(medical_records),
            "injuries": len(injuries),
            "treatments": len(treatments),
            "examinations": len(examinations),
        },
        "latest_injury": {
            "date": latest_injury.get('encounter_date') if latest_injury else None,
            "diagnosis": latest_injury.get('diagnosis') if latest_injury else None,
            "severity": latest_injury.get('injury_severity') if latest_injury else None,
            "outcome": latest_injury.get('outcome') if latest_injury else None,
        },
        "latest_treatment": {
            "date": latest_treatment.get('encounter_date') if latest_treatment else None,
            "treatment": latest_treatment.get('treatment') if latest_treatment else None,
            "outcome": latest_treatment.get('outcome') if latest_treatment else None,
        },
        "generated_at": datetime.utcnow().isoformat()
    }


def export_deployment_summary(deployments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Експорт довідки про розгортання."""
    
    if not deployments:
        return {"error": "No deployment records found"}
    
    # Розрахунок загальних показників
    total_days = sum(d.get('duration_days', 0) for d in deployments if isinstance(d.get('duration_days'), (int, float)))
    combat_deployments = [d for d in deployments if d.get('mission_type') == 'COMBAT']
    
    return {
        "summary": {
            "total_deployments": len(deployments),
            "combat_deployments": len(combat_deployments),
            "total_days_deployed": int(total_days),
            "currently_deployed": any(d.get('status') == 'ACTIVE' for d in deployments),
        },
        "deployments": [
            {
                "operation": d.get('operation_name'),
                "location": d.get('location'),
                "start_date": d.get('start_date'),
                "end_date": d.get('end_date'),
                "duration_days": d.get('duration_days'),
                "mission_type": d.get('mission_type'),
                "role": d.get('role'),
                "status": d.get('status'),
            }
            for d in deployments
        ],
        "generated_at": datetime.utcnow().isoformat()
    }


def _format_date(date_obj: Any) -> str:
    """Форматування дати."""
    if not date_obj:
        return "—"
    
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
        except:
            return str(date_obj)
    
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%d.%m.%Y')
    
    return str(date_obj)


def export_personnel_fhir(member: Dict[str, Any]) -> Dict[str, Any]:
    """Експорт військовослужбовця в FHIR Patient ресурс."""
    
    return {
        "resourceType": "Patient",
        "id": member.get('id'),
        "identifier": [
            {
                "type": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "SB",
                        "display": "Social Beneficiary Identifier"
                    }]
                },
                "value": member.get('service_number')
            }
        ],
        "name": [{
            "use": "official",
            "family": member.get('last_name'),
            "given": [member.get('first_name'), member.get('middle_name')] if member.get('middle_name') else [member.get('first_name')]
        }],
        "birthDate": member.get('date_of_birth'),
        "extension": [
            {
                "url": "http://example.org/fhir/StructureDefinition/military-service",
                "extension": [
                    {"url": "rank", "valueString": member.get('rank')},
                    {"url": "specialty", "valueString": member.get('specialty')},
                    {"url": "unit", "valueString": member.get('unit')},
                    {"url": "serviceNumber", "valueString": member.get('service_number')},
                    {"url": "yearsOfService", "valueDecimal": member.get('years_of_service')},
                    {"url": "combatExperience", "valueBoolean": member.get('combat_experience')},
                    {"url": "bloodType", "valueString": member.get('blood_type')}
                ]
            }
        ]
    }
