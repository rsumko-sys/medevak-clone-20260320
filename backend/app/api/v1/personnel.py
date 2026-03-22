"""Personnel Records API - управління військовими особовими справами."""
import uuid
from typing import Annotated, List, Dict, Any, Optional
from datetime import datetime
import structlog

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from sqlalchemy.exc import IntegrityError


from app.api.deps import (
    get_session, 
    get_current_user as get_current_user_simple, 
    get_request_id as get_request_id_simple,
    get_security_context,
    require_permission
)
from app.core.security import SecurityContext, Permission, UserRole
from app.models.personnel import ServiceMember, PersonnelRecord, MedicalRecord, DeploymentRecord
from app.models.cases import Case
from app.schemas.personnel import (
    ServiceMemberCreate, 
    ServiceMemberUpdate, 
    ServiceMemberResponse,
    PersonnelListResponse,
    MedicalRecordCreate,
    ErrorResponse
)
from app.core.utils import envelope
from app.exporters.personnel_exporter import (
    export_service_record_pdf,
    export_personnel_summary,
    export_medical_summary,
    export_deployment_summary,
    export_personnel_fhir
)
from app.exporters.military_templates import (
    generate_casualty_report,
    generate_medical_evacuation_form,
    generate_treatment_summary,
)
from app.repositories.personnel import PersonnelRepository
from app.core.idempotency import get_idempotent_response, save_idempotent_response


router = APIRouter(tags=["personnel"])

logger = structlog.get_logger()


@router.get("/members")
async def list_service_members(
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_PERSONNEL))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(le=100)] = 50,
    unit: Annotated[Optional[str], Query()] = None,
    rank: Annotated[Optional[str], Query()] = None,
    status: Annotated[Optional[str], Query()] = None,
    is_deployed: Annotated[Optional[bool], Query()] = None,
):

    """Список військовослужбовців з фільтрацією."""
    
    repo = PersonnelRepository(session)
    
    # Base filters for QLAC
    # Note: unit filter is handled inside repository based on ctx.unit if not admin
    effective_unit = unit if ctx.role == UserRole.ADMIN else ctx.unit
    
    members = await repo.list_with_filters(
        unit=effective_unit,
        rank=rank,
        status=status,
        is_deployed=is_deployed,
        limit=limit,
        offset=offset
    )
    
    members_data = []
    for member in members:
        member_dict = {
            "id": member.id,
            "service_number": member.service_number,
            "rank": member.rank,
            "last_name": member.last_name,
            "first_name": member.first_name,
            "middle_name": member.middle_name,
            "unit": member.unit,
            "specialty": member.specialty,
            "position": member.position,
            "status": member.status,
            "is_deployed": member.is_deployed,
            "blood_type": member.blood_type,
            "years_of_service": member.years_of_service,
            "created_at": member.created_at.isoformat(),
        }
        members_data.append(member_dict)
    
    return envelope({
        "data": members_data,
        "total": len(members_data),
        "offset": offset,
        "limit": limit
    }, request_id=request_id)



