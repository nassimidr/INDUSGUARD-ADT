from indusguard.multi_agent.protocols.contract_net_protocol import evaluate_proposal
def test_accept_proposal(): assert evaluate_proposal({"available":1,"parts_available":1,"deadline_respected":1,"proposal_score":.8})==(True,"accepted")
def test_refuse_missing_part(): assert evaluate_proposal({"available":1,"parts_available":0})==(False,"parts_unavailable")
