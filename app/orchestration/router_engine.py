from __future__ import annotations

from typing import Dict, Any


def route_task(task: Dict[str, Any]) -> str:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    problem = str(payload.get("problem", task.get("problem", ""))).strip().lower()

    structural_mesh_problems = {
        "missing_init_group",
        "missing_init",
        "package_structure",
        "structural_orphans_group",
        "missing_module_group",
        "broken_module_group",
    }

    import_llm_mesh_problems = {
        "broken_import_group",
    }

    if problem in structural_mesh_problems:
        return "STRUCTURAL_MESH"

    if problem in import_llm_mesh_problems:
        return "IMPORT_LLM_MESH"

    return "ROUTE_NOT_IMPLEMENTED"


if __name__ == "__main__":
    demos = [
        {"problem": "missing_init_group"},
        {"problem": "structural_orphans_group"},
        {"problem": "broken_import_group"},
        {"problem": "unknown_problem"},
    ]

    for item in demos:
        print(item["problem"], "->", route_task(item))
