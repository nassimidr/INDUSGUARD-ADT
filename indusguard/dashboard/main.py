from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy import select

from .config import DashboardConfig, load_dashboard_config
from .database import build_engine, initialize_database, session_factory
from .process_manager import ProcessManager
from .models import SystemEvent
from .routers import router
from .schemas import Subscription
from .websocket import DashboardConnectionManager


def create_app(config: DashboardConfig | None = None) -> FastAPI:
    settings = config or load_dashboard_config()
    engine = build_engine(settings); initialize_database(engine); Session = session_factory(engine)

    ws = DashboardConnectionManager(int(settings.values["websocket"]["maximum_connections"]))

    async def relay_database_events() -> None:
        last_id = 0
        mapping = {"sensor.measurement": "measurement.created", "anomaly.result": "anomaly.detected",
                   "diagnosis.result": "diagnosis.completed", "rul.result": "rul.updated",
                   "maintenance.recommendation": "maintenance.recommended", "alert.created": "alert.created",
                   "heartbeat": "agent.health_updated", "pipeline.completed": "pipeline.trace_updated"}
        while True:
            with Session() as session:
                events = session.scalars(select(SystemEvent).where(SystemEvent.id > last_id).order_by(SystemEvent.id).limit(200)).all()
                for event in events:
                    last_id = event.id
                    await ws.broadcast(mapping.get(event.event_type, "pipeline.trace_updated"), {"event_id": event.id,
                        "trace_id": event.trace_id, "equipment_id": event.equipment_id, "timestamp": event.timestamp})
            await asyncio.sleep(float(settings.values["websocket"]["batch_interval_ms"]) / 1000)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        relay = asyncio.create_task(relay_database_events())
        try: yield
        finally:
            relay.cancel()
            try: await relay
            except asyncio.CancelledError: pass
            engine.dispose()

    app = FastAPI(title="INDUSGUARD-ADT Dashboard API", version="7.0.0", lifespan=lifespan)
    app.state.config, app.state.engine, app.state.Session = settings, engine, Session
    app.state.ws = ws
    app.state.process_manager = ProcessManager(settings.root, Session)
    app.add_middleware(CORSMiddleware, allow_origins=settings.values["api"]["cors_origins"], allow_credentials=False,
                       allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])
    app.include_router(router)

    @app.websocket(settings.values["websocket"]["path"])
    async def dashboard_socket(websocket: WebSocket):
        if not await app.state.ws.connect(websocket): return
        timeout = float(settings.values["websocket"]["heartbeat_seconds"])
        maximum = int(settings.values["websocket"]["maximum_message_bytes"])
        try:
            while True:
                try: text = await asyncio.wait_for(websocket.receive_text(), timeout=timeout)
                except asyncio.TimeoutError:
                    await websocket.send_json({"event": "heartbeat", "data": {}}); continue
                if len(text.encode("utf-8")) > maximum:
                    await websocket.close(code=1009, reason="Message trop volumineux"); break
                try: subscription = Subscription.model_validate(json.loads(text))
                except (ValidationError, json.JSONDecodeError):
                    await websocket.send_json({"event": "error", "data": {"message": "Souscription invalide"}}); continue
                await app.state.ws.subscribe(websocket, subscription.event_types)
                await websocket.send_json({"event": "subscribed", "data": {"event_types": subscription.event_types or ["*"]}})
        except WebSocketDisconnect:
            await app.state.ws.disconnect(websocket)
    return app


app = create_app()
