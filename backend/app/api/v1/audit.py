"""Audit router."""
from typing import Annotated
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_request_id, get_session
from app.core.utils import envelope
from app.repositories.audit import AuditRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/audit", tags=["audit"])


def _serialize_audit(a) -> dict:
    return {
        "id": str(getattr(a, "id", "")),
        "table_name": getattr(a, "table_name", None),
        "row_id": getattr(a, "row_id", None),
        "action": getattr(a, "action", None),
        "user_id": getattr(a, "user_id", None),
        "created_at": a.created_at.isoformat() if getattr(a, "created_at", None) else None,
    }


@router.get("")
async def list_audit(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
    table_name: str | None = Query(None),
    row_id: str | None = Query(None),
    limit: int = Query(200, le=500),
):
    """List audit log entries."""
    repo = AuditRepository(session)
    items = await repo.get_filtered(table_name=table_name, row_id=row_id, limit=limit)
    return envelope([_serialize_audit(a) for a in items], request_id=request_id)
