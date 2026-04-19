from __future__ import annotations

from typing import Dict, Any
from typing import List


from app.orchestration.task_dispatcher import dispatch_task
from runtime_experimental.tank_policy import evaluate_tank_policy




def _scope_module_to_path(module: str) -> str:
    mod = str(module or "").strip().strip(".")
    if not mod:
        return ""
    return mod.replace(".", "/") + ".py"


def _merge_scope_paths(task: Dict[str, Any], max_scope_paths: int = 6) -> Dict[str, Any]:
    prepared = dict(task or {})
    payload = prepared.get("payload", {})
    if not isinstance(payload, dict):
        payload = {}

    original_paths = payload.get("paths", [])
    if not isinstance(original_paths, list):
        original_paths = []

    repair_scope = prepared.get("_repair_scope", {})
    if not isinstance(repair_scope, dict):
        repair_scope = {}

    scope = repair_scope.get("scope", [])
    if not isinstance(scope, list):
        scope = []

    merged: List[str] = []
    seen = set()

    for item in original_paths:
        sp = str(item).strip()
        if sp and sp not in seen:
            seen.add(sp)
            merged.append(sp)

    added = 0
    for mod in scope:
        path = _scope_module_to_path(mod)
        if not path or path in seen:
            continue
        if added >= max_scope_paths:
            break
        seen.add(path)
        merged.append(path)
        added += 1

    payload["paths"] = merged
    prepared["payload"] = payload
    prepared["_scope_paths_added"] = added
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
