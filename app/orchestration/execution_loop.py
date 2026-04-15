from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from runtime_experimental.object_store import get_latest_open_task
from actor_executor import execute_party, execute_pair
from router import should_use_party


REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


def make_report_path(task: Dict[str, Any]) -> str:
    task_id = str(task.get("id", "task_unknown")).strip()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return str(REPORTS_DIR / f"{task_id}_{ts}.md")


def write_report_header(report_path: str, task: Dict[str, Any]) -> None:
    title = str(task.get("title", "Untitled task")).strip()
    task_id = str(task.get("id", "task_unknown")).strip()
    payload = task.get("payload", {})

    text = (
        f"# GitCube Execution Report\n\n"
        f"- task_id: {task_id}\n"
        f"- title: {title}\n"
        f"- generated_at_utc: {datetime.utcnow().isoformat()}Z\n\n"
        f"## Payload\n\n"
        f"```python\n{payload}\n```\n"
    )
    Path(report_path).write_text(text, encoding="utf-8")


def append_report_result(report_path: str, result: Dict[str, Any]) -> None:
    text = (
        f"\n## Result\n\n"
        f"```python\n{result}\n```\n"
    )
    with open(report_path, "a", encoding="utf-8") as f:
        f.write(text)


def run_single_cycle() -> Dict[str, Any]:
    task: Optional[Dict[str, Any]] = get_latest_open_task()

    if not task:
        return {
            "ok": True,
            "reason": "no_open_tasks",
        }

    report_path = make_report_path(task)
    write_report_header(report_path, task)

    if should_use_party(task):
        result = execute_party(task, report_path)
    else:
        result = execute_pair(task, report_path)

    append_report_result(report_path, result)

    return {
        "ok": True,
        "task_id": str(task.get("id", "task_unknown")),
        "report_path": report_path,
        "execution_result": result,
    }


def run_loop(max_cycles: int = 10) -> Dict[str, Any]:
    completed = []

    for step in range(max_cycles):
        result = run_single_cycle()
        completed.append(result)

        if result.get("reason") == "no_open_tasks":
            break

    return {
        "ok": True,
        "cycles": len(completed),
        "results": completed,
    }


if __name__ == "__main__":
    print(run_loop(max_cycles=5))
