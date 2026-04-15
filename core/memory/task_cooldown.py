from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, UTC, timedelta
from typing import Dict, Any


COOLDOWN_FILE = Path("reports/task_cooldown.json")
COOLDOWN_FILE.parent.mkdir(exist_ok=True)

DEFAULT_COOLDOWN_SECONDS = 900  # 15 хв


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_state() -> Dict[str, Any]:
    if not COOLDOWN_FILE.exists():
        return {"tasks": {}}

    try:
        return json.loads(COOLDOWN_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"tasks": {}}


def _save_state(state: Dict[str, Any]) -> None:
    COOLDOWN_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def is_task_on_cooldown(task_id: str, cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS) -> Dict[str, Any]:
    state = _load_state()
    tasks = state.get("tasks", {})
    item = tasks.get(task_id)

    if not item:
        return {"ok": True, "on_cooldown": False}

    try:
        last_seen = datetime.fromisoformat(item["last_seen"])
    except Exception:
        return {"ok": True, "on_cooldown": False}

    until = last_seen + timedelta(seconds=cooldown_seconds)
    now = datetime.now(UTC)

    return {
        "ok": True,
        "on_cooldown": now < until,
        "last_seen": item.get("last_seen"),
        "cooldown_until": until.isoformat(),
    }


def touch_task(task_id: str, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state = _load_state()
    tasks = state.setdefault("tasks", {})
    tasks[task_id] = {
        "last_seen": _now_iso(),
        "meta": meta or {},
    }
    _save_state(state)
    return {"ok": True, "task_id": task_id}


def clear_task(task_id: str) -> Dict[str, Any]:
    state = _load_state()
    tasks = state.setdefault("tasks", {})
    if task_id in tasks:
        del tasks[task_id]
        _save_state(state)
    return {"ok": True, "task_id": task_id}


def clear_all_cooldowns() -> Dict[str, Any]:
    _save_state({"tasks": {}})
    return {"ok": True}
