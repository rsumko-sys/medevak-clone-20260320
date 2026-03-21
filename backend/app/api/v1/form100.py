"""Form 100 router."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_request_id, get_session, require_permission
from app.core.security import Permission, SecurityContext
from app.core.utils import envelope
from app.models.cases import Case
from app.models.form100 import Form100Record
from app.schemas.unified import Form100Create, Form100Response, Form100Update


router = APIRouter(prefix="/cases", tags=["form100"])


@router.post("/{case_id}/form100", response_model=dict)
async def create_form100(
    case_id: Annotated[str, Path(...)],
    body: Form100Create,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.CREATE_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    existing = (
        await session.execute(
            select(Form100Record)
            .where(Form100Record.case_id == case_id, Form100Record.voided == False)
            .order_by(Form100Record.created_at.desc())
            .limit(1)
        )
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail="Form 100 already exists for this case")

    form = Form100Record(
        id=str(uuid.uuid4()),
        case_id=case_id,
        **body.model_dump(),
    )
    session.add(form)
    await session.commit()
    await session.refresh(form)

    return envelope(Form100Response.model_validate(form).model_dump(mode="json"), request_id=request_id)


@router.get("/{case_id}/form100", response_model=dict)
async def get_form100(
    case_id: Annotated[str, Path(...)],
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    form = (
        await session.execute(
            select(Form100Record)
            .where(Form100Record.case_id == case_id, Form100Record.voided == False)
            .order_by(Form100Record.created_at.desc())
            .limit(1)
        )
    ).scalars().first()
    if not form:
        raise HTTPException(status_code=404, detail="Form 100 not found")

    return envelope(Form100Response.model_validate(form).model_dump(mode="json"), request_id=request_id)


@router.patch("/{case_id}/form100", response_model=dict)
async def update_form100(
    case_id: Annotated[str, Path(...)],
    body: Form100Update,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.UPDATE_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    form = (
        await session.execute(
            select(Form100Record)
            .where(Form100Record.case_id == case_id, Form100Record.voided == False)
            .order_by(Form100Record.created_at.desc())
            .limit(1)
        )
    ).scalars().first()
    if not form:
        raise HTTPException(status_code=404, detail="Form 100 not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(form, field, value)

    await session.commit()
    await session.refresh(form)
    return envelope(Form100Response.model_validate(form).model_dump(mode="json"), request_id=request_id)
