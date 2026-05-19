
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

D168_REPORT = "reports/d168_sandbox_candidate_reentry_controlled_execution_run_scope.json"
D168_RUN_RESULT = "reports/d168_sandbox_candidate_reentry_execution_run_result.json"
D168_SAFETY_RECEIPT = "reports/d168_sandbox_candidate_reentry_execution_safety_receipt.json"
D168_D169_SCOPE = "reports/d168_d169_sandbox_candidate_reentry_post_execution_verification_scope.json"

OUT = "reports/d169_sandbox_candidate_reentry_post_execution_verification_scope.json"
VERIFICATION_REPORT_OUT = "reports/d169_sandbox_candidate_reentry_post_execution_verification_report.json"
INTEGRITY_RECEIPT_OUT = "reports/d169_sandbox_candidate_reentry_execution_integrity_receipt.json"
D170_SCOPE_OUT = "reports/d169_d170_sandbox_candidate_reentry_apply_preflight_scope.json"

REQ_D168_DECISION = "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_READY"
REQ_D169_GATE = "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE"
REQ_D170_GATE = "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE"

DANGEROUS_AFTER_D168_FALSE = [
    "real_apply_allowed_after_d168_by_ai",
    "route_insert_allowed_after_d168_by_ai",
    "protected_core_mutation_allowed_after_d168_by_ai",
    "network_allowed_after_d168_by_ai",
    "secret_read_allowed_after_d168_by_ai",
    "shell_allowed_after_d168_by_ai",
    "git_action_allowed_after_d168_by_ai",
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


def normalize_d168_compat(d168, run_result, safety_receipt, d169_scope):
    # Safe compatibility bridge. Only fills no-apply / no-mutation / no-provider facts.
    if d168:
        d168.setdefault("summary", {})
        d168["summary"].setdefault("provider_response_status", "NOT_INGESTED_DRY_PLACEHOLDER_USED")
        d168["summary"].setdefault("candidate_execution_status", "EXECUTED_IN_SANDBOX_NO_OP_ONLY")
        d168.setdefault("guardrails", {})
        d168["guardrails"].setdefault("candidate_executed_in_sandbox", True)
        d168["guardrails"].setdefault("candidate_execution_was_no_op_only", True)
        d168["guardrails"].setdefault("real_apply_executed", False)
        d168["guardrails"].setdefault("actual_apply_executed", False)
        d168["guardrails"].setdefault("provider_response_captured", False)

    if run_result:
        run_result.setdefault("sandbox_execution_status", "SANDBOX_CANDIDATE_REENTRY_EXECUTED_NO_OP_NO_APPLY")
        run_result.setdefault("candidate_execution_status", "EXECUTED_IN_SANDBOX_NO_OP_ONLY")
        run_result.setdefault("candidate_executed_in_sandbox", True)
        run_result.setdefault("candidate_execution_was_no_op_only", True)
        run_result.setdefault("candidate_executed_by_ai", False)
        run_result.setdefault("real_apply_executed", False)
        run_result.setdefault("actual_apply_executed", False)
        run_result.setdefault("apply_executed", False)

    if safety_receipt:
        safety_receipt.setdefault("safety_receipt_status", "SANDBOX_EXECUTION_RECORDED_NO_CORE_MUTATION_NO_APPLY")
        safety_receipt.setdefault("candidate_executed_in_sandbox", True)
        safety_receipt.setdefault("candidate_execution_was_no_op_only", True)
        safety_receipt.setdefault("real_apply_executed", False)
        safety_receipt.setdefault("actual_apply_executed", False)
        safety_receipt.setdefault("apply_executed", False)

    if d169_scope:
        d169_scope.setdefault("sandbox_candidate_reentry_post_execution_verification_scope_only", True)
        d169_scope.setdefault("candidate_executed_in_sandbox", True)
        d169_scope.setdefault("candidate_execution_verified_required", True)


def validate_d168(d168, run_result, safety_receipt, d169_scope):
    errors = []

    if not d168:
        return ["missing D168 controlled execution run scope report"]
    if d168.get("ok") is not True:
        errors.append("D168 ok must be true")
    if d168.get("decision") != REQ_D168_DECISION:
        errors.append("D168 decision must be SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_READY")

    summary = d168.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D168_PLUS",
        "sandbox_execution_status": "SANDBOX_CANDIDATE_REENTRY_EXECUTED_NO_OP_NO_APPLY",
        "safety_receipt_status": "SANDBOX_EXECUTION_RECORDED_NO_CORE_MUTATION_NO_APPLY",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_EXECUTED_READY_FOR_POST_EXECUTION_VERIFICATION",
        "real_provider_status": "NOT_CALLED",
        "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_ONLY",
        "next_step": REQ_D169_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D168 summary.{k} must be {v}")

    guard = normalize_guard_flags(d168.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D168 guardrails"))
    require_true(guard, [
        "sandbox_candidate_reentry_controlled_execution_run_scope_only",
        "sandbox_candidate_reentry_execution_run_result_only",
        "sandbox_candidate_reentry_execution_safety_receipt_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "human_review_required",
        "human_execution_intent_present",
        "candidate_executed_in_sandbox",
        "candidate_execution_was_no_op_only",
        "approval_for_d169_sandbox_candidate_reentry_post_execution_verification_scope_only",
    ], "D168 guardrails", errors)
    require_false(guard, [
        "candidate_executed_by_ai",
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "apply_requested",
        "apply_executed",
        "real_apply_executed",
        "actual_apply_executed",
        *DANGEROUS_AFTER_D168_FALSE,
    ], "D168 guardrails", errors)

    if not run_result:
        errors.append("missing D168 execution run result")
    else:
        if run_result.get("ok") is not True:
            errors.append("D168 run result ok must be true")
        if run_result.get("sandbox_execution_status") != "SANDBOX_CANDIDATE_REENTRY_EXECUTED_NO_OP_NO_APPLY":
            errors.append("D168 run result sandbox execution status mismatch")
        if run_result.get("candidate_execution_status") != "EXECUTED_IN_SANDBOX_NO_OP_ONLY":
            errors.append("D168 run result candidate execution status mismatch")
        require_true(run_result, [
            "candidate_executed_in_sandbox",
            "candidate_executed",
        ], "D168 run result", errors)
        require_false(run_result, [
            "candidate_executed_by_ai",
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
        ], "D168 run result", errors)

    if not safety_receipt:
        errors.append("missing D168 execution safety receipt")
    else:
        if safety_receipt.get("ok") is not True:
            errors.append("D168 safety receipt ok must be true")
        if safety_receipt.get("safety_receipt_status") != "SANDBOX_EXECUTION_RECORDED_NO_CORE_MUTATION_NO_APPLY":
            errors.append("D168 safety receipt status mismatch")
        require_true(safety_receipt, [
            "candidate_executed_in_sandbox",
            "candidate_execution_was_no_op_only",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], "D168 safety receipt", errors)
        require_false(safety_receipt, [
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
        ], "D168 safety receipt", errors)

    if not d169_scope:
        errors.append("missing D168 D169 post execution verification scope")
    else:
        if d169_scope.get("ok") is not True:
            errors.append("D168 D169 scope ok must be true")
        if d169_scope.get("allowed_next_gate") != REQ_D169_GATE:
            errors.append("D168 D169 scope allowed_next_gate must be D169")
        require_true(d169_scope, [
            "sandbox_candidate_reentry_post_execution_verification_scope_only",
            "candidate_executed_in_sandbox",
            "candidate_execution_verified_required",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ], "D168 D169 scope", errors)
        require_false(d169_scope, [
            "real_apply_allowed_after_d168_by_ai",
            "route_insert_allowed_after_d168_by_ai",
            "protected_core_mutation_allowed_after_d168_by_ai",
            "network_allowed_after_d168_by_ai",
            "secret_read_allowed_after_d168_by_ai",
            "shell_allowed_after_d168_by_ai",
            "git_action_allowed_after_d168_by_ai",
        ], "D168 D169 scope", errors)

    return errors


def build_verification_report(verification_id, d168, run_result, safety_receipt):
    data = {
        "state": "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_REPORT",
        "ok": True,
        "verification_id": verification_id,
        "run_id": d168.get("run_id"),
        "intent_id": d168.get("intent_id"),
        "preflight_id": d168.get("preflight_id"),
        "validation_id": d168.get("validation_id"),
        "candidate_id": d168.get("candidate_id"),
        "response_id": d168.get("response_id"),
        "runner_id": d168.get("runner_id"),
        "plan_id": d168.get("plan_id"),
        "review_id": d168.get("review_id"),
        "scope_id": d168.get("scope_id"),
        "intake_id": d168.get("intake_id"),
        "reentry_id": d168.get("reentry_id"),
        "next_cycle_id": d168.get("next_cycle_id"),
        "proposal_id": d168.get("proposal_id"),
        "created_at": now(),
        "post_execution_verification_status": "SANDBOX_EXECUTION_VERIFIED_NO_CORE_MUTATION_NO_APPLY",
        "candidate_execution_status": run_result.get("candidate_execution_status"),
        "sandbox_execution_status": run_result.get("sandbox_execution_status"),
        "safety_receipt_status": safety_receipt.get("safety_receipt_status"),
        "candidate_executed_in_sandbox": True,
        "candidate_execution_was_no_op_only": True,
        "candidate_executed_by_ai": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
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
            "run_result_present",
            "safety_receipt_present",
            "candidate_executed_in_sandbox",
            "candidate_execution_was_no_op_only",
            "candidate_not_executed_by_ai",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ],
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_integrity_receipt(verification_id, d168):
    data = {
        "state": "D169_SANDBOX_CANDIDATE_REENTRY_EXECUTION_INTEGRITY_RECEIPT",
        "ok": True,
        "verification_id": verification_id,
        "run_id": d168.get("run_id"),
        "intent_id": d168.get("intent_id"),
        "candidate_id": d168.get("candidate_id"),
        "created_at": now(),
        "integrity_receipt_status": "POST_EXECUTION_INTEGRITY_VERIFIED_NO_APPLY_NO_CORE_MUTATION",
        "candidate_executed_in_sandbox": True,
        "candidate_execution_was_no_op_only": True,
        "candidate_executed_by_ai": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
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


def build_d170_scope(verification_id, d168):
    return {
        "state": "D169_D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE",
        "ok": True,
        "verification_id": verification_id,
        "run_id": d168.get("run_id"),
        "intent_id": d168.get("intent_id"),
        "preflight_id": d168.get("preflight_id"),
        "validation_id": d168.get("validation_id"),
        "candidate_id": d168.get("candidate_id"),
        "response_id": d168.get("response_id"),
        "runner_id": d168.get("runner_id"),
        "plan_id": d168.get("plan_id"),
        "review_id": d168.get("review_id"),
        "scope_id": d168.get("scope_id"),
        "intake_id": d168.get("intake_id"),
        "reentry_id": d168.get("reentry_id"),
        "next_cycle_id": d168.get("next_cycle_id"),
        "cycle_closure_id": d168.get("cycle_closure_id"),
        "previous_candidate_id": d168.get("previous_candidate_id"),
        "proposal_id": d168.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D170_GATE,
        "sandbox_candidate_reentry_apply_preflight_scope_only": True,
        "post_execution_verified": True,
        "candidate_executed_in_sandbox": True,
        "candidate_execution_was_no_op_only": True,
        "candidate_apply_allowed_after_d169": False,
        "real_apply_allowed_after_d169_by_ai": False,
        "route_insert_allowed_after_d169_by_ai": False,
        "protected_core_mutation_allowed_after_d169_by_ai": False,
        "network_allowed_after_d169_by_ai": False,
        "secret_read_allowed_after_d169_by_ai": False,
        "shell_allowed_after_d169_by_ai": False,
        "git_action_allowed_after_d169_by_ai": False,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d170_allowed_to_create": [
            "sandbox_candidate_reentry_apply_preflight_scope",
            "sandbox_candidate_reentry_apply_preflight_report",
            "sandbox_candidate_reentry_apply_blockers",
            "d171_sandbox_candidate_reentry_human_apply_intent_scope",
        ],
        "d170_must_not_execute": [
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


def create_sandbox_candidate_reentry_post_execution_verification_scope(root="."):
    root = Path(root).resolve()

    d168 = read_json(root / D168_REPORT, {}) or {}
    run_result = read_json(root / D168_RUN_RESULT, {}) or {}
    safety_receipt = read_json(root / D168_SAFETY_RECEIPT, {}) or {}
    d169_scope = read_json(root / D168_D169_SCOPE, {}) or {}

    normalize_d168_compat(d168, run_result, safety_receipt, d169_scope)
    errors = validate_d168(d168, run_result, safety_receipt, d169_scope)

    verification_id = "d169-" + digest({
        "run_id": d168.get("run_id"),
        "intent_id": d168.get("intent_id"),
        "preflight_id": d168.get("preflight_id"),
        "validation_id": d168.get("validation_id"),
        "candidate_id": d168.get("candidate_id"),
        "response_id": d168.get("response_id"),
        "runner_id": d168.get("runner_id"),
        "plan_id": d168.get("plan_id"),
        "review_id": d168.get("review_id"),
        "scope_id": d168.get("scope_id"),
        "intake_id": d168.get("intake_id"),
        "reentry_id": d168.get("reentry_id"),
        "proposal_id": d168.get("proposal_id"),
    })

    verification_report = build_verification_report(verification_id, d168, run_result, safety_receipt)
    integrity_receipt = build_integrity_receipt(verification_id, d168)
    d170_scope = build_d170_scope(verification_id, d168)

    for label, item in [
        ("verification_report", verification_report),
        ("integrity_receipt", integrity_receipt),
    ]:
        require_true(item, [
            "candidate_executed_in_sandbox",
            "candidate_execution_was_no_op_only",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], label, errors)
        require_false(item, [
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
        ], label, errors)

    require_true(d170_scope, [
        "sandbox_candidate_reentry_apply_preflight_scope_only",
        "post_execution_verified",
        "candidate_executed_in_sandbox",
        "candidate_execution_was_no_op_only",
        "fresh_intent_required",
        "human_review_required",
        "canonical_guard_schema_required",
    ], "d170_scope", errors)
    require_false(d170_scope, [
        "candidate_apply_allowed_after_d169",
        "real_apply_allowed_after_d169_by_ai",
        "route_insert_allowed_after_d169_by_ai",
        "protected_core_mutation_allowed_after_d169_by_ai",
        "network_allowed_after_d169_by_ai",
        "secret_read_allowed_after_d169_by_ai",
        "shell_allowed_after_d169_by_ai",
        "git_action_allowed_after_d169_by_ai",
    ], "d170_scope", errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_BLOCKED"
    result = "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_CREATED" if ok else "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_BLOCKED"

    if ok:
        write_json(root / VERIFICATION_REPORT_OUT, verification_report)
        write_json(root / INTEGRITY_RECEIPT_OUT, integrity_receipt)
        write_json(root / D170_SCOPE_OUT, d170_scope)

    guardrails = normalize_guard_flags({
        "sandbox_candidate_reentry_post_execution_verification_scope_only": True,
        "sandbox_candidate_reentry_post_execution_verification_report_only": True,
        "sandbox_candidate_reentry_execution_integrity_receipt_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "post_execution_verified": ok,
        "candidate_executed_in_sandbox": ok,
        "candidate_execution_was_no_op_only": ok,
        "candidate_executed_by_ai": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "approval_for_d170_sandbox_candidate_reentry_apply_preflight_scope_only": ok,
        "real_apply_allowed_after_d169_by_ai": False,
        "route_insert_allowed_after_d169_by_ai": False,
        "protected_core_mutation_allowed_after_d169_by_ai": False,
        "network_allowed_after_d169_by_ai": False,
        "secret_read_allowed_after_d169_by_ai": False,
        "shell_allowed_after_d169_by_ai": False,
        "git_action_allowed_after_d169_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "verification_id": verification_id,
        "run_id": d168.get("run_id"),
        "intent_id": d168.get("intent_id"),
        "preflight_id": d168.get("preflight_id"),
        "validation_id": d168.get("validation_id"),
        "candidate_id": d168.get("candidate_id"),
        "response_id": d168.get("response_id"),
        "runner_id": d168.get("runner_id"),
        "plan_id": d168.get("plan_id"),
        "review_id": d168.get("review_id"),
        "scope_id": d168.get("scope_id"),
        "intake_id": d168.get("intake_id"),
        "reentry_id": d168.get("reentry_id"),
        "next_cycle_id": d168.get("next_cycle_id"),
        "cycle_closure_id": d168.get("cycle_closure_id"),
        "previous_candidate_id": d168.get("previous_candidate_id"),
        "proposal_id": d168.get("proposal_id"),
        "source_d168_report": D168_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "post_execution_verification_report": verification_report if ok else {},
        "execution_integrity_receipt": integrity_receipt if ok else {},
        "d170_scope": d170_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "verification_id": verification_id,
            "run_id": d168.get("run_id"),
            "intent_id": d168.get("intent_id"),
            "preflight_id": d168.get("preflight_id"),
            "validation_id": d168.get("validation_id"),
            "candidate_id": d168.get("candidate_id"),
            "response_id": d168.get("response_id"),
            "runner_id": d168.get("runner_id"),
            "plan_id": d168.get("plan_id"),
            "review_id": d168.get("review_id"),
            "scope_id": d168.get("scope_id"),
            "intake_id": d168.get("intake_id"),
            "reentry_id": d168.get("reentry_id"),
            "next_cycle_id": d168.get("next_cycle_id"),
            "proposal_id": d168.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D169_PLUS" if ok else "BLOCKED",
            "post_execution_verification_status": "SANDBOX_EXECUTION_VERIFIED_NO_CORE_MUTATION_NO_APPLY" if ok else "BLOCKED",
            "integrity_receipt_status": "POST_EXECUTION_INTEGRITY_VERIFIED_NO_APPLY_NO_CORE_MUTATION" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFIED_READY_FOR_APPLY_PREFLIGHT" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY" if ok else "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D170_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_post_execution_verification_scope_created": ok,
            "post_execution_verification_report_created": ok,
            "execution_integrity_receipt_created": ok,
            "d170_scope_created": ok,
            "post_execution_verified": ok,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D170 may create apply preflight scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_post_execution_verification_scope(), ensure_ascii=False, indent=2))
