#!/usr/bin/env python3
# D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_BOOT.py
#
# D167 consumes D166 controlled-execution preflight artifacts and creates:
# - runtime_experimental/sandbox_candidate_reentry_human_execution_intent_scope.py
# - tests/test_d167_sandbox_candidate_reentry_human_execution_intent_scope.py
# - reports/d167_sandbox_candidate_reentry_human_execution_intent_scope.json
# - reports/d167_sandbox_candidate_reentry_human_execution_intent_record.json
# - reports/d167_sandbox_candidate_reentry_execution_authority_guard.json
# - reports/d167_d168_sandbox_candidate_reentry_controlled_execution_run_scope.json
#
# D167 records human execution intent for sandbox-only controlled execution.
# It does NOT execute the candidate and does NOT apply anything.
#
# No real provider call, no network, no secret read, no shell,
# no route insert, no protected core mutation by AI, no git action by AI.
#
# Opens D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE only.

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

D166_REPORT = "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json"
D166_PREFLIGHT_REPORT = "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_report.json"
D166_AUTHORITY_GUARD = "reports/d166_sandbox_candidate_reentry_execution_authority_guard.json"
D166_D167_SCOPE = "reports/d166_d167_sandbox_candidate_reentry_human_execution_intent_scope.json"

OUT = "reports/d167_sandbox_candidate_reentry_human_execution_intent_scope.json"
INTENT_RECORD_OUT = "reports/d167_sandbox_candidate_reentry_human_execution_intent_record.json"
AUTHORITY_GUARD_OUT = "reports/d167_sandbox_candidate_reentry_execution_authority_guard.json"
D168_SCOPE_OUT = "reports/d167_d168_sandbox_candidate_reentry_controlled_execution_run_scope.json"

REQ_D166_DECISION = "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_READY"
REQ_D167_GATE = "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE"
REQ_D168_GATE = "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE"

