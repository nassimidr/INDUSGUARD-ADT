PIPELINE={"sensor.measurement":"diagnosis.request","diagnosis.request":"rul.request","rul.request":"maintenance.request","maintenance.request":"resource.call_for_proposal"}
def next_message_type(message_type:str)->str|None:return PIPELINE.get(message_type)
