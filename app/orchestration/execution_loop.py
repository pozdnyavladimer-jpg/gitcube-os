from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, Optional
import subprocess
import sys

from runtime_experimental.object_store import get_latest_open_task
from actor_executor import execute_party, execute_pair
from router import should_use_party


REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

SEEN_TASKS = set()  # 🔥 анти-повтор


def make_report_path(task: Dict[str, Any]) -> str:
    task_id = str(task.get("id", "task_unknown")).strip()
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return str(REPORTS_DIR / f"{task_id}_{ts}.md")


def refresh_tasks_from_analyzer():
    try:
        proc = subprocess.run(
            [sys.executable, "repo_analyzer.py"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {"ok": proc.returncode == 0}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def run_single_cycle():
    task = get_latest_open_task()

    if not task:
        return {"ok": True, "reason": "no_open_tasks"}

    task_id = str(task.get("id"))

    # 🔥 АНТИ-ПОВТОР
    if task_id in SEEN_TASKS:
        return {"ok": True, "reason": "skip_seen_task", "task_id": task_id}

    SEEN_TASKS.add(task_id)

    report_path = make_report_path(task)

    if should_use_party(task):
        result = execute_party(task, report_path)
    else:
        result = execute_pair(task, report_path)

    return {
        "ok": True,
        "task_id": task_id,
        "report_path": report_path,
        "execution_result": result,
    }


def run_loop(max_cycles: int = 10):
    refresh = refresh_tasks_from_analyzer()
    print("ANALYZER:", refresh)

    results = []

    for _ in range(max_cycles):
        res = run_single_cycle()
        results.append(res)

        if res.get("reason") == "no_open_tasks":
            break

    return {"ok": True, "cycles": len(results), "results": results}


if __name__ == "__main__":
    print(run_loop(10))
