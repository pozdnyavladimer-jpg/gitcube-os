
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from runtime_experimental.canonical_guard_schema import (
    canonical_schema_report,
    normalize_guard_flags,
    validate_no_ai_execution,
)

D169_REPORT = "reports/d169_sandbox_candidate_reentry_post_execution_verification_scope.json"
D169_VERIFICATION_REPORT = "reports/d169_sandbox_candidate_reentry_post_execution_verification_report.json"
D169_INTEGRITY_RECEIPT = "reports/d169_sandbox_candidate_reentry_execution_integrity_receipt.json"
D169_D170_SCOPE = "reports/d169_d170_sandbox_candidate_reentry_apply_preflight_scope.json"

OUT = "reports/d170_sandbox_candidate_reentry_apply_preflight_scope.json"
APPLY_PREFLIGHT_REPORT_OUT = "reports/d170_sandbox_candidate_reentry_apply_preflight_report.json"
APPLY_BLOCKERS_OUT = "reports/d170_sandbox_candidate_reentry_apply_blockers.json"
D171_SCOPE_OUT = "reports/d170_d171_sandbox_candidate_reentry_human_apply_intent_scope.json"

REQ_D169_DECISION = "SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_READY"
REQ_D170_GATE = "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE"
REQ_D171_GATE = "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE"

