"""Case documents repository."""
from app.models.documents import CaseDocument
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(CaseDocument, session)
