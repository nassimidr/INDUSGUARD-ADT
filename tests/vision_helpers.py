from copy import deepcopy
from pathlib import Path

from PIL import Image

from indusguard.vision.config import VisionConfig, load_vision_config
from indusguard.vision.detector import VisionDetector
from indusguard.vision.model_manager import VisionModelManager


class FakeVisionModel:
    names = {0: "belt_misalignment", 1: "obstacle", 2: "material_accumulation"}

    def __init__(self, predictions=None):
        self.predictions = predictions or [{
            "defect_type": "obstacle",
            "confidence": 0.91,
            "bounding_box": [10, 12, 80, 75],
        }]
        self.calls = 0

    def predict(self, **kwargs):
        self.calls += 1
        return self.predictions


def temporary_vision_config(tmp_path: Path, *, save_json: bool = True) -> VisionConfig:
    base = load_vision_config()
    values = deepcopy(base.values)
    values["model"]["weights_path"] = "models/best.pt"
    values["outputs"]["annotated_directory"] = "outputs/annotated"
    values["outputs"]["predictions_directory"] = "outputs/predictions"
    values["outputs"]["save_json"] = save_json
    values["api"]["allowed_input_directories"] = ["demo"]
    return VisionConfig(tmp_path, values)


def fake_detector(config: VisionConfig, predictions=None):
    model = FakeVisionModel(predictions)
    manager = VisionModelManager(config, model=model, injected_custom_model=True)
    return VisionDetector(config, manager), model


def make_image(path: Path, mode: str = "RGB", size=(120, 90)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    color = 120 if mode == "L" else (30, 50, 70, 255) if mode == "RGBA" else (30, 50, 70)
    Image.new(mode, size, color).save(path)
    return path
