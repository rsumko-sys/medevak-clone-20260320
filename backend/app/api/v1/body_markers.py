"""Body markers router — reference body parts for body map."""
from typing import Annotated
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_request_id, get_session
from app.core.utils import envelope
from app.models.injuries import Injury as CaseInjury

from app.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/body_markers", tags=["body_markers"])

BODY_PARTS = [
    "HEAD", "NECK", "CHEST", "ABDOMEN", "PELVIS",
    "L_ARM", "R_ARM", "L_LEG", "R_LEG", "BACK",
]


def _serialize_marker(m) -> dict:
    return {
        "id": str(getattr(m, "id", "")),
        "case_id": str(getattr(m, "case_id", "")),
        "body_part_code": getattr(m, "body_part_code", None),
        "injury_type_code": getattr(m, "injury_type_code", None),
    }


@router.get("")
async def list_body_markers(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
    case_id: str | None = Query(None),
    offset: int = 0,
    limit: int = 100,
):
    """List body markers — from CaseInjury when case_id given, else reference list."""
    if case_id:
        repo = BaseRepository(CaseInjury, session)
        items = await repo.get_all(
            filters=[CaseInjury.case_id == case_id],
            offset=offset,
            limit=limit,
        )
        return envelope([_serialize_marker(i) for i in items], request_id=request_id)
    return envelope([{"code": c, "label": c} for c in BODY_PARTS], request_id=request_id)
