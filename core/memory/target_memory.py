from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List


MEMORY_FILE = Path("reports/target_memory.json")
MEMORY_FILE.parent.mkdir(exist_ok=True)

DEFAULT_TARGET_COOLDOWN_SECONDS = 1800
SHORT_RETRY_COOLDOWN_SECONDS = 300
MEDIUM_RETRY_COOLDOWN_SECONDS = 900
LONG_RETRY_COOLDOWN_SECONDS = 3600

PRIORITY_BASE = {
    "critical": 60,
    "high": 300,
    "normal": 900,
    "low": 1800,
}


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


def resolve_retry_cooldown(reason: str, attempts: int, priority: str = "normal") -> int:
    reason = str(reason or "").strip().lower()
    priority = str(priority or "normal").strip().lower()
    base = PRIORITY_BASE.get(priority, PRIORITY_BASE["normal"])

    if "success" in reason:
        return max(base, DEFAULT_TARGET_COOLDOWN_SECONDS if priority != "critical" else 300)

    if attempts <= 1:
        return max(60, min(base, SHORT_RETRY_COOLDOWN_SECONDS))

    if attempts <= 3:
        return max(base, MEDIUM_RETRY_COOLDOWN_SECONDS)

    return max(base, LONG_RETRY_COOLDOWN_SECONDS)


def touch_targets(
    targets: List[str],
    reason: str = "",
    cooldown_seconds: int | None = None,
    priority: str = "normal",
) -> Dict[str, Any]:
    state = _load_state()
    bucket = state.setdefault("targets", {})
    count = 0

    for target in targets:
        st = str(target).strip()
        if not st:
            continue

        old = bucket.get(st, {})
        attempts = int(old.get("attempts", 0)) + 1

        cd = cooldown_seconds
        if cd is None:
            cd = resolve_retry_cooldown(reason, attempts, priority=priority)

        bucket[st] = {
            "last_seen": _now_iso(),
            "reason": reason,
            "cooldown_seconds": int(cd),
            "attempts": attempts,
            "priority": priority,
        }
        count += 1

    _save_state(state)
    return {"ok": True, "count": count}


def _priority_rank(priority: str) -> int:
    mapping = {
        "critical": 0,
        "high": 1,
        "normal": 2,
        "low": 3,
    }
    return mapping.get(str(priority or "normal").strip().lower(), 2)


def filter_targets_on_cooldown(targets: List[str], priority: str = "normal") -> Dict[str, Any]:
    state = _load_state()
    bucket = state.get("targets", {})

    allowed: List[str] = []
    blocked: List[str] = []
    blocked_meta: Dict[str, Any] = {}

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
            attempts = int(item.get("attempts", 0))
            saved_priority = str(item.get("priority", "normal"))
        except Exception:
            allowed.append(st)
            continue

        until = last_seen + timedelta(seconds=cooldown_seconds)
        if now < until:
            blocked.append(st)
            blocked_meta[st] = {
                "cooldown_until": until.isoformat(),
                "attempts": attempts,
                "reason": item.get("reason", ""),
                "priority": saved_priority,
            }
        else:
            allowed.append(st)

    allowed = sorted(allowed, key=lambda x: _priority_rank(priority))
    blocked = sorted(blocked, key=lambda x: _priority_rank(blocked_meta.get(x, {}).get("priority", "normal")))

    return {
        "ok": True,
        "allowed": allowed,
        "blocked": blocked,
        "blocked_meta": blocked_meta,
    }


def mark_target_success(targets: List[str], priority: str = "normal") -> Dict[str, Any]:
    return touch_targets(
        targets,
        reason="import_fix_success",
        cooldown_seconds=resolve_retry_cooldown("success", attempts=1, priority=priority),
        priority=priority,
    )


def mark_target_no_change(targets: List[str], priority: str = "normal") -> Dict[str, Any]:
    return touch_targets(targets, reason="import_no_change", cooldown_seconds=None, priority=priority)


def mark_target_validation_failed(targets: List[str], priority: str = "normal") -> Dict[str, Any]:
    return touch_targets(targets, reason="import_validation_failed", cooldown_seconds=None, priority=priority)


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
