from __future__ import annotations

from indusguard.vision import VisionModelManager, VisionService, load_vision_config
from indusguard.vision.detector import VisionDetector
from indusguard.vision.schemas import VisionInferenceRequest

from .base_indusguard_agent import BaseIndusGuardAgent


class VisionAgent(BaseIndusGuardAgent):
    def __init__(self, *args, service: VisionService | None = None, **kwargs) -> None:
        super().__init__("vision", *args, **kwargs)
        if service is None:
            config = load_vision_config(self.config.root / "configs/vision.yaml")
            manager = VisionModelManager(config)
            service = VisionService(config, VisionDetector(config, manager))
        self.service = service

    async def setup(self) -> None:
        await self.common_setup(["vision.analysis.request"])

    async def process(self, envelope, message) -> None:
        request = VisionInferenceRequest.model_validate({
            **envelope.payload,
            "equipment_id": envelope.equipment_id or envelope.payload.get("equipment_id"),
            "trace_id": envelope.trace_id,
        })
        try:
            result = self.service.analyze(request, source="vision_agent")
            for detection in result.detections:
                payload = detection.model_dump(mode="json")
                self.metrics.increment("vision_detections_produced")
                await self.send_fipa(
                    "supervisor", "vision.detection", payload, "inform", "industrial-vision",
                    parent=envelope, equipment_id=detection.equipment_id,
                    equipment_type=envelope.equipment_type or "conveyor",
                    priority="high" if detection.confidence >= 0.8 else "medium",
                )
                await self.emit_historian(envelope, "vision_detection_created", payload)
                threshold = float(self.service.config.values["agent"]["alert_confidence_threshold"])
                if detection.confidence >= threshold:
                    await self.send_fipa(
                        "alert", "alert.created",
                        {"alert_id": detection.detection_id, "level": "high", "title": "Defaut visuel detecte",
                         "message": f"{detection.defect_type} ({detection.confidence:.2f})", "acknowledged": False},
                        "inform", "alerting", parent=envelope, equipment_id=detection.equipment_id,
                        equipment_type=envelope.equipment_type or "conveyor", priority="high",
                    )
            if not result.detections:
                await self.send_fipa(
                    "supervisor", "vision.analysis.completed",
                    {"frame_id": result.frame_id, "detections": 0, "custom_model_loaded": result.custom_model_loaded},
                    "inform", "industrial-vision", parent=envelope, priority="low",
                )
        except Exception as exc:
            await self.send_fipa(
                "supervisor", "vision.analysis.failed", {"reason": str(exc)}, "failure", "industrial-vision",
                parent=envelope, priority="high",
            )
            await self.emit_historian(envelope, "vision_analysis_failed", {"reason": str(exc)})
            raise
