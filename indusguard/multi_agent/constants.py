"""Vocabulaire FIPA-ACL et constantes du système multi-agents."""

SCHEMA_VERSION = "1.0"
EQUIPMENT_TYPES = frozenset({"motor", "bearing", "conveyor", "pump"})
PRIORITIES = frozenset({"low", "medium", "high", "urgent", "critical"})
PERFORMATIVES = frozenset({
    "inform", "request", "query-if", "cfp", "propose", "accept-proposal",
    "reject-proposal", "confirm", "refuse", "failure", "not-understood", "cancel",
})
ONTOLOGIES = frozenset({
    "sensor-monitoring", "anomaly-detection", "fault-diagnosis", "rul-prediction",
    "maintenance-planning", "resource-allocation", "supervision", "alerting",
    "historian", "agent-health",
    "industrial-vision",
})
PROTOCOLS = frozenset({
    "indusguard-pipeline", "fipa-request", "fipa-contract-net",
    "indusguard-emergency", "indusguard-heartbeat",
})
MESSAGE_TYPES = frozenset({
    "sensor.measurement", "sensor.stream_started", "sensor.stream_completed",
    "anomaly.result", "diagnosis.request", "diagnosis.result", "rul.request",
    "rul.result", "maintenance.request", "maintenance.recommendation",
    "resource.call_for_proposal", "resource.proposal", "resource.refusal",
    "resource.acceptance", "resource.rejection", "resource.confirmation",
    "resource.failure", "supervisor.decision", "supervisor.reanalysis_request",
    "alert.created", "historian.event", "heartbeat", "agent.status",
    "processing.failure", "pipeline.completed",
    "vision.analysis.request", "vision.detection", "vision.analysis.completed", "vision.analysis.failed",
})
AGENT_STATES = frozenset({"starting", "ready", "busy", "degraded", "unavailable", "stopping", "stopped"})
CASE_STATES = (
    "measurement_received", "anomaly_analysis", "normal", "anomaly_detected",
    "diagnosis_pending", "diagnosed", "rul_pending", "rul_predicted",
    "maintenance_pending", "resource_negotiation", "scheduled", "blocked",
    "emergency", "failed", "completed",
)
FIPA_METADATA = (
    "performative", "ontology", "protocol", "conversation-id", "language",
    "message-type", "schema-version", "priority", "trace-id", "correlation-id", "message-id",
)
