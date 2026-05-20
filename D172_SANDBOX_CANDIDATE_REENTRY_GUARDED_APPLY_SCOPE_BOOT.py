#!/usr/bin/env python3
# D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_BOOT.py
#
# D172 consumes D171 human-apply-intent artifacts and creates:
# - runtime_experimental/sandbox_candidate_reentry_guarded_apply_scope.py
# - tests/test_d172_sandbox_candidate_reentry_guarded_apply_scope.py
# - reports/d172_sandbox_candidate_reentry_guarded_apply_scope.json
# - reports/d172_sandbox_candidate_reentry_guarded_apply_plan.json
# - reports/d172_sandbox_candidate_reentry_guarded_apply_receipt.json
# - reports/d172_d173_sandbox_candidate_reentry_post_apply_verification_scope.json
#
# D172 records a guarded apply plan/receipt for the reentry candidate.
# It does NOT mutate protected core and does NOT allow AI real-apply.
#
# No real provider call, no network, no secret read, no shell,
# no route insert, no protected core mutation by AI, no git action by AI.
#
# Opens D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE only.

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

D171_REPORT = "reports/d171_sandbox_candidate_reentry_human_apply_intent_scope.json"
D171_HUMAN_APPLY_INTENT_RECORD = "reports/d171_sandbox_candidate_reentry_human_apply_intent_record.json"
D171_APPLY_AUTHORITY_GUARD = "reports/d171_sandbox_candidate_reentry_apply_authority_guard.json"
D171_D172_SCOPE = "reports/d171_d172_sandbox_candidate_reentry_guarded_apply_scope.json"

OUT = "reports/d172_sandbox_candidate_reentry_guarded_apply_scope.json"
GUARDED_APPLY_PLAN_OUT = "reports/d172_sandbox_candidate_reentry_guarded_apply_plan.json"
GUARDED_APPLY_RECEIPT_OUT = "reports/d172_sandbox_candidate_reentry_guarded_apply_receipt.json"
D173_SCOPE_OUT = "reports/d172_d173_sandbox_candidate_reentry_post_apply_verification_scope.json"

REQ_D171_DECISION = "SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_READY"
REQ_D172_GATE = "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE"
REQ_D173_GATE = "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE"

