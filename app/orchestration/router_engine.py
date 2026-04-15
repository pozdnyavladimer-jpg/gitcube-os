from __future__ import annotations

from typing import Dict, Any


def route_task(task: Dict[str, Any]) -> str:
    problem = str(task.get("problem", "")).strip().lower()

    if problem in {"missing_init_group"}:
        return "STRUCTURAL_MESH"

    if problem in {"broken_import_group", "structural_orphans_group"}:
        return "LLM_OR_COMPLEX"

    return "DEFAULT"
