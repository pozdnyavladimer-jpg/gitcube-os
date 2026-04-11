from typing import Any, Dict, Optional, Tuple

from runtime_experimental.object_store import load_objects
from runtime_experimental.github_bridge import (
    is_github_enabled,
    find_open_issue_by_meta_key,
    normalize_meta_key,
)


def build_external_meta_key(task_obj: Dict[str, Any]) -> str:
    payload = task_obj.get("payload", {}) or {}

    payload_title = str(payload.get("title", "")).strip().lower()
    payload_origin = str(payload.get("origin", "")).strip().lower()

    kind = str(task_obj.get("kind", "task")).strip().lower()
    origin = str(task_obj.get("origin", "external")).strip().lower()

    raw = f"external|{kind}|{origin}|{payload_origin}|{payload_title}|no_path"
    return normalize_meta_key(raw)


def find_open_task_by_meta_key(meta_key: str) -> Optional[Dict[str, Any]]:
    if not meta_key:
        return None

    for obj in load_objects():
        if obj.get("type") != "task":
            continue
        if str(obj.get("status", "")).strip().lower() != "open":
            continue
        if str(obj.get("meta_key", "")).strip().lower() == str(meta_key).strip().lower():
            return obj

    return None


def should_create_external_task(task_obj: Dict[str, Any]) -> Tuple[bool, str]:
    meta_key = str(task_obj.get("meta_key", "")).strip()
    if not meta_key:
        return True, "missing_meta_key_allow"

    existing_open = find_open_task_by_meta_key(meta_key)
    if existing_open:
        return False, f"duplicate_open_task:{existing_open.get('id', '')}"

    if is_github_enabled():
        issue = find_open_issue_by_meta_key(meta_key)
        if issue:
            return False, f"absorbed_by_issue:{issue.get('url', '')}"

    return True, "create"
