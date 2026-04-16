from __future__ import annotations

from datetime import datetime, UTC
from typing import Dict, Any, Optional

from runtime_experimental.object_store import (
    get_latest_open_task,
)
from actor_executor import execute_party, execute_pair
from router import should_use_party
from repo_analyzer import refresh_tasks_from_analyzer
from core.memory.task_cooldown import is_task_on_cooldown, touch_task
from core.memory.graph_weight_engine import apply_decay


def make_report_path(task: Dict[str, Any]) -> str:
    task_id = str(task.get("id", "task_unknown"))
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return f"reports/task_{task_id}_{ts}.md"


def write_report_header(report_path: str, task: Dict[str, Any]) -> None:
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Task Report\n\n")
        f.write(f"- task_id: {task.get('id', 'task_unknown')}\n")
        f.write(f"- title: {task.get('title', '')}\n")
        f.write(f"- payload: {task.get('payload', {})}\n")


def append_report_result(report_path: str, result: Dict[str, Any]) -> None:
    with open(report_path, "a", encoding="utf-8") as f:
        f.write("\n## Result\n\n")
        f.write(str(result))
        f.write("\n")


def run_single_cycle(cooldown_seconds: int = 900) -> Dict[str, Any]:
    task: Optional[Dict[str, Any]] = get_latest_open_task()

    if not task:
        return {
            "ok": True,
            "reason": "no_open_tasks",
        }

    task_id = str(task.get("id", "task_unknown"))

    if is_task_on_cooldown(task_id):
        return {
            "ok": True,
            "reason": "task_on_cooldown",
            "task_id": task_id,
        }


    report_path = make_report_path(task)
    write_report_header(report_path, task)

    if should_use_party(task):
        result = execute_party(task, report_path)
    else:
        result = execute_pair(task, report_path)

    append_report_result(report_path, result)
    touch_task(task_id, cooldown_seconds=cooldown_seconds)

    return {
        "ok": True,
        "task_id": task_id,
        "report_path": report_path,
        "execution_result": result,
    }


def run_loop(max_cycles: int = 10, refresh_first: bool = True, cooldown_seconds: int = 900) -> Dict[str, Any]:
    completed = []
    analyzer_result: Dict[str, Any] = {"ok": True, "reason": "refresh_skipped"}

    if refresh_first:
        analyzer_result = refresh_tasks_from_analyzer()
        print("ANALYZER:", analyzer_result)

    for _ in range(max_cycles):
        result = run_single_cycle(cooldown_seconds=cooldown_seconds)
        completed.append(result)

        if result.get("reason") in {"no_open_tasks", "task_on_cooldown"}:
            break

    decay_result = apply_decay()
    print("GRAPH_DECAY:", decay_result)

    return {
        "ok": True,
        "analyzer": analyzer_result,
        "cycles": len(completed),
        "results": completed,
        "graph_decay": decay_result,
    }


if __name__ == "__main__":
    print(run_loop(max_cycles=5, refresh_first=True, cooldown_seconds=900))
