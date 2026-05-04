from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_D70_REVIEW = "reports/d70_sandbox_bundle_review.json"
DEFAULT_D69_BUNDLE = "reports/d69_sandbox_patch_bundle.json"
DEFAULT_D69_REPORT = "reports/d69_sandbox_patch_write_report.json"
DEFAULT_D68_PROPOSAL = "reports/d68_ai_patch_proposal.json"
DEFAULT_D67_REPORT = "reports/d67_topological_memory_map_report.json"
DEFAULT_D63_REPORT = "reports/d63_field_memory_replay_report.json"
DEFAULT_D66_REPORT = "reports/d66_core_guard_reviewer_report.json"
DEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"
DEFAULT_OUTPUT = "reports/d64_safe_mutation_gate_request.json"

ALLOWED_SANDBOX_PREFIXES = (
    "runtime_experimental/ai_bypass_proposals/",
)


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
    raw = str(path_value or "").strip().replace("\\", "/")
    raw = raw.lstrip("/")
    parts: List[str] = []
    for part in raw.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            continue
        parts.append(part)
    return "/".join(parts)


def _is_allowed_sandbox_file(path_value: str) -> bool:
    rel = _safe_relative_path(path_value)
    return rel.endswith(".py") and any(rel.startswith(prefix) for prefix in ALLOWED_SANDBOX_PREFIXES)


def _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:
    for key in ("protected_files", "immutable_core", "core_files"):
        value = policy.get(key)
        if isinstance(value, list):
            return [str(v) for v in value]
    return []


def _guardrails_clean(source_name: str, guardrails: Dict[str, Any], errors: List[str]) -> None:
    required_false = [
        "runtime_code_mutated",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "external_ai_called",
    ]
    for key in required_false:
        if guardrails.get(key) is not False:
            errors.append(f"{source_name}.guardrail_not_false:{key}")

    if guardrails.get("sandbox_only") is not True:
        errors.append(f"{source_name}.guardrail_sandbox_only_not_true")


def _extract_macro_decision(d63: Dict[str, Any]) -> Dict[str, Any]:
    value = d63.get("macro_decision")
    return value if isinstance(value, dict) else {}


