from indusguard.multi_agent.dead_letter import DeadLetterQueue
from indusguard.multi_agent.schemas import AgentMessage
def test_dead_letter_round_trip(tmp_path):
    q=DeadLetterQueue(tmp_path/"dlq.jsonl");m=AgentMessage("processing.failure","a@localhost","b@localhost",{});q.add(m,"b",ValueError("bad"));assert q.read()[0]["message_id"]==m.message_id
