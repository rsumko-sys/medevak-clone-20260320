"""Blood inventory router."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session, require_role
from app.core.audit_helper import log_audit
from app.core.sync_helper import enqueue_sync
from app.core.utils import envelope
from app.models.blood import BloodInventory, BloodTransaction
from app.models.cases import Case
from app.services.events import log_event
from app.schemas.blood import (
    BLOOD_TYPES,
    BloodInventoryAdjustRequest,
    BloodInventoryResponse,
    normalize_blood_type,
)

router = APIRouter(prefix="/blood", tags=["blood"])


@router.get("", response_model=dict)
async def get_blood_inventory(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    user_unit = user.get("unit", "")
    result = await session.execute(
        select(BloodInventory).where(BloodInventory.unit == user_unit)
    )
    rows = result.scalars().all()
    by_type = {row.blood_type: row for row in rows}
    payload = [
        BloodInventoryResponse.model_validate(by_type[blood_type]).model_dump(mode="json")
        if blood_type in by_type
        else BloodInventoryResponse(blood_type=blood_type, quantity=0).model_dump(mode="json")
        for blood_type in BLOOD_TYPES
    ]
    return envelope(payload, request_id=request_id)


@router.patch("/{blood_type}", response_model=dict)
async def adjust_blood_inventory(
    blood_type: Annotated[str, Path(...)],
    body: BloodInventoryAdjustRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(require_role("admin", "medic"))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    normalized_type = normalize_blood_type(blood_type)
    user_unit = user.get("unit", "")

    if body.case_id:
        case = await session.get(Case, body.case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        if case.unit != user_unit:
            raise HTTPException(status_code=403, detail="Unauthorized: Case is in different unit")

    result = await session.execute(
        select(BloodInventory)
        .where(
            BloodInventory.unit == user_unit,
            BloodInventory.blood_type == normalized_type,
        )
        .with_for_update()
    )
    inventory = result.scalar_one_or_none()

    if inventory is None:
        inventory = BloodInventory(
            id=str(uuid.uuid4()),
            unit=user_unit,
            blood_type=normalized_type,
            quantity=0,
        )
        session.add(inventory)
        await session.flush()

    new_quantity = inventory.quantity + body.delta
    if new_quantity < 0:
        raise HTTPException(status_code=409, detail="Insufficient blood inventory")

    old_quantity = inventory.quantity
    inventory.quantity = new_quantity

    tx = BloodTransaction(
        id=str(uuid.uuid4()),
        unit=user_unit,
        blood_type=normalized_type,
        delta=body.delta,
        reason=body.reason,
        case_id=body.case_id,
        created_by=user.get("sub"),
    )
    session.add(tx)

    await log_audit(
        session,
        "blood_inventory",
        inventory.id,
        "adjust",
        user.get("sub"),
        old_values={"quantity": old_quantity},
        new_values={
            "blood_type": normalized_type,
            "quantity": new_quantity,
            "delta": body.delta,
            "reason": body.reason,
            "case_id": body.case_id,
            "unit": user_unit,
        },
        device_id=user.get("device_id"),
    )
    await enqueue_sync(
        session,
        "blood_inventory",
        inventory.id,
        "update",
        {
            "blood_type": normalized_type,
            "quantity": new_quantity,
            "delta": body.delta,
            "reason": body.reason,
            "case_id": body.case_id,
            "unit": user_unit,
        },
        user.get("device_id"),
    )

    # ── Case timeline event when blood is linked to a case ────────────────
    if body.case_id:
        await log_event(
            session,
            type="BLOOD_USED" if body.delta < 0 else "BLOOD_RESTOCKED",
            entity_type="blood",
            entity_id=inventory.id,
            payload={
                "delta": body.delta,
                "blood_type": normalized_type,
                "reason": body.reason,
                "quantity_after": new_quantity,
                "case_id": body.case_id,
            },
            user=user,
        )

    await session.commit()
    await session.refresh(inventory)
    return envelope(
        BloodInventoryResponse.model_validate(inventory).model_dump(mode="json"),
        request_id=request_id,
    )