from indusguard.multi_agent.runtime import MultiAgentRuntime
def test_runtime_order_and_dependencies(): assert MultiAgentRuntime.STARTUP_ORDER[0]=="historian" and MultiAgentRuntime.dependency_versions()["spade"].startswith("4.1.")
