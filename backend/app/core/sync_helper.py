"""Sync queue helper (outbox pattern)."""
import json
import uuid
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sync_queue import SyncQueue


def _normalize_status(status: str | None) -> str:
    if status == "synced":
        return "acked"
    if status == "failed":
        return "dead_letter"
    return status or "pending"


async def enqueue_sync(
    session: AsyncSession,
    entity_type: str,
    entity_id: str,
    action: str,
    payload: dict | None = None,
    device_id: str | None = None,
) -> None:
    """Enqueue sync job on mutation."""
    job = SyncQueue(
        id=str(uuid.uuid4()),
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        payload=json.dumps(payload) if payload else None,
        status="pending",
        retries=0,
        device_id=device_id,
    )
    session.add(job)


async def get_sync_stats(session: AsyncSession) -> dict:
    """Real stats from sync_queue."""
    result = await session.execute(
        select(
            func.sum(case((SyncQueue.status == "pending", 1), else_=0)).label("pending"),
            func.sum(case((SyncQueue.status == "synced", 1), else_=0)).label("synced"),
            func.sum(case((SyncQueue.status == "failed", 1), else_=0)).label("failed"),
            func.sum(case((SyncQueue.status == "acked", 1), else_=0)).label("acked"),
            func.sum(case((SyncQueue.status == "dead_letter", 1), else_=0)).label("dead_letter"),
        ).select_from(SyncQueue)
    )
    row = result.one()
    pending = int(row.pending or 0)
    acked = int((row.acked or 0) + (row.synced or 0))
    dead_letter = int((row.dead_letter or 0) + (row.failed or 0))
    return {
        "pending": pending,
        "acked": acked,
        "dead_letter": dead_letter,
        # Keep legacy keys for frontend compatibility during migration.
        "synced": acked,
        "failed": dead_letter,
    }


async def get_sync_queue(
    session: AsyncSession,
    status_filter: str | None = None,
    entity_type: str | None = None,
    limit: int = 200,
) -> list[dict]:
    """List sync queue items."""
    stmt = select(SyncQueue).order_by(SyncQueue.created_at.desc()).limit(limit)
    if status_filter:
        if status_filter == "acked":
            stmt = stmt.where(SyncQueue.status.in_(["acked", "synced"]))
        elif status_filter == "dead_letter":
            stmt = stmt.where(SyncQueue.status.in_(["dead_letter", "failed"]))
        else:
            stmt = stmt.where(SyncQueue.status == status_filter)
    if entity_type:
        stmt = stmt.where(SyncQueue.entity_type == entity_type)
    result = await session.execute(stmt)
    items = result.scalars().all()
    return [
        {
            "id": i.id,
            "entity_type": i.entity_type,
            "entity_id": i.entity_id,
            "action": i.action,
            "status": _normalize_status(i.status),
            "retries": i.retries,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in items
    ]
