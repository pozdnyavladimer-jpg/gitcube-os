from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, UTC, timedelta
from typing import Dict, Any


COOLDOWN_FILE = Path("reports/task_cooldown.json")
COOLDOWN_FILE.parent.mkdir(exist_ok=True)

DEFAULT_COOLDOWN_SECONDS = 900
SUCCESS_COOLDOWN_SECONDS = 1800
FAIL_COOLDOWN_SECONDS = 300
NO_CHANGE_COOLDOWN_SECONDS = 600


def _now() -> datetime:
    return datetime.now(UTC)


def _now_iso() -> str:
    return _now().isoformat()


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


def resolve_cooldown_seconds(result: Dict[str, Any] | None = None) -> int:
    if not isinstance(result, dict):
        return DEFAULT_COOLDOWN_SECONDS

    reason = str(result.get("reason", "")).strip().lower()
    ok = bool(result.get("ok", False))
    published = bool(result.get("published", False))

    if ok or published or "done" in reason:
        return SUCCESS_COOLDOWN_SECONDS

    if reason in {"no_changes", "task_on_cooldown"}:
        return NO_CHANGE_COOLDOWN_SECONDS

    return FAIL_COOLDOWN_SECONDS


def is_task_on_cooldown(task_id: str) -> Dict[str, Any]:
    state = _load_state()
    tasks = state.get("tasks", {})
    item = tasks.get(task_id)

    if not item:
        return {"ok": True, "on_cooldown": False}

    try:
        last_seen = datetime.fromisoformat(item["last_seen"])
        cooldown_seconds = int(item.get("cooldown_seconds", DEFAULT_COOLDOWN_SECONDS))
    except Exception:
        return {"ok": True, "on_cooldown": False}

    until = last_seen + timedelta(seconds=cooldown_seconds)
    now = _now()

    return {
        "ok": True,
        "on_cooldown": now < until,
        "last_seen": item.get("last_seen"),
        "cooldown_seconds": cooldown_seconds,
        "cooldown_until": until.isoformat(),
        "meta": item.get("meta", {}),
    }


def touch_task(
    task_id: str,
    meta: Dict[str, Any] | None = None,
    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS,
) -> Dict[str, Any]:
    state = _load_state()
    tasks = state.setdefault("tasks", {})
    tasks[task_id] = {
        "last_seen": _now_iso(),
        "cooldown_seconds": int(cooldown_seconds),
        "meta": meta or {},
    }
    _save_state(state)
    return {"ok": True, "task_id": task_id, "cooldown_seconds": int(cooldown_seconds)}


def set_task_cooldown_from_result(
    task_id: str,
    result: Dict[str, Any] | None,
    meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    cooldown_seconds = resolve_cooldown_seconds(result)
    return touch_task(task_id, meta=meta, cooldown_seconds=cooldown_seconds)


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
