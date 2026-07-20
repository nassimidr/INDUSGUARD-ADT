from __future__ import annotations

import argparse

from indusguard.dashboard.config import load_dashboard_config
from indusguard.dashboard.database import build_engine, initialize_database, session_factory
from indusguard.vision import VisionModelManager, VisionService, load_vision_config
from indusguard.vision.detector import VisionDetector
from indusguard.vision.repository import SQLAlchemyVisionRepository
from indusguard.vision.schemas import VisionInferenceRequest


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local Phase 8A inference and persist detections")
    parser.add_argument("--config", default="configs/vision.yaml")
    parser.add_argument("--image", required=True)
    parser.add_argument("--equipment-id", default="CONVEYOR-001")
    parser.add_argument("--camera-id", default="camera_01")
    parser.add_argument("--trace-id")
    args = parser.parse_args()
    try:
        config = load_vision_config(args.config)
        manager = VisionModelManager(config)
        detector = VisionDetector(config, manager)
        dashboard = load_dashboard_config()
        engine = build_engine(dashboard); initialize_database(engine); Session = session_factory(engine)
        with Session() as session:
            service = VisionService(config, detector, SQLAlchemyVisionRepository(session))
            response = service.analyze(VisionInferenceRequest(
                image_path=args.image, equipment_id=args.equipment_id, camera_id=args.camera_id, trace_id=args.trace_id,
            ), source="vision_cli")
        engine.dispose()
        print(response.model_dump_json(indent=2))
        return 0
    except Exception as exc:
        print(f"Vision inference failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
