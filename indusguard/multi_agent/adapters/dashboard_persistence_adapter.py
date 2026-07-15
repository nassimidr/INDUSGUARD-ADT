"""Non-blocking bridge from Phase 6 persistence calls to the Phase 7 database."""
from __future__ import annotations

import queue
import threading
from typing import Any

from sqlalchemy.dialects.sqlite import insert

from indusguard.dashboard import models
from indusguard.dashboard.config import load_dashboard_config
from indusguard.dashboard.database import build_engine, initialize_database, session_factory
from indusguard.dashboard.utils import json_text


class DashboardPersistenceAdapter:
    def __init__(self, config_path: str = "configs/dashboard.yaml", queue_size: int = 10_000) -> None:
        config = load_dashboard_config(config_path); self.engine = build_engine(config); initialize_database(self.engine)
        self.Session = session_factory(self.engine); self.queue: queue.Queue[tuple[str, dict[str, Any]] | None] = queue.Queue(queue_size)
        self.worker = threading.Thread(target=self._consume, name="dashboard-db-writer", daemon=True); self.worker.start()

    def submit(self, kind: str, record: dict[str, Any]) -> None:
        try: self.queue.put_nowait((kind, dict(record)))
        except queue.Full: pass  # CSV remains the source of truth and can be re-imported.

    def close(self, timeout: float = 5) -> None:
        self.queue.put(None); self.worker.join(timeout); self.engine.dispose()

    def _consume(self) -> None:
        while True:
            item = self.queue.get()
            if item is None: return
            kind, record = item
            try:
                with self.Session() as session:
                    model, values, unique = self._map(kind, record)
                    if model:
                        session.execute(insert(model).values(**values).on_conflict_do_nothing(index_elements=unique)); session.commit()
            except Exception:
                # Dashboard persistence must never interrupt the industrial pipeline.
                continue

    def _map(self, kind: str, row: dict[str, Any]):
        timestamp = str(row.get("timestamp", "")); trace_id = row.get("trace_id"); equipment_id = row.get("equipment_id")
        if kind == "domain":
            payload = row.get("payload") or {}; message_type = row.get("message_type")
            common = {"timestamp": str(payload.get("timestamp") or timestamp), "trace_id": trace_id, "equipment_id": equipment_id}
            if message_type == "sensor.measurement":
                fields = ("temperature", "vibration", "rpm", "current", "load", "pressure", "flow_rate", "conveyor_speed", "slip_rate", "health_score", "operating_state", "is_anomaly")
                return models.SensorMeasurement, {**common, "equipment_type": row.get("equipment_type", "unknown"), **{key: payload.get(key) for key in fields}}, ["timestamp", "equipment_id"]
            if message_type == "anomaly.result":
                return models.AnomalyResult, {**common, "is_anomaly": bool(payload.get("is_anomaly")), "threshold_prediction": bool(payload.get("threshold_prediction")),
                    "isolation_forest_prediction": bool(payload.get("isolation_forest_prediction")), "anomaly_score": payload.get("anomaly_score"),
                    "detected_sensors": json_text(payload.get("detected_sensors")), "explanation": payload.get("anomaly_explanation")}, ["timestamp", "equipment_id"]
            if message_type == "diagnosis.result":
                return models.FaultDiagnosis, {**common, "diagnosis": payload.get("final_diagnosis") or payload.get("diagnosis") or "unknown",
                    "confidence": payload.get("final_confidence") or payload.get("confidence") or 0, "severity": payload.get("severity", "unknown"),
                    "responsible_sensors": json_text(payload.get("responsible_sensors")), "explanation": payload.get("diagnosis_explanation") or payload.get("explanation")}, ["timestamp", "equipment_id"]
            if message_type == "rul.result":
                return models.RULPrediction, {**common, "predicted_rul_steps": payload.get("predicted_rul_steps", 0), "predicted_rul_hours": payload.get("predicted_rul_hours", 0),
                    "rul_lower_bound": payload.get("rul_lower_bound"), "rul_upper_bound": payload.get("rul_upper_bound"), "prediction_confidence": payload.get("prediction_confidence"),
                    "risk_level": payload.get("risk_level", "unknown"), "responsible_features": json_text(payload.get("responsible_features")), "explanation": payload.get("rul_explanation")}, ["timestamp", "equipment_id"]
            if message_type == "maintenance.recommendation":
                return models.MaintenanceRecommendation, {**common, "maintenance_strategy": payload.get("maintenance_strategy", "monitor"),
                    "recommended_action": payload.get("recommended_action", "Surveiller"), "priority": payload.get("priority", row.get("priority", "medium")),
                    "priority_score": payload.get("priority_score"), "recommended_start": payload.get("recommended_start"), "recommended_deadline": payload.get("recommended_deadline"),
                    "estimated_duration_hours": payload.get("estimated_duration_hours"), "required_skills": json_text(payload.get("required_skills")),
                    "required_parts": json_text(payload.get("required_parts")), "shutdown_required": bool(payload.get("shutdown_required")),
                    "estimated_total_cost": payload.get("estimated_total_cost"), "confidence": payload.get("recommendation_confidence"),
                    "explanation": payload.get("recommendation_explanation")}, ["id"]
            return None, {}, []
        if kind == "event":
            return models.SystemEvent, {"timestamp": timestamp, "event_type": row.get("message_type", "event"), "trace_id": trace_id,
                "equipment_id": equipment_id, "priority": row.get("priority"), "payload": json_text(row) or "{}"}, ["id"]
        if kind == "message":
            return models.AgentMessage, {"timestamp": timestamp, "message_id": row.get("message_id"), "trace_id": trace_id,
                "sender_agent": row.get("sender_agent", ""), "receiver_agent": row.get("target_agent", ""), "message_type": row.get("message_type", "unknown"),
                "performative": row.get("performative"), "protocol": row.get("protocol"), "equipment_id": equipment_id, "body": json_text(row.get("payload"))}, ["message_id"]
        if kind == "health":
            return models.AgentHealth, {"timestamp": timestamp, "agent_id": row.get("agent_id", ""), "jid": row.get("agent_id", ""),
                "status": row.get("status", "unknown"), "last_heartbeat": row.get("last_heartbeat"), "messages_processed": row.get("messages_processed", 0),
                "errors_count": row.get("errors_count", 0), "queue_size": row.get("queue_size", 0), "average_processing_time_ms": row.get("average_processing_time_ms", 0)}, ["id"]
        if kind == "alert":
            return models.Alert, {"alert_id": row.get("alert_id"), "timestamp": timestamp, "trace_id": trace_id, "equipment_id": equipment_id,
                "level": row.get("level", "info"), "title": row.get("title", "Alerte"), "message": row.get("message", ""), "acknowledged": False}, ["alert_id"]
        if kind == "decision":
            return models.SystemDecision, {"timestamp": timestamp, "trace_id": trace_id or row.get("message_id", "legacy"), "equipment_id": equipment_id,
                "priority": row.get("priority"), "decision": row.get("supervisor_decision") or row.get("resource_decision") or "decision",
                "explanation": row.get("decision_explanation"), "payload": json_text(row) or "{}"}, ["id"]
        return None, {}, []
