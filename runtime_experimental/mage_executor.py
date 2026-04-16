from __future__ import annotations

from typing import Dict, Any

from app.orchestration.task_dispatcher import dispatch_task
from runtime_experimental.tank_policy import evaluate_tank_policy


def run_mage(task: Dict[str, Any]) -> Dict[str, Any]:
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
