"""Persistance CSV/JSONL sécurisée et reconstructible par trace."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


EVENT_COLUMNS = ["timestamp","trace_id","correlation_id","conversation_id","message_id","sender_agent","receiver_agent","message_type","performative","ontology","protocol","equipment_id","status","processing_time_ms"]
DECISION_COLUMNS = ["timestamp","trace_id","equipment_id","equipment_type","is_anomaly","diagnosis","diagnosis_confidence","severity","predicted_rul_steps","risk_level","maintenance_strategy","priority","resource_decision","supervisor_decision","work_order_id","decision_explanation"]
ALERT_COLUMNS = ["timestamp","alert_id","trace_id","equipment_id","level","title","message","acknowledged"]
HEALTH_COLUMNS = ["timestamp","agent_id","status","last_heartbeat","messages_processed","errors_count","queue_size","average_processing_time_ms"]


class PersistenceAdapter:
    def __init__(self, directory: str | Path) -> None:
        self.directory=Path(directory); self.directory.mkdir(parents=True,exist_ok=True)

    def append_jsonl(self, filename: str, record: dict[str, Any]) -> None:
        with (self.directory/filename).open("a",encoding="utf-8") as stream:
            stream.write(json.dumps(record,ensure_ascii=False,default=str)+"\n")

    def append_csv(self, filename: str, columns: list[str], record: dict[str, Any]) -> None:
        path=self.directory/filename; exists=path.exists() and path.stat().st_size>0
        with path.open("a",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=columns,extrasaction="ignore")
            if not exists: writer.writeheader()
            writer.writerow({key: record.get(key,"") for key in columns})

    def event(self, record: dict[str, Any]) -> None: self.append_csv("events.csv",EVENT_COLUMNS,record)
    def decision(self, record: dict[str, Any]) -> None: self.append_csv("decisions.csv",DECISION_COLUMNS,record)
    def alert(self, record: dict[str, Any]) -> None: self.append_csv("alerts.csv",ALERT_COLUMNS,record)
    def health(self, record: dict[str, Any]) -> None: self.append_csv("agent_health.csv",HEALTH_COLUMNS,record)

    def reset(self) -> None:
        for name in ("messages.jsonl","events.csv","decisions.csv","alerts.csv","agent_health.csv","dead_letter_messages.jsonl"):
            path=self.directory/name
            if path.exists(): path.unlink()
        for name in ("messages.jsonl","dead_letter_messages.jsonl"):
            (self.directory/name).touch()
