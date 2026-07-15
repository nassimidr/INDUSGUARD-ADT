from __future__ import annotations
import time
from ..notifications import ConsoleNotificationChannel,FileNotificationChannel
from ..schemas import utc_now
from .base_indusguard_agent import BaseIndusGuardAgent

class AlertAgent(BaseIndusGuardAgent):
    def __init__(self,*args,cooldown_seconds:float=10,**kwargs)->None:
        super().__init__("alert",*args,**kwargs); self.cooldown=cooldown_seconds; self.recent={}; self.channels=[ConsoleNotificationChannel(),FileNotificationChannel(self.persistence)]
    async def setup(self)->None: await self.common_setup(["alert.created","supervisor.decision"])
    async def process(self,envelope,message)->None:
        payload=dict(envelope.payload); key=f"{envelope.equipment_id}:{payload.get('level')}:{payload.get('title')}"; now=time.monotonic()
        if now-self.recent.get(key,0)<self.cooldown: self.metrics.increment("messages_duplicated"); return
        self.recent[key]=now; alert={"timestamp":utc_now(),"trace_id":envelope.trace_id,"equipment_id":envelope.equipment_id,**payload}
        for channel in self.channels: channel.notify(alert)
        if payload.get("level")=="critical": self.metrics.increment("critical_alerts")
        await self.emit_historian(envelope,"alert_created",alert)
