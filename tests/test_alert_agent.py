import pytest
from indusguard.multi_agent.notifications import ConsoleNotificationChannel,EmailNotificationChannel
def test_console_channel(capsys): ConsoleNotificationChannel().notify({"level":"high","title":"T","message":"M"});assert "[HIGH]" in capsys.readouterr().out
def test_email_is_future_interface():
    with pytest.raises(NotImplementedError):EmailNotificationChannel().notify({})
