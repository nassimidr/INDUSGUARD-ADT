"""Compteurs et latences thread-safe dans la boucle asyncio."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import time
from typing import Any


class MetricsCollector:
    def __init__(self) -> None:
        self.started = time.perf_counter(); self.counters: Counter[str] = Counter()
        self.by_type: Counter[str] = Counter(); self.by_agent: Counter[str] = Counter()
        self.latencies: defaultdict[str, list[float]] = defaultdict(list)
        self.trace_started: dict[str, float] = {}; self.trace_latencies: list[float] = []

    def sent(self, message_type: str, sender: str, trace_id: str) -> None:
        self.counters["total_messages"] += 1; self.by_type[message_type] += 1; self.by_agent[sender] += 1
        self.trace_started.setdefault(trace_id, time.perf_counter())

    def processed(self, agent: str, elapsed_ms: float) -> None:
        self.counters["messages_successful"] += 1; self.latencies[agent].append(float(elapsed_ms))

    def increment(self, name: str, amount: int = 1) -> None:
        self.counters[name] += amount

    def complete_trace(self, trace_id: str, success: bool = True) -> None:
        start = self.trace_started.pop(trace_id, None)
        if start is not None: self.trace_latencies.append((time.perf_counter() - start) * 1000)
        self.counters["traces_completed" if success else "traces_failed"] += 1

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float:
        if not values: return 0.0
        ordered = sorted(values); index = min(len(ordered)-1, max(0, math.ceil(percentile*len(ordered))-1))
        return ordered[index]

    def snapshot(self) -> dict[str, Any]:
        elapsed = max(time.perf_counter() - self.started, 1e-9)
        all_latencies = [x for values in self.latencies.values() for x in values]
        completed = self.counters["traces_completed"]; failed = self.counters["traces_failed"]
        required=("total_messages","messages_successful","errors","messages_duplicated","messages_rejected","timeouts","retries","dead_letters",
            "anomalies_detected","diagnostics_produced","rul_predictions_produced","recommendations_produced","resource_proposals",
            "resource_proposals_accepted","resource_proposals_rejected","resource_proposals_refused","work_orders_created","interventions_scheduled",
            "interventions_blocked","critical_alerts","vision_detections_produced","heartbeats_received","heartbeats_missing","agents_unavailable","traces_completed","traces_failed")
        return {
            **{name:self.counters[name] for name in required}, **dict(self.counters), "messages_by_type": dict(self.by_type),
            "messages_by_agent": dict(self.by_agent),
            "average_processing_time_by_agent_ms": {k: round(sum(v)/len(v),3) for k,v in self.latencies.items() if v},
            "average_processing_time_ms": round(sum(all_latencies)/len(all_latencies),3) if all_latencies else 0.0,
            "end_to_end_average_latency_ms": round(sum(self.trace_latencies)/len(self.trace_latencies),3) if self.trace_latencies else 0.0,
            "latency_p50_ms": round(self._percentile(self.trace_latencies, .50),3),
            "latency_p95_ms": round(self._percentile(self.trace_latencies, .95),3),
            "messages_per_second": round(self.counters["total_messages"]/elapsed,3),
            "pipeline_success_rate": round(completed/max(completed+failed,1),4),
            "messages_lost": max(0,self.counters["total_messages"]-self.counters["messages_successful"]),
            "duration_seconds": round(elapsed,3),
        }

    def save(self, path: str | Path) -> Path:
        target=Path(path); target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(self.snapshot(),ensure_ascii=False,indent=2),encoding="utf-8"); return target
