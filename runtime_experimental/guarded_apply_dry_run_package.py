from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_D72_PLAN = "reports/d72_reviewed_apply_plan.json"
DEFAULT_D71_DRY_RUN = "reports/d71_route_dry_run_simulation.json"
DEFAULT_D64_REQUEST = "reports/d64_safe_mutation_gate_request.json"
DEFAULT_D66_REVIEW = "reports/d66_core_guard_reviewer_report.json"
DEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"
DEFAULT_OUTPUT = "reports/d73_guarded_apply_dry_run_package.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_relative_path(path_value: str) -> str:
    raw = str(path_value or "").strip().replace("\\", "/").lstrip("/")
    parts: List[str] = []
    for part in raw.split("/"):
        if not part or part == "." or part == "..":
            continue
        parts.append(part)
    return "/".join(parts)


def _sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha(root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except Exception:
        pass
    return "UNKNOWN"


def _git_status_porcelain(root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except Exception:
        pass
    return "UNKNOWN"


def _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:
    for key in ("protected_files", "immutable_core", "core_files"):
        value = policy.get(key)
        if isinstance(value, list):
            return [str(v) for v in value]
    return []


def _backup_manifest(root: Path, protected_files: List[str]) -> List[Dict[str, Any]]:
    manifest: List[Dict[str, Any]] = []
    for raw in protected_files:
        rel = _safe_relative_path(raw)
        path = root / rel
        manifest.append(
            {
                "path": rel,
                "exists": path.exists(),
                "is_file": path.is_file(),
                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
                "sha256": _sha256_file(path),
                "backup_required_before_apply": True,
                "restore_policy": "git restore -- " + rel,
            }
        )
    return manifest


def _validate_d72(d72: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
    plan = d72.get("reviewed_apply_plan") if isinstance(d72.get("reviewed_apply_plan"), dict) else {}

    if not d72:
        errors.append("D72 reviewed apply plan missing or unreadable")
        return {}

    if d72.get("ok") is not True:
        errors.append("D72 ok flag is not true")

    if d72.get("decision") != "REVIEWED_APPLY_PLAN_READY":
        errors.append(f"D72 decision is not REVIEWED_APPLY_PLAN_READY: {d72.get('decision')}")

    guardrails = d72.get("guardrails") if isinstance(d72.get("guardrails"), dict) else {}
    if guardrails.get("actual_apply_executed") is not False:
        errors.append("D72 actual_apply_executed is not false")
    if guardrails.get("plan_only") is not True:
        errors.append("D72 plan_only is not true")

    if plan.get("enabled") is not True:
        errors.append("D72 reviewed apply plan is not enabled")

    rollback = plan.get("rollback_plan") if isinstance(plan.get("rollback_plan"), dict) else {}
    if rollback.get("required") is not True:
        errors.append("D72 rollback plan is not required=true")

    return plan


def build_guarded_apply_dry_run_package(
    root: str | Path = ".",
    d72_plan_path: str = DEFAULT_D72_PLAN,
    d71_dry_run_path: str = DEFAULT_D71_DRY_RUN,
    d64_request_path: str = DEFAULT_D64_REQUEST,
    d66_review_path: str = DEFAULT_D66_REVIEW,
    core_policy_path: str = DEFAULT_CORE_POLICY,
    output_path: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()

    d72 = _read_json(root_path / d72_plan_path, default={}) or {}
    d71 = _read_json(root_path / d71_dry_run_path, default={}) or {}
    d64 = _read_json(root_path / d64_request_path, default={}) or {}
    d66 = _read_json(root_path / d66_review_path, default={}) or {}
    policy = _read_json(root_path / core_policy_path, default={}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    plan = _validate_d72(d72, errors)

    if not d71:
        warnings.append("D71 dry-run report missing or unreadable")
    elif d71.get("decision") != "ROUTE_DRY_RUN_APPROVED":
        errors.append(f"D71 decision is not ROUTE_DRY_RUN_APPROVED: {d71.get('decision')}")

    if not d64:
        warnings.append("D64 gate request missing or unreadable")
    elif d64.get("decision") != "CREATE_GUARDED_APPLY_REQUEST":
        errors.append(f"D64 decision is not CREATE_GUARDED_APPLY_REQUEST: {d64.get('decision')}")

    if not d66:
        warnings.append("D66 reviewer report missing or unreadable; D73 will still require recheck before apply")

    if not policy:
        warnings.append("core guard policy missing or unreadable")

    protected_files = _protected_files_from_policy(policy)
    if not protected_files:
        rollback = plan.get("rollback_plan") if isinstance(plan.get("rollback_plan"), dict) else {}
        backup_targets = rollback.get("backup_targets")
        if isinstance(backup_targets, list):
            protected_files = [str(x) for x in backup_targets if x]

    sandbox_candidates_raw = plan.get("sandbox_candidates", [])
    sandbox_candidates = [_safe_relative_path(str(x)) for x in sandbox_candidates_raw if x] if isinstance(sandbox_candidates_raw, list) else []

    route_diff = plan.get("simulated_route_diff", [])
    if not isinstance(route_diff, list):
        route_diff = []
        errors.append("D72 simulated_route_diff is not a list")

    if not sandbox_candidates:
        errors.append("D73 has no sandbox candidates from D72")

    if not route_diff:
        errors.append("D73 has no route diff from D72")

    backup_manifest = _backup_manifest(root_path, protected_files)
    pre_apply_sha = _git_sha(root_path)
    status_before = _git_status_porcelain(root_path)

    package_ready = len(errors) == 0
    decision = "GUARDED_APPLY_DRY_RUN_PACKAGE_READY" if package_ready else "GUARDED_APPLY_DRY_RUN_PACKAGE_BLOCKED"
    result = "D73_GUARDED_APPLY_DRY_RUN_PACKAGE_CREATED" if package_ready else "D73_GUARDED_APPLY_DRY_RUN_PACKAGE_BLOCKED"

    dry_run_package = {
        "package_state": "D73_GUARDED_APPLY_DRY_RUN_PACKAGE",
        "enabled": package_ready,
        "mode": "DRY_RUN_PACKAGE_ONLY",
        "pre_apply_git_sha": pre_apply_sha,
        "git_status_before_package": status_before,
        "source_plan_id": d72.get("plan_id"),
        "sandbox_candidates": sandbox_candidates,
        "simulated_route_diff": route_diff,
        "backup_manifest": backup_manifest,
        "rollback_instructions": {
            "rollback_required": True,
            "restore_protected_files": ["git restore -- " + item["path"] for item in backup_manifest],
            "revert_commit_policy": "only_after_human_or_higher_policy_review",
            "must_preserve_reports": True,
        },
        "required_validation_commands": [
            "python -m py_compile runtime_experimental/reviewed_apply_plan.py",
            "python -m py_compile runtime_experimental/route_dry_run_simulator.py",
            "python -m unittest tests.test_d64_safe_mutation_gate -v",
            "python -m unittest tests.test_d70_sandbox_bundle_reviewer -v",
            "python -m unittest tests.test_d71_route_dry_run_simulator -v",
            "python -m unittest tests.test_d72_reviewed_apply_plan -v",
            "python -m unittest tests.test_d73_guarded_apply_dry_run_package -v",
        ],
        "required_gates_before_real_apply": [
            "D66_REVIEWER_RECHECK",
            "D71_ROUTE_DRY_RUN_APPROVED",
            "D72_REVIEWED_APPLY_PLAN_READY",
            "ROLLBACK_MANIFEST_READY",
            "FULL_TEST_SUITE_OK",
            "HUMAN_OR_HIGHER_POLICY_APPROVAL",
        ],
        "forbidden_actions": [
            "direct_core_edit",
            "overwrite_canonical_memory",
            "auto_commit_runtime_mutation",
            "apply_without_backup_manifest",
            "apply_without_D66_recheck",
            "apply_without_explicit_approval",
        ],
    }

    report = {
        "state": "D73_GUARDED_APPLY_DRY_RUN_PACKAGE",
        "result": result,
        "route": "FIELD_INTENT_GUARDED_APPLY_DRY_RUN_PACKAGE",
        "ok": package_ready,
        "decision": decision,
        "created_at": _now(),
        "dry_run_package": dry_run_package,
        "input_reports": {
            "d72_plan_path": str(root_path / d72_plan_path),
            "d71_dry_run_path": str(root_path / d71_dry_run_path),
            "d64_request_path": str(root_path / d64_request_path),
            "d66_review_path": str(root_path / d66_review_path),
            "core_policy_path": str(root_path / core_policy_path),
        },
        "evidence": {
            "d72_decision": d72.get("decision"),
            "d72_ok": d72.get("ok"),
            "d71_decision": d71.get("decision"),
            "d64_decision": d64.get("decision"),
            "d66_decision": d66.get("decision"),
            "pre_apply_git_sha": pre_apply_sha,
            "backup_manifest_count": len(backup_manifest),
            "sandbox_candidates_count": len(sandbox_candidates),
            "route_diff_count": len(route_diff),
        },
        "guardrails": {
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "package_only": True,
        },
        "validation": {
            "ok": package_ready,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "sandbox_candidates_count": len(sandbox_candidates),
            "route_diff_count": len(route_diff),
            "backup_manifest_count": len(backup_manifest),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "dry_run_package_created": package_ready,
            "actual_apply_executed": False,
            "backup_manifest_ready": len(backup_manifest) > 0,
            "next_step": "D74 should analyze differentiation / module extraction pressure. Real apply remains blocked until D66 recheck and explicit approval.",
        },
    }

    _write_json(root_path / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(build_guarded_apply_dry_run_package(), ensure_ascii=False, indent=2))
