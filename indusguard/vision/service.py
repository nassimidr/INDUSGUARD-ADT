from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from uuid import UUID, uuid4, uuid5

from .config import VisionConfig
from .constants import DATASET_NAME
from .detector import RawVisionDetection, VisionDetector
from .preprocessing import load_and_preprocess_image
from .repository import VisionDetectionRepository
from .schemas import (
    BoundingBox,
    VisionDetection,
    VisionInferenceRequest,
    VisionInferenceResponse,
    VisionProvenance,
)
from .visualizer import save_annotated_image


class VisionService:
    def __init__(
        self,
        config: VisionConfig,
        detector: VisionDetector,
        repository: VisionDetectionRepository | None = None,
    ) -> None:
        self.config = config
        self.detector = detector
        self.repository = repository

    def analyze(self, request: VisionInferenceRequest, *, source: str = "vision_agent") -> VisionInferenceResponse:
        started = time.perf_counter()
        trace_id = request.trace_id or str(uuid4())
        UUID(trace_id)
        processed = load_and_preprocess_image(request.image_path)
        frame_id = request.frame_id or f"{request.camera_id}_{processed.path.stem}"
        raw = self.detector.detect(processed.image)
        manager = self.detector.manager
        annotated_path = None
        if self.config.values["outputs"].get("save_annotated", True):
            destination = self.config.path(self.config.values["outputs"]["annotated_directory"]) / f"{frame_id}.jpg"
            annotated_path = save_annotated_image(processed.image, raw, destination)
        detections = [
            self._build_detection(
                item,
                request,
                frame_id,
                trace_id,
                processed.width,
                processed.height,
                processed.path,
                annotated_path,
                source,
            )
            for item in raw
        ]
        for detection in detections:
            if self.repository:
                self.repository.add(detection)
        elapsed = (time.perf_counter() - started) * 1000
        response = VisionInferenceResponse(
            trace_id=trace_id,
            frame_id=frame_id,
            detections=detections,
            inference_time_ms=elapsed,
            model_name=manager.model_name,
            model_version=manager.model_version,
            custom_model_loaded=manager.custom_model_loaded,
            technical_fallback=manager.technical_fallback,
            annotated_image_path=self._stored_path(annotated_path),
        )
        if self.config.values["outputs"].get("save_json", True):
            directory = self.config.path(self.config.values["outputs"]["predictions_directory"])
            directory.mkdir(parents=True, exist_ok=True)
            output = directory / f"{frame_id}_{trace_id}.json"
            response.prediction_json_path = self._stored_path(output)
            output.write_text(response.model_dump_json(indent=2), encoding="utf-8")
        return response

    def analyze_many(self, requests: list[VisionInferenceRequest], *, source: str = "vision_agent") -> list[VisionInferenceResponse]:
        return [self.analyze(request, source=source) for request in requests]

    def analyze_directory(
        self,
        directory: str | Path,
        *,
        equipment_id: str,
        camera_id: str,
        source: str = "vision_agent",
    ) -> list[VisionInferenceResponse]:
        from .constants import SUPPORTED_EXTENSIONS

        root = Path(directory)
        requests = [
            VisionInferenceRequest(image_path=str(path), equipment_id=equipment_id, camera_id=camera_id)
            for path in sorted(root.iterdir())
            if path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        return self.analyze_many(requests, source=source)

    def _build_detection(
        self,
        raw: RawVisionDetection,
        request: VisionInferenceRequest,
        frame_id: str,
        trace_id: str,
        width: int,
        height: int,
        original: Path,
        annotated: Path | None,
        source: str,
    ) -> VisionDetection:
        clipped = (
            max(0, min(width - 1, raw.box[0])),
            max(0, min(height - 1, raw.box[1])),
            max(1, min(width, raw.box[2])),
            max(1, min(height, raw.box[3])),
        )
        identity = f"{trace_id}|{frame_id}|{raw.defect_type}|{','.join(f'{x:.3f}' for x in clipped)}"
        detection_id = f"vision-det-{uuid5(UUID(trace_id), identity).hex}"
        return VisionDetection(
            detection_id=detection_id,
            equipment_id=request.equipment_id,
            camera_id=request.camera_id,
            frame_id=frame_id,
            defect_type=raw.defect_type,
            confidence=raw.confidence,
            bounding_box=BoundingBox(x_min=clipped[0], y_min=clipped[1], x_max=clipped[2], y_max=clipped[3]),
            image_width=width,
            image_height=height,
            original_image_path=self._stored_path(original),
            annotated_image_path=self._stored_path(annotated),
            source=source,
            trace_id=trace_id,
            model_name=self.detector.manager.model_name,
            model_version=self.detector.manager.model_version,
            provenance=VisionProvenance(
                dataset=DATASET_NAME,
                custom_model_loaded=self.detector.manager.custom_model_loaded,
            ),
        )

    def _stored_path(self, path: Path | None) -> str | None:
        if path is None:
            return None
        resolved = path.resolve()
        try:
            return resolved.relative_to(self.config.root).as_posix()
        except ValueError:
            return resolved.as_posix()
