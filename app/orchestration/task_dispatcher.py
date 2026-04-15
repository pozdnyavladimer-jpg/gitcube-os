from __future__ import annotations

from typing import Dict, Any, List

from app.orchestration.router_engine import route_task
from core.field.v_core_self_stabilizing_mesh import stabilize_task_mesh
from core.execution.structural_fix_engine import execute_structural_fix
from core.execution.llm_fix_engine import (
    apply_llm_fix_multi,
    rollback_changed_files,
    finalize_backups,
)
from core.validation.healer_validator import validate_changed_files
from core.validation.import_validator import validate_import_targets


def _pick_cluster_targets(task: Dict[str, Any], mesh_result: Dict[str, Any]) -> List[str]:
    recommended = mesh_result.get("recommended_targets", [])
    targets: List[str] = []

    if isinstance(recommended, list):
        for p in recommended:
            sp = str(p).strip()
            if sp:
                targets.append(sp)

    if not targets:
        payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
        paths = payload.get("paths", [])
        if isinstance(paths, list):
            for p in paths:
                sp = str(p).strip()
                if sp:
                    targets.append(sp)

    py_targets = [p for p in targets if p.endswith(".py")]

    out: List[str] = []
    seen = set()
    for p in py_targets:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)

    return out[:3]


def _run_import_mesh(task: Dict[str, Any], mesh_result: Dict[str, Any]) -> Dict[str, Any]:
    score = float(mesh_result.get("stabilization_score", 0.0) or 0.0)
    if score < 0.6:
        return {
            "route": "IMPORT_LLM_MESH",
            "mesh": mesh_result,
            "execution": {
                "ok": False,
                "reason": "blocked_low_stabilization_score",
                "changed_files": [],
            },
            "validation": {
                "ok": False,
                "errors": [f"blocked_low_stabilization_score:{score}"],
            },
            "ok": False,
        }

    target_files = _pick_cluster_targets(task, mesh_result)
    if not target_files:
        return {
            "route": "IMPORT_LLM_MESH",
            "mesh": mesh_result,
            "execution": {
                "ok": False,
                "reason": "no_python_targets",
                "changed_files": [],
            },
            "validation": {
                "ok": False,
                "errors": ["no_python_targets"],
            },
            "ok": False,
        }

    execution_result = apply_llm_fix_multi(task, target_files)
    changed = execution_result.get("changed_files", [])
    validate_targets = changed if changed else target_files
    validation_result = validate_import_targets(validate_targets)

    if execution_result.get("ok", False) and not validation_result.get("ok", False) and changed:
        rollback_result = rollback_changed_files(changed)
        return {
            "route": "IMPORT_LLM_MESH",
            "mesh": mesh_result,
            "targets": target_files,
            "execution": execution_result,
            "validation": validation_result,
            "rollback": rollback_result,
            "ok": False,
        }

    if changed and validation_result.get("ok", False):
        finalize_backups(changed)

    return {
        "route": "IMPORT_LLM_MESH",
        "mesh": mesh_result,
        "targets": target_files,
        "execution": execution_result,
        "validation": validation_result,
        "ok": mesh_result.get("ok", False)
        and execution_result.get("ok", False)
        and validation_result.get("ok", False),
    }


def dispatch_task(task: Dict[str, Any]) -> Dict[str, Any]:
    route = route_task(task)

    if route == "STRUCTURAL_MESH":
        mesh_result = stabilize_task_mesh(task)
        execution_result = execute_structural_fix(task, mesh_result)
        validation_result = validate_changed_files(execution_result.get("changed_files", []))

        result = {
            "route": route,
            "mesh": mesh_result,
            "execution": execution_result,
            "validation": validation_result,
            "ok": mesh_result.get("ok", False)
            and execution_result.get("ok", False)
            and validation_result.get("ok", False),
        }

        changed_files = execution_result.get("changed_files", [])
        py_files = [p for p in changed_files if str(p).endswith(".py")]

        if result["ok"] and py_files:
            import_task = {
                **task,
                "problem": "broken_import_group",
                "payload": {
                    "problem": "broken_import_group",
                    "paths": py_files,
                },
            }
            import_mesh_result = stabilize_task_mesh(import_task)
            chained = _run_import_mesh(import_task, import_mesh_result)
            result["chained_import_mesh"] = chained

        return result

    if route == "IMPORT_LLM_MESH":
        mesh_result = stabilize_task_mesh(task)
        return _run_import_mesh(task, mesh_result)

    return {
        "route": route,
        "ok": False,
        "reason": "route_not_implemented_yet",
    }


if __name__ == "__main__":
    demo_task = {
        "problem": "structural_orphans_group",
        "paths": ["core.policy.safety_policy"],
        "priority": "high",
        "payload": {
            "problem": "structural_orphans_group",
            "paths": ["core.policy.safety_policy"],
        },
    }
    print(dispatch_task(demo_task))
