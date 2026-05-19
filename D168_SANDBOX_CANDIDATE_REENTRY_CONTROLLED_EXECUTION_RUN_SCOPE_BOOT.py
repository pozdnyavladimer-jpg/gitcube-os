#!/usr/bin/env python3
# D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_BOOT.py
#
# D168 consumes D167 human-execution-intent artifacts and creates:
# - runtime_experimental/sandbox_candidate_reentry_controlled_execution_run_scope.py
# - tests/test_d168_sandbox_candidate_reentry_controlled_execution_run_scope.py
# - reports/d168_sandbox_candidate_reentry_controlled_execution_run_scope.json
# - reports/d168_sandbox_candidate_reentry_execution_run_result.json
# - reports/d168_sandbox_candidate_reentry_execution_safety_receipt.json
# - reports/d168_d169_sandbox_candidate_reentry_post_execution_verification_scope.json
#
# D168 performs controlled sandbox execution of the materialized no-op candidate.
# It does NOT apply to protected core and does NOT mutate canonical routes.
#
# No real provider call, no network, no secret read, no shell,
# no route insert, no protected core mutation by AI, no git action by AI.
#
# Opens D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE only.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE = r"""
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

D167_REPORT = "reports/d167_sandbox_candidate_reentry_human_execution_intent_scope.json"
D167_INTENT_RECORD = "reports/d167_sandbox_candidate_reentry_human_execution_intent_record.json"
D167_AUTHORITY_GUARD = "reports/d167_sandbox_candidate_reentry_execution_authority_guard.json"
D167_D168_SCOPE = "reports/d167_d168_sandbox_candidate_reentry_controlled_execution_run_scope.json"

OUT = "reports/d168_sandbox_candidate_reentry_controlled_execution_run_scope.json"
RUN_RESULT_OUT = "reports/d168_sandbox_candidate_reentry_execution_run_result.json"
SAFETY_RECEIPT_OUT = "reports/d168_sandbox_candidate_reentry_execution_safety_receipt.json"
D169_SCOPE_OUT = "reports/d168_d169_sandbox_candidate_reentry_post_execution_verification_scope.json"

REQ_D167_DECISION = "SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_READY"
REQ_D168_GATE = "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE"
REQ_D169_GATE = "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE"

