from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, Optional
import subprocess
import sys

from runtime_experimental.object_store import get_latest_open_task
from actor_executor import execute_party, execute_pair
from router import should_use_party
from core.memory.task_cooldown import is_task_on_cooldown, touch_task


REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


def make_report_path(task: Dict[str, Any]) -> str:
    task_id = str(task.get("id", "task_unknown")).strip()
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return str(REPORTS_DIR / f"{task_id}_{ts}.md")


def write_report_header(report_path: str, task: Dict[str, Any]) -> None:
    title = str(task.get("title", "Untitled task")).strip()
    task_id = str(task.get("id", "task_unknown")).strip()
    payload = task.get("payload", {})

    text = (
        f"# GitCube Execution Report\n\n"
        f"- task_id: {task_id}\n"
        f"- title: {title}\n"
        f"- generated_at_utc: {datetime.now(UTC).isoformat()}Z\n\n"
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


def refresh_tasks_from_analyzer() -> Dict[str, Any]:
    analyzer_path = Path("repo_analyzer.py")
    if not analyzer_path.exists():
        return {
            "ok": False,
            "reason": "repo_analyzer_missing",
        }

    try:
        proc = subprocess.run(
            [sys.executable, "repo_analyzer.py"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "ok": proc.returncode == 0,
            "reason": "analyzer_run_complete" if proc.returncode == 0 else "analyzer_run_failed",
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-2000:],
        }
    except Exception as e:
        return {
            "ok": False,
            "reason": f"analyzer_exception:{e}",
        }


def run_single_cycle(cooldown_seconds: int = 900) -> Dict[str, Any]:
    task: Optional[Dict[str, Any]] = get_latest_open_task()

    if not task:
        return {
            "ok": True,
            "reason": "no_open_tasks",
        }

    task_id = str(task.get("id", "task_unknown")).strip()

    cooldown = is_task_on_cooldown(task_id, cooldown_seconds=cooldown_seconds)
    if cooldown.get("on_cooldown", False):
        return {
            "ok": True,
            "reason": "task_on_cooldown",
            "task_id": task_id,
            "cooldown": cooldown,
        }

    touch_task(task_id, meta={"title": task.get("title", "")})

    report_path = make_report_path(task)
    write_report_header(report_path, task)

    if should_use_party(task):
        result = execute_party(task, report_path)
    else:
        result = execute_pair(task, report_path)

    append_report_result(report_path, result)

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

    for step in range(max_cycles):
        result = run_single_cycle(cooldown_seconds=cooldown_seconds)
        completed.append(result)

        if result.get("reason") in {"no_open_tasks", "task_on_cooldown"}:
            break

    return {
        "ok": True,
        "analyzer": analyzer_result,
        "cycles": len(completed),
        "results": completed,
    }


if __name__ == "__main__":
    print(run_loop(max_cycles=5, refresh_first=True, cooldown_seconds=900))
