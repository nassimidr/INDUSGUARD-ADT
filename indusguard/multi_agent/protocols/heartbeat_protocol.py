REQUIRED_HEARTBEAT_FIELDS=frozenset({"agent_id","status","timestamp","messages_processed","errors_count","queue_size","average_processing_time_ms"})
def validate_heartbeat(payload:dict)->bool:return REQUIRED_HEARTBEAT_FIELDS<=set(payload)
