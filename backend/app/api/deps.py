import logging
import uuid
import time
from typing import Annotated, Dict, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import decode_token
from app.core.config import DEV_AUTH_BYPASS
from app.core.database import get_session
from app.models.user import User
from app.core.security import Permission, SecurityContext

logger = logging.getLogger(__name__)

# Simple in-memory cache for user data to reduce DB load
# Short TTL so role changes and deactivation propagate quickly
_USER_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL = 5  # seconds — fast propagation of role/deactivation changes

def invalidate_user_cache(user_id: str) -> None:
    """Call this on password change, role update, or forced logout."""
    _USER_CACHE.pop(user_id, None)

http_bearer = HTTPBearer(auto_error=False)

async def get_request_id(request: Request) -> str:
    """Отримати або згенерувати Request ID."""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    return request_id

async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)] = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if DEV_AUTH_BYPASS and (not creds or not creds.credentials):
        return {"sub": "dev-user", "device_id": "dev-1", "role": "admin", "unit": "HQ"}

    raw = creds.credentials if creds else None
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(raw)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Check cache first
    now = time.time()
    if user_id in _USER_CACHE:
        cached = _USER_CACHE[user_id]
        if cached["expires_at"] > now:
            return cached["data"]

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated")

    # Enforce logout-all: reject tokens issued before the current token_version
    token_tv = payload.get("tv", 0)
    if token_tv < (user.token_version or 0):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session revoked — please log in again",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_data = {
        "sub": user.id,
        "email": user.email,
        "device_id": user.device_id,  # None if not bound — no fake fallback
        "role": user.role or "viewer",
        "unit": user.unit or ""
    }
    
    # Update cache
    _USER_CACHE[user_id] = {
        "data": user_data,
        "expires_at": now + _CACHE_TTL
    }

    return user_data

async def get_security_context(
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> SecurityContext:
    return SecurityContext(user, request_id=request_id)

def require_permission(permission: Permission):
    """Require a specific permission; returns the user dict (not SecurityContext)."""
    async def _check(
        user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        from app.core.security import ROLE_PERMISSIONS, UserRole
        try:
            role = UserRole(user.get("role", "viewer"))
        except ValueError:
            role = UserRole.VIEWER
        if permission not in ROLE_PERMISSIONS.get(role, []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}",
            )
        return user
    return _check

def require_role(*roles: str):
    async def _check(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user
    return _check


def get_client_ip(request: Request) -> str:
    """Extract real client IP, honouring X-Forwarded-For set by trusted proxies."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
