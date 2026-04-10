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
from router import select_agent

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
    return True, "ok"


def normalize_title(text: str) -> str:
    return str(text or "").strip().lower()


def find_duplicate_task(task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    current_id = str(task.get("id", ""))
    current_title = normalize_title(task.get("title", ""))

    if not current_title:
        return None

    for obj in load_objects():
        if str(obj.get("id", "")) == current_id:
            continue
        if normalize_title(obj.get("title", "")) == current_title:
            return obj
    return None


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
    print("GITHUB:", is_github_enabled())

    if action == "WAIT":
        print("SKIP: WAIT")
        return

    task = select_task(open_tasks, latest_task_id)
    if not task:
        print("SKIP: no task")
        return

    task_id = str(task.get("id"))
    print("SELECTED TASK:", task.get("title"))
    print("TARGET PATH:", task.get("payload", {}).get("path"))

    payload_ok, reason = validate_task_payload(task)
    if not payload_ok:
        mark_task_skipped(task_id, reason=reason)
        print("SKIP:", reason)
        return

    selected_agent, scores, route_reason = select_agent(task)

    print("ROUTED_AGENT:", selected_agent)
    print("ROUTE_REASON:", route_reason)
    print("ROUTE_SCORES:", scores)

    ensure_dir(OUTPUT_DIR)

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(OUTPUT_DIR, f"{task_id}_{ts}.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"TASK {task_id}\n")
        f.write(f"TITLE: {task.get('title')}\n")
        f.write(f"ROUTED_AGENT: {selected_agent}\n")
        f.write(f"ROUTE_REASON: {route_reason}\n")
        f.write(f"ROUTE_SCORES: {scores}\n")

    mark_task_in_progress(task_id, report_path)
    print("REPORT:", report_path)

    if selected_agent == "ARCHER":
        try:
            success, pr_reason = run_pr_task(task)
        except Exception as e:
            mark_task_failed(task_id, report_path, f"archer_exception:{e}")
            print("PR_ATTEMPT:", False, f"archer_exception:{e}")
            return

        print("PR_ATTEMPT:", success, pr_reason)

        if success:
            mark_task_done(task_id, report_path, f"agent={selected_agent};{pr_reason}")
            print("DONE")
            return

        skip_set = {
            "no_changes",
            "not_supported_task",
            "missing_path",
            "path_not_found",
            "blocked_file",
            "blocked_runtime_experimental",
            "blocked_core_runtime_app",
            "outside_safe_prefix",
            "missing_payload_path",
        }

        if pr_reason in skip_set or str(pr_reason).startswith("unsupported_extension:") or str(pr_reason).startswith("validation_failed:"):
            mark_task_skipped(task_id, report_path, f"agent={selected_agent};{pr_reason}")
        else:
            mark_task_failed(task_id, report_path, f"agent={selected_agent};{pr_reason}")

    allow, publish_reason = should_publish_to_github(task)
    print("PUBLISH:", allow, publish_reason)

    if not allow or not is_github_enabled():
        return

    duplicate = find_duplicate_task(task)
    if duplicate:
        print("DUPLICATE -> SKIP")
        return

    issue = build_issue_from_task(task, action, report_path)
    issue["body"] += f"\n\nRouted agent: {selected_agent}\nRoute reason: {route_reason}\nScores: {scores}\n"

    result = create_issue(issue["title"], issue["body"])

    if result.get("ok"):
        mark_task_published(task_id, result.get("url"), report_path, f"agent={selected_agent};issue")
        print("ISSUE:", result.get("url"))
    else:
        mark_task_failed(task_id, report_path, f"agent={selected_agent};issue_fail")
        print("ERROR:", result.get("error", "unknown"))


if __name__ == "__main__":
    main()
