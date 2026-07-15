"""Dead-letter queue JSONL append-only."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .schemas import AgentMessage, utc_now


@dataclass(frozen=True)
class DeadLetter:
    timestamp: str
    message_id: str
    trace_id: str
    failed_agent: str
    receiver_agent: str
    message_type: str
    retry_count: int
    error_type: str
    error_message: str
    original_message: dict[str, Any]


class DeadLetterQueue:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def add(self, envelope: AgentMessage, failed_agent: str, error: BaseException) -> DeadLetter:
        entry = DeadLetter(
            utc_now(), envelope.message_id, envelope.trace_id, failed_agent,
            envelope.target_agent, envelope.message_type, envelope.retry_count,
            type(error).__name__, str(error), envelope.to_dict(),
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(entry), ensure_ascii=False, default=str) + "\n")
        return entry

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists(): return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line]
