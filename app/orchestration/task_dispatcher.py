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
from core.memory.target_memory import (
    filter_targets_on_cooldown,
    mark_target_success,
    mark_target_no_change,
    mark_target_validation_failed,
)


MAGE_SAFE_PROBLEMS = {
    "broken_import_group",
    "missing_init_group",
    "missing_init",
    "package_structure",
    "structural_orphans_group",
    "missing_module_group",
    "broken_module_group",
    "python_without_docs",
    "missing_root_readme",
    "missing_start_here",
    "empty_directories_group",
}

STRUCTURAL_FALLBACK = {
    "missing_init_group",
    "missing_init",
    "package_structure",
    "structural_orphans_group",
    "missing_module_group",
    "broken_module_group",
    "python_without_docs",
    "missing_root_readme",
    "missing_start_here",
    "empty_directories_group",
    "pass_blocks_group",
    "debug_prints_group",
    "todo_group",
    "bare_except_group",
}

IMPORT_FALLBACK = {
    "broken_import_group",
    "broken_imports",
    "missing_imports",
    "import_error",
}


def _task_priority(task: Dict[str, Any]) -> str:
    value = str(task.get("priority", "normal")).strip().lower()
    if value in {"critical", "high", "normal", "low"}:
        return value
    return "normal"


def _prepare_task(task: Dict[str, Any]) -> Dict[str, Any]:
    prepared = dict(task or {})
    payload = dict(prepared.get("payload", {}) or {})

    problem = str(payload.get("problem", prepared.get("problem", ""))).strip().lower()
    priority = _task_priority(prepared)

    if problem:
        prepared["problem"] = problem
        payload.setdefault("problem", problem)

    prepared["priority"] = priority

    if problem in MAGE_SAFE_PROBLEMS:
        payload.setdefault("has_shadow_backup", True)
        payload.setdefault("executor_hint", "MAGE")

    prepared["payload"] = payload
    return prepared