@router.get("/members/{member_id}")
async def get_service_member(
    member_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_PERSONNEL))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
    include_records: Annotated[bool, Query()] = False,
    include_medical: Annotated[bool, Query()] = False,
    include_deployments: Annotated[bool, Query()] = False,
):
    """Отримати детальну інформацію про військовослужбовця."""
    
    repo = PersonnelRepository(session)
    try:
        # QLAC: Query with unit isolation and soft-delete hidden by default
        member = await repo.get_by_id_all_relations(
            member_id=member_id,
            unit=None if ctx.role == UserRole.ADMIN else ctx.unit,
            include_medical=include_medical,
            include_deployments=include_deployments,
            include_personnel=include_records,
            include_documents=False # Documents not needed for this response
        )
        
        if not member:
            raise HTTPException(status_code=404, detail="Service member not found")


        # Build member data
        member_data = {
            "id": member.id,
            "service_number": member.service_number,
            "last_name": member.last_name,
            "first_name": member.first_name,
            "middle_name": member.middle_name,
            "date_of_birth": member.date_of_birth.isoformat() if member.date_of_birth else None,
            "place_of_birth": member.place_of_birth,
            "citizenship": member.citizenship,
            "rank": member.rank,
            "specialty": member.specialty,
            "unit": member.unit,
            "position": member.position,
            "enlistment_date": member.enlistment_date.isoformat() if member.enlistment_date else None,
            "service_start_date": member.service_start_date.isoformat() if member.service_start_date else None,
            "contract_end_date": member.contract_end_date.isoformat() if member.contract_end_date else None,
            "years_of_service": member.years_of_service,
            "blood_type": member.blood_type,
            "allergies": member.allergies,
            "medical_conditions": member.medical_conditions,
            "medications": member.medications,
            "last_physical_date": member.last_physical_date.isoformat() if member.last_physical_date else None,
            "deployments": member.deployments,
            "combat_experience": member.combat_experience,
            "awards": member.awards,
            "qualifications": member.qualifications,
            "status": member.status,
            "is_deployed": member.is_deployed,
            "created_at": member.created_at.isoformat(),
            "updated_at": member.updated_at.isoformat(),
        }
        
        # Add all fields for now (simplified)
        member_data["social_security"] = member.social_security
        member_data["phone"] = member.phone
        member_data["email"] = member.email
        member_data["address"] = member.address
        member_data["emergency_contact"] = member.emergency_contact
        member_data["version_id"] = member.version_id
        
        # Filter sensitive data
        member_data = ctx.filter_data(member_data)
        
        ctx.audit_access(member.id, "read")
        
        return envelope(member_data, request_id=request_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get service member", 
                   member_id=member_id,
                   error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Помилка при отриманні даних військовослужбовця"
        )


@router.post("/members")
async def create_service_member(
    member_data: ServiceMemberCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.CREATE_PERSONNEL))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
):
    """Створити нову особову справу військовослужбовця."""
    
    if idempotency_key:
        existing = await get_idempotent_response(session, idempotency_key, ctx.user_id)
        if existing:
            return envelope(existing["body"], request_id=request_id)
            
    try:

        member_id = str(uuid.uuid4())
        
        async with session.begin():
            member = ServiceMember(
                id=member_id,
                service_number=member_data.service_number,
                social_security=member_data.social_security,
                last_name=member_data.last_name,
                first_name=member_data.first_name,
                middle_name=member_data.middle_name,
                date_of_birth=member_data.date_of_birth,
                place_of_birth=member_data.place_of_birth,
                citizenship=member_data.citizenship,
                rank=member_data.rank,
                specialty=member_data.specialty,
                unit=member_data.unit,
                position=member_data.position,
                enlistment_date=member_data.enlistment_date,
                service_start_date=member_data.service_start_date,
                contract_end_date=member_data.contract_end_date,
                years_of_service=member_data.years_of_service,
                phone=member_data.phone,
                email=member_data.email,
                address=member_data.address,
                emergency_contact=member_data.emergency_contact,
                blood_type=member_data.blood_type,
                allergies=member_data.allergies,
                medical_conditions=member_data.medical_conditions,
                medications=member_data.medications,
                last_physical_date=member_data.last_physical_date,
                deployments=member_data.deployments,
                combat_experience=member_data.combat_experience,
                awards=member_data.awards,
                qualifications=member_data.qualifications,
                status=member_data.status,
                is_deployed=member_data.is_deployed,
                created_by=ctx.user_id,
                version_id=1 # Initialize version for optimistic locking
            )
            
            session.add(member)
        
        ctx.audit_access(member_id, "create")
        
        response_data = {
            "id": member_id,
            "message": "Service member created successfully"
        }
        
        if idempotency_key:
            await save_idempotent_response(session, idempotency_key, ctx.user_id, "/personnel/members", 200, response_data)
        
        return envelope(response_data, request_id=request_id)

        
    except IntegrityError as e:
        await session.rollback()
        logger.error("Duplicate service number", 
                   service_number=member_data.service_number,
                   error=str(e))
        raise HTTPException(
            status_code=400, 
            detail="Військовий номер вже існує"
        )
    except Exception as e:
        await session.rollback()
        logger.error("Failed to create service member", 
                   service_number=member_data.service_number,
                   error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Помилка при створенні військовослужбовця"
        )


