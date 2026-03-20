"""Base repository."""
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, model, session: AsyncSession):
        self.model = model
        self.session = session

    async def get_all(
        self,
        filters=None,
        order_by=None,
        offset: int = 0,
        limit: int | None = None,
    ):
        stmt = select(self.model)
        if filters:
            for f in filters:
                stmt = stmt.where(f)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
