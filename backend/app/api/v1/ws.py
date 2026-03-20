"""WebSocket endpoints for realtime backend events."""
from fastapi import APIRouter, WebSocket

from app.core.auth import decode_token
from app.core.realtime import realtime_manager


router = APIRouter(tags=["ws"])


def _extract_bearer_token(websocket: WebSocket) -> str | None:
    auth_header = websocket.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return websocket.query_params.get("access_token")


@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    token = _extract_bearer_token(websocket)
    if not token:
        await websocket.close(code=4401, reason="Missing token")
        return

    payload = decode_token(token)
    if not payload or payload.get("type") != "access" or not payload.get("sub"):
        await websocket.close(code=4401, reason="Invalid token")
        return

    await realtime_manager.connect(websocket)
    try:
        while True:
            # Keepalive: client may send ping text frames.
            await websocket.receive_text()
    except Exception:
        realtime_manager.disconnect(websocket)
