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
from app.orchestration.task_dispatcher import dispatch_task


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


def safe_append_file(path: str, content: str) -> bool:
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


def ensure_init_file_from_file_path(file_path: str) -> Optional[str]:
    try:
        parent = os.path.dirname(file_path) or "."
        os.makedirs(parent, exist_ok=True)
        if os.path.basename(file_path) == "__init__.py":
            init_path = file_path
        else:
            init_path = os.path.join(parent, "__init__.py")

        if not os.path.exists(init_path):
            with open(init_path, "w", encoding="utf-8") as f:
                f.write('"""Auto-created package marker."""\n')
            return init_path

        return None
    except Exception:
        return None


def normalize_paths(raw_paths: Any) -> List[str]:
    if not isinstance(raw_paths, list):
        return []
    out = []
    for p in raw_paths:
        s = str(p).strip()
        if s:
            out.append(s)
    return out


def infer_target_paths(problem: str, path: str, paths: List[str]) -> tuple[Optional[str], List[str], str]:
    problem = str(problem or "").strip().lower()
    path = str(path or "").strip()
    paths = normalize_paths(paths)

    if path:
        return path, [], "existing_payload_path"

    if problem in {"missing_init", "missing_init_group", "package_structure"}:
        resolved_paths = []
        for p in paths:
            p = p.rstrip("/")
            if not p:
                continue

            if p.endswith(".py"):
                parent = os.path.dirname(p) or "."
                resolved_paths.append(os.path.join(parent, "__init__.py"))
            else:
                resolved_paths.append(os.path.join(p, "__init__.py"))

        if resolved_paths:
            return None, resolved_paths, "mage_resolved_package_markers"

        return None, [], "mage_no_package_target"

    if problem == "missing_root_readme":
        return "README.md", [], "mage_resolved_root_readme"

    if problem == "missing_start_here":
        return "START_HERE.md", [], "mage_resolved_start_here"

    if problem == "python_without_docs":
        if os.path.isdir("docs"):
            return "docs/README.md", [], "mage_resolved_docs_readme"
        return "README.md", [], "mage_resolved_fallback_readme"

    if problem == "missing_init":
        if paths:
            p = paths[0]
            if p.endswith(".py"):
                parent = os.path.dirname(p) or "."
                return os.path.join(parent, "__init__.py"), [], "mage_resolved_missing_init"
            return os.path.join(p, "__init__.py"), [], "mage_resolved_missing_init"

    if paths:
        first = str(paths[0]).strip().rstrip("/")
        if first.endswith(".py"):
            return first, [], "mage_resolved_first_path"

        if problem in {"missing_init_group", "missing_init", "package_structure", "empty_directories_group"}:
            return os.path.join(first, "__init__.py"), [], "mage_resolved_structural_dir"

        if problem in {"structural_orphans_group", "broken_import_group"}:
            py_candidate = os.path.join(first, "__init__.py")
            return py_candidate, [], "mage_resolved_topology_target"

        return os.path.join(first, "__init__.py"), [], "mage_resolved_first_dir"

    structural_dirs = [
        "runtime_experimental",
        "app",
        "core",
        "docs",
        "examples",
        "tests",
        "environments",
    ]

    for d in structural_dirs:
        if os.path.isdir(d):
            return os.path.join(d, "__init__.py"), [], "mage_structural_default_dir"

    if os.path.exists("README.md"):
        return "README.md", [], "mage_fallback_existing_readme"

    return "README.md", [], "mage_fallback_create_readme"


def build_runtime_note(task: Dict[str, Any]) -> str:
    title = str(task.get("title", "Untitled task")).strip()
    task_id = str(task.get("id", "task_unknown")).strip()
    return (
        "\n\n---\n"
        f"Auto-updated by GitCube builder.\n"
        f"- task_id: {task_id}\n"
        f"- title: {title}\n"
        "---\n"
    )


def run_leader_phase(task: Dict[str, Any], leader: str) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    problem = str(payload.get("problem", "")).strip().lower()
    raw_path = str(payload.get("path", "")).strip()
    raw_paths = payload.get("paths", [])

    resolved_path, resolved_paths, resolution_note = infer_target_paths(
        problem=problem,
        path=raw_path,
        paths=raw_paths,
    )

    result = {
        "ok": True,
        "leader": leader,
        "plan": {
            "problem": problem,
            "path": raw_path,
            "paths": normalize_paths(raw_paths),
            "executor_hint": payload.get("executor_hint", ""),
        },
        "resolved_path": resolved_path,
        "resolved_paths": resolved_paths,
        "resolution_note": resolution_note,
    }

    print("LEADER_RESULT:", result)
    print("RESOLVED_PATH:", resolved_path)
    print("RESOLVED_PATHS:", resolved_paths)

    return result


