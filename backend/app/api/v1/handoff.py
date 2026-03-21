"""Handoff router — patient handoff generation and confirmation."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session
from app.core.utils import envelope
from app.models.cases import Case
from app.models.evacuation import EvacuationRecord as CaseHandoff
from app.models.medications import MedicationAdministration as CaseMedicationAdministration

from app.repositories.base import BaseRepository
from app.repositories.medications import MedicationRepository
from app.repositories.observations import ObservationRepository
from app.repositories.procedures import ProcedureRepository
from app.schemas.handoff import HandoffUpdateRequest, HandoffConfirmRequest
from app.services.handoff_service import HandoffService

router = APIRouter(tags=["handoff"])

_top_router = APIRouter(prefix="/handoffs")
_case_router = APIRouter(prefix="/cases/{case_id}/handoff")


async def _aggregate_mist(session: AsyncSession, case_id: str) -> tuple[dict, list[str]]:
    """Aggregate MIST data: mechanism, injuries, signs, treatment. Never returns nulls.
    Returns (mist_dict, warnings). Warnings list contains non-fatal aggregation errors."""
    mechanism = ""
    injuries: list = []
    signs: dict = {"vitals": []}
    treatment: dict = {"medications": [], "procedures": []}
    warnings: list[str] = []

    # Mechanism from case
    case = await session.get(Case, case_id)
    if case:
        mechanism = getattr(case, "mechanism_of_injury", None) or getattr(case, "mechanism", None) or ""

    # Injuries (from CaseInjury if available)
    try:
        from app.models.cases import CaseInjury
        stmt = select(CaseInjury).where(CaseInjury.case_id == case_id)
        res = await session.execute(stmt)
        for row in res.scalars().all():
            injuries.append({
                "id": row.id,
                "body_part": getattr(row, "body_part_code", "") or "",
                "type": getattr(row, "injury_type_code", "") or "",
            })
    except ImportError as e:
        logger.warning("CaseInjury import failed in MIST aggregation: %s", e)
    except Exception as e:
        logger.exception("MIST injuries aggregation failed for case %s: %s", case_id, e)
        warnings.append("failed to load injuries")

    # Signs from observations/vitals
    obs_repo = ObservationRepository(session)
    try:
        obs_list = await obs_repo.get_by_case(case_id)
        signs["vitals"] = [
            {"type": getattr(o, "observation_type", "") or "", "value": str(getattr(o, "value", "") or "")}
            for o in obs_list
        ]
    except Exception as e:
        logger.exception("MIST signs aggregation failed for case %s: %s", case_id, e)
        warnings.append("failed to load signs")

    # Treatment: medications
    try:
        med_repo = MedicationRepository(session)
        meds = await med_repo.get_all(filters=[CaseMedicationAdministration.case_id == case_id])
        for row in meds:
            treatment["medications"].append({
                "code": row.medication_code or "",
                "dose": row.dose_value,
                "unit": row.dose_unit_code or "",
            })
    except Exception as e:
        logger.exception("MIST medications aggregation failed for case %s: %s", case_id, e)
        warnings.append("failed to load medications")

    # Treatment: procedures
    try:
        from app.models.cases import CaseProcedure
        proc_repo = ProcedureRepository(session)
        procs = await proc_repo.get_all(filters=[CaseProcedure.case_id == case_id])
        for row in procs:
            treatment["procedures"].append({
                "code": getattr(row, "procedure_code", "") or "",
                "notes": getattr(row, "notes", "") or "",
            })
    except Exception as e:
        logger.exception("MIST procedures aggregation failed for case %s: %s", case_id, e)
        warnings.append("failed to load procedures")

    mist = {"mechanism": mechanism, "injuries": injuries, "signs": signs, "treatment": treatment}
    return mist, warnings


@_top_router.get("")
async def list_handoffs(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
    case_id: Annotated[str | None, Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(le=500)] = 100,
):
    """List all handoff records (dashboard view) with full MIST data."""
    repo = BaseRepository(CaseHandoff, session)
    filters = [CaseHandoff.case_id == case_id] if case_id else None
    items = await repo.get_all(
        filters=filters,
        order_by=CaseHandoff.created_at.desc(),
        offset=offset,
        limit=limit,
    )
    
    # H4.1: Batch-load MIST data for all cases to avoid N+1
    case_ids = [i.case_id for i in items]
    mist_data = {}
    for cid in case_ids:
        mist, warnings = await _aggregate_mist(session, cid)
        mist_data[cid] = (mist, warnings)
    
    result = []
    for i in items:
        mist, warnings = mist_data.get(i.case_id, ({}, []))
        item = {
            "id": i.id,
            "case_id": i.case_id,
            "mist_text": i.mist_summary or "",
            "mechanism": mist.get("mechanism", []),
            "injuries": mist.get("injuries", []),
            "signs": mist.get("signs", []),
            "treatment": mist.get("treatment", []),
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "operator_id": getattr(i, "operator_id", None),
        }
        if warnings:
            item["warnings"] = warnings
        result.append(item)
    return envelope(result, request_id=request_id)


@_case_router.get("")
async def get_handoff(
    case_id: Annotated[str, Path(...)],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Fetch the handoff record for a case with full MIST data."""
    repo = BaseRepository(CaseHandoff, session)
    items = await repo.get_all(
        filters=[CaseHandoff.case_id == case_id],
        order_by=CaseHandoff.created_at.desc(),
        offset=0,
        limit=1,
    )
    if not items:
        raise HTTPException(status_code=404, detail="Handoff not found")
    i = items[0]
    mist, warnings = await _aggregate_mist(session, case_id)
    result = {
        "id": i.id,
        "case_id": i.case_id,
        "mist_text": i.mist_summary or "",
        "mechanism": mist["mechanism"],
        "injuries": mist["injuries"],
        "signs": mist["signs"],
        "treatment": mist["treatment"],
        "created_at": i.created_at.isoformat() if i.created_at else None,
        "operator_id": getattr(i, "operator_id", None),
    }
    if warnings:
        result["warnings"] = warnings
    return envelope(result, request_id=request_id)


