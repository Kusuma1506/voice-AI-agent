from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Any


class MemoryStore:
    """JSON-backed memory with the same shape a Redis/Postgres adapter would expose."""

    _lock = Lock()

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("VOICE_AI_DATA_PATH", "./data/store.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"sessions": {}, "patients": {}, "appointments": {}, "campaigns": []})

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._read()["sessions"].get(session_id, {})

    def update_session(self, session_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        session = data["sessions"].setdefault(session_id, {})
        for key, value in updates.items():
            if value is None:
                session.pop(key, None)
            else:
                session[key] = value
        self._write(data)
        return session

    def get_patient(self, patient_id: str) -> dict[str, Any]:
        return self._read()["patients"].get(patient_id, {})

    def update_patient(self, patient_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        patient = data["patients"].setdefault(patient_id, {"past_appointments": []})
        patient.update({key: value for key, value in updates.items() if value is not None})
        self._write(data)
        return patient

    def _read(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        with self._lock:
            self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

