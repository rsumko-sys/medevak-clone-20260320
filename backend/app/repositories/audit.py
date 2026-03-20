"""Audit log repository."""
from sqlalchemy import select
from app.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(AuditLog, session)

    async def log(self, table_name: str, action: str, row_id: str = None, old_values=None, new_values=None, user_id=None):
        """Create audit log entry."""
        import uuid
        entry = AuditLog(
            id=str(uuid.uuid4()),
            table_name=table_name,
            action=action,
            row_id=str(row_id) if row_id else None,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
        )
        self.session.add(entry)

    async def get_filtered(self, table_name: str | None = None, row_id: str = None, limit: int = 200):
        """Get filtered audit logs."""
        stmt = select(AuditLog)
        if table_name:
            stmt = stmt.where(AuditLog.table_name == table_name)
        if row_id:
            stmt = stmt.where(AuditLog.row_id == row_id)
        
        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
