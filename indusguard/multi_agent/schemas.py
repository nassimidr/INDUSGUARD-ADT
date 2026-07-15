"""Enveloppe JSON commune, typée et versionnée."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from typing import Any
from uuid import UUID, uuid4

from .constants import EQUIPMENT_TYPES, MESSAGE_TYPES, PRIORITIES, SCHEMA_VERSION


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class AgentMessage:
    message_type: str
    sender_agent: str
    target_agent: str
    payload: dict[str, Any]
    equipment_id: str | None = None
    equipment_type: str | None = None
    priority: str = "medium"
    context: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
    message_id: str = field(default_factory=lambda: str(uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=utc_now)
    retry_count: int = 0

    def validate(self, maximum_body_bytes: int = 262144) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Version de schéma non supportée: {self.schema_version}")
        for name in ("message_id", "trace_id", "correlation_id", "conversation_id"):
            UUID(str(getattr(self, name)))
        parsed = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Le timestamp doit inclure un fuseau horaire.")
        if self.message_type not in MESSAGE_TYPES:
            raise ValueError(f"Type de message inconnu: {self.message_type}")
        if self.priority not in PRIORITIES:
            raise ValueError(f"Priorité inconnue: {self.priority}")
        if self.equipment_type is not None and self.equipment_type not in EQUIPMENT_TYPES:
            raise ValueError(f"Type d'équipement inconnu: {self.equipment_type}")
        if self.retry_count < 0:
            raise ValueError("retry_count ne peut pas être négatif.")
        if len(self.to_json().encode("utf-8")) > maximum_body_bytes:
            raise ValueError("Corps de message trop volumineux.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"), default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMessage":
        required = {"message_type", "sender_agent", "target_agent", "payload"}
        missing = required - set(data)
        if missing:
            raise ValueError(f"Champs obligatoires absents: {sorted(missing)}")
        return cls(**data)

    @classmethod
    def from_json(cls, body: str) -> "AgentMessage":
        try:
            data = json.loads(body)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Corps JSON invalide.") from exc
        if not isinstance(data, dict):
            raise ValueError("L'enveloppe JSON doit être un objet.")
        return cls.from_dict(data)
