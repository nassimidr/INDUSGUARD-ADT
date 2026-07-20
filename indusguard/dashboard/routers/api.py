from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from .. import models
from ..dependencies import get_session
from ..schemas import SystemRunStart, WorkOrderStatusUpdate
from ..utils import as_dict, envelope
from indusguard.vision.exceptions import InvalidImageError, VisionModelUnavailableError
from indusguard.vision.repository import SQLAlchemyVisionRepository
from indusguard.vision.schemas import VisionInferenceRequest
from indusguard.vision.service import VisionService

router = APIRouter(prefix="/api/v1")


def _page(session: Session, model: type, page: int, page_size: int, *conditions, order=None) -> dict[str, Any]:
    total = session.scalar(select(func.count()).select_from(model).where(*conditions)) or 0
    statement = select(model).where(*conditions).order_by(order if order is not None else desc(model.id)).offset((page - 1) * page_size).limit(page_size)
    return envelope([as_dict(item) for item in session.scalars(statement)], page=page, page_size=page_size,
                    total=total, pages=math.ceil(total / page_size) if total else 0)


def _one(session: Session, model: type, condition, label: str):
    item = session.scalar(select(model).where(condition))
    if not item:
        raise HTTPException(404, f"{label} introuvable")
    return item


@router.get("/health")
def health(request: Request, session: Session = Depends(get_session)):
    session.execute(select(1))
    return envelope({"status": "healthy", "database": "connected", "websocket_connections": request.app.state.ws.connection_count})


@router.get("/config")
def config(request: Request):
    values = request.app.state.config.values
    return envelope({"app": values["app"], "dashboard": values["dashboard"], "runtime": {"allowed_scenarios": values["runtime"]["allowed_scenarios"]}})


@router.get("/overview")
def overview(session: Session = Depends(get_session)):
    counts = {model.__tablename__: session.scalar(select(func.count()).select_from(model)) or 0 for model in
              (models.Asset, models.AnomalyResult, models.FaultDiagnosis, models.RULPrediction, models.WorkOrder, models.Alert)}
    counts["unacknowledged_alerts"] = session.scalar(select(func.count()).select_from(models.Alert).where(models.Alert.acknowledged.is_(False))) or 0
    counts["active_work_orders"] = session.scalar(select(func.count()).select_from(models.WorkOrder).where(models.WorkOrder.status.notin_(["completed", "cancelled"]))) or 0
    latest = session.scalars(select(models.SensorMeasurement).order_by(desc(models.SensorMeasurement.timestamp)).limit(8)).all()
    return envelope({"counts": counts, "latest_measurements": [as_dict(x) for x in latest]})


@router.get("/assets")
def assets(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200), search: str | None = None,
           session: Session = Depends(get_session)):
    conditions = [or_(models.Asset.equipment_id.contains(search), models.Asset.display_name.contains(search))] if search else []
    return _page(session, models.Asset, page, page_size, *conditions, order=models.Asset.equipment_id)


@router.get("/assets/{equipment_id}")
def asset(equipment_id: str, session: Session = Depends(get_session)):
    return envelope(as_dict(_one(session, models.Asset, models.Asset.equipment_id == equipment_id, "Equipement")))


@router.get("/assets/{equipment_id}/latest")
def asset_latest(equipment_id: str, session: Session = Depends(get_session)):
    data = {}
    for name, model in (("measurement", models.SensorMeasurement), ("anomaly", models.AnomalyResult),
                        ("diagnosis", models.FaultDiagnosis), ("rul", models.RULPrediction)):
        item = session.scalar(select(model).where(model.equipment_id == equipment_id).order_by(desc(model.timestamp)).limit(1))
        data[name] = as_dict(item) if item else None
    return envelope(data)


@router.get("/assets/{equipment_id}/timeline")
def asset_timeline(equipment_id: str, limit: int = Query(200, ge=1, le=1000), session: Session = Depends(get_session)):
    items = session.scalars(select(models.SensorMeasurement).where(models.SensorMeasurement.equipment_id == equipment_id)
                            .order_by(desc(models.SensorMeasurement.timestamp)).limit(limit)).all()
    return envelope([as_dict(x) for x in reversed(items)])


