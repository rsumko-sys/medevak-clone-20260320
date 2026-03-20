"""Medications repository."""
from app.models.medications import MedicationAdministration
from app.repositories.base import BaseRepository


class MedicationRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(MedicationAdministration, session)
