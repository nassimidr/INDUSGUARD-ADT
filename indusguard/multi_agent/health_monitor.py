"""Heartbeats et détection des agents indisponibles."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class HealthMonitor:
    def __init__(self, unhealthy_after_seconds: float = 20) -> None:
        self.unhealthy_after_seconds = float(unhealthy_after_seconds)
        self.records: dict[str, dict[str, Any]] = {}

    def record(self, payload: dict[str, Any]) -> None:
        self.records[str(payload["agent_id"])] = dict(payload)

    def unavailable(self, now: datetime | None = None) -> list[str]:
        instant = now or datetime.now(timezone.utc)
        unavailable = []
        for jid, data in self.records.items():
            stamp = datetime.fromisoformat(str(data["timestamp"]).replace("Z", "+00:00"))
            if (instant - stamp).total_seconds() > self.unhealthy_after_seconds:
                unavailable.append(jid)
        return unavailable
