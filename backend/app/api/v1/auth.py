"""Auth router — JWT login, refresh, register, logout."""
import logging
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, field_validator, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, invalidate_user_cache
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.config import REFRESH_TOKEN_EXPIRE_DAYS
from app.core.utils import envelope
from app.core.database import get_session
from app.models.user import User
from app.models.revoked_token import RevokedToken

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["auth"])

_PASSWORD_RE = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d).{8,72}$')


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError(
                'Password must be 8–72 characters and contain at least one letter and one digit'
            )
        return v


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register")
@limiter.limit("3/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    result = await session.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=body.email,
        hashed_password=hash_password(body.password),
        role="medic",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    tv = user.token_version or 0
    access = create_access_token({"sub": user.id, "tv": tv})
    refresh, _jti = create_refresh_token({"sub": user.id, "tv": tv})
    return envelope({
        "access_token": access,
        "refresh_token": refresh,
        "user": {"id": user.id, "email": user.email, "role": user.role},
    }, request_id=request_id)


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    tv = user.token_version or 0
    access = create_access_token({"sub": user.id, "tv": tv})
    refresh, _jti = create_refresh_token({"sub": user.id, "tv": tv})
    return envelope({
        "access_token": access,
        "refresh_token": refresh,
        "user": {"id": user.id, "email": user.email, "role": user.role},
    }, request_id=request_id)


@router.post("/refresh")
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    body: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    jti = payload.get("jti")
    if jti:
        result = await session.execute(select(RevokedToken).where(RevokedToken.jti == jti))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    # Token rotation: revoke the consumed refresh token, issue a fresh one
    if jti:
        exp = payload.get("exp")
        expires_at = (
            datetime.fromtimestamp(exp, tz=timezone.utc)
            if exp
            else datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        session.add(RevokedToken(jti=jti, expires_at=expires_at))
    # Look up current token_version to embed in new tokens
    result = await session.execute(select(User).where(User.id == user_id))
    user_obj = result.scalar_one_or_none()
    if not user_obj or not user_obj.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    tv = user_obj.token_version or 0
    access = create_access_token({"sub": user_id, "tv": tv})
    new_refresh, _new_jti = create_refresh_token({"sub": user_id, "tv": tv})
    await session.commit()
    return envelope({"access_token": access, "refresh_token": new_refresh}, request_id=request_id)


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/logout")
async def logout(
    body: LogoutRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    payload = decode_token(body.refresh_token)
    if payload and payload.get("type") == "refresh":
        jti = payload.get("jti")
        if jti:
            exp = payload.get("exp")
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            session.add(RevokedToken(jti=jti, expires_at=expires_at))
            await session.commit()
    return envelope({"message": "Logged out"}, request_id=request_id)


@router.post("/logout-all")
@limiter.limit("5/minute")
async def logout_all(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Bump token_version for the user, invalidating ALL existing refresh tokens."""
    user_obj = await session.get(User, user["sub"])
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user_obj.token_version = (user_obj.token_version or 0) + 1
    await session.commit()
    # Clear cache so `get_current_user` re-reads token_version immediately
    invalidate_user_cache(user["sub"])
    return envelope({"message": "All sessions revoked"}, request_id=request_id)


@router.get("/me")
async def get_me(
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    return envelope(user, request_id=request_id)