def _normalize_targets(raw_targets: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()

    for item in raw_targets:
        sp = str(item).strip()
        if not sp:
            continue

        if sp.endswith(".py"):
            target = sp
        else:
            target = sp.replace(".", "/") + ".py"

        if target in seen:
            continue
        seen.add(target)
        out.append(target)

    return out


def _pick_cluster_targets(task: Dict[str, Any], mesh_result: Dict[str, Any]) -> List[str]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    problem = str(payload.get("problem", task.get("problem", ""))).strip().lower()

    raw_targets: List[str] = []

    # для broken_import_group довіряємо payload.paths в першу чергу
    if problem == "broken_import_group":
        paths = payload.get("paths", [])
        if isinstance(paths, list):
            raw_targets.extend(str(p).strip() for p in paths if str(p).strip())

    if not raw_targets:
        recommended = mesh_result.get("recommended_targets", [])
        if isinstance(recommended, list):
            raw_targets.extend(str(p).strip() for p in recommended if str(p).strip())

    if not raw_targets:
        paths = payload.get("paths", [])
        if isinstance(paths, list):
            raw_targets.extend(str(p).strip() for p in paths if str(p).strip())

    normalized = _normalize_targets(raw_targets)
    py_targets = [p for p in normalized if p.endswith(".py")]
    return py_targets[:5]


def _select_reroute_targets(
    target_files: List[str],
    priority: str,
) -> Dict[str, Any]:
    cooldown_filter = filter_targets_on_cooldown(target_files, priority=priority)

    allowed_targets = cooldown_filter.get("allowed", [])
    blocked_targets = cooldown_filter.get("blocked", [])
    dead_targets = cooldown_filter.get("dead", [])
    blocked_meta = cooldown_filter.get("blocked_meta", {})
    dead_meta = cooldown_filter.get("dead_meta", {})

    chosen: List[str] = []
    rerouted = False
    reroute_from: List[str] = []

    if allowed_targets:
        chosen = allowed_targets[:3]
        if chosen != target_files[:len(chosen)]:
            rerouted = True
            reroute_from = target_files[:3]
    else:
        if priority == "critical":
            for candidate in target_files:
                if candidate not in dead_targets:
                    chosen = [candidate]
                    rerouted = True
                    reroute_from = target_files[:3]
                    blocked_targets = [t for t in blocked_targets if t != candidate]
                    blocked_meta.pop(candidate, None)
                    break

    return {
        "chosen": chosen,
        "blocked_targets": blocked_targets,
        "dead_targets": dead_targets,
        "blocked_meta": blocked_meta,
        "dead_meta": dead_meta,
        "rerouted": rerouted,
        "reroute_from": reroute_from,
    }


def _run_import_mesh(task: Dict[str, Any], mesh_result: Dict[str, Any]) -> Dict[str, Any]:
    priority = _task_priority(task)

    score = float(mesh_result.get("stabilization_score", 0.0) or 0.0)

    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    has_shadow_backup = bool(payload.get("has_shadow_backup", False))
    problem = str(payload.get("problem", task.get("problem", ""))).strip().lower()

    emergency_pass = (
        has_shadow_backup
        and problem in MAGE_SAFE_PROBLEMS
        and priority in {"high", "critical"}
    )

    if score < 0.6 and priority not in {"critical"} and not emergency_pass:
        return {
            "route": "IMPORT_LLM_MESH",
            "mesh": mesh_result,
            "execution": {"ok": False, "reason": "blocked_low_stabilization_score"},
            "validation": {"ok": False},
            "ok": False,
        }

    target_files = _pick_cluster_targets(task, mesh_result)
    if not target_files:
        return {
            "route": "IMPORT_LLM_MESH",
            "mesh": mesh_result,
            "execution": {"ok": False, "reason": "no_python_targets"},
            "validation": {"ok": False},
            "ok": False,
        }

    selection = _select_reroute_targets(target_files, priority=priority)

    allowed_targets = selection["chosen"]
    blocked_targets = selection["blocked_targets"]
    dead_targets = selection["dead_targets"]
    blocked_meta = selection["blocked_meta"]
    dead_meta = selection["dead_meta"]
    rerouted = selection["rerouted"]
    reroute_from = selection["reroute_from"]

    if not allowed_targets:
        reason = "all_targets_dead_locked" if dead_targets else "all_targets_on_cooldown"
        return {
            "route": "IMPORT_LLM_MESH",
            "mesh": mesh_result,
            "targets": target_files,
            "blocked_targets": blocked_targets,
            "dead_targets": dead_targets,
            "blocked_meta": blocked_meta,
            "dead_meta": dead_meta,
            "rerouted": rerouted,
            "reroute_from": reroute_from,
            "execution": {"ok": False, "reason": reason},
            "validation": {"ok": False},
            "ok": False,
        }

    execution_result = apply_llm_fix_multi(task, allowed_targets)
    changed = execution_result.get("changed_files", [])
    validate_targets = changed if changed else allowed_targets
    validation_result = validate_import_targets(validate_targets)

    if execution_result.get("ok", False) and not validation_result.get("ok", False) and changed:
        rollback_result = rollback_changed_files(changed)
        mark_target_validation_failed(allowed_targets, priority=priority)
        return {
            "route": "IMPORT_LLM_MESH",
            "mesh": mesh_result,
            "targets": allowed_targets,
            "blocked_targets": blocked_targets,
            "dead_targets": dead_targets,
            "blocked_meta": blocked_meta,
            "dead_meta": dead_meta,
            "rerouted": rerouted,
            "reroute_from": reroute_from,
            "execution": execution_result,
            "validation": validation_result,
            "rollback": rollback_result,
            "ok": False,
        }

    if changed and validation_result.get("ok", False):
        finalize_backups(changed)
        mark_target_success(allowed_targets, priority=priority)
    else:
        mark_target_no_change(allowed_targets, priority=priority)

    return {
        "route": "IMPORT_LLM_MESH",
        "mesh": mesh_result,
        "targets": allowed_targets,
        "blocked_targets": blocked_targets,
        "dead_targets": dead_targets,
        "blocked_meta": blocked_meta,
        "dead_meta": dead_meta,
        "rerouted": rerouted,
        "reroute_from": reroute_from,
        "priority": priority,
        "execution": execution_result,
        "validation": validation_result,
        "ok": execution_result.get("ok", False)
        and validation_result.get("ok", False),
    }



def _merge_priority(events: List[Dict[str, Any]]) -> str:
    order = {
        "critical": 0,
        "high": 1,
        "normal": 2,
        "low": 3,
    }

    best = "normal"
    best_rank = order[best]

    for ev in events:
        rank = order.get(_task_priority(ev), 2)
        if rank < best_rank:
            best_rank = rank
            for name, value in order.items():
                if value == rank:
                    best = name
                    break

    return best


def build_kernel_state() -> Dict[str, Any]:
    return {
        "mode": "idle",
        "tick": 0,
        "last_route": "",
        "last_problem": "",
        "last_result": None,
        "pending_events": [],
        "merged_task": None,
        "hotspots": {},
    }


def ingest_event(kernel_state: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    state = dict(kernel_state or {})
    pending = list(state.get("pending_events", []))
    pending.append(dict(event or {}))
    state["pending_events"] = pending
    return state


def merge_pending_events(kernel_state: Dict[str, Any]) -> Dict[str, Any]:
    state = dict(kernel_state or {})
    pending = list(state.get("pending_events", []))

    raw_paths: List[str] = []
    problems: List[str] = []
    scope_payloads: List[Dict[str, Any]] = []

    for ev in pending:
        payload = dict(ev.get("payload", {}) or {})

        ev_paths = payload.get("paths", [])
        if isinstance(ev_paths, list):
            raw_paths.extend(str(p).strip() for p in ev_paths if str(p).strip())

        problem = str(payload.get("problem", ev.get("problem", ""))).strip().lower()
        if problem:
            problems.append(problem)

        if isinstance(ev.get("_repair_scope"), dict):
            scope_payloads.append(dict(ev["_repair_scope"]))

    merged_problem = problems[0] if problems else "broken_import_group"
    merged_priority = _merge_priority(pending)
    merged_paths = _normalize_targets(raw_paths)[:8]

    merged_scope: Dict[str, Any] = {
        "targets": [],
        "dependents": {},
        "scope": [],
    }

    seen_targets = set()
    seen_scope = set()

    for scope_info in scope_payloads:
        targets = scope_info.get("targets", [])
        if isinstance(targets, list):
            for t in targets:
                st = str(t).strip()
                if st and st not in seen_targets:
                    seen_targets.add(st)
                    merged_scope["targets"].append(st)

        dependents = scope_info.get("dependents", {})
        if isinstance(dependents, dict):
            for k, v in dependents.items():
                sk = str(k).strip()
                if not sk:
                    continue
                merged_scope["dependents"].setdefault(sk, [])
                if isinstance(v, list):
                    for item in v:
                        sv = str(item).strip()
                        if sv and sv not in merged_scope["dependents"][sk]:
                            merged_scope["dependents"][sk].append(sv)

        scope = scope_info.get("scope", [])
        if isinstance(scope, list):
            for item in scope:
                sv = str(item).strip()
                if sv and sv not in seen_scope:
                    seen_scope.add(sv)
                    merged_scope["scope"].append(sv)

    merged_task = {
        "id": f"tick_{int(state.get('tick', 0)) + 1}",
        "priority": merged_priority,
        "payload": {
            "problem": merged_problem,
            "paths": merged_paths,
            "has_shadow_backup": merged_problem in MAGE_SAFE_PROBLEMS,
            "executor_hint": "MAGE" if merged_problem in MAGE_SAFE_PROBLEMS else "",
        },
    }

    if merged_scope["targets"] or merged_scope["scope"]:
        merged_task["_repair_scope"] = merged_scope

    state["pending_events"] = []
    state["merged_task"] = merged_task
    return state


def dispatch_tick(kernel_state: Dict[str, Any]) -> Dict[str, Any]:
    state = dict(kernel_state or {})
    state["tick"] = int(state.get("tick", 0)) + 1

    pending = list(state.get("pending_events", []))
    if not pending:
        state["mode"] = "idle"
        state["last_result"] = {
            "ok": True,
            "reason": "no_pending_events",
            "tick": state["tick"],
        }
        return state

    state["mode"] = "sense"
    state = merge_pending_events(state)

    task = dict(state.get("merged_task", {}) or {})
    if not task:
        state["mode"] = "idle"
        state["last_result"] = {
            "ok": False,
            "reason": "merged_task_missing",
            "tick": state["tick"],
        }
        return state

    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    state["last_problem"] = str(payload.get("problem", task.get("problem", ""))).strip().lower()

    state["mode"] = "route"
    result = dispatch_task(task)

    state["last_route"] = str(result.get("route", "")).strip()
    state["last_result"] = result

    validation = result.get("validation", {}) if isinstance(result.get("validation"), dict) else {}
    execution = result.get("execution", {}) if isinstance(result.get("execution"), dict) else {}

    if result.get("ok", False):
        state["mode"] = "cooldown"
    elif execution.get("reason") in {"all_targets_on_cooldown", "all_targets_dead_locked"}:
        state["mode"] = "cooldown"
    elif validation.get("ok", True) is False:
        state["mode"] = "repair"
    else:
        state["mode"] = "idle"

    hotspots = dict(state.get("hotspots", {}) or {})
    problem = state["last_problem"] or "unknown_problem"
    hotspots[problem] = int(hotspots.get(problem, 0)) + 1
    state["hotspots"] = hotspots

    return state


def dispatch_task(task: Dict[str, Any]) -> Dict[str, Any]:
    task = _prepare_task(task)
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

        if not py_files:
            recommended = mesh_result.get("recommended_targets", [])
            if isinstance(recommended, list):
                py_files = _normalize_targets(recommended)

        if result["ok"] and py_files:
            import_task = {
                **task,
                "problem": "broken_import_group",
                "payload": {
                    **dict(task.get("payload", {}) or {}),
                    "problem": "broken_import_group",
                    "paths": py_files,
                    "has_shadow_backup": True,
                    "executor_hint": "MAGE",
                },
            }
            import_mesh_result = stabilize_task_mesh(import_task)
            chained = _run_import_mesh(import_task, import_mesh_result)
            result["chained_import_mesh"] = chained

        return result

    if route == "IMPORT_LLM_MESH":
        mesh_result = stabilize_task_mesh(task)
        return _run_import_mesh(task, mesh_result)

    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    problem = str(payload.get("problem", task.get("problem", ""))).strip().lower()

    if problem in STRUCTURAL_FALLBACK:
        mesh_result = stabilize_task_mesh(task)
        execution_result = execute_structural_fix(task, mesh_result)
        validation_result = validate_changed_files(execution_result.get("changed_files", []))
        return {
            "route": "STRUCTURAL_MESH_FALLBACK",
            "mesh": mesh_result,
            "execution": execution_result,
            "validation": validation_result,
            "ok": mesh_result.get("ok", False)
            and execution_result.get("ok", False)
            and validation_result.get("ok", False),
            "reason": "fallback_structural_mesh",
        }

    if problem in IMPORT_FALLBACK or "import" in problem:
        mesh_result = stabilize_task_mesh(task)
        result = _run_import_mesh(task, mesh_result)
        result["reason"] = result.get("reason", "fallback_import_mesh")
        result["route"] = "IMPORT_LLM_MESH_FALLBACK"
        return result

    return {
        "route": route,
        "ok": False,
        "reason": "route_not_implemented_yet",
        "problem": problem,
    }


if __name__ == "__main__":
    demo_task = {
        "problem": "broken_import_group",
        "paths": [
            "core/policy/safety_policy.py",
            "repo_analyzer.py",
            "router.py",
        ],
        "priority": "high",
        "payload": {
            "problem": "broken_import_group",
            "paths": [
                "core/policy/safety_policy.py",
                "repo_analyzer.py",
                "router.py",
            ],
        },
    }
    print(dispatch_task(demo_task))
