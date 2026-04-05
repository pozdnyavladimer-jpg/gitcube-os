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
GITHUB_COOLDOWN_SECONDS = 300  # 5 хвилин


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

    duplicate = find_duplicate_task(task)
    duplicate_id = str(duplicate.get("id", "")) if duplicate else ""
    duplicate_url = str(duplicate.get("github_url", "")) if duplicate else ""

    now_iso = datetime.now(UTC).isoformat()

    report_text = (
        "GitCube Task Report\n\n"
        f"id: {task.get('id')}\n"
        f"title: {task.get('title')}\n"
        f"origin: {task.get('origin')}\n"
        f"kind: {task.get('kind')}\n"
        f"status: done\n"
        f"generated_at: {now_iso}\n"
        f"action: {action}\n"
        f"intensity: {task.get('intensity')}\n"
        f"novelty: {task.get('novelty')}\n"
        f"duplicate_found: {bool(duplicate)}\n"
        f"duplicate_id: {duplicate_id}\n"
        f"duplicate_url: {duplicate_url}\n\n"
        f"{build_graph_text(task)}\n\n"
        f"payload: {task.get('payload', {})}\n"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)

    done_task = mark_task_done(str(task.get("id")), path)
    if done_task is not None:
        done_task["generated_at"] = now_iso

    print("CREATED:", path)

    allow_publish, reason = should_publish_to_github(task)
    print("PUBLISH_DECISION:", allow_publish)
    print("PUBLISH_REASON:", reason)

    if duplicate:
        print("DUPLICATE_FOUND:", duplicate_id)
        if duplicate_url:
            print("DUPLICATE_URL:", duplicate_url)
        print("SKIP_GITHUB: duplicate title")
        return

    if not allow_publish:
        print("SKIP_GITHUB: below publish threshold")
        return

    cooldown_is_on, cooldown_reason = cooldown_blocked()
    if cooldown_is_on:
        print("SKIP_GITHUB:", cooldown_reason)
        return

    if not is_github_enabled():
        print("SKIP_GITHUB: GitHub not configured")
        return

    issue = build_issue_from_task(done_task or task, action, path)

    graph_block = "\n\n" + build_graph_text(done_task or task)
    issue["body"] = issue["body"] + graph_block

    result = create_issue(issue["title"], issue["body"])

    if result.get("ok"):
        mark_task_published(str(task.get("id")), result.get("url", ""))
        data = load_objects()
        for obj in data:
            if str(obj.get("id")) == str(task.get("id")):
                obj["published_at"] = now_iso
                break
        from runtime_experimental.object_store import save_objects
        save_objects(data)
        print("ISSUE:", result.get("url", ""))
    else:
        print("ERROR:", result.get("error", "unknown error"))


if __name__ == "__main__":
    main()
