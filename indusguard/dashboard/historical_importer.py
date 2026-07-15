from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

import yaml
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from . import models
from .utils import json_text


def _bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "oui"}


def _number(value: Any, cast=float) -> Any:
    try:
        return cast(value) if value not in (None, "", "nan") else None
    except (TypeError, ValueError):
        return None


def _rows(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _keep(model: type, row: dict[str, Any]) -> dict[str, Any]:
    columns = {column.name for column in model.__table__.columns if column.name != "id"}
    # All rows in a multi-value INSERT must expose the same mapped columns.
    # Supplying None is valid and avoids SQLAlchemy's heterogeneous-key error.
    return {key: row.get(key) for key in columns if key in row}


class HistoricalImporter:
    """Imports generated Phase 1-6 artifacts using SQLite conflict protection."""

    def __init__(self, root: Path, session: Session) -> None:
        self.root, self.session = root, session
        self.counts: dict[str, int] = {}

    def _insert(self, model: type, rows: Iterable[dict[str, Any]], unique: list[str]) -> None:
        values = [_keep(model, row) for row in rows]
        values = [row for row in values if row]
        inserted = 0
        for offset in range(0, len(values), 500):
            result = self.session.execute(insert(model).values(values[offset:offset + 500]).on_conflict_do_nothing(index_elements=unique))
            inserted += max(result.rowcount or 0, 0)
        self.counts[model.__tablename__] = inserted

    def _bulk(self, model: type, rows: list[dict[str, Any]]) -> None:
        for offset in range(0, len(rows), 500):
            self.session.execute(insert(model).values([_keep(model, row) for row in rows[offset:offset + 500]]))

    def run(self) -> dict[str, int]:
        self._assets_and_measurements()
        self._predictions()
        self._maintenance()
        self._multi_agent()
        self.session.commit()
        return self.counts

    def _assets_and_measurements(self) -> None:
        source = list(_rows(self.root / "data/synthetic/industrial_line_scenario.csv"))
        assets: dict[str, dict[str, Any]] = {}
        measurements = []
        for row in source:
            equipment_id = row.get("equipment_id", "")
            if not equipment_id:
                continue
            assets[equipment_id] = {
                "equipment_id": equipment_id, "equipment_type": row.get("equipment_type", "unknown"),
                "line_id": "line_01", "display_name": equipment_id, "status": row.get("operating_state", "unknown"),
                "health_score": _number(row.get("health_score")), "last_seen_at": row.get("timestamp"),
            }
            measurements.append({
                "timestamp": row.get("timestamp"), "equipment_id": equipment_id,
                "equipment_type": row.get("equipment_type", "unknown"), "operating_state": row.get("operating_state"),
                "is_anomaly": _bool(row.get("is_anomaly")), **{key: _number(row.get(key)) for key in
                ("temperature", "vibration", "rpm", "current", "load", "pressure", "flow_rate", "conveyor_speed", "slip_rate", "health_score")},
            })
        self._insert(models.Asset, assets.values(), ["equipment_id"])
        self._insert(models.SensorMeasurement, measurements, ["timestamp", "equipment_id"])

    def _predictions(self) -> None:
        anomaly = ({
            "timestamp": row.get("timestamp"), "equipment_id": row.get("equipment_id"),
            "is_anomaly": _bool(row.get("is_anomaly")), "threshold_prediction": _bool(row.get("threshold_prediction")),
            "isolation_forest_prediction": _bool(row.get("isolation_forest_prediction")),
            "anomaly_score": _number(row.get("anomaly_score")), "detected_sensors": row.get("detected_sensors"),
            "explanation": row.get("anomaly_explanation"),
        } for row in _rows(self.root / "outputs/predictions/anomaly_predictions.csv"))
        self._insert(models.AnomalyResult, anomaly, ["timestamp", "equipment_id"])
        diagnoses = ({
            "timestamp": row.get("timestamp"), "equipment_id": row.get("equipment_id"),
            "diagnosis": row.get("final_diagnosis", "unknown"), "confidence": _number(row.get("final_confidence")) or 0,
            "severity": row.get("severity", "unknown"), "responsible_sensors": row.get("responsible_sensors"),
            "explanation": row.get("diagnosis_explanation"),
        } for row in _rows(self.root / "outputs/diagnosis/fault_diagnosis_predictions.csv"))
        self._insert(models.FaultDiagnosis, diagnoses, ["timestamp", "equipment_id"])
        rul = ({
            "timestamp": row.get("timestamp"), "equipment_id": row.get("equipment_id"),
            "predicted_rul_steps": _number(row.get("predicted_rul_steps")) or 0,
            "predicted_rul_hours": _number(row.get("predicted_rul_hours")) or 0,
            "rul_lower_bound": _number(row.get("rul_lower_bound")), "rul_upper_bound": _number(row.get("rul_upper_bound")),
            "prediction_confidence": _number(row.get("prediction_confidence")), "risk_level": row.get("risk_level", "unknown"),
            "responsible_features": row.get("responsible_features"), "explanation": row.get("rul_explanation"),
        } for row in _rows(self.root / "outputs/rul_predictions/rul_predictions.csv"))
        self._insert(models.RULPrediction, rul, ["timestamp", "equipment_id"])

    def _maintenance(self) -> None:
        recommendations = []
        for row in _rows(self.root / "outputs/maintenance/maintenance_recommendations.csv"):
            mapped = dict(row)
            mapped.update({"trace_id": None, "shutdown_required": _bool(row.get("shutdown_required")),
                           "priority_score": _number(row.get("priority_score")), "estimated_duration_hours": _number(row.get("estimated_duration_hours")),
                           "estimated_total_cost": _number(row.get("estimated_total_cost")), "confidence": _number(row.get("recommendation_confidence")),
                           "explanation": row.get("recommendation_explanation")})
            recommendations.append(mapped)
        # The generated recommendation set has no stable ID; timestamp/equipment/action is stable.
        existing = {(x.timestamp, x.equipment_id, x.recommended_action) for x in self.session.scalars(select(models.MaintenanceRecommendation))}
        fresh = [row for row in recommendations if (row.get("timestamp"), row.get("equipment_id"), row.get("recommended_action")) not in existing]
        if fresh:
            self._bulk(models.MaintenanceRecommendation, fresh)
        self.counts[models.MaintenanceRecommendation.__tablename__] = len(fresh)
        work_orders = []
        for row in _rows(self.root / "outputs/maintenance/work_orders.csv"):
            work_orders.append({**row, "strategy": row.get("maintenance_strategy"), "assigned_resource": row.get("assigned_skill"),
                                "estimated_cost": _number(row.get("estimated_total_cost"))})
        self._insert(models.WorkOrder, work_orders, ["work_order_id"])
        schedule = list(_rows(self.root / "outputs/maintenance/maintenance_schedule.csv"))
        existing_schedule = {(x.work_order_id, x.scheduled_start) for x in self.session.scalars(select(models.MaintenanceSchedule))}
        fresh_schedule = [{**r, "deadline_respected": _bool(r.get("deadline_respected"))} for r in schedule if (r.get("work_order_id"), r.get("scheduled_start")) not in existing_schedule]
        if fresh_schedule:
            self._bulk(models.MaintenanceSchedule, fresh_schedule)
        self.counts[models.MaintenanceSchedule.__tablename__] = len(fresh_schedule)

    def _multi_agent(self) -> None:
        events_path = self.root / "outputs/multi_agent/events.csv"
        events = list(_rows(events_path))
        existing_events = {(x.timestamp, x.trace_id, x.event_type) for x in self.session.scalars(select(models.SystemEvent))}
        event_rows = []
        for row in events:
            key = (row.get("timestamp"), row.get("trace_id"), row.get("message_type"))
            if key not in existing_events:
                event_rows.append({"timestamp": row.get("timestamp"), "event_type": row.get("message_type", "event"),
                                   "trace_id": row.get("trace_id"), "equipment_id": row.get("equipment_id") or None,
                                   "payload": json_text(row) or "{}"})
        if event_rows:
            self._bulk(models.SystemEvent, event_rows)
        self.counts[models.SystemEvent.__tablename__] = len(event_rows)
        health = ({**row, "jid": row.get("agent_id", ""), "messages_processed": _number(row.get("messages_processed"), int) or 0,
                   "errors_count": _number(row.get("errors_count"), int) or 0, "queue_size": _number(row.get("queue_size"), int) or 0,
                   "average_processing_time_ms": _number(row.get("average_processing_time_ms")) or 0}
                  for row in _rows(self.root / "outputs/multi_agent/agent_health.csv"))
        # Health is a time series, with exact source rows naturally unique by timestamp/agent.
        existing_health = {(x.timestamp, x.agent_id) for x in self.session.scalars(select(models.AgentHealth))}
        health = [row for row in health if (row.get("timestamp"), row.get("agent_id")) not in existing_health]
        if health:
            self._bulk(models.AgentHealth, health)
        self.counts[models.AgentHealth.__tablename__] = len(health)
        messages = []
        path = self.root / "outputs/multi_agent/messages.jsonl"
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                messages.append({"timestamp": row.get("timestamp"), "message_id": row.get("message_id"), "trace_id": row.get("trace_id"),
                                 "sender_agent": row.get("sender_agent", ""), "receiver_agent": row.get("target_agent", ""),
                                 "message_type": row.get("message_type", "unknown"), "performative": row.get("performative"),
                                 "protocol": row.get("protocol"), "equipment_id": row.get("equipment_id"), "body": json_text(row.get("payload"))})
        self._insert(models.AgentMessage, messages, ["message_id"])
        self._simple_agent_file(models.SystemDecision, "decisions.csv", "decision")
        self._alerts()
        self._traces(events)

    def _simple_agent_file(self, model: type, filename: str, label: str) -> None:
        source = list(_rows(self.root / f"outputs/multi_agent/{filename}"))
        existing = {(x.timestamp, x.trace_id, x.decision) for x in self.session.scalars(select(model))}
        rows = [{"timestamp": r.get("timestamp"), "trace_id": r.get("trace_id") or f"legacy-{i}", "equipment_id": r.get("equipment_id") or None,
                 "priority": r.get("priority"), "decision": r.get("decision") or r.get("message_type") or label,
                 "explanation": r.get("explanation"), "payload": json_text(r) or "{}"} for i, r in enumerate(source)]
        rows = [r for r in rows if (r["timestamp"], r["trace_id"], r["decision"]) not in existing]
        if rows:
            self._bulk(model, rows)
        self.counts[model.__tablename__] = len(rows)

    def _alerts(self) -> None:
        rows = []
        for index, row in enumerate(_rows(self.root / "outputs/multi_agent/alerts.csv")):
            rows.append({"alert_id": row.get("alert_id") or row.get("message_id") or f"legacy-alert-{index}",
                         "timestamp": row.get("timestamp"), "trace_id": row.get("trace_id"), "equipment_id": row.get("equipment_id") or None,
                         "level": row.get("level") or row.get("priority") or "info", "title": row.get("title") or row.get("alert_type") or "Alerte",
                         "message": row.get("message") or row.get("description") or json_text(row) or "Alerte", "acknowledged": _bool(row.get("acknowledged"))})
        self._insert(models.Alert, rows, ["alert_id"])

    def _traces(self, events: list[dict[str, Any]]) -> None:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for event in events:
            trace_id = event.get("trace_id")
            if trace_id:
                grouped.setdefault(trace_id, []).append(event)
        rows = [{"trace_id": trace_id, "equipment_id": items[0].get("equipment_id") or None,
                 "started_at": min(str(x.get("timestamp")) for x in items), "completed_at": max(str(x.get("timestamp")) for x in items),
                 "status": "completed", "steps_count": len(items), "last_step": items[-1].get("message_type")}
                for trace_id, items in grouped.items()]
        self._insert(models.PipelineTrace, rows, ["trace_id"])
