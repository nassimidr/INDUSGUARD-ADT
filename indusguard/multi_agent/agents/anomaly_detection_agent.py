from __future__ import annotations
from ..adapters.anomaly_adapter import AnomalyAdapter
from .base_indusguard_agent import BaseIndusGuardAgent

class AnomalyDetectionAgent(BaseIndusGuardAgent):
    def __init__(self,*args,**kwargs)->None: super().__init__("anomaly",*args,**kwargs); self.adapter=AnomalyAdapter(self.config.root)
    async def setup(self)->None: await self.common_setup(["sensor.measurement"])
    async def process(self,envelope,message)->None:
        result=self.adapter.analyze(envelope.payload); payload={"measurement":envelope.payload,"anomaly":result}
        self.metrics.increment("anomalies_detected",int(result["is_anomaly"]))
        if result["is_anomaly"]:
            await self.send_fipa("diagnosis","diagnosis.request",payload,"request","fault-diagnosis",parent=envelope)
            if result["threshold_severity"]>=0.8: await self.send_fipa("supervisor","anomaly.result",result,"inform","anomaly-detection",parent=envelope,priority="high")
        else:
            await self.send_fipa("supervisor","anomaly.result",result,"inform","anomaly-detection",parent=envelope,priority="low")
        await self.emit_historian(envelope,"anomaly_analyzed",result)
