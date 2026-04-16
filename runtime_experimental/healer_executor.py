from __future__ import annotations

from typing import Dict, Any

from core.memory.graph_weight_engine import apply_decay
from core.memory.task_cooldown import resolve_cooldown_seconds


def run_healer(task: Dict[str, Any], previous_result: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cooldown_seconds = resolve_cooldown_seconds(previous_result or {})
    decay_result = apply_decay()

    return {
        "ok": True,
        "role": "HEALER",
        "cooldown_seconds": cooldown_seconds,
        "decay": decay_result,
        "reason": "stabilization_complete",
    }
