from runtime_experimental.pr_actor import run_pr_task
import os
from datetime import datetime, UTC
from typing import Optional, Dict, Any

from runtime_experimental.object_store import (
    get_open_tasks,
    mark_task_done,
    mark_task_published,
    load_objects,
    save_objects,
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
GITHUB_COOLDOWN_SECONDS = 300


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
        obj_id = str(obj.get("id", ""))
        if obj_id == current_id:
            continue
        if normalize_title(str(obj.get("title", ""))) == current_title:
            return obj
    return None


def find_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    for obj in load_objects():
        if str(obj.get("id")) == str(task_id):
            return obj
    return None


def build_graph_text(task: Dict[str, Any]) -> str:
    parent_id = task.get("parent_id")
    related_to = task.get("related_to", [])
    graph_depth = task.get("graph_depth", 0)

    parent_url = ""
    if parent_id:
        parent_task = find_task_by_id(str(parent_id))
        if parent_task:
            parent_url = str(parent_task.get("github_url", ""))

    lines = [
        "Graph Context",
        "",
        f"parent_id: {parent_id}",
        f"graph_depth: {graph_depth}",
        f"related_to: {related_to}",
    ]

    if parent_url:
        lines.append(f"parent_github_url: {parent_url}")

    return "\n".join(lines)


def parse_generated_at(text: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def get_last_published_time() -> Optional[datetime]:
    latest_dt = None

    for obj in load_objects():
        if not obj.get("published_to_github"):
            continue

        dt_raw = obj.get("published_at") or obj.get("generated_at")
        if not dt_raw:
            continue

        dt = parse_generated_at(str(dt_raw))
        if dt is None:
            continue

        if latest_dt is None or dt > latest_dt:
            latest_dt = dt

    return latest_dt


def cooldown_blocked() -> tuple[bool, str]:
    last_dt = get_last_published_time()
    if last_dt is None:
        return False, "no_previous_publish"

    now_dt = datetime.now(UTC)
    delta = (now_dt - last_dt).total_seconds()

    if delta < GITHUB_COOLDOWN_SECONDS:
        remaining = int(GITHUB_COOLDOWN_SECONDS - delta)
        return True, f"cooldown_active:{remaining}s"

    return False, "cooldown_passed"


def select_task(open_tasks, latest_task_id):
    # 🔥 ПРІОРИТЕТ PR задач
    for t in open_tasks:
        title = str(t.get("title", "")).lower()
        if "debug prints" in title:
            return t

    # fallback
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


    if action == "WAIT":
        return

    if not open_tasks:
        return

    task = select_task(open_tasks, latest_task_id)

    ensure_dir(OUTPUT_DIR)

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"{task['id']}_{ts}.md")

    now_iso = datetime.now(UTC).isoformat()

    audit_status = str(task.get("audit_status", "none"))
    audit_reason = str(task.get("audit_reason", "none"))

    report_text = (
        "GitCube Task Report\n\n"
        f"id: {task.get('id')}\n"
        f"title: {task.get('title')}\n"
        f"generated_at: {now_iso}\n"
        f"audit_status: {audit_status}\n"
        f"audit_reason: {audit_reason}\n"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)

    mark_task_done(str(task.get("id")), path)


    # 🔥 PR СПРОБА
    success, pr_reason = run_pr_task(task)

    if success:
        return

    # 🔥 fallback → ISSUE
    allow_publish, reason = should_publish_to_github(task)

    if not allow_publish:
        return

    if not is_github_enabled():
        return

    issue = build_issue_from_task(task, action, path)
    result = create_issue(issue["title"], issue["body"])

    if result.get("ok"):
        mark_task_published(str(task.get("id")), result.get("url", ""))
    else:


if __name__ == "__main__":
    main()
