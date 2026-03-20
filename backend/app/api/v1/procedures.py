"""Procedures router."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session
from app.core.utils import envelope

from app.models.cases import Case
from app.models.procedures import Procedure
from app.schemas.unified import ProcedureCreate, ProcedureResponse

router = APIRouter(prefix="/cases", tags=["procedures"])


@router.post("/{case_id}/procedures", response_model=dict)
async def add_procedure(
    case_id: str,
    body: ProcedureCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    proc_id = str(uuid.uuid4())
    proc = Procedure(id=proc_id, case_id=case_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(proc, field, value)

    session.add(proc)
    await session.commit()
    await session.refresh(proc)

    return envelope(ProcedureResponse.model_validate(proc).model_dump(mode='json'), request_id=request_id)
