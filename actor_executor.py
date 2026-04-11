from typing import Dict, Any
from runtime_experimental.object_store import get_open_tasks

STRUCTURAL_PROBLEMS = {
    "missing_init",
    "missing_init_group",
    "python_without_docs",
    "package_structure",
    "missing_root_readme",
    "missing_start_here",
}

META_PROBLEMS = {
    "routing_failure",
    "no_target_path",
    "global_block",
}


def get_problem(task: Dict[str, Any]) -> str:
    payload = task.get("payload", {})
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("problem", "")).strip().lower()


def is_structural(task: Dict[str, Any]) -> bool:
    return get_problem(task) in STRUCTURAL_PROBLEMS


def is_meta(task: Dict[str, Any]) -> bool:
    return get_problem(task) in META_PROBLEMS


def select_task():
    tasks = get_open_tasks()
    if not tasks:
        return None

    # 🔥 1. Structural first
    structural_tasks = [t for t in tasks if is_structural(t)]
    if structural_tasks:
        return structural_tasks[0]

    # 🔥 2. Normal tasks
    normal_tasks = [t for t in tasks if not is_meta(t)]
    if normal_tasks:
        return normal_tasks[0]

    # 🔥 3. Fallback
    return tasks[0]
