import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.idempotency import IdempotencyRecord

async def get_idempotent_response(
    session: AsyncSession, 
    key: str, 
    user_id: str
) -> Optional[Dict[str, Any]]:
    """Check if a request with this key has already been processed."""
    stmt = select(IdempotencyRecord).where(
        IdempotencyRecord.key == key,
        IdempotencyRecord.user_id == user_id
    )
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    
    if record:
        if record.expires_at < datetime.now(timezone.utc):
            # Clean up expired record
            await session.delete(record)
            await session.commit()
            return None
        return {
            "status_code": int(record.response_code),
            "body": record.response_body
        }
    return None

async def save_idempotent_response(
    session: AsyncSession,
    key: str,
    user_id: str,
    path: str,
    status_code: int,
    response_body: Dict[str, Any],
    ttl_hours: int = 24
):
    """Save a response for an idempotent request."""
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    
    record = IdempotencyRecord(
        key=key,
        user_id=user_id,
        request_path=path,
        response_code=str(status_code),
        response_body=response_body,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at
    )
    session.add(record)
    await session.commit()

async def cleanup_idempotency_records(session: AsyncSession):
    """Remove expired idempotency records."""
    stmt = delete(IdempotencyRecord).where(IdempotencyRecord.expires_at < datetime.now(timezone.utc))
    await session.execute(stmt)
    await session.commit()
