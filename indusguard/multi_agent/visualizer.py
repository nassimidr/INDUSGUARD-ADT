"""Douze figures de supervision Phase 6, toujours fermées après sauvegarde."""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

def _save(fig,path): fig.tight_layout();fig.savefig(path,dpi=130);plt.close(fig)
def _bar(series,title,path,ylabel="count"):
    if series.empty: series=pd.Series({"none":0.0})
    series=pd.to_numeric(series,errors="coerce").fillna(0.0)
    fig,ax=plt.subplots(figsize=(8,4)); series.plot(kind="bar",ax=ax,color="#2878b5");ax.set_title(title);ax.set_ylabel(ylabel);_save(fig,path)
def create_multi_agent_plots(output_directory:str|Path,plots_directory:str|Path)->list[Path]:
    out=Path(output_directory);dest=Path(plots_directory);dest.mkdir(parents=True,exist_ok=True)
    metrics=json.loads((out/"multi_agent_metrics.json").read_text(encoding="utf-8")) if (out/"multi_agent_metrics.json").exists() else {}
    events=pd.read_csv(out/"events.csv") if (out/"events.csv").exists() else pd.DataFrame()
    decisions=pd.read_csv(out/"decisions.csv") if (out/"decisions.csv").exists() else pd.DataFrame()
    alerts=pd.read_csv(out/"alerts.csv") if (out/"alerts.csv").exists() else pd.DataFrame()
    health=pd.read_csv(out/"agent_health.csv") if (out/"agent_health.csv").exists() else pd.DataFrame()
    paths=[]
    specs=[
      (pd.Series(metrics.get("messages_by_agent",{"none":0})),"Messages traités par agent","01_messages_by_agent.png"),
      (pd.Series(metrics.get("messages_by_type",{"none":0})),"Messages par type","02_messages_by_type.png"),
      (pd.Series(metrics.get("average_processing_time_by_agent_ms",{"none":0})),"Latence moyenne par agent","03_average_latency_by_agent.png"),
      (pd.Series({"P50":metrics.get("latency_p50_ms",0),"P95":metrics.get("latency_p95_ms",0)}),"Latences bout en bout","04_latency_percentiles.png"),
      (pd.Series({"success":metrics.get("pipeline_success_rate",0),"failure":1-metrics.get("pipeline_success_rate",0)}),"Taux de succès du pipeline","05_pipeline_success.png"),
      (pd.Series({k:metrics.get(k,0) for k in ["errors","timeouts","retries"]}),"Erreurs, timeouts et retries","06_reliability.png"),
      ((health["status"].value_counts() if not health.empty else pd.Series({"no heartbeat":0})),"État des agents","07_agent_health.png"),
      ((decisions["priority"].value_counts() if not decisions.empty else pd.Series({"none":0})),"Décisions par priorité","09_decisions_by_priority.png"),
      ((alerts["level"].value_counts() if not alerts.empty else pd.Series({"none":0})),"Alertes par niveau","10_alerts_by_level.png"),
      (pd.Series({"accepted":metrics.get("resource_proposals_accepted",0),"refused":metrics.get("resource_proposals_refused",0)+metrics.get("resource_proposals_rejected",0)}),"Propositions de ressources","11_resource_proposals.png"),
    ]
    for series,title,name in specs: path=dest/name;_bar(series,title,path);paths.append(path)
    fig,ax=plt.subplots(figsize=(10,4))
    if not events.empty:
        trace=events[events.trace_id==events.trace_id.iloc[0]].reset_index();ax.scatter(trace.index,trace.processing_time_ms.fillna(0));ax.set_xticks(trace.index);ax.set_xticklabels(trace.message_type,rotation=75,ha="right",fontsize=7)
    ax.set_title("Chronologie d'une trace");path=dest/"08_trace_timeline.png";_save(fig,path);paths.append(path)
    fig,ax=plt.subplots(figsize=(10,5))
    if not events.empty:
        links=events.groupby(["sender_agent","receiver_agent"]).size();nodes=sorted(set(events.sender_agent)|set(events.receiver_agent));positions={n:i for i,n in enumerate(nodes)}
        for (sender,receiver),count in links.items(): ax.annotate("",xy=(positions[receiver],0),xytext=(positions[sender],0),arrowprops={"arrowstyle":"->","lw":max(1,min(5,count/10)),"alpha":.5})
        ax.scatter(range(len(nodes)),[0]*len(nodes),s=300);ax.set_xticks(range(len(nodes)));ax.set_xticklabels(nodes,rotation=35,ha="right",fontsize=8)
    ax.set_yticks([]);ax.set_title("Graphe des communications");path=dest/"12_communication_graph.png";_save(fig,path);paths.append(path)
    return paths
