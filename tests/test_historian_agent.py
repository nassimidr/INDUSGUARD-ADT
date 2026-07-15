from indusguard.multi_agent.adapters.persistence_adapter import PersistenceAdapter
def test_event_persistence(tmp_path):
    p=PersistenceAdapter(tmp_path);p.event({"timestamp":"t","message_id":"m"});assert (tmp_path/"events.csv").read_text().count("\n")==2
