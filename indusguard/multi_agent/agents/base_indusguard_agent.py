"""Classe SPADE commune: sécurité, FIPA, idempotence, retry et heartbeat."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour

from ..adapters.persistence_adapter import PersistenceAdapter
from ..config import MultiAgentConfig
from ..dead_letter import DeadLetterQueue
from ..idempotency import IdempotencyCache
from ..message_factory import MessageFactory
from ..message_validator import MessageValidator
from ..metrics import MetricsCollector
from ..retry_policy import RetryPolicy
from ..schemas import AgentMessage, utc_now


class MessageHandlingBehaviour(CyclicBehaviour):
    async def run(self) -> None:
        message=await self.receive(timeout=1)
        if message is not None: await self.agent.handle_spade_message(message)


class HeartbeatBehaviour(PeriodicBehaviour):
    async def run(self) -> None:
        await self.agent.send_fipa(
            "supervisor", "heartbeat", self.agent.health_payload(), "inform",
            "agent-health", "indusguard-heartbeat", priority="low",
        )


class BaseIndusGuardAgent(Agent):
    def __init__(self,name:str,config:MultiAgentConfig,metrics:MetricsCollector,persistence:PersistenceAdapter) -> None:
        self.agent_name=name; self.config=config; self.metrics=metrics; self.persistence=persistence
        super().__init__(config.jid(name),config.password,port=int(config.values["xmpp"]["client_port"]),verify_security=False)
        msg_cfg=config.values["messages"]
        self.factory=MessageFactory(msg_cfg["schema_version"],msg_cfg["maximum_body_bytes"])
        self.validator=MessageValidator(config.allowed_jids,msg_cfg["maximum_body_bytes"])
        idem=config.values["idempotency"]; self.idempotency=IdempotencyCache(idem["cache_size"],idem["ttl_seconds"])
        retries=config.values["retries"]; self.retry_policy=RetryPolicy(retries["maximum_attempts"],retries["initial_delay_seconds"],retries["backoff_factor"],retries["maximum_delay_seconds"])
        self.dead_letters=DeadLetterQueue(persistence.directory/"dead_letter_messages.jsonl")
        self.status="starting"; self.messages_processed=0; self.errors_count=0; self.processing_times:list[float]=[]

    async def common_setup(self, message_types: list[str]) -> None:
        self.status="ready"
        for message_type in message_types:
            self.add_behaviour(MessageHandlingBehaviour(),self.factory.template(message_type=message_type))
        hb=self.config.values["heartbeats"]
        if hb["enabled"]:
            self.add_behaviour(HeartbeatBehaviour(period=float(hb["interval_seconds"])))

    async def send_fipa(self,target_name:str,message_type:str,payload:dict[str,Any],performative:str,ontology:str,
                        protocol:str="indusguard-pipeline",*,parent:AgentMessage|None=None,equipment_id:str|None=None,
                        equipment_type:str|None=None,priority:str="medium",context:dict[str,Any]|None=None) -> AgentMessage:
        target=self.config.jid(target_name) if "@" not in target_name else target_name
        envelope,message=self.factory.build(sender=str(self.jid).split("/")[0],target=target,message_type=message_type,payload=payload,
            performative=performative,ontology=ontology,protocol=protocol,equipment_id=equipment_id or (parent.equipment_id if parent else None),
            equipment_type=equipment_type or (parent.equipment_type if parent else None),priority=priority,parent=parent,context=context)
        # Force le chemin XMPP de SPADE. Container.send court-circuite sinon les
        # agents du même processus par une distribution mémoire.
        message.sender=str(self.jid)
        message.prepare(self.client).send(); message.sent=True
        self.metrics.sent(message_type,self.agent_name,envelope.trace_id)
        self.persistence.append_jsonl("messages.jsonl",envelope.to_dict())
        self.persistence.event({"timestamp":envelope.timestamp,"trace_id":envelope.trace_id,"correlation_id":envelope.correlation_id,
            "conversation_id":envelope.conversation_id,"message_id":envelope.message_id,"sender_agent":envelope.sender_agent,
            "receiver_agent":envelope.target_agent,"message_type":message_type,"performative":performative,"ontology":ontology,
            "protocol":protocol,"equipment_id":envelope.equipment_id,"status":"sent","processing_time_ms":0})
        return envelope

    async def handle_spade_message(self,message) -> None:
        started=time.perf_counter(); envelope=None; self.status="busy"
        try:
            envelope=self.validator.validate(message)
            if self.idempotency.contains(envelope.message_id):
                self.metrics.increment("messages_duplicated"); return
            await self.process(envelope,message)
            self.idempotency.put(envelope.message_id); self.messages_processed+=1
            elapsed=(time.perf_counter()-started)*1000; self.processing_times.append(elapsed); self.metrics.processed(self.agent_name,elapsed)
        except Exception as exc:
            self.errors_count+=1; self.metrics.increment("errors")
            if envelope is not None: await self._retry_or_dead_letter(envelope,message,exc)
        finally: self.status="ready" if self.is_alive() else "stopped"

    async def _retry_or_dead_letter(self,envelope:AgentMessage,message,error:BaseException)->None:
        if self.retry_policy.should_retry(envelope.retry_count):
            await asyncio.sleep(self.retry_policy.delay(envelope.retry_count)); envelope.retry_count+=1
            envelope.context.setdefault("original_sender_agent",envelope.sender_agent)
            envelope.sender_agent=str(self.jid).split("/")[0]; envelope.target_agent=envelope.sender_agent
            message.to=envelope.target_agent; message.body=envelope.to_json(); message.sender=str(self.jid); self.metrics.increment("retries")
            message.prepare(self.client).send(); message.sent=True
        else:
            self.dead_letters.add(envelope,self.agent_name,error); self.metrics.increment("dead_letters")

    async def process(self,envelope:AgentMessage,message)->None: raise NotImplementedError

    def health_payload(self)->dict[str,Any]:
        average=sum(self.processing_times)/len(self.processing_times) if self.processing_times else 0.0
        return {"agent_id":str(self.jid).split("/")[0],"status":self.status,"timestamp":utc_now(),
            "messages_processed":self.messages_processed,"errors_count":self.errors_count,"queue_size":0,
            "average_processing_time_ms":round(average,3)}

    async def emit_historian(self,parent:AgentMessage,status:str,payload:dict[str,Any]|None=None)->None:
        if self.agent_name != "historian":
            await self.send_fipa("historian","historian.event",{"status":status,**(payload or {})},"inform","historian",parent=parent,priority="low")

    async def stop(self) -> None:
        self.status="stopping"; await super().stop(); self.status="stopped"
