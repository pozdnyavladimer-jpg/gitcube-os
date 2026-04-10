from runtime_experimental.pr_actor import run_pr_task
from runtime_experimental.assassin_actor import run_assassin_task
from runtime_experimental.healer_actor import run_healer_task
from runtime_experimental.healer_support import run_healer_support
from runtime_experimental.mage_actor import run_mage_task
from runtime_experimental.tank_policy import build_tank_policy
from runtime_experimental.memory_router import select_pair_with_memory
from runtime_experimental.github_bridge import (
    is_github_enabled,
    create_issue,
    build_issue_from_task,
    find_open_issue_by_meta_key,
)
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
from v_bridge import VBridge

OUTPUT_DIR = "reports"
BUS_PATH = os.environ.get("V_RESONANCE_PATH", "v_resonance.json")

MIN_INTENSITY_FOR_GITHUB = 0.8
MIN_NOVELTY_FOR_GITHUB = 0.85


def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def get_policy_owner(primary_agent: str, support_agent: str, tank_policy) -> str:
    if tank_policy and (primary_agent == "TANK" or support_agent == "TANK"):
        return "TANK"
    return primary_agent


def should_publish_to_github(task, tank_policy=None):
    if tank_policy and tank_policy.get("force_publish"):
        return True, "tank_force_publish"

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


def get_task_meta_key(task):
    meta_key = str(task.get("meta_key", "")).strip()
    if meta_key:
        return meta_key

    payload = task.get("payload", {}) or {}
    problem = str(payload.get("problem", "generic_problem")).strip().lower()
    path = str(payload.get("path", "")).strip()
    priority = str(payload.get("priority", "")).strip().lower()
    origin = str(task.get("origin", "")).strip().lower()
    has_path = "path" if path else "no_path"
    return f"{problem}|{has_path}|{priority}|{origin}"


def is_absorbed_by_open_issue(task):
    if not is_github_enabled():
        return False, None

    meta_key = get_task_meta_key(task)
    if not meta_key:
        return False, None

    issue = find_open_issue_by_meta_key(meta_key)
    if not issue:
        return False, None

    return True, issue


def run_primary_agent(primary_agent: str, task: Dict[str, Any], tank_policy=None):
    if primary_agent == "TANK":
        return False, "tank_policy_mode"

    if tank_policy and tank_policy.get("block_local_execution"):
        return False, "tank_blocked_local_execution"

    if primary_agent == "ARCHER":
        return run_pr_task(task)

    if primary_agent == "ASSASSIN":
        return run_assassin_task(task)

    if primary_agent == "HEALER":
        return run_healer_task(task)

    if primary_agent == "MAGE":
        return run_mage_task(task)

    return False, "not_supported_task"


