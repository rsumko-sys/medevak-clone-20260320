"""MARCH Assessments router."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session
from app.core.utils import envelope

from app.models.cases import Case
from app.models.march import MarchAssessment
from app.schemas.unified import MarchCreate, MarchResponse

router = APIRouter(prefix="/cases", tags=["march"])


@router.post("/{case_id}/march", response_model=dict)
async def add_march(
    case_id: str,
    body: MarchCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    m_id = str(uuid.uuid4())
    m = MarchAssessment(id=m_id, case_id=case_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(m, field, value)

    session.add(m)
    await session.commit()
    await session.refresh(m)

    return envelope(MarchResponse.model_validate(m).model_dump(mode='json'), request_id=request_id)
