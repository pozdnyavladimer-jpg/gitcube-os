from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


DECISION_APPROVE = "APPROVE"
DECISION_REJECT = "REJECT"
DECISION_NEEDS_SANDBOX = "NEEDS_SANDBOX"
DECISION_FORBIDDEN_CORE_MUTATION = "FORBIDDEN_CORE_MUTATION"
DECISION_VALIDATION_BYPASS = "VALIDATION_BYPASS"
DECISION_UNSAFE_MEMORY_WRITE = "UNSAFE_MEMORY_WRITE"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _norm_path(value: Any) -> str:
    text = str(value or "").strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def _collect_strings(value: Any) -> List[str]:
    out: List[str] = []
    if value is None:
        return out
    if isinstance(value, str):
        if value.strip():
            out.append(value.strip())
        return out
    if isinstance(value, (list, tuple, set)):
        for item in value:
            out.extend(_collect_strings(item))
        return out
    if isinstance(value, dict):
        for key in ("path", "file", "target", "target_file", "target_path", "name", "id"):
            if key in value:
                out.extend(_collect_strings(value.get(key)))
    return out


def _collect_target_files(proposal: Dict[str, Any]) -> List[str]:
    candidates: List[str] = []
    for key in ("target_files", "changed_files", "files", "candidate_target_files", "protected_files", "patch_files"):
        candidates.extend(_collect_strings(proposal.get(key)))

    payload = proposal.get("payload")
    if isinstance(payload, dict):
        for key in ("target_files", "changed_files", "files", "candidate_target_files", "patch_files", "paths"):
            candidates.extend(_collect_strings(payload.get(key)))

    raw_patch = proposal.get("patch") or proposal.get("candidate_patch")
    if isinstance(raw_patch, dict):
        candidates.extend(_collect_strings(raw_patch.get("target_files")))
        candidates.extend(_collect_strings(raw_patch.get("changed_files")))

    normalized: List[str] = []
    seen: Set[str] = set()
    for item in candidates:
        p = _norm_path(item)
        if not p or p in seen:
            continue
        seen.add(p)
        normalized.append(p)
    return normalized


def _collect_actions(proposal: Dict[str, Any]) -> List[str]:
    actions: List[str] = []
    for key in ("actions", "requested_actions", "agent_actions", "forbidden_actions"):
        actions.extend(_collect_strings(proposal.get(key)))

    execution = proposal.get("execution")
    if isinstance(execution, dict):
        actions.extend(_collect_strings(execution.get("actions")))

    payload = proposal.get("payload")
    if isinstance(payload, dict):
        for key in ("actions", "requested_actions", "agent_actions"):
            actions.extend(_collect_strings(payload.get(key)))

    normalized: List[str] = []
    seen: Set[str] = set()
    for item in actions:
        a = str(item or "").strip().lower()
        if not a or a in seen:
            continue
        seen.add(a)
        normalized.append(a)
    return normalized


def _truthy_from_keys(data: Dict[str, Any], keys: Iterable[str]) -> bool:
    for key in keys:
        if bool(data.get(key)) is True:
            return True
    return False


def _collect_validation(proposal: Dict[str, Any]) -> Dict[str, bool]:
    merged: Dict[str, Any] = {}

    for source_key in ("validation", "evidence", "success_condition"):
        if isinstance(proposal.get(source_key), dict):
            merged.update(proposal.get(source_key) or {})

    payload = proposal.get("payload")
    if isinstance(payload, dict):
        for source_key in ("validation", "evidence", "success_condition"):
            if isinstance(payload.get(source_key), dict):
                merged.update(payload.get(source_key) or {})

    unit_tests = _truthy_from_keys(merged, (
        "unit_tests_passed", "tests_passed", "py_compile_passed",
        "local_validation_ok", "local_life_ok", "eye_1_passed",
    ))
    regression = _truthy_from_keys(merged, (
        "regression_passed", "closed_loop_regression_passed",
        "global_validation_ok", "global_life_ok", "eye_2_passed",
    ))
    daemon_smoke = _truthy_from_keys(merged, (
        "daemon_smoke_passed", "daemon_test_passed",
        "runtime_smoke_passed", "runtime_check_passed",
    ))
    backup_plan = _truthy_from_keys(merged, (
        "backup_plan_exists", "backup_created",
        "rollback_plan_exists", "rollback_available",
    ))
    payload_preserved = _truthy_from_keys(merged, (
        "payload_preserved", "resonance_vector_preserved",
        "protected_payload_preserved", "payload_preservation_confirmed",
    ))
    reviewer_approved = _truthy_from_keys(merged, (
        "reviewer_approved", "d66_approved", "independent_review_passed",
    ))

    return {
        "unit_tests_passed": unit_tests,
        "regression_passed": regression,
        "daemon_smoke_passed": daemon_smoke,
        "backup_or_rollback_exists": backup_plan,
        "payload_preserved": payload_preserved,
        "reviewer_approved": reviewer_approved,
        "two_eyes_passed": bool(unit_tests and regression),
    }


