"""Participant Contract Net réutilisant inventaire et ressources Phase 5."""

from __future__ import annotations

from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from indusguard.maintenance_planning.spare_parts import SparePartsManager
from .base_indusguard_agent import BaseIndusGuardAgent


class ResourceAgent(BaseIndusGuardAgent):
    def __init__(self,*args,scenario:str|None=None,**kwargs)->None:
        super().__init__("resource",*args,**kwargs); self.scenario=scenario
        self.resources=yaml.safe_load((self.config.root/"configs/maintenance_resources.yaml").read_text(encoding="utf-8"))
        self.parts=SparePartsManager(self.resources); self.proposals:dict[str,dict[str,Any]]={}; self.reservations:dict[str,dict[str,Any]]={}; self.held_parts:Counter[str]=Counter()
    async def setup(self)->None: await self.common_setup(["resource.call_for_proposal","resource.acceptance","resource.rejection"])
    async def process(self,envelope,message)->None:
        if envelope.message_type=="resource.call_for_proposal": await self._cfp(envelope)
        elif envelope.message_type=="resource.acceptance": await self._accept(envelope)
        else: await self._reject(envelope)
    async def _cfp(self,envelope)->None:
        cfp=envelope.payload["cfp"]; skills=tuple(cfp["required_skills"]); parts=tuple(cfp["required_parts"])
        missing_resources=[s for s in skills if int(self.resources["technicians"].get(s,{}).get("available_count",0))<1]
        missing_parts=tuple(part for part in parts if self.parts.inventory.get(part,0)-self.held_parts[part]<1)
        if self.scenario=="resource_unavailable": missing_resources=list(skills or ["mechanical_technician"])
        if self.scenario=="part_unavailable": missing_parts=parts or ("industrial_bearing",)
        if missing_resources or missing_parts:
            refusal={"refusal_reason":"Ressources ou pièces indisponibles","missing_resources":missing_resources,
                "missing_parts":list(missing_parts),"deadline_conflict":False,"source":envelope.payload}
            self.metrics.increment("resource_proposals_refused")
            await self.send_fipa("supervisor","resource.refusal",refusal,"refuse","resource-allocation","fipa-contract-net",parent=envelope,priority=envelope.priority); return
        start=datetime.fromisoformat(str(cfp["recommended_start"])); end=start+timedelta(hours=float(cfp["estimated_duration_hours"])); deadline=datetime.fromisoformat(str(cfp["recommended_deadline"]))
        proposal_id=str(uuid4()); proposal={"proposal_id":proposal_id,"available":True,"proposed_start":start.isoformat(),"proposed_end":end.isoformat(),
            "assigned_resources":[f"{skill}_1" for skill in skills],"reserved_parts":list(parts),"parts_available":True,
            "deadline_respected":end<=deadline,"estimated_cost":float(cfp["estimated_cost"]),"proposal_score":1.0 if end<=deadline else 0.4}
        for part in parts:self.held_parts[part]+=1
        self.proposals[proposal_id]={"proposal":proposal,"source":envelope.payload,"parent":envelope}; self.metrics.increment("resource_proposals")
        await self.send_fipa("supervisor","resource.proposal",{**proposal,"source":envelope.payload},"propose","resource-allocation","fipa-contract-net",parent=envelope,priority=envelope.priority)
    async def _accept(self,envelope)->None:
        proposal_id=str(envelope.payload["proposal_id"]); stored=self.proposals.get(proposal_id)
        if not stored:
            await self.send_fipa("supervisor","resource.failure",{"proposal_id":proposal_id,"reason":"Proposition inconnue"},"failure","resource-allocation","fipa-contract-net",parent=envelope); return
        if proposal_id not in self.reservations:
            held=tuple(stored["proposal"]["reserved_parts"])
            for part in held:self.held_parts[part]=max(0,self.held_parts[part]-1)
            self.parts.reserve(held); self.reservations[proposal_id]=stored["proposal"]
        self.metrics.increment("resource_proposals_accepted")
        await self.send_fipa("supervisor","resource.confirmation",{**stored["proposal"],"source":stored["source"]},"confirm","resource-allocation","fipa-contract-net",parent=envelope,priority=envelope.priority)
    async def _reject(self,envelope)->None:
        proposal_id=str(envelope.payload["proposal_id"]); stored=self.proposals.pop(proposal_id,None)
        if stored:
            for part in stored["proposal"]["reserved_parts"]:self.held_parts[part]=max(0,self.held_parts[part]-1)
        self.metrics.increment("resource_proposals_rejected")
        await self.emit_historian(envelope,"resource_proposal_rejected",{"proposal_id":proposal_id})
