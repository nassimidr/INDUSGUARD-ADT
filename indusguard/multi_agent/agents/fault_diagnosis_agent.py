from __future__ import annotations
from ..adapters.diagnosis_adapter import DiagnosisAdapter
from .base_indusguard_agent import BaseIndusGuardAgent

class FaultDiagnosisAgent(BaseIndusGuardAgent):
    def __init__(self,*args,**kwargs)->None: super().__init__("diagnosis",*args,**kwargs); self.adapter=DiagnosisAdapter(self.config.root)
    async def setup(self)->None: await self.common_setup(["diagnosis.request"])
    async def process(self,envelope,message)->None:
        measurement=envelope.payload["measurement"]; anomaly=envelope.payload["anomaly"]
        result=self.adapter.diagnose(measurement,anomaly); payload={**envelope.payload,"diagnosis":result}; self.metrics.increment("diagnostics_produced")
        priority="critical" if result["severity"]=="critical" or result["final_diagnosis"]=="cascade_failure" else "high"
        protocol="indusguard-emergency" if priority=="critical" else "indusguard-pipeline"
        await self.send_fipa("rul","rul.request",payload,"request","rul-prediction",protocol,parent=envelope,priority=priority)
        if priority=="critical": await self.send_fipa("supervisor","diagnosis.result",result,"inform","fault-diagnosis",protocol,parent=envelope,priority=priority)
        await self.emit_historian(envelope,"diagnosed",result)
