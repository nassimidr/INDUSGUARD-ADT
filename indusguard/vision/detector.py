from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import VisionConfig
from .model_manager import VisionModelManager


@dataclass(frozen=True)
class RawVisionDetection:
    defect_type: str
    confidence: float
    box: tuple[float, float, float, float]


class VisionDetector:
    def __init__(self, config: VisionConfig, manager: VisionModelManager) -> None:
        self.config = config
        self.manager = manager

    def detect(self, image: Any) -> list[RawVisionDetection]:
        predictions = self.manager.predict(image)
        threshold = float(self.config.values["model"]["confidence_threshold"])
        if predictions and isinstance(predictions[0], dict):
            return self._from_dicts(predictions, threshold)
        detections: list[RawVisionDetection] = []
        for result in predictions or []:
            names = getattr(result, "names", getattr(self.manager.load(), "names", {}))
            for box in getattr(result, "boxes", []) or []:
                class_id = int(self._scalar(box.cls))
                name = names[class_id] if isinstance(names, (list, tuple)) else names.get(class_id, str(class_id))
                confidence = float(self._scalar(box.conf))
                coordinates = tuple(float(value) for value in box.xyxy[0].tolist())
                if name in self.config.classes and confidence >= threshold:
                    detections.append(RawVisionDetection(name, confidence, coordinates))
        return detections

    def _from_dicts(self, predictions: list[dict], threshold: float) -> list[RawVisionDetection]:
        output = []
        for item in predictions:
            name = str(item["defect_type"])
            confidence = float(item["confidence"])
            coordinates = tuple(float(value) for value in item["bounding_box"])
            if name in self.config.classes and confidence >= threshold:
                output.append(RawVisionDetection(name, confidence, coordinates))
        return output

    @staticmethod
    def _scalar(value: Any) -> float:
        if hasattr(value, "item"):
            return float(value.item())
        if isinstance(value, (list, tuple)):
            return float(value[0])
        return float(value)