@router.get("/assets/{equipment_id}/trace")
def asset_trace(equipment_id: str, session: Session = Depends(get_session)):
    return envelope([as_dict(x) for x in session.scalars(select(models.PipelineTrace).where(models.PipelineTrace.equipment_id == equipment_id).order_by(desc(models.PipelineTrace.started_at)).limit(50))])


@router.get("/assets/{equipment_id}/vision-detections")
def asset_vision_detections(equipment_id: str, limit: int = Query(100, ge=1, le=1000), session: Session = Depends(get_session)):
    items = session.scalars(select(models.VisionDetectionModel).where(models.VisionDetectionModel.equipment_id == equipment_id)
                            .order_by(desc(models.VisionDetectionModel.timestamp)).limit(limit)).all()
    return envelope([as_dict(item) for item in items])


@router.get("/measurements")
def measurements(page: int = 1, page_size: int = Query(25, le=200), equipment_id: str | None = None, session: Session = Depends(get_session)):
    conditions = [models.SensorMeasurement.equipment_id == equipment_id] if equipment_id else []
    return _page(session, models.SensorMeasurement, page, page_size, *conditions, order=desc(models.SensorMeasurement.timestamp))


@router.get("/measurements/latest")
def measurements_latest(limit: int = Query(20, le=200), session: Session = Depends(get_session)):
    return envelope([as_dict(x) for x in session.scalars(select(models.SensorMeasurement).order_by(desc(models.SensorMeasurement.timestamp)).limit(limit))])


@router.get("/measurements/equipment/{equipment_id}")
def measurements_equipment(equipment_id: str, page: int = 1, page_size: int = Query(100, le=1000), session: Session = Depends(get_session)):
    return _page(session, models.SensorMeasurement, page, page_size, models.SensorMeasurement.equipment_id == equipment_id, order=desc(models.SensorMeasurement.timestamp))


def _analysis_routes(path: str, model: type, detail_name: str):
    @router.get(f"/{path}", name=f"list_{path}")
    def listing(page: int = 1, page_size: int = Query(25, le=200), equipment_id: str | None = None, session: Session = Depends(get_session)):
        conditions = [model.equipment_id == equipment_id] if equipment_id else []
        return _page(session, model, page, page_size, *conditions, order=desc(model.timestamp))

    @router.get(f"/{path}/summary", name=f"summary_{path}")
    def summary(session: Session = Depends(get_session)):
        total = session.scalar(select(func.count()).select_from(model)) or 0
        by_equipment = session.execute(select(model.equipment_id, func.count()).group_by(model.equipment_id)).all()
        return envelope({"total": total, "by_equipment": dict(by_equipment)})

    @router.get(f"/{path}/{{item_id}}", name=f"detail_{path}")
    def detail(item_id: int, session: Session = Depends(get_session)):
        return envelope(as_dict(_one(session, model, model.id == item_id, detail_name)))


_analysis_routes("anomalies", models.AnomalyResult, "Anomalie")
_analysis_routes("diagnoses", models.FaultDiagnosis, "Diagnostic")


@router.get("/rul")
def rul(page: int = 1, page_size: int = Query(25, le=200), equipment_id: str | None = None, session: Session = Depends(get_session)):
    conditions = [models.RULPrediction.equipment_id == equipment_id] if equipment_id else []
    return _page(session, models.RULPrediction, page, page_size, *conditions, order=desc(models.RULPrediction.timestamp))


@router.get("/rul/latest")
def rul_latest(session: Session = Depends(get_session)):
    latest_ids = select(func.max(models.RULPrediction.id)).group_by(models.RULPrediction.equipment_id)
    return envelope([as_dict(x) for x in session.scalars(select(models.RULPrediction).where(models.RULPrediction.id.in_(latest_ids)))])


