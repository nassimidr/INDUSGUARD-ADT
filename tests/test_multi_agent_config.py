import os
from indusguard.multi_agent.config import load_multi_agent_config

def test_config_has_ten_local_agents_including_vision():
    c=load_multi_agent_config();assert len(c.agents)==10;assert c.agents["vision"]["jid"]=="vision@localhost";assert all(v["jid"].endswith("@localhost") for v in c.agents.values())
def test_config_default_embedded(): assert load_multi_agent_config().mode=="embedded"
def test_password_environment(monkeypatch): monkeypatch.setenv("INDUSGUARD_AGENT_PASSWORD","secret-test");assert load_multi_agent_config().password=="secret-test"
