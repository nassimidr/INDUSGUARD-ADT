"""Lance la Phase 6 avec PyJabber embarqué ou un XMPP externe."""
from __future__ import annotations
import argparse,json,os
import spade
from indusguard.multi_agent import MultiAgentRuntime,load_multi_agent_config

def arguments():
    p=argparse.ArgumentParser(description="INDUSGUARD-ADT Phase 6 SPADE")
    p.add_argument("--scenario",default="normal",choices=["normal","bearing_wear","pump_cavitation","emergency","resource_unavailable","part_unavailable","agent_unavailable","duplicate"])
    p.add_argument("--mode",choices=["embedded","external"])
    p.add_argument("--speed",type=float)
    p.add_argument("--max-measurements",type=int)
    p.add_argument("--equipment-id")
    return p.parse_args()

async def main(args):
    runtime=MultiAgentRuntime(load_multi_agent_config(),scenario=args.scenario,speed=args.speed,max_measurements=args.max_measurements,equipment_id=args.equipment_id)
    print(json.dumps(await runtime.run(),ensure_ascii=False,indent=2))

if __name__=="__main__":
    args=arguments()
    if args.mode: os.environ["INDUSGUARD_XMPP_MODE"]=args.mode
    mode=os.environ.get("INDUSGUARD_XMPP_MODE","embedded")
    spade.run(main(args),embedded_xmpp_server=mode=="embedded")
