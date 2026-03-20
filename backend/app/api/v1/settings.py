"""Application settings endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_request_id
from app.core.config import ALLOW_GPS, PRIVATE_NETWORK_ONLY
from app.core.utils import envelope


router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/security-policy")
async def get_security_policy(
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Return active runtime security policy flags."""
    return envelope(
        {
            "private_network_only": PRIVATE_NETWORK_ONLY,
            "allow_gps": ALLOW_GPS,
            "network_mode": "private_only" if PRIVATE_NETWORK_ONLY else "open",
            "gps_mode": "enabled" if ALLOW_GPS else "disabled",
        },
        request_id=request_id,
    )