def run_support_agent(support_agent: str, task: Dict[str, Any]):
    if support_agent == "HEALER":
        return run_healer_support(task)

    if support_agent == "NONE":
        return True, "no_support_needed"

    return True, f"support_not_implemented:{support_agent}"


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

    absorbed, absorbed_issue = is_absorbed_by_open_issue(task)
    if absorbed:
        ensure_dir(OUTPUT_DIR)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(OUTPUT_DIR, f"{task_id}_{ts}.md")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"TASK {task_id}\n")
            f.write(f"TITLE: {task.get('title')}\n")
            f.write("ABSORBED_BY_ISSUE: True\n")
            f.write(f"ISSUE_URL: {absorbed_issue.get('url', '')}\n")
            f.write(f"ISSUE_TITLE: {absorbed_issue.get('title', '')}\n")

        mark_task_done(
            task_id,
            report_path,
            f"primary=TANK;support=NONE;policy_owner=TANK;absorbed_by_issue:{absorbed_issue.get('url', '')}",
        )
        print("ABSORBED_BY_ISSUE:", absorbed_issue.get("url", ""))
        print("DONE")
        return

    primary_agent, support_agent, scores, pair_reason, memory_bias = select_pair_with_memory(task)

    print("PRIMARY_AGENT:", primary_agent)
    print("SUPPORT_AGENT:", support_agent)
    print("PAIR_REASON:", pair_reason)
    print("PAIR_SCORES:", scores)
    print("MEMORY_BIAS:", memory_bias)

    tank_policy = None
    if primary_agent == "TANK" or support_agent == "TANK":
        tank_policy = build_tank_policy(task)
        print("TANK_POLICY:", tank_policy)

    policy_owner = get_policy_owner(primary_agent, support_agent, tank_policy)

    ensure_dir(OUTPUT_DIR)

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(OUTPUT_DIR, f"{task_id}_{ts}.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"TASK {task_id}\n")
        f.write(f"TITLE: {task.get('title')}\n")
        f.write(f"PRIMARY_AGENT: {primary_agent}\n")
        f.write(f"SUPPORT_AGENT: {support_agent}\n")
        f.write(f"POLICY_OWNER: {policy_owner}\n")
        f.write(f"PAIR_REASON: {pair_reason}\n")
        f.write(f"PAIR_SCORES: {scores}\n")
        f.write(f"MEMORY_BIAS: {memory_bias}\n")
        if tank_policy:
            f.write(f"TANK_POLICY: {tank_policy}\n")

    mark_task_in_progress(task_id, report_path)
    print("REPORT:", report_path)

    try:
        success, exec_reason = run_primary_agent(primary_agent, task, tank_policy=tank_policy)
    except Exception as e:
        mark_task_failed(
            task_id,
            report_path,
            f"primary={primary_agent};support={support_agent};policy_owner={policy_owner};exception:{e}",
        )
        print("PRIMARY_ATTEMPT:", False, f"primary={primary_agent};exception:{e}")
        return

    print("PRIMARY_ATTEMPT:", success, exec_reason)

    support_success = True
    support_reason = "support_skipped"

    if success:
        try:
            support_success, support_reason = run_support_agent(support_agent, task)
        except Exception as e:
            support_success, support_reason = False, f"support_exception:{e}"

        print("SUPPORT_ATTEMPT:", support_success, support_reason)

        if support_success:
            final_reason = (
                f"primary={primary_agent};support={support_agent};policy_owner={policy_owner};"
                f"primary_reason={exec_reason};support_reason={support_reason}"
            )
            mark_task_done(task_id, report_path, final_reason)
            print("DONE")
            return

        allow, publish_reason = should_publish_to_github(task, tank_policy=tank_policy)
        print("PUBLISH:", allow, publish_reason)

        if not allow or not is_github_enabled():
            mark_task_failed(
                task_id,
                report_path,
                f"primary={primary_agent};support={support_agent};policy_owner={policy_owner};support_failed={support_reason}",
            )
            return

        issue = build_issue_from_task(task, action, report_path)
        issue["body"] += (
            f"\n\nPrimary agent: {primary_agent}"
            f"\nSupport agent: {support_agent}"
            f"\nPolicy owner: {policy_owner}"
            f"\nPair reason: {pair_reason}"
            f"\nScores: {scores}"
            f"\nMemory bias: {memory_bias}"
            f"\nSupport failure: {support_reason}"
        )
        if tank_policy:
            issue["body"] += f"\nTank policy: {tank_policy}"

        result = create_issue(issue["title"], issue["body"])

        if result.get("ok"):
            mark_task_published(
                task_id,
                result.get("url"),
                report_path,
                f"primary={primary_agent};support={support_agent};policy_owner={policy_owner};support_failed_issue",
            )
            print("ISSUE:", result.get("url"))
        else:
            mark_task_failed(
                task_id,
                report_path,
                f"primary={primary_agent};support={support_agent};policy_owner={policy_owner};support_failed_issue_fail",
            )
            print("ERROR:", result.get("error", "unknown"))
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

    tagged_reason = f"primary={primary_agent};support={support_agent};policy_owner={policy_owner};{exec_reason}"

    if exec_reason in skip_set or str(exec_reason).startswith("unsupported_extension:") or str(exec_reason).startswith("validation_failed:") or str(exec_reason).startswith("blocked_dir:"):
        mark_task_skipped(task_id, report_path, tagged_reason)
    else:
        mark_task_failed(task_id, report_path, tagged_reason)

    allow, publish_reason = should_publish_to_github(task, tank_policy=tank_policy)
    print("PUBLISH:", allow, publish_reason)

    if not allow or not is_github_enabled():
        return

    duplicate = find_duplicate_task(task)
    if duplicate:
        print("DUPLICATE -> SKIP")
        return

    issue = build_issue_from_task(task, action, report_path)
    issue["body"] += (
        f"\n\nPrimary agent: {primary_agent}"
        f"\nSupport agent: {support_agent}"
        f"\nPolicy owner: {policy_owner}"
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
            result.get("url"),
            report_path,
            f"primary={primary_agent};support={support_agent};policy_owner={policy_owner};issue",
        )
        print("ISSUE:", result.get("url"))
    else:
        mark_task_failed(
            task_id,
            report_path,
            f"primary={primary_agent};support={support_agent};policy_owner={policy_owner};issue_fail",
        )
        print("ERROR:", result.get("error", "unknown"))


if __name__ == "__main__":
    main()