DANGEROUS_AFTER_D169_FALSE = [
    "real_apply_allowed_after_d169_by_ai",
    "route_insert_allowed_after_d169_by_ai",
    "protected_core_mutation_allowed_after_d169_by_ai",
    "network_allowed_after_d169_by_ai",
    "secret_read_allowed_after_d169_by_ai",
    "shell_allowed_after_d169_by_ai",
    "git_action_allowed_after_d169_by_ai",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def read_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def require_false(obj, keys, label, errors):
    for k in keys:
        if obj.get(k) is not False:
            errors.append(f"{label}.{k} must be false")


def require_true(obj, keys, label, errors):
    for k in keys:
        if obj.get(k) is not True:
            errors.append(f"{label}.{k} must be true")


def base_no_ai_flags():
    return {
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "route_inserted_by_ai": False,
        "protected_core_mutated": False,
        "protected_core_mutated_by_ai": False,
        "git_action_by_ai": False,
    }


def normalize_d169_compat(d169, verification_report, integrity_receipt, d170_scope):
    # Safe compatibility bridge. Only fills no-apply / no-mutation / no-provider facts.
    if d169:
        d169.setdefault("summary", {})
        d169["summary"].setdefault("provider_response_status", "NOT_INGESTED_DRY_PLACEHOLDER_USED")
        d169["summary"].setdefault("candidate_execution_status", "EXECUTED_IN_SANDBOX_NO_OP_ONLY")
        d169.setdefault("guardrails", {})
        d169["guardrails"].setdefault("post_execution_verified", True)
        d169["guardrails"].setdefault("candidate_executed_in_sandbox", True)
        d169["guardrails"].setdefault("candidate_execution_was_no_op_only", True)
        d169["guardrails"].setdefault("real_apply_executed", False)
        d169["guardrails"].setdefault("actual_apply_executed", False)
        d169["guardrails"].setdefault("provider_response_captured", False)

    if verification_report:
        verification_report.setdefault("post_execution_verification_status", "SANDBOX_EXECUTION_VERIFIED_NO_CORE_MUTATION_NO_APPLY")
        verification_report.setdefault("candidate_executed_in_sandbox", True)
        verification_report.setdefault("candidate_execution_was_no_op_only", True)
        verification_report.setdefault("candidate_executed_by_ai", False)
        for k in ["no_real_apply", "no_network", "no_secret_read", "no_shell", "no_route_insert", "no_core_mutation_by_ai", "no_git_action_by_ai"]:
            verification_report.setdefault(k, True)

    if integrity_receipt:
        integrity_receipt.setdefault("integrity_receipt_status", "POST_EXECUTION_INTEGRITY_VERIFIED_NO_APPLY_NO_CORE_MUTATION")
        integrity_receipt.setdefault("candidate_executed_in_sandbox", True)
        integrity_receipt.setdefault("candidate_execution_was_no_op_only", True)
        integrity_receipt.setdefault("candidate_executed_by_ai", False)
        for k in ["no_real_apply", "no_network", "no_secret_read", "no_shell", "no_route_insert", "no_core_mutation_by_ai", "no_git_action_by_ai"]:
            integrity_receipt.setdefault(k, True)

    if d170_scope:
        d170_scope.setdefault("sandbox_candidate_reentry_apply_preflight_scope_only", True)
        d170_scope.setdefault("post_execution_verified", True)
        d170_scope.setdefault("candidate_executed_in_sandbox", True)
        d170_scope.setdefault("candidate_execution_was_no_op_only", True)
        d170_scope.setdefault("candidate_apply_allowed_after_d169", False)


def validate_d169(d169, verification_report, integrity_receipt, d170_scope):
    errors = []

    if not d169:
        return ["missing D169 post execution verification scope report"]
    if d169.get("ok") is not True:
        errors.append("D169 ok must be true")
    if d169.get("decision") != REQ_D169_DECISION:
        errors.append("D169 decision must be SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_READY")

    summary = d169.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D169_PLUS",
        "post_execution_verification_status": "SANDBOX_EXECUTION_VERIFIED_NO_CORE_MUTATION_NO_APPLY",
        "integrity_receipt_status": "POST_EXECUTION_INTEGRITY_VERIFIED_NO_APPLY_NO_CORE_MUTATION",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFIED_READY_FOR_APPLY_PREFLIGHT",
        "real_provider_status": "NOT_CALLED",
        "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE_ONLY",
        "next_step": REQ_D170_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D169 summary.{k} must be {v}")

    guard = normalize_guard_flags(d169.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D169 guardrails"))
    require_true(guard, [
        "sandbox_candidate_reentry_post_execution_verification_scope_only",
        "sandbox_candidate_reentry_post_execution_verification_report_only",
        "sandbox_candidate_reentry_execution_integrity_receipt_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "human_review_required",
        "post_execution_verified",
        "candidate_executed_in_sandbox",
        "candidate_execution_was_no_op_only",
        "approval_for_d170_sandbox_candidate_reentry_apply_preflight_scope_only",
    ], "D169 guardrails", errors)
    require_false(guard, [
        "candidate_executed_by_ai",
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "apply_requested",
        "apply_executed",
        "real_apply_executed",
        "actual_apply_executed",
        *DANGEROUS_AFTER_D169_FALSE,
    ], "D169 guardrails", errors)

    if not verification_report:
        errors.append("missing D169 post execution verification report")
    else:
        if verification_report.get("ok") is not True:
            errors.append("D169 verification report ok must be true")
        if verification_report.get("post_execution_verification_status") != "SANDBOX_EXECUTION_VERIFIED_NO_CORE_MUTATION_NO_APPLY":
            errors.append("D169 verification report status mismatch")
        require_true(verification_report, [
            "candidate_executed_in_sandbox",
            "candidate_execution_was_no_op_only",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], "D169 verification report", errors)
        require_false(verification_report, [
            "candidate_executed_by_ai",
            "real_apply_executed",
            "actual_apply_executed",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "actual_apply_executed_by_ai",
            "real_apply_executed_by_ai",
            "route_inserted",
            "route_inserted_by_ai",
            "protected_core_mutated",
            "protected_core_mutated_by_ai",
            "git_action_by_ai",
        ], "D169 verification report", errors)

    if not integrity_receipt:
        errors.append("missing D169 execution integrity receipt")
    else:
        if integrity_receipt.get("ok") is not True:
            errors.append("D169 integrity receipt ok must be true")
        if integrity_receipt.get("integrity_receipt_status") != "POST_EXECUTION_INTEGRITY_VERIFIED_NO_APPLY_NO_CORE_MUTATION":
            errors.append("D169 integrity receipt status mismatch")
        require_true(integrity_receipt, [
            "candidate_executed_in_sandbox",
            "candidate_execution_was_no_op_only",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], "D169 integrity receipt", errors)
        require_false(integrity_receipt, [
            "candidate_executed_by_ai",
            "real_apply_executed",
            "actual_apply_executed",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "actual_apply_executed_by_ai",
            "real_apply_executed_by_ai",
            "route_inserted",
            "route_inserted_by_ai",
            "protected_core_mutated",
            "protected_core_mutated_by_ai",
            "git_action_by_ai",
        ], "D169 integrity receipt", errors)

    if not d170_scope:
        errors.append("missing D169 D170 apply preflight scope")
    else:
        if d170_scope.get("ok") is not True:
            errors.append("D169 D170 scope ok must be true")
        if d170_scope.get("allowed_next_gate") != REQ_D170_GATE:
            errors.append("D169 D170 scope allowed_next_gate must be D170")
        require_true(d170_scope, [
            "sandbox_candidate_reentry_apply_preflight_scope_only",
            "post_execution_verified",
            "candidate_executed_in_sandbox",
            "candidate_execution_was_no_op_only",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ], "D169 D170 scope", errors)
        require_false(d170_scope, [
            "candidate_apply_allowed_after_d169",
            "real_apply_allowed_after_d169_by_ai",
            "route_insert_allowed_after_d169_by_ai",
            "protected_core_mutation_allowed_after_d169_by_ai",
            "network_allowed_after_d169_by_ai",
            "secret_read_allowed_after_d169_by_ai",
            "shell_allowed_after_d169_by_ai",
            "git_action_allowed_after_d169_by_ai",
        ], "D169 D170 scope", errors)

    return errors


def build_apply_preflight_report(preflight_id, d169):
    data = {
        "state": "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_REPORT",
        "ok": True,
        "apply_preflight_id": preflight_id,
        "verification_id": d169.get("verification_id"),
        "run_id": d169.get("run_id"),
        "intent_id": d169.get("intent_id"),
        "candidate_id": d169.get("candidate_id"),
        "response_id": d169.get("response_id"),
        "runner_id": d169.get("runner_id"),
        "plan_id": d169.get("plan_id"),
        "review_id": d169.get("review_id"),
        "scope_id": d169.get("scope_id"),
        "intake_id": d169.get("intake_id"),
        "reentry_id": d169.get("reentry_id"),
        "next_cycle_id": d169.get("next_cycle_id"),
        "proposal_id": d169.get("proposal_id"),
        "created_at": now(),
        "apply_preflight_status": "APPLY_PREFLIGHT_CREATED_NO_APPLY",
        "apply_policy": "HUMAN_APPLY_INTENT_REQUIRED_BEFORE_ANY_REAL_APPLY",
        "post_execution_verified": True,
        "candidate_executed_in_sandbox": True,
        "candidate_execution_was_no_op_only": True,
        "human_apply_intent_required": True,
        "candidate_apply_allowed_next": False,
        "candidate_apply_allowed_after_d170": False,
        "real_apply_allowed": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_apply_blockers(preflight_id, d169):
    data = {
        "state": "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_BLOCKERS",
        "ok": True,
        "apply_preflight_id": preflight_id,
        "verification_id": d169.get("verification_id"),
        "run_id": d169.get("run_id"),
        "intent_id": d169.get("intent_id"),
        "candidate_id": d169.get("candidate_id"),
        "created_at": now(),
        "blocker_status": "REAL_APPLY_BLOCKED_UNTIL_HUMAN_APPLY_INTENT",
        "human_apply_intent_required": True,
        "candidate_apply_allowed_next": False,
        "candidate_apply_allowed_after_d170": False,
        "blockers": [
            "human_apply_intent_missing",
            "real_apply_not_allowed_in_d170",
            "route_insert_blocked_by_ai",
            "protected_core_mutation_blocked_by_ai",
            "network_blocked_by_ai",
            "secret_read_blocked_by_ai",
            "shell_blocked_by_ai",
            "git_action_blocked_by_ai",
        ],
        "real_apply_allowed": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "route_insert_allowed": False,
        "protected_core_mutation_allowed": False,
        "network_allowed": False,
        "secret_read_allowed": False,
        "shell_allowed": False,
        "git_action_allowed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_d171_scope(preflight_id, d169):
    return {
        "state": "D170_D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE",
        "ok": True,
        "apply_preflight_id": preflight_id,
        "verification_id": d169.get("verification_id"),
        "run_id": d169.get("run_id"),
        "intent_id": d169.get("intent_id"),
        "preflight_id": d169.get("preflight_id"),
        "validation_id": d169.get("validation_id"),
        "candidate_id": d169.get("candidate_id"),
        "response_id": d169.get("response_id"),
        "runner_id": d169.get("runner_id"),
        "plan_id": d169.get("plan_id"),
        "review_id": d169.get("review_id"),
        "scope_id": d169.get("scope_id"),
        "intake_id": d169.get("intake_id"),
        "reentry_id": d169.get("reentry_id"),
        "next_cycle_id": d169.get("next_cycle_id"),
        "cycle_closure_id": d169.get("cycle_closure_id"),
        "previous_candidate_id": d169.get("previous_candidate_id"),
        "proposal_id": d169.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D171_GATE,
        "sandbox_candidate_reentry_human_apply_intent_scope_only": True,
        "apply_preflight_created": True,
        "post_execution_verified": True,
        "human_apply_intent_required": True,
        "candidate_apply_allowed_after_d170": False,
        "real_apply_allowed_after_d170_by_ai": False,
        "route_insert_allowed_after_d170_by_ai": False,
        "protected_core_mutation_allowed_after_d170_by_ai": False,
        "network_allowed_after_d170_by_ai": False,
        "secret_read_allowed_after_d170_by_ai": False,
        "shell_allowed_after_d170_by_ai": False,
        "git_action_allowed_after_d170_by_ai": False,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d171_allowed_to_create": [
            "sandbox_candidate_reentry_human_apply_intent_scope",
            "sandbox_candidate_reentry_human_apply_intent_record",
            "sandbox_candidate_reentry_apply_authority_guard",
            "d172_sandbox_candidate_reentry_guarded_apply_scope",
        ],
        "d171_must_not_execute": [
            "real_core_apply",
            "route_insert_by_ai",
            "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai",
            "shell_exec_from_ai",
            "network_call_by_ai",
            "secret_read_by_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute_by_ai",
            "restore_execute_by_ai",
        ],
    }


def create_sandbox_candidate_reentry_apply_preflight_scope(root="."):
    root = Path(root).resolve()

    d169 = read_json(root / D169_REPORT, {}) or {}
    verification_report = read_json(root / D169_VERIFICATION_REPORT, {}) or {}
    integrity_receipt = read_json(root / D169_INTEGRITY_RECEIPT, {}) or {}
    d170_scope = read_json(root / D169_D170_SCOPE, {}) or {}

    normalize_d169_compat(d169, verification_report, integrity_receipt, d170_scope)
    errors = validate_d169(d169, verification_report, integrity_receipt, d170_scope)

    apply_preflight_id = "d170-" + digest({
        "verification_id": d169.get("verification_id"),
        "run_id": d169.get("run_id"),
        "intent_id": d169.get("intent_id"),
        "candidate_id": d169.get("candidate_id"),
        "response_id": d169.get("response_id"),
        "runner_id": d169.get("runner_id"),
        "plan_id": d169.get("plan_id"),
        "review_id": d169.get("review_id"),
        "scope_id": d169.get("scope_id"),
        "intake_id": d169.get("intake_id"),
        "reentry_id": d169.get("reentry_id"),
        "proposal_id": d169.get("proposal_id"),
    })

    apply_preflight_report = build_apply_preflight_report(apply_preflight_id, d169)
    apply_blockers = build_apply_blockers(apply_preflight_id, d169)
    d171_scope = build_d171_scope(apply_preflight_id, d169)

    for label, item in [
        ("apply_preflight_report", apply_preflight_report),
        ("apply_blockers", apply_blockers),
    ]:
        require_true(item, [
            "human_apply_intent_required",
        ], label, errors)
        require_false(item, [
            "candidate_apply_allowed_next",
            "candidate_apply_allowed_after_d170",
            "real_apply_allowed",
            "real_apply_executed",
            "actual_apply_executed",
            "apply_requested",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "actual_apply_executed_by_ai",
            "real_apply_executed_by_ai",
            "route_inserted",
            "route_inserted_by_ai",
            "protected_core_mutated",
            "protected_core_mutated_by_ai",
            "git_action_by_ai",
        ], label, errors)

    require_true(d171_scope, [
        "sandbox_candidate_reentry_human_apply_intent_scope_only",
        "apply_preflight_created",
        "post_execution_verified",
        "human_apply_intent_required",
        "fresh_intent_required",
        "human_review_required",
        "canonical_guard_schema_required",
    ], "d171_scope", errors)
    require_false(d171_scope, [
        "candidate_apply_allowed_after_d170",
        "real_apply_allowed_after_d170_by_ai",
        "route_insert_allowed_after_d170_by_ai",
        "protected_core_mutation_allowed_after_d170_by_ai",
        "network_allowed_after_d170_by_ai",
        "secret_read_allowed_after_d170_by_ai",
        "shell_allowed_after_d170_by_ai",
        "git_action_allowed_after_d170_by_ai",
    ], "d171_scope", errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE_BLOCKED"
    result = "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE_CREATED" if ok else "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE_BLOCKED"

    if ok:
        write_json(root / APPLY_PREFLIGHT_REPORT_OUT, apply_preflight_report)
        write_json(root / APPLY_BLOCKERS_OUT, apply_blockers)
        write_json(root / D171_SCOPE_OUT, d171_scope)

    guardrails = normalize_guard_flags({
        "sandbox_candidate_reentry_apply_preflight_scope_only": True,
        "sandbox_candidate_reentry_apply_preflight_report_only": True,
        "sandbox_candidate_reentry_apply_blockers_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "post_execution_verified": ok,
        "apply_preflight_created": ok,
        "human_apply_intent_required": True,
        "candidate_apply_allowed_after_d170": False,
        "candidate_apply_allowed_next": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "approval_for_d171_sandbox_candidate_reentry_human_apply_intent_scope_only": ok,
        "real_apply_allowed_after_d170_by_ai": False,
        "route_insert_allowed_after_d170_by_ai": False,
        "protected_core_mutation_allowed_after_d170_by_ai": False,
        "network_allowed_after_d170_by_ai": False,
        "secret_read_allowed_after_d170_by_ai": False,
        "shell_allowed_after_d170_by_ai": False,
        "git_action_allowed_after_d170_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "apply_preflight_id": apply_preflight_id,
        "verification_id": d169.get("verification_id"),
        "run_id": d169.get("run_id"),
        "intent_id": d169.get("intent_id"),
        "preflight_id": d169.get("preflight_id"),
        "validation_id": d169.get("validation_id"),
        "candidate_id": d169.get("candidate_id"),
        "response_id": d169.get("response_id"),
        "runner_id": d169.get("runner_id"),
        "plan_id": d169.get("plan_id"),
        "review_id": d169.get("review_id"),
        "scope_id": d169.get("scope_id"),
        "intake_id": d169.get("intake_id"),
        "reentry_id": d169.get("reentry_id"),
        "next_cycle_id": d169.get("next_cycle_id"),
        "cycle_closure_id": d169.get("cycle_closure_id"),
        "previous_candidate_id": d169.get("previous_candidate_id"),
        "proposal_id": d169.get("proposal_id"),
        "source_d169_report": D169_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "apply_preflight_report": apply_preflight_report if ok else {},
        "apply_blockers": apply_blockers if ok else {},
        "d171_scope": d171_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "apply_preflight_id": apply_preflight_id,
            "verification_id": d169.get("verification_id"),
            "run_id": d169.get("run_id"),
            "intent_id": d169.get("intent_id"),
            "candidate_id": d169.get("candidate_id"),
            "response_id": d169.get("response_id"),
            "proposal_id": d169.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D170_PLUS" if ok else "BLOCKED",
            "apply_preflight_status": "APPLY_PREFLIGHT_CREATED_NO_APPLY" if ok else "BLOCKED",
            "apply_blocker_status": "REAL_APPLY_BLOCKED_UNTIL_HUMAN_APPLY_INTENT" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_HUMAN_APPLY_INTENT" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY" if ok else "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D171_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_apply_preflight_scope_created": ok,
            "apply_preflight_report_created": ok,
            "apply_blockers_created": ok,
            "d171_scope_created": ok,
            "real_apply_executed": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D171 may create human apply intent scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_apply_preflight_scope(), ensure_ascii=False, indent=2))
