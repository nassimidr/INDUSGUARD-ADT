from __future__ import annotations

SUPPORTED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
INDUSTRIAL_DEFECT_CLASSES = (
    "belt_misalignment",
    "obstacle",
    "material_accumulation",
)
UNKNOWN_DEFECT = "unknown_defect"
ALLOWED_DEFECT_CLASSES = frozenset((*INDUSTRIAL_DEFECT_CLASSES, UNKNOWN_DEFECT))
MODEL_SOURCE = "vision_agent"
DATASET_NAME = "indusguard-vision-synthetic"
