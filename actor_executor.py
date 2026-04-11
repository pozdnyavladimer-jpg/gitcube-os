import os
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List

from runtime_experimental.pr_actor import run_pr_task
from runtime_experimental.assassin_actor import run_assassin_task
from runtime_experimental.healer_actor import run_healer_task
from runtime_experimental.mage_actor import run_mage_task

from runtime_experimental.object_store import (
    get_open_tasks,
    mark_task_in_progress,
    mark_task_done,
    mark_task_skipped,
    mark_task_failed,
    mark_task_absorbed,
    mark_task_published,
    load_objects,
)

from runtime_experimental.github_bridge import (
    is_github_enabled,
    create_issue,
    build_issue_from_task,
    find_open_issue_by_meta_key,
)

from runtime_experimental.memory_router import select_pair_with_memory
from runtime_experimental.tank_policy import evaluate_tank_policy
from v_bridge import VBridge

OUTPUT_DIR = "reports"
BUS_PATH = os.environ.get("V_RESONANCE_PATH", "v_resonance.json")

MIN_INTENSITY_FOR_GITHUB = 0.8
MIN_NOVELTY_FOR_GITHUB = 0.85

STRUCTURAL_PROBLEMS = {
    "missing_init",
    "missing_init_group",
    "python_without_docs",
    "package_structure",
    "missing_root_readme",
    "missing_start_here",
}

META_PROBLEMS = {
    "routing_failure",
    "no_target_path",
    "global_block",
}


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def should_publish_to_github(task: Dict[str, Any], tank_policy: Optional[Dict[str, Any]] = None):
    if tank_policy and tank_policy.get("force_publish"):
        return True, "tank_force_publish"

    intensity = float(task.get("intensity", 0.0))
    novelty = float(task.get("novelty", 0.0))

    if intensity >= MIN_INTENSITY_FOR_GITHUB:
        return True, f"intensity>={MIN_INTENSITY_FOR_GITHUB}"

    if novelty >= MIN_NOVELTY_FOR_GITHUB:
        return True, f"novelty>={MIN_NOVELTY_FOR_GITHUB}"

    return False, "below_threshold"


def normalize_title(text: str) -> str:
    return str(text or "").strip().lower()


def get_problem(task: Dict[str, Any]) -> str:
    payload = task.get("payload", {})
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("problem", "")).strip().lower()


def is_structural(task: Dict[str, Any]) -> bool:
    return get_problem(task) in STRUCTURAL_PROBLEMS


def is_meta(task: Dict[str, Any]) -> bool:
    return get_problem(task) in META_PROBLEMS


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


def is_absorbed(task: Dict[str, Any]) -> bool:
    meta_key = str(task.get("meta_key", "")).strip()
    if not meta_key:
        return False

    issue = find_open_issue_by_meta_key(meta_key)
    return bool(issue)


def select_task(open_tasks: List[Dict[str, Any]], latest_task_id: str = ""):
    if not open_tasks:
        return None

    valid_tasks = [t for t in open_tasks if not is_absorbed(t)]
    if not valid_tasks:
        return None

    # 1. structural first
    structural_tasks = [t for t in valid_tasks if is_structural(t)]
    if structural_tasks:
        return structural_tasks[0]

    # 2. if latest_task_id points to valid non-absorbed task
    if latest_task_id:
        for t in valid_tasks:
            if str(t.get("id")) == str(latest_task_id):
                return t

    # 3. prefer tasks with explicit path/paths
    with_path = []
    without_path = []

    for t in valid_tasks:
        payload = t.get("payload", {})
        if not isinstance(payload, dict):
            without_path.append(t)
            continue

        path = str(payload.get("path", "")).strip()
        paths = payload.get("paths", [])

        if path or (isinstance(paths, list) and len(paths) > 0):
            with_path.append(t)
        else:
            without_path.append(t)

    ordered = with_path + without_path
    return ordered[-1] if ordered else None


def build_report(task: Dict[str, Any], action: str) -> str:
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"{task['id']}_{ts}.md")
    now_iso = datetime.now(UTC).isoformat()

    report_text = (
        "GitCube Task Report\n\n"
        f"id: {task.get('id')}\n"
        f"title: {task.get('title')}\n"
        f"generated_at: {now_iso}\n"
        f"action: {action}\n"
        f"payload: {task.get('payload', {})}\n"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)

    return path


