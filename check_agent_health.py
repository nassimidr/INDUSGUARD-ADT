"""Affiche le dernier état connu de chaque agent."""
from pathlib import Path
import pandas as pd

if __name__=="__main__":
    path=Path("outputs/multi_agent/agent_health.csv")
    if not path.exists(): raise SystemExit("Aucun heartbeat disponible; lancez d'abord le système multi-agents.")
    data=pd.read_csv(path).sort_values("timestamp").groupby("agent_id",as_index=False).tail(1)
    columns=["agent_id","status","last_heartbeat","messages_processed","errors_count","queue_size","average_processing_time_ms"]
    print(data[columns].rename(columns={"agent_id":"agent"}).to_string(index=False))
