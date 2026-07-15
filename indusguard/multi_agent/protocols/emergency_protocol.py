def is_critical(*,severity:str="",risk_level:str="",predicted_rul_steps:float=999999,diagnosis:str="",strategy:str="",critical_rul:float=10)->bool:
    return severity=="critical" or risk_level=="critical" or predicted_rul_steps<=critical_rul or diagnosis=="cascade_failure" or strategy=="emergency_shutdown"
