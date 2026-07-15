from __future__ import annotations
from ..adapters.maintenance_adapter import MaintenanceAdapter
from .base_indusguard_agent import BaseIndusGuardAgent

class MaintenanceAgent(BaseIndusGuardAgent):
    def __init__(self,*args,**kwargs)->None: super().__init__("maintenance",*args,**kwargs); self.adapter=MaintenanceAdapter(self.config.root)
    async def setup(self)->None: await self.common_setup(["maintenance.request"])
    async def process(self,envelope,message)->None:
        source=envelope.payload; result=self.adapter.recommend(source["measurement"],source["diagnosis"],source["rul"]); self.metrics.increment("recommendations_produced")
        payload={**source,"recommendation":result,"cfp":{
            "equipment_id":envelope.equipment_id,"equipment_type":envelope.equipment_type,"diagnosed_fault":source["diagnosis"]["final_diagnosis"],
            "priority":result["priority"],"required_skills":result["required_skills"],"required_parts":result["required_parts"],
            "estimated_duration_hours":result["estimated_duration_hours"],"recommended_start":result["recommended_start"],
            "recommended_deadline":result["recommended_deadline"],"shutdown_required":result["shutdown_required"],"estimated_cost":result["estimated_total_cost"]}}
        critical=result["maintenance_strategy"]=="emergency_shutdown" or result["priority"]=="critical"
        protocol="indusguard-emergency" if critical else "fipa-contract-net"; priority="critical" if critical else result["priority"]
        await self.send_fipa("resource","resource.call_for_proposal",payload,"cfp","resource-allocation",protocol,parent=envelope,priority=priority)
        await self.send_fipa("supervisor","maintenance.recommendation",result,"inform","maintenance-planning",protocol,parent=envelope,priority=priority)
        await self.emit_historian(envelope,"maintenance_recommended",result)
