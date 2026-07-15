"""Agent source CSV ordonné et accéléré."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pandas as pd
from spade.behaviour import OneShotBehaviour
from spade.message import Message

from .base_indusguard_agent import BaseIndusGuardAgent


class SensorStreamBehaviour(OneShotBehaviour):
    async def run(self)->None: await self.agent.publish_stream()


class SensorAgent(BaseIndusGuardAgent):
    def __init__(self,*args,scenario:str|None=None,speed:float|None=None,max_measurements:int|None=None,equipment_id:str|None=None,**kwargs)->None:
        super().__init__("sensor",*args,**kwargs); self.scenario=scenario; self.speed=speed; self.maximum=max_measurements; self.equipment_id=equipment_id
        self.stream_done=asyncio.Event(); self.sent_ids:set[str]=set()

    async def setup(self)->None:
        await self.common_setup([]); self.add_behaviour(SensorStreamBehaviour())

    def _load(self)->pd.DataFrame:
        simulation=self.config.values["simulation"]; path=self.config.root/simulation["input_path"]
        if not path.is_file(): raise FileNotFoundError(path)
        data=pd.read_csv(path).sort_values(["timestamp","equipment_id"]).iloc[int(simulation.get("start_row",0)):]
        scenario=self.scenario or simulation.get("scenario_filter")
        aliases={"normal":"scenario_1_normal","bearing_wear":"scenario_2_bearing","pump_cavitation":"scenario_4_pump","emergency":"scenario_5_cascade",
            "resource_unavailable":"scenario_2_bearing","part_unavailable":"scenario_2_bearing","agent_unavailable":"scenario_2_bearing","duplicate":"scenario_1_normal","benchmark":"scenario_1_normal"}
        if scenario and scenario!="all":
            data=data[data["scenario_id"]==aliases.get(scenario,scenario)]
        equipment=self.equipment_id or simulation.get("equipment_filter")
        if equipment: data=data[data["equipment_id"].str.lower()==str(equipment).lower()]
        maximum=self.maximum if self.maximum is not None else simulation["max_measurements"]
        if self.scenario=="benchmark" and 0<len(data)<int(maximum):
            copies=[]
            for index in range((int(maximum)+len(data)-1)//len(data)):
                copy=data.copy();copy["timestamp"]=(pd.to_datetime(copy["timestamp"])+pd.to_timedelta(index,unit="D")).astype(str);copies.append(copy)
            data=pd.concat(copies,ignore_index=True)
        return data.tail(int(maximum)) if self.scenario=="emergency" else data.head(int(maximum))

    async def publish_stream(self)->None:
        try:
            data=self._load(); count=len(data)
            await self.send_fipa("supervisor","sensor.stream_started",{"measurement_count":count,"scenario":self.scenario or "configured"},"inform","sensor-monitoring")
            speed=float(self.speed or self.config.values["simulation"]["speed_factor"]); mode=self.config.values["simulation"]["mode"]
            for position,(_,row) in enumerate(data.iterrows()):
                payload={k:(None if pd.isna(v) else v.item() if hasattr(v,"item") else v) for k,v in row.to_dict().items()}
                dedup=f"{payload['equipment_id']}:{payload.get('timestamp')}"
                if dedup in self.sent_ids: self.metrics.increment("messages_duplicated"); continue
                self.sent_ids.add(dedup)
                envelope=await self.send_fipa("anomaly","sensor.measurement",payload,"inform","sensor-monitoring",equipment_id=str(payload["equipment_id"]),equipment_type=str(payload["equipment_type"]),priority="medium")
                if self.scenario=="duplicate" and position==0:
                    duplicate=Message(to=envelope.target_agent,body=envelope.to_json(),thread=envelope.conversation_id);duplicate.sender=str(self.jid)
                    metadata={"performative":"inform","ontology":"sensor-monitoring","protocol":"indusguard-pipeline","conversation-id":envelope.conversation_id,
                        "language":"json-utf8","message-type":envelope.message_type,"schema-version":envelope.schema_version,"priority":envelope.priority,
                        "trace-id":envelope.trace_id,"correlation-id":envelope.correlation_id,"message-id":envelope.message_id}
                    for key,value in metadata.items():duplicate.set_metadata(key,value)
                    duplicate.prepare(self.client).send();self.metrics.sent(envelope.message_type,self.agent_name,envelope.trace_id)
                if mode in {"accelerated","realtime_simulation"}: await asyncio.sleep(max(0.0,1.0/max(speed,1.0)))
            await self.send_fipa("supervisor","sensor.stream_completed",{"measurement_count":count},"inform","sensor-monitoring")
        finally: self.stream_done.set()

    async def process(self,envelope,message)->None: return None
