import subprocess,sys
from pathlib import Path
import pytest
@pytest.mark.integration
def test_real_xmpp_message_with_embedded_pyjabber():
    probe=Path(__file__).with_name("spade_integration_probe.py");result=subprocess.run([sys.executable,str(probe)],capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stderr
    assert 'REAL_XMPP_OK' in result.stdout and '"value": 42' in result.stdout