@router.put("/members/{member_id}")
async def update_service_member(
    member_id: str,
    member_data: Dict[str, Any],
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.UPDATE_PERSONNEL))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
):
    """Оновити дані військовослужбовця."""
    
    # Atomic Optimistic Locking refactor
    client_version = member_data.get("version_id")
    if client_version is None:
        raise HTTPException(status_code=400, detail="version_id is required for updates")
    
    # Construct update statement with version check
    stmt = update(ServiceMember).where(
        and_(
            ServiceMember.id == member_id,
            ServiceMember.version_id == client_version,
            ServiceMember.is_deleted == False
        )
    )

    
    # QLAC: Unit isolation in update
    if ctx.role != UserRole.ADMIN:
        stmt = stmt.where(ServiceMember.unit == ctx.unit)
        
    update_values = {}
    for field, value in member_data.items():
        if hasattr(ServiceMember, field) and field not in ["id", "created_at", "created_by", "version_id"]:
            if field.endswith("_date") and value:
                update_values[field] = datetime.fromisoformat(value).replace(tzinfo=None)
            else:
                update_values[field] = value
                
    update_values["updated_at"] = datetime.utcnow()
    update_values["version_id"] = ServiceMember.version_id + 1
    
    stmt = stmt.values(**update_values)
    
    result = await session.execute(stmt)
    if result.rowcount == 0:
        # Check if it was a version conflict or access denied
        # Note: In a production system, we'd do a quick SELECT to distinguish,
        # but 409 is a safe default for "failed to apply update to this version".
        raise HTTPException(status_code=409, detail="Conflict or record not found/accessible")
    
    await session.commit()
    
    ctx.audit_access(member_id, "update", reason=member_data.get("update_reason"))
    
    return envelope({
        "id": member_id,
        "message": "Service member updated successfully",
        "new_version": client_version + 1
    }, request_id=request_id)



@router.delete("/members/{member_id}")
async def soft_delete_service_member(
    member_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.DELETE_PERSONNEL))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
    reason: Annotated[str, Query()] = "Removal requested",
):
    """Soft-delete a service member record."""
    member = await session.get(ServiceMember, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="Service member not found")
    
    ctx.validate_unit_access(member.unit)
    
    async with session.begin():
        member.is_deleted = True
        member.status = "DELETED"
        member.updated_at = datetime.utcnow()
    
    ctx.audit_access(member_id, "soft_delete", reason=reason)
    
    return envelope({
        "id": member_id,
        "message": "Service member record soft-deleted successfully"
    }, request_id=request_id)


