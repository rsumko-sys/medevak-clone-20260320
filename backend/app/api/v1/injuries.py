"""Injuries router."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session
from app.core.utils import envelope

from app.models.cases import Case
from app.models.injuries import Injury
from app.schemas.unified import InjuryCreate, InjuryResponse

router = APIRouter(prefix="/cases", tags=["injuries"])


@router.post("/{case_id}/injuries", response_model=dict)
async def add_injury(
    case_id: str,
    body: InjuryCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    inj_id = str(uuid.uuid4())
    inj = Injury(id=inj_id, case_id=case_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(inj, field, value)

    session.add(inj)
    await session.commit()
    await session.refresh(inj)

    return envelope(InjuryResponse.model_validate(inj).model_dump(mode='json'), request_id=request_id)