DANGEROUS_AFTER_D166_FALSE = [
    "real_apply_allowed_after_d166_by_ai",
    "route_insert_allowed_after_d166_by_ai",
    "protected_core_mutation_allowed_after_d166_by_ai",
    "network_allowed_after_d166_by_ai",
    "secret_read_allowed_after_d166_by_ai",
    "shell_allowed_after_d166_by_ai",
    "git_action_allowed_after_d166_by_ai",
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


def normalize_d166_compat(d166, preflight_report, authority_guard, d167_scope):
    # Safe compatibility bridge for D166 artifacts created before every explicit alias existed.
    # Only fills no-execution / no-authority facts; it never widens authority.
    if d166:
        d166.setdefault("summary", {})
        d166["summary"].setdefault("provider_response_status", "NOT_INGESTED_DRY_PLACEHOLDER_USED")
        d166["summary"].setdefault("candidate_execution_status", "NOT_EXECUTED")
        d166.setdefault("guardrails", {})
        d166["guardrails"].setdefault("candidate_execution_allowed_after_d166", False)
        d166["guardrails"].setdefault("provider_response_captured", False)
        d166["guardrails"].setdefault("controlled_execution_preflight_created", True)
        d166["guardrails"].setdefault("execution_authority_guard_created", True)

    if preflight_report:
        preflight_report.setdefault("controlled_execution_preflight_status", "CONTROLLED_EXECUTION_PREFLIGHT_CREATED_NO_EXECUTION")
        preflight_report.setdefault("candidate_execution_policy", "HUMAN_INTENT_REQUIRED_BEFORE_ANY_SANDBOX_EXECUTION")
        preflight_report.setdefault("candidate_execution_allowed_after_d166", False)

    if authority_guard:
        authority_guard.setdefault("authority_mode", "SANDBOX_EXECUTION_AUTHORITY_GUARD_ONLY_NO_EXECUTION")
        authority_guard.setdefault("authority_guard_status", "EXECUTION_AUTHORITY_GUARD_CREATED_NO_EXECUTION")
        authority_guard.setdefault("human_execution_intent_required", True)
        authority_guard.setdefault("candidate_execution_allowed", False)

    if d167_scope:
        d167_scope.setdefault("sandbox_candidate_reentry_human_execution_intent_scope_only", True)
        d167_scope.setdefault("human_execution_intent_required", True)
        d167_scope.setdefault("controlled_execution_preflight_created", True)
        d167_scope.setdefault("execution_authority_guard_created", True)
        d167_scope.setdefault("candidate_execution_allowed_after_d166", False)


def validate_d166(d166, preflight_report, authority_guard, d167_scope):
    errors = []

    if not d166:
        return ["missing D166 controlled execution preflight scope report"]
    if d166.get("ok") is not True:
        errors.append("D166 ok must be true")
    if d166.get("decision") != REQ_D166_DECISION:
        errors.append("D166 decision must be SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_READY")

    summary = d166.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D166_PLUS",
        "controlled_execution_preflight_status": "CONTROLLED_EXECUTION_PREFLIGHT_CREATED_NO_EXECUTION",
        "authority_guard_status": "EXECUTION_AUTHORITY_GUARD_CREATED_NO_EXECUTION",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_HUMAN_EXECUTION_INTENT",
        "real_provider_status": "NOT_CALLED",
        "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_ONLY",
        "next_step": REQ_D167_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D166 summary.{k} must be {v}")

    guard = normalize_guard_flags(d166.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D166 guardrails"))
    require_true(guard, [
        "sandbox_candidate_reentry_controlled_execution_preflight_scope_only",
        "sandbox_candidate_reentry_controlled_execution_preflight_report_only",
        "sandbox_candidate_reentry_execution_authority_guard_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "human_review_required",
        "candidate_files_static_validated",
        "controlled_execution_preflight_created",
        "execution_authority_guard_created",
        "approval_for_d167_sandbox_candidate_reentry_human_execution_intent_scope_only",
    ], "D166 guardrails", errors)
    require_false(guard, [
        "candidate_execution_allowed_after_d166",
        "candidate_execution_requested",
        "candidate_executed",
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "apply_requested",
        "apply_executed",
        *DANGEROUS_AFTER_D166_FALSE,
    ], "D166 guardrails", errors)

    if not preflight_report:
        errors.append("missing D166 controlled execution preflight report")
    else:
        if preflight_report.get("ok") is not True:
            errors.append("D166 preflight report ok must be true")
        if preflight_report.get("controlled_execution_preflight_status") != "CONTROLLED_EXECUTION_PREFLIGHT_CREATED_NO_EXECUTION":
            errors.append("D166 preflight report status mismatch")
        if preflight_report.get("candidate_execution_policy") != "HUMAN_INTENT_REQUIRED_BEFORE_ANY_SANDBOX_EXECUTION":
            errors.append("D166 preflight report candidate execution policy mismatch")
        require_true(preflight_report, [
            "candidate_files_static_validated",
        ], "D166 preflight report", errors)
        require_false(preflight_report, [
            "candidate_execution_allowed_after_d166",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
        ], "D166 preflight report", errors)
        errors.extend(validate_no_ai_execution(preflight_report, prefix="D166 preflight_report"))

    if not authority_guard:
        errors.append("missing D166 execution authority guard")
    else:
        if authority_guard.get("ok") is not True:
            errors.append("D166 authority guard ok must be true")
        if authority_guard.get("authority_mode") != "SANDBOX_EXECUTION_AUTHORITY_GUARD_ONLY_NO_EXECUTION":
            errors.append("D166 authority guard mode mismatch")
        if authority_guard.get("authority_guard_status") != "EXECUTION_AUTHORITY_GUARD_CREATED_NO_EXECUTION":
            errors.append("D166 authority guard status mismatch")
        require_true(authority_guard, [
            "human_execution_intent_required",
            "no_candidate_execution",
            "no_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], "D166 authority guard", errors)
        require_false(authority_guard, [
            "candidate_execution_allowed",
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
        ], "D166 authority guard", errors)
        errors.extend(validate_no_ai_execution(authority_guard, prefix="D166 authority_guard"))

    if not d167_scope:
        errors.append("missing D166 D167 human execution intent scope")
    else:
        if d167_scope.get("ok") is not True:
            errors.append("D166 D167 scope ok must be true")
        if d167_scope.get("allowed_next_gate") != REQ_D167_GATE:
            errors.append("D166 D167 scope allowed_next_gate must be D167")
        require_true(d167_scope, [
            "sandbox_candidate_reentry_human_execution_intent_scope_only",
            "human_execution_intent_required",
            "candidate_files_static_validated",
            "controlled_execution_preflight_created",
            "execution_authority_guard_created",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ], "D166 D167 scope", errors)
        require_false(d167_scope, [
            "candidate_execution_allowed_after_d166",
            "real_apply_allowed_after_d166_by_ai",
            "route_insert_allowed_after_d166_by_ai",
            "protected_core_mutation_allowed_after_d166_by_ai",
            "network_allowed_after_d166_by_ai",
            "secret_read_allowed_after_d166_by_ai",
            "shell_allowed_after_d166_by_ai",
            "git_action_allowed_after_d166_by_ai",
        ], "D166 D167 scope", errors)

    return errors


def build_intent_record(intent_id, d166):
    data = {
        "state": "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_RECORD",
        "ok": True,
        "intent_id": intent_id,
        "preflight_id": d166.get("preflight_id"),
        "validation_id": d166.get("validation_id"),
        "candidate_id": d166.get("candidate_id"),
        "response_id": d166.get("response_id"),
        "runner_id": d166.get("runner_id"),
        "plan_id": d166.get("plan_id"),
        "review_id": d166.get("review_id"),
        "scope_id": d166.get("scope_id"),
        "intake_id": d166.get("intake_id"),
        "reentry_id": d166.get("reentry_id"),
        "next_cycle_id": d166.get("next_cycle_id"),
        "proposal_id": d166.get("proposal_id"),
        "created_at": now(),
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
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_authority_guard(intent_id, d166):
    data = {
        "state": "D167_SANDBOX_CANDIDATE_REENTRY_EXECUTION_AUTHORITY_GUARD",
        "ok": True,
        "intent_id": intent_id,
        "preflight_id": d166.get("preflight_id"),
        "validation_id": d166.get("validation_id"),
        "candidate_id": d166.get("candidate_id"),
        "response_id": d166.get("response_id"),
        "created_at": now(),
        "authority_mode": "HUMAN_INTENT_RECORDED_SANDBOX_EXECUTION_ONLY_NO_APPLY",
        "authority_guard_status": "HUMAN_INTENT_RECORDED_RUN_AUTHORITY_NOT_EXECUTED",
        "human_execution_intent_present": True,
        "human_execution_intent_required": True,
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
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_d168_scope(intent_id, d166):
    return {
        "state": "D167_D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE",
        "ok": True,
        "intent_id": intent_id,
        "preflight_id": d166.get("preflight_id"),
        "validation_id": d166.get("validation_id"),
        "candidate_id": d166.get("candidate_id"),
        "response_id": d166.get("response_id"),
        "runner_id": d166.get("runner_id"),
        "plan_id": d166.get("plan_id"),
        "review_id": d166.get("review_id"),
        "scope_id": d166.get("scope_id"),
        "intake_id": d166.get("intake_id"),
        "reentry_id": d166.get("reentry_id"),
        "next_cycle_id": d166.get("next_cycle_id"),
        "cycle_closure_id": d166.get("cycle_closure_id"),
        "previous_candidate_id": d166.get("previous_candidate_id"),
        "proposal_id": d166.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D168_GATE,
        "sandbox_candidate_reentry_controlled_execution_run_scope_only": True,
        "human_execution_intent_present": True,
        "sandbox_execution_only": True,
        "candidate_execution_allowed_after_d167_only_in_sandbox": True,
        "real_apply_allowed_after_d167_by_ai": False,
        "route_insert_allowed_after_d167_by_ai": False,
        "protected_core_mutation_allowed_after_d167_by_ai": False,
        "network_allowed_after_d167_by_ai": False,
        "secret_read_allowed_after_d167_by_ai": False,
        "shell_allowed_after_d167_by_ai": False,
        "git_action_allowed_after_d167_by_ai": False,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d168_allowed_to_create": [
            "sandbox_candidate_reentry_controlled_execution_run_scope",
            "sandbox_candidate_reentry_execution_run_result",
            "sandbox_candidate_reentry_execution_safety_receipt",
            "d169_sandbox_candidate_reentry_post_execution_verification_scope",
        ],
        "d168_must_not_execute": [
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


def create_sandbox_candidate_reentry_human_execution_intent_scope(root="."):
    root = Path(root).resolve()

    d166 = read_json(root / D166_REPORT, {}) or {}
    preflight_report = read_json(root / D166_PREFLIGHT_REPORT, {}) or {}
    authority_guard = read_json(root / D166_AUTHORITY_GUARD, {}) or {}
    d167_scope = read_json(root / D166_D167_SCOPE, {}) or {}

    normalize_d166_compat(d166, preflight_report, authority_guard, d167_scope)
    errors = validate_d166(d166, preflight_report, authority_guard, d167_scope)

    intent_id = "d167-" + digest({
        "preflight_id": d166.get("preflight_id"),
        "validation_id": d166.get("validation_id"),
        "candidate_id": d166.get("candidate_id"),
        "response_id": d166.get("response_id"),
        "runner_id": d166.get("runner_id"),
        "plan_id": d166.get("plan_id"),
        "review_id": d166.get("review_id"),
        "scope_id": d166.get("scope_id"),
        "intake_id": d166.get("intake_id"),
        "reentry_id": d166.get("reentry_id"),
        "proposal_id": d166.get("proposal_id"),
    })

    intent_record = build_intent_record(intent_id, d166)
    new_authority_guard = build_authority_guard(intent_id, d166)
    d168_scope = build_d168_scope(intent_id, d166)

    for label, item in [
        ("intent_record", intent_record),
        ("authority_guard", new_authority_guard),
    ]:
        errors.extend(validate_no_ai_execution(item, prefix=label))
        require_false(item, [
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
        ], label, errors)

    require_true(intent_record, [
        "human_execution_intent_present",
        "sandbox_execution_intent_only",
        "candidate_execution_allowed_next",
    ], "intent_record", errors)
    require_false(intent_record, [
        "candidate_execution_allowed_after_d167",
        "real_apply_allowed",
    ], "intent_record", errors)

    require_true(new_authority_guard, [
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
    ], "authority_guard", errors)
    require_false(new_authority_guard, [
        "candidate_execution_allowed_after_d167",
        "candidate_execution_requested",
        "candidate_executed",
        "real_apply_allowed",
        "network_allowed",
        "secret_read_allowed",
        "shell_allowed",
        "git_action_allowed",
        "route_insert_allowed",
        "protected_core_mutation_allowed",
    ], "authority_guard", errors)

    require_true(d168_scope, [
        "sandbox_candidate_reentry_controlled_execution_run_scope_only",
        "human_execution_intent_present",
        "sandbox_execution_only",
        "candidate_execution_allowed_after_d167_only_in_sandbox",
        "fresh_intent_required",
        "human_review_required",
        "canonical_guard_schema_required",
    ], "d168_scope", errors)
    require_false(d168_scope, [
        "real_apply_allowed_after_d167_by_ai",
        "route_insert_allowed_after_d167_by_ai",
        "protected_core_mutation_allowed_after_d167_by_ai",
        "network_allowed_after_d167_by_ai",
        "secret_read_allowed_after_d167_by_ai",
        "shell_allowed_after_d167_by_ai",
        "git_action_allowed_after_d167_by_ai",
    ], "d168_scope", errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_BLOCKED"
    result = "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_CREATED" if ok else "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_BLOCKED"

    if ok:
        write_json(root / INTENT_RECORD_OUT, intent_record)
        write_json(root / AUTHORITY_GUARD_OUT, new_authority_guard)
        write_json(root / D168_SCOPE_OUT, d168_scope)

    guardrails = normalize_guard_flags({
        "sandbox_candidate_reentry_human_execution_intent_scope_only": True,
        "sandbox_candidate_reentry_human_execution_intent_record_only": True,
        "sandbox_candidate_reentry_execution_authority_guard_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "human_execution_intent_present": ok,
        "sandbox_execution_intent_only": ok,
        "candidate_execution_allowed_next": ok,
        "candidate_execution_allowed_after_d167": False,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "apply_requested": False,
        "apply_executed": False,
        "approval_for_d168_sandbox_candidate_reentry_controlled_execution_run_scope_only": ok,
        "real_apply_allowed_after_d167_by_ai": False,
        "route_insert_allowed_after_d167_by_ai": False,
        "protected_core_mutation_allowed_after_d167_by_ai": False,
        "network_allowed_after_d167_by_ai": False,
        "secret_read_allowed_after_d167_by_ai": False,
        "shell_allowed_after_d167_by_ai": False,
        "git_action_allowed_after_d167_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "intent_id": intent_id,
        "preflight_id": d166.get("preflight_id"),
        "validation_id": d166.get("validation_id"),
        "candidate_id": d166.get("candidate_id"),
        "response_id": d166.get("response_id"),
        "runner_id": d166.get("runner_id"),
        "plan_id": d166.get("plan_id"),
        "review_id": d166.get("review_id"),
        "scope_id": d166.get("scope_id"),
        "intake_id": d166.get("intake_id"),
        "reentry_id": d166.get("reentry_id"),
        "next_cycle_id": d166.get("next_cycle_id"),
        "cycle_closure_id": d166.get("cycle_closure_id"),
        "previous_candidate_id": d166.get("previous_candidate_id"),
        "proposal_id": d166.get("proposal_id"),
        "source_d166_report": D166_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "human_execution_intent_record": intent_record if ok else {},
        "execution_authority_guard": new_authority_guard if ok else {},
        "d168_scope": d168_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "intent_id": intent_id,
            "preflight_id": d166.get("preflight_id"),
            "validation_id": d166.get("validation_id"),
            "candidate_id": d166.get("candidate_id"),
            "response_id": d166.get("response_id"),
            "runner_id": d166.get("runner_id"),
            "plan_id": d166.get("plan_id"),
            "review_id": d166.get("review_id"),
            "scope_id": d166.get("scope_id"),
            "intake_id": d166.get("intake_id"),
            "reentry_id": d166.get("reentry_id"),
            "next_cycle_id": d166.get("next_cycle_id"),
            "proposal_id": d166.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D167_PLUS" if ok else "BLOCKED",
            "human_execution_intent_status": "HUMAN_EXECUTION_INTENT_RECORDED_FOR_SANDBOX_ONLY_NO_REAL_APPLY" if ok else "BLOCKED",
            "authority_guard_status": "HUMAN_INTENT_RECORDED_RUN_AUTHORITY_NOT_EXECUTED" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_CONTROLLED_EXECUTION_RUN_SCOPE" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D168_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_human_execution_intent_scope_created": ok,
            "human_execution_intent_record_created": ok,
            "execution_authority_guard_created": ok,
            "d168_scope_created": ok,
            "candidate_executed": False,
            "apply_executed": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D168 may create sandbox controlled execution run scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_human_execution_intent_scope(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_human_execution_intent_scope import create_sandbox_candidate_reentry_human_execution_intent_scope


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


class TestD167SandboxCandidateReentryHumanExecutionIntentScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

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

        d166 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_READY",
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
                "sandbox_candidate_reentry_controlled_execution_preflight_scope_only": True,
                "sandbox_candidate_reentry_controlled_execution_preflight_report_only": True,
                "sandbox_candidate_reentry_execution_authority_guard_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "candidate_files_static_validated": True,
                "controlled_execution_preflight_created": True,
                "execution_authority_guard_created": True,
                "candidate_execution_allowed_after_d166": False,
                "candidate_execution_requested": False,
                "candidate_executed": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "approval_for_d167_sandbox_candidate_reentry_human_execution_intent_scope_only": True,
                "real_apply_allowed_after_d166_by_ai": False,
                "route_insert_allowed_after_d166_by_ai": False,
                "protected_core_mutation_allowed_after_d166_by_ai": False,
                "network_allowed_after_d166_by_ai": False,
                "secret_read_allowed_after_d166_by_ai": False,
                "shell_allowed_after_d166_by_ai": False,
                "git_action_allowed_after_d166_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D166_PLUS",
                "controlled_execution_preflight_status": "CONTROLLED_EXECUTION_PREFLIGHT_CREATED_NO_EXECUTION",
                "authority_guard_status": "EXECUTION_AUTHORITY_GUARD_CREATED_NO_EXECUTION",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_HUMAN_EXECUTION_INTENT",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_ONLY",
                "next_step": "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE",
            },
        }

        preflight_report = {
            **no_ai_flags(),
            "ok": True,
            "controlled_execution_preflight_status": "CONTROLLED_EXECUTION_PREFLIGHT_CREATED_NO_EXECUTION",
            "candidate_execution_policy": "HUMAN_INTENT_REQUIRED_BEFORE_ANY_SANDBOX_EXECUTION",
            "candidate_files_static_validated": True,
            "candidate_execution_allowed_after_d166": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        authority_guard = {
            **no_ai_flags(),
            "ok": True,
            "authority_mode": "SANDBOX_EXECUTION_AUTHORITY_GUARD_ONLY_NO_EXECUTION",
            "authority_guard_status": "EXECUTION_AUTHORITY_GUARD_CREATED_NO_EXECUTION",
            "human_execution_intent_required": True,
            "candidate_execution_allowed": False,
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
            "no_candidate_execution": True,
            "no_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
        }

        d167_scope = {
            "ok": True,
            "allowed_next_gate": "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE",
            "sandbox_candidate_reentry_human_execution_intent_scope_only": True,
            "human_execution_intent_required": True,
            "candidate_files_static_validated": True,
            "controlled_execution_preflight_created": True,
            "execution_authority_guard_created": True,
            "candidate_execution_allowed_after_d166": False,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d166_by_ai": False,
            "route_insert_allowed_after_d166_by_ai": False,
            "protected_core_mutation_allowed_after_d166_by_ai": False,
            "network_allowed_after_d166_by_ai": False,
            "secret_read_allowed_after_d166_by_ai": False,
            "shell_allowed_after_d166_by_ai": False,
            "git_action_allowed_after_d166_by_ai": False,
        }

        write(root / "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json", d166)
        write(root / "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_report.json", preflight_report)
        write(root / "reports/d166_sandbox_candidate_reentry_execution_authority_guard.json", authority_guard)
        write(root / "reports/d166_d167_sandbox_candidate_reentry_human_execution_intent_scope.json", d167_scope)
        return td, root

    def test_creates_human_execution_intent_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_human_execution_intent_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_ONLY")
            self.assertEqual(r["d168_scope"]["allowed_next_gate"], "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE")
            self.assertTrue(r["guardrails"]["human_execution_intent_present"])
            self.assertTrue(r["guardrails"]["candidate_execution_allowed_next"])
            self.assertFalse(r["guardrails"]["candidate_executed"])
            self.assertFalse(r["guardrails"]["apply_executed"])
            self.assertTrue((root / "reports/d167_sandbox_candidate_reentry_human_execution_intent_scope.json").exists())
            self.assertTrue((root / "reports/d167_sandbox_candidate_reentry_human_execution_intent_record.json").exists())
            self.assertTrue((root / "reports/d167_sandbox_candidate_reentry_execution_authority_guard.json").exists())
            self.assertTrue((root / "reports/d167_d168_sandbox_candidate_reentry_controlled_execution_run_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d166(self):
        td, root = self.root()
        try:
            (root / "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json").unlink()
            r = create_sandbox_candidate_reentry_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_preflight_report_executed_candidate(self):
        td, root = self.root()
        try:
            p = root / "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_report.json"
            data = json.loads(p.read_text())
            data["candidate_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d167_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d166_d167_sandbox_candidate_reentry_human_execution_intent_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d166_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_authority_guard_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d166_sandbox_candidate_reentry_execution_authority_guard.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_human_execution_intent_scope(root)
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

print("D167 SANDBOX CANDIDATE REENTRY HUMAN EXECUTION INTENT SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_reentry_human_execution_intent_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d167_sandbox_candidate_reentry_human_execution_intent_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_reentry_human_execution_intent_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d167_sandbox_candidate_reentry_human_execution_intent_scope", "-v"], check=True)

print("\n== run D167 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_reentry_human_execution_intent_scope import create_sandbox_candidate_reentry_human_execution_intent_scope\n"
    "r=create_sandbox_candidate_reentry_human_execution_intent_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d167_sandbox_candidate_reentry_human_execution_intent_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_reentry_human_execution_intent_scope.py",
    "tests/test_d167_sandbox_candidate_reentry_human_execution_intent_scope.py",
    "reports/d167_sandbox_candidate_reentry_human_execution_intent_scope.json",
    "reports/d167_sandbox_candidate_reentry_human_execution_intent_record.json",
    "reports/d167_sandbox_candidate_reentry_execution_authority_guard.json",
    "reports/d167_d168_sandbox_candidate_reentry_controlled_execution_run_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D167 sandbox candidate reentry human execution intent scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D167 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD167 SANDBOX CANDIDATE REENTRY HUMAN EXECUTION INTENT SCOPE BOOT DONE")