def run_builder_phase(task: Dict[str, Any], builder: str, leader_result: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    problem = str(payload.get("problem", "")).strip().lower()

    resolved_path = str(leader_result.get("resolved_path", "") or "").strip()
    resolved_paths = normalize_paths(leader_result.get("resolved_paths", []))
    changed_files: List[str] = []
    note = build_runtime_note(task)

    try:
        if problem in {"missing_init", "missing_init_group", "package_structure"}:
            all_targets = []
            if resolved_path:
                all_targets.append(resolved_path)
            all_targets.extend(resolved_paths)

            seen = set()
            unique_targets = []
            for t in all_targets:
                if t not in seen:
                    seen.add(t)
                    unique_targets.append(t)

            for target in unique_targets:
                created = ensure_init_file_from_file_path(target)
                if created:
                    changed_files.append(created)

            if changed_files:
                return {
                    "ok": True,
                    "builder": builder,
                    "reason": "package_markers_created",
                    "changed_files": changed_files,
                }

            if resolved_path or resolved_paths:
                return {
                    "ok": True,
                    "builder": builder,
                    "reason": "package_markers_already_exist",
                    "changed_files": [],
                }

            return {
                "ok": False,
                "builder": builder,
                "reason": "no_changes",
                "changed_files": [],
            }

        if problem in {"missing_root_readme", "missing_start_here", "python_without_docs"}:
            target = resolved_path
            if target:
                if not os.path.exists(target):
                    ok = safe_write_file(
                        target,
                        f"# {os.path.basename(target)}\n\nAuto-created by GitCube builder.\n",
                    )
                    if ok:
                        changed_files.append(target)
                else:
                    ok = safe_append_file(target, note)
                    if ok:
                        changed_files.append(target)

            if changed_files:
                return {
                    "ok": True,
                    "builder": builder,
                    "reason": "docs_written",
                    "changed_files": changed_files,
                }

            return {
                "ok": False,
                "builder": builder,
                "reason": "no_changes",
                "changed_files": [],
            }

        if resolved_path:
            if not os.path.exists(resolved_path):
                if os.path.basename(resolved_path) == "__init__.py":
                    ok = safe_write_file(
                        resolved_path,
                        '"""Auto-created package marker."""\n',
                    )
                else:
                    ok = safe_write_file(
                        resolved_path,
                        "# Auto-created by GitCube builder\n\n"
                        "def placeholder():\n"
                        "    return True\n",
                    )
                if ok:
                    changed_files.append(resolved_path)
            elif os.path.basename(resolved_path).lower() in {"readme.md", "start_here.md"}:
                ok = safe_append_file(resolved_path, note)
                if ok:
                    changed_files.append(resolved_path)

        if changed_files:
            return {
                "ok": True,
                "builder": builder,
                "reason": "files_written",
                "changed_files": changed_files,
            }

        if resolved_path or resolved_paths:
            return {
                "ok": True,
                "builder": builder,
                "reason": "target_already_exists",
                "changed_files": [],
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
    stabilizer: str,
    cleanup: Optional[str],
    scores: Dict[str, float],
) -> Dict[str, Any]:
    tank_policy = evaluate_tank_policy(
        task,
        scores=scores,
        leader=leader,
        builder=builder,
        stabilizer=stabilizer,
        guard=guard,
        cleanup=cleanup,
        mode="party",
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
        stabilizer,
        cleanup,
        scores,
    )

    tank_policy = guard_result.get("tank_policy", {}) if isinstance(guard_result.get("tank_policy"), dict) else {}
    print("TANK_POLICY:", tank_policy)

    allow_publish, publish_reason = should_publish_to_github(task, tank_policy)

    task_id = str(task.get("id"))
    changed_files = builder_result.get("changed_files", [])

    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    problem = str(payload.get("problem", "")).strip().lower()

    tagged_reason = (
        f"leader={leader};builder={builder};stabilizer={stabilizer};guard={guard};"
        f"party_reason={reason};leader_resolution={leader_result.get('resolution_note')};"
        f"resolved_path={leader_result.get('resolved_path')};"
        f"resolved_paths={leader_result.get('resolved_paths')};"
        f"changed_files={changed_files}"
    )

    if problem in {"missing_init_group", "broken_import_group"}:
        dispatch_result = dispatch_task({
            "problem": problem,
            "paths": payload.get("paths", []),
            "priority": payload.get("priority", "high"),
            "payload": payload,
        })
        print("DISPATCH_RESULT:", dispatch_result)

        mesh_ok = bool(dispatch_result.get("mesh", {}).get("ok", False))
        exec_ok = bool(dispatch_result.get("execution", {}).get("ok", False))
        valid_ok = bool(dispatch_result.get("validation", {}).get("ok", False))

        if mesh_ok and exec_ok and valid_ok:
            dispatch_changed = dispatch_result.get("execution", {}).get("changed_files", [])
            dispatch_route = str(dispatch_result.get("route", "")).strip().lower()
            tagged_reason += f";dispatch_changed_files={dispatch_changed};dispatch_mode={dispatch_route}"
            mark_task_done(task_id, report_path, tagged_reason + ";party_done_via_dispatch")
            print("=== DONE ===")
            return {
                "mode": "party",
                "ok": True,
                "published": False,
                "reason": "party_done_via_dispatch",
            }

        print("DISPATCH FAILED -> FALLBACK TO BUILDER")

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
        f"\nLeader result: {leader_result}"
        f"\nBuilder result: {builder_result}"
        f"\nStabilizer result: {stabilizer_result}"
        f"\nPrimary attempt: {primary_attempt_ok}"
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

    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    print("TARGET_PATH:", payload.get("path", ""))

    report_path = f"reports/{str(task.get('id', 'task_unknown'))}.md"

    if should_use_party(task):
        execute_party(task, report_path)
    else:
        execute_pair(task, report_path)


if __name__ == "__main__":
    main()
