"""Fabrique de messages SPADE portant une enveloppe FIPA-ACL JSON."""

from __future__ import annotations

from spade.message import Message
from spade.template import Template

from .schemas import AgentMessage


class MessageFactory:
    def __init__(self, schema_version: str = "1.0", maximum_body_bytes: int = 262144) -> None:
        self.schema_version = schema_version
        self.maximum_body_bytes = maximum_body_bytes

    def build(
        self, *, sender: str, target: str, message_type: str, payload: dict,
        performative: str, ontology: str, protocol: str = "indusguard-pipeline",
        equipment_id: str | None = None, equipment_type: str | None = None,
        priority: str = "medium", parent: AgentMessage | None = None, context: dict | None = None,
    ) -> tuple[AgentMessage, Message]:
        envelope = AgentMessage(
            message_type=message_type, sender_agent=sender, target_agent=target,
            payload=payload,
            equipment_id=equipment_id or (parent.equipment_id if parent else None),
            equipment_type=equipment_type or (parent.equipment_type if parent else None),
            priority=priority, context=context or {}, schema_version=self.schema_version,
            trace_id=parent.trace_id if parent else AgentMessage.__dataclass_fields__["trace_id"].default_factory(),
            correlation_id=parent.correlation_id if parent else AgentMessage.__dataclass_fields__["correlation_id"].default_factory(),
            conversation_id=parent.conversation_id if parent else AgentMessage.__dataclass_fields__["conversation_id"].default_factory(),
        )
        envelope.validate(self.maximum_body_bytes)
        msg = Message(to=target, body=envelope.to_json(), thread=envelope.conversation_id)
        metadata = {
            "performative": performative, "ontology": ontology, "protocol": protocol,
            "conversation-id": envelope.conversation_id, "language": "json-utf8",
            "message-type": message_type, "schema-version": envelope.schema_version,
            "priority": priority, "trace-id": envelope.trace_id,
            "correlation-id": envelope.correlation_id, "message-id": envelope.message_id,
        }
        for key, value in metadata.items():
            msg.set_metadata(key, value)
        return envelope, msg

    @staticmethod
    def template(message_type: str | None = None, performative: str | None = None,
                 protocol: str | None = None) -> Template:
        metadata = {}
        if message_type: metadata["message-type"] = message_type
        if performative: metadata["performative"] = performative
        if protocol: metadata["protocol"] = protocol
        return Template(metadata=metadata)
