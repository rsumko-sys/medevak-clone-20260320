"""Event logging service."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.events import Event


async def log_event(
    db: AsyncSession,
    *,
    type: str,
    entity_type: str,
    entity_id: str,
    payload: dict,
    user: dict,
) -> Event:
    """Append a domain event and stage it in the session (caller must commit)."""
    event = Event(
        type=type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        payload=payload,
        unit=user.get("unit", ""),
        created_by=user.get("sub"),
    )
    db.add(event)
    return event
