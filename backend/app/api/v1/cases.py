"""Cases router."""
import json
import logging
import uuid
from datetime import datetime
from typing import Annotated, Optional
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Header
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session, require_role, require_permission
from app.core.audit_helper import log_audit
from app.core.config import CASES_CREATE_RATE_LIMIT
from app.core.idempotency import get_idempotent_response, payload_fingerprint, save_idempotent_response
from app.core.realtime import realtime_manager
from app.core.security import Permission, SecurityContext
from app.core.sync_helper import enqueue_sync
from app.core.utils import envelope

# Models
from app.models.cases import Case
from app.models.injuries import Injury
from app.models.procedures import Procedure
from app.models.medications import MedicationAdministration
from app.models.vitals import VitalsObservation
from app.models.march import MarchAssessment
from app.models.form100 import Form100Record
from app.models.evacuation import EvacuationRecord
from app.models.events import Event

# Schemas
from app.schemas.unified import CaseCreate, CaseUpdate, CaseResponse, CaseDetailResponse, InjuryCreate, Form100Response

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/cases", tags=["cases"])


def _from_json(value: str | None):
    if not value:
        return None
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


def _legacy_to_canonical(form: Form100Record) -> dict:
    marks = []
    if form.injury_location:
        marks.append({"wound_mark_location": form.injury_location})
    return {
        "stub": {
            "issued_at": form.created_at.isoformat() if form.created_at else None,
            "isolation_flag": False,
            "urgent_care_flag": False,
            "sanitary_processing_flag": False,
        },
        "front_side": {
            "injury": {
                "injury_or_illness_datetime": form.injury_datetime.isoformat() if form.injury_datetime else None,
                "diagnosis": form.diagnosis_summary,
                "injury_mechanism": form.injury_mechanism,
                "injury_category_codes": [form.injury_mechanism] if form.injury_mechanism else [],
                "body_diagram_marks": marks,
            },
            "treatment": {
                "treatment_notes": form.treatment_summary,
            },
            "evacuation": {
                "recommendation_notes": form.evacuation_recommendation,
            },
        },
        "back_side": {
            "stage_log": [],
            "signature": {
                "physician_name": form.documented_by,
                "signed_at": form.updated_at.isoformat() if form.updated_at else None,
            },
        },
        "meta_legal_rules": {
            "commander_notified": form.commander_notified,
            "additional_notes": form.notes,
        },
    }


def _canonical_from_form(form: Form100Record) -> dict:
    front_side = {}
    identity = _from_json(form.front_side_identity_json)
    injury = _from_json(form.front_side_injury_json)
    treatment = _from_json(form.front_side_treatment_json)
    evacuation = _from_json(form.front_side_evacuation_json)
    triage_markers = _from_json(form.front_side_triage_markers_json)
    body_diagram = _from_json(form.front_side_body_diagram_json)

    if identity is not None:
        front_side["identity"] = identity
    if injury is not None:
        front_side["injury"] = injury
    if treatment is not None:
        front_side["treatment"] = treatment
    if evacuation is not None:
        front_side["evacuation"] = evacuation
    if triage_markers is not None:
        front_side["triage_markers"] = triage_markers
    if body_diagram is not None:
        front_side["body_diagram"] = body_diagram

    back_side = {}
    stage_log = _from_json(form.back_side_stage_log_json)
    signature = _from_json(form.back_side_signature_json)
    if stage_log is not None:
        back_side["stage_log"] = stage_log
    if signature is not None:
        back_side["signature"] = signature

    canonical = {
        "stub": _from_json(form.stub_json),
        "front_side": front_side if front_side else None,
        "back_side": back_side if back_side else None,
        "meta_legal_rules": _from_json(form.meta_legal_rules_json),
    }
    if not canonical["stub"] and not canonical["front_side"] and not canonical["back_side"] and not canonical["meta_legal_rules"]:
        return _legacy_to_canonical(form)
    return canonical


def _form100_response_payload(form: Form100Record) -> dict:
    canonical = _canonical_from_form(form)
    payload = {
        "id": form.id,
        "case_id": form.case_id,
        "document_number": form.document_number,
        "injury_datetime": form.injury_datetime,
        "injury_location": form.injury_location,
        "injury_mechanism": form.injury_mechanism,
        "diagnosis_summary": form.diagnosis_summary,
        "documented_by": form.documented_by,
        "treatment_summary": form.treatment_summary,
        "evacuation_recommendation": form.evacuation_recommendation,
        "commander_notified": form.commander_notified,
        "notes": form.notes,
        "stub": canonical.get("stub"),
        "front_side": canonical.get("front_side"),
        "back_side": canonical.get("back_side"),
        "meta_legal_rules": canonical.get("meta_legal_rules"),
        "created_at": form.created_at,
        "updated_at": form.updated_at,
        "voided": form.voided,
    }
    return Form100Response.model_validate(payload).model_dump(mode="json")

