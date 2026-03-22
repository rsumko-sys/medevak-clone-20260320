"""Evacuation router."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user, get_request_id, get_session, require_role
from app.core.utils import envelope

from app.models.cases import Case
from app.models.evacuation import EvacuationRecord
from app.schemas.unified import EvacuationCreate, EvacuationResponse

router = APIRouter(prefix="/cases", tags=["evacuation"])


@router.post("/{case_id}/evacuation", response_model=dict)
async def upsert_evacuation(
    case_id: str,
    body: EvacuationCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(require_role("admin", "medic"))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    stmt = select(EvacuationRecord).where(EvacuationRecord.case_id == case_id)
    result = await session.execute(stmt)
    evac = result.scalars().first()
    
    if not evac:
        evac = EvacuationRecord(id=str(uuid.uuid4()), case_id=case_id)
        session.add(evac)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(evac, field, value)

    await session.commit()
    await session.refresh(evac)

    return envelope(EvacuationResponse.model_validate(evac).model_dump(mode='json'), request_id=request_id)


@router.get("/{case_id}/mist", response_model=dict)
async def generate_mist(
    case_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    from app.models.injuries import Injury
    from app.models.vitals import VitalsObservation
    from app.models.march import MarchAssessment
    from app.models.medications import MedicationAdministration
    from app.models.procedures import Procedure

    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    injuries = (await session.execute(select(Injury).where(Injury.case_id == case_id))).scalars().all()
    vitals = (await session.execute(select(VitalsObservation).where(VitalsObservation.case_id == case_id).order_by(VitalsObservation.measured_at.desc()))).scalars().first()
    march = (await session.execute(select(MarchAssessment).where(MarchAssessment.case_id == case_id).order_by(MarchAssessment.assessed_at.desc()))).scalars().first()
    meds = (await session.execute(select(MedicationAdministration).where(MedicationAdministration.case_id == case_id))).scalars().all()
    procs = (await session.execute(select(Procedure).where(Procedure.case_id == case_id))).scalars().all()

    # M - Mechanism
    mechanism = case.mechanism_of_injury or case.mechanism or "UNKNOWN"

    # I - Injuries
    injury_desc = ", ".join([f"{i.injury_type} ({i.body_region})" for i in injuries]) if injuries else "None recorded"

    # S - Signs/Symptoms
    signs = []
    if vitals:
        if vitals.heart_rate: signs.append(f"HR: {vitals.heart_rate}")
        if vitals.systolic_bp and vitals.diastolic_bp: signs.append(f"BP: {vitals.systolic_bp}/{vitals.diastolic_bp}")
        if vitals.gcs_total: signs.append(f"GCS: {vitals.gcs_total}")
    if march:
        if march.m_massive_bleeding: signs.append("Massive Bleeding: Yes")
        if march.a_airway_open: signs.append("Airway Open: Yes")
    signs_desc = ", ".join(signs) if signs else "No vitals/MARCH recorded"

    # T - Treatments
    treatments = []
    if case.tourniquet_applied:
        treatments.append(f"TQ Applied" + (f" at {case.tourniquet_time}" if case.tourniquet_time else ""))
    for med in meds:
        dose_info = f" {med.dose_value}{med.dose_unit_code}" if med.dose_value else ""
        treatments.append(f"{med.medication_code}{dose_info}")
    for proc in procs:
        treatments.append(f"{proc.procedure_code}")
    
    treatment_desc = ", ".join(treatments) if treatments else "None recorded"

    mist_summary = (
        f"M - Mechanism: {mechanism}\n"
        f"I - Injuries: {injury_desc}\n"
        f"S - Signs: {signs_desc}\n"
        f"T - Treatment: {treatment_desc}"
    )

    return envelope({"mist_summary": mist_summary}, request_id=request_id)