@router.get("/rul/equipment/{equipment_id}")
def rul_equipment(equipment_id: str, limit: int = Query(200, le=1000), session: Session = Depends(get_session)):
    return envelope([as_dict(x) for x in session.scalars(select(models.RULPrediction).where(models.RULPrediction.equipment_id == equipment_id).order_by(desc(models.RULPrediction.timestamp)).limit(limit))])


@router.get("/rul/summary")
def rul_summary(session: Session = Depends(get_session)):
    rows = session.execute(select(models.RULPrediction.risk_level, func.count()).group_by(models.RULPrediction.risk_level)).all()
    return envelope({"total": sum(count for _, count in rows), "by_risk": dict(rows)})


@router.get("/vision/health")
def vision_health(request: Request):
    if not request.app.state.vision_manager.loaded:
        try: request.app.state.vision_manager.load()
        except VisionModelUnavailableError: pass
    return envelope(request.app.state.vision_manager.status().model_dump(mode="json"))


def _controlled_vision_path(request: Request, image_path: str):
    config = request.app.state.vision_config
    candidate = config.path(image_path)
    allowed = [config.path(value) for value in config.values.get("api", {}).get("allowed_input_directories", [])]
    if not any(candidate == root or root in candidate.parents for root in allowed):
        raise HTTPException(422, "Image path is outside the configured demo directories.")
    if not candidate.is_file():
        raise HTTPException(422, "Image file does not exist.")
    maximum = int(config.values.get("api", {}).get("maximum_image_bytes", 10 * 1024 * 1024))
    if candidate.stat().st_size > maximum:
        raise HTTPException(413, "Image exceeds the configured size limit.")
    return candidate


@router.post("/vision/analyze")
async def vision_analyze(payload: VisionInferenceRequest, request: Request, session: Session = Depends(get_session)):
    controlled = _controlled_vision_path(request, payload.image_path)
    safe_payload = payload.model_copy(update={"image_path": str(controlled)})
    service = VisionService(request.app.state.vision_config, request.app.state.vision_detector, SQLAlchemyVisionRepository(session))
    try:
        result = service.analyze(safe_payload, source="vision_api")
    except InvalidImageError as error:
        raise HTTPException(422, str(error)) from error
    except VisionModelUnavailableError as error:
        await request.app.state.ws.broadcast("vision.analysis.failed", {"trace_id": payload.trace_id, "error": str(error)})
        raise HTTPException(503, str(error)) from error
    for detection in result.detections:
        await request.app.state.ws.broadcast("vision.detection.created", detection.model_dump(mode="json"))
    return envelope(result.model_dump(mode="json"))


@router.get("/vision/detections")
def vision_detections(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200),
                      equipment_id: str | None = None, defect_type: str | None = None,
                      camera_id: str | None = None, start: str | None = None, end: str | None = None,
                      session: Session = Depends(get_session)):
    conditions = []
    if equipment_id: conditions.append(models.VisionDetectionModel.equipment_id == equipment_id)
    if defect_type: conditions.append(models.VisionDetectionModel.defect_type == defect_type)
    if camera_id: conditions.append(models.VisionDetectionModel.camera_id == camera_id)
    if start: conditions.append(models.VisionDetectionModel.timestamp >= start)
    if end: conditions.append(models.VisionDetectionModel.timestamp <= end)
    return _page(session, models.VisionDetectionModel, page, page_size, *conditions, order=desc(models.VisionDetectionModel.timestamp))


@router.get("/vision/detections/{detection_id}")
def vision_detection(detection_id: str, session: Session = Depends(get_session)):
    item = _one(session, models.VisionDetectionModel, models.VisionDetectionModel.detection_id == detection_id, "Detection vision")
    return envelope(as_dict(item))


