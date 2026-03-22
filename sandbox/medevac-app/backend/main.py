import hashlib
import json
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import anyio
from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from db import Base, SessionLocal, engine
from models import Case, CaseNeed, IdempotencyRecord, InventoryItem, Position
from schemas import CaseCreate, PositionCreate, PositionOut

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Medevac API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_DISTANCE = 5.0

TOKENS = {
    "dev-admin-token": {"sub": "dev-admin", "role": "admin", "unit": "HQ"},
    "dev-dispatcher-token": {"sub": "dev-dispatcher", "role": "dispatcher", "unit": "HQ"},
    "dev-medic-token": {"sub": "dev-medic", "role": "medic", "unit": "FIELD"},
}

ROLE_PERMISSIONS = {
    "medic": {"view_data", "create_case"},
    "dispatcher": {"view_data", "create_case", "commit_dispatch", "manage_inventory"},
    "commander": {"view_data", "commit_dispatch"},
    "admin": {"view_data", "create_case", "commit_dispatch", "manage_inventory", "manage_users"},
}


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast(self, event: Dict[str, Any]) -> None:
        stale: List[WebSocket] = []
        for ws in self.active_connections:
            try:
                await ws.send_json(event)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)


manager = ConnectionManager()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def calc_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    user = TOKENS.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def require_permission(permission: str):
    def checker(user: Dict[str, str] = Depends(get_current_user)) -> Dict[str, str]:
        role = user.get("role")
        if permission not in ROLE_PERMISSIONS.get(role, set()):
            raise HTTPException(status_code=403, detail=f"Forbidden: missing permission {permission}")
        return user

    return checker


def _payload_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_idempotent(
    db: Session,
    *,
    key: Optional[str],
    scope: str,
    payload: Dict[str, Any],
    callback,
):
    if not key:
        return callback()

    p_hash = _payload_hash(payload)
    existing = (
        db.query(IdempotencyRecord)
        .filter(IdempotencyRecord.key == key, IdempotencyRecord.scope == scope)
        .first()
    )
    if existing:
        if existing.payload_hash != p_hash:
            raise HTTPException(status_code=409, detail="Idempotency key re-used with different payload")
        return json.loads(existing.response_json)

    result = callback()
    record = IdempotencyRecord(
        key=key,
        scope=scope,
        payload_hash=p_hash,
        response_json=json.dumps(result),
    )
    db.add(record)
    db.commit()
    return result


