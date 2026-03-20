"""Realtime event manager for WebSocket subscribers."""
from typing import Any, Dict, Set

from fastapi import WebSocket


class RealtimeManager:
    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, event_type: str, payload: Dict[str, Any]) -> None:
        if not self._connections:
            return

        message = {"type": event_type, "payload": payload}
        stale: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_json(message)
            except Exception:
                stale.append(ws)

        for ws in stale:
            self.disconnect(ws)


realtime_manager = RealtimeManager()