@router.get("/vision/detections/{detection_id}/image/{variant}")
def vision_detection_image(detection_id: str, variant: str, request: Request, session: Session = Depends(get_session)):
    if variant not in {"original", "annotated"}:
        raise HTTPException(404, "Image variant not found")
    item = _one(session, models.VisionDetectionModel, models.VisionDetectionModel.detection_id == detection_id, "Detection vision")
    stored = item.original_image_path if variant == "original" else item.annotated_image_path
    if not stored:
        raise HTTPException(404, "Image not found")
    candidate = request.app.state.vision_config.path(stored)
    root = request.app.state.vision_config.root
    if root not in candidate.parents or not candidate.is_file():
        raise HTTPException(404, "Image not found")
    return FileResponse(candidate)


@router.get("/maintenance/recommendations")
def recommendations(page: int = 1, page_size: int = Query(25, le=200), session: Session = Depends(get_session)):
    return _page(session, models.MaintenanceRecommendation, page, page_size, order=desc(models.MaintenanceRecommendation.timestamp))


@router.get("/maintenance/equipment/{equipment_id}")
def recommendations_equipment(equipment_id: str, session: Session = Depends(get_session)):
    return envelope([as_dict(x) for x in session.scalars(select(models.MaintenanceRecommendation).where(models.MaintenanceRecommendation.equipment_id == equipment_id).order_by(desc(models.MaintenanceRecommendation.timestamp)))])


@router.get("/maintenance/summary")
def maintenance_summary(session: Session = Depends(get_session)):
    priorities = session.execute(select(models.MaintenanceRecommendation.priority, func.count()).group_by(models.MaintenanceRecommendation.priority)).all()
    cost = session.scalar(select(func.sum(models.MaintenanceRecommendation.estimated_total_cost))) or 0
    return envelope({"by_priority": dict(priorities), "estimated_total_cost": cost})


@router.get("/work-orders")
def work_orders(page: int = 1, page_size: int = Query(25, le=200), status: str | None = None, session: Session = Depends(get_session)):
    conditions = [models.WorkOrder.status == status] if status else []
    return _page(session, models.WorkOrder, page, page_size, *conditions, order=desc(models.WorkOrder.created_at))


@router.get("/work-orders/{work_order_id}")
def work_order(work_order_id: str, session: Session = Depends(get_session)):
    return envelope(as_dict(_one(session, models.WorkOrder, models.WorkOrder.work_order_id == work_order_id, "Ordre de travail")))


@router.patch("/work-orders/{work_order_id}/status")
async def update_work_order(work_order_id: str, update: WorkOrderStatusUpdate, request: Request, session: Session = Depends(get_session)):
    item = _one(session, models.WorkOrder, models.WorkOrder.work_order_id == work_order_id, "Ordre de travail")
    item.status = update.status; item.updated_at = datetime.now(timezone.utc).isoformat(); session.commit(); session.refresh(item)
    await request.app.state.ws.broadcast("work_order.updated", as_dict(item))
    return envelope(as_dict(item))


@router.get("/agents")
def agents(session: Session = Depends(get_session)):
    latest = select(func.max(models.AgentHealth.id)).group_by(models.AgentHealth.agent_id)
    return envelope([as_dict(x) for x in session.scalars(select(models.AgentHealth).where(models.AgentHealth.id.in_(latest)))])


@router.get("/agents/summary")
def agents_summary(session: Session = Depends(get_session)):
    rows = session.execute(select(models.AgentHealth.status, func.count()).group_by(models.AgentHealth.status)).all()
    return envelope({"by_status": dict(rows), "messages": session.scalar(select(func.count()).select_from(models.AgentMessage)) or 0})


@router.get("/agents/{agent_id}")
def agent(agent_id: str, session: Session = Depends(get_session)):
    item = session.scalar(select(models.AgentHealth).where(models.AgentHealth.agent_id == agent_id).order_by(desc(models.AgentHealth.timestamp)).limit(1))
    if not item: raise HTTPException(404, "Agent introuvable")
    return envelope(as_dict(item))


