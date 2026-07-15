from __future__ import annotations

import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from .models import SystemRun


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProcessManager:
    """Owns at most one local demo process; arguments come from a strict whitelist."""

    SCENARIOS = {"normal": "normal", "bearing_wear": "bearing_wear", "pump_cavitation": "pump_cavitation",
                 "emergency": "emergency", "resource_unavailable": "resource_unavailable",
                 "agent_unavailable": "agent_unavailable", "duplicate_message": "duplicate"}

    def __init__(self, root: Path, session_factory) -> None:
        self.root, self.Session = root, session_factory
        self._process: subprocess.Popen | None = None
        self._run_id: str | None = None
        self._lock = threading.Lock()

    def start(self, scenario: str, mode: str, speed: float, maximum: int, equipment_id: str | None) -> SystemRun:
        if scenario not in self.SCENARIOS:
            raise ValueError("Scenario non autorise")
        with self._lock:
            if self._process and self._process.poll() is None:
                raise RuntimeError("Une execution est deja active")
            run_id = f"run-{uuid.uuid4()}"
            command = [sys.executable, str(self.root / "run_multi_agent_system.py"), "--scenario", self.SCENARIOS[scenario],
                       "--mode", mode, "--speed", str(speed), "--max-measurements", str(maximum)]
            if equipment_id:
                command.extend(["--equipment-id", equipment_id])
            self._process = subprocess.Popen(command, cwd=self.root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            self._run_id = run_id
            with self.Session() as session:
                run = SystemRun(run_id=run_id, scenario=scenario, mode=mode, status="running", started_at=_now(), process_id=self._process.pid)
                session.add(run); session.commit(); session.refresh(run)
            threading.Thread(target=self._watch, args=(run_id, self._process), daemon=True).start()
            return run

    def _watch(self, run_id: str, process: subprocess.Popen) -> None:
        code = process.wait()
        with self.Session() as session:
            run = session.scalar(select(SystemRun).where(SystemRun.run_id == run_id))
            if run and run.status == "running":
                run.status = "completed" if code == 0 else "failed"
                run.completed_at = _now()
                if code:
                    run.error_message = f"Le processus s'est termine avec le code {code}."
                session.commit()

    def stop(self) -> SystemRun | None:
        with self._lock:
            if not self._run_id:
                return None
            if self._process and self._process.poll() is None:
                self._process.terminate()
            with self.Session() as session:
                run = session.scalar(select(SystemRun).where(SystemRun.run_id == self._run_id))
                if run:
                    run.status = "stopped"; run.completed_at = _now(); session.commit(); session.refresh(run)
                return run
