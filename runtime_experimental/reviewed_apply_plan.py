from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_D64_REQUEST = "reports/d64_safe_mutation_gate_request.json"
DEFAULT_D71_DRY_RUN = "reports/d71_route_dry_run_simulation.json"
DEFAULT_D66_REVIEW = "reports/d66_core_guard_reviewer_report.json"
DEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"
DEFAULT_OUTPUT = "reports/d72_reviewed_apply_plan.json"

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
    return "/".join(part for part in raw.split("/") if part and part not in (".", ".."))

def _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:
    for key in ("protected_files", "immutable_core", "core_files"):
        value = policy.get(key)
        if isinstance(value, list):
            return [str(v) for v in value]
    return []

def _sha256_json(data: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

def _validate_route_diff(route_diff: List[Dict[str, Any]], errors: List[str]) -> None:
    if not route_diff:
        errors.append("D71 simulated_route_diff is empty")
        return
    for idx, item in enumerate(route_diff):
        if not isinstance(item, dict):
            errors.append(f"D71 route diff item {idx} is not a dict")
            continue
        if item.get("dry_run_only") is not True:
            errors.append(f"D71 route diff item {idx} is not dry_run_only")
        if item.get("would_touch_protected_core") is not False:
            errors.append(f"D71 route diff item {idx} would touch protected core")
        if item.get("would_touch_canonical_memory") is not False:
            errors.append(f"D71 route diff item {idx} would touch canonical memory")
        if item.get("would_execute_runtime_mutation") is not False:
            errors.append(f"D71 route diff item {idx} would execute runtime mutation")
        handler = _safe_relative_path(str(item.get("sandbox_handler", "")))
        if not handler.startswith("runtime_experimental/ai_bypass_proposals/"):
            errors.append(f"D71 route diff item {idx} has non-sandbox handler: {handler}")

def build_reviewed_apply_plan(
    root: str | Path = ".",
    d64_request_path: str = DEFAULT_D64_REQUEST,
    d71_dry_run_path: str = DEFAULT_D71_DRY_RUN,
    d66_review_path: str = DEFAULT_D66_REVIEW,
    core_policy_path: str = DEFAULT_CORE_POLICY,
    output_path: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()
    d64 = _read_json(root_path / d64_request_path, default={}) or {}
    d71 = _read_json(root_path / d71_dry_run_path, default={}) or {}
    d66 = _read_json(root_path / d66_review_path, default={}) or {}
    policy = _read_json(root_path / core_policy_path, default={}) or {}

    errors: List[str] = []
    warnings: List[str] = []
    if not d64:
        errors.append("D64 safe mutation gate request missing or unreadable")
    if not d71:
        errors.append("D71 route dry-run simulation missing or unreadable")
    if not d66:
        warnings.append("D66 core guard reviewer report missing or unreadable")
    if not policy:
        warnings.append("core guard policy missing or unreadable")

    if d64:
        if d64.get("ok") is not True:
            errors.append("D64 ok flag is not true")
        if d64.get("decision") != "CREATE_GUARDED_APPLY_REQUEST":
            errors.append(f"D64 decision is not CREATE_GUARDED_APPLY_REQUEST: {d64.get('decision')}")
        d64_guardrails = d64.get("guardrails") if isinstance(d64.get("guardrails"), dict) else {}
        if d64_guardrails.get("actual_apply_executed") is not False:
            errors.append("D64 actual_apply_executed is not false")
        if d64_guardrails.get("gate_only") is not True:
            errors.append("D64 gate_only is not true")

    if d71:
        if d71.get("ok") is not True:
            errors.append("D71 ok flag is not true")
        if d71.get("decision") != "ROUTE_DRY_RUN_APPROVED":
            errors.append(f"D71 decision is not ROUTE_DRY_RUN_APPROVED: {d71.get('decision')}")
        d71_guardrails = d71.get("guardrails") if isinstance(d71.get("guardrails"), dict) else {}
        if d71_guardrails.get("actual_apply_executed") is not False:
            errors.append("D71 actual_apply_executed is not false")
        if d71_guardrails.get("dry_run_only") is not True:
            errors.append("D71 dry_run_only is not true")

    d64_request = d64.get("guarded_apply_request") if isinstance(d64.get("guarded_apply_request"), dict) else {}
    if d64_request and d64_request.get("enabled") is not True:
        errors.append("D64 guarded apply request is not enabled")

    route_diff = d71.get("simulated_route_diff") if isinstance(d71.get("simulated_route_diff"), list) else []
    _validate_route_diff(route_diff, errors)

    sandbox_candidates_raw = d64_request.get("sandbox_candidates", [])
    sandbox_candidates = [_safe_relative_path(str(x)) for x in sandbox_candidates_raw if x] if isinstance(sandbox_candidates_raw, list) else []
    if not sandbox_candidates:
        errors.append("D64 sandbox candidates missing")

    protected_files = _protected_files_from_policy(policy)
    target_scope = d71.get("target_scope") if isinstance(d71.get("target_scope"), list) else []

    plan_id = "d72-" + _sha256_json({
        "sandbox_candidates": sandbox_candidates,
        "route_diff_count": len(route_diff),
        "target_scope": target_scope,
    })[:16]

    approved = len(errors) == 0
    decision = "REVIEWED_APPLY_PLAN_READY" if approved else "REVIEWED_APPLY_PLAN_BLOCKED"
    result = "D72_REVIEWED_APPLY_PLAN_CREATED" if approved else "D72_REVIEWED_APPLY_PLAN_BLOCKED"

    reviewed_apply_plan = {
        "plan_id": plan_id,
        "enabled": approved,
        "apply_mode": "MANUAL_GUARDED_APPLY_ONLY",
        "status": decision,
        "sandbox_candidates": sandbox_candidates,
        "simulated_route_diff": route_diff,
        "target_scope": target_scope,
        "rollback_plan": {
            "required": True,
            "mode": "PRE_APPLY_BACKUP_AND_REVERT",
            "backup_targets": protected_files,
            "rollback_artifacts_required": [
                "pre_apply_git_sha",
                "protected_file_backup_manifest",
                "post_apply_validation_report",
            ],
            "rollback_command_policy": "git_restore_or_revert_only_after_human_review",
        },
        "required_gates_before_real_apply": [
            "D66_REVIEWER_RECHECK",
            "D71_DRY_RUN_APPROVED",
            "UNIT_TESTS",
            "REGRESSION_TESTS",
            "ROLLBACK_PLAN_READY",
            "HUMAN_OR_HIGHER_POLICY_APPROVAL",
        ],
        "forbidden_actions": [
            "direct_core_edit_without_guarded_route",
            "overwrite_canonical_memory",
            "auto_commit_runtime_mutation",
            "apply_without_rollback",
            "apply_without_D66_recheck",
        ],
        "next_allowed_actions": [
            "generate pre-apply backup manifest",
            "run D66 reviewer recheck on this plan",
            "run full unit/regression suite",
            "prepare D73 guarded apply dry-run package",
        ],
    }

    report = {
        "state": "D72_REVIEWED_APPLY_PLAN",
        "result": result,
        "route": "FIELD_INTENT_REVIEWED_APPLY_PLAN",
        "ok": approved,
        "decision": decision,
        "created_at": _now(),
        "plan_id": plan_id,
        "reviewed_apply_plan": reviewed_apply_plan,
        "input_reports": {
            "d64_request_path": str(root_path / d64_request_path),
            "d71_dry_run_path": str(root_path / d71_dry_run_path),
            "d66_review_path": str(root_path / d66_review_path),
            "core_policy_path": str(root_path / core_policy_path),
        },
        "evidence": {
            "d64_decision": d64.get("decision"),
            "d64_ok": d64.get("ok"),
            "d71_decision": d71.get("decision"),
            "d71_ok": d71.get("ok"),
            "d66_decision": d66.get("decision"),
            "route_diff_count": len(route_diff),
            "sandbox_candidates_count": len(sandbox_candidates),
        },
        "guardrails": {
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "plan_only": True,
        },
        "validation": {"ok": approved, "errors": errors, "warnings": warnings},
        "summary": {
            "decision": decision,
            "plan_id": plan_id,
            "sandbox_candidates_count": len(sandbox_candidates),
            "route_diff_count": len(route_diff),
            "protected_files_count": len(protected_files),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "reviewed_apply_plan_created": approved,
            "actual_apply_executed": False,
            "rollback_required": True,
            "next_step": "D73 can prepare a guarded apply dry-run package, but no real mutation should run without D66 recheck and rollback evidence.",
        },
    }
    _write_json(root_path / output_path, report)
    return report

if __name__ == "__main__":
    print(json.dumps(build_reviewed_apply_plan(), ensure_ascii=False, indent=2))
