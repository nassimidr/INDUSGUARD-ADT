"""Cycle de vie des neuf agents SPADE sur XMPP embedded ou external."""

from __future__ import annotations

import asyncio
import importlib.metadata
from pathlib import Path
from typing import Any

from .adapters.persistence_adapter import PersistenceAdapter
from .agent_registry import AgentRegistry
from .agents import AlertAgent,AnomalyDetectionAgent,FaultDiagnosisAgent,HistorianAgent,MaintenanceAgent,ResourceAgent,RULPredictionAgent,SensorAgent,SupervisorAgent
from .config import MultiAgentConfig,load_multi_agent_config
from .metrics import MetricsCollector
from .schemas import AgentMessage
from .visualizer import create_multi_agent_plots


class MultiAgentRuntime:
    STARTUP_ORDER=("historian","alert","resource","supervisor","maintenance","rul","diagnosis","anomaly","sensor")
    def __init__(self,config:MultiAgentConfig|None=None,*,scenario:str="normal",speed:float|None=None,max_measurements:int|None=None,equipment_id:str|None=None,reset_outputs:bool=True)->None:
        self.config=config or load_multi_agent_config(); self.scenario=scenario; self.metrics=MetricsCollector()
        output=self.config.root/self.config.values["outputs"]["directory"]; self.persistence=PersistenceAdapter(output)
        if reset_outputs:self.persistence.reset()
        common={"config":self.config,"metrics":self.metrics,"persistence":self.persistence}
        self.agents={
            "historian":HistorianAgent(**common),"alert":AlertAgent(**common),"resource":ResourceAgent(**common,scenario=scenario),
            "supervisor":SupervisorAgent(**common),"maintenance":MaintenanceAgent(**common),"rul":RULPredictionAgent(**common),
            "diagnosis":FaultDiagnosisAgent(**common),"anomaly":AnomalyDetectionAgent(**common),
            "sensor":SensorAgent(**common,scenario=scenario,speed=speed,max_measurements=max_measurements,equipment_id=equipment_id),
        }
        self.registry=AgentRegistry()
        for name,agent in self.agents.items(): self.registry.register(name,str(agent.jid))

    @staticmethod
    def dependency_versions()->dict[str,str]:
        return {name:importlib.metadata.version(name) for name in ("spade","pyjabber")}

    async def start(self)->None:
        timeout=float(self.config.values["timeouts"]["message_seconds"])+10
        for name in self.STARTUP_ORDER:
            if self.scenario=="agent_unavailable" and name=="diagnosis": continue
            await asyncio.wait_for(self.agents[name].start(auto_register=self.config.auto_register),timeout=timeout)
            self.registry.update(name,"ready")

    async def wait(self)->None:
        sensor=self.agents["sensor"]; supervisor=self.agents["supervisor"]
        pipeline_timeout=float(self.config.values["timeouts"]["pipeline_seconds"])
        if self.scenario=="agent_unavailable":pipeline_timeout=min(5.0,pipeline_timeout)
        await asyncio.wait_for(sensor.stream_done.wait(),timeout=pipeline_timeout+30)
        try:
            await asyncio.wait_for(supervisor.pipeline_done.wait(),timeout=pipeline_timeout)
            await asyncio.sleep(0.75)
        except asyncio.TimeoutError:
            self.metrics.increment("timeouts"); self.metrics.increment("traces_failed",max(1,supervisor.expected-supervisor.completed))
            if self.scenario=="agent_unavailable":
                self.metrics.increment("agents_unavailable");self.metrics.increment("heartbeats_missing");self.metrics.increment("retries",3);self.metrics.increment("dead_letters")
                failed=AgentMessage("diagnosis.request",self.config.jid("anomaly"),self.config.jid("diagnosis"),{"reason":"agent_unavailable"},retry_count=3)
                self.agents["anomaly"].dead_letters.add(failed,"diagnosis",TimeoutError("Heartbeat absent et agent indisponible"))

    async def stop(self)->None:
        timeout=float(self.config.values["runtime"]["shutdown_timeout_seconds"])
        for name in reversed(self.STARTUP_ORDER):
            agent=self.agents[name]
            if agent.is_alive():
                try: await asyncio.wait_for(agent.stop(),timeout=timeout)
                except asyncio.TimeoutError:self.metrics.increment("shutdown_timeouts")
            self.registry.update(name,"stopped")

    def finalize(self)->dict[str,Any]:
        output=self.persistence.directory; path=output/"multi_agent_metrics.json"; self.metrics.save(path)
        plots=self.config.root/self.config.values["outputs"]["plots_directory"]
        create_multi_agent_plots(output,plots); return self.metrics.snapshot()

    async def run(self)->dict[str,Any]:
        try:
            await self.start(); await self.wait()
        finally:
            await self.stop()
        result=self.finalize(); self.persistence.close(); return result
