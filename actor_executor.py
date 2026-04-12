import os
from typing import Dict, Any, Optional, List

from runtime_experimental.object_store import (
    get_latest_open_task,
    mark_task_done,
    mark_task_failed,
    mark_task_published,
    mark_task_skipped,
)
from runtime_experimental.github_bridge import (
    create_issue,
    is_github_enabled,
)
from runtime_experimental.tank_policy import evaluate_tank_policy
from router import select_pair, select_party, should_use_party


def build_issue_from_task(task: Dict[str, Any], action: str, report_path: str) -> Dict[str, str]:
    title = str(task.get("title", "Untitled task")).strip()
    body = [
        f"Action: {action}",
        f"Report: {report_path}",
        "",
        "Payload:",
        str(task.get("payload", {})),
        "",
        "Resonance:",
        str(task.get("resonance_vector", {})),
    ]
    return {
        "title": title,
        "body": "\n".join(body),
    }


def find_duplicate_task(task: Dict[str, Any]) -> bool:
    return False


def should_publish_to_github(task: Dict[str, Any], tank_policy: Optional[Dict[str, Any]]) -> tuple[bool, str]:
    if not is_github_enabled():
        return False, "github_disabled"

    if not tank_policy:
        return False, "no_tank_policy"

    force_publish = bool(tank_policy.get("force_publish", False))
    intensity = float(task.get("intensity", 0.0) or 0.0)

    if force_publish:
        return True, "tank_force_publish"

    if intensity >= 0.8:
        return True, "intensity>=0.8"

    return False, "below_publish_threshold"


def safe_write_file(path: str, content: str) -> bool:
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


