from runtime_experimental.pr_actor import run_pr_task
import os
from datetime import datetime, UTC
from typing import Optional, Dict, Any

from runtime_experimental.object_store import (
    get_open_tasks,
    mark_task_done,
    mark_task_published,
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


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def should_publish_to_github(task: Dict[str, Any]):
    intensity = float(task.get("intensity", 0.0))
    novelty = float(task.get("novelty", 0.0))

    if intensity >= MIN_INTENSITY_FOR_GITHUB:
        return True, f"intensity>={MIN_INTENSITY_FOR_GITHUB}"

    if novelty >= MIN_NOVELTY_FOR_GITHUB:
        return True, f"novelty>={MIN_NOVELTY_FOR_GITHUB}"

    return False, "below_threshold"


def normalize_title(text: str) -> str:
    return str(text or "").strip().lower()


def find_duplicate_task(task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    current_id = str(task.get("id", ""))
    current_title = normalize_title(task.get("title", ""))

    if not current_title:
        return None

    for obj in load_objects():
        if str(obj.get("id")) == current_id:
            continue
        if normalize_title(obj.get("title", "")) == current_title:
            return obj
    return None


def ensure_safe_payload(task):
    payload = task.get("payload", {}) or {}
    path = payload.get("path")

    if path:
        return task

    # fallback → знайти safe файл
    for root, _, files in os.walk("examples"):
        for f in files:
            if f.endswith(".py"):
                safe_path = os.path.join(root, f).replace("\\", "/")
                task["payload"] = {"path": safe_path}
                task["title"] = f"Remove debug prints in {safe_path}"
                return task

    return task


def select_task(open_tasks, latest_task_id):
    for t in open_tasks:
        title = str(t.get("title", "")).lower()
        if "debug prints" in title:
            return t

    if latest_task_id:
        for t in open_tasks:
            if str(t.get("id")) == latest_task_id:
                return t

    return open_tasks[0]


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
        print("SKIP: WAIT")
        return

    if not open_tasks:
        print("SKIP: no tasks")
        return

    task = select_task(open_tasks, latest_task_id)
    task = ensure_safe_payload(task)

    print("SELECTED TASK:", task.get("title"))
    print("TARGET PATH:", task.get("payload", {}).get("path"))

    ensure_dir(OUTPUT_DIR)

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"{task['id']}_{ts}.md")

    now_iso = datetime.now(UTC).isoformat()

    report_text = (
        "GitCube Task Report\n\n"
        f"id: {task.get('id')}\n"
        f"title: {task.get('title')}\n"
        f"generated_at: {now_iso}\n"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)

    mark_task_done(str(task.get("id")), path)

    print("REPORT:", path)

    # 🔥 PR
    success, pr_reason = run_pr_task(task)
    print("PR_ATTEMPT:", success, pr_reason)

    if success:
        print("PR_CREATED → DONE")
        return

    # fallback → ISSUE
    allow_publish, reason = should_publish_to_github(task)

    print("PUBLISH:", allow_publish, reason)

    if not allow_publish:
        return

    if not is_github_enabled():
        print("GitHub not enabled")
        return

    duplicate = find_duplicate_task(task)
    if duplicate:
        print("DUPLICATE → SKIP")
        return

    issue = build_issue_from_task(task, action, path)
    result = create_issue(issue["title"], issue["body"])

    if result.get("ok"):
        mark_task_published(str(task.get("id")), result.get("url", ""))
        print("ISSUE:", result.get("url"))
    else:
        print("ERROR:", result.get("error", "unknown"))


if __name__ == "__main__":
    main()