def run_primary_agent(primary_agent: str, task: Dict[str, Any]):
    agent = str(primary_agent or "").upper()

    if agent == "ARCHER":
        return run_pr_task(task)

    if agent == "ASSASSIN":
        return run_assassin_task(task)

    if agent == "HEALER":
        return run_healer_task(task)

    if agent == "MAGE":
        return run_mage_task(task)

    if agent == "TANK":
        return False, "tank_policy_mode"

    return False, f"unknown_agent:{agent}"


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
        print("=== DONE ===")
        return

    if not open_tasks:
        print("SKIP: no tasks")
        print("=== DONE ===")
        return

    task = select_task(open_tasks, latest_task_id)
    if task is None:
        print("SKIP: no valid task")
        print("=== DONE ===")
        return

    if is_absorbed(task):
        issue = find_open_issue_by_meta_key(str(task.get("meta_key", "")).strip())
        issue_url = issue.get("url", "") if issue else ""
        print("SELECTED TASK:", task.get("title"))
        print("TARGET PATH:", task.get("payload", {}).get("path"))
        print("ABSORBED_BY_ISSUE:", issue_url)
        mark_task_absorbed(str(task.get("id")), reason=f"absorbed_by_issue:{issue_url}")
        print("=== DONE ===")
        return

    print("SELECTED TASK:", task.get("title"))
    print("TARGET PATH:", task.get("payload", {}).get("path"))

    ensure_dir(OUTPUT_DIR)
    report_path = build_report(task, action)
    task_id = str(task.get("id"))

    mark_task_in_progress(task_id, report_path)
    print("REPORT:", report_path)

    primary_agent, support_agent, scores, pair_reason, memory_bias = select_pair_with_memory(task)

    print("PRIMARY_AGENT:", primary_agent)
    print("SUPPORT_AGENT:", support_agent)
    print("PAIR_REASON:", pair_reason)
    print("PAIR_SCORES:", scores)
    print("MEMORY_BIAS:", memory_bias)

    tank_policy = evaluate_tank_policy(task, primary_agent, support_agent, scores)
    if tank_policy:
        print("TANK_POLICY:", tank_policy)

    success, exec_reason = run_primary_agent(primary_agent, task)
    print("PRIMARY_ATTEMPT:", success, exec_reason)

    if success:
        mark_task_done(
            task_id,
            report_path,
            f"primary={primary_agent};support={support_agent};{exec_reason}",
        )
        print("DONE")
        print("=== DONE ===")
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
        "tank_policy_mode",
        "tank_blocked_local_execution",
        "root_not_supported",
    }

    tagged_reason = f"primary={primary_agent};support={support_agent};{exec_reason}"

    if exec_reason in skip_set or str(exec_reason).startswith("unsupported_extension:") or str(exec_reason).startswith("validation_failed:") or str(exec_reason).startswith("blocked_dir:"):
        mark_task_skipped(task_id, report_path, tagged_reason)
    else:
        mark_task_failed(task_id, report_path, tagged_reason)

    allow_publish, publish_reason = should_publish_to_github(task, tank_policy)
    print("PUBLISH:", allow_publish, publish_reason)

    if not allow_publish or not is_github_enabled():
        print("=== DONE ===")
        return

    duplicate = find_duplicate_task(task)
    if duplicate:
        print("DUPLICATE -> SKIP")
        print("=== DONE ===")
        return

    issue = build_issue_from_task(task, action, report_path)
    issue["body"] += (
        f"\n\nPrimary agent: {primary_agent}"
        f"\nSupport agent: {support_agent}"
        f"\nPair reason: {pair_reason}"
        f"\nScores: {scores}"
        f"\nMemory bias: {memory_bias}\n"
    )

    if tank_policy:
        issue["body"] += f"\nTank policy: {tank_policy}\n"

    result = create_issue(issue["title"], issue["body"])

    if result.get("ok"):
        mark_task_published(
            task_id,
            result.get("url", ""),
            report_path,
            f"primary={primary_agent};support={support_agent};issue",
        )
        print("ISSUE:", result.get("url"))
    else:
        mark_task_failed(
            task_id,
            report_path,
            f"primary={primary_agent};support={support_agent};issue_fail",
        )
        print("ERROR:", result.get("error", "unknown"))

    print("=== DONE ===")


if __name__ == "__main__":
    main()
