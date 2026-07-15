from datetime import datetime,timezone,timedelta
from indusguard.multi_agent.health_monitor import HealthMonitor
def test_unavailable_agent():
    h=HealthMonitor(5);h.record({"agent_id":"x@localhost","timestamp":datetime.now(timezone.utc).isoformat()});assert h.unavailable(datetime.now(timezone.utc)+timedelta(seconds=6))==["x@localhost"]