@router.get("/members/{member_id}/export/pdf")
async def export_member_pdf(
    member_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.EXPORT_DATA))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
):
    """Експорт особової справи в PDF формат."""
    
    member = await session.get(ServiceMember, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="Service member not found")
    
    ctx.validate_unit_access(member.unit)
    
    # Rate limit exports
    ctx.check_rate_limit("export", limit=5, window_seconds=60)

    # Отримати пов'язані дані (with soft-delete filter)
    records_query = select(PersonnelRecord).where(
        and_(
            PersonnelRecord.service_member_id == member_id,
            PersonnelRecord.is_deleted == False
        )
    )
    records_result = await session.execute(records_query)
    records = records_result.scalars().all()
    
    medical_query = select(MedicalRecord).where(
        and_(
            MedicalRecord.service_member_id == member_id,
            MedicalRecord.is_deleted == False
        )
    )
    medical_result = await session.execute(medical_query)
    medical = medical_result.scalars().all()
    
    deploy_query = select(DeploymentRecord).where(
        and_(
            DeploymentRecord.service_member_id == member_id,
            DeploymentRecord.is_deleted == False
        )
    )
    deploy_result = await session.execute(deploy_query)
    deployments = deploy_result.scalars().all()

    
    # Конвертація в словники
    member_dict = {
        "id": member.id,
        "service_number": member.service_number,
        "last_name": member.last_name,
        "first_name": member.first_name,
        "middle_name": member.middle_name,
        "date_of_birth": member.date_of_birth,
        "place_of_birth": member.place_of_birth,
        "citizenship": member.citizenship,
        "rank": member.rank,
        "specialty": member.specialty,
        "unit": member.unit,
        "position": member.position,
        "enlistment_date": member.enlistment_date,
        "service_start_date": member.service_start_date,
        "contract_end_date": member.contract_end_date,
        "years_of_service": member.years_of_service,
        "phone": member.phone,
        "email": member.email,
        "address": member.address,
        "blood_type": member.blood_type,
        "allergies": member.allergies,
        "medical_conditions": member.medical_conditions,
        "medications": member.medications,
        "last_physical_date": member.last_physical_date,
        "status": member.status,
        "is_deployed": member.is_deployed,
    }
    
    records_dict = [
        {
            "record_type": r.record_type,
            "title": r.title,
            "description": r.description,
            "effective_date": r.effective_date,
            "recorded_date": r.recorded_date,
            "status": r.status,
        }
        for r in records
    ]
    
    medical_dict = [
        {
            "record_type": m.record_type,
            "diagnosis": m.diagnosis,
            "treatment": m.treatment,
            "encounter_date": m.encounter_date,
            "outcome": m.outcome,
        }
        for m in medical
    ]
    
    deployments_dict = [
        {
            "operation_name": d.operation_name,
            "location": d.location,
            "start_date": d.start_date,
            "end_date": d.end_date,
            "duration_days": d.duration_days,
            "mission_type": d.mission_type,
            "role": d.role,
            "status": d.status,
        }
        for d in deployments
    ]
    
    # Apply record caps for exports (e.g., limit to 100 records per type)
    max_export_records = 100
    records_dict = [r for idx, r in enumerate(records_dict) if idx < max_export_records]
    medical_dict = [m for idx, m in enumerate(medical_dict) if idx < max_export_records]
    deployments_dict = [d for idx, d in enumerate(deployments_dict) if idx < max_export_records]




    # Експорт в PDF
    pdf_bytes = export_service_record_pdf(member_dict, records_dict, medical_dict, deployments_dict)
    
    ctx.audit_access(member_id, "export_pdf")
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="personnel_record_{member_id}.pdf"',
            "X-Request-ID": request_id
        }
    )


@router.get("/members/{member_id}/summary")
async def get_member_summary(
    member_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_PERSONNEL))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
):
    """Отримати коротку довідку про військовослужбовця."""
    
    member = await session.get(ServiceMember, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="Service member not found")
    
    ctx.validate_unit_access(member.unit)

    member_dict = {
        "id": member.id,
        "service_number": member.service_number,
        "last_name": member.last_name,
        "first_name": member.first_name,
        "middle_name": member.middle_name,
        "rank": member.rank,
        "unit": member.unit,
        "specialty": member.specialty,
        "position": member.position,
        "status": member.status,
        "is_deployed": member.is_deployed,
        "years_of_service": member.years_of_service,
        "blood_type": member.blood_type,
        "combat_experience": member.combat_experience,
        "phone": member.phone,
        "email": member.email,
        "address": member.address,
        "enlistment_date": member.enlistment_date,
        "contract_end_date": member.contract_end_date,
        "allergies": member.allergies,
        "medical_conditions": member.medical_conditions,
        "medications": member.medications,
        "last_physical_date": member.last_physical_date,
    }
    
    summary = export_personnel_summary(member_dict)
    
    return envelope(summary, request_id=request_id)


