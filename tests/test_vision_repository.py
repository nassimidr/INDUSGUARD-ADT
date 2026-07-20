from uuid import uuid4

from sqlalchemy import func, select

from indusguard.dashboard.config import DashboardConfig, load_dashboard_config
from indusguard.dashboard.database import build_engine, initialize_database, session_factory
from indusguard.dashboard.models import VisionDetectionModel
from indusguard.vision.repository import SQLAlchemyVisionRepository
from tests.test_vision_schemas import valid_detection


def test_repository_is_idempotent_and_round_trips(tmp_path):
    base = load_dashboard_config(); values = {**base.values, "database": {**base.values["database"], "url": f"sqlite:///{(tmp_path/'vision.db').as_posix()}"}}
    engine = build_engine(DashboardConfig(base.root, values)); initialize_database(engine); Session = session_factory(engine)
    detection = valid_detection(detection_id=f"vision-det-{uuid4().hex}")
    with Session() as session:
        repository = SQLAlchemyVisionRepository(session)
        repository.add(detection); repository.add(detection)
        assert session.scalar(select(func.count()).select_from(VisionDetectionModel)) == 1
        assert repository.get(detection.detection_id).trace_id == detection.trace_id
    engine.dispose()
