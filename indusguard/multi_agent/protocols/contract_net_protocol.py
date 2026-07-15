"""Règle déterministe d'évaluation des propositions Contract Net."""
def evaluate_proposal(proposal:dict)->tuple[bool,str]:
    if not proposal.get("available"): return False,"resources_unavailable"
    if not proposal.get("parts_available"): return False,"parts_unavailable"
    if not proposal.get("deadline_respected"): return False,"deadline_conflict"
    if float(proposal.get("proposal_score",0))<0.5:return False,"proposal_score_too_low"
    return True,"accepted"
