"""Audit logging helper."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_audit(
    session: AsyncSession,
    table_name: str,
    row_id: str | None,
    action: str,
    user_id: str | None = None,
    old_values=None,
    new_values=None,
):
    """Append audit log entry."""
    entry = AuditLog(
        id=str(uuid.uuid4()),
        table_name=table_name,
        row_id=row_id,
        action=action,
        user_id=user_id,
        old_values=old_values,
        new_values=new_values,
    )
    session.add(entry)
