from __future__ import annotations
from datetime import datetime,timezone
from typing import Any,Literal
from pydantic import BaseModel,Field,ConfigDict

def timestamp()->str:return datetime.now(timezone.utc).isoformat()
class WorkOrderStatusUpdate(BaseModel):status:Literal["proposed","scheduled","in_progress","completed","blocked","cancelled"]
class SystemRunStart(BaseModel):
    scenario:str;mode:Literal["embedded","external"]="embedded";speed:float=Field(20,gt=0,le=100000);max_measurements:int=Field(1000,gt=0,le=10000);equipment_id:str|None=None
class DashboardEvent(BaseModel):
    event_id:int|None=None;event_type:str;timestamp:str=Field(default_factory=timestamp);trace_id:str|None=None;equipment_id:str|None=None;priority:str="medium";payload:dict[str,Any]=Field(default_factory=dict)
class Subscription(BaseModel):event_types:list[str]=Field(default_factory=list);equipment_id:str|None=None;last_event_id:int|None=None
class ApiMeta(BaseModel):timestamp:str=Field(default_factory=timestamp);timezone:str="Africa/Casablanca";page:int|None=None;page_size:int|None=None;total:int|None=None;pages:int|None=None
class ORMModel(BaseModel):model_config=ConfigDict(from_attributes=True)
