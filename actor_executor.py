import os
from datetime import datetime, UTC

from runtime_experimental.object_store import get_open_tasks, mark_task_done, mark_task_published
from runtime_experimental.github_bridge import is_github_enabled, create_issue, build_issue_from_task
from v_bridge import VBridge

OUTPUT_DIR = "reports"
BUS_PATH = os.environ.get("V_RESONANCE_PATH", "v_resonance.json")

MIN_INTENSITY_FOR_GITHUB = 0.8
MIN_NOVELTY_FOR_GITHUB = 0.85


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def should_publish_to_github(task):
    intensity = float(task.get("intensity", 0.0))
    novelty = float(task.get("novelty", 0.0))

    if intensity >= MIN_INTENSITY_FOR_GITHUB:
        return True, f"intensity>={MIN_INTENSITY_FOR_GITHUB}"

    if novelty >= MIN_NOVELTY_FOR_GITHUB:
        return True, f"novelty>={MIN_NOVELTY_FOR_GITHUB}"

    return False, "below_threshold"


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
        print("SKIP: action is WAIT")
        return

    if not open_tasks:
        print("SKIP: no open tasks")
        return

    task = None

    if latest_task_id:
        for t in open_tasks:
            if str(t.get("id")) == latest_task_id:
                task = t
                break

    if task is None:
        task = open_tasks[0]

    ensure_dir(OUTPUT_DIR)

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"{task['id']}_{ts}.md")

    report_text = (
        "GitCube Task Report\n\n"
        f"id: {task.get('id')}\n"
        f"title: {task.get('title')}\n"
        f"origin: {task.get('origin')}\n"
        f"kind: {task.get('kind')}\n"
        f"status: done\n"
        f"generated_at: {datetime.now(UTC).isoformat()}\n"
        f"action: {action}\n"
        f"intensity: {task.get('intensity')}\n"
        f"novelty: {task.get('novelty')}\n\n"
        f"payload: {task.get('payload', {})}\n"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)

    done_task = mark_task_done(str(task.get("id")), path)
    print("CREATED:", path)

    allow_publish, reason = should_publish_to_github(task)
    print("PUBLISH_DECISION:", allow_publish)
    print("PUBLISH_REASON:", reason)

    if not allow_publish:
        print("SKIP_GITHUB: below publish threshold")
        return

    if not is_github_enabled():
        print("SKIP_GITHUB: GitHub not configured")
        return

    issue = build_issue_from_task(done_task or task, action, path)
    result = create_issue(issue["title"], issue["body"])

    if result.get("ok"):
        mark_task_published(str(task.get("id")), result.get("url", ""))
        print("ISSUE:", result.get("url", ""))
    else:
        print("ERROR:", result.get("error", "unknown error"))


if __name__ == "__main__":
    main()