def emit_event(event_type: str, data: Dict[str, Any]) -> None:
    try:
        anyio.from_thread.run(manager.broadcast, {"type": event_type, "data": data})
    except RuntimeError:
        pass


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/auth/me")
def auth_me(user: Dict[str, str] = Depends(get_current_user)):
    return {"ok": True, "user": user}


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/positions", response_model=PositionOut)
def create_position(
    payload: PositionCreate,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    _user: Dict[str, str] = Depends(require_permission("manage_inventory")),
):
    def _create():
        existing = db.query(Position).filter(Position.name == payload.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Position already exists")

        position = Position(name=payload.name, x=payload.x, y=payload.y, updated_at=datetime.utcnow())
        db.add(position)
        db.flush()

        for item in payload.items:
            db.add(InventoryItem(position_id=position.id, item_name=item.item_name, qty=item.qty))

        db.commit()
        saved = (
            db.query(Position)
            .options(joinedload(Position.items))
            .filter(Position.id == position.id)
            .first()
        )
        response = {
            "id": saved.id,
            "name": saved.name,
            "x": saved.x,
            "y": saved.y,
            "items": [{"item_name": i.item_name, "qty": i.qty, "id": i.id} for i in saved.items],
        }
        emit_event("inventory_updated", {"position_id": saved.id, "position": saved.name})
        return response

    return run_idempotent(
        db,
        key=idempotency_key,
        scope="create_position",
        payload=payload.model_dump(mode="json"),
        callback=_create,
    )


@app.get("/positions")
def get_positions(
    db: Session = Depends(get_db),
    _user: Dict[str, str] = Depends(require_permission("view_data")),
):
    positions = db.query(Position).options(joinedload(Position.items)).all()
    result = []
    for p in positions:
        result.append(
            {
                "id": p.id,
                "name": p.name,
                "x": p.x,
                "y": p.y,
                "updated_at": p.updated_at.isoformat(),
                "items": [{"id": i.id, "item_name": i.item_name, "qty": i.qty} for i in p.items],
            }
        )
    return result


@app.put("/positions/{position_id}/items/{item_id}")
def update_inventory(
    position_id: int,
    item_id: int,
    qty: int,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    _user: Dict[str, str] = Depends(require_permission("manage_inventory")),
):
    def _update():
        item = (
            db.query(InventoryItem)
            .filter(InventoryItem.id == item_id, InventoryItem.position_id == position_id)
            .first()
        )

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        item.qty = max(0, qty)
        item.position.updated_at = datetime.utcnow()
        db.commit()

        response = {"ok": True, "item_id": item.id, "qty": item.qty}
        emit_event("inventory_updated", {"position_id": position_id, "item_id": item_id, "qty": item.qty})
        return response

    return run_idempotent(
        db,
        key=idempotency_key,
        scope="update_inventory",
        payload={"position_id": position_id, "item_id": item_id, "qty": qty},
        callback=_update,
    )


@app.post("/cases")
def create_case(
    payload: CaseCreate,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    _user: Dict[str, str] = Depends(require_permission("create_case")),
):
    def _create():
        case = Case(x=payload.x, y=payload.y, status="active")
        db.add(case)
        db.flush()

        for need in payload.needs:
            db.add(CaseNeed(case_id=case.id, item_name=need.item_name, qty=need.qty))

        db.commit()
        response = {"ok": True, "case_id": case.id}
        emit_event("case_updated", {"case_id": case.id, "status": "active"})
        return response

    return run_idempotent(
        db,
        key=idempotency_key,
        scope="create_case",
        payload=payload.model_dump(mode="json"),
        callback=_create,
    )


@app.get("/cases")
def get_cases(
    db: Session = Depends(get_db),
    _user: Dict[str, str] = Depends(require_permission("view_data")),
):
    cases = db.query(Case).options(joinedload(Case.needs)).all()
    result = []
    for c in cases:
        result.append(
            {
                "id": c.id,
                "x": c.x,
                "y": c.y,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
                "needs": [{"item_name": n.item_name, "qty": n.qty} for n in c.needs],
            }
        )
    return result


@app.get("/cases/{case_id}/recommendation")
def get_recommendation(
    case_id: int,
    db: Session = Depends(get_db),
    _user: Dict[str, str] = Depends(require_permission("view_data")),
):
    case = db.query(Case).options(joinedload(Case.needs)).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    positions = db.query(Position).options(joinedload(Position.items)).all()

    nearby = []
    for p in positions:
        dist = calc_distance(case.x, case.y, p.x, p.y)
        if dist <= MAX_DISTANCE:
            nearby.append((p, dist))

    plan = []

    for need in case.needs:
        remaining = need.qty

        sorted_positions = sorted(
            nearby,
            key=lambda row: next((item.qty for item in row[0].items if item.item_name == need.item_name), 0),
            reverse=True,
        )

        for p, dist in sorted_positions:
            item = next((i for i in p.items if i.item_name == need.item_name and i.qty > 0), None)
            if not item or remaining <= 0:
                continue

            send_qty = min(item.qty, remaining)
            plan.append(
                {
                    "position_id": p.id,
                    "position": p.name,
                    "item_name": need.item_name,
                    "qty": send_qty,
                    "distance": round(dist, 2),
                }
            )
            remaining -= send_qty

        if remaining > 0:
            plan.append(
                {
                    "position_id": None,
                    "position": "NONE",
                    "item_name": need.item_name,
                    "qty": remaining,
                    "distance": None,
                    "status": "NOT_ENOUGH",
                }
            )

    return {"case_id": case.id, "plan": plan}


@app.post("/cases/{case_id}/commit")
def commit_recommendation(
    case_id: int,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    _user: Dict[str, str] = Depends(require_permission("commit_dispatch")),
):
    def _commit():
        recommendation = get_recommendation(case_id, db, _user)
        applied = []

        for row in recommendation["plan"]:
            if row["position_id"] is None:
                continue

            item = (
                db.query(InventoryItem)
                .filter(
                    InventoryItem.position_id == row["position_id"],
                    InventoryItem.item_name == row["item_name"],
                )
                .first()
            )

            if not item:
                continue

            item.qty = max(0, item.qty - row["qty"])
            position = db.query(Position).filter(Position.id == row["position_id"]).first()
            position.updated_at = datetime.utcnow()

            applied.append(
                {"position": row["position"], "item_name": row["item_name"], "qty": row["qty"]}
            )

        db.commit()
        response = {"ok": True, "applied": applied}
        emit_event("case_updated", {"case_id": case_id, "status": "committed"})
        emit_event("inventory_updated", {"case_id": case_id, "applied": applied})
        return response

    return run_idempotent(
        db,
        key=idempotency_key,
        scope="commit_recommendation",
        payload={"case_id": case_id},
        callback=_commit,
    )
