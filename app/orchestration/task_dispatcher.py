from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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
from core.utils.shadow_autofix import autofix_shadowed_stdlib
from core.utils.auto_commit import auto_commit_changes
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



def _maybe_auto_commit(result: Dict[str, Any], problem: str) -> Dict[str, Any]:
    execution = result.get("execution", {}) if isinstance(result.get("execution"), dict) else {}
    changed_files = execution.get("changed_files", [])

    if not result.get("ok", False):
        return {"ok": False, "reason": "result_not_ok"}

    if not changed_files:
        return {"ok": False, "reason": "no_changed_files"}

    if result.get("rollback"):
        return {"ok": False, "reason": "rollback_present"}

    message = f"auto-repair: {problem}"
    return auto_commit_changes(changed_files, message)


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

    auto_commit_result = {"ok": False, "reason": "not_attempted"}

    if changed and validation_result.get("ok", False):
        finalize_backups(changed)
        mark_target_success(allowed_targets, priority=priority)
    else:
        mark_target_no_change(allowed_targets, priority=priority)

    result = {
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

    auto_commit_result = _maybe_auto_commit(result, problem)
    result["auto_commit"] = auto_commit_result
    return result



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
    merged_payload: Dict[str, Any] = {}

    for ev in pending:
        payload = dict(ev.get("payload", {}) or {})

        # Preserve full external/event payload.
        # The kernel may normalize problem/paths later, but fields like
        # intent, bridge, field_case, meta_key and resonance_vector must survive.
        for key, value in payload.items():
            if key == "paths":
                continue
            if value in (None, "", [], {}):
                continue
            merged_payload[key] = value

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

    final_payload = dict(merged_payload)
    final_payload["problem"] = merged_problem
    final_payload["paths"] = merged_paths

    if "has_shadow_backup" not in final_payload:
        final_payload["has_shadow_backup"] = merged_problem in MAGE_SAFE_PROBLEMS

    if not str(final_payload.get("executor_hint", "")).strip():
        final_payload["executor_hint"] = "MAGE" if merged_problem in MAGE_SAFE_PROBLEMS else ""

    merged_task = {
        "id": f"tick_{int(state.get('tick', 0)) + 1}",
        "priority": merged_priority,
        "payload": final_payload,
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



FIELD_INTENT_PROBLEMS = {
    "field_intent_phase_repair",
    "field_intent_memory_retention",
    "field_intent_clock_stabilization",
    "field_intent_disambiguation",
    "field_intent_synthesis",
    "field_intent_bridge_task",
}


def _run_field_intent_bridge_ack(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    problem = (
        task.get("problem")
        or payload.get("problem")
        or "field_intent_bridge_task"
    )

    intent = (
        task.get("intent")
        or payload.get("intent")
        or payload.get("verdict")
        or "UNKNOWN_INTENT"
    )

    bridge = (
        task.get("bridge")
        or payload.get("bridge")
        or "D46_FIELD_INTENT_BRIDGE"
    )

    target_agent = (
        task.get("target_agent")
        or task.get("executor_hint")
        or payload.get("target_agent")
        or payload.get("executor_hint")
        or "MAGE"
    )

    resonance_vector = payload.get("resonance_vector", {})
    if not isinstance(resonance_vector, dict):
        resonance_vector = {}

    return {
        "route": "FIELD_INTENT_BRIDGE_ACK",
        "ok": True,
        "reason": "field_intent_received",
        "problem": problem,
        "intent": intent,
        "bridge": bridge,
        "target_agent": target_agent,
        "field_case": task.get("field_case") or payload.get("field_case") or payload.get("case"),
        "meta_key": task.get("meta_key") or payload.get("meta_key"),
        "resonance_vector": resonance_vector,
        "execution": {
            "ok": True,
            "changed_files": [],
            "actions": [],
            "note": "ACK only. No code repair executed yet.",
        },
        "validation": {
            "ok": True,
            "errors": [],
            "note": "D46 bridge event accepted by GitCube OS.",
        },
        "auto_commit": {
            "ok": False,
            "reason": "ack_only_no_changed_files",
        },
    }


def _field_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _run_field_intent_repair_plan(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    problem = str(payload.get("problem") or task.get("problem") or "field_intent_phase_repair")
    intent = str(payload.get("intent") or task.get("intent") or "UNKNOWN_INTENT")
    bridge = str(payload.get("bridge") or task.get("bridge") or "D46_FIELD_INTENT_BRIDGE")
    field_case = str(payload.get("field_case") or payload.get("case") or task.get("field_case") or "UNKNOWN_CASE")
    meta_key = str(payload.get("meta_key") or task.get("meta_key") or "")

    target_agent = str(
        payload.get("target_agent")
        or payload.get("executor_hint")
        or task.get("target_agent")
        or task.get("executor_hint")
        or "MAGE"
    )

    resonance_vector = payload.get("resonance_vector", {})
    if not isinstance(resonance_vector, dict):
        resonance_vector = {}

    phase_error = _field_float(resonance_vector.get("phase_error"), _field_float(payload.get("phase_error"), 0.0))
    jitter = _field_float(resonance_vector.get("jitter"), _field_float(payload.get("jitter"), 0.0))
    ambiguity = _field_float(resonance_vector.get("ambiguity"), _field_float(payload.get("ambiguity"), 0.0))
    decay = _field_float(resonance_vector.get("decay"), _field_float(payload.get("decay"), 0.0))
    strength = _field_float(resonance_vector.get("strength"), _field_float(payload.get("strength"), 0.0))

    causes = []
    proposed = []

    if phase_error >= 0.25:
        causes.append("large_phase_drift")
        proposed.append("add phase resync before memory write")
        proposed.append("tighten phase lock validation for this spectral key")

    if jitter >= 0.20:
        causes.append("clock_jitter")
        proposed.append("route follow-up to HEALER clock stabilization")

    if ambiguity >= 0.25:
        causes.append("ambiguous_intent")
        proposed.append("route follow-up to TANK disambiguation gate")

    if decay >= 0.35:
        causes.append("memory_decay")
        proposed.append("route follow-up to HEALER memory retention")

    if not causes:
        causes.append("field_intent_requires_review")
        proposed.append("create diagnostic repair plan without code mutation")

    risk_level = "critical" if phase_error >= 0.30 or strength >= 0.80 else "high" if phase_error >= 0.18 else "medium"

    repair_plan = {
        "state": "FIELD_INTENT_REPAIR_PLAN",
        "result": "FIELD_INTENT_REPAIR_PLAN_CREATED",
        "source_task_id": task.get("id"),
        "problem": problem,
        "bridge": bridge,
        "intent": intent,
        "field_case": field_case,
        "meta_key": meta_key,
        "target_agent": target_agent,
        "resonance_vector": resonance_vector,
        "detected_cause": causes,
        "proposed_repair": proposed,
        "risk_level": risk_level,
        "validation_rule": {
            "phase_error_after_max": 0.12,
            "jitter_after_max": 0.08,
            "intent_must_remain": intent,
            "orbital_mode_must_remain": resonance_vector.get("orbital_mode"),
            "no_unvalidated_code_mutation": True
        },
        "success_condition": {
            "route": "FIELD_INTENT_REPAIR",
            "plan_created": True,
            "payload_preserved": True,
            "next_step": "MAGE may generate concrete patch only after this plan is reviewed"
        },
        "raw_payload": payload
    }

    out_path = Path("reports/field_intent_repair_plan.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(repair_plan, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "route": "FIELD_INTENT_REPAIR",
        "ok": True,
        "reason": "field_intent_repair_plan_created",
        "repair_plan_path": str(out_path),
        "problem": problem,
        "intent": intent,
        "bridge": bridge,
        "field_case": field_case,
        "meta_key": meta_key,
        "target_agent": target_agent,
        "resonance_vector": resonance_vector,
        "execution": {
            "ok": True,
            "changed_files": [str(out_path)],
            "actions": ["write_field_intent_repair_plan"],
            "note": "Plan only. No code mutation executed yet."
        },
        "validation": {
            "ok": True,
            "errors": [],
            "note": "Repair plan created and full D46 payload preserved."
        },
        "auto_commit": {
            "ok": False,
            "reason": "plan_only_manual_commit"
        }
    }


def _run_field_intent_executor(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    plan_path = Path(str(payload.get("plan_path") or "reports/field_intent_repair_plan.json"))
    if not plan_path.exists():
        return {
            "route": "FIELD_INTENT_EXECUTOR",
            "ok": False,
            "reason": "repair_plan_missing",
            "plan_path": str(plan_path),
            "execution": {
                "ok": False,
                "changed_files": [],
                "actions": [],
            },
            "validation": {
                "ok": False,
                "errors": ["repair plan not found"],
            },
        }

    try:
        repair_plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "route": "FIELD_INTENT_EXECUTOR",
            "ok": False,
            "reason": "repair_plan_read_error",
            "error": str(exc),
            "plan_path": str(plan_path),
            "execution": {
                "ok": False,
                "changed_files": [],
                "actions": [],
            },
            "validation": {
                "ok": False,
                "errors": [str(exc)],
            },
        }

    intent = str(repair_plan.get("intent") or payload.get("intent") or "UNKNOWN_INTENT")
    field_case = str(repair_plan.get("field_case") or payload.get("field_case") or "UNKNOWN_CASE")
    bridge = str(repair_plan.get("bridge") or payload.get("bridge") or "D47_FIELD_INTENT_EXECUTOR")
    problem = str(repair_plan.get("problem") or payload.get("problem") or "field_intent_execute_repair")
    target_agent = str(repair_plan.get("target_agent") or payload.get("target_agent") or payload.get("executor_hint") or "MAGE")

    resonance_vector = repair_plan.get("resonance_vector", {})
    if not isinstance(resonance_vector, dict):
        resonance_vector = {}

    causes = repair_plan.get("detected_cause", [])
    if not isinstance(causes, list):
        causes = [str(causes)]

    action = {
        "agent": target_agent,
        "mode": "PLAN_ONLY",
        "safe_to_mutate_code": False,
        "target_files": [],
        "executor_problem": "field_intent_executor_review",
        "reason": "generic_field_intent_review",
    }

    if "large_phase_drift" in causes:
        action.update({
            "agent": "MAGE",
            "executor_problem": "field_intent_phase_resync_patch",
            "reason": "phase_error_exceeds_threshold",
            "target_files": [
                "reports/field_intent_repair_plan.json"
            ],
            "recommended_next_file": "reports/d47_phase_resync_patch_request.json",
        })

    elif "clock_jitter" in causes:
        action.update({
            "agent": "HEALER",
            "executor_problem": "field_intent_clock_stabilization",
            "reason": "jitter_exceeds_threshold",
            "recommended_next_file": "reports/d47_clock_stabilization_request.json",
        })

    elif "ambiguous_intent" in causes:
        action.update({
            "agent": "TANK",
            "executor_problem": "field_intent_disambiguation_gate",
            "reason": "ambiguity_exceeds_threshold",
            "recommended_next_file": "reports/d47_disambiguation_request.json",
        })

    elif "memory_decay" in causes:
        action.update({
            "agent": "HEALER",
            "executor_problem": "field_intent_memory_retention",
            "reason": "decay_exceeds_threshold",
            "recommended_next_file": "reports/d47_memory_retention_request.json",
        })

    executor_action = {
        "state": "D47_FIELD_INTENT_EXECUTOR",
        "result": "FIELD_INTENT_EXECUTOR_ACTION_CREATED",
        "source_plan": str(plan_path),
        "problem": problem,
        "bridge": bridge,
        "intent": intent,
        "field_case": field_case,
        "resonance_vector": resonance_vector,
        "detected_cause": causes,
        "selected_action": action,
        "validation_rule": {
            "must_preserve_payload": True,
            "must_not_mutate_code_yet": True,
            "must_write_agent_action_file": True,
            "next_route_required": action.get("executor_problem"),
        },
        "success_condition": {
            "route": "FIELD_INTENT_EXECUTOR",
            "executor_action_created": True,
            "agent_selected": action.get("agent"),
            "next_step": "Generate concrete agent patch request in the recommended_next_file"
        },
        "raw_repair_plan": repair_plan,
    }

    out_path = Path("reports/field_intent_executor_action.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(executor_action, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "route": "FIELD_INTENT_EXECUTOR",
        "ok": True,
        "reason": "field_intent_executor_action_created",
        "executor_action_path": str(out_path),
        "source_plan": str(plan_path),
        "problem": problem,
        "intent": intent,
        "bridge": bridge,
        "field_case": field_case,
        "target_agent": action.get("agent"),
        "executor_problem": action.get("executor_problem"),
        "resonance_vector": resonance_vector,
        "execution": {
            "ok": True,
            "changed_files": [str(out_path)],
            "actions": ["write_field_intent_executor_action"],
            "note": "D47 action selected. No code mutation executed yet.",
        },
        "validation": {
            "ok": True,
            "errors": [],
            "note": "Executor action created from D46 repair plan.",
        },
        "auto_commit": {
            "ok": False,
            "reason": "executor_plan_only_manual_commit",
        },
    }


def _d48_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _run_field_intent_phase_resync_patch_request(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    action_path = Path(str(payload.get("action_path") or "reports/field_intent_executor_action.json"))
    if not action_path.exists():
        return {
            "route": "FIELD_INTENT_PHASE_RESYNC_PATCH_REQUEST",
            "ok": False,
            "reason": "executor_action_missing",
            "action_path": str(action_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": ["executor action file not found"]},
        }

    try:
        executor_action = json.loads(action_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "route": "FIELD_INTENT_PHASE_RESYNC_PATCH_REQUEST",
            "ok": False,
            "reason": "executor_action_read_error",
            "error": str(exc),
            "action_path": str(action_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": [str(exc)]},
        }

    repair_plan = executor_action.get("raw_repair_plan", {})
    if not isinstance(repair_plan, dict):
        repair_plan = {}

    resonance_vector = executor_action.get("resonance_vector", {})
    if not isinstance(resonance_vector, dict):
        resonance_vector = repair_plan.get("resonance_vector", {})
    if not isinstance(resonance_vector, dict):
        resonance_vector = {}

    memory_key = str(resonance_vector.get("memory_key") or "UNKNOWN_MEMORY_KEY")
    orbital_mode = str(resonance_vector.get("orbital_mode") or "UNKNOWN_ORBITAL")
    phase_error = _d48_float(resonance_vector.get("phase_error"), 0.0)
    jitter = _d48_float(resonance_vector.get("jitter"), 0.0)
    strength = _d48_float(resonance_vector.get("strength"), 0.0)
    ambiguity = _d48_float(resonance_vector.get("ambiguity"), 0.0)
    decay = _d48_float(resonance_vector.get("decay"), 0.0)

    intent = str(executor_action.get("intent") or repair_plan.get("intent") or payload.get("intent") or "NEEDS_PHASE_REPAIR")
    field_case = str(executor_action.get("field_case") or repair_plan.get("field_case") or payload.get("field_case") or "PHASE_DRIFT")
    bridge = str(executor_action.get("bridge") or repair_plan.get("bridge") or payload.get("bridge") or "D48_FIELD_INTENT_PHASE_RESYNC")
    problem = str(payload.get("problem") or executor_action.get("executor_problem") or "field_intent_phase_resync_patch")

    patch_request = {
        "state": "D48_FIELD_INTENT_PHASE_RESYNC_PATCH_REQUEST",
        "result": "PHASE_RESYNC_PATCH_REQUEST_CREATED",
        "source_action": str(action_path),
        "problem": problem,
        "bridge": bridge,
        "intent": intent,
        "field_case": field_case,
        "target_agent": "MAGE",
        "executor_problem": "field_intent_phase_resync_patch",
        "resonance_vector": resonance_vector,
        "diagnosis": {
            "memory_key": memory_key,
            "orbital_mode": orbital_mode,
            "phase_error": phase_error,
            "jitter": jitter,
            "strength": strength,
            "ambiguity": ambiguity,
            "decay": decay,
            "cause": "phase_error_exceeds_threshold" if phase_error >= 0.25 else "phase_repair_review"
        },
        "mage_request": {
            "task": "Generate a safe phase-resync patch proposal.",
            "mode": "PATCH_REQUEST_ONLY",
            "do_not_mutate_code_yet": True,
            "goal": "Reduce phase drift before memory write while preserving full D46 payload.",
            "suggested_strategy": [
                "add a phase_resync step before memory write",
                "clamp or normalize phase_error toward target threshold",
                "preserve orbital_mode and memory_key",
                "do not overwrite resonance_vector",
                "write patch proposal before any executable code change"
            ],
            "target_thresholds": {
                "phase_error_after_max": 0.12,
                "jitter_after_max": 0.08,
                "preserve_intent": intent,
                "preserve_orbital_mode": orbital_mode,
                "preserve_memory_key": memory_key
            },
            "candidate_target_files": [
                "app/orchestration/task_dispatcher.py",
                "runtime_experimental/v_kernel_daemon.py",
                "reports/field_intent_repair_plan.json",
                "reports/field_intent_executor_action.json"
            ]
        },
        "validation_rule": {
            "must_preserve_payload": True,
            "must_preserve_resonance_vector": True,
            "must_not_mutate_code_yet": True,
            "must_create_patch_proposal_file": True,
            "phase_error_after_max": 0.12,
            "jitter_after_max": 0.08
        },
        "success_condition": {
            "route": "FIELD_INTENT_PHASE_RESYNC_PATCH_REQUEST",
            "patch_request_created": True,
            "target_agent": "MAGE",
            "next_step": "D49 may create a concrete patch proposal from this request"
        },
        "raw_executor_action": executor_action
    }

    out_path = Path("reports/d47_phase_resync_patch_request.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(patch_request, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "route": "FIELD_INTENT_PHASE_RESYNC_PATCH_REQUEST",
        "ok": True,
        "reason": "phase_resync_patch_request_created",
        "patch_request_path": str(out_path),
        "source_action": str(action_path),
        "problem": problem,
        "intent": intent,
        "bridge": bridge,
        "field_case": field_case,
        "target_agent": "MAGE",
        "executor_problem": "field_intent_phase_resync_patch",
        "resonance_vector": resonance_vector,
        "execution": {
            "ok": True,
            "changed_files": [str(out_path)],
            "actions": ["write_phase_resync_patch_request"],
            "note": "D48 patch request created. No code mutation executed yet."
        },
        "validation": {
            "ok": True,
            "errors": [],
            "note": "Phase resync patch request created from D47 executor action."
        },
        "auto_commit": {
            "ok": False,
            "reason": "patch_request_only_manual_commit"
        }
    }


def _run_field_intent_phase_resync_patch_proposal(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    request_path = Path(str(payload.get("request_path") or "reports/d47_phase_resync_patch_request.json"))
    if not request_path.exists():
        return {
            "route": "FIELD_INTENT_PHASE_RESYNC_PATCH_PROPOSAL",
            "ok": False,
            "reason": "patch_request_missing",
            "request_path": str(request_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": ["patch request file not found"]},
        }

    try:
        patch_request = json.loads(request_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "route": "FIELD_INTENT_PHASE_RESYNC_PATCH_PROPOSAL",
            "ok": False,
            "reason": "patch_request_read_error",
            "error": str(exc),
            "request_path": str(request_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": [str(exc)]},
        }

    resonance_vector = patch_request.get("resonance_vector", {})
    if not isinstance(resonance_vector, dict):
        resonance_vector = {}

    diagnosis = patch_request.get("diagnosis", {})
    if not isinstance(diagnosis, dict):
        diagnosis = {}

    memory_key = str(resonance_vector.get("memory_key") or diagnosis.get("memory_key") or "UNKNOWN_MEMORY_KEY")
    orbital_mode = str(resonance_vector.get("orbital_mode") or diagnosis.get("orbital_mode") or "UNKNOWN_ORBITAL")
    intent = str(patch_request.get("intent") or "NEEDS_PHASE_REPAIR")
    field_case = str(patch_request.get("field_case") or "PHASE_DRIFT_HEX")

    phase_error = float(resonance_vector.get("phase_error", diagnosis.get("phase_error", 0.0)) or 0.0)
    jitter = float(resonance_vector.get("jitter", diagnosis.get("jitter", 0.0)) or 0.0)

    phase_error_after = min(phase_error, phase_error * 0.35)
    jitter_after = min(jitter, jitter * 0.70)

    proposal = {
        "state": "D49_FIELD_INTENT_PHASE_RESYNC_PATCH_PROPOSAL",
        "result": "PHASE_RESYNC_PATCH_PROPOSAL_CREATED",
        "source_request": str(request_path),
        "problem": "field_intent_phase_resync_patch_proposal",
        "bridge": "D49_FIELD_INTENT_PHASE_RESYNC_PATCH_PROPOSAL",
        "intent": intent,
        "field_case": field_case,
        "target_agent": "MAGE",
        "mode": "PATCH_PROPOSAL_ONLY",
        "do_not_apply_patch_yet": True,
        "resonance_vector": resonance_vector,
        "proposal_summary": {
            "goal": "Reduce phase drift before memory write while preserving D46 resonance payload.",
            "memory_key": memory_key,
            "orbital_mode": orbital_mode,
            "cause": diagnosis.get("cause", "phase_error_exceeds_threshold"),
        },
        "proposed_algorithm": {
            "name": "phase_resync_before_memory_write",
            "steps": [
                "read incoming resonance_vector",
                "detect phase_error before memory write",
                "if phase_error exceeds threshold, compute corrected phase_error",
                "preserve memory_key, orbital_mode, intent and original payload",
                "write resync diagnostics into report before any runtime mutation"
            ],
            "formula": {
                "phase_error_before": phase_error,
                "phase_error_after": phase_error_after,
                "jitter_before": jitter,
                "jitter_after": jitter_after,
                "phase_lock_ok": phase_error_after <= 0.12 and jitter_after <= 0.08
            }
        },
        "candidate_patch": {
            "safe_target": True,
            "code_mutation_required_now": False,
            "proposal_file": "reports/d49_phase_resync_patch_proposal.json",
            "next_real_code_target_candidates": [
                "app/orchestration/task_dispatcher.py",
                "runtime_experimental/v_kernel_daemon.py"
            ]
        },
        "validation_rule": {
            "must_preserve_payload": True,
            "must_preserve_resonance_vector": True,
            "must_preserve_memory_key": memory_key,
            "must_preserve_orbital_mode": orbital_mode,
            "phase_error_after_max": 0.12,
            "jitter_after_max": 0.08,
            "no_runtime_code_mutation_yet": True
        },
        "success_condition": {
            "route": "FIELD_INTENT_PHASE_RESYNC_PATCH_PROPOSAL",
            "patch_proposal_created": True,
            "target_agent": "MAGE",
            "next_step": "D50 may convert this proposal into a guarded apply route"
        },
        "raw_patch_request": patch_request
    }

    out_path = Path("reports/d49_phase_resync_patch_proposal.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "route": "FIELD_INTENT_PHASE_RESYNC_PATCH_PROPOSAL",
        "ok": True,
        "reason": "phase_resync_patch_proposal_created",
        "patch_proposal_path": str(out_path),
        "source_request": str(request_path),
        "problem": "field_intent_phase_resync_patch_proposal",
        "intent": intent,
        "field_case": field_case,
        "target_agent": "MAGE",
        "resonance_vector": resonance_vector,
        "execution": {
            "ok": True,
            "changed_files": [str(out_path)],
            "actions": ["write_phase_resync_patch_proposal"],
            "note": "D49 patch proposal created. No runtime code mutation executed yet."
        },
        "validation": {
            "ok": True,
            "errors": [],
            "note": "Patch proposal created from D48 request."
        },
        "auto_commit": {
            "ok": False,
            "reason": "patch_proposal_only_manual_commit"
        }
    }


def _run_field_intent_phase_resync_guarded_apply(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    proposal_path = Path(str(payload.get("proposal_path") or "reports/d49_phase_resync_patch_proposal.json"))
    if not proposal_path.exists():
        return {
            "route": "FIELD_INTENT_PHASE_RESYNC_GUARDED_APPLY",
            "ok": False,
            "reason": "patch_proposal_missing",
            "proposal_path": str(proposal_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": ["patch proposal file not found"]},
        }

    try:
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "route": "FIELD_INTENT_PHASE_RESYNC_GUARDED_APPLY",
            "ok": False,
            "reason": "patch_proposal_read_error",
            "error": str(exc),
            "proposal_path": str(proposal_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": [str(exc)]},
        }

    resonance_vector = proposal.get("resonance_vector", {})
    if not isinstance(resonance_vector, dict):
        resonance_vector = {}

    algorithm = proposal.get("proposed_algorithm", {})
    if not isinstance(algorithm, dict):
        algorithm = {}

    formula = algorithm.get("formula", {})
    if not isinstance(formula, dict):
        formula = {}

    validation_rule = proposal.get("validation_rule", {})
    if not isinstance(validation_rule, dict):
        validation_rule = {}

    phase_error_after = float(formula.get("phase_error_after", 999.0) or 999.0)
    jitter_after = float(formula.get("jitter_after", 999.0) or 999.0)
    phase_error_max = float(validation_rule.get("phase_error_after_max", 0.12) or 0.12)
    jitter_max = float(validation_rule.get("jitter_after_max", 0.08) or 0.08)

    memory_key = str(validation_rule.get("must_preserve_memory_key") or resonance_vector.get("memory_key") or "UNKNOWN_MEMORY_KEY")
    orbital_mode = str(validation_rule.get("must_preserve_orbital_mode") or resonance_vector.get("orbital_mode") or "UNKNOWN_ORBITAL")
    intent = str(proposal.get("intent") or "NEEDS_PHASE_REPAIR")
    field_case = str(proposal.get("field_case") or "PHASE_DRIFT_HEX")

    errors = []

    if proposal.get("mode") != "PATCH_PROPOSAL_ONLY":
        errors.append("proposal mode must be PATCH_PROPOSAL_ONLY before guarded apply")

    if proposal.get("do_not_apply_patch_yet") is not True:
        errors.append("proposal must explicitly say do_not_apply_patch_yet=true")

    if not isinstance(resonance_vector, dict) or not resonance_vector:
        errors.append("resonance_vector missing")

    if phase_error_after > phase_error_max:
        errors.append(f"phase_error_after too high: {phase_error_after} > {phase_error_max}")

    if jitter_after > jitter_max:
        errors.append(f"jitter_after too high: {jitter_after} > {jitter_max}")

    if str(resonance_vector.get("memory_key", "")) != memory_key:
        errors.append("memory_key was not preserved")

    if str(resonance_vector.get("orbital_mode", "")) != orbital_mode:
        errors.append("orbital_mode was not preserved")

    if errors:
        return {
            "route": "FIELD_INTENT_PHASE_RESYNC_GUARDED_APPLY",
            "ok": False,
            "reason": "guard_validation_failed",
            "proposal_path": str(proposal_path),
            "errors": errors,
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": errors},
        }

    policy = {
        "state": "D50_FIELD_INTENT_PHASE_RESYNC_POLICY_LOCK",
        "result": "PHASE_RESYNC_POLICY_LOCKED",
        "source_proposal": str(proposal_path),
        "bridge": "D50_FIELD_INTENT_PHASE_RESYNC_GUARDED_APPLY",
        "intent": intent,
        "field_case": field_case,
        "memory_key": memory_key,
        "orbital_mode": orbital_mode,
        "resonance_vector": resonance_vector,
        "locked_thresholds": {
            "phase_error_after_max": phase_error_max,
            "jitter_after_max": jitter_max,
            "phase_error_after": phase_error_after,
            "jitter_after": jitter_after,
            "phase_lock_ok": True
        },
        "apply_mode": "POLICY_ONLY",
        "runtime_code_mutated": False,
        "safe_to_generate_guarded_patch_next": True,
        "next_step": "D51 may use this locked policy to generate a guarded runtime patch"
    }

    result = {
        "state": "D50_FIELD_INTENT_PHASE_RESYNC_GUARDED_APPLY",
        "result": "GUARDED_APPLY_ACCEPTED",
        "route": "FIELD_INTENT_PHASE_RESYNC_GUARDED_APPLY",
        "source_proposal": str(proposal_path),
        "policy_path": "reports/d50_phase_resync_policy_lock.json",
        "problem": "field_intent_phase_resync_guarded_apply",
        "intent": intent,
        "field_case": field_case,
        "target_agent": "MAGE",
        "resonance_vector": resonance_vector,
        "validated": True,
        "applied": {
            "mode": "POLICY_ONLY",
            "runtime_code_mutated": False,
            "phase_error_after": phase_error_after,
            "jitter_after": jitter_after,
            "phase_lock_ok": True
        },
        "validation_rule": {
            "payload_preserved": True,
            "resonance_vector_preserved": True,
            "memory_key_preserved": True,
            "orbital_mode_preserved": True,
            "phase_error_after_max": phase_error_max,
            "jitter_after_max": jitter_max
        },
        "success_condition": {
            "route": "FIELD_INTENT_PHASE_RESYNC_GUARDED_APPLY",
            "policy_locked": True,
            "next_step": "D51 may create a guarded runtime patch from this locked policy"
        },
        "raw_patch_proposal": proposal
    }

    policy_path = Path("reports/d50_phase_resync_policy_lock.json")
    result_path = Path("reports/d50_phase_resync_guarded_apply_result.json")

    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "route": "FIELD_INTENT_PHASE_RESYNC_GUARDED_APPLY",
        "ok": True,
        "reason": "phase_resync_guarded_apply_accepted",
        "proposal_path": str(proposal_path),
        "policy_path": str(policy_path),
        "result_path": str(result_path),
        "problem": "field_intent_phase_resync_guarded_apply",
        "intent": intent,
        "field_case": field_case,
        "target_agent": "MAGE",
        "resonance_vector": resonance_vector,
        "execution": {
            "ok": True,
            "changed_files": [str(policy_path), str(result_path)],
            "actions": ["write_phase_resync_policy_lock", "write_guarded_apply_result"],
            "note": "D50 guarded apply accepted as policy only. No runtime code mutation executed yet."
        },
        "validation": {
            "ok": True,
            "errors": [],
            "note": "D50 validated D49 proposal and locked safe phase-resync policy."
        },
        "auto_commit": {
            "ok": False,
            "reason": "guarded_apply_policy_only_manual_commit"
        }
    }


def _run_field_intent_guarded_runtime_patch_generator(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    policy_path = Path(str(payload.get("policy_path") or "reports/d50_phase_resync_policy_lock.json"))
    result_path = Path(str(payload.get("result_path") or "reports/d50_phase_resync_guarded_apply_result.json"))

    if not policy_path.exists():
        return {
            "route": "FIELD_INTENT_GUARDED_RUNTIME_PATCH_GENERATOR",
            "ok": False,
            "reason": "policy_lock_missing",
            "policy_path": str(policy_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": ["D50 policy lock file not found"]},
        }

    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "route": "FIELD_INTENT_GUARDED_RUNTIME_PATCH_GENERATOR",
            "ok": False,
            "reason": "policy_lock_read_error",
            "error": str(exc),
            "policy_path": str(policy_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": [str(exc)]},
        }

    guarded_result = {}
    if result_path.exists():
        try:
            guarded_result = json.loads(result_path.read_text(encoding="utf-8"))
        except Exception:
            guarded_result = {}

    resonance_vector = policy.get("resonance_vector", {})
    if not isinstance(resonance_vector, dict):
        resonance_vector = {}

    locked_thresholds = policy.get("locked_thresholds", {})
    if not isinstance(locked_thresholds, dict):
        locked_thresholds = {}

    memory_key = str(policy.get("memory_key") or resonance_vector.get("memory_key") or "UNKNOWN_MEMORY_KEY")
    orbital_mode = str(policy.get("orbital_mode") or resonance_vector.get("orbital_mode") or "UNKNOWN_ORBITAL")
    intent = str(policy.get("intent") or "NEEDS_PHASE_REPAIR")
    field_case = str(policy.get("field_case") or "PHASE_DRIFT_HEX")

    errors = []

    if policy.get("result") != "PHASE_RESYNC_POLICY_LOCKED":
        errors.append("D50 policy result must be PHASE_RESYNC_POLICY_LOCKED")

    if policy.get("apply_mode") != "POLICY_ONLY":
        errors.append("D50 policy apply_mode must be POLICY_ONLY")

    if policy.get("runtime_code_mutated") is not False:
        errors.append("D50 policy must not have mutated runtime code")

    if policy.get("safe_to_generate_guarded_patch_next") is not True:
        errors.append("D50 policy does not allow guarded patch generation")

    if locked_thresholds.get("phase_lock_ok") is not True:
        errors.append("phase lock is not ok")

    if str(resonance_vector.get("memory_key", "")) != memory_key:
        errors.append("memory_key not preserved")

    if str(resonance_vector.get("orbital_mode", "")) != orbital_mode:
        errors.append("orbital_mode not preserved")

    if errors:
        return {
            "route": "FIELD_INTENT_GUARDED_RUNTIME_PATCH_GENERATOR",
            "ok": False,
            "reason": "d51_guard_validation_failed",
            "errors": errors,
            "policy_path": str(policy_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": errors},
        }

    module_lines = [
        "# -*- coding: utf-8 -*-",
        '"""',
        "runtime_experimental/phase_resync_policy.py",
        "",
        "Guarded phase-resync helper generated from D51.",
        "",
        "Purpose:",
        "- reduce phase drift before memory/write/report stages",
        "- preserve full D46 resonance payload",
        "- never overwrite memory_key, orbital_mode, intent, or resonance_vector",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, Dict",
        "",
        "",
        "def _num(value: Any, default: float = 0.0) -> float:",
        "    try:",
        "        return float(value) if value is not None else default",
        "    except Exception:",
        "        return default",
        "",
        "",
        "def compute_phase_resync(",
        "    resonance_vector: Dict[str, Any],",
        "    *,",
        "    phase_error_after_max: float = 0.12,",
        "    jitter_after_max: float = 0.08,",
        ") -> Dict[str, Any]:",
        "    original = dict(resonance_vector or {})",
        "",
        '    phase_error_before = _num(original.get("phase_error"), 0.0)',
        '    jitter_before = _num(original.get("jitter"), 0.0)',
        "",
        "    phase_error_after = min(phase_error_before, phase_error_before * 0.35)",
        "    jitter_after = min(jitter_before, jitter_before * 0.70)",
        "",
        "    return {",
        '        "ok": phase_error_after <= phase_error_after_max and jitter_after <= jitter_after_max,',
        '        "memory_key": original.get("memory_key"),',
        '        "orbital_mode": original.get("orbital_mode"),',
        '        "phase_error_before": phase_error_before,',
        '        "phase_error_after": phase_error_after,',
        '        "jitter_before": jitter_before,',
        '        "jitter_after": jitter_after,',
        '        "phase_error_after_max": phase_error_after_max,',
        '        "jitter_after_max": jitter_after_max,',
        '        "preserved_resonance_vector": original,',
        "    }",
        "",
    ]

    module_content = "\n".join(module_lines)

    patch_bundle = {
        "state": "D51_FIELD_INTENT_GUARDED_RUNTIME_PATCH_GENERATOR",
        "result": "GUARDED_RUNTIME_PATCH_BUNDLE_CREATED",
        "source_policy": str(policy_path),
        "source_guarded_apply_result": str(result_path),
        "bridge": "D51_FIELD_INTENT_GUARDED_RUNTIME_PATCH_GENERATOR",
        "intent": intent,
        "field_case": field_case,
        "target_agent": "MAGE",
        "mode": "PATCH_BUNDLE_ONLY",
        "do_not_apply_patch_yet": True,
        "runtime_code_mutated": False,
        "memory_key": memory_key,
        "orbital_mode": orbital_mode,
        "resonance_vector": resonance_vector,
        "locked_thresholds": locked_thresholds,
        "patch_bundle": {
            "goal": "Create a guarded runtime helper for phase resync without applying it yet.",
            "new_file_candidate": "runtime_experimental/phase_resync_policy.py",
            "integration_candidates": [
                "app/orchestration/task_dispatcher.py",
                "runtime_experimental/v_kernel_daemon.py"
            ],
            "module_content": module_content,
            "rollback_plan": [
                "remove runtime_experimental/phase_resync_policy.py if validation fails",
                "do not modify task_dispatcher.py until D52 guarded apply",
                "do not modify v_kernel_daemon.py until D52 guarded apply"
            ],
            "validation_commands": [
                "python -m py_compile runtime_experimental/phase_resync_policy.py",
                "python -m py_compile app/orchestration/task_dispatcher.py",
                "PYTHONPATH=. python runtime_experimental/v_kernel_daemon.py"
            ]
        },
        "validation_rule": {
            "must_preserve_payload": True,
            "must_preserve_resonance_vector": True,
            "must_preserve_memory_key": memory_key,
            "must_preserve_orbital_mode": orbital_mode,
            "runtime_code_mutated_now": False,
            "next_apply_requires_backup": True,
            "next_apply_requires_py_compile": True,
            "next_apply_requires_daemon_test": True
        },
        "success_condition": {
            "route": "FIELD_INTENT_GUARDED_RUNTIME_PATCH_GENERATOR",
            "patch_bundle_created": True,
            "next_step": "D52 may write the helper file with backup and validation"
        },
        "raw_policy": policy,
        "raw_guarded_apply_result": guarded_result
    }

    out_path = Path("reports/d51_guarded_runtime_patch_bundle.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(patch_bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "route": "FIELD_INTENT_GUARDED_RUNTIME_PATCH_GENERATOR",
        "ok": True,
        "reason": "guarded_runtime_patch_bundle_created",
        "patch_bundle_path": str(out_path),
        "policy_path": str(policy_path),
        "problem": "field_intent_guarded_runtime_patch_generator",
        "intent": intent,
        "field_case": field_case,
        "target_agent": "MAGE",
        "resonance_vector": resonance_vector,
        "execution": {
            "ok": True,
            "changed_files": [str(out_path)],
            "actions": ["write_guarded_runtime_patch_bundle"],
            "note": "D51 patch bundle created. No runtime code mutation executed yet."
        },
        "validation": {
            "ok": True,
            "errors": [],
            "note": "D51 generated guarded runtime patch bundle from D50 locked policy."
        },
        "auto_commit": {
            "ok": False,
            "reason": "patch_bundle_only_manual_commit"
        }
    }


def _run_field_intent_guarded_runtime_patch_apply(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    bundle_path = Path(str(payload.get("bundle_path") or "reports/d51_guarded_runtime_patch_bundle.json"))
    if not bundle_path.exists():
        return {
            "route": "FIELD_INTENT_GUARDED_RUNTIME_PATCH_APPLY",
            "ok": False,
            "reason": "patch_bundle_missing",
            "bundle_path": str(bundle_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": ["D51 patch bundle file not found"]},
        }

    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "route": "FIELD_INTENT_GUARDED_RUNTIME_PATCH_APPLY",
            "ok": False,
            "reason": "patch_bundle_read_error",
            "error": str(exc),
            "bundle_path": str(bundle_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": [str(exc)]},
        }

    patch_bundle = bundle.get("patch_bundle", {})
    if not isinstance(patch_bundle, dict):
        patch_bundle = {}

    module_content = str(patch_bundle.get("module_content") or "")
    target_path = Path(str(patch_bundle.get("new_file_candidate") or "runtime_experimental/phase_resync_policy.py"))

    resonance_vector = bundle.get("resonance_vector", {})
    if not isinstance(resonance_vector, dict):
        resonance_vector = {}

    memory_key = str(bundle.get("memory_key") or resonance_vector.get("memory_key") or "UNKNOWN_MEMORY_KEY")
    orbital_mode = str(bundle.get("orbital_mode") or resonance_vector.get("orbital_mode") or "UNKNOWN_ORBITAL")
    intent = str(bundle.get("intent") or "NEEDS_PHASE_REPAIR")
    field_case = str(bundle.get("field_case") or "PHASE_DRIFT_HEX")

    errors = []

    if bundle.get("result") != "GUARDED_RUNTIME_PATCH_BUNDLE_CREATED":
        errors.append("D51 bundle result must be GUARDED_RUNTIME_PATCH_BUNDLE_CREATED")

    if bundle.get("mode") != "PATCH_BUNDLE_ONLY":
        errors.append("D51 bundle mode must be PATCH_BUNDLE_ONLY")

    if bundle.get("do_not_apply_patch_yet") is not True:
        errors.append("D51 bundle must explicitly say do_not_apply_patch_yet=true")

    if bundle.get("runtime_code_mutated") is not False:
        errors.append("D51 bundle must not have mutated runtime code")

    if target_path.as_posix() != "runtime_experimental/phase_resync_policy.py":
        errors.append(f"unexpected target path: {target_path}")

    if "def compute_phase_resync" not in module_content:
        errors.append("module_content missing compute_phase_resync")

    if str(resonance_vector.get("memory_key", "")) != memory_key:
        errors.append("memory_key not preserved")

    if str(resonance_vector.get("orbital_mode", "")) != orbital_mode:
        errors.append("orbital_mode not preserved")

    if errors:
        return {
            "route": "FIELD_INTENT_GUARDED_RUNTIME_PATCH_APPLY",
            "ok": False,
            "reason": "d52_guard_validation_failed_before_write",
            "errors": errors,
            "bundle_path": str(bundle_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": errors},
        }

    backup_dir = Path("reports/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / "phase_resync_policy.py.d52.bak"

    target_existed = target_path.exists()
    original_text = target_path.read_text(encoding="utf-8") if target_existed else ""

    if target_existed:
        backup_path.write_text(original_text, encoding="utf-8")

    def rollback(reason: str, validation_errors: list[str]) -> Dict[str, Any]:
        try:
            if target_existed:
                target_path.write_text(original_text, encoding="utf-8")
            else:
                if target_path.exists():
                    target_path.unlink()
        except Exception as rollback_exc:
            validation_errors.append(f"rollback_error: {rollback_exc}")

        return {
            "route": "FIELD_INTENT_GUARDED_RUNTIME_PATCH_APPLY",
            "ok": False,
            "reason": reason,
            "bundle_path": str(bundle_path),
            "target_path": str(target_path),
            "backup_path": str(backup_path) if target_existed else None,
            "rolled_back": True,
            "execution": {
                "ok": False,
                "changed_files": [],
                "actions": ["write_runtime_helper", "validation_failed", "rollback"],
            },
            "validation": {
                "ok": False,
                "errors": validation_errors,
            },
        }

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(module_content, encoding="utf-8")

    def run_cmd(cmd: list[str]) -> Dict[str, Any]:
        proc = subprocess.run(cmd, text=True, capture_output=True)
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "ok": proc.returncode == 0,
        }

    compile_helper = run_cmd([sys.executable, "-m", "py_compile", str(target_path)])
    if not compile_helper["ok"]:
        return rollback("helper_py_compile_failed", [compile_helper["stderr"] or compile_helper["stdout"]])

    compile_dispatcher = run_cmd([sys.executable, "-m", "py_compile", "app/orchestration/task_dispatcher.py"])
    if not compile_dispatcher["ok"]:
        return rollback("dispatcher_py_compile_failed", [compile_dispatcher["stderr"] or compile_dispatcher["stdout"]])

    test_vector = dict(resonance_vector)
    test_code = (
        "from runtime_experimental.phase_resync_policy import compute_phase_resync\n"
        f"v = {json.dumps(test_vector, ensure_ascii=False)}\n"
        "r = compute_phase_resync(v)\n"
        "assert r['ok'] is True\n"
        "assert r['memory_key'] == v.get('memory_key')\n"
        "assert r['orbital_mode'] == v.get('orbital_mode')\n"
        "assert r['phase_error_after'] <= r['phase_error_after_max']\n"
        "assert r['jitter_after'] <= r['jitter_after_max']\n"
        "print('phase_resync_policy_ok')\n"
    )

    functional_test = run_cmd([sys.executable, "-c", test_code])
    if not functional_test["ok"]:
        return rollback("functional_validation_failed", [functional_test["stderr"] or functional_test["stdout"]])

    result = {
        "state": "D52_FIELD_INTENT_GUARDED_RUNTIME_PATCH_APPLY",
        "result": "GUARDED_RUNTIME_HELPER_WRITTEN",
        "route": "FIELD_INTENT_GUARDED_RUNTIME_PATCH_APPLY",
        "source_bundle": str(bundle_path),
        "target_path": str(target_path),
        "backup_path": str(backup_path) if target_existed else None,
        "bridge": "D52_FIELD_INTENT_GUARDED_RUNTIME_PATCH_APPLY",
        "intent": intent,
        "field_case": field_case,
        "target_agent": "MAGE",
        "memory_key": memory_key,
        "orbital_mode": orbital_mode,
        "resonance_vector": resonance_vector,
        "applied": {
            "mode": "GUARDED_FILE_WRITE",
            "runtime_code_mutated": True,
            "new_file_written": True,
            "rollback_available": target_existed,
            "target_existed_before": target_existed,
        },
        "validation": {
            "helper_py_compile": compile_helper,
            "dispatcher_py_compile": compile_dispatcher,
            "functional_test": functional_test,
            "ok": True,
        },
        "success_condition": {
            "route": "FIELD_INTENT_GUARDED_RUNTIME_PATCH_APPLY",
            "helper_written": True,
            "validation_passed": True,
            "next_step": "D53 may integrate compute_phase_resync into the runtime path"
        },
        "raw_bundle": bundle,
    }

    result_path = Path("reports/d52_guarded_runtime_patch_apply_result.json")
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    changed_files = [str(target_path), str(result_path)]
    if target_existed:
        changed_files.append(str(backup_path))

    return {
        "route": "FIELD_INTENT_GUARDED_RUNTIME_PATCH_APPLY",
        "ok": True,
        "reason": "guarded_runtime_helper_written",
        "bundle_path": str(bundle_path),
        "target_path": str(target_path),
        "result_path": str(result_path),
        "backup_path": str(backup_path) if target_existed else None,
        "problem": "field_intent_guarded_runtime_patch_apply",
        "intent": intent,
        "field_case": field_case,
        "target_agent": "MAGE",
        "resonance_vector": resonance_vector,
        "execution": {
            "ok": True,
            "changed_files": changed_files,
            "actions": ["write_phase_resync_policy_helper", "py_compile", "functional_validation"],
            "note": "D52 wrote runtime helper with guarded validation."
        },
        "validation": {
            "ok": True,
            "errors": [],
            "note": "D52 helper file compiled and functional validation passed."
        },
        "auto_commit": {
            "ok": False,
            "reason": "guarded_runtime_patch_manual_commit"
        }
    }


def _run_field_intent_phase_resync_runtime_check(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    resonance_vector = payload.get("resonance_vector", {})
    if not isinstance(resonance_vector, dict):
        resonance_vector = {}

    # Fallback: if event payload is thin, recover vector from D52 result.
    if not resonance_vector:
        fallback_path = Path(str(payload.get("source_result") or "reports/d52_guarded_runtime_patch_apply_result.json"))
        if fallback_path.exists():
            try:
                fallback = json.loads(fallback_path.read_text(encoding="utf-8"))
                rv = fallback.get("resonance_vector", {})
                if isinstance(rv, dict):
                    resonance_vector = rv
            except Exception:
                resonance_vector = {}

    if not resonance_vector:
        return {
            "route": "FIELD_INTENT_PHASE_RESYNC_RUNTIME_CHECK",
            "ok": False,
            "reason": "missing_resonance_vector",
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": ["No resonance_vector found in payload or fallback result"]},
        }

    try:
        from runtime_experimental.phase_resync_policy import compute_phase_resync
    except Exception as exc:
        return {
            "route": "FIELD_INTENT_PHASE_RESYNC_RUNTIME_CHECK",
            "ok": False,
            "reason": "phase_resync_helper_import_failed",
            "error": str(exc),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": [str(exc)]},
        }

    phase_error_after_max = float(payload.get("phase_error_after_max", 0.12))
    jitter_after_max = float(payload.get("jitter_after_max", 0.08))

    check = compute_phase_resync(
        resonance_vector,
        phase_error_after_max=phase_error_after_max,
        jitter_after_max=jitter_after_max,
    )

    memory_key_before = resonance_vector.get("memory_key")
    orbital_mode_before = resonance_vector.get("orbital_mode")

    errors = []

    if check.get("memory_key") != memory_key_before:
        errors.append("memory_key changed during runtime check")

    if check.get("orbital_mode") != orbital_mode_before:
        errors.append("orbital_mode changed during runtime check")

    if check.get("phase_error_after", 999) > phase_error_after_max:
        errors.append("phase_error_after exceeds threshold")

    if check.get("jitter_after", 999) > jitter_after_max:
        errors.append("jitter_after exceeds threshold")

    ok = bool(check.get("ok")) and not errors

    report = {
        "state": "D53_FIELD_INTENT_PHASE_RESYNC_RUNTIME_CHECK",
        "result": "PHASE_RESYNC_RUNTIME_CHECK_PASSED" if ok else "PHASE_RESYNC_RUNTIME_CHECK_FAILED",
        "route": "FIELD_INTENT_PHASE_RESYNC_RUNTIME_CHECK",
        "bridge": "D53_FIELD_INTENT_PHASE_RESYNC_RUNTIME_CHECK",
        "intent": str(payload.get("intent") or "RUNTIME_PHASE_RESYNC_CHECK"),
        "field_case": str(payload.get("field_case") or "PHASE_DRIFT_HEX"),
        "target_agent": str(payload.get("target_agent") or payload.get("executor_hint") or "MAGE"),
        "source_payload_problem": str(payload.get("problem") or "field_intent_phase_resync_runtime_check"),
        "resonance_vector_before": resonance_vector,
        "runtime_check": check,
        "thresholds": {
            "phase_error_after_max": phase_error_after_max,
            "jitter_after_max": jitter_after_max,
        },
        "preservation": {
            "memory_key_preserved": check.get("memory_key") == memory_key_before,
            "orbital_mode_preserved": check.get("orbital_mode") == orbital_mode_before,
            "resonance_vector_not_overwritten": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
        },
        "success_condition": {
            "route": "FIELD_INTENT_PHASE_RESYNC_RUNTIME_CHECK",
            "runtime_helper_imported": True,
            "phase_resync_computed": True,
            "payload_preserved": True,
            "next_step": "D54 may inject runtime_check result into a guarded downstream decision"
        },
    }

    out_path = Path("reports/d53_phase_resync_runtime_check.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "route": "FIELD_INTENT_PHASE_RESYNC_RUNTIME_CHECK",
        "ok": ok,
        "reason": "phase_resync_runtime_check_passed" if ok else "phase_resync_runtime_check_failed",
        "report_path": str(out_path),
        "problem": "field_intent_phase_resync_runtime_check",
        "intent": report["intent"],
        "field_case": report["field_case"],
        "target_agent": report["target_agent"],
        "resonance_vector": resonance_vector,
        "runtime_check": check,
        "execution": {
            "ok": ok,
            "changed_files": [str(out_path)],
            "actions": ["import_phase_resync_policy", "compute_phase_resync", "write_runtime_check_report"],
            "note": "D53 used the D52 helper in runtime check mode. No payload mutation yet."
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "note": "Runtime phase resync check completed."
        },
        "auto_commit": {
            "ok": False,
            "reason": "runtime_check_report_manual_commit"
        }
    }


def _run_field_intent_phase_resync_downstream_decision(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    check_path = Path(str(payload.get("check_path") or "reports/d53_phase_resync_runtime_check.json"))

    if not check_path.exists():
        return {
            "route": "FIELD_INTENT_PHASE_RESYNC_DOWNSTREAM_DECISION",
            "ok": False,
            "reason": "d53_runtime_check_missing",
            "check_path": str(check_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": ["D53 runtime check report not found"]},
        }

    try:
        check_report = json.loads(check_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "route": "FIELD_INTENT_PHASE_RESYNC_DOWNSTREAM_DECISION",
            "ok": False,
            "reason": "d53_runtime_check_read_error",
            "error": str(exc),
            "check_path": str(check_path),
            "execution": {"ok": False, "changed_files": [], "actions": []},
            "validation": {"ok": False, "errors": [str(exc)]},
        }

    runtime_check = check_report.get("runtime_check", {})
    if not isinstance(runtime_check, dict):
        runtime_check = {}

    validation = check_report.get("validation", {})
    if not isinstance(validation, dict):
        validation = {}

    preservation = check_report.get("preservation", {})
    if not isinstance(preservation, dict):
        preservation = {}

    resonance_vector = check_report.get("resonance_vector_before", {})
    if not isinstance(resonance_vector, dict):
        resonance_vector = {}

    thresholds = check_report.get("thresholds", {})
    if not isinstance(thresholds, dict):
        thresholds = {}

    phase_error_after_max = float(thresholds.get("phase_error_after_max", payload.get("phase_error_after_max", 0.12)))
    jitter_after_max = float(thresholds.get("jitter_after_max", payload.get("jitter_after_max", 0.08)))

    phase_error_after = float(runtime_check.get("phase_error_after", 999.0))
    jitter_after = float(runtime_check.get("jitter_after", 999.0))

    errors = []

    if check_report.get("result") != "PHASE_RESYNC_RUNTIME_CHECK_PASSED":
        errors.append("D53 result is not PHASE_RESYNC_RUNTIME_CHECK_PASSED")

    if runtime_check.get("ok") is not True:
        errors.append("runtime_check.ok is not true")

    if validation.get("ok") is not True:
        errors.append("D53 validation.ok is not true")

    if preservation.get("memory_key_preserved") is not True:
        errors.append("memory_key was not preserved")

    if preservation.get("orbital_mode_preserved") is not True:
        errors.append("orbital_mode was not preserved")

    if preservation.get("resonance_vector_not_overwritten") is not True:
        errors.append("resonance_vector was overwritten")

    if phase_error_after > phase_error_after_max:
        errors.append("phase_error_after still exceeds allowed threshold")

    if jitter_after > jitter_after_max:
        errors.append("jitter_after still exceeds allowed threshold")

    allow_write = not errors

    decision = "ALLOW_GUARDED_MEMORY_WRITE" if allow_write else "HOLD_FOR_REVIEW"

    report = {
        "state": "D54_FIELD_INTENT_PHASE_RESYNC_DOWNSTREAM_DECISION",
        "result": "DOWNSTREAM_DECISION_CREATED",
        "route": "FIELD_INTENT_PHASE_RESYNC_DOWNSTREAM_DECISION",
        "bridge": "D54_FIELD_INTENT_PHASE_RESYNC_DOWNSTREAM_DECISION",
        "source_check": str(check_path),
        "decision": decision,
        "allow_guarded_memory_write": allow_write,
        "must_not_mutate_code": True,
        "runtime_code_mutated": False,
        "memory_write_executed": False,
        "intent": str(check_report.get("intent") or payload.get("intent") or "RUNTIME_PHASE_RESYNC_CHECK"),
        "field_case": str(check_report.get("field_case") or payload.get("field_case") or "PHASE_DRIFT_HEX"),
        "target_agent": str(check_report.get("target_agent") or payload.get("target_agent") or payload.get("executor_hint") or "MAGE"),
        "resonance_vector": resonance_vector,
        "runtime_check": runtime_check,
        "thresholds": {
            "phase_error_after_max": phase_error_after_max,
            "jitter_after_max": jitter_after_max,
            "phase_error_after": phase_error_after,
            "jitter_after": jitter_after,
        },
        "decision_rules": {
            "require_d53_passed": True,
            "require_runtime_check_ok": True,
            "require_memory_key_preserved": True,
            "require_orbital_mode_preserved": True,
            "require_resonance_vector_not_overwritten": True,
            "require_phase_error_after_lte_max": True,
            "require_jitter_after_lte_max": True,
        },
        "validation": {
            "ok": allow_write,
            "errors": errors,
        },
        "success_condition": {
            "route": "FIELD_INTENT_PHASE_RESYNC_DOWNSTREAM_DECISION",
            "decision_created": True,
            "allow_guarded_memory_write": allow_write,
            "next_step": "D55 may create a guarded memory-write request if decision is ALLOW_GUARDED_MEMORY_WRITE",
        },
        "raw_d53_runtime_check": check_report,
    }

    out_path = Path("reports/d54_phase_resync_downstream_decision.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "route": "FIELD_INTENT_PHASE_RESYNC_DOWNSTREAM_DECISION",
        "ok": allow_write,
        "reason": "guarded_memory_write_allowed" if allow_write else "hold_for_review",
        "decision": decision,
        "allow_guarded_memory_write": allow_write,
        "report_path": str(out_path),
        "problem": "field_intent_phase_resync_downstream_decision",
        "intent": report["intent"],
        "field_case": report["field_case"],
        "target_agent": report["target_agent"],
        "resonance_vector": resonance_vector,
        "execution": {
            "ok": allow_write,
            "changed_files": [str(out_path)],
            "actions": ["read_d53_runtime_check", "evaluate_downstream_decision", "write_d54_decision_report"],
            "note": "D54 created downstream decision. No memory write executed yet."
        },
        "validation": {
            "ok": allow_write,
            "errors": errors,
            "note": "Downstream decision completed."
        },
        "auto_commit": {
            "ok": False,
            "reason": "downstream_decision_manual_commit"
        }
    }

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



    if problem == "field_intent_phase_resync_downstream_decision":
        return _run_field_intent_phase_resync_downstream_decision(task)

    if problem == "field_intent_phase_resync_runtime_check":
        return _run_field_intent_phase_resync_runtime_check(task)

    if problem == "field_intent_guarded_runtime_patch_apply":
        return _run_field_intent_guarded_runtime_patch_apply(task)

    if problem == "field_intent_guarded_runtime_patch_generator":
        return _run_field_intent_guarded_runtime_patch_generator(task)

    if problem == "field_intent_phase_resync_guarded_apply":
        return _run_field_intent_phase_resync_guarded_apply(task)

    if problem == "field_intent_phase_resync_patch_proposal":
        return _run_field_intent_phase_resync_patch_proposal(task)

    if problem == "field_intent_phase_resync_patch":
        return _run_field_intent_phase_resync_patch_request(task)

    if problem == "field_intent_execute_repair":
        return _run_field_intent_executor(task)

    if problem == "field_intent_phase_repair":
        return _run_field_intent_repair_plan(task)

    if problem in FIELD_INTENT_PROBLEMS:
        return _run_field_intent_bridge_ack(task)

    if problem == "shadow_stdlib_group":
        execution_result = autofix_shadowed_stdlib(".", apply=True)
        validation_result = {"ok": execution_result.get("ok", False), "errors": []}

        shadow_changed_files = []
        actions = execution_result.get("actions", [])
        if isinstance(actions, list):
            for action in actions:
                if isinstance(action, dict):
                    to_path = str(action.get("to", "")).strip()
                    if to_path:
                        shadow_changed_files.append(to_path)

        execution_payload = {
            **execution_result,
            "changed_files": shadow_changed_files,
        }

        result = {
            "route": "SHADOW_STDLIB_AUTOFIX",
            "execution": execution_payload,
            "validation": validation_result,
            "ok": execution_result.get("ok", False),
            "reason": execution_result.get("reason", "shadow_stdlib_autofix"),
        }

        result["auto_commit"] = _maybe_auto_commit(result, problem)
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
