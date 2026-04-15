from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List


MEMORY_FILE = Path("reports/target_memory.json")
MEMORY_FILE.parent.mkdir(exist_ok=True)

DEFAULT_TARGET_COOLDOWN_SECONDS = 1800  # 30 хв


def _now() -> datetime:
    return datetime.now(UTC)


def _now_iso() -> str:
    return _now().isoformat()


def _load_state() -> Dict[str, Any]:
    if not MEMORY_FILE.exists():
        return {"targets": {}}
    try:
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"targets": {}}


def _save_state(state: Dict[str, Any]) -> None:
    MEMORY_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def touch_targets(
    targets: List[str],
    reason: str = "",
    cooldown_seconds: int = DEFAULT_TARGET_COOLDOWN_SECONDS,
) -> Dict[str, Any]:
    state = _load_state()
    bucket = state.setdefault("targets", {})

    for target in targets:
        st = str(target).strip()
        if not st:
            continue
        bucket[st] = {
            "last_seen": _now_iso(),
            "reason": reason,
            "cooldown_seconds": int(cooldown_seconds),
        }

    _save_state(state)
    return {"ok": True, "count": len(targets)}


def filter_targets_on_cooldown(targets: List[str]) -> Dict[str, Any]:
    state = _load_state()
    bucket = state.get("targets", {})

    allowed: List[str] = []
    blocked: List[str] = []

    now = _now()

    for target in targets:
        st = str(target).strip()
        if not st:
            continue

        item = bucket.get(st)
        if not item:
            allowed.append(st)
            continue

        try:
            last_seen = datetime.fromisoformat(item["last_seen"])
            cooldown_seconds = int(item.get("cooldown_seconds", DEFAULT_TARGET_COOLDOWN_SECONDS))
        except Exception:
            allowed.append(st)
            continue

        until = last_seen + timedelta(seconds=cooldown_seconds)
        if now < until:
            blocked.append(st)
        else:
            allowed.append(st)

    return {
        "ok": True,
        "allowed": allowed,
        "blocked": blocked,
    }


def clear_target(target: str) -> Dict[str, Any]:
    state = _load_state()
    bucket = state.setdefault("targets", {})
    st = str(target).strip()
    if st in bucket:
        del bucket[st]
        _save_state(state)
    return {"ok": True, "target": st}


def clear_all_target_memory() -> Dict[str, Any]:
    _save_state({"targets": {}})
    return {"ok": True}
