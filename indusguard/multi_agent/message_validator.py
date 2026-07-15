"""Validation conjointe du corps JSON et des métadonnées SPADE."""

from __future__ import annotations

from spade.message import Message

from .constants import FIPA_METADATA, ONTOLOGIES, PERFORMATIVES, PROTOCOLS
from .schemas import AgentMessage


class MessageValidator:
    def __init__(self, allowed_jids: set[str], maximum_body_bytes: int = 262144) -> None:
        self.allowed_jids = {jid.lower() for jid in allowed_jids}
        self.maximum_body_bytes = int(maximum_body_bytes)

    def validate(self, message: Message) -> AgentMessage:
        missing = [key for key in FIPA_METADATA if not message.get_metadata(key)]
        if missing:
            raise ValueError(f"Métadonnées FIPA absentes: {missing}")
        envelope = AgentMessage.from_json(message.body or "")
        envelope.validate(self.maximum_body_bytes)
        sender = str(message.sender or envelope.sender_agent).split("/")[0].lower()
        if sender not in self.allowed_jids:
            raise ValueError(f"Expéditeur non autorisé: {sender}")
        if envelope.sender_agent.lower() != sender:
            raise ValueError("L'expéditeur XMPP diffère de l'enveloppe.")
        if message.get_metadata("performative") not in PERFORMATIVES:
            raise ValueError("Performative FIPA invalide.")
        if message.get_metadata("ontology") not in ONTOLOGIES:
            raise ValueError("Ontologie invalide.")
        if message.get_metadata("protocol") not in PROTOCOLS:
            raise ValueError("Protocole invalide.")
        expected = {
            "message-type": envelope.message_type, "schema-version": envelope.schema_version,
            "priority": envelope.priority, "trace-id": envelope.trace_id,
            "correlation-id": envelope.correlation_id, "message-id": envelope.message_id,
            "conversation-id": envelope.conversation_id,
        }
        if any(message.get_metadata(k) != v for k, v in expected.items()):
            raise ValueError("Incohérence entre métadonnées FIPA et enveloppe JSON.")
        return envelope
