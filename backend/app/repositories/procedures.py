"""Procedures repository."""
from app.models.procedures import Procedure
from app.repositories.base import BaseRepository


class ProcedureRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(Procedure, session)

