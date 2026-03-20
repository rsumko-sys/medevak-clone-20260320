"""Documents router."""
import logging
import uuid
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.api.deps import get_current_user, get_request_id, get_session, require_role
from app.core.config import DOCUMENTS_UPLOAD_RATE_LIMIT
from app.core.utils import envelope
from app.models.cases import Case
from app.models.documents import CaseDocument
from app.repositories.documents import DocumentRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_BASE = Path(__file__).resolve().parents[3] / "uploads"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def _serialize_doc(d) -> dict:
    created_at = getattr(d, "created_at", None)
    if created_at is None:
        created_iso = None
    elif hasattr(created_at, "isoformat"):
        created_iso = created_at.isoformat()
    else:
        created_iso = str(created_at)

    filename = getattr(d, "filename", None)
    content_type = getattr(d, "content_type", None)
    return {
        "id": str(getattr(d, "id", "")),
        "case_id": str(getattr(d, "case_id", "")),
        "filename": filename,
        "file_name": filename,
        "content_type": content_type,
        "document_type": content_type,
        "file_path": filename,
        "created_at": created_iso,
    }


@router.get("")
async def list_documents(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
    case_id: str | None = Query(None),
):
    repo = DocumentRepository(session)
    filters = [CaseDocument.case_id == case_id] if case_id else None
    try:
        items = await repo.get_all(filters=filters)
    except (OperationalError, ProgrammingError) as exc:
        # Keep API alive during schema drift; empty list is safer than crashing command flow.
        logger.exception("Documents table unavailable: %s", exc)
        return envelope([], request_id=request_id)
    return envelope([_serialize_doc(d) for d in items], request_id=request_id)


@router.post("/upload")
@limiter.limit(DOCUMENTS_UPLOAD_RATE_LIMIT)
async def upload_document(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(require_role("admin", "medic"))],
    request_id: Annotated[str, Depends(get_request_id)],
    case_id: str | None = Query(None),
    file: UploadFile = File(...),
):
    if not case_id:
        raise HTTPException(status_code=400, detail="case_id required")
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=422, detail=f"Unsupported file type. Allowed: pdf, jpeg, png")

    ext_map = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}
    ext = ext_map[content_type]

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max {MAX_UPLOAD_BYTES // (1024 * 1024)}MB",
        )

    doc_id = str(uuid.uuid4())
    stored_name = f"{doc_id}{ext}"
    case_dir = UPLOAD_BASE / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    stored_path = case_dir / stored_name
    stored_path.write_bytes(content)

    doc = CaseDocument(
        id=doc_id,
        case_id=case_id,
        filename=stored_name,
        content_type=content_type,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return envelope(_serialize_doc(doc), request_id=request_id)
