from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any


IGNORED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
}


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def build_repo_snapshot(repo_root: str = ".") -> Dict[str, float]:
    root = Path(repo_root)
    snapshot: Dict[str, float] = {}

    for path in root.rglob("*.py"):
        if _is_ignored(path):
            continue
        try:
            snapshot[str(path)] = path.stat().st_mtime
        except Exception:
            continue

    return snapshot


def diff_repo_snapshot(old: Dict[str, float], new: Dict[str, float]) -> Dict[str, Any]:
    old = dict(old or {})
    new = dict(new or {})

    created: List[str] = []
    changed: List[str] = []
    deleted: List[str] = []

    old_keys = set(old.keys())
    new_keys = set(new.keys())

    for path in sorted(new_keys - old_keys):
        created.append(path)

    for path in sorted(old_keys - new_keys):
        deleted.append(path)

    for path in sorted(old_keys & new_keys):
        if float(old[path]) != float(new[path]):
            changed.append(path)

    touched = created + changed

    return {
        "ok": True,
        "created": created,
        "changed": changed,
        "deleted": deleted,
        "touched": touched,
        "has_changes": bool(created or changed or deleted),
    }


def build_change_event(diff: Dict[str, Any], priority: str = "high") -> Dict[str, Any]:
    touched = list(diff.get("touched", []))

    return {
        "priority": priority,
        "payload": {
            "problem": "broken_import_group",
            "paths": touched[:8],
            "has_shadow_backup": True,
        },
    }


if __name__ == "__main__":
    from pprint import pprint
    snap = build_repo_snapshot(".")
    pprint({
        "ok": True,
        "file_count": len(snap),
        "sample": sorted(list(snap.keys()))[:10],
    })
