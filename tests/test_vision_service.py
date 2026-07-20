import json
from uuid import uuid4

from indusguard.vision.schemas import VisionInferenceRequest
from indusguard.vision.service import VisionService
from tests.vision_helpers import fake_detector, make_image, temporary_vision_config


class MemoryRepository:
    def __init__(self): self.items = {}
    def add(self, detection): self.items.setdefault(detection.detection_id, detection); return detection


def test_service_saves_annotation_json_and_preserves_identifiers(tmp_path):
    config = temporary_vision_config(tmp_path)
    image = make_image(tmp_path / "demo" / "frame.png")
    detector, _ = fake_detector(config)
    repository = MemoryRepository()
    trace_id = str(uuid4())
    service = VisionService(config, detector, repository)
    request = VisionInferenceRequest(image_path=str(image), equipment_id="CONVEYOR-001", camera_id="camera_01", trace_id=trace_id)
    first = service.analyze(request)
    second = service.analyze(request)
    assert first.trace_id == trace_id and first.detections[0].equipment_id == "CONVEYOR-001"
    assert first.detections[0].detection_id == second.detections[0].detection_id
    assert len(repository.items) == 1
    assert (tmp_path / first.annotated_image_path).is_file()
    saved = json.loads((tmp_path / first.prediction_json_path).read_text(encoding="utf-8"))
    assert saved["detections"][0]["defect_type"] == "obstacle"


def test_service_can_analyze_directory_without_camera(tmp_path):
    config = temporary_vision_config(tmp_path, save_json=False)
    make_image(tmp_path / "demo" / "one.png"); make_image(tmp_path / "demo" / "two.jpg")
    detector, model = fake_detector(config)
    results = VisionService(config, detector).analyze_directory(
        tmp_path / "demo", equipment_id="CONVEYOR-001", camera_id="camera_demo"
    )
    assert len(results) == 2 and model.calls == 2
