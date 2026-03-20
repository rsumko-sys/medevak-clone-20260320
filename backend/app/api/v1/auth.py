"""Auth router — JWT login, refresh, register."""
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.utils import envelope
from app.core.database import get_session
from app.models.user import User

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register")
async def register(
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
    access = create_access_token({"sub": user.id})
    refresh = create_refresh_token({"sub": user.id})
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
    access = create_access_token({"sub": user.id})
    refresh = create_refresh_token({"sub": user.id})
    return envelope({
        "access_token": access,
        "refresh_token": refresh,
        "user": {"id": user.id, "email": user.email, "role": user.role},
    }, request_id=request_id)


@router.post("/refresh")
async def refresh(
    body: RefreshRequest,
    request_id: Annotated[str, Depends(get_request_id)],
):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    access = create_access_token({"sub": user_id})
    return envelope({"access_token": access}, request_id=request_id)


@router.get("/me")
async def get_me(
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    return envelope(user, request_id=request_id)
