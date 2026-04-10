from typing import Dict, Any, Tuple
from runtime_experimental.object_store import load_objects
from runtime_experimental.github_bridge import (
    is_github_enabled,
    find_open_issue_by_meta_key,
)

META_PROBLEMS = {
    "routing_failure",
    "no_target_path",
    "global_block",
}


def normalize_problem(payload: Dict[str, Any]) -> str:
    return str((payload or {}).get("problem", "")).strip().lower()


def has_similar_open_task(payload: Dict[str, Any]) -> bool:
    problem = normalize_problem(payload)
    if not problem:
        return False

    for obj in load_objects():
        if obj.get("type") != "task":
            continue
        if str(obj.get("status", "")).strip().lower() != "open":
            continue

        other_payload = obj.get("payload", {}) or {}
        other_problem = normalize_problem(other_payload)

        if other_problem == problem:
            return True

    return False


def has_similar_issue(meta_key: str) -> bool:
    if not meta_key:
        return False

    if not is_github_enabled():
        return False

    issue = find_open_issue_by_meta_key(meta_key)
    return bool(issue)


def should_block_task(payload: Dict[str, Any], meta_key: str) -> Tuple[bool, str]:
    """
    Блокуємо тільки META problems.
    Structural tasks не блокуємо цим guard-ом.
    """
    problem = normalize_problem(payload)

    if problem not in META_PROBLEMS:
        return False, "not_meta_problem"

    if has_similar_open_task(payload):
        return True, "duplicate_open_task"

    if has_similar_issue(meta_key):
        return True, "duplicate_issue"

    return False, "ok"
