"""Field-drop logistics router."""
import math
import uuid
from collections import defaultdict
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_request_id, get_session, require_permission
from app.core.idempotency import get_idempotent_response, payload_fingerprint, save_idempotent_response
from app.core.security import Permission, SecurityContext
from app.core.utils import envelope
from app.models.field_drop import (
    FieldDispatchLog,
    FieldInventoryItem,
    FieldPosition,
    FieldSupplyNeed,
    FieldSupplyRequest,
)
from app.schemas.field_drop import (
    FieldCommitResponse,
    FieldNeedCreate,
    FieldPositionCreate,
    FieldPositionResponse,
    FieldRecommendationResponse,
    FieldRecommendationRow,
    FieldRequestCreate,
    FieldRequestResponse,
    InventorySnapshot,
)


router = APIRouter(prefix="/field-drop", tags=["field-drop"])
TRACKED_ITEMS = ("hemostatic", "bandage", "tourniquet")


class InventoryUpdateBody(BaseModel):
    item_name: str
    qty: int = Field(ge=0)


def _normalize_item_name(item_name: str) -> str:
    return item_name.strip().lower()


def _distance_km(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _eta_minutes(distance_km: Optional[float]) -> Optional[int]:
    if distance_km is None:
        return None
    return max(2, round(distance_km * 1.6 + 2))


def _build_snapshot(items: list[FieldInventoryItem]) -> InventorySnapshot:
    base = {"hemostatic": 0, "bandage": 0, "tourniquet": 0}
    meds: dict[str, int] = {}

    for item in items:
        name = _normalize_item_name(item.item_name)
        qty = max(0, int(item.qty or 0))
        if name in base:
            base[name] = qty
        else:
            meds[name] = qty

    return InventorySnapshot(
        hemostatic=base["hemostatic"],
        bandage=base["bandage"],
        tourniquet=base["tourniquet"],
        meds=meds,
    )


async def _get_request_with_needs(
    session: AsyncSession,
    request_id: str,
) -> tuple[FieldSupplyRequest, list[FieldSupplyNeed]]:
    req = await session.get(FieldSupplyRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Field supply request not found")

    need_stmt = select(FieldSupplyNeed).where(FieldSupplyNeed.request_id == request_id)
    needs = (await session.execute(need_stmt)).scalars().all()
    return req, needs


async def _compute_recommendation(
    session: AsyncSession,
    request_obj: FieldSupplyRequest,
    needs: list[FieldSupplyNeed],
) -> FieldRecommendationResponse:
    positions = (await session.execute(select(FieldPosition))).scalars().all()
    inv_items = (await session.execute(select(FieldInventoryItem))).scalars().all()

    inv_by_position_item: dict[tuple[str, str], int] = defaultdict(int)
    for inv in inv_items:
        key = (inv.position_id, _normalize_item_name(inv.item_name))
        inv_by_position_item[key] += max(0, int(inv.qty or 0))

    nearby_positions: list[tuple[FieldPosition, float]] = []
    for position in positions:
        dist = _distance_km(position.x, position.y, request_obj.x, request_obj.y)
        if dist <= float(request_obj.radius_km):
            nearby_positions.append((position, dist))

    actions: list[FieldRecommendationRow] = []

    for need in needs:
        item_name = _normalize_item_name(need.item_name)
        remaining = int(need.qty)
        ranked: list[tuple[float, float, FieldPosition, int]] = []

        for position, distance in nearby_positions:
            available_qty = inv_by_position_item.get((position.id, item_name), 0)
            score = (1.5 * available_qty) - (1.0 * distance)
            ranked.append((score, distance, position, available_qty))

        ranked.sort(key=lambda row: (row[0], -row[1]), reverse=True)

        for score, distance, position, available_qty in ranked:
            if remaining <= 0:
                break
            if available_qty <= 0:
                continue

            take_qty = min(remaining, available_qty)
            remaining -= take_qty
            inv_by_position_item[(position.id, item_name)] = available_qty - take_qty

            actions.append(
                FieldRecommendationRow(
                    position_id=position.id,
                    position=position.name,
                    item_name=item_name,
                    qty=take_qty,
                    distance_km=round(distance, 3),
                    score=round(score, 3),
                    eta_min=_eta_minutes(distance),
                    status="RECOMMENDED",
                )
            )

        if remaining > 0:
            actions.append(
                FieldRecommendationRow(
                    item_name=item_name,
                    qty=remaining,
                    status="NOT_ENOUGH",
                )
            )

    eta_values = [row.eta_min for row in actions if row.eta_min is not None]
    return FieldRecommendationResponse(
        request_id=request_obj.id,
        urgency=request_obj.urgency,
        eta_min=min(eta_values) if eta_values else None,
        eta_max=max(eta_values) if eta_values else None,
        actions=actions,
    )


@router.get("/positions", response_model=dict)
async def list_positions(
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    _ = ctx
    positions = (await session.execute(select(FieldPosition).order_by(FieldPosition.updated_at.desc()))).scalars().all()
    all_items = (await session.execute(select(FieldInventoryItem))).scalars().all()

    items_by_position: dict[str, list[FieldInventoryItem]] = defaultdict(list)
    for item in all_items:
        items_by_position[item.position_id].append(item)

    data = [
        FieldPositionResponse(
            id=position.id,
            name=position.name,
            x=position.x,
            y=position.y,
            updated_at=position.updated_at,
            inventory=_build_snapshot(items_by_position.get(position.id, [])),
        ).model_dump(mode="json")
        for position in positions
    ]
    return envelope(data, request_id=request_id)


@router.post("/positions", response_model=dict)
async def create_position(
    body: FieldPositionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.UPDATE_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
):
    path = "/field-drop/positions"
    payload = body.model_dump(mode="json")
    payload_hash = payload_fingerprint(payload)

    if idempotency_key:
        existing = await get_idempotent_response(
            session,
            idempotency_key,
            ctx.user_id,
            request_path=path,
            payload_hash=payload_hash,
        )
        if existing:
            if existing.get("conflict"):
                raise HTTPException(status_code=409, detail="Idempotency key re-used with different payload")
            return envelope(existing["body"], request_id=request_id)

    existing_name = await session.execute(select(FieldPosition).where(FieldPosition.name == body.name.strip()))
    if existing_name.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Position name already exists")

    position = FieldPosition(
        id=str(uuid.uuid4()),
        name=body.name.strip(),
        x=body.x,
        y=body.y,
    )
    session.add(position)

    item_values: dict[str, int] = {
        "hemostatic": body.inventory.hemostatic,
        "bandage": body.inventory.bandage,
        "tourniquet": body.inventory.tourniquet,
    }
    for med_name, med_qty in body.inventory.meds.items():
        normalized_name = _normalize_item_name(med_name)
        item_values[normalized_name] = max(0, int(med_qty))

    for tracked_name in TRACKED_ITEMS:
        item_values.setdefault(tracked_name, 0)

    for item_name, qty in item_values.items():
        session.add(
            FieldInventoryItem(
                id=str(uuid.uuid4()),
                position_id=position.id,
                item_name=_normalize_item_name(item_name),
                qty=max(0, int(qty)),
            )
        )

    await session.commit()
    await session.refresh(position)

    response_data = FieldPositionResponse(
        id=position.id,
        name=position.name,
        x=position.x,
        y=position.y,
        updated_at=position.updated_at,
        inventory=InventorySnapshot(
            hemostatic=max(0, int(item_values.get("hemostatic", 0))),
            bandage=max(0, int(item_values.get("bandage", 0))),
            tourniquet=max(0, int(item_values.get("tourniquet", 0))),
            meds={
                key: value
                for key, value in item_values.items()
                if key not in TRACKED_ITEMS
            },
        ),
    ).model_dump(mode="json")

    if idempotency_key:
        await save_idempotent_response(
            session,
            idempotency_key,
            ctx.user_id,
            path,
            200,
            response_data,
            payload_hash=payload_hash,
        )

    return envelope(response_data, request_id=request_id)


@router.patch("/positions/{position_id}/inventory", response_model=dict)
async def update_position_inventory(
    position_id: str,
    body: InventoryUpdateBody,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.UPDATE_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    _ = ctx
    position = await session.get(FieldPosition, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    item_name = _normalize_item_name(body.item_name)
    if not item_name:
        raise HTTPException(status_code=400, detail="item_name is required")

    item_stmt = select(FieldInventoryItem).where(
        FieldInventoryItem.position_id == position_id,
        FieldInventoryItem.item_name == item_name,
    )
    item = (await session.execute(item_stmt)).scalar_one_or_none()
    if item is None:
        item = FieldInventoryItem(
            id=str(uuid.uuid4()),
            position_id=position_id,
            item_name=item_name,
            qty=body.qty,
        )
        session.add(item)
    else:
        item.qty = body.qty

    await session.commit()
    return envelope(
        {
            "position_id": position_id,
            "item_name": item_name,
            "qty": body.qty,
        },
        request_id=request_id,
    )


@router.get("/requests", response_model=dict)
async def list_requests(
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    _ = ctx
    reqs = (
        await session.execute(select(FieldSupplyRequest).order_by(FieldSupplyRequest.created_at.desc()))
    ).scalars().all()

    req_ids = [row.id for row in reqs]
    needs: list[FieldSupplyNeed] = []
    if req_ids:
        needs = (
            await session.execute(select(FieldSupplyNeed).where(FieldSupplyNeed.request_id.in_(req_ids)))
        ).scalars().all()

    needs_by_request: dict[str, list[FieldNeedCreate]] = defaultdict(list)
    for need in needs:
        needs_by_request[need.request_id].append(
            FieldNeedCreate(item_name=_normalize_item_name(need.item_name), qty=need.qty)
        )

    data = [
        FieldRequestResponse(
            id=req.id,
            x=req.x,
            y=req.y,
            urgency=req.urgency,
            radius_km=req.radius_km,
            status=req.status,
            created_at=req.created_at,
            required=needs_by_request.get(req.id, []),
        ).model_dump(mode="json")
        for req in reqs
    ]
    return envelope(data, request_id=request_id)


@router.post("/requests", response_model=dict)
async def create_request(
    body: FieldRequestCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.CREATE_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
):
    path = "/field-drop/requests"
    payload = body.model_dump(mode="json")
    payload_hash = payload_fingerprint(payload)

    if idempotency_key:
        existing = await get_idempotent_response(
            session,
            idempotency_key,
            ctx.user_id,
            request_path=path,
            payload_hash=payload_hash,
        )
        if existing:
            if existing.get("conflict"):
                raise HTTPException(status_code=409, detail="Idempotency key re-used with different payload")
            return envelope(existing["body"], request_id=request_id)

    req = FieldSupplyRequest(
        id=str(uuid.uuid4()),
        x=body.x,
        y=body.y,
        urgency=body.urgency,
        radius_km=body.radius_km,
        status="ACTIVE",
        created_by=ctx.user_id,
    )
    session.add(req)

    norm_required: list[FieldNeedCreate] = []
    for needed in body.required:
        normalized_name = _normalize_item_name(needed.item_name)
        norm_required.append(FieldNeedCreate(item_name=normalized_name, qty=needed.qty))
        session.add(
            FieldSupplyNeed(
                id=str(uuid.uuid4()),
                request_id=req.id,
                item_name=normalized_name,
                qty=needed.qty,
            )
        )

    await session.commit()
    await session.refresh(req)

    response_data = FieldRequestResponse(
        id=req.id,
        x=req.x,
        y=req.y,
        urgency=req.urgency,
        radius_km=req.radius_km,
        status=req.status,
        created_at=req.created_at,
        required=norm_required,
    ).model_dump(mode="json")

    if idempotency_key:
        await save_idempotent_response(
            session,
            idempotency_key,
            ctx.user_id,
            path,
            200,
            response_data,
            payload_hash=payload_hash,
        )

    return envelope(response_data, request_id=request_id)


@router.get("/requests/{request_id}/recommendation", response_model=dict)
async def get_request_recommendation(
    request_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_MEDICAL))],
    req_trace_id: Annotated[str, Depends(get_request_id)],
):
    _ = ctx
    req_obj, needs = await _get_request_with_needs(session, request_id)
    response = await _compute_recommendation(session, req_obj, needs)
    return envelope(response.model_dump(mode="json"), request_id=req_trace_id)


@router.post("/requests/{request_id}/commit", response_model=dict)
async def commit_request_recommendation(
    request_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.UPDATE_MEDICAL))],
    req_trace_id: Annotated[str, Depends(get_request_id)],
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
):
    path = f"/field-drop/requests/{request_id}/commit"
    payload_hash = payload_fingerprint({"request_id": request_id})

    if idempotency_key:
        existing = await get_idempotent_response(
            session,
            idempotency_key,
            ctx.user_id,
            request_path=path,
            payload_hash=payload_hash,
        )
        if existing:
            if existing.get("conflict"):
                raise HTTPException(status_code=409, detail="Idempotency key re-used with different payload")
            return envelope(existing["body"], request_id=req_trace_id)

    req_obj, needs = await _get_request_with_needs(session, request_id)
    recommendation = await _compute_recommendation(session, req_obj, needs)

    applied_rows: list[FieldRecommendationRow] = []
    messages: list[str] = []

    for row in recommendation.actions:
        if row.status == "RECOMMENDED" and row.position_id and row.qty > 0:
            item_name = _normalize_item_name(row.item_name)
            item_stmt = select(FieldInventoryItem).where(
                FieldInventoryItem.position_id == row.position_id,
                FieldInventoryItem.item_name == item_name,
            )
            inv_item = (await session.execute(item_stmt)).scalar_one_or_none()
            if inv_item is None:
                inv_item = FieldInventoryItem(
                    id=str(uuid.uuid4()),
                    position_id=row.position_id,
                    item_name=item_name,
                    qty=0,
                )
                session.add(inv_item)

            inv_item.qty = max(0, int(inv_item.qty or 0) - int(row.qty))
            applied_rows.append(row)
            messages.append(
                f"{row.position or 'UNKNOWN'}: send {row.qty} {item_name} to grid X:{req_obj.x:.1f} Y:{req_obj.y:.1f}"
            )

        session.add(
            FieldDispatchLog(
                id=str(uuid.uuid4()),
                request_id=req_obj.id,
                position_id=row.position_id,
                position_name=row.position,
                item_name=_normalize_item_name(row.item_name),
                qty=row.qty,
                distance_km=row.distance_km,
                eta_min=row.eta_min,
                status=row.status,
            )
        )

    req_obj.status = "DISPATCHED"
    await session.commit()

    response_data = FieldCommitResponse(
        ok=True,
        applied=applied_rows,
        messages=messages,
    ).model_dump(mode="json")

    if idempotency_key:
        await save_idempotent_response(
            session,
            idempotency_key,
            ctx.user_id,
            path,
            200,
            response_data,
            payload_hash=payload_hash,
        )

    return envelope(response_data, request_id=req_trace_id)


@router.get("/logs", response_model=dict)
async def list_logs(
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
    limit: int = 50,
):
    _ = ctx
    safe_limit = min(max(limit, 1), 500)
    logs = (
        await session.execute(
            select(FieldDispatchLog).order_by(FieldDispatchLog.created_at.desc()).limit(safe_limit)
        )
    ).scalars().all()

    data = [
        {
            "id": log.id,
            "request_id": log.request_id,
            "position_id": log.position_id,
            "position_name": log.position_name,
            "item_name": log.item_name,
            "qty": log.qty,
            "distance_km": log.distance_km,
            "eta_min": log.eta_min,
            "status": log.status,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
    return envelope(data, request_id=request_id)
