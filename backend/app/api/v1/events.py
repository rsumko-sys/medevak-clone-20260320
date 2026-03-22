"""Events router."""
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session, require_role
from app.core.utils import envelope
from app.models.cases import Case
from app.models.events import Event
from app.schemas.unified import EventCreate, EventResponse
from app.services.events import log_event

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/case/{case_id}", response_model=dict)
async def add_case_event(
    case_id: str,
    body: EventCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(require_role("admin", "medic"))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    evt = await log_event(
        session,
        type=body.type,
        entity_type="case",
        entity_id=case_id,
        payload=body.payload or {},
        user=user,
    )

    await session.commit()
    await session.refresh(evt)
    return envelope(EventResponse.model_validate(evt).model_dump(mode="json"), request_id=request_id)


@router.get("", response_model=dict)
async def get_events(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
    since: Optional[str] = Query(None, description="ISO datetime — return events after this timestamp"),
    limit: int = Query(50, le=200),
):
    stmt = select(Event).where(Event.unit == user.get("unit", ""))

    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            stmt = stmt.where(Event.created_at > since_dt)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid 'since' datetime format")

    stmt = stmt.order_by(Event.created_at.desc()).limit(limit)
    events = (await session.execute(stmt)).scalars().all()

    return envelope(
        [EventResponse.model_validate(e).model_dump(mode="json") for e in events],
        request_id=request_id,
    )
