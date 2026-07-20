from uuid import uuid4

from indusguard.vision.model_manager import VisionModelManager
from tests.vision_helpers import FakeVisionModel, make_image, temporary_vision_config
from tests.dashboard.conftest import app, client  # noqa: F401


def configure_fake_vision(app, tmp_path):
    config = temporary_vision_config(tmp_path)
    model = FakeVisionModel()
    manager = VisionModelManager(config, model=model, injected_custom_model=True)
    from indusguard.vision.detector import VisionDetector
    app.state.vision_config = config; app.state.vision_manager = manager; app.state.vision_detector = VisionDetector(config, manager)
    return make_image(tmp_path / "demo" / "api.png")


def test_vision_health_analyze_list_detail_and_images(app, client, tmp_path):
    image = configure_fake_vision(app, tmp_path)
    health = client.get("/api/v1/vision/health")
    assert health.status_code == 200 and health.json()["data"]["custom_model_loaded"] is True
    trace_id = str(uuid4())
    response = client.post("/api/v1/vision/analyze", json={
        "image_path": str(image), "equipment_id": "CONVEYOR-001", "camera_id": "camera_01", "trace_id": trace_id,
    })
    assert response.status_code == 200, response.text
    detection = response.json()["data"]["detections"][0]
    assert detection["trace_id"] == trace_id
    listed = client.get("/api/v1/vision/detections?defect_type=obstacle").json()["data"]
    assert len(listed) == 1
    assert client.get(f"/api/v1/vision/detections/{detection['detection_id']}").status_code == 200
    assert client.get(f"/api/v1/vision/detections/{detection['detection_id']}/image/annotated").status_code == 200
    assert len(client.get("/api/v1/assets/CONVEYOR-001/vision-detections").json()["data"]) == 1


def test_vision_api_rejects_arbitrary_paths_and_missing_detection(app, client, tmp_path):
    configure_fake_vision(app, tmp_path)
    response = client.post("/api/v1/vision/analyze", json={
        "image_path": str(tmp_path / "outside.png"), "equipment_id": "CONVEYOR-001", "camera_id": "camera_01",
    })
    assert response.status_code == 422
    assert client.get("/api/v1/vision/detections/missing").status_code == 404


def test_vision_websocket_receives_created_detection(app, client, tmp_path):
    image = configure_fake_vision(app, tmp_path)
    with client.websocket_connect("/ws/dashboard") as socket:
        socket.send_json({"event_types": ["vision.detection.created"]})
        assert socket.receive_json()["event"] == "subscribed"
        response = client.post("/api/v1/vision/analyze", json={
            "image_path": str(image), "equipment_id": "CONVEYOR-001", "camera_id": "camera_01",
        })
        assert response.status_code == 200
        event = socket.receive_json()
        assert event["event"] == "vision.detection.created"
        assert event["data"]["equipment_id"] == "CONVEYOR-001"
