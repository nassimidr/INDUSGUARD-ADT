"""Reconstruit chronologiquement une trace depuis events.csv."""
import argparse
import pandas as pd

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--trace-id",required=True);args=parser.parse_args()
    events=pd.read_csv("outputs/multi_agent/events.csv");trace=events[events.trace_id==args.trace_id].sort_values("timestamp")
    if trace.empty: raise SystemExit(f"Trace inconnue: {args.trace_id}")
    print(trace.to_string(index=False))