def ensure_init_file(dir_path: str) -> Optional[str]:
    try:
        os.makedirs(dir_path, exist_ok=True)
        init_path = os.path.join(dir_path, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w", encoding="utf-8") as f:
                f.write('"""Auto-created package marker."""\n')
            return init_path
        return None
    except Exception:
        return None


def run_leader_phase(task: Dict[str, Any], leader: str) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    return {
        "ok": True,
        "leader": leader,
        "plan": {
            "problem": payload.get("problem", ""),
            "paths": payload.get("paths", []),
            "path": payload.get("path", ""),
            "executor_hint": payload.get("executor_hint", ""),
        },
    }


def run_builder_phase(task: Dict[str, Any], builder: str, leader_result: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    problem = str(payload.get("problem", "")).strip().lower()
    changed_files: List[str] = []

    path = str(payload.get("path", "")).strip()
    paths = payload.get("paths", [])
    if not isinstance(paths, list):
        paths = []

    try:
        if problem in {"missing_init", "missing_init_group", "package_structure"}:
            for p in paths:
                p = str(p).strip()
                if not p:
                    continue
                created = ensure_init_file(p)
                if created:
                    changed_files.append(created)

            if path:
                parent = os.path.dirname(path) or "."
                created = ensure_init_file(parent)
                if created:
                    changed_files.append(created)

            if changed_files:
                return {
                    "ok": True,
                    "builder": builder,
                    "reason": "package_markers_created",
                    "changed_files": changed_files,
                }

            return {
                "ok": False,
                "builder": builder,
                "reason": "no_changes",
                "changed_files": [],
            }

        if problem in {"missing_root_readme", "missing_start_here"} and path:
            if not os.path.exists(path):
                ok = safe_write_file(path, f"# {os.path.basename(path)}\n\nAuto-created by GitCube builder.\n")
                if ok:
                    changed_files.append(path)

        elif path:
            if not os.path.exists(path):
                ok = safe_write_file(
                    path,
                    "# Auto-created by GitCube builder\n\n"
                    "def placeholder():\n"
                    "    return True\n",
                )
                if ok:
                    changed_files.append(path)

        if changed_files:
            return {
                "ok": True,
                "builder": builder,
                "reason": "files_written",
                "changed_files": changed_files,
            }

        return {
            "ok": False,
            "builder": builder,
            "reason": "no_changes",
            "changed_files": [],
        }
    except Exception as e:
        return {
            "ok": False,
            "builder": builder,
            "reason": f"builder_exception:{e}",
            "changed_files": [],
        }


def run_stabilizer_phase(task: Dict[str, Any], stabilizer: str, builder_result: Dict[str, Any]) -> Dict[str, Any]:
    if not builder_result.get("ok"):
        return {
            "ok": False,
            "stabilizer": stabilizer,
            "reason": "builder_failed",
        }

    changed_files = builder_result.get("changed_files", [])
    if not isinstance(changed_files, list):
        changed_files = []

    all_exist = all(os.path.exists(str(p)) for p in changed_files)

    if not all_exist:
        return {
            "ok": False,
            "stabilizer": stabilizer,
            "reason": "validation_failed",
        }

    return {
        "ok": True,
        "stabilizer": stabilizer,
        "reason": "validated",
    }


def run_guard_phase(
    task: Dict[str, Any],
    guard: str,
    leader: str,
    builder: str,
    scores: Dict[str, float],
) -> Dict[str, Any]:
    primary_agent = builder
    support_agent = leader

    tank_policy = evaluate_tank_policy(
        task,
        primary_agent,
        support_agent,
        scores,
    )

    return {
        "ok": True,
        "guard": guard,
        "tank_policy": tank_policy,
    }


def execute_party(task: Dict[str, Any], report_path: str) -> Dict[str, Any]:
    party = select_party(task)

    leader = party["leader"]
    builder = party["builder"]
    stabilizer = party["stabilizer"]
    guard = party["guard"]
    cleanup = party.get("cleanup")
    reason = party["reason"]
    scores = party["scores"]
    party_scores = party["party_scores"]

    print("PARTY_MODE: True")
    print("LEADER:", leader)
    print("BUILDER:", builder)
    print("STABILIZER:", stabilizer)
    print("GUARD:", guard)
    if cleanup:
        print("CLEANUP:", cleanup)
    print("PARTY_REASON:", reason)
    print("PARTY_SCORES:", party_scores)
    print("SCORES:", scores)

    leader_result = run_leader_phase(task, leader)
    builder_result = run_builder_phase(task, builder, leader_result)
    print("BUILDER_RESULT:", builder_result)
    stabilizer_result = run_stabilizer_phase(task, stabilizer, builder_result)
    print("STABILIZER_RESULT:", stabilizer_result)

    guard_result = run_guard_phase(
        task,
        guard,
        leader,
        builder,
        scores,
    )

    tank_policy = guard_result.get("tank_policy", {}) if isinstance(guard_result.get("tank_policy"), dict) else {}
    allow_publish, publish_reason = should_publish_to_github(task, tank_policy)

    task_id = str(task.get("id"))
    changed_files = builder_result.get("changed_files", [])
    tagged_reason = (
        f"leader={leader};builder={builder};stabilizer={stabilizer};guard={guard};"
        f"party_reason={reason};changed_files={changed_files}"
    )

    primary_attempt_ok = bool(builder_result.get("ok")) and bool(stabilizer_result.get("ok"))
    primary_reason = str(builder_result.get("reason", "")) if not primary_attempt_ok else "party_ok"

    print("PRIMARY_ATTEMPT:", primary_attempt_ok, primary_reason)
    print("PUBLISH:", allow_publish, publish_reason)

    if primary_attempt_ok and not allow_publish:
        mark_task_done(task_id, report_path, tagged_reason + ";party_done")
        print("=== DONE ===")
        return {
            "mode": "party",
            "ok": True,
            "published": False,
            "reason": "party_done_local",
        }

    if not allow_publish:
        if primary_reason in {"no_changes", "builder_failed", "validation_failed"} or primary_reason.startswith("builder_exception:"):
            mark_task_skipped(task_id, report_path, tagged_reason + f";{primary_reason}")
        else:
            mark_task_failed(task_id, report_path, tagged_reason + f";{primary_reason}")
        print("=== DONE ===")
        return {
            "mode": "party",
            "ok": False,
            "published": False,
            "reason": primary_reason,
        }

    if find_duplicate_task(task):
        print("DUPLICATE -> SKIP")
        mark_task_skipped(task_id, report_path, tagged_reason + ";duplicate")
        print("=== DONE ===")
        return {
            "mode": "party",
            "ok": False,
            "published": False,
            "reason": "duplicate",
        }

    issue = build_issue_from_task(task, "PARTY_EXECUTION", report_path)
    issue["body"] += (
        f"\n\nLeader: {leader}"
        f"\nBuilder: {builder}"
        f"\nStabilizer: {stabilizer}"
        f"\nGuard: {guard}"
        f"\nParty reason: {reason}"
        f"\nScores: {scores}"
        f"\nParty scores: {party_scores}"
        f"\nPrimary attempt: {primary_attempt_ok}"
        f"\nBuilder result: {builder_result}"
        f"\nStabilizer result: {stabilizer_result}"
    )
    if tank_policy:
        issue["body"] += f"\n\nTank policy: {tank_policy}"

    result = create_issue(issue["title"], issue["body"])

    if result.get("ok"):
        mark_task_published(
            task_id,
            result.get("url", ""),
            report_path,
            tagged_reason + f";publish={publish_reason};party_ok",
        )
        print("ISSUE:", result.get("url", ""))
    else:
        mark_task_failed(
            task_id,
            report_path,
            tagged_reason + ";issue_fail",
        )
        print("ERROR:", result.get("error", "unknown"))

    print("=== DONE ===")
    return {
        "mode": "party",
        "ok": bool(result.get("ok")),
        "published": bool(result.get("ok")),
        "reason": publish_reason,
    }


def execute_pair(task: Dict[str, Any], report_path: str) -> Dict[str, Any]:
    primary_agent, support_agent, scores, reason = select_pair(task)

    print("PARTY_MODE: False")
    print("PRIMARY_AGENT:", primary_agent)
    print("SUPPORT_AGENT:", support_agent)
    print("PAIR_REASON:", reason)
    print("PAIR_SCORES:", scores)

    tank_policy = evaluate_tank_policy(task, primary_agent, support_agent, scores)
    print("TANK_POLICY:", tank_policy)

    allow_publish, publish_reason = should_publish_to_github(task, tank_policy)
    task_id = str(task.get("id"))
    tagged_reason = f"primary={primary_agent};support={support_agent};pair_reason={reason}"

    primary_attempt_ok = False
    primary_reason = "no_changes"

    print("PRIMARY_ATTEMPT:", primary_attempt_ok, primary_reason)
    print("PUBLISH:", allow_publish, publish_reason)

    if not allow_publish:
        mark_task_skipped(task_id, report_path, tagged_reason + f";{primary_reason}")
        print("=== DONE ===")
        return {
            "mode": "pair",
            "ok": False,
            "published": False,
            "reason": primary_reason,
        }

    if find_duplicate_task(task):
        print("DUPLICATE -> SKIP")
        mark_task_skipped(task_id, report_path, tagged_reason + ";duplicate")
        print("=== DONE ===")
        return {
            "mode": "pair",
            "ok": False,
            "published": False,
            "reason": "duplicate",
        }

    issue = build_issue_from_task(task, "PAIR_EXECUTION", report_path)
    issue["body"] += (
        f"\n\nPrimary agent: {primary_agent}"
        f"\nSupport agent: {support_agent}"
        f"\nPair reason: {reason}"
        f"\nScores: {scores}"
    )
    if tank_policy:
        issue["body"] += f"\n\nTank policy: {tank_policy}"

    result = create_issue(issue["title"], issue["body"])

    if result.get("ok"):
        mark_task_published(
            task_id,
            result.get("url", ""),
            report_path,
            tagged_reason + f";publish={publish_reason}",
        )
        print("ISSUE:", result.get("url", ""))
    else:
        mark_task_failed(
            task_id,
            report_path,
            tagged_reason + ";issue_fail",
        )
        print("ERROR:", result.get("error", "unknown"))

    print("=== DONE ===")
    return {
        "mode": "pair",
        "ok": bool(result.get("ok")),
        "published": bool(result.get("ok")),
        "reason": publish_reason,
    }


def main():
    task = get_latest_open_task()
    if not task:
        print("NO_OPEN_TASK")
        print("=== DONE ===")
        return

    print("ACTION:", task.get("title", "UNKNOWN"))
    print("TARGET PATH:", task.get("payload", {}).get("path") if isinstance(task.get("payload"), dict) else None)

    report_path = f"reports/{str(task.get('id', 'task_unknown'))}.md"

    if should_use_party(task):
        execute_party(task, report_path)
    else:
        execute_pair(task, report_path)


if __name__ == "__main__":
    main()