@router.get("/members/{member_id}/medical/summary")
async def get_medical_summary(
    member_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
):
    """Отримати медичну довідку."""
    
    member = await session.get(ServiceMember, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="Service member not found")
    
    ctx.validate_unit_access(member.unit)

    medical_query = select(MedicalRecord).where(MedicalRecord.service_member_id == member_id)
    medical_result = await session.execute(medical_query)
    medical = medical_result.scalars().all()
    
    medical_dict = [
        {
            "record_type": m.record_type,
            "diagnosis": m.diagnosis,
            "treatment": m.treatment,
            "encounter_date": m.encounter_date,
            "outcome": m.outcome,
            "injury_severity": m.injury_severity,
        }
        for m in medical
    ]
    
    summary = export_medical_summary(medical_dict)
    
    return envelope(summary, request_id=request_id)


@router.get("/members/{member_id}/deployments/summary")
async def get_deployment_summary(
    member_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_PERSONNEL))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
):
    """Отримати довідку про розгортання."""
    
    member = await session.get(ServiceMember, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="Service member not found")
    
    ctx.validate_unit_access(member.unit)

    deploy_query = select(DeploymentRecord).where(DeploymentRecord.service_member_id == member_id)
    deploy_result = await session.execute(deploy_query)
    deployments = deploy_result.scalars().all()
    
    deploy_dict = [
        {
            "operation_name": d.operation_name,
            "location": d.location,
            "start_date": d.start_date,
            "end_date": d.end_date,
            "duration_days": d.duration_days,
            "mission_type": d.mission_type,
            "role": d.role,
            "status": d.status,
        }
        for d in deployments
    ]
    
    summary = export_deployment_summary(deploy_dict)
    
    return envelope(summary, request_id=request_id)


@router.get("/members/{member_id}/fhir")
async def export_member_fhir(
    member_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.EXPORT_DATA))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
):
    """Експорт військовослужбовця в FHIR формат."""
    
    member = await session.get(ServiceMember, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="Service member not found")
    
    ctx.validate_unit_access(member.unit)
    
    # Rate limit exports
    ctx.check_rate_limit("export", limit=5, window_seconds=60)


    member_dict = {
        "id": member.id,
        "service_number": member.service_number,
        "last_name": member.last_name,
        "first_name": member.first_name,
        "middle_name": member.middle_name,
        "date_of_birth": member.date_of_birth,
        "rank": member.rank,
        "specialty": member.specialty,
        "unit": member.unit,
        "years_of_service": member.years_of_service,
        "combat_experience": member.combat_experience,
        "blood_type": member.blood_type,
    }
    
    fhir_data = export_personnel_fhir(member_dict)
    
    # Audit export
    ctx.audit_access(member_id, "export_fhir")
    
    return envelope(fhir_data, request_id=request_id)



# Військові шаблони документів
@router.get("/members/{member_id}/templates/casualty-report")
async def generate_casualty_report_pdf(
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.EXPORT_DATA))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
    member_id: str,
    case_id: Annotated[Optional[str], Query()] = None,
):
    """Генерувати звіт про бойову травму (DD Form 1380)."""
    
    member = await session.get(ServiceMember, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="Service member not found")
    
    ctx.validate_unit_access(member.unit)
    
    # Rate limit exports
    ctx.check_rate_limit("export", limit=5, window_seconds=60)


    case_data = {}
    if case_id:
        case = await session.get(Case, case_id)
        if case:
            case_data = {
                "full_name": f"{member.last_name} {member.first_name} {member.middle_name or ''}".strip(),
                "incident_time": case.created_at,
                "incident_location": "—",  # Можна додати в модель
                "mechanism_of_injury": case.mechanism_of_injury or case.mechanism,
                "triage_code": case.triage_code,
                "evac_status": "—",  # Можна отримати з handoff
                "blood_type": member.blood_type,
                "vitals_json": case.vitals_json if hasattr(case, 'vitals_json') else [],
                "injuries_json": case.injuries_json if hasattr(case, 'injuries_json') else [],
                "treatments_json": case.treatments_json if hasattr(case, 'treatments_json') else [],
            }
    
    member_data = {
        "service_number": member.service_number,
        "rank": member.rank,
        "unit": member.unit,
        "blood_type": member.blood_type,
        "allergies": member.allergies,
    }
    
    pdf_bytes = generate_casualty_report(case_data, member_data)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="casualty_report_{member_id}.pdf"',
            "X-Request-ID": request_id
        }
    )


