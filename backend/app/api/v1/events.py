"""Events router."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session, require_role
from app.core.utils import envelope

from app.models.cases import Case
from app.models.events import Event
from app.schemas.unified import EventCreate, EventResponse

router = APIRouter(prefix="/cases", tags=["events"])


@router.post("/{case_id}/events", response_model=dict)
async def add_event(
    case_id: str,
    body: EventCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(require_role("admin", "medic"))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    e_id = str(uuid.uuid4())
    evt = Event(id=e_id, case_id=case_id, actor_id=user.get("sub"))
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(evt, field, value)

    session.add(evt)
    await session.commit()
    await session.refresh(evt)

    return envelope(EventResponse.model_validate(evt).model_dump(mode='json'), request_id=request_id)
