"""Phase 8A industrial vision components."""

from .config import VisionConfig, load_vision_config
from .model_manager import VisionModelManager
from .schemas import BoundingBox, VisionDetection, VisionInferenceRequest, VisionInferenceResponse
from .service import VisionService

__all__ = [
    "BoundingBox",
    "VisionConfig",
    "VisionDetection",
    "VisionInferenceRequest",
    "VisionInferenceResponse",
    "VisionModelManager",
    "VisionService",
    "load_vision_config",
]