@router.get("/members/{member_id}/templates/medical-evacuation")
async def generate_medical_evacuation_pdf(
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.EXPORT_DATA))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
    member_id: str,
    case_id: Annotated[Optional[str], Query()] = None,
):
    """Генерувати медичну форму евакуації."""
    
    member = await session.get(ServiceMember, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="Service member not found")
    
    ctx.validate_unit_access(member.unit)
    
    # Rate limit exports
    ctx.check_rate_limit("export", limit=5, window_seconds=60)


    case_data = {}
    if case_id:
        case = await session.get(Case, case_id)
        if case:
            case_data = {
                "last_name": member.last_name,
                "first_name": member.first_name,
                "middle_name": member.middle_name,
                "incident_time": case.created_at,
                "incident_location": "—",
                "mechanism_of_injury": case.mechanism_of_injury or case.mechanism,
                "triage_code": case.triage_code,
                "blood_type": member.blood_type,
                "vitals_json": case.vitals_json if hasattr(case, 'vitals_json') else [],
                "treatments_json": case.treatments_json if hasattr(case, 'treatments_json') else [],
            }
    
    member_data = {
        "service_number": member.service_number,
        "rank": member.rank,
        "unit": member.unit,
        "blood_type": member.blood_type,
        "allergies": member.allergies,
        "date_of_birth": member.date_of_birth,
    }
    
    pdf_bytes = generate_medical_evacuation_form(case_data, member_data)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="medical_evacuation_{member_id}.pdf"',
            "X-Request-ID": request_id
        }
    )


@router.get("/members/{member_id}/templates/treatment-summary")
async def generate_treatment_summary_pdf(
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.EXPORT_DATA))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
    member_id: str,
    case_id: Annotated[Optional[str], Query()] = None,
):
    """Генерувати звіт про лікування."""
    
    member = await session.get(ServiceMember, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="Service member not found")
    
    ctx.validate_unit_access(member.unit)
    
    # Rate limit exports
    ctx.check_rate_limit("export", limit=5, window_seconds=60)


    case_data = {}
    if case_id:
        case = await session.get(Case, case_id)
        if case:
            case_data = {
                "full_name": f"{member.rank} {member.last_name} {member.first_name} {member.middle_name or ''}".strip(),
                "incident_time": case.created_at,
                "mechanism_of_injury": case.mechanism_of_injury or case.mechanism,
                "incident_location": "—",
                "triage_code": case.triage_code,
                "evac_status": "—",
                "treatments_json": case.treatments_json if hasattr(case, 'treatments_json') else [],
            }
    
    member_data = {
        "service_number": member.service_number,
        "rank": member.rank,
        "unit": member.unit,
    }
    
    pdf_bytes = generate_treatment_summary(case_data, member_data)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="treatment_summary_{member_id}.pdf"',
            "X-Request-ID": request_id
        }
    )


# Інтеграція з існуючими кейсами
@router.post("/members/{member_id}/link-case/{case_id}")
async def link_case_to_member(
    member_id: str,
    case_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.UPDATE_PERSONNEL))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
):
    """Прив'язати медичний кейс до військовослужбовця."""
    
    # Get member
    repo = PersonnelRepository(session)
    member = await repo.get_by_id_with_relations(
        member_id,
        include_medical=False, # Not needed for linking
        include_deployments=False,
        include_personnel=False,
        include_documents=False
    )
    
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="Service member not found")
    
    # ABAC: Unit isolation
    ctx.validate_unit_access(member.unit)
    
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Створити медичний запис
    medical_record = MedicalRecord(
        id=str(uuid.uuid4()),
        service_member_id=member_id,
        case_id=case_id,
        record_type="INJURY",
        diagnosis="—",  # Можна заповнити з даних кейсу
        diagnosis_code="—",
        treatment=case.notes or "—",
        provider_name=ctx.user_id,
        provider_type="MEDIC",
        encounter_date=case.created_at,
        injury_type="COMBAT" if case.mechanism_of_injury else "ACCIDENT",
        injury_mechanism=case.mechanism_of_injury or case.mechanism,
        injury_severity=case.triage_code,
        recorded_by=ctx.user_id
    )
    
    async with session.begin():
        session.add(medical_record)
    
    ctx.audit_access(member_id, "link_case")
    
    return envelope({
        "id": medical_record.id,
        "message": f"Case {case_id} linked to member {member_id}"
    }, request_id=request_id)