@router.get("/agents/{agent_id}/messages")
def agent_messages(agent_id: str, limit: int = Query(100, le=1000), session: Session = Depends(get_session)):
    condition = or_(models.AgentMessage.sender_agent == agent_id, models.AgentMessage.receiver_agent == agent_id)
    return envelope([as_dict(x) for x in session.scalars(select(models.AgentMessage).where(condition).order_by(desc(models.AgentMessage.timestamp)).limit(limit))])


@router.get("/alerts")
def alerts(page: int = 1, page_size: int = Query(25, le=200), acknowledged: bool | None = None, session: Session = Depends(get_session)):
    conditions = [models.Alert.acknowledged == acknowledged] if acknowledged is not None else []
    return _page(session, models.Alert, page, page_size, *conditions, order=desc(models.Alert.timestamp))


@router.get("/alerts/{alert_id}")
def alert(alert_id: str, session: Session = Depends(get_session)):
    return envelope(as_dict(_one(session, models.Alert, models.Alert.alert_id == alert_id, "Alerte")))


@router.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge(alert_id: str, request: Request, session: Session = Depends(get_session)):
    item = _one(session, models.Alert, models.Alert.alert_id == alert_id, "Alerte")
    item.acknowledged = True; item.acknowledged_at = datetime.now(timezone.utc).isoformat(); session.commit(); session.refresh(item)
    await request.app.state.ws.broadcast("alert.acknowledged", as_dict(item)); return envelope(as_dict(item))


@router.post("/alerts/acknowledge-all")
async def acknowledge_all(request: Request, session: Session = Depends(get_session)):
    items = session.scalars(select(models.Alert).where(models.Alert.acknowledged.is_(False))).all(); timestamp = datetime.now(timezone.utc).isoformat()
    for item in items: item.acknowledged = True; item.acknowledged_at = timestamp
    session.commit(); await request.app.state.ws.broadcast("alert.acknowledged", {"count": len(items)}); return envelope({"acknowledged": len(items)})


@router.get("/traces")
def traces(page: int = 1, page_size: int = Query(25, le=200), session: Session = Depends(get_session)):
    return _page(session, models.PipelineTrace, page, page_size, order=desc(models.PipelineTrace.started_at))


@router.get("/traces/{trace_id}")
def trace(trace_id: str, session: Session = Depends(get_session)):
    return envelope(as_dict(_one(session, models.PipelineTrace, models.PipelineTrace.trace_id == trace_id, "Trace")))


@router.get("/traces/{trace_id}/timeline")
def trace_timeline(trace_id: str, session: Session = Depends(get_session)):
    events = session.scalars(select(models.SystemEvent).where(models.SystemEvent.trace_id == trace_id).order_by(models.SystemEvent.timestamp)).all()
    return envelope([as_dict(x) for x in events])


@router.get("/system-runs")
def runs(page: int = 1, page_size: int = Query(25, le=200), session: Session = Depends(get_session)):
    return _page(session, models.SystemRun, page, page_size, order=desc(models.SystemRun.started_at))


@router.get("/system-runs/current")
def current_run(session: Session = Depends(get_session)):
    item = session.scalar(select(models.SystemRun).where(models.SystemRun.status == "running").order_by(desc(models.SystemRun.started_at)).limit(1))
    return envelope(as_dict(item) if item else None)


@router.post("/system-runs/start", status_code=201)
async def start_run(payload: SystemRunStart, request: Request):
    try: item = request.app.state.process_manager.start(payload.scenario, payload.mode, payload.speed, payload.max_measurements, payload.equipment_id)
    except ValueError as error: raise HTTPException(400, str(error)) from error
    except RuntimeError as error: raise HTTPException(409, str(error)) from error
    await request.app.state.ws.broadcast("system_run.started", as_dict(item)); return envelope(as_dict(item))


@router.post("/system-runs/stop")
async def stop_run(request: Request):
    item = request.app.state.process_manager.stop()
    if not item: raise HTTPException(409, "Aucune execution active")
    await request.app.state.ws.broadcast("system_run.completed", as_dict(item)); return envelope(as_dict(item))