def _is_memory_path(path: str) -> bool:
    p = _norm_path(path)
    return p.startswith("memory/") and not (
        p.endswith("_decayed.json")
        or p.endswith("_candidate.json")
        or p.endswith("_reviewed.json")
        or p.endswith(".bak")
    )


def review_core_mutation(
    proposal: Dict[str, Any] | None = None,
    proposal_path: str | None = None,
    policy_path: str = "runtime_experimental/core_guard_policy.json",
    report_path: str = "reports/d66_core_guard_reviewer_report.json",
) -> Dict[str, Any]:
    policy = _load_json(policy_path, default={}) or {}

    if proposal is None:
        proposal = {}

    if proposal_path:
        loaded = _load_json(proposal_path, default=None)
        if isinstance(loaded, dict):
            proposal = loaded

    protected_files = {_norm_path(p) for p in policy.get("protected_files", []) if _norm_path(p)}
    forbidden_actions = {
        str(a or "").strip().lower()
        for a in policy.get("forbidden_without_review", [])
        if str(a or "").strip()
    }

    target_files = _collect_target_files(proposal)
    actions = _collect_actions(proposal)
    validation = _collect_validation(proposal)

    protected_touched = [p for p in target_files if p in protected_files]
    canonical_memory_touched = [p for p in target_files if _is_memory_path(p)]
    forbidden_action_hits = sorted(set(actions).intersection(forbidden_actions))

    errors: List[str] = []
    warnings: List[str] = []

    if "validation_bypass" in forbidden_action_hits or "regression_disable" in forbidden_action_hits:
        decision = DECISION_VALIDATION_BYPASS
        reason = "validation_bypass_detected"
        errors.append("proposal attempts to bypass or disable validation")
    elif canonical_memory_touched and not validation.get("backup_or_rollback_exists"):
        decision = DECISION_UNSAFE_MEMORY_WRITE
        reason = "canonical_memory_write_without_backup_or_rollback"
        errors.append("canonical memory target requires backup/rollback proof")
    elif protected_touched and not validation.get("two_eyes_passed"):
        decision = DECISION_FORBIDDEN_CORE_MUTATION
        reason = "protected_core_touched_without_two_eyes"
        errors.append("protected core mutation requires two eyes: local tests + regression")
    elif protected_touched and not validation.get("payload_preserved"):
        decision = DECISION_FORBIDDEN_CORE_MUTATION
        reason = "protected_core_touched_without_payload_preservation"
        errors.append("protected core mutation requires payload preservation proof")
    elif forbidden_action_hits and not validation.get("two_eyes_passed"):
        decision = DECISION_REJECT
        reason = "forbidden_action_requires_review"
        errors.append("forbidden action requested without two-eye validation")
    elif not validation.get("unit_tests_passed") or not validation.get("regression_passed"):
        decision = DECISION_NEEDS_SANDBOX
        reason = "sandbox_required_before_approval"
        warnings.append("proposal should pass local tests and regression before approval")
    else:
        decision = DECISION_APPROVE
        reason = "two_eyes_policy_satisfied"

    report = {
        "state": "D66_CORE_GUARD_REVIEWER",
        "result": f"D66_REVIEW_{decision}",
        "route": "FIELD_INTENT_CORE_GUARD_REVIEWER",
        "ok": decision == DECISION_APPROVE,
        "created_at": _now(),
        "decision": decision,
        "reason": reason,
        "policy_path": str(policy_path),
        "proposal_path": str(proposal_path or ""),
        "report_path": str(report_path),
        "target_files": target_files,
        "actions": actions,
        "protected_files_touched": protected_touched,
        "canonical_memory_touched": canonical_memory_touched,
        "forbidden_action_hits": forbidden_action_hits,
        "validation": {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            **validation,
        },
        "review_rules": {
            "protected_core_requires_two_eyes": True,
            "canonical_memory_requires_backup": True,
            "validation_bypass_rejected": True,
            "payload_preservation_required_for_core": True,
        },
        "success_condition": {
            "reviewer_executed": True,
            "decision_emitted": True,
            "runtime_code_mutated": False,
            "next_step": "If APPROVE, D64 may use this report as one guarded-apply input. If not, create sandbox/test evidence first.",
        },
        "raw_proposal": proposal,
    }

    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = review_core_mutation()
    print(json.dumps(result, ensure_ascii=False, indent=2))
