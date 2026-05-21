from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from threading import Lock
from uuid import uuid4


class CampaignScheduler:
    _lock = Lock()

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("VOICE_AI_DATA_PATH", "./data/store.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"sessions": {}, "patients": {}, "appointments": {}, "campaigns": []})

    def create_call_task(self, payload: dict) -> dict:
        data = self._read()
        task = {
            "id": f"call-{uuid4().hex[:8]}",
            "status": "queued",
            "created_at": datetime.utcnow().isoformat() + "Z",
            **payload,
            "opening_message": self._opening(payload.get("campaign_type", "reminder"), payload.get("language", "en")),
        }
        data["campaigns"].append(task)
        self._write(data)
        return task

    def list_tasks(self) -> list[dict]:
        return self._read()["campaigns"]

    def _opening(self, campaign_type: str, language: str) -> str:
        messages = {
            "en": {
                "reminder": "Hello, this is a reminder about your upcoming appointment.",
                "follow_up": "Hello, I am calling to schedule your follow-up checkup.",
                "vaccination": "Hello, I am calling about a vaccination reminder.",
            },
            "hi": {
                "reminder": "नमस्ते, यह आपकी आने वाली अपॉइंटमेंट की याद दिलाने के लिए कॉल है।",
                "follow_up": "नमस्ते, मैं आपका फॉलो-अप चेकअप शेड्यूल करने के लिए कॉल कर रहा हूँ।",
                "vaccination": "नमस्ते, यह टीकाकरण रिमाइंडर के लिए कॉल है।",
            },
            "ta": {
                "reminder": "வணக்கம், உங்கள் வரவிருக்கும் நேர்முகத்தை நினைவூட்டுகிறோம்.",
                "follow_up": "வணக்கம், உங்கள் follow-up checkup-ஐ அமைக்க அழைக்கிறோம்.",
                "vaccination": "வணக்கம், தடுப்பூசி நினைவூட்டலுக்காக அழைக்கிறோம்.",
            },
        }
        return messages.get(language, messages["en"]).get(campaign_type, messages.get(language, messages["en"])["reminder"])

    def _read(self) -> dict:
        with self._lock:
            return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict) -> None:
        with self._lock:
            self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

