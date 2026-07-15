from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class DashboardConnectionManager:
    def __init__(self, maximum_connections: int = 20) -> None:
        self.maximum_connections = maximum_connections
        self._connections: dict[WebSocket, set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> bool:
        async with self._lock:
            if len(self._connections) >= self.maximum_connections:
                await websocket.close(code=1013, reason="Capacite atteinte")
                return False
            await websocket.accept()
            self._connections[websocket] = {"*"}
            return True

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.pop(websocket, None)

    async def subscribe(self, websocket: WebSocket, event_types: list[str]) -> None:
        if websocket in self._connections:
            self._connections[websocket] = set(event_types) or {"*"}

    async def broadcast(self, event_type: str, payload: dict[str, Any]) -> None:
        message = {"event": event_type, "data": payload}
        stale: list[WebSocket] = []
        for socket, subscriptions in list(self._connections.items()):
            if "*" not in subscriptions and event_type not in subscriptions:
                continue
            try:
                await socket.send_json(message)
            except Exception:
                stale.append(socket)
        for socket in stale:
            await self.disconnect(socket)

    @property
    def connection_count(self) -> int:
        return len(self._connections)
