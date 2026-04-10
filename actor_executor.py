from runtime_experimental.pr_actor import run_pr_task
import os
from datetime import datetime, UTC
from typing import Optional, Dict, Any

from runtime_experimental.object_store import (
    get_open_tasks,
    get_task_by_id,
    mark_task_in_progress,
    mark_task_done,
    mark_task_published,
    mark_task_skipped,
    mark_task_failed,
    load_objects,
)
from runtime_experimental.github_bridge import (
    is_github_enabled,
    create_issue,
    build_issue_from_task,
)
from v_bridge import VBridge

OUTPUT_DIR = "reports"
BUS_PATH = os.environ.get("V_RESONANCE_PATH", "v_resonance.json")

MIN_INTENSITY_FOR_GITHUB = 0.8
MIN_NOVELTY_FOR_GITHUB = 0.85


def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def should_publish_to_github(task):
    intensity = float(task.get("intensity", 0.0))
    novelty = float(task.get("novelty", 0.0))

    if intensity >= MIN_INTENSITY_FOR_GITHUB:
        return True, "intensity"

    if novelty >= MIN_NOVELTY_FOR_GITHUB:
        return True, "novelty"

    return False, "low_signal"


def validate_task_payload(task):
    payload = task.get("payload", {}) or {}
    path = str(payload.get("path", "")).strip()

    title = str(task.get("title", "")).lower()
    if "debug prints" in title and not path:
        return False, "missing_payload_path"

    return True, "ok"


def select_task(open_tasks, latest_task_id):
    if latest_task_id:
        t = get_task_by_id(latest_task_id)
        if t and t.get("status") == "open":
            return t

    if open_tasks:
        return open_tasks[-1]

    return None


def main():
    bridge = VBridge(BUS_PATH)
    state = bridge.read_state()
    signal = dict(state.get("signal", {}))

    action = str(signal.get("action", "WAIT"))
    latest_task_id = str(signal.get("latest_task_id", ""))

    open_tasks = get_open_tasks()

    print("ACTION:", action)
    print("TASKS:", len(open_tasks))

    if action == "WAIT":
        return

    task = select_task(open_tasks, latest_task_id)
    if not task:
        return

    task_id = str(task.get("id"))

    payload_ok, reason = validate_task_payload(task)
    if not payload_ok:
        mark_task_skipped(task_id, reason=reason)
        print("SKIP:", reason)
        return

    ensure_dir(OUTPUT_DIR)

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(OUTPUT_DIR, f"{task_id}_{ts}.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"TASK {task_id}\n")

    mark_task_in_progress(task_id, report_path)

    try:
        success, pr_reason = run_pr_task(task)
    except Exception as e:
        mark_task_failed(task_id, report_path, str(e))
        return

    print("PR_ATTEMPT:", success, pr_reason)

    if success:
        mark_task_done(task_id, report_path, pr_reason)
        print("DONE")
        return

    skip_set = {
        "no_changes",
        "not_supported_task",
        "missing_path",
        "path_not_found",
        "blocked_file",
        "outside_safe_prefix",
    }

    if pr_reason in skip_set:
        mark_task_skipped(task_id, report_path, pr_reason)
    else:
        mark_task_failed(task_id, report_path, pr_reason)

    allow, _ = should_publish_to_github(task)

    if not allow or not is_github_enabled():
        return

    issue = build_issue_from_task(task, action, report_path)
    result = create_issue(issue["title"], issue["body"])

    if result.get("ok"):
        mark_task_published(task_id, result.get("url"), report_path, "issue")
    else:
        mark_task_failed(task_id, report_path, "issue_fail")


if __name__ == "__main__":
    main()
