from __future__ import annotations

from typing import Dict, Any
from typing import List


from app.orchestration.task_dispatcher import dispatch_task
from runtime_experimental.tank_policy import evaluate_tank_policy
from pathlib import Path




def _scope_module_to_path(module: str) -> str:
    mod = str(module or "").strip().strip(".")
    if not mod:
        return ""
    return mod.replace(".", "/") + ".py"


def _path_exists(path: str) -> bool:
    sp = str(path or "").strip()
    return bool(sp) and Path(sp).exists()


def _priority_scope_limit(priority: str) -> int:
    p = str(priority or "normal").strip().lower()
    if p == "critical":
        return 8
    if p == "high":
        return 3
    return 0


def _merge_scope_paths(task: Dict[str, Any], max_scope_paths: int = 6) -> Dict[str, Any]:
    prepared = dict(task or {})
    payload = prepared.get("payload", {})
    if not isinstance(payload, dict):
        payload = {}

    priority = str(prepared.get("priority", "normal")).strip().lower()
    max_scope_paths = _priority_scope_limit(priority)

    original_paths = payload.get("paths", [])
    if not isinstance(original_paths, list):
        original_paths = []

    repair_scope = prepared.get("_repair_scope", {})
    if not isinstance(repair_scope, dict):
        repair_scope = {}

    targets = repair_scope.get("targets", [])
    if not isinstance(targets, list):
        targets = []

    dependents_map = repair_scope.get("dependents", {})
    if not isinstance(dependents_map, dict):
        dependents_map = {}

    merged: List[str] = []
    seen = set()

    for item in original_paths:
        sp = str(item).strip()
        if sp and sp not in seen:
            seen.add(sp)
            merged.append(sp)

    if max_scope_paths <= 0:
        payload["paths"] = merged
        prepared["payload"] = payload
        prepared["_scope_paths_added"] = 0
        return prepared

    scope_modules: List[str] = []

    # only direct dependents of explicit targets
    for target in targets:
        st = str(target).strip()
        if not st:
            continue

        if priority == "critical":
            if st not in scope_modules:
                scope_modules.append(st)

        deps = dependents_map.get(st, [])
        if isinstance(deps, list):
            for dep in deps:
                sdep = str(dep).strip()
                if sdep and sdep not in scope_modules:
                    scope_modules.append(sdep)

    added = 0
    for mod in scope_modules:
        path = _scope_module_to_path(mod)
        if not path or path in seen or not _path_exists(path):
            continue
        if added >= max_scope_paths:
            break
        seen.add(path)
        merged.append(path)
        added += 1

    payload["paths"] = merged
    prepared["payload"] = payload
    prepared["_scope_paths_added"] = added
    prepared["_scope_policy"] = {
        "priority": priority,
        "max_scope_paths": max_scope_paths,
        "mode": "direct_dependents_only" if priority != "critical" else "critical_bounded_wave",
    }
    return prepared


def run_mage(task: Dict[str, Any]) -> Dict[str, Any]:
    task = _merge_scope_paths(task)
    # 👉 1. Підготовка payload
    prepared = dict(task or {})
    payload = dict(prepared.get("payload", {}) or {})

    payload.setdefault("has_shadow_backup", True)
    payload.setdefault("executor_hint", "MAGE")

    prepared["payload"] = payload

    # 👉 2. Проганяємо через policy
    policy = evaluate_tank_policy(prepared)

    if policy.get("block_local_execution", False):
        return {
            "ok": False,
            "role": "MAGE",
            "reason": policy.get("note", "blocked"),
            "policy": policy,
        }

    # 👉 3. Якщо дозволено — виконуємо
    result = dispatch_task(prepared)

    return {
        "ok": bool(result.get("ok", False)),
        "role": "MAGE",
        "result": result,
        "reason": result.get("reason", ""),
        "policy": policy,
    }
