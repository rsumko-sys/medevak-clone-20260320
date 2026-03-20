import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.idempotency import IdempotencyRecord

async def get_idempotent_response(
    session: AsyncSession, 
    key: str, 
    user_id: str,
    request_path: Optional[str] = None,
    payload_hash: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Check if a request with this key has already been processed."""
    stmt = select(IdempotencyRecord).where(
        IdempotencyRecord.key == key,
        IdempotencyRecord.user_id == user_id
    )
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    
    if record:
        if record.expires_at < datetime.utcnow():
            # Clean up expired record
            await session.delete(record)
            await session.commit()
            return None

        stored_path = record.request_path or ""
        stored_hash = ""
        if "#" in stored_path:
            stored_path, stored_hash = stored_path.split("#", 1)

        if request_path and stored_path and stored_path != request_path:
            return {"conflict": True, "reason": "path_mismatch"}

        if payload_hash and stored_hash and stored_hash != payload_hash:
            return {"conflict": True, "reason": "payload_mismatch"}

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
    payload_hash: Optional[str] = None,
    ttl_hours: int = 24
):
    """Save a response for an idempotent request."""
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    
    request_path_value = path
    if payload_hash:
        request_path_value = f"{path}#{payload_hash}"

    record = IdempotencyRecord(
        key=key,
        user_id=user_id,
        request_path=request_path_value,
        response_code=str(status_code),
        response_body=response_body,
        created_at=datetime.utcnow(),
        expires_at=expires_at
    )
    session.add(record)
    await session.commit()


def payload_fingerprint(payload: Dict[str, Any]) -> str:
    """Create deterministic payload hash for idempotency conflict detection."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

async def cleanup_idempotency_records(session: AsyncSession):
    """Remove expired idempotency records."""
    stmt = delete(IdempotencyRecord).where(IdempotencyRecord.expires_at < datetime.utcnow())
    await session.execute(stmt)
    await session.commit()