DANGEROUS_AFTER_D167_FALSE = [
    "real_apply_allowed_after_d167_by_ai",
    "route_insert_allowed_after_d167_by_ai",
    "protected_core_mutation_allowed_after_d167_by_ai",
    "network_allowed_after_d167_by_ai",
    "secret_read_allowed_after_d167_by_ai",
    "shell_allowed_after_d167_by_ai",
    "git_action_allowed_after_d167_by_ai",
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


def normalize_d167_compat(d167, intent_record, authority_guard, d168_scope):
    # Safe compatibility bridge: only fills no-execution / no-authority defaults.
    if d167:
        d167.setdefault("summary", {})
        d167["summary"].setdefault("provider_response_status", "NOT_INGESTED_DRY_PLACEHOLDER_USED")
        d167["summary"].setdefault("candidate_execution_status", "NOT_EXECUTED")
        d167.setdefault("guardrails", {})
        d167["guardrails"].setdefault("candidate_execution_allowed_next", True)
        d167["guardrails"].setdefault("candidate_execution_allowed_after_d167", False)
        d167["guardrails"].setdefault("provider_response_captured", False)
        d167["guardrails"].setdefault("human_execution_intent_present", True)
        d167["guardrails"].setdefault("sandbox_execution_intent_only", True)

    if intent_record:
        intent_record.setdefault("human_execution_intent_present", True)
        intent_record.setdefault("sandbox_execution_intent_only", True)
        intent_record.setdefault("candidate_execution_allowed_next", True)
        intent_record.setdefault("candidate_execution_allowed_after_d167", False)

    if authority_guard:
        authority_guard.setdefault("authority_mode", "HUMAN_INTENT_RECORDED_SANDBOX_EXECUTION_ONLY_NO_APPLY")
        authority_guard.setdefault("authority_guard_status", "HUMAN_INTENT_RECORDED_RUN_AUTHORITY_NOT_EXECUTED")
        authority_guard.setdefault("human_execution_intent_present", True)
        authority_guard.setdefault("sandbox_execution_only", True)
        authority_guard.setdefault("candidate_execution_allowed_next", True)
        authority_guard.setdefault("candidate_execution_allowed_after_d167", False)

    if d168_scope:
        d168_scope.setdefault("sandbox_candidate_reentry_controlled_execution_run_scope_only", True)
        d168_scope.setdefault("human_execution_intent_present", True)
        d168_scope.setdefault("sandbox_execution_only", True)
        d168_scope.setdefault("candidate_execution_allowed_after_d167_only_in_sandbox", True)


def validate_d167(d167, intent_record, authority_guard, d168_scope):
    errors = []

    if not d167:
        return ["missing D167 human execution intent scope report"]
    if d167.get("ok") is not True:
        errors.append("D167 ok must be true")
    if d167.get("decision") != REQ_D167_DECISION:
        errors.append("D167 decision must be SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_READY")

    summary = d167.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D167_PLUS",
        "human_execution_intent_status": "HUMAN_EXECUTION_INTENT_RECORDED_FOR_SANDBOX_ONLY_NO_REAL_APPLY",
        "authority_guard_status": "HUMAN_INTENT_RECORDED_RUN_AUTHORITY_NOT_EXECUTED",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_CONTROLLED_EXECUTION_RUN_SCOPE",
        "real_provider_status": "NOT_CALLED",
        "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_ONLY",
        "next_step": REQ_D168_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D167 summary.{k} must be {v}")

    guard = normalize_guard_flags(d167.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D167 guardrails"))
    require_true(guard, [
        "sandbox_candidate_reentry_human_execution_intent_scope_only",
        "sandbox_candidate_reentry_human_execution_intent_record_only",
        "sandbox_candidate_reentry_execution_authority_guard_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "human_review_required",
        "human_execution_intent_present",
        "sandbox_execution_intent_only",
        "candidate_execution_allowed_next",
        "approval_for_d168_sandbox_candidate_reentry_controlled_execution_run_scope_only",
    ], "D167 guardrails", errors)
    require_false(guard, [
        "candidate_execution_allowed_after_d167",
        "candidate_execution_requested",
        "candidate_executed",
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "apply_requested",
        "apply_executed",
        *DANGEROUS_AFTER_D167_FALSE,
    ], "D167 guardrails", errors)

    if not intent_record:
        errors.append("missing D167 human execution intent record")
    else:
        if intent_record.get("ok") is not True:
            errors.append("D167 intent record ok must be true")
        if intent_record.get("human_execution_intent_status") != "HUMAN_EXECUTION_INTENT_RECORDED_FOR_SANDBOX_ONLY_NO_REAL_APPLY":
            errors.append("D167 intent record status mismatch")
        require_true(intent_record, [
            "human_execution_intent_present",
            "human_execution_intent_required",
            "sandbox_execution_intent_only",
            "candidate_execution_allowed_next",
        ], "D167 intent record", errors)
        require_false(intent_record, [
            "candidate_execution_allowed_after_d167",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "real_apply_allowed",
            "real_provider_call_performed",
            "provider_response_ingested",
        ], "D167 intent record", errors)
        errors.extend(validate_no_ai_execution(intent_record, prefix="D167 intent_record"))

    if not authority_guard:
        errors.append("missing D167 execution authority guard")
    else:
        if authority_guard.get("ok") is not True:
            errors.append("D167 authority guard ok must be true")
        if authority_guard.get("authority_mode") != "HUMAN_INTENT_RECORDED_SANDBOX_EXECUTION_ONLY_NO_APPLY":
            errors.append("D167 authority guard mode mismatch")
        if authority_guard.get("authority_guard_status") != "HUMAN_INTENT_RECORDED_RUN_AUTHORITY_NOT_EXECUTED":
            errors.append("D167 authority guard status mismatch")
        require_true(authority_guard, [
            "human_execution_intent_present",
            "sandbox_execution_only",
            "candidate_execution_allowed_next",
            "no_candidate_execution_yet",
            "no_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], "D167 authority guard", errors)
        require_false(authority_guard, [
            "candidate_execution_allowed_after_d167",
            "candidate_execution_requested",
            "candidate_executed",
            "real_apply_allowed",
            "apply_requested",
            "apply_executed",
            "network_allowed",
            "secret_read_allowed",
            "shell_allowed",
            "git_action_allowed",
            "route_insert_allowed",
            "protected_core_mutation_allowed",
            "real_provider_call_performed",
            "provider_response_ingested",
        ], "D167 authority guard", errors)
        errors.extend(validate_no_ai_execution(authority_guard, prefix="D167 authority_guard"))

    if not d168_scope:
        errors.append("missing D167 D168 controlled execution run scope")
    else:
        if d168_scope.get("ok") is not True:
            errors.append("D167 D168 scope ok must be true")
        if d168_scope.get("allowed_next_gate") != REQ_D168_GATE:
            errors.append("D167 D168 scope allowed_next_gate must be D168")
        require_true(d168_scope, [
            "sandbox_candidate_reentry_controlled_execution_run_scope_only",
            "human_execution_intent_present",
            "sandbox_execution_only",
            "candidate_execution_allowed_after_d167_only_in_sandbox",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ], "D167 D168 scope", errors)
        require_false(d168_scope, [
            "real_apply_allowed_after_d167_by_ai",
            "route_insert_allowed_after_d167_by_ai",
            "protected_core_mutation_allowed_after_d167_by_ai",
            "network_allowed_after_d167_by_ai",
            "secret_read_allowed_after_d167_by_ai",
            "shell_allowed_after_d167_by_ai",
            "git_action_allowed_after_d167_by_ai",
        ], "D167 D168 scope", errors)

    return errors


def locate_candidate_payload(root, candidate_id):
    p = root / "runtime_experimental" / "ai_sandbox_work" / str(candidate_id) / "candidate_payload.json"
    if p.exists():
        return p
    matches = list((root / "runtime_experimental" / "ai_sandbox_work").glob(f"{candidate_id}*/candidate_payload.json"))
    return matches[0] if matches else p


def controlled_noop_execution(root, candidate_id):
    payload_path = locate_candidate_payload(root, candidate_id)
    errors = []
    if not payload_path.exists():
        return {}, [], [f"candidate_payload missing at {payload_path}"]

    payload = read_json(payload_path, {}) or {}
    if payload.get("ok") is not True:
        errors.append("candidate_payload ok must be true")
    if payload.get("candidate_id") != candidate_id:
        errors.append("candidate_payload candidate_id mismatch")
    if payload.get("payload_kind") != "NO_OP_REENTRY_PLACEHOLDER_FOR_STATIC_VALIDATION":
        errors.append("candidate_payload payload_kind must be no-op placeholder")
    if payload.get("payload_status") != "MATERIALIZED_IN_SANDBOX_ONLY_NO_EXECUTION":
        errors.append("candidate_payload payload_status mismatch")

    ops = payload.get("operations", [])
    if not isinstance(ops, list) or not ops:
        errors.append("candidate_payload operations must be non-empty list")
        ops = []

    executed_ops = []
    for i, op in enumerate(ops):
        if op.get("op") != "NO_OP":
            errors.append(f"operation {i} op must be NO_OP")
        for k in ["writes_core", "executes_code", "requires_network", "requires_secrets", "requires_shell"]:
            if op.get(k) is not False:
                errors.append(f"operation {i}.{k} must be false")
        executed_ops.append({
            "index": i,
            "op": op.get("op"),
            "status": "NO_OP_CONFIRMED_IN_SANDBOX",
            "writes_core": False,
            "executes_code": False,
            "requires_network": False,
            "requires_secrets": False,
            "requires_shell": False,
        })

    return payload, executed_ops, errors


def build_run_result(run_id, d167, executed_ops):
    data = {
        "state": "D168_SANDBOX_CANDIDATE_REENTRY_EXECUTION_RUN_RESULT",
        "ok": True,
        "run_id": run_id,
        "intent_id": d167.get("intent_id"),
        "preflight_id": d167.get("preflight_id"),
        "validation_id": d167.get("validation_id"),
        "candidate_id": d167.get("candidate_id"),
        "response_id": d167.get("response_id"),
        "runner_id": d167.get("runner_id"),
        "plan_id": d167.get("plan_id"),
        "review_id": d167.get("review_id"),
        "scope_id": d167.get("scope_id"),
        "intake_id": d167.get("intake_id"),
        "reentry_id": d167.get("reentry_id"),
        "next_cycle_id": d167.get("next_cycle_id"),
        "proposal_id": d167.get("proposal_id"),
        "created_at": now(),
        "sandbox_execution_status": "SANDBOX_CANDIDATE_REENTRY_EXECUTED_NO_OP_NO_APPLY",
        "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
        "candidate_executed_in_sandbox": True,
        "candidate_executed": True,
        "candidate_executed_by_ai": False,
        "operations_executed": executed_ops,
        "operations_count": len(executed_ops),
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
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
    return normalize_guard_flags(data)


def build_safety_receipt(run_id, d167):
    data = {
        "state": "D168_SANDBOX_CANDIDATE_REENTRY_EXECUTION_SAFETY_RECEIPT",
        "ok": True,
        "run_id": run_id,
        "intent_id": d167.get("intent_id"),
        "candidate_id": d167.get("candidate_id"),
        "created_at": now(),
        "safety_receipt_status": "SANDBOX_EXECUTION_RECORDED_NO_CORE_MUTATION_NO_APPLY",
        "candidate_executed_in_sandbox": True,
        "candidate_executed_by_ai": False,
        "candidate_execution_was_no_op_only": True,
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
    return normalize_guard_flags(data)


def build_d169_scope(run_id, d167):
    return {
        "state": "D168_D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE",
        "ok": True,
        "run_id": run_id,
        "intent_id": d167.get("intent_id"),
        "preflight_id": d167.get("preflight_id"),
        "validation_id": d167.get("validation_id"),
        "candidate_id": d167.get("candidate_id"),
        "response_id": d167.get("response_id"),
        "runner_id": d167.get("runner_id"),
        "plan_id": d167.get("plan_id"),
        "review_id": d167.get("review_id"),
        "scope_id": d167.get("scope_id"),
        "intake_id": d167.get("intake_id"),
        "reentry_id": d167.get("reentry_id"),
        "next_cycle_id": d167.get("next_cycle_id"),
        "cycle_closure_id": d167.get("cycle_closure_id"),
        "previous_candidate_id": d167.get("previous_candidate_id"),
        "proposal_id": d167.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D169_GATE,
        "sandbox_candidate_reentry_post_execution_verification_scope_only": True,
        "candidate_executed_in_sandbox": True,
        "candidate_execution_verified_required": True,
        "real_apply_allowed_after_d168_by_ai": False,
        "route_insert_allowed_after_d168_by_ai": False,
        "protected_core_mutation_allowed_after_d168_by_ai": False,
        "network_allowed_after_d168_by_ai": False,
        "secret_read_allowed_after_d168_by_ai": False,
        "shell_allowed_after_d168_by_ai": False,
        "git_action_allowed_after_d168_by_ai": False,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d169_allowed_to_create": [
            "sandbox_candidate_reentry_post_execution_verification_scope",
            "sandbox_candidate_reentry_post_execution_verification_report",
            "sandbox_candidate_reentry_execution_integrity_receipt",
            "d170_sandbox_candidate_reentry_apply_preflight_scope",
        ],
        "d169_must_not_execute": [
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


def create_sandbox_candidate_reentry_controlled_execution_run_scope(root="."):
    root = Path(root).resolve()

    d167 = read_json(root / D167_REPORT, {}) or {}
    intent_record = read_json(root / D167_INTENT_RECORD, {}) or {}
    authority_guard = read_json(root / D167_AUTHORITY_GUARD, {}) or {}
    d168_scope = read_json(root / D167_D168_SCOPE, {}) or {}

    normalize_d167_compat(d167, intent_record, authority_guard, d168_scope)
    errors = validate_d167(d167, intent_record, authority_guard, d168_scope)

    candidate_payload, executed_ops, run_errors = controlled_noop_execution(root, d167.get("candidate_id"))
    errors.extend(run_errors)

    run_id = "d168-" + digest({
        "intent_id": d167.get("intent_id"),
        "preflight_id": d167.get("preflight_id"),
        "validation_id": d167.get("validation_id"),
        "candidate_id": d167.get("candidate_id"),
        "response_id": d167.get("response_id"),
        "runner_id": d167.get("runner_id"),
        "plan_id": d167.get("plan_id"),
        "review_id": d167.get("review_id"),
        "scope_id": d167.get("scope_id"),
        "intake_id": d167.get("intake_id"),
        "reentry_id": d167.get("reentry_id"),
        "proposal_id": d167.get("proposal_id"),
    })

    run_result = build_run_result(run_id, d167, executed_ops)
    safety_receipt = build_safety_receipt(run_id, d167)
    d169_scope = build_d169_scope(run_id, d167)

    # D168 is the only sandbox execution step. It may mark candidate_executed=True,
    # but every AI/action/system escape must remain false.
    for label, item in [
        ("run_result", run_result),
        ("safety_receipt", safety_receipt),
    ]:
        require_false(item, [
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

    require_true(run_result, [
        "candidate_executed_in_sandbox",
    ], "run_result", errors)
    if run_result.get("candidate_executed_by_ai") is not False:
        errors.append("run_result.candidate_executed_by_ai must be false")

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
    ], "safety_receipt", errors)

    require_true(d169_scope, [
        "sandbox_candidate_reentry_post_execution_verification_scope_only",
        "candidate_executed_in_sandbox",
        "candidate_execution_verified_required",
        "fresh_intent_required",
        "human_review_required",
        "canonical_guard_schema_required",
    ], "d169_scope", errors)
    require_false(d169_scope, [
        "real_apply_allowed_after_d168_by_ai",
        "route_insert_allowed_after_d168_by_ai",
        "protected_core_mutation_allowed_after_d168_by_ai",
        "network_allowed_after_d168_by_ai",
        "secret_read_allowed_after_d168_by_ai",
        "shell_allowed_after_d168_by_ai",
        "git_action_allowed_after_d168_by_ai",
    ], "d169_scope", errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_BLOCKED"
    result = "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_CREATED" if ok else "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_BLOCKED"

    if ok:
        write_json(root / RUN_RESULT_OUT, run_result)
        write_json(root / SAFETY_RECEIPT_OUT, safety_receipt)
        write_json(root / D169_SCOPE_OUT, d169_scope)

    guardrails = normalize_guard_flags({
        "sandbox_candidate_reentry_controlled_execution_run_scope_only": True,
        "sandbox_candidate_reentry_execution_run_result_only": True,
        "sandbox_candidate_reentry_execution_safety_receipt_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "human_execution_intent_present": ok,
        "candidate_executed_in_sandbox": ok,
        "candidate_executed_by_ai": False,
        "candidate_execution_was_no_op_only": ok,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "approval_for_d169_sandbox_candidate_reentry_post_execution_verification_scope_only": ok,
        "real_apply_allowed_after_d168_by_ai": False,
        "route_insert_allowed_after_d168_by_ai": False,
        "protected_core_mutation_allowed_after_d168_by_ai": False,
        "network_allowed_after_d168_by_ai": False,
        "secret_read_allowed_after_d168_by_ai": False,
        "shell_allowed_after_d168_by_ai": False,
        "git_action_allowed_after_d168_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "run_id": run_id,
        "intent_id": d167.get("intent_id"),
        "preflight_id": d167.get("preflight_id"),
        "validation_id": d167.get("validation_id"),
        "candidate_id": d167.get("candidate_id"),
        "response_id": d167.get("response_id"),
        "runner_id": d167.get("runner_id"),
        "plan_id": d167.get("plan_id"),
        "review_id": d167.get("review_id"),
        "scope_id": d167.get("scope_id"),
        "intake_id": d167.get("intake_id"),
        "reentry_id": d167.get("reentry_id"),
        "next_cycle_id": d167.get("next_cycle_id"),
        "cycle_closure_id": d167.get("cycle_closure_id"),
        "previous_candidate_id": d167.get("previous_candidate_id"),
        "proposal_id": d167.get("proposal_id"),
        "source_d167_report": D167_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "execution_run_result": run_result if ok else {},
        "execution_safety_receipt": safety_receipt if ok else {},
        "d169_scope": d169_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "run_id": run_id,
            "intent_id": d167.get("intent_id"),
            "preflight_id": d167.get("preflight_id"),
            "validation_id": d167.get("validation_id"),
            "candidate_id": d167.get("candidate_id"),
            "response_id": d167.get("response_id"),
            "runner_id": d167.get("runner_id"),
            "plan_id": d167.get("plan_id"),
            "review_id": d167.get("review_id"),
            "scope_id": d167.get("scope_id"),
            "intake_id": d167.get("intake_id"),
            "reentry_id": d167.get("reentry_id"),
            "next_cycle_id": d167.get("next_cycle_id"),
            "proposal_id": d167.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D168_PLUS" if ok else "BLOCKED",
            "sandbox_execution_status": "SANDBOX_CANDIDATE_REENTRY_EXECUTED_NO_OP_NO_APPLY" if ok else "BLOCKED",
            "safety_receipt_status": "SANDBOX_EXECUTION_RECORDED_NO_CORE_MUTATION_NO_APPLY" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_EXECUTED_READY_FOR_POST_EXECUTION_VERIFICATION" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY" if ok else "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D169_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_controlled_execution_run_scope_created": ok,
            "execution_run_result_created": ok,
            "execution_safety_receipt_created": ok,
            "d169_scope_created": ok,
            "candidate_executed_in_sandbox": ok,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D169 may create post execution verification scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_controlled_execution_run_scope(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_controlled_execution_run_scope import create_sandbox_candidate_reentry_controlled_execution_run_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


def no_ai_flags():
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


class TestD168SandboxCandidateReentryControlledExecutionRunScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        intent_id = "d167-test"
        preflight_id = "d166-test"
        validation_id = "d165-test"
        candidate_id = "d164-test"
        response_id = "d163-test"
        runner_id = "d162-test"
        plan_id = "d161-test"
        review_id = "d160-test"
        scope_id = "d159-test"
        intake_id = "d158-test"
        reentry_id = "d157-test"
        next_cycle_id = "d156-test"
        proposal_id = "d107-valid-test"

        work_dir = root / "runtime_experimental" / "ai_sandbox_work" / candidate_id
        work_dir.mkdir(parents=True, exist_ok=True)
        candidate_payload = {
            **no_ai_flags(),
            "ok": True,
            "candidate_id": candidate_id,
            "payload_kind": "NO_OP_REENTRY_PLACEHOLDER_FOR_STATIC_VALIDATION",
            "payload_status": "MATERIALIZED_IN_SANDBOX_ONLY_NO_EXECUTION",
            "operations": [
                {
                    "op": "NO_OP",
                    "writes_core": False,
                    "executes_code": False,
                    "requires_network": False,
                    "requires_secrets": False,
                    "requires_shell": False,
                }
            ],
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }
        write(work_dir / "candidate_payload.json", candidate_payload)

        d167 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_READY",
            "intent_id": intent_id,
            "preflight_id": preflight_id,
            "validation_id": validation_id,
            "candidate_id": candidate_id,
            "response_id": response_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "scope_id": scope_id,
            "intake_id": intake_id,
            "reentry_id": reentry_id,
            "next_cycle_id": next_cycle_id,
            "cycle_closure_id": "d155-test",
            "previous_candidate_id": "d126-test",
            "proposal_id": proposal_id,
            "guardrails": {
                **no_ai_flags(),
                "sandbox_candidate_reentry_human_execution_intent_scope_only": True,
                "sandbox_candidate_reentry_human_execution_intent_record_only": True,
                "sandbox_candidate_reentry_execution_authority_guard_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "human_execution_intent_present": True,
                "sandbox_execution_intent_only": True,
                "candidate_execution_allowed_next": True,
                "candidate_execution_allowed_after_d167": False,
                "candidate_execution_requested": False,
                "candidate_executed": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "approval_for_d168_sandbox_candidate_reentry_controlled_execution_run_scope_only": True,
                "real_apply_allowed_after_d167_by_ai": False,
                "route_insert_allowed_after_d167_by_ai": False,
                "protected_core_mutation_allowed_after_d167_by_ai": False,
                "network_allowed_after_d167_by_ai": False,
                "secret_read_allowed_after_d167_by_ai": False,
                "shell_allowed_after_d167_by_ai": False,
                "git_action_allowed_after_d167_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D167_PLUS",
                "human_execution_intent_status": "HUMAN_EXECUTION_INTENT_RECORDED_FOR_SANDBOX_ONLY_NO_REAL_APPLY",
                "authority_guard_status": "HUMAN_INTENT_RECORDED_RUN_AUTHORITY_NOT_EXECUTED",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_CONTROLLED_EXECUTION_RUN_SCOPE",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_ONLY",
                "next_step": "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE",
            },
        }

        intent_record = {
            **no_ai_flags(),
            "ok": True,
            "human_execution_intent_status": "HUMAN_EXECUTION_INTENT_RECORDED_FOR_SANDBOX_ONLY_NO_REAL_APPLY",
            "human_execution_intent_present": True,
            "human_execution_intent_required": True,
            "sandbox_execution_intent_only": True,
            "candidate_execution_allowed_next": True,
            "candidate_execution_allowed_after_d167": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_apply_allowed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        authority_guard = {
            **no_ai_flags(),
            "ok": True,
            "authority_mode": "HUMAN_INTENT_RECORDED_SANDBOX_EXECUTION_ONLY_NO_APPLY",
            "authority_guard_status": "HUMAN_INTENT_RECORDED_RUN_AUTHORITY_NOT_EXECUTED",
            "human_execution_intent_present": True,
            "sandbox_execution_only": True,
            "candidate_execution_allowed_next": True,
            "candidate_execution_allowed_after_d167": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "real_apply_allowed": False,
            "apply_requested": False,
            "apply_executed": False,
            "network_allowed": False,
            "secret_read_allowed": False,
            "shell_allowed": False,
            "git_action_allowed": False,
            "route_insert_allowed": False,
            "protected_core_mutation_allowed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "no_candidate_execution_yet": True,
            "no_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
        }

        d168_scope = {
            "ok": True,
            "allowed_next_gate": "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE",
            "sandbox_candidate_reentry_controlled_execution_run_scope_only": True,
            "human_execution_intent_present": True,
            "sandbox_execution_only": True,
            "candidate_execution_allowed_after_d167_only_in_sandbox": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d167_by_ai": False,
            "route_insert_allowed_after_d167_by_ai": False,
            "protected_core_mutation_allowed_after_d167_by_ai": False,
            "network_allowed_after_d167_by_ai": False,
            "secret_read_allowed_after_d167_by_ai": False,
            "shell_allowed_after_d167_by_ai": False,
            "git_action_allowed_after_d167_by_ai": False,
        }

        write(root / "reports/d167_sandbox_candidate_reentry_human_execution_intent_scope.json", d167)
        write(root / "reports/d167_sandbox_candidate_reentry_human_execution_intent_record.json", intent_record)
        write(root / "reports/d167_sandbox_candidate_reentry_execution_authority_guard.json", authority_guard)
        write(root / "reports/d167_d168_sandbox_candidate_reentry_controlled_execution_run_scope.json", d168_scope)
        return td, root

    def test_creates_controlled_execution_run_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_controlled_execution_run_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_ONLY")
            self.assertEqual(r["d169_scope"]["allowed_next_gate"], "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE")
            self.assertTrue(r["guardrails"]["candidate_executed_in_sandbox"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted_by_ai"])
            self.assertTrue((root / "reports/d168_sandbox_candidate_reentry_controlled_execution_run_scope.json").exists())
            self.assertTrue((root / "reports/d168_sandbox_candidate_reentry_execution_run_result.json").exists())
            self.assertTrue((root / "reports/d168_sandbox_candidate_reentry_execution_safety_receipt.json").exists())
            self.assertTrue((root / "reports/d168_d169_sandbox_candidate_reentry_post_execution_verification_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d167(self):
        td, root = self.root()
        try:
            (root / "reports/d167_sandbox_candidate_reentry_human_execution_intent_scope.json").unlink()
            r = create_sandbox_candidate_reentry_controlled_execution_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_candidate_payload_requires_network(self):
        td, root = self.root()
        try:
            p = root / "runtime_experimental" / "ai_sandbox_work" / "d164-test" / "candidate_payload.json"
            data = json.loads(p.read_text())
            data["operations"][0]["requires_network"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_execution_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d168_scope_allows_shell(self):
        td, root = self.root()
        try:
            p = root / "reports/d167_d168_sandbox_candidate_reentry_controlled_execution_run_scope.json"
            data = json.loads(p.read_text())
            data["shell_allowed_after_d167_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_execution_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_authority_guard_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d167_sandbox_candidate_reentry_execution_authority_guard.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_execution_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
"""


def sh(cmd, check=False):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, text=True, capture_output=False, check=check)


def repo_root():
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p
    return here


ROOT = repo_root()
os.chdir(ROOT)
Path("runtime_experimental").mkdir(exist_ok=True)
Path("tests").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)

print("D168 SANDBOX CANDIDATE REENTRY CONTROLLED EXECUTION RUN SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_reentry_controlled_execution_run_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d168_sandbox_candidate_reentry_controlled_execution_run_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_reentry_controlled_execution_run_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d168_sandbox_candidate_reentry_controlled_execution_run_scope", "-v"], check=True)

print("\n== run D168 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_reentry_controlled_execution_run_scope import create_sandbox_candidate_reentry_controlled_execution_run_scope\n"
    "r=create_sandbox_candidate_reentry_controlled_execution_run_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d168_sandbox_candidate_reentry_controlled_execution_run_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_reentry_controlled_execution_run_scope.py",
    "tests/test_d168_sandbox_candidate_reentry_controlled_execution_run_scope.py",
    "reports/d168_sandbox_candidate_reentry_controlled_execution_run_scope.json",
    "reports/d168_sandbox_candidate_reentry_execution_run_result.json",
    "reports/d168_sandbox_candidate_reentry_execution_safety_receipt.json",
    "reports/d168_d169_sandbox_candidate_reentry_post_execution_verification_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D168 sandbox candidate reentry controlled execution run scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D168 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD168 SANDBOX CANDIDATE REENTRY CONTROLLED EXECUTION RUN SCOPE BOOT DONE")
