from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session
from app.core.sync_helper import get_sync_queue as fetch_queue, get_sync_stats as fetch_stats
from app.core.utils import envelope
from app.services.sync_service import SyncService


router = APIRouter(tags=["sync"])



@router.get("/stats")
async def get_sync_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Sync statistics from sync_queue."""
    stats = await fetch_stats(session)
    return envelope(stats, request_id=request_id)


@router.get("/queue")
async def get_sync_queue(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
    status: str | None = None,
    entity_type: str | None = None,
    limit: int = 200,
):
    """Sync queue items."""
    items = await fetch_queue(session, status_filter=status, entity_type=entity_type, limit=limit)
    return envelope(items, request_id=request_id)


@router.post("/reconcile")
async def reconcile_sync_data(
    data: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """
    Reconcile remote sync data with local database.
    Body should contain 'entity_type' and 'payload'.
    """
    entity_type = data.get("entity_type")
    payload = data.get("payload")
    
    if not entity_type or not payload:
        raise HTTPException(status_code=400, detail="Missing entity_type or payload")
        
    sync_service = SyncService(session)
    success = await sync_service.reconcile_entity(entity_type, payload)
    
    return envelope({
        "success": success,
        "entity_id": payload.get("id"),
        "timestamp": datetime.utcnow().isoformat()
    }, request_id=request_id)

