from __future__ import annotations

from typing import Dict, Any

from app.orchestration.task_dispatcher import dispatch_task


def run_mage(task: Dict[str, Any]) -> Dict[str, Any]:
    result = dispatch_task(task)
    return {
        "ok": bool(result.get("ok", False)),
        "role": "MAGE",
        "result": result,
        "reason": result.get("reason", result.get("execution", {}).get("reason", "")),
    }