def _apply_body_to_case(case: Case, body: CaseCreate | CaseUpdate) -> None:
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(case, field, value)

@router.post("", response_model=dict)
@limiter.limit(CASES_CREATE_RATE_LIMIT)
async def create_case(
    request: Request,
    body: CaseCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.CREATE_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
):
    path = "/cases"
    payload_hash = payload_fingerprint(body.model_dump(mode="json", exclude_unset=True))
    if idempotency_key:
        existing = await get_idempotent_response(
            session,
            idempotency_key,
            ctx.user_id,
            request_path=path,
            payload_hash=payload_hash,
        )
        if existing:
            if existing.get("conflict"):
                raise HTTPException(status_code=409, detail="Idempotency key re-used with different payload")
            return envelope(existing["body"], request_id=request_id)

    case_id = str(uuid.uuid4())
    case = Case(id=case_id, created_by=ctx.user_id)
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
    await log_audit(session, "cases", case_id, "create", ctx.user_id, new_values=body_data)
    await enqueue_sync(session, "case", case_id, "create", {"id": case_id}, ctx.user.get("device_id"))
    
    await session.commit()
    await session.refresh(case)

    response_data = CaseResponse.model_validate(case).model_dump(mode='json')
    if idempotency_key:
        await save_idempotent_response(
            session,
            idempotency_key,
            ctx.user_id,
            path,
            200,
            response_data,
            payload_hash=payload_hash,
        )

    await realtime_manager.broadcast("case.created", {"id": case_id, "by": ctx.user_id})
    return envelope(response_data, request_id=request_id)


@router.get("", response_model=dict)
async def list_cases(
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_MEDICAL))],
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
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_MEDICAL))],
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
    form100 = (
        await session.execute(
            get_stmt(Form100Record).order_by(Form100Record.created_at.desc())
        )
    ).scalars().first()
    evac = (await session.execute(get_stmt(EvacuationRecord))).scalars().first()
    events = (await session.execute(get_stmt(Event).order_by(Event.event_time.desc()))).scalars().all()

    detail = CaseDetailResponse.model_validate(case)
    detail.injuries = injuries
    detail.procedures = procedures
    detail.sub_medications = medications
    detail.observations = vitals
    detail.march_assessments = march
    detail.form100 = Form100Response.model_validate(_form100_response_payload(form100)) if form100 else None
    detail.evacuation = evac
    detail.events = events

    return envelope(detail.model_dump(mode='json'), request_id=request_id)


@router.patch("/{case_id}", response_model=dict)
async def update_case(
    case_id: Annotated[str, Path(...)],
    body: CaseUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.UPDATE_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
):
    path = f"/cases/{case_id}"
    payload_hash = payload_fingerprint(body.model_dump(mode="json", exclude_unset=True))
    if idempotency_key:
        existing = await get_idempotent_response(
            session,
            idempotency_key,
            ctx.user_id,
            request_path=path,
            payload_hash=payload_hash,
        )
        if existing:
            if existing.get("conflict"):
                raise HTTPException(status_code=409, detail="Idempotency key re-used with different payload")
            return envelope(existing["body"], request_id=request_id)

    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    old_values = CaseUpdate.model_validate(case).model_dump()
    _apply_body_to_case(case, body)
    
    await log_audit(session, "cases", case_id, "update", ctx.user_id, old_values=old_values, new_values=body.model_dump(exclude_unset=True))
    await enqueue_sync(session, "case", case_id, "update", {"id": case_id}, ctx.user.get("device_id"))
    
    await session.commit()
    await session.refresh(case)
    response_data = CaseResponse.model_validate(case).model_dump(mode='json')
    if idempotency_key:
        await save_idempotent_response(
            session,
            idempotency_key,
            ctx.user_id,
            path,
            200,
            response_data,
            payload_hash=payload_hash,
        )

    await realtime_manager.broadcast("case.updated", {"id": case_id, "by": ctx.user_id})
    return envelope(response_data, request_id=request_id)


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
    await realtime_manager.broadcast("case.deleted", {"id": case_id, "by": user.get("sub")})
    return envelope({"deleted": case_id}, request_id=request_id)
