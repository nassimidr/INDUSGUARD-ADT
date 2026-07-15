from __future__ import annotations

import pytest


@pytest.mark.parametrize("path", [
    "/api/v1/health", "/api/v1/config", "/api/v1/overview", "/api/v1/assets",
    "/api/v1/measurements", "/api/v1/anomalies", "/api/v1/diagnoses", "/api/v1/rul",
    "/api/v1/maintenance/recommendations", "/api/v1/work-orders", "/api/v1/agents",
    "/api/v1/alerts", "/api/v1/traces", "/api/v1/system-runs",
])
def test_collection_routes_return_envelope(client, path):
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert "data" in response.json()


def test_health_reports_database(client):
    data = client.get("/api/v1/health").json()["data"]
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_asset_detail_and_latest(client):
    assert client.get("/api/v1/assets/MOTOR-001").json()["data"]["health_score"] == 91
    assert client.get("/api/v1/assets/MOTOR-001/latest").json()["data"]["measurement"]["temperature"] == 55


def test_missing_asset_is_404(client):
    assert client.get("/api/v1/assets/UNKNOWN").status_code == 404


def test_work_order_status_update(client):
    response = client.patch("/api/v1/work-orders/WO-001/status", json={"status": "in_progress"})
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "in_progress"


def test_work_order_rejects_unknown_status(client):
    assert client.patch("/api/v1/work-orders/WO-001/status", json={"status": "unsafe"}).status_code == 422


def test_alert_acknowledgement(client):
    response = client.patch("/api/v1/alerts/ALT-001/acknowledge")
    assert response.status_code == 200
    assert response.json()["data"]["acknowledged"] is True


def test_websocket_subscription(client):
    with client.websocket_connect("/ws/dashboard") as socket:
        socket.send_json({"event_types": ["alert.created"]})
        message = socket.receive_json()
        assert message == {"event": "subscribed", "data": {"event_types": ["alert.created"]}}
