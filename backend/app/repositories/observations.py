"""Observations repository."""
from sqlalchemy import select
from app.models.vitals import VitalsObservation
from app.repositories.base import BaseRepository


class ObservationRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(VitalsObservation, session)

    async def get_by_case(self, case_id: str):
        return await self.get_all(
            filters=[VitalsObservation.case_id == case_id],
        )