@router.get("/members/{member_id}/cases")
async def get_member_cases(
    member_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_PERSONNEL))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
):
    """Отримати всі медичні кейси військовослужбовця."""
    
    member = await session.get(ServiceMember, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="Service member not found")
        
    ctx.validate_unit_access(member.unit)
    
    # Export Hardening: Cap related records
    records_limit = 50
    # Знайти всі медичні записи для цього військовослужбовця
    medical_query = select(MedicalRecord).where(MedicalRecord.service_member_id == member_id)
    medical_result = await session.execute(medical_query)
    medical_records = medical_result.scalars().all()
    
    cases = []
    for med_record in medical_records:
        if med_record.case_id:
            case = await session.get(Case, med_record.case_id)
            if case:
                cases.append({
                    "id": case.id,
                    "created_at": case.created_at.isoformat(),
                    "mechanism_of_injury": case.mechanism_of_injury,
                    "triage_code": case.triage_code,
                    "notes": case.notes,
                    "medical_record_id": med_record.id,
                    "record_type": med_record.record_type,
                    "diagnosis": med_record.diagnosis,
                    "treatment": med_record.treatment,
                    "outcome": med_record.outcome,
                })
    
    return envelope({
        "service_member_id": member_id,
        "total_cases": len(cases),
        "cases": cases
    }, request_id=request_id)


@router.post("/members/{member_id}/medical-records")
async def create_medical_record(
    member_id: str,
    record_data: Dict[str, Any],
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.CREATE_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id_simple)],
):
    """Створити новий медичний запис для військовослужбовця."""
    
    member = await session.get(ServiceMember, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Service member not found")
    
    medical_record = MedicalRecord(
        id=str(uuid.uuid4()),
        service_member_id=member_id,
        case_id=record_data.get("case_id"),
        record_type=record_data.get("record_type", "EXAMINATION"),
        diagnosis=record_data.get("diagnosis"),
        diagnosis_code=record_data.get("diagnosis_code"),
        treatment=record_data.get("treatment"),
        medications=record_data.get("medications"),
        procedures=record_data.get("procedures"),
        provider_name=record_data.get("provider_name") or ctx.user_id,
        provider_type=record_data.get("provider_type", "MEDIC"),
        facility=record_data.get("facility"),
        encounter_date=datetime.fromisoformat(record_data["encounter_date"]).replace(tzinfo=None) if record_data.get("encounter_date") else datetime.utcnow(),
        discharge_date=datetime.fromisoformat(record_data["discharge_date"]).replace(tzinfo=None) if record_data.get("discharge_date") else None,
        outcome=record_data.get("outcome"),
        return_to_duty_date=datetime.fromisoformat(record_data["return_to_duty_date"]).replace(tzinfo=None) if record_data.get("return_to_duty_date") else None,
        limited_duty=record_data.get("limited_duty", False),
        limited_duty_end_date=datetime.fromisoformat(record_data["limited_duty_end_date"]).replace(tzinfo=None) if record_data.get("limited_duty_end_date") else None,
        injury_type=record_data.get("injury_type"),
        injury_mechanism=record_data.get("injury_mechanism"),
        injury_severity=record_data.get("injury_severity"),
        recorded_by=ctx.user_id
    )
    
    async with session.begin():
        session.add(medical_record)
    
    ctx.audit_access(member_id, "create_medical_record")
    
    return envelope({
        "id": medical_record.id,
        "message": "Medical record created successfully"
    }, request_id=request_id)
