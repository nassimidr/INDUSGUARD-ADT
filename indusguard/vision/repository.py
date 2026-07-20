from __future__ import annotations

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from .schemas import VisionDetection


class VisionDetectionRepository(Protocol):
    def add(self, detection: VisionDetection) -> VisionDetection: ...


class SQLAlchemyVisionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, detection: VisionDetection) -> VisionDetection:
        from indusguard.dashboard.models import VisionDetectionModel

        values = detection_to_record(detection)
        self.session.execute(
            insert(VisionDetectionModel)
            .values(**values)
            .on_conflict_do_nothing(index_elements=["detection_id"])
        )
        self.session.commit()
        return detection

    def get(self, detection_id: str) -> VisionDetection | None:
        from indusguard.dashboard.models import VisionDetectionModel

        row = self.session.scalar(
            select(VisionDetectionModel).where(VisionDetectionModel.detection_id == detection_id)
        )
        return record_to_detection(row) if row else None


def detection_to_record(detection: VisionDetection) -> dict:
    import json

    return {
        "detection_id": detection.detection_id,
        "equipment_id": detection.equipment_id,
        "camera_id": detection.camera_id,
        "frame_id": detection.frame_id,
        "defect_type": detection.defect_type,
        "confidence": detection.confidence,
        "x_min": detection.bounding_box.x_min,
        "y_min": detection.bounding_box.y_min,
        "x_max": detection.bounding_box.x_max,
        "y_max": detection.bounding_box.y_max,
        "image_width": detection.image_width,
        "image_height": detection.image_height,
        "original_image_path": detection.original_image_path,
        "annotated_image_path": detection.annotated_image_path,
        "timestamp": detection.timestamp.isoformat().replace("+00:00", "Z"),
        "trace_id": detection.trace_id,
        "source": detection.source,
        "model_name": detection.model_name,
        "model_version": detection.model_version,
        "provenance": json.dumps(detection.provenance.model_dump(), ensure_ascii=False),
    }


def record_to_detection(row) -> VisionDetection:
    import json

    return VisionDetection.model_validate({
        "detection_id": row.detection_id,
        "equipment_id": row.equipment_id,
        "camera_id": row.camera_id,
        "frame_id": row.frame_id,
        "defect_type": row.defect_type,
        "confidence": row.confidence,
        "bounding_box": {"x_min": row.x_min, "y_min": row.y_min, "x_max": row.x_max, "y_max": row.y_max},
        "image_width": row.image_width,
        "image_height": row.image_height,
        "original_image_path": row.original_image_path,
        "annotated_image_path": row.annotated_image_path,
        "timestamp": row.timestamp,
        "trace_id": row.trace_id,
        "source": row.source,
        "model_name": row.model_name,
        "model_version": row.model_version,
        "provenance": json.loads(row.provenance),
    })