@_case_router.post("/generate")
async def generate_handoff(
    case_id: Annotated[str, Path(...)],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Generate a handoff presentation from the current case state with full MIST data."""
    svc = HandoffService(session, user_id=user.get("sub"), device_id=user.get("device_id"))
    result = await svc.generate(case_id)
    mist, warnings = await _aggregate_mist(session, case_id)
    if isinstance(result, dict):
        result.update({
            "mechanism": mist["mechanism"],
            "injuries": mist["injuries"],
            "signs": mist["signs"],
            "treatment": mist["treatment"],
        })
        if warnings:
            result["warnings"] = warnings
    return envelope(result, request_id=request_id)


@_case_router.put("")
async def update_handoff(
    case_id: Annotated[str, Path(...)],
    body: HandoffUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Update the handoff record."""
    svc = HandoffService(session, user_id=user.get("sub"), device_id=user.get("device_id"))
    result = await svc.update(case_id, body)
    if isinstance(result, dict):
        mist, warnings = await _aggregate_mist(session, case_id)
        result.setdefault("mechanism", mist["mechanism"])
        result.setdefault("injuries", mist["injuries"])
        result.setdefault("signs", mist["signs"])
        result.setdefault("treatment", mist["treatment"])
        if warnings:
            result["warnings"] = warnings
    return envelope(result, request_id=request_id)


@_case_router.post("/confirm")
async def confirm_handoff(
    case_id: Annotated[str, Path(...)],
    body: HandoffConfirmRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Mark the handoff as confirmed by the receiving party."""
    svc = HandoffService(session, user_id=user.get("sub"), device_id=user.get("device_id"))
    result = await svc.confirm(case_id, body)
    if isinstance(result, dict):
        mist, warnings = await _aggregate_mist(session, case_id)
        result.setdefault("mechanism", mist["mechanism"])
        result.setdefault("injuries", mist["injuries"])
        result.setdefault("signs", mist["signs"])
        result.setdefault("treatment", mist["treatment"])
        if warnings:
            result["warnings"] = warnings
    return envelope(result, request_id=request_id)


# Include both sub-routers into the main router
router.include_router(_top_router)
router.include_router(_case_router)