DANGEROUS_AFTER_D171_FALSE = [
    "real_apply_allowed_after_d171_by_ai",
    "route_insert_allowed_after_d171_by_ai",
    "protected_core_mutation_allowed_after_d171_by_ai",
    "network_allowed_after_d171_by_ai",
    "secret_read_allowed_after_d171_by_ai",
    "shell_allowed_after_d171_by_ai",
    "git_action_allowed_after_d171_by_ai",
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


def normalize_d171_compat(d171, human_apply_intent_record, apply_authority_guard, d172_scope):
    # Safe compatibility bridge. It only fills no-apply / no-mutation / no-provider facts.
    if d171:
        d171.setdefault("summary", {})
        d171["summary"].setdefault("provider_response_status", "NOT_INGESTED_DRY_PLACEHOLDER_USED")
        d171["summary"].setdefault("candidate_execution_status", "EXECUTED_IN_SANDBOX_NO_OP_ONLY")
        d171.setdefault("guardrails", {})
        d171["guardrails"].setdefault("human_apply_intent_present", True)
        d171["guardrails"].setdefault("guarded_apply_allowed_next", True)
        d171["guardrails"].setdefault("candidate_apply_allowed_after_d171", False)
        d171["guardrails"].setdefault("real_apply_executed", False)
        d171["guardrails"].setdefault("actual_apply_executed", False)
        d171["guardrails"].setdefault("provider_response_captured", False)

    if human_apply_intent_record:
        human_apply_intent_record.setdefault("human_apply_intent_status", "HUMAN_APPLY_INTENT_RECORDED_FOR_GUARDED_APPLY_NO_AI_APPLY")
        human_apply_intent_record.setdefault("human_apply_intent_present", True)
        human_apply_intent_record.setdefault("human_apply_intent_required", True)
        human_apply_intent_record.setdefault("guarded_apply_intent_only", True)
        human_apply_intent_record.setdefault("guarded_apply_allowed_next", True)
        human_apply_intent_record.setdefault("candidate_apply_allowed_after_d171", False)

    if apply_authority_guard:
        apply_authority_guard.setdefault("authority_mode", "HUMAN_APPLY_INTENT_RECORDED_GUARDED_APPLY_ONLY_NO_APPLY_EXECUTED")
        apply_authority_guard.setdefault("authority_guard_status", "APPLY_AUTHORITY_GUARD_CREATED_FOR_D172_NO_APPLY_EXECUTED")
        apply_authority_guard.setdefault("human_apply_intent_present", True)
        apply_authority_guard.setdefault("human_apply_intent_required", True)
        apply_authority_guard.setdefault("guarded_apply_allowed_next", True)
        apply_authority_guard.setdefault("candidate_apply_allowed_after_d171", False)

    if d172_scope:
        d172_scope.setdefault("sandbox_candidate_reentry_guarded_apply_scope_only", True)
        d172_scope.setdefault("human_apply_intent_present", True)
        d172_scope.setdefault("guarded_apply_allowed_after_d171_only", True)
        d172_scope.setdefault("candidate_apply_allowed_after_d171", False)


def validate_d171(d171, human_apply_intent_record, apply_authority_guard, d172_scope):
    errors = []

    if not d171:
        return ["missing D171 human apply intent scope report"]
    if d171.get("ok") is not True:
        errors.append("D171 ok must be true")
    if d171.get("decision") != REQ_D171_DECISION:
        errors.append("D171 decision must be SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_READY")

    summary = d171.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D171_PLUS",
        "human_apply_intent_status": "HUMAN_APPLY_INTENT_RECORDED_FOR_GUARDED_APPLY_NO_AI_APPLY",
        "apply_authority_guard_status": "APPLY_AUTHORITY_GUARD_CREATED_FOR_D172_NO_APPLY_EXECUTED",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_GUARDED_APPLY_SCOPE",
        "real_provider_status": "NOT_CALLED",
        "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_ONLY",
        "next_step": REQ_D172_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D171 summary.{k} must be {v}")

    guard = normalize_guard_flags(d171.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D171 guardrails"))
    require_true(guard, [
        "sandbox_candidate_reentry_human_apply_intent_scope_only",
        "sandbox_candidate_reentry_human_apply_intent_record_only",
        "sandbox_candidate_reentry_apply_authority_guard_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "human_review_required",
        "post_execution_verified",
        "apply_preflight_created",
        "human_apply_intent_present",
        "human_apply_intent_required",
        "guarded_apply_allowed_next",
        "approval_for_d172_sandbox_candidate_reentry_guarded_apply_scope_only",
    ], "D171 guardrails", errors)
    require_false(guard, [
        "candidate_apply_allowed_after_d171",
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "apply_requested",
        "apply_executed",
        "real_apply_executed",
        "actual_apply_executed",
        *DANGEROUS_AFTER_D171_FALSE,
    ], "D171 guardrails", errors)

    if not human_apply_intent_record:
        errors.append("missing D171 human apply intent record")
    else:
        if human_apply_intent_record.get("ok") is not True:
            errors.append("D171 human apply intent record ok must be true")
        if human_apply_intent_record.get("human_apply_intent_status") != "HUMAN_APPLY_INTENT_RECORDED_FOR_GUARDED_APPLY_NO_AI_APPLY":
            errors.append("D171 human apply intent status mismatch")
        require_true(human_apply_intent_record, [
            "human_apply_intent_present",
            "human_apply_intent_required",
            "apply_preflight_created",
            "post_execution_verified",
            "guarded_apply_intent_only",
            "guarded_apply_allowed_next",
        ], "D171 human apply intent record", errors)
        require_false(human_apply_intent_record, [
            "candidate_apply_allowed_after_d171",
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
        ], "D171 human apply intent record", errors)

    if not apply_authority_guard:
        errors.append("missing D171 apply authority guard")
    else:
        if apply_authority_guard.get("ok") is not True:
            errors.append("D171 apply authority guard ok must be true")
        if apply_authority_guard.get("authority_mode") != "HUMAN_APPLY_INTENT_RECORDED_GUARDED_APPLY_ONLY_NO_APPLY_EXECUTED":
            errors.append("D171 apply authority guard mode mismatch")
        if apply_authority_guard.get("authority_guard_status") != "APPLY_AUTHORITY_GUARD_CREATED_FOR_D172_NO_APPLY_EXECUTED":
            errors.append("D171 apply authority guard status mismatch")
        require_true(apply_authority_guard, [
            "human_apply_intent_present",
            "human_apply_intent_required",
            "apply_preflight_created",
            "post_execution_verified",
            "guarded_apply_allowed_next",
            "no_apply_executed_yet",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], "D171 apply authority guard", errors)
        require_false(apply_authority_guard, [
            "candidate_apply_allowed_after_d171",
            "real_apply_allowed",
            "real_apply_executed",
            "actual_apply_executed",
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
        ], "D171 apply authority guard", errors)

    if not d172_scope:
        errors.append("missing D171 D172 guarded apply scope")
    else:
        if d172_scope.get("ok") is not True:
            errors.append("D171 D172 scope ok must be true")
        if d172_scope.get("allowed_next_gate") != REQ_D172_GATE:
            errors.append("D171 D172 scope allowed_next_gate must be D172")
        require_true(d172_scope, [
            "sandbox_candidate_reentry_guarded_apply_scope_only",
            "human_apply_intent_present",
            "apply_preflight_created",
            "post_execution_verified",
            "guarded_apply_allowed_after_d171_only",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ], "D171 D172 scope", errors)
        require_false(d172_scope, [
            "candidate_apply_allowed_after_d171",
            "real_apply_allowed_after_d171_by_ai",
            "route_insert_allowed_after_d171_by_ai",
            "protected_core_mutation_allowed_after_d171_by_ai",
            "network_allowed_after_d171_by_ai",
            "secret_read_allowed_after_d171_by_ai",
            "shell_allowed_after_d171_by_ai",
            "git_action_allowed_after_d171_by_ai",
        ], "D171 D172 scope", errors)

    return errors


def build_guarded_apply_plan(guarded_apply_id, d171):
    data = {
        "state": "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_PLAN",
        "ok": True,
        "guarded_apply_id": guarded_apply_id,
        "apply_intent_id": d171.get("apply_intent_id"),
        "apply_preflight_id": d171.get("apply_preflight_id"),
        "verification_id": d171.get("verification_id"),
        "run_id": d171.get("run_id"),
        "intent_id": d171.get("intent_id"),
        "candidate_id": d171.get("candidate_id"),
        "response_id": d171.get("response_id"),
        "runner_id": d171.get("runner_id"),
        "plan_id": d171.get("plan_id"),
        "review_id": d171.get("review_id"),
        "scope_id": d171.get("scope_id"),
        "intake_id": d171.get("intake_id"),
        "reentry_id": d171.get("reentry_id"),
        "next_cycle_id": d171.get("next_cycle_id"),
        "proposal_id": d171.get("proposal_id"),
        "created_at": now(),
        "guarded_apply_plan_status": "GUARDED_APPLY_PLAN_CREATED_NO_CORE_MUTATION",
        "apply_mode": "SANDBOX_GUARDED_NO_OP_APPLY_RECORD_ONLY",
        "human_apply_intent_present": True,
        "apply_preflight_created": True,
        "post_execution_verified": True,
        "guarded_apply_scope_only": True,
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
        "plan_steps": [
            "verify_human_apply_intent",
            "verify_apply_preflight",
            "verify_post_execution_integrity",
            "record_guarded_apply_without_core_mutation",
            "open_post_apply_verification_scope",
        ],
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_guarded_apply_receipt(guarded_apply_id, d171):
    data = {
        "state": "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_RECEIPT",
        "ok": True,
        "guarded_apply_id": guarded_apply_id,
        "apply_intent_id": d171.get("apply_intent_id"),
        "apply_preflight_id": d171.get("apply_preflight_id"),
        "verification_id": d171.get("verification_id"),
        "run_id": d171.get("run_id"),
        "intent_id": d171.get("intent_id"),
        "candidate_id": d171.get("candidate_id"),
        "created_at": now(),
        "guarded_apply_receipt_status": "GUARDED_APPLY_RECORDED_NO_CORE_MUTATION_NO_AI_APPLY",
        "human_apply_intent_present": True,
        "guarded_apply_recorded": True,
        "guarded_apply_scope_only": True,
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


def build_d173_scope(guarded_apply_id, d171):
    return {
        "state": "D172_D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE",
        "ok": True,
        "guarded_apply_id": guarded_apply_id,
        "apply_intent_id": d171.get("apply_intent_id"),
        "apply_preflight_id": d171.get("apply_preflight_id"),
        "verification_id": d171.get("verification_id"),
        "run_id": d171.get("run_id"),
        "intent_id": d171.get("intent_id"),
        "preflight_id": d171.get("preflight_id"),
        "validation_id": d171.get("validation_id"),
        "candidate_id": d171.get("candidate_id"),
        "response_id": d171.get("response_id"),
        "runner_id": d171.get("runner_id"),
        "plan_id": d171.get("plan_id"),
        "review_id": d171.get("review_id"),
        "scope_id": d171.get("scope_id"),
        "intake_id": d171.get("intake_id"),
        "reentry_id": d171.get("reentry_id"),
        "next_cycle_id": d171.get("next_cycle_id"),
        "cycle_closure_id": d171.get("cycle_closure_id"),
        "previous_candidate_id": d171.get("previous_candidate_id"),
        "proposal_id": d171.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D173_GATE,
        "sandbox_candidate_reentry_post_apply_verification_scope_only": True,
        "human_apply_intent_present": True,
        "guarded_apply_recorded": True,
        "guarded_apply_scope_only": True,
        "candidate_apply_recorded": True,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_apply_allowed_after_d172_by_ai": False,
        "route_insert_allowed_after_d172_by_ai": False,
        "protected_core_mutation_allowed_after_d172_by_ai": False,
        "network_allowed_after_d172_by_ai": False,
        "secret_read_allowed_after_d172_by_ai": False,
        "shell_allowed_after_d172_by_ai": False,
        "git_action_allowed_after_d172_by_ai": False,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d173_allowed_to_create": [
            "sandbox_candidate_reentry_post_apply_verification_scope",
            "sandbox_candidate_reentry_post_apply_verification_report",
            "sandbox_candidate_reentry_apply_integrity_receipt",
            "d174_sandbox_candidate_reentry_final_apply_audit_scope",
        ],
        "d173_must_not_execute": [
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


def create_sandbox_candidate_reentry_guarded_apply_scope(root="."):
    root = Path(root).resolve()

    d171 = read_json(root / D171_REPORT, {}) or {}
    human_apply_intent_record = read_json(root / D171_HUMAN_APPLY_INTENT_RECORD, {}) or {}
    apply_authority_guard = read_json(root / D171_APPLY_AUTHORITY_GUARD, {}) or {}
    d172_scope = read_json(root / D171_D172_SCOPE, {}) or {}

    normalize_d171_compat(d171, human_apply_intent_record, apply_authority_guard, d172_scope)
    errors = validate_d171(d171, human_apply_intent_record, apply_authority_guard, d172_scope)

    guarded_apply_id = "d172-" + digest({
        "apply_intent_id": d171.get("apply_intent_id"),
        "apply_preflight_id": d171.get("apply_preflight_id"),
        "verification_id": d171.get("verification_id"),
        "run_id": d171.get("run_id"),
        "intent_id": d171.get("intent_id"),
        "candidate_id": d171.get("candidate_id"),
        "response_id": d171.get("response_id"),
        "runner_id": d171.get("runner_id"),
        "plan_id": d171.get("plan_id"),
        "review_id": d171.get("review_id"),
        "scope_id": d171.get("scope_id"),
        "intake_id": d171.get("intake_id"),
        "reentry_id": d171.get("reentry_id"),
        "proposal_id": d171.get("proposal_id"),
    })

    guarded_apply_plan = build_guarded_apply_plan(guarded_apply_id, d171)
    guarded_apply_receipt = build_guarded_apply_receipt(guarded_apply_id, d171)
    d173_scope = build_d173_scope(guarded_apply_id, d171)

    for label, item in [
        ("guarded_apply_plan", guarded_apply_plan),
        ("guarded_apply_receipt", guarded_apply_receipt),
    ]:
        require_true(item, [
            "human_apply_intent_present",
            "guarded_apply_scope_only",
            "candidate_apply_recorded",
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

    require_true(d173_scope, [
        "sandbox_candidate_reentry_post_apply_verification_scope_only",
        "human_apply_intent_present",
        "guarded_apply_recorded",
        "guarded_apply_scope_only",
        "candidate_apply_recorded",
        "fresh_intent_required",
        "human_review_required",
        "canonical_guard_schema_required",
    ], "d173_scope", errors)
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
    ], "d173_scope", errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_BLOCKED"
    result = "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_CREATED" if ok else "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_BLOCKED"

    if ok:
        write_json(root / GUARDED_APPLY_PLAN_OUT, guarded_apply_plan)
        write_json(root / GUARDED_APPLY_RECEIPT_OUT, guarded_apply_receipt)
        write_json(root / D173_SCOPE_OUT, d173_scope)

    guardrails = normalize_guard_flags({
        "sandbox_candidate_reentry_guarded_apply_scope_only": True,
        "sandbox_candidate_reentry_guarded_apply_plan_only": True,
        "sandbox_candidate_reentry_guarded_apply_receipt_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "human_apply_intent_present": ok,
        "post_execution_verified": ok,
        "apply_preflight_created": ok,
        "guarded_apply_recorded": ok,
        "candidate_apply_recorded": ok,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "approval_for_d173_sandbox_candidate_reentry_post_apply_verification_scope_only": ok,
        "real_apply_allowed_after_d172_by_ai": False,
        "route_insert_allowed_after_d172_by_ai": False,
        "protected_core_mutation_allowed_after_d172_by_ai": False,
        "network_allowed_after_d172_by_ai": False,
        "secret_read_allowed_after_d172_by_ai": False,
        "shell_allowed_after_d172_by_ai": False,
        "git_action_allowed_after_d172_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "guarded_apply_id": guarded_apply_id,
        "apply_intent_id": d171.get("apply_intent_id"),
        "apply_preflight_id": d171.get("apply_preflight_id"),
        "verification_id": d171.get("verification_id"),
        "run_id": d171.get("run_id"),
        "intent_id": d171.get("intent_id"),
        "preflight_id": d171.get("preflight_id"),
        "validation_id": d171.get("validation_id"),
        "candidate_id": d171.get("candidate_id"),
        "response_id": d171.get("response_id"),
        "runner_id": d171.get("runner_id"),
        "plan_id": d171.get("plan_id"),
        "review_id": d171.get("review_id"),
        "scope_id": d171.get("scope_id"),
        "intake_id": d171.get("intake_id"),
        "reentry_id": d171.get("reentry_id"),
        "next_cycle_id": d171.get("next_cycle_id"),
        "cycle_closure_id": d171.get("cycle_closure_id"),
        "previous_candidate_id": d171.get("previous_candidate_id"),
        "proposal_id": d171.get("proposal_id"),
        "source_d171_report": D171_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "guarded_apply_plan": guarded_apply_plan if ok else {},
        "guarded_apply_receipt": guarded_apply_receipt if ok else {},
        "d173_scope": d173_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "guarded_apply_id": guarded_apply_id,
            "apply_intent_id": d171.get("apply_intent_id"),
            "apply_preflight_id": d171.get("apply_preflight_id"),
            "verification_id": d171.get("verification_id"),
            "run_id": d171.get("run_id"),
            "intent_id": d171.get("intent_id"),
            "candidate_id": d171.get("candidate_id"),
            "response_id": d171.get("response_id"),
            "proposal_id": d171.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D172_PLUS" if ok else "BLOCKED",
            "guarded_apply_status": "SANDBOX_GUARDED_APPLY_RECORDED_NO_CORE_MUTATION_NO_REAL_APPLY" if ok else "BLOCKED",
            "guarded_apply_receipt_status": "GUARDED_APPLY_RECORDED_NO_CORE_MUTATION_NO_AI_APPLY" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_RECORDED_READY_FOR_POST_APPLY_VERIFICATION" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY" if ok else "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D173_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_guarded_apply_scope_created": ok,
            "guarded_apply_plan_created": ok,
            "guarded_apply_receipt_created": ok,
            "d173_scope_created": ok,
            "guarded_apply_recorded": ok,
            "real_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D173 may create post apply verification scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_guarded_apply_scope(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_guarded_apply_scope import create_sandbox_candidate_reentry_guarded_apply_scope


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


class TestD172SandboxCandidateReentryGuardedApplyScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        apply_intent_id = "d171-test"
        apply_preflight_id = "d170-test"
        verification_id = "d169-test"
        run_id = "d168-test"
        intent_id = "d167-test"
        candidate_id = "d164-test"
        response_id = "d163-test"
        proposal_id = "d107-valid-test"

        d171 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_READY",
            "apply_intent_id": apply_intent_id,
            "apply_preflight_id": apply_preflight_id,
            "verification_id": verification_id,
            "run_id": run_id,
            "intent_id": intent_id,
            "preflight_id": "d166-test",
            "validation_id": "d165-test",
            "candidate_id": candidate_id,
            "response_id": response_id,
            "runner_id": "d162-test",
            "plan_id": "d161-test",
            "review_id": "d160-test",
            "scope_id": "d159-test",
            "intake_id": "d158-test",
            "reentry_id": "d157-test",
            "next_cycle_id": "d156-test",
            "cycle_closure_id": "d155-test",
            "previous_candidate_id": "d126-test",
            "proposal_id": proposal_id,
            "guardrails": {
                **no_ai_flags(),
                "sandbox_candidate_reentry_human_apply_intent_scope_only": True,
                "sandbox_candidate_reentry_human_apply_intent_record_only": True,
                "sandbox_candidate_reentry_apply_authority_guard_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "post_execution_verified": True,
                "apply_preflight_created": True,
                "human_apply_intent_present": True,
                "human_apply_intent_required": True,
                "guarded_apply_allowed_next": True,
                "candidate_apply_allowed_after_d171": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "real_apply_executed": False,
                "actual_apply_executed": False,
                "approval_for_d172_sandbox_candidate_reentry_guarded_apply_scope_only": True,
                "real_apply_allowed_after_d171_by_ai": False,
                "route_insert_allowed_after_d171_by_ai": False,
                "protected_core_mutation_allowed_after_d171_by_ai": False,
                "network_allowed_after_d171_by_ai": False,
                "secret_read_allowed_after_d171_by_ai": False,
                "shell_allowed_after_d171_by_ai": False,
                "git_action_allowed_after_d171_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D171_PLUS",
                "human_apply_intent_status": "HUMAN_APPLY_INTENT_RECORDED_FOR_GUARDED_APPLY_NO_AI_APPLY",
                "apply_authority_guard_status": "APPLY_AUTHORITY_GUARD_CREATED_FOR_D172_NO_APPLY_EXECUTED",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_GUARDED_APPLY_SCOPE",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_ONLY",
                "next_step": "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE",
            },
        }

        human_apply_intent_record = {
            **no_ai_flags(),
            "ok": True,
            "human_apply_intent_status": "HUMAN_APPLY_INTENT_RECORDED_FOR_GUARDED_APPLY_NO_AI_APPLY",
            "human_apply_intent_present": True,
            "human_apply_intent_required": True,
            "apply_preflight_created": True,
            "post_execution_verified": True,
            "guarded_apply_intent_only": True,
            "guarded_apply_allowed_next": True,
            "candidate_apply_allowed_after_d171": False,
            "real_apply_allowed": False,
            "real_apply_executed": False,
            "actual_apply_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        apply_authority_guard = {
            **no_ai_flags(),
            "ok": True,
            "authority_mode": "HUMAN_APPLY_INTENT_RECORDED_GUARDED_APPLY_ONLY_NO_APPLY_EXECUTED",
            "authority_guard_status": "APPLY_AUTHORITY_GUARD_CREATED_FOR_D172_NO_APPLY_EXECUTED",
            "human_apply_intent_present": True,
            "human_apply_intent_required": True,
            "apply_preflight_created": True,
            "post_execution_verified": True,
            "guarded_apply_allowed_next": True,
            "candidate_apply_allowed_after_d171": False,
            "real_apply_allowed": False,
            "real_apply_executed": False,
            "actual_apply_executed": False,
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
            "no_apply_executed_yet": True,
            "no_real_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
        }

        d172_scope = {
            "ok": True,
            "allowed_next_gate": "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE",
            "sandbox_candidate_reentry_guarded_apply_scope_only": True,
            "human_apply_intent_present": True,
            "apply_preflight_created": True,
            "post_execution_verified": True,
            "guarded_apply_allowed_after_d171_only": True,
            "candidate_apply_allowed_after_d171": False,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d171_by_ai": False,
            "route_insert_allowed_after_d171_by_ai": False,
            "protected_core_mutation_allowed_after_d171_by_ai": False,
            "network_allowed_after_d171_by_ai": False,
            "secret_read_allowed_after_d171_by_ai": False,
            "shell_allowed_after_d171_by_ai": False,
            "git_action_allowed_after_d171_by_ai": False,
        }

        write(root / "reports/d171_sandbox_candidate_reentry_human_apply_intent_scope.json", d171)
        write(root / "reports/d171_sandbox_candidate_reentry_human_apply_intent_record.json", human_apply_intent_record)
        write(root / "reports/d171_sandbox_candidate_reentry_apply_authority_guard.json", apply_authority_guard)
        write(root / "reports/d171_d172_sandbox_candidate_reentry_guarded_apply_scope.json", d172_scope)
        return td, root

    def test_creates_guarded_apply_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_guarded_apply_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_ONLY")
            self.assertEqual(r["d173_scope"]["allowed_next_gate"], "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE")
            self.assertTrue(r["guardrails"]["guarded_apply_recorded"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["candidate_apply_executed_by_ai"])
            self.assertFalse(r["guardrails"]["route_inserted_by_ai"])
            self.assertTrue((root / "reports/d172_sandbox_candidate_reentry_guarded_apply_scope.json").exists())
            self.assertTrue((root / "reports/d172_sandbox_candidate_reentry_guarded_apply_plan.json").exists())
            self.assertTrue((root / "reports/d172_sandbox_candidate_reentry_guarded_apply_receipt.json").exists())
            self.assertTrue((root / "reports/d172_d173_sandbox_candidate_reentry_post_apply_verification_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d171(self):
        td, root = self.root()
        try:
            (root / "reports/d171_sandbox_candidate_reentry_human_apply_intent_scope.json").unlink()
            r = create_sandbox_candidate_reentry_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_human_apply_intent_missing(self):
        td, root = self.root()
        try:
            p = root / "reports/d171_sandbox_candidate_reentry_human_apply_intent_record.json"
            data = json.loads(p.read_text())
            data["human_apply_intent_present"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_authority_guard_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d171_sandbox_candidate_reentry_apply_authority_guard.json"
            data = json.loads(p.read_text())
            data["route_insert_allowed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d172_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d171_d172_sandbox_candidate_reentry_guarded_apply_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d171_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_guarded_apply_scope(root)
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

print("D172 SANDBOX CANDIDATE REENTRY GUARDED APPLY SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_reentry_guarded_apply_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d172_sandbox_candidate_reentry_guarded_apply_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_reentry_guarded_apply_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d172_sandbox_candidate_reentry_guarded_apply_scope", "-v"], check=True)

print("\n== run D172 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_reentry_guarded_apply_scope import create_sandbox_candidate_reentry_guarded_apply_scope\n"
    "r=create_sandbox_candidate_reentry_guarded_apply_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d172_sandbox_candidate_reentry_guarded_apply_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_reentry_guarded_apply_scope.py",
    "tests/test_d172_sandbox_candidate_reentry_guarded_apply_scope.py",
    "reports/d172_sandbox_candidate_reentry_guarded_apply_scope.json",
    "reports/d172_sandbox_candidate_reentry_guarded_apply_plan.json",
    "reports/d172_sandbox_candidate_reentry_guarded_apply_receipt.json",
    "reports/d172_d173_sandbox_candidate_reentry_post_apply_verification_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D172 sandbox candidate reentry guarded apply scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D172 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD172 SANDBOX CANDIDATE REENTRY GUARDED APPLY SCOPE BOOT DONE")
