from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from indusguard.vision.schemas import BoundingBox, VisionDetection, VisionProvenance


def valid_detection(**updates):
    data = {
        "detection_id": "vision-det-1", "equipment_id": "CONVEYOR-001", "camera_id": "camera_01",
        "frame_id": "frame_1", "defect_type": "obstacle", "confidence": 0.8,
        "bounding_box": {"x_min": 1, "y_min": 2, "x_max": 10, "y_max": 12},
        "image_width": 20, "image_height": 20, "original_image_path": "data/vision/demo/a.png",
        "timestamp": datetime.now(timezone.utc), "source": "vision_agent", "trace_id": str(uuid4()),
        "model_name": "yolov8n", "model_version": "phase8a-v1",
        "provenance": VisionProvenance(dataset="test", custom_model_loaded=True),
    }
    data.update(updates)
    return VisionDetection.model_validate(data)


def test_vision_detection_accepts_strict_valid_payload():
    assert valid_detection().defect_type == "obstacle"


@pytest.mark.parametrize("updates", [
    {"confidence": 1.1},
    {"defect_type": "person"},
    {"trace_id": "not-a-uuid"},
    {"timestamp": datetime.now()},
    {"original_image_path": "../secret.png"},
    {"bounding_box": {"x_min": 10, "y_min": 1, "x_max": 3, "y_max": 8}},
])
def test_invalid_vision_payloads_are_rejected(updates):
    with pytest.raises(ValidationError):
        valid_detection(**updates)


def test_box_must_remain_inside_image():
    with pytest.raises(ValidationError):
        valid_detection(bounding_box=BoundingBox(x_min=1, y_min=1, x_max=30, y_max=10))
