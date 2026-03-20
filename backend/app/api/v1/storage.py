"""Storage router for disk organization, archival, and space optimization."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_request_id, require_role
from app.core.utils import envelope
from app.core.storage_manager import archive_case_uploads, get_storage_stats


router = APIRouter(prefix="/storage", tags=["storage"])

PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_BASE = PROJECT_ROOT / "uploads"
ARCHIVE_BASE = PROJECT_ROOT / "archives"
EXPORT_BASE = PROJECT_ROOT / "exports"


@router.get("/stats")
async def storage_stats(
    user: Annotated[dict, Depends(require_role("admin", "medic"))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    data = await asyncio.to_thread(get_storage_stats, UPLOAD_BASE, ARCHIVE_BASE, EXPORT_BASE)
    return envelope(data, request_id=request_id)


@router.post("/archive")
async def archive_storage(
    user: Annotated[dict, Depends(require_role("admin"))],
    request_id: Annotated[str, Depends(get_request_id)],
    older_than_days: int = Query(7, ge=1, le=3650),
    remove_source: bool = Query(True),
    dry_run: bool = Query(False),
):
    result = await asyncio.to_thread(
        archive_case_uploads,
        UPLOAD_BASE,
        ARCHIVE_BASE,
        older_than_days,
        remove_source=remove_source,
        dry_run=dry_run,
    )
    return envelope(result, request_id=request_id)
