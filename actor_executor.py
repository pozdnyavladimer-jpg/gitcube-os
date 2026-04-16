from __future__ import annotations

from typing import Dict, Any

from runtime_experimental.mage_executor import run_mage
from runtime_experimental.healer_executor import run_healer
from runtime_experimental.tank_executor import run_tank

from runtime_experimental.object_store import (
    mark_task_done,
    mark_task_failed,
    mark_task_skipped,
    mark_task_published,
)
from runtime_experimental.github_bridge import create_issue, is_github_enabled
from runtime_experimental.tank_policy import evaluate_tank_policy
from router import select_pair


def build_issue_from_task(task: Dict[str, Any], action: str, report_path: str) -> Dict[str, str]:
    title = str(task.get("title", "Untitled task"))
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
    return {"title": title, "body": "\n".join(body)}


def find_duplicate_task(task: Dict[str, Any]) -> bool:
    return False


def should_publish_to_github(task: Dict[str, Any], tank_policy: Dict[str, Any]) -> tuple[bool, str]:
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
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


def execute_party(task: Dict[str, Any], report_path: str) -> Dict[str, Any]:
    print("PARTY_MODE: True")

    leader = run_tank(task)
    print("LEADER:", leader.get("role"))

    mage = run_mage(task)
    print("BUILDER:", mage.get("role"))

    healer = run_healer(task, mage.get("result") if isinstance(mage.get("result"), dict) else mage)
    print("STABILIZER:", healer.get("role"))

    guard = "TANK"
    print("GUARD:", guard)

    tank_policy = evaluate_tank_policy(task, leader, mage)
    print("TANK_POLICY:", tank_policy)

    task_id = str(task.get("id", "task_unknown"))
    tagged_reason = (
        f"leader={leader.get('role')};"
        f"builder={mage.get('role')};"
        f"stabilizer={healer.get('role')};"
        f"guard={guard}"
    )

    allow_publish, publish_reason = should_publish_to_github(task, tank_policy)

    if not mage.get("ok", False):
        mark_task_failed(task_id, report_path, tagged_reason + ";mage_failed")
        print("=== DONE ===")
        return {
            "mode": "party",
            "ok": False,
            "published": False,
            "reason": "mage_failed",
            "leader": leader,
            "mage": mage,
            "healer": healer,
        }

    if find_duplicate_task(task):
        mark_task_skipped(task_id, report_path, tagged_reason + ";duplicate")
        print("=== DONE ===")
        return {
            "mode": "party",
            "ok": False,
            "published": False,
            "reason": "duplicate",
            "leader": leader,
            "mage": mage,
            "healer": healer,
        }

    if not allow_publish:
        mark_task_done(task_id, report_path, tagged_reason + f";local_only;publish={publish_reason}")
        print("=== DONE ===")
        return {
            "mode": "party",
            "ok": True,
            "published": False,
            "reason": "party_done_local",
            "leader": leader,
            "mage": mage,
            "healer": healer,
        }

    issue = build_issue_from_task(task, "PARTY_EXECUTION", report_path)
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
        "leader": leader,
        "mage": mage,
        "healer": healer,
    }


def execute_pair(task: Dict[str, Any], report_path: str) -> Dict[str, Any]:
    primary_agent, support_agent, scores, pair_reason = select_pair(task)

    print("PARTY_MODE: False")
    print("PRIMARY_AGENT:", primary_agent)
    print("SUPPORT_AGENT:", support_agent)
    print("PAIR_REASON:", pair_reason)
    print("PAIR_SCORES:", scores)

    task_id = str(task.get("id", "task_unknown"))
    tagged_reason = f"primary={primary_agent};support={support_agent};pair_reason={pair_reason}"

    if primary_agent == "MAGE":
        primary_result = run_mage(task)
    elif primary_agent == "HEALER":
        primary_result = run_healer(task)
    else:
        primary_result = run_tank(task)

    healer_result = run_healer(task, primary_result.get("result") if isinstance(primary_result.get("result"), dict) else primary_result)

    tank_policy = evaluate_tank_policy(task, primary_result, healer_result)
    print("TANK_POLICY:", tank_policy)

    allow_publish, publish_reason = should_publish_to_github(task, tank_policy)

    if not primary_result.get("ok", False):
        mark_task_skipped(task_id, report_path, tagged_reason + ";primary_failed")
        print("=== DONE ===")
        return {
            "mode": "pair",
            "ok": False,
            "published": False,
            "reason": "primary_failed",
            "primary": primary_result,
            "healer": healer_result,
        }

    if find_duplicate_task(task):
        mark_task_skipped(task_id, report_path, tagged_reason + ";duplicate")
        print("=== DONE ===")
        return {
            "mode": "pair",
            "ok": False,
            "published": False,
            "reason": "duplicate",
            "primary": primary_result,
            "healer": healer_result,
        }

    if not allow_publish:
        mark_task_done(task_id, report_path, tagged_reason + f";local_only;publish={publish_reason}")
        print("=== DONE ===")
        return {
            "mode": "pair",
            "ok": True,
            "published": False,
            "reason": "pair_done_local",
            "primary": primary_result,
            "healer": healer_result,
        }

    issue = build_issue_from_task(task, "PAIR_EXECUTION", report_path)
    result = create_issue(issue["title"], issue["body"])

    if result.get("ok"):
        mark_task_published(
            task_id,
            result.get("url", ""),
            report_path,
            tagged_reason + f";publish={publish_reason};pair_ok",
        )
        print("ISSUE:", result.get("url", ""))
    else:
        mark_task_failed(task_id, report_path, tagged_reason + ";issue_fail")
        print("ERROR:", result.get("error", "unknown"))

    print("=== DONE ===")
    return {
        "mode": "pair",
        "ok": bool(result.get("ok")),
        "published": bool(result.get("ok")),
        "reason": publish_reason,
        "primary": primary_result,
        "healer": healer_result,
    }
