from __future__ import annotations
from ..adapters.rul_adapter import RULAdapter
from .base_indusguard_agent import BaseIndusGuardAgent

class RULPredictionAgent(BaseIndusGuardAgent):
    def __init__(self,*args,**kwargs)->None: super().__init__("rul",*args,**kwargs); self.adapter=RULAdapter(self.config.root)
    async def setup(self)->None: await self.common_setup(["rul.request"])
    async def process(self,envelope,message)->None:
        result=self.adapter.predict(envelope.payload["measurement"]); payload={**envelope.payload,"rul":result}; self.metrics.increment("rul_predictions_produced")
        critical=result["risk_level"]=="critical" or result["predicted_rul_steps"]<=float(self.adapter.config["risk_thresholds"]["critical_max"])
        protocol="indusguard-emergency" if critical else "indusguard-pipeline"; priority="critical" if critical else "high"
        await self.send_fipa("maintenance","maintenance.request",payload,"request","maintenance-planning",protocol,parent=envelope,priority=priority)
        if critical: await self.send_fipa("supervisor","rul.result",result,"inform","rul-prediction",protocol,parent=envelope,priority=priority)
        await self.emit_historian(envelope,"rul_predicted",result)
