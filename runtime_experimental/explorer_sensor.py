import json
import os
from typing import Dict, Any

SIGNAL_PATH = os.environ.get("EXTERNAL_SIGNAL_PATH", "external_signal.json")


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def load_external_signal() -> Dict[str, Any]:
    if not os.path.exists(SIGNAL_PATH):
        return {
            "source": "EXPLORER",
            "kind": "none",
            "intensity": 0.0,
            "novelty": 0.0,
            "payload": {},
        }

    with open(SIGNAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "source": str(data.get("source", "EXPLORER")),
        "kind": str(data.get("kind", "none")),
        "intensity": float(data.get("intensity", 0.0)),
        "novelty": float(data.get("novelty", 0.0)),
        "payload": data.get("payload", {}) if isinstance(data.get("payload", {}), dict) else {},
    }


def build_explorer_patch(signal: Dict[str, Any]) -> Dict[str, Any]:
    kind = str(signal.get("kind", "none"))
    intensity = _clamp01(float(signal.get("intensity", 0.0)))
    novelty = _clamp01(float(signal.get("novelty", 0.0)))

    pressure_delta = 0.0
    future_delta = 0.0
    mode = None

    if kind == "issue":
        pressure_delta += 0.08 * intensity
        future_delta += 0.03 * novelty
        mode = "external_pressure"

    elif kind == "task":
        pressure_delta += 0.05 * intensity
        future_delta += 0.06 * novelty
        mode = "task_intake"

    elif kind == "opportunity":
        pressure_delta += 0.02 * intensity
        future_delta += 0.10 * novelty
        mode = "discovery"

    elif kind == "warning":
        pressure_delta += 0.10 * intensity
        future_delta += 0.02 * novelty
        mode = "caution"

    return {
        "source": signal.get("source", "EXPLORER"),
        "kind": kind,
        "pressure_delta": round(pressure_delta, 3),
        "future_delta": round(future_delta, 3),
        "mode": mode,
        "raw": signal,
    }


def build_task_object(signal: Dict[str, Any]) -> Dict[str, Any]:
    payload = signal.get("payload", {}) if isinstance(signal.get("payload", {}), dict) else {}
    title = str(payload.get("title", "Untitled task"))
    origin = str(payload.get("origin", signal.get("source", "EXPLORER")))

    return {
        "type": "task",
        "title": title,
        "origin": origin,
        "status": "open",
        "kind": str(signal.get("kind", "task")),
        "intensity": float(signal.get("intensity", 0.0)),
        "novelty": float(signal.get("novelty", 0.0)),
        "payload": payload,
    }
