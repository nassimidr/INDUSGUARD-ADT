from __future__ import annotations

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from indusguard.dashboard.config import DashboardConfig, load_dashboard_config
from indusguard.dashboard.main import create_app
from indusguard.dashboard.models import AgentHealth, Alert, Asset, SensorMeasurement, WorkOrder


@pytest.fixture()
def app(tmp_path):
    base = load_dashboard_config(); values = deepcopy(base.values)
    values["database"]["url"] = f"sqlite:///{(tmp_path / 'dashboard.db').as_posix()}"
    application = create_app(DashboardConfig(base.root, values))
    with application.state.Session() as session:
        session.add_all([
            Asset(equipment_id="MOTOR-001", equipment_type="motor", display_name="Moteur principal", status="normal", health_score=91),
            SensorMeasurement(timestamp="2026-07-15T12:00:00Z", equipment_id="MOTOR-001", equipment_type="motor", temperature=55, vibration=2.1, health_score=91),
            Alert(alert_id="ALT-001", timestamp="2026-07-15T12:01:00Z", level="high", title="Vibration", message="Seuil approche", acknowledged=False),
            WorkOrder(work_order_id="WO-001", equipment_id="MOTOR-001", priority="high", status="scheduled"),
            AgentHealth(timestamp="2026-07-15T12:00:00Z", agent_id="sensor@localhost", jid="sensor@localhost", status="ready"),
        ]); session.commit()
    return application


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client
