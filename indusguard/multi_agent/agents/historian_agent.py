from __future__ import annotations
from .base_indusguard_agent import BaseIndusGuardAgent

class HistorianAgent(BaseIndusGuardAgent):
    async def setup(self)->None:
        await self.common_setup(["historian.event","pipeline.completed","alert.created","processing.failure"])
    def __init__(self,*args,**kwargs)->None: super().__init__("historian",*args,**kwargs)
    async def process(self,envelope,message)->None:
        self.persistence.event({"timestamp":envelope.timestamp,"trace_id":envelope.trace_id,"correlation_id":envelope.correlation_id,
            "conversation_id":envelope.conversation_id,"message_id":envelope.message_id,"sender_agent":envelope.sender_agent,
            "receiver_agent":envelope.target_agent,"message_type":envelope.message_type,"performative":message.get_metadata("performative"),
            "ontology":message.get_metadata("ontology"),"protocol":message.get_metadata("protocol"),"equipment_id":envelope.equipment_id,
            "status":envelope.payload.get("status",envelope.payload.get("state","received")),"processing_time_ms":0})
