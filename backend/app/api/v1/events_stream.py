"""SSE endpoint — realtime event stream (polling over long-lived HTTP)."""
import asyncio
import json
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.core.database import AsyncSessionLocal
from app.models.events import Event
from sqlalchemy import select

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/stream")
async def stream_events(
    user: Annotated[dict, Depends(get_current_user)],
):
    """
    Server-Sent Events stream.

    Polls for new events every second and pushes them to the client.
    Use GET /events?since=<iso> for a polling fallback.

    Client usage:
        const es = new EventSource("/api/events/stream");
        es.onmessage = e => console.log("NEW EVENT:", JSON.parse(e.data));
    """
    unit = user.get("unit", "")

    async def event_generator() -> AsyncIterator[str]:
        last_id: str | None = None

        async with AsyncSessionLocal() as db:
            while True:
                stmt = (
                    select(Event)
                    .where(Event.unit == unit)
                    .order_by(Event.created_at.desc())
                    .limit(1)
                )
                latest = (await db.execute(stmt)).scalar_one_or_none()

                if latest and str(latest.id) != last_id:
                    last_id = str(latest.id)
                    data = json.dumps(
                        {
                            "id": str(latest.id),
                            "type": latest.type,
                            "entity_type": latest.entity_type,
                            "entity_id": str(latest.entity_id),
                            "payload": latest.payload,
                            "created_at": (
                                latest.created_at.isoformat()
                                if latest.created_at is not None
                                else None
                            ),
                        },
                        ensure_ascii=False,
                    )
                    yield f"data: {data}\n\n"

                await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable Nginx buffering
        },
    )
