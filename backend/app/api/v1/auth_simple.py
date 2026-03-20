"""Simple auth without tokens for development."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_session
from app.core.utils import envelope

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def simple_login(
    email: str,
    password: str,
    session: AsyncSession = Depends(get_session)
):
    """Simple login without tokens for development."""
    
    # For development, accept any email/password
    if "@" in email and password:
        user_data = {
            "id": "dev-user",
            "email": email,
            "role": "admin" if "admin" in email else "medic"
        }
        
        return envelope({
            "user": user_data,
            "message": "Login successful"
        })
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/me")
async def get_current_user():
    """Get current user info (development mode)."""
    
    return envelope({
        "id": "dev-user",
        "email": "dev@test.com",
        "role": "admin"
    })
