"""Cases router."""
import logging
import uuid
from datetime import datetime
from typing import Annotated
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session, require_role
from app.core.audit_helper import log_audit
from app.core.config import CASES_CREATE_RATE_LIMIT
from app.core.sync_helper import enqueue_sync
from app.core.utils import envelope
from app.mappers.form100 import build_form100, validate_form100_minimum

# Models
from app.models.cases import Case
from app.models.injuries import Injury
from app.models.procedures import Procedure
from app.models.medications import MedicationAdministration
from app.models.vitals import VitalsObservation
from app.models.march import MarchAssessment
from app.models.evacuation import EvacuationRecord
from app.models.events import Event

# Schemas
from app.schemas.unified import CaseCreate, CaseUpdate, CaseResponse, CaseDetailResponse, InjuryCreate

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/cases", tags=["cases"])

def _apply_body_to_case(case: Case, body: CaseCreate | CaseUpdate) -> None:
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(case, field, value)

@router.post("", response_model=dict)
@limiter.limit(CASES_CREATE_RATE_LIMIT)
async def create_case(
    request: Request,
    body: CaseCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(require_role("admin", "medic"))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case_id = str(uuid.uuid4())
    case = Case(id=case_id, created_by=user.get("sub"))
    # Apply all fields EXCEPT injuries (handled below)
    body_data = body.model_dump(exclude={'injuries'}, exclude_unset=True)
    for field, value in body_data.items():
        setattr(case, field, value)
    session.add(case)

    # Transactional batch: save injuries in the SAME commit
    batch_injuries = body.injuries or []
    for inj_data in batch_injuries:
        inj = Injury(
            id=str(uuid.uuid4()),
            case_id=case_id,
            **inj_data.model_dump(exclude_unset=True)
        )
        session.add(inj)

    # Audit and Sync
    await log_audit(session, "cases", case_id, "create", user.get("sub"), new_values=body_data)
    await enqueue_sync(session, "case", case_id, "create", {"id": case_id}, user.get("device_id"))
    
    await session.commit()
    await session.refresh(case)
    
    return envelope(CaseResponse.model_validate(case).model_dump(mode='json'), request_id=request_id)


@router.get("", response_model=dict)
async def list_cases(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
    offset: int = 0,
    limit: int = 100,
):
    stmt = select(Case).order_by(Case.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    cases = result.scalars().all()
    
    resp = [CaseResponse.model_validate(c).model_dump(mode='json') for c in cases]
    return envelope(resp, request_id=request_id)


@router.get("/{case_id}", response_model=dict)
async def get_case(
    case_id: Annotated[str, Path(...)],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Fetch sub-records
    def get_stmt(model):
        return select(model).where(model.case_id == case_id, model.voided == False)

    injuries = (await session.execute(get_stmt(Injury))).scalars().all()
    procedures = (await session.execute(get_stmt(Procedure))).scalars().all()
    medications = (await session.execute(get_stmt(MedicationAdministration))).scalars().all()
    vitals = (await session.execute(get_stmt(VitalsObservation).order_by(VitalsObservation.measured_at.desc()))).scalars().all()
    march = (await session.execute(get_stmt(MarchAssessment).order_by(MarchAssessment.assessed_at.desc()))).scalars().all()
    evac = (await session.execute(get_stmt(EvacuationRecord))).scalars().first()
    events = (await session.execute(get_stmt(Event).order_by(Event.event_time.desc()))).scalars().all()

    detail = CaseDetailResponse.model_validate(case)
    detail.injuries = injuries
    detail.procedures = procedures
    detail.sub_medications = medications
    detail.observations = vitals
    detail.march_assessments = march
    detail.evacuation = evac
    detail.events = events
    detail.form100 = build_form100(detail)
    detail.form100_validation_errors = validate_form100_minimum(detail.form100)

    return envelope(detail.model_dump(mode='json'), request_id=request_id)


@router.patch("/{case_id}", response_model=dict)
async def update_case(
    case_id: Annotated[str, Path(...)],
    body: CaseUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(require_role("admin", "medic"))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    old_values = CaseUpdate.model_validate(case).model_dump()
    _apply_body_to_case(case, body)
    
    await log_audit(session, "cases", case_id, "update", user.get("sub"), old_values=old_values, new_values=body.model_dump(exclude_unset=True))
    await enqueue_sync(session, "case", case_id, "update", {"id": case_id}, user.get("device_id"))
    
    await session.commit()
    await session.refresh(case)
    return envelope(CaseResponse.model_validate(case).model_dump(mode='json'), request_id=request_id)


@router.delete("/{case_id}", response_model=dict)
async def delete_case(
    case_id: Annotated[str, Path(...)],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(require_role("admin"))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case.case_status = "VOIDED"
    await log_audit(session, "cases", case_id, "delete", user.get("sub"))
    await enqueue_sync(session, "case", case_id, "delete", {"id": case_id}, user.get("device_id"))
    
    await session.commit()
    return envelope({"deleted": case_id}, request_id=request_id)
