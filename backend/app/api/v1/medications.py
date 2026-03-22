"""Medications router."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session, require_role
from app.core.utils import envelope

from app.models.cases import Case
from app.models.medications import MedicationAdministration
from app.schemas.unified import MedicationCreate, MedicationResponse

router = APIRouter(prefix="/cases", tags=["medications"])


@router.post("/{case_id}/medications", response_model=dict)
async def add_medication(
    case_id: str,
    body: MedicationCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(require_role("admin", "medic"))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    med_id = str(uuid.uuid4())
    med = MedicationAdministration(id=med_id, case_id=case_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(med, field, value)

    session.add(med)
    await session.commit()
    await session.refresh(med)

    return envelope(MedicationResponse.model_validate(med).model_dump(mode='json'), request_id=request_id)
