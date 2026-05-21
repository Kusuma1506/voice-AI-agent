from __future__ import annotations

import json
import os
from pathlib import Path
from time import perf_counter


class LatencyTracker:
    def __init__(self) -> None:
        self.started_at = perf_counter()
        self.marks: dict[str, float] = {}

    def mark(self, name: str) -> None:
        self.marks[name] = perf_counter()

    def report(self) -> dict[str, float | bool]:
        previous = self.started_at
        stages: dict[str, float | bool] = {}
        for name, value in self.marks.items():
            stages[f"{name}_ms"] = round((value - previous) * 1000, 2)
            previous = value
        total_ms = round((previous - self.started_at) * 1000, 2)
        stages["total_ms"] = total_ms
        stages["under_450ms"] = total_ms < 450
        return stages


class LatencyLogger:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("VOICE_AI_LOG_PATH", "./logs/latency.jsonl"))
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: dict) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