def build_safe_mutation_gate_request(
    root: str | Path = ".",
    d70_review_path: str = DEFAULT_D70_REVIEW,
    d69_bundle_path: str = DEFAULT_D69_BUNDLE,
    d69_report_path: str = DEFAULT_D69_REPORT,
    d68_proposal_path: str = DEFAULT_D68_PROPOSAL,
    d67_report_path: str = DEFAULT_D67_REPORT,
    d63_report_path: str = DEFAULT_D63_REPORT,
    d66_report_path: str = DEFAULT_D66_REPORT,
    core_policy_path: str = DEFAULT_CORE_POLICY,
    output_path: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()

    d70 = _read_json(root_path / d70_review_path, default={}) or {}
    d69_bundle = _read_json(root_path / d69_bundle_path, default={}) or {}
    d69_report = _read_json(root_path / d69_report_path, default={}) or {}
    d68 = _read_json(root_path / d68_proposal_path, default={}) or {}
    d67 = _read_json(root_path / d67_report_path, default={}) or {}
    d63 = _read_json(root_path / d63_report_path, default={}) or {}
    d66 = _read_json(root_path / d66_report_path, default={}) or {}
    policy = _read_json(root_path / core_policy_path, default={}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    if not d70:
        errors.append("D70 review missing or unreadable")
    if not d69_bundle:
        errors.append("D69 sandbox bundle missing or unreadable")
    if not policy:
        warnings.append("core guard policy missing or unreadable")
    if not d63:
        warnings.append("D63 replay report missing or unreadable")
    if not d67:
        warnings.append("D67 topology report missing or unreadable")
    if not d66:
        warnings.append("D66 reviewer report missing or unreadable")
    if not d68:
        warnings.append("D68 proposal report missing or unreadable")

    if d70:
        if d70.get("ok") is not True:
            errors.append("D70 review ok flag is not true")
        if d70.get("decision") != "APPROVE_SANDBOX_BUNDLE":
            errors.append(f"D70 decision is not APPROVE_SANDBOX_BUNDLE: {d70.get('decision')}")
        if d70.get("guardrails", {}).get("d64_apply_allowed") is not True:
            errors.append("D70 does not allow D64 consumption")

    if d69_bundle:
        if d69_bundle.get("ok") is not True:
            errors.append("D69 bundle ok flag is not true")
        _guardrails_clean("D69", d69_bundle.get("guardrails", {}) if isinstance(d69_bundle.get("guardrails"), dict) else {}, errors)

    if d70:
        _guardrails_clean("D70", d70.get("guardrails", {}) if isinstance(d70.get("guardrails"), dict) else {}, errors)

    d69_validation = d69_report.get("validation", {}) if isinstance(d69_report.get("validation"), dict) else {}
    if d69_report and d69_validation.get("ok") is not True:
        errors.append("D69 report validation is not ok")

    protected_files = _protected_files_from_policy(policy)

    written_files_raw = d69_bundle.get("written_files", [])
    written_files = [_safe_relative_path(str(x)) for x in written_files_raw] if isinstance(written_files_raw, list) else []

    if not written_files:
        errors.append("D69 bundle has no sandbox written_files")

    sandbox_candidates: List[str] = []
    for rel in written_files:
        if not _is_allowed_sandbox_file(rel):
            errors.append(f"D64 rejected non-sandbox candidate: {rel}")
            continue
        if rel in protected_files:
            errors.append(f"D64 rejected protected candidate: {rel}")
            continue
        if not (root_path / rel).exists():
            errors.append(f"D64 candidate missing on disk: {rel}")
            continue
        sandbox_candidates.append(rel)

    probe_results = d69_bundle.get("probe_results", [])
    if isinstance(probe_results, list):
        for item in probe_results:
            if isinstance(item, dict) and item.get("ok") is not True:
                errors.append(f"D69 probe not ok for {item.get('path')}: {item.get('reason')}")
    else:
        errors.append("D69 probe_results missing or invalid")

    macro_decision = _extract_macro_decision(d63)
    macro_decision_value = macro_decision.get("decision", "UNKNOWN")

    gate_passed = len(errors) == 0
    decision = "CREATE_GUARDED_APPLY_REQUEST" if gate_passed else "BLOCK_GUARDED_APPLY"
    result = "D64_GUARDED_APPLY_REQUEST_CREATED" if gate_passed else "D64_GUARDED_APPLY_BLOCKED"

    guarded_apply_request = {
        "request_state": "D64_GUARDED_APPLY_REQUEST",
        "enabled": gate_passed,
        "apply_mode": "DRY_RUN_FIRST_SANDBOX_TO_GUARDED_ROUTE",
        "source_sandbox_bundle": str(root_path / d69_bundle_path),
        "source_d70_review": str(root_path / d70_review_path),
        "sandbox_candidates": sandbox_candidates,
        "protected_files": protected_files,
        "forbidden_actions": [
            "direct_core_edit",
            "overwrite_canonical_memory",
            "auto_commit_without_review",
            "apply_without_dry_run",
            "apply_without_rollback",
        ],
        "required_next_evidence": [
            "D71_ROUTE_DRY_RUN_SIMULATION",
            "D66_REVIEWER_RECHECK",
            "UNIT_TESTS",
            "REGRESSION_TESTS",
            "ROLLBACK_PLAN",
        ],
        "allowed_next_scope": [
            "generate dry-run route diff",
            "generate rollback plan",
            "generate validation bundle",
        ],
        "disallowed_next_scope": [
            "mutate protected core immediately",
            "write canonical memory directly",
            "commit runtime mutation automatically",
        ],
    }

    report = {
        "state": "D64_SAFE_MUTATION_GATE",
        "result": result,
        "route": "FIELD_INTENT_SAFE_MUTATION_GATE",
        "ok": gate_passed,
        "decision": decision,
        "created_at": _now(),
        "macro_decision": macro_decision_value,
        "sandbox_candidates": sandbox_candidates,
        "protected_files": protected_files,
        "guarded_apply_request": guarded_apply_request,
        "input_reports": {
            "d70_review_path": str(root_path / d70_review_path),
            "d69_bundle_path": str(root_path / d69_bundle_path),
            "d69_report_path": str(root_path / d69_report_path),
            "d68_proposal_path": str(root_path / d68_proposal_path),
            "d67_report_path": str(root_path / d67_report_path),
            "d63_report_path": str(root_path / d63_report_path),
            "d66_report_path": str(root_path / d66_report_path),
            "core_policy_path": str(root_path / core_policy_path),
        },
        "evidence": {
            "d70_decision": d70.get("decision"),
            "d70_ok": d70.get("ok"),
            "d69_bundle_ok": d69_bundle.get("ok"),
            "d68_proposed_action": d68.get("proposed_action"),
            "d67_result": d67.get("result"),
            "d66_decision": d66.get("decision"),
            "macro_decision": macro_decision,
        },
        "guardrails": {
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "gate_only": True,
        },
        "validation": {
            "ok": gate_passed,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "sandbox_candidates_count": len(sandbox_candidates),
            "protected_files_count": len(protected_files),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "gate_evaluated": True,
            "guarded_apply_request_created": gate_passed,
            "actual_apply_executed": False,
            "next_step": "D71 should run a route dry-run simulation before any real guarded apply.",
        },
    }

    _write_json(root_path / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(build_safe_mutation_gate_request(), ensure_ascii=False, indent=2))
