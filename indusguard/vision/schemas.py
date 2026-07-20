from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePath
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .constants import ALLOWED_DEFECT_CLASSES, MODEL_SOURCE


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class BoundingBox(StrictModel):
    x_min: float = Field(ge=0)
    y_min: float = Field(ge=0)
    x_max: float = Field(gt=0)
    y_max: float = Field(gt=0)

    @model_validator(mode="after")
    def ordered(self) -> "BoundingBox":
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            raise ValueError("Bounding-box maximum coordinates must exceed minimum coordinates.")
        return self


class VisionProvenance(StrictModel):
    modality: Literal["vision"] = "vision"
    input_type: Literal["image", "frame"] = "image"
    dataset: str = Field(min_length=1)
    custom_model_loaded: bool = False


class VisionDetection(StrictModel):
    detection_id: str = Field(min_length=1)
    equipment_id: str = Field(min_length=1)
    camera_id: str = Field(min_length=1)
    frame_id: str = Field(min_length=1)
    defect_type: str
    confidence: float = Field(ge=0, le=1)
    bounding_box: BoundingBox
    image_width: int = Field(gt=0)
    image_height: int = Field(gt=0)
    original_image_path: str = Field(min_length=1)
    annotated_image_path: str | None = None
    timestamp: datetime = Field(default_factory=utc_now)
    source: Literal["vision_agent", "vision_api", "vision_cli"] = MODEL_SOURCE
    trace_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    provenance: VisionProvenance

    @field_validator("defect_type")
    @classmethod
    def allowed_class(cls, value: str) -> str:
        if value not in ALLOWED_DEFECT_CLASSES:
            raise ValueError(f"Unknown visual defect class: {value}")
        return value

    @field_validator("timestamp")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
            raise ValueError("Vision timestamps must be UTC-aware.")
        return value

    @field_validator("trace_id")
    @classmethod
    def valid_trace(cls, value: str) -> str:
        try:
            UUID(value)
        except ValueError as exc:
            raise ValueError("trace_id must be a UUID.") from exc
        return value

    @field_validator("original_image_path", "annotated_image_path")
    @classmethod
    def normalized_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        path = PurePath(value)
        if ".." in path.parts:
            raise ValueError("Image paths cannot contain parent traversal segments.")
        return Path(value).as_posix()

    @model_validator(mode="after")
    def box_inside_image(self) -> "VisionDetection":
        if self.bounding_box.x_max > self.image_width or self.bounding_box.y_max > self.image_height:
            raise ValueError("Bounding box must remain inside image dimensions.")
        return self


class VisionInferenceRequest(StrictModel):
    image_path: str = Field(min_length=1)
    equipment_id: str = Field(min_length=1)
    camera_id: str = Field(min_length=1)
    frame_id: str | None = Field(default=None, min_length=1)
    trace_id: str | None = None

    @field_validator("trace_id")
    @classmethod
    def optional_uuid(cls, value: str | None) -> str | None:
        if value is not None:
            UUID(value)
        return value


class VisionInferenceResponse(StrictModel):
    trace_id: str
    frame_id: str
    detections: list[VisionDetection]
    inference_time_ms: float = Field(ge=0)
    model_name: str
    model_version: str
    custom_model_loaded: bool
    technical_fallback: bool
    annotated_image_path: str | None = None
    prediction_json_path: str | None = None


class VisionHealthStatus(StrictModel):
    enabled: bool
    mode: str
    loaded: bool
    available: bool
    custom_model_loaded: bool
    technical_fallback: bool
    model_name: str
    model_version: str
    device: str
    detail: str | None = None


class VisionDatasetMetadata(StrictModel):
    dataset_name: str
    seed: int
    generated_at: datetime
    image_width: int = Field(gt=0)
    image_height: int = Field(gt=0)
    total_images: int = Field(ge=0)
    splits: dict[str, int]
    class_counts: dict[str, int]
    normal_images: int = Field(ge=0)
    generation_parameters: dict[str, Any]
