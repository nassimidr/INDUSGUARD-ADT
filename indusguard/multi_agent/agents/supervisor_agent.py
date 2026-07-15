"""Coordination, machine d'états, décision Contract Net et urgences simulées."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from ..health_monitor import HealthMonitor
from ..schemas import utc_now
from .base_indusguard_agent import BaseIndusGuardAgent


class SupervisorAgent(BaseIndusGuardAgent):
    def __init__(self,*args,**kwargs)->None:
        super().__init__("supervisor",*args,**kwargs); self.health=HealthMonitor(self.config.values["heartbeats"]["unhealthy_after_seconds"])
        self.case_states:dict[str,str]={}; self.expected=0; self.completed=0; self.stream_finished=False; self.pipeline_done=asyncio.Event()
        self.work_orders:dict[str,str]={}; self.active_contracts:set[str]=set(); self.blocked_cases:set[str]=set()
    async def setup(self)->None:
        await self.common_setup(["sensor.stream_started","sensor.stream_completed","anomaly.result","diagnosis.result","rul.result","maintenance.recommendation","resource.proposal","resource.refusal","resource.confirmation","resource.failure","heartbeat","processing.failure"])
    async def process(self,envelope,message)->None:
        kind=envelope.message_type
        if kind=="sensor.stream_started": self.expected=int(envelope.payload["measurement_count"])
        elif kind=="sensor.stream_completed": self.stream_finished=True; self._check_done()
        elif kind=="heartbeat": self.health.record(envelope.payload); self.metrics.increment("heartbeats_received"); self.persistence.health({"timestamp":utc_now(),**envelope.payload,"last_heartbeat":envelope.payload["timestamp"]})
        elif kind=="anomaly.result":
            if envelope.payload["is_anomaly"]: self.case_states[envelope.trace_id]="anomaly_detected"
            else: await self._finish(envelope,"normal",{"is_anomaly":False})
        elif kind in {"diagnosis.result","rul.result","maintenance.recommendation"}:
            self.case_states[envelope.trace_id]="emergency" if envelope.priority=="critical" else kind.split(".")[0]+"_pending"
            if envelope.priority=="critical": await self._alert(envelope,"critical","Urgence industrielle simulée","Arrêt d'urgence simulé; aucun équipement physique n'est commandé.")
        elif kind=="resource.proposal": await self._proposal(envelope)
        elif kind=="resource.refusal": await self._blocked(envelope,envelope.payload["refusal_reason"])
        elif kind=="resource.confirmation": await self._scheduled(envelope)
        elif kind in {"resource.failure","processing.failure"}: await self._blocked(envelope,str(envelope.payload.get("reason","Échec de traitement")))
    async def _proposal(self,envelope)->None:
        p=envelope.payload; source=p.get("source",{}); key=self._business_key(envelope,source)
        if key in self.active_contracts or key in self.work_orders or key in self.blocked_cases:
            self.metrics.increment("messages_duplicated")
            await self.send_fipa("resource","resource.rejection",{"proposal_id":p["proposal_id"],"accepted":False},"reject-proposal","resource-allocation","fipa-contract-net",parent=envelope,priority=envelope.priority)
            await self._finish(envelope,"completed",{"duplicate_business_case":key}); return
        self.active_contracts.add(key)
        accepted=bool(p["available"] and p["parts_available"] and p["deadline_respected"] and p["proposal_score"]>=0.5)
        message_type="resource.acceptance" if accepted else "resource.rejection"; performative="accept-proposal" if accepted else "reject-proposal"
        await self.send_fipa("resource",message_type,{"proposal_id":p["proposal_id"],"accepted":accepted},performative,"resource-allocation","fipa-contract-net",parent=envelope,priority=envelope.priority)
        self.case_states[envelope.trace_id]="resource_negotiation"
    async def _scheduled(self,envelope)->None:
        source=envelope.payload["source"]; work_order_id=f"WO-MAS-{uuid4().hex[:10].upper()}"
        key=self._business_key(envelope,source)
        if key in self.work_orders:
            self.metrics.increment("messages_duplicated"); await self._finish(envelope,"completed",{"work_order_id":self.work_orders[key]}); return
        self.work_orders[key]=work_order_id; self.active_contracts.discard(key); self.metrics.increment("work_orders_created"); self.metrics.increment("interventions_scheduled")
        recommendation=source["recommendation"]; diagnosis=source["diagnosis"]; rul=source["rul"]
        record=self._decision_record(envelope,source,"scheduled",work_order_id)
        self.persistence.decision(record); await self._alert(envelope,"critical" if envelope.priority=="critical" else "high","Ordre de travail confirmé",f"{work_order_id} planifié pour {envelope.equipment_id}.")
        await self._finish(envelope,"scheduled",record)
    async def _blocked(self,envelope,reason:str)->None:
        source=envelope.payload.get("source",{}); key=self._business_key(envelope,source)
        if key in self.active_contracts or key in self.work_orders or key in self.blocked_cases:
            self.metrics.increment("messages_duplicated"); await self._finish(envelope,"completed",{"duplicate_business_case":key}); return
        self.metrics.increment("interventions_blocked")
        self.blocked_cases.add(key)
        self.active_contracts.discard(key)
        record=self._decision_record(envelope,source,"blocked",""); record["decision_explanation"]=reason; self.persistence.decision(record)
        await self._alert(envelope,"urgent","Intervention bloquée",reason); await self._finish(envelope,"blocked",record,False)
    def _decision_record(self,envelope,source,status,work_order_id):
        d=source.get("diagnosis",{}); r=source.get("rul",{}); rec=source.get("recommendation",{}); a=source.get("anomaly",{})
        return {"timestamp":utc_now(),"trace_id":envelope.trace_id,"equipment_id":envelope.equipment_id,"equipment_type":envelope.equipment_type,
            "is_anomaly":a.get("is_anomaly",True),"diagnosis":d.get("final_diagnosis",""),"diagnosis_confidence":d.get("final_confidence",""),
            "severity":d.get("severity",""),"predicted_rul_steps":r.get("predicted_rul_steps",""),"risk_level":r.get("risk_level",""),
            "maintenance_strategy":rec.get("maintenance_strategy",""),"priority":rec.get("priority",envelope.priority),"resource_decision":status,
            "supervisor_decision":"accepted" if status=="scheduled" else "blocked","work_order_id":work_order_id,
            "decision_explanation":rec.get("recommendation_explanation",status)}
    @staticmethod
    def _business_key(envelope,source)->str:
        diagnosis=source.get("diagnosis",{}).get("final_diagnosis","unknown")
        return f"{envelope.equipment_id}:{diagnosis}"
    async def _alert(self,envelope,level,title,text)->None:
        await self.send_fipa("alert","alert.created",{"alert_id":str(uuid4()),"level":level,"title":title,"message":text,"acknowledged":False},"inform","alerting","indusguard-emergency" if level=="critical" else "indusguard-pipeline",parent=envelope,priority=level if level in {"high","urgent","critical"} else "medium")
    async def _finish(self,envelope,state,payload,success=True)->None:
        self.case_states[envelope.trace_id]=state; self.completed+=1; self.metrics.complete_trace(envelope.trace_id,success)
        await self.send_fipa("historian","pipeline.completed",{"state":state,"decision":payload},"inform","supervision",parent=envelope,priority=envelope.priority)
        self._check_done()
    def _check_done(self)->None:
        if self.stream_finished and self.completed>=self.expected: self.pipeline_done.set()
