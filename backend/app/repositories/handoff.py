"""Handoff repository."""
from app.models.evacuation import EvacuationRecord
from app.repositories.base import BaseRepository


class HandoffRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(EvacuationRecord, session)

