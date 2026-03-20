"""Events router."""
import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_request_id, get_session, require_permission
from app.core.idempotency import get_idempotent_response, payload_fingerprint, save_idempotent_response
from app.core.realtime import realtime_manager
from app.core.security import Permission, SecurityContext
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
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.CREATE_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
):
    path = f"/cases/{case_id}/events"
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

    e_id = str(uuid.uuid4())
    evt = Event(id=e_id, case_id=case_id, actor_id=ctx.user_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(evt, field, value)

    session.add(evt)
    await session.commit()
    await session.refresh(evt)

    response_data = EventResponse.model_validate(evt).model_dump(mode='json')
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

    await realtime_manager.broadcast(
        "case.event.created",
        {"case_id": case_id, "event_id": e_id, "by": ctx.user_id},
    )

    return envelope(response_data, request_id=request_id)
