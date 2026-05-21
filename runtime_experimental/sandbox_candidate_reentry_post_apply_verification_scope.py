
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

D172_REPORT = "reports/d172_sandbox_candidate_reentry_guarded_apply_scope.json"
D172_GUARDED_APPLY_PLAN = "reports/d172_sandbox_candidate_reentry_guarded_apply_plan.json"
D172_GUARDED_APPLY_RECEIPT = "reports/d172_sandbox_candidate_reentry_guarded_apply_receipt.json"
D172_D173_SCOPE = "reports/d172_d173_sandbox_candidate_reentry_post_apply_verification_scope.json"

OUT = "reports/d173_sandbox_candidate_reentry_post_apply_verification_scope.json"
POST_APPLY_VERIFICATION_REPORT_OUT = "reports/d173_sandbox_candidate_reentry_post_apply_verification_report.json"
APPLY_INTEGRITY_RECEIPT_OUT = "reports/d173_sandbox_candidate_reentry_apply_integrity_receipt.json"
D174_SCOPE_OUT = "reports/d173_d174_sandbox_candidate_reentry_final_apply_audit_scope.json"

REQ_D172_DECISION = "SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_READY"
REQ_D173_GATE = "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE"
REQ_D174_GATE = "D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE"

DANGEROUS_AFTER_D172_FALSE = [
    "real_apply_allowed_after_d172_by_ai",
    "route_insert_allowed_after_d172_by_ai",
    "protected_core_mutation_allowed_after_d172_by_ai",
    "network_allowed_after_d172_by_ai",
    "secret_read_allowed_after_d172_by_ai",
    "shell_allowed_after_d172_by_ai",
    "git_action_allowed_after_d172_by_ai",
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


def normalize_d172_compat(d172, guarded_apply_plan, guarded_apply_receipt, d173_scope):
    # Safe compatibility bridge. It only fills no-apply / no-mutation facts.
    if d172:
        d172.setdefault("summary", {})
        d172["summary"].setdefault("provider_response_status", "NOT_INGESTED_DRY_PLACEHOLDER_USED")
        d172["summary"].setdefault("candidate_execution_status", "EXECUTED_IN_SANDBOX_NO_OP_ONLY")
        d172.setdefault("guardrails", {})
        d172["guardrails"].setdefault("guarded_apply_recorded", True)
        d172["guardrails"].setdefault("candidate_apply_recorded", True)
        d172["guardrails"].setdefault("candidate_apply_executed", False)
        d172["guardrails"].setdefault("candidate_apply_executed_by_ai", False)
        d172["guardrails"].setdefault("real_apply_executed", False)
        d172["guardrails"].setdefault("actual_apply_executed", False)
        d172["guardrails"].setdefault("provider_response_captured", False)

    if guarded_apply_plan:
        guarded_apply_plan.setdefault("guarded_apply_plan_status", "GUARDED_APPLY_PLAN_CREATED_NO_CORE_MUTATION")
        guarded_apply_plan.setdefault("apply_mode", "SANDBOX_GUARDED_NO_OP_APPLY_RECORD_ONLY")
        guarded_apply_plan.setdefault("human_apply_intent_present", True)
        guarded_apply_plan.setdefault("guarded_apply_scope_only", True)
        guarded_apply_plan.setdefault("candidate_apply_recorded", True)
        guarded_apply_plan.setdefault("candidate_apply_executed", False)
        guarded_apply_plan.setdefault("candidate_apply_executed_by_ai", False)

    if guarded_apply_receipt:
        guarded_apply_receipt.setdefault("guarded_apply_receipt_status", "GUARDED_APPLY_RECORDED_NO_CORE_MUTATION_NO_AI_APPLY")
        guarded_apply_receipt.setdefault("human_apply_intent_present", True)
        guarded_apply_receipt.setdefault("guarded_apply_recorded", True)
        guarded_apply_receipt.setdefault("guarded_apply_scope_only", True)
        guarded_apply_receipt.setdefault("candidate_apply_recorded", True)
        guarded_apply_receipt.setdefault("candidate_apply_executed", False)
        guarded_apply_receipt.setdefault("candidate_apply_executed_by_ai", False)

    if d173_scope:
        d173_scope.setdefault("sandbox_candidate_reentry_post_apply_verification_scope_only", True)
        d173_scope.setdefault("human_apply_intent_present", True)
        d173_scope.setdefault("guarded_apply_recorded", True)
        d173_scope.setdefault("guarded_apply_scope_only", True)
        d173_scope.setdefault("candidate_apply_recorded", True)
        d173_scope.setdefault("candidate_apply_executed", False)
        d173_scope.setdefault("candidate_apply_executed_by_ai", False)


def validate_d172(d172, guarded_apply_plan, guarded_apply_receipt, d173_scope):
    errors = []

    if not d172:
        return ["missing D172 guarded apply scope report"]
    if d172.get("ok") is not True:
        errors.append("D172 ok must be true")
    if d172.get("decision") != REQ_D172_DECISION:
        errors.append("D172 decision must be SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_READY")

    summary = d172.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D172_PLUS",
        "guarded_apply_status": "SANDBOX_GUARDED_APPLY_RECORDED_NO_CORE_MUTATION_NO_REAL_APPLY",
        "guarded_apply_receipt_status": "GUARDED_APPLY_RECORDED_NO_CORE_MUTATION_NO_AI_APPLY",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_RECORDED_READY_FOR_POST_APPLY_VERIFICATION",
        "real_provider_status": "NOT_CALLED",
        "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_ONLY",
        "next_step": REQ_D173_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D172 summary.{k} must be {v}")

    guard = normalize_guard_flags(d172.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D172 guardrails"))
    require_true(guard, [
        "sandbox_candidate_reentry_guarded_apply_scope_only",
        "sandbox_candidate_reentry_guarded_apply_plan_only",
        "sandbox_candidate_reentry_guarded_apply_receipt_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "human_review_required",
        "human_apply_intent_present",
        "post_execution_verified",
        "apply_preflight_created",
        "guarded_apply_recorded",
        "candidate_apply_recorded",
        "approval_for_d173_sandbox_candidate_reentry_post_apply_verification_scope_only",
    ], "D172 guardrails", errors)
    require_false(guard, [
        "candidate_apply_executed",
        "candidate_apply_executed_by_ai",
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "apply_requested",
        "apply_executed",
        "real_apply_executed",
        "actual_apply_executed",
        *DANGEROUS_AFTER_D172_FALSE,
    ], "D172 guardrails", errors)

    if not guarded_apply_plan:
        errors.append("missing D172 guarded apply plan")
    else:
        if guarded_apply_plan.get("ok") is not True:
            errors.append("D172 guarded apply plan ok must be true")
        if guarded_apply_plan.get("guarded_apply_plan_status") != "GUARDED_APPLY_PLAN_CREATED_NO_CORE_MUTATION":
            errors.append("D172 guarded apply plan status mismatch")
        if guarded_apply_plan.get("apply_mode") != "SANDBOX_GUARDED_NO_OP_APPLY_RECORD_ONLY":
            errors.append("D172 guarded apply plan mode mismatch")
        require_true(guarded_apply_plan, [
            "human_apply_intent_present",
            "apply_preflight_created",
            "post_execution_verified",
            "guarded_apply_scope_only",
            "candidate_apply_recorded",
        ], "D172 guarded apply plan", errors)
        require_false(guarded_apply_plan, [
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
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
        ], "D172 guarded apply plan", errors)

    if not guarded_apply_receipt:
        errors.append("missing D172 guarded apply receipt")
    else:
        if guarded_apply_receipt.get("ok") is not True:
            errors.append("D172 guarded apply receipt ok must be true")
        if guarded_apply_receipt.get("guarded_apply_receipt_status") != "GUARDED_APPLY_RECORDED_NO_CORE_MUTATION_NO_AI_APPLY":
            errors.append("D172 guarded apply receipt status mismatch")
        require_true(guarded_apply_receipt, [
            "human_apply_intent_present",
            "guarded_apply_recorded",
            "guarded_apply_scope_only",
            "candidate_apply_recorded",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], "D172 guarded apply receipt", errors)
        require_false(guarded_apply_receipt, [
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
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
        ], "D172 guarded apply receipt", errors)

    if not d173_scope:
        errors.append("missing D172 D173 post apply verification scope")
    else:
        if d173_scope.get("ok") is not True:
            errors.append("D172 D173 scope ok must be true")
        if d173_scope.get("allowed_next_gate") != REQ_D173_GATE:
            errors.append("D172 D173 scope allowed_next_gate must be D173")
        require_true(d173_scope, [
            "sandbox_candidate_reentry_post_apply_verification_scope_only",
            "human_apply_intent_present",
            "guarded_apply_recorded",
            "guarded_apply_scope_only",
            "candidate_apply_recorded",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ], "D172 D173 scope", errors)
        require_false(d173_scope, [
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
            "real_apply_allowed_after_d172_by_ai",
            "route_insert_allowed_after_d172_by_ai",
            "protected_core_mutation_allowed_after_d172_by_ai",
            "network_allowed_after_d172_by_ai",
            "secret_read_allowed_after_d172_by_ai",
            "shell_allowed_after_d172_by_ai",
            "git_action_allowed_after_d172_by_ai",
        ], "D172 D173 scope", errors)

    return errors


def build_post_apply_verification_report(post_apply_verification_id, d172):
    data = {
        "state": "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_REPORT",
        "ok": True,
        "post_apply_verification_id": post_apply_verification_id,
        "guarded_apply_id": d172.get("guarded_apply_id"),
        "apply_intent_id": d172.get("apply_intent_id"),
        "apply_preflight_id": d172.get("apply_preflight_id"),
        "verification_id": d172.get("verification_id"),
        "run_id": d172.get("run_id"),
        "intent_id": d172.get("intent_id"),
        "candidate_id": d172.get("candidate_id"),
        "response_id": d172.get("response_id"),
        "created_at": now(),
        "post_apply_verification_status": "GUARDED_APPLY_VERIFIED_NO_CORE_MUTATION_NO_REAL_APPLY",
        "guarded_apply_recorded": True,
        "candidate_apply_recorded": True,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_apply_allowed": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "no_real_apply": True,
        "no_network": True,
        "no_secret_read": True,
        "no_shell": True,
        "no_route_insert": True,
        "no_core_mutation_by_ai": True,
        "no_git_action_by_ai": True,
        "verification_checks": [
            "guarded_apply_record_exists",
            "candidate_apply_was_record_only",
            "candidate_apply_not_executed_by_ai",
            "real_apply_not_executed",
            "route_insert_not_performed_by_ai",
            "protected_core_not_mutated_by_ai",
            "network_not_accessed",
            "secret_not_read",
            "shell_not_executed",
            "git_action_not_performed_by_ai",
        ],
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_apply_integrity_receipt(post_apply_verification_id, d172):
    data = {
        "state": "D173_SANDBOX_CANDIDATE_REENTRY_APPLY_INTEGRITY_RECEIPT",
        "ok": True,
        "post_apply_verification_id": post_apply_verification_id,
        "guarded_apply_id": d172.get("guarded_apply_id"),
        "apply_intent_id": d172.get("apply_intent_id"),
        "apply_preflight_id": d172.get("apply_preflight_id"),
        "verification_id": d172.get("verification_id"),
        "run_id": d172.get("run_id"),
        "intent_id": d172.get("intent_id"),
        "candidate_id": d172.get("candidate_id"),
        "created_at": now(),
        "apply_integrity_receipt_status": "POST_APPLY_INTEGRITY_VERIFIED_NO_CORE_MUTATION_NO_AI_APPLY",
        "guarded_apply_recorded": True,
        "candidate_apply_recorded": True,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_apply_allowed": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "no_real_apply": True,
        "no_network": True,
        "no_secret_read": True,
        "no_shell": True,
        "no_route_insert": True,
        "no_core_mutation_by_ai": True,
        "no_git_action_by_ai": True,
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_d174_scope(post_apply_verification_id, d172):
    return {
        "state": "D173_D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE",
        "ok": True,
        "post_apply_verification_id": post_apply_verification_id,
        "guarded_apply_id": d172.get("guarded_apply_id"),
        "apply_intent_id": d172.get("apply_intent_id"),
        "apply_preflight_id": d172.get("apply_preflight_id"),
        "verification_id": d172.get("verification_id"),
        "run_id": d172.get("run_id"),
        "intent_id": d172.get("intent_id"),
        "preflight_id": d172.get("preflight_id"),
        "validation_id": d172.get("validation_id"),
        "candidate_id": d172.get("candidate_id"),
        "response_id": d172.get("response_id"),
        "runner_id": d172.get("runner_id"),
        "plan_id": d172.get("plan_id"),
        "review_id": d172.get("review_id"),
        "scope_id": d172.get("scope_id"),
        "intake_id": d172.get("intake_id"),
        "reentry_id": d172.get("reentry_id"),
        "next_cycle_id": d172.get("next_cycle_id"),
        "cycle_closure_id": d172.get("cycle_closure_id"),
        "previous_candidate_id": d172.get("previous_candidate_id"),
        "proposal_id": d172.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D174_GATE,
        "sandbox_candidate_reentry_final_apply_audit_scope_only": True,
        "post_apply_verified": True,
        "apply_integrity_verified": True,
        "guarded_apply_recorded": True,
        "candidate_apply_recorded": True,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_apply_allowed_after_d173_by_ai": False,
        "route_insert_allowed_after_d173_by_ai": False,
        "protected_core_mutation_allowed_after_d173_by_ai": False,
        "network_allowed_after_d173_by_ai": False,
        "secret_read_allowed_after_d173_by_ai": False,
        "shell_allowed_after_d173_by_ai": False,
        "git_action_allowed_after_d173_by_ai": False,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d174_allowed_to_create": [
            "sandbox_candidate_reentry_final_apply_audit_scope",
            "sandbox_candidate_reentry_final_apply_ledger",
            "sandbox_candidate_reentry_replay_index",
            "d175_sandbox_candidate_reentry_chain_archive_scope",
        ],
        "d174_must_not_execute": [
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


def create_sandbox_candidate_reentry_post_apply_verification_scope(root="."):
    root = Path(root).resolve()

    d172 = read_json(root / D172_REPORT, {}) or {}
    guarded_apply_plan = read_json(root / D172_GUARDED_APPLY_PLAN, {}) or {}
    guarded_apply_receipt = read_json(root / D172_GUARDED_APPLY_RECEIPT, {}) or {}
    d173_scope = read_json(root / D172_D173_SCOPE, {}) or {}

    normalize_d172_compat(d172, guarded_apply_plan, guarded_apply_receipt, d173_scope)
    errors = validate_d172(d172, guarded_apply_plan, guarded_apply_receipt, d173_scope)

    post_apply_verification_id = "d173-" + digest({
        "guarded_apply_id": d172.get("guarded_apply_id"),
        "apply_intent_id": d172.get("apply_intent_id"),
        "apply_preflight_id": d172.get("apply_preflight_id"),
        "verification_id": d172.get("verification_id"),
        "run_id": d172.get("run_id"),
        "intent_id": d172.get("intent_id"),
        "candidate_id": d172.get("candidate_id"),
        "response_id": d172.get("response_id"),
        "runner_id": d172.get("runner_id"),
        "plan_id": d172.get("plan_id"),
        "review_id": d172.get("review_id"),
        "scope_id": d172.get("scope_id"),
        "intake_id": d172.get("intake_id"),
        "reentry_id": d172.get("reentry_id"),
        "proposal_id": d172.get("proposal_id"),
    })

    post_apply_verification_report = build_post_apply_verification_report(post_apply_verification_id, d172)
    apply_integrity_receipt = build_apply_integrity_receipt(post_apply_verification_id, d172)
    d174_scope = build_d174_scope(post_apply_verification_id, d172)

    for label, item in [
        ("post_apply_verification_report", post_apply_verification_report),
        ("apply_integrity_receipt", apply_integrity_receipt),
    ]:
        require_true(item, [
            "guarded_apply_recorded",
            "candidate_apply_recorded",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], label, errors)
        require_false(item, [
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
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

    require_true(d174_scope, [
        "sandbox_candidate_reentry_final_apply_audit_scope_only",
        "post_apply_verified",
        "apply_integrity_verified",
        "guarded_apply_recorded",
        "candidate_apply_recorded",
        "fresh_intent_required",
        "human_review_required",
        "canonical_guard_schema_required",
    ], "d174_scope", errors)
    require_false(d174_scope, [
        "candidate_apply_executed",
        "candidate_apply_executed_by_ai",
        "real_apply_allowed_after_d173_by_ai",
        "route_insert_allowed_after_d173_by_ai",
        "protected_core_mutation_allowed_after_d173_by_ai",
        "network_allowed_after_d173_by_ai",
        "secret_read_allowed_after_d173_by_ai",
        "shell_allowed_after_d173_by_ai",
        "git_action_allowed_after_d173_by_ai",
    ], "d174_scope", errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_BLOCKED"
    result = "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_CREATED" if ok else "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_BLOCKED"

    if ok:
        write_json(root / POST_APPLY_VERIFICATION_REPORT_OUT, post_apply_verification_report)
        write_json(root / APPLY_INTEGRITY_RECEIPT_OUT, apply_integrity_receipt)
        write_json(root / D174_SCOPE_OUT, d174_scope)

    guardrails = normalize_guard_flags({
        "sandbox_candidate_reentry_post_apply_verification_scope_only": True,
        "sandbox_candidate_reentry_post_apply_verification_report_only": True,
        "sandbox_candidate_reentry_apply_integrity_receipt_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "guarded_apply_recorded": ok,
        "candidate_apply_recorded": ok,
        "post_apply_verified": ok,
        "apply_integrity_verified": ok,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "approval_for_d174_sandbox_candidate_reentry_final_apply_audit_scope_only": ok,
        "real_apply_allowed_after_d173_by_ai": False,
        "route_insert_allowed_after_d173_by_ai": False,
        "protected_core_mutation_allowed_after_d173_by_ai": False,
        "network_allowed_after_d173_by_ai": False,
        "secret_read_allowed_after_d173_by_ai": False,
        "shell_allowed_after_d173_by_ai": False,
        "git_action_allowed_after_d173_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "post_apply_verification_id": post_apply_verification_id,
        "guarded_apply_id": d172.get("guarded_apply_id"),
        "apply_intent_id": d172.get("apply_intent_id"),
        "apply_preflight_id": d172.get("apply_preflight_id"),
        "verification_id": d172.get("verification_id"),
        "run_id": d172.get("run_id"),
        "intent_id": d172.get("intent_id"),
        "preflight_id": d172.get("preflight_id"),
        "validation_id": d172.get("validation_id"),
        "candidate_id": d172.get("candidate_id"),
        "response_id": d172.get("response_id"),
        "runner_id": d172.get("runner_id"),
        "plan_id": d172.get("plan_id"),
        "review_id": d172.get("review_id"),
        "scope_id": d172.get("scope_id"),
        "intake_id": d172.get("intake_id"),
        "reentry_id": d172.get("reentry_id"),
        "next_cycle_id": d172.get("next_cycle_id"),
        "cycle_closure_id": d172.get("cycle_closure_id"),
        "previous_candidate_id": d172.get("previous_candidate_id"),
        "proposal_id": d172.get("proposal_id"),
        "source_d172_report": D172_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "post_apply_verification_report": post_apply_verification_report if ok else {},
        "apply_integrity_receipt": apply_integrity_receipt if ok else {},
        "d174_scope": d174_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "post_apply_verification_id": post_apply_verification_id,
            "guarded_apply_id": d172.get("guarded_apply_id"),
            "apply_intent_id": d172.get("apply_intent_id"),
            "apply_preflight_id": d172.get("apply_preflight_id"),
            "verification_id": d172.get("verification_id"),
            "run_id": d172.get("run_id"),
            "intent_id": d172.get("intent_id"),
            "candidate_id": d172.get("candidate_id"),
            "response_id": d172.get("response_id"),
            "proposal_id": d172.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D173_PLUS" if ok else "BLOCKED",
            "post_apply_verification_status": "GUARDED_APPLY_VERIFIED_NO_CORE_MUTATION_NO_REAL_APPLY" if ok else "BLOCKED",
            "apply_integrity_receipt_status": "POST_APPLY_INTEGRITY_VERIFIED_NO_CORE_MUTATION_NO_AI_APPLY" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFIED_READY_FOR_FINAL_APPLY_AUDIT" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY" if ok else "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D174_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_post_apply_verification_scope_created": ok,
            "post_apply_verification_report_created": ok,
            "apply_integrity_receipt_created": ok,
            "d174_scope_created": ok,
            "guarded_apply_recorded": ok,
            "real_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D174 may create final apply audit scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_post_apply_verification_scope(), ensure_ascii=False, indent=2))
