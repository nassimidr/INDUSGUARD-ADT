from indusguard.vision.detector import VisionDetector
from indusguard.vision.model_manager import VisionModelManager
from indusguard.vision.exceptions import VisionModelUnavailableError
from tests.vision_helpers import FakeVisionModel, temporary_vision_config
import pytest


def test_model_is_loaded_once_and_detector_filters_classes(tmp_path):
    config = temporary_vision_config(tmp_path)
    model = FakeVisionModel([
        {"defect_type": "obstacle", "confidence": 0.9, "bounding_box": [1, 2, 30, 40]},
        {"defect_type": "person", "confidence": 0.99, "bounding_box": [1, 2, 30, 40]},
        {"defect_type": "material_accumulation", "confidence": 0.2, "bounding_box": [1, 2, 30, 40]},
    ])
    loads = []
    manager = VisionModelManager(config, loader=lambda weights: loads.append(weights) or model)
    (tmp_path / "models").mkdir(); (tmp_path / "models" / "best.pt").write_bytes(b"weights")
    detector = VisionDetector(config, manager)
    assert [item.defect_type for item in detector.detect(object())] == ["obstacle"]
    detector.detect(object())
    assert len(loads) == 1 and manager.custom_model_loaded is True


def test_demo_fallback_is_explicit_and_coco_class_is_not_remapped(tmp_path):
    config = temporary_vision_config(tmp_path)
    fallback = FakeVisionModel([{"defect_type": "person", "confidence": 0.99, "bounding_box": [1, 2, 30, 40]}])
    fallback.names = {0: "person"}
    manager = VisionModelManager(config, loader=lambda weights: fallback)
    assert VisionDetector(config, manager).detect(object()) == []
    assert manager.custom_model_loaded is False and manager.technical_fallback is True


def test_model_unavailable_is_explicit_outside_demo_mode(tmp_path):
    config = temporary_vision_config(tmp_path)
    config.values["mode"] = "camera"
    with pytest.raises(VisionModelUnavailableError, match="weights not found"):
        VisionModelManager(config).load()
