"""Reference data router — triage, blood codes, etc."""
from typing import Annotated
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_request_id
from app.core.utils import envelope

router = APIRouter(prefix="/reference", tags=["reference"])

TRIAGE_CODES = ["RED", "YELLOW", "GREEN", "BLACK", "EXPECTANT"]
BLOOD_CODES = [
    "BLOOD", "PRBC", "FFP", "PLT", "PLATELETS", "CRYO",
    "WHOLE_BLOOD", "PACKED_RBC", "FRESH_FROZEN_PLASMA", "CRYOPRECIPITATE",
]


@router.get("")
async def get_reference(
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Reference dictionaries: triage codes, blood product codes."""
    return envelope({
        "triage_codes": TRIAGE_CODES,
        "blood_codes": BLOOD_CODES,
    }, request_id=request_id)
