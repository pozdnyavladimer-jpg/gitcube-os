from __future__ import annotations

from typing import Dict, Any

from app.orchestration.router_engine import route_task
from core.field.v_core_self_stabilizing_mesh import stabilize_task_mesh
from core.execution.structural_fix_engine import execute_structural_fix
from core.execution.llm_fix_engine import apply_llm_fix
from core.validation.healer_validator import validate_changed_files
from core.validation.import_validator import validate_import_targets


def dispatch_task(task: Dict[str, Any]) -> Dict[str, Any]:
    route = route_task(task)

    if route == "STRUCTURAL_MESH":
        mesh_result = stabilize_task_mesh(task)
        execution_result = execute_structural_fix(task, mesh_result)
        validation_result = validate_changed_files(execution_result.get("changed_files", []))

        return {
            "route": route,
            "mesh": mesh_result,
            "execution": execution_result,
            "validation": validation_result,
            "ok": mesh_result.get("ok", False)
            and execution_result.get("ok", False)
            and validation_result.get("ok", False),
        }

    if route == "IMPORT_LLM_MESH":
        mesh_result = stabilize_task_mesh(task)

        paths = task.get("paths", [])
        target_file = ""
        if isinstance(paths, list):
            for p in paths:
                s = str(p).strip()
                if s.endswith(".py"):
                    target_file = s
                    break

        if not target_file:
            return {
                "route": route,
                "mesh": mesh_result,
                "execution": {"ok": False, "reason": "no_python_target", "changed_files": []},
                "validation": {"ok": False, "errors": ["no_python_target"]},
                "ok": False,
            }

        execution_result = apply_llm_fix(task, target_file)
        changed = execution_result.get("changed_files", [])
        validate_targets = changed if changed else [target_file]
        validation_result = validate_import_targets(validate_targets)

        return {
            "route": route,
            "mesh": mesh_result,
            "execution": execution_result,
            "validation": validation_result,
            "ok": mesh_result.get("ok", False)
            and execution_result.get("ok", False)
            and validation_result.get("ok", False),
        }

    return {
        "route": route,
        "ok": False,
        "reason": "route_not_implemented_yet",
    }


if __name__ == "__main__":
    demo_task = {
        "problem": "missing_init_group",
        "paths": ["core", "tests", "runtime_experimental"],
        "priority": "high",
    }
    print(dispatch_task(demo_task))
