"""Registre des agents, JID et états d'exécution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class AgentRecord:
    name: str
    jid: str
    status: str = "starting"
    last_heartbeat: str | None = None


class AgentRegistry:
    def __init__(self) -> None:
        self._by_name: dict[str, AgentRecord] = {}
        self._by_jid: dict[str, AgentRecord] = {}

    def register(self, name: str, jid: str) -> AgentRecord:
        bare = jid.split("/")[0].lower()
        if name in self._by_name or bare in self._by_jid:
            raise ValueError(f"Agent déjà enregistré: {name}/{jid}")
        record = AgentRecord(name, bare)
        self._by_name[name] = self._by_jid[bare] = record
        return record

    def get(self, name_or_jid: str) -> AgentRecord:
        key = name_or_jid.lower()
        return self._by_name.get(key) or self._by_jid[key]

    def update(self, name_or_jid: str, status: str) -> None:
        record = self.get(name_or_jid)
        record.status = status
        record.last_heartbeat = datetime.now(timezone.utc).isoformat()

    def all(self) -> tuple[AgentRecord, ...]:
        return tuple(self._by_name.values())
