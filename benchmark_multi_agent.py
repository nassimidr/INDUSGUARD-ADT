"""Benchmark académique de stabilité sur au moins 1 000 mesures."""
from __future__ import annotations
import json,time
import spade
from indusguard.multi_agent import MultiAgentRuntime

async def benchmark():
    started=time.perf_counter(); runtime=MultiAgentRuntime(scenario="benchmark",speed=100000,max_measurements=1000)
    metrics=await runtime.run(); metrics["benchmark_wall_seconds"]=round(time.perf_counter()-started,3)
    print(json.dumps({k:metrics.get(k,0) for k in ["benchmark_wall_seconds","messages_per_second","average_processing_time_ms","latency_p50_ms","latency_p95_ms","errors","messages_lost","retries"]},indent=2))

if __name__=="__main__": spade.run(benchmark(),embedded_xmpp_server=True)
