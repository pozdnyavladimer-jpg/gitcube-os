from __future__ import annotations

from typing import Dict, Any

from router import should_use_party
from app.orchestration.router_engine import route_task
from core.memory.target_memory import filter_targets_on_cooldown


def _extract_paths(task: Dict[str, Any]) -> list[str]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    paths = payload.get("paths", task.get("paths", []))
    if not isinstance(paths, list):
        return []
    return [str(x).strip() for x in paths if str(x).strip()]


def run_tank(task: Dict[str, Any]) -> Dict[str, Any]:
    priority = str(task.get("priority", "normal")).strip().lower()
    paths = _extract_paths(task)
    cooldown_view = filter_targets_on_cooldown(paths, priority=priority) if paths else {
        "ok": True, "allowed": [], "blocked": [], "dead": []
    }

    route = route_task(task)
    mode = "party" if should_use_party(task) else "pair"

    return {
        "ok": True,
        "role": "TANK",
        "route": route,
        "mode": mode,
        "cooldown_view": cooldown_view,
        "reason": "routing_complete",
    }
