"""Vitals router."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session, require_role
from app.core.utils import envelope

from app.models.cases import Case
from app.models.vitals import VitalsObservation
from app.schemas.unified import VitalsCreate, VitalsResponse

router = APIRouter(prefix="/cases", tags=["vitals"])


@router.post("/{case_id}/vitals", response_model=dict)
async def add_vitals(
    case_id: str,
    body: VitalsCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(require_role("admin", "medic"))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    v_id = str(uuid.uuid4())
    v = VitalsObservation(id=v_id, case_id=case_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(v, field, value)

    session.add(v)
    await session.commit()
    await session.refresh(v)

    return envelope(VitalsResponse.model_validate(v).model_dump(mode='json'), request_id=request_id)
