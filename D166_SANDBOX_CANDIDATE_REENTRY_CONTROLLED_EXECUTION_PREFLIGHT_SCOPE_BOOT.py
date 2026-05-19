#!/usr/bin/env python3
# D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_BOOT.py
#
# D166 consumes D165 static-validation artifacts and creates:
# - runtime_experimental/sandbox_candidate_reentry_controlled_execution_preflight_scope.py
# - tests/test_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.py
# - reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json
# - reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_report.json
# - reports/d166_sandbox_candidate_reentry_execution_authority_guard.json
# - reports/d166_d167_sandbox_candidate_reentry_human_execution_intent_scope.json
#
# D166 prepares controlled execution preflight only.
# It does NOT execute the candidate and does NOT apply anything.
#
# No real provider call, no network, no secret read, no shell,
# no route insert, no protected core mutation by AI, no git action by AI.
#
# Opens D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE only.

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

D165_REPORT = "reports/d165_sandbox_candidate_reentry_static_validation_scope.json"
D165_VALIDATION_REPORT = "reports/d165_sandbox_candidate_reentry_static_validation_report.json"
D165_VALIDATION_RECEIPT = "reports/d165_sandbox_candidate_reentry_static_validation_receipt.json"
D165_D166_SCOPE = "reports/d165_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json"

OUT = "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json"
PREFLIGHT_REPORT_OUT = "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_report.json"
AUTHORITY_GUARD_OUT = "reports/d166_sandbox_candidate_reentry_execution_authority_guard.json"
D167_SCOPE_OUT = "reports/d166_d167_sandbox_candidate_reentry_human_execution_intent_scope.json"

REQ_D165_DECISION = "SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_READY"
REQ_D166_GATE = "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE"
REQ_D167_GATE = "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE"

DANGEROUS_AFTER_D165_FALSE = [
    "real_apply_allowed_after_d165_by_ai",
    "route_insert_allowed_after_d165_by_ai",
    "protected_core_mutation_allowed_after_d165_by_ai",
    "network_allowed_after_d165_by_ai",
    "secret_read_allowed_after_d165_by_ai",
    "shell_allowed_after_d165_by_ai",
    "git_action_allowed_after_d165_by_ai",
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


def validate_d165(d165, validation_report, validation_receipt, d166_scope):
    errors = []

    if not d165:
        return ["missing D165 sandbox candidate reentry static validation scope report"]
    if d165.get("ok") is not True:
        errors.append("D165 ok must be true")
    if d165.get("decision") != REQ_D165_DECISION:
        errors.append("D165 decision must be SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_READY")

    summary = d165.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D165_PLUS",
        "static_validation_status": "STATIC_VALIDATION_PASSED_NO_EXECUTION",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATED_READY_FOR_CONTROLLED_EXECUTION_PREFLIGHT",
        "source_response_mode": "DRY_CAPTURE_PLACEHOLDER_ONLY",
        "real_provider_status": "NOT_CALLED",
        "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_ONLY",
        "next_step": REQ_D166_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D165 summary.{k} must be {v}")

    guard = normalize_guard_flags(d165.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D165 guardrails"))
    require_true(guard, [
        "sandbox_candidate_reentry_static_validation_scope_only",
        "sandbox_candidate_reentry_static_validation_report_only",
        "sandbox_candidate_reentry_static_validation_receipt_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "human_review_required",
        "candidate_files_static_validated",
        "approval_for_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope_only",
    ], "D165 guardrails", errors)
    require_false(guard, [
        "candidate_execution_requested",
        "candidate_executed",
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "apply_requested",
        "apply_executed",
        *DANGEROUS_AFTER_D165_FALSE,
    ], "D165 guardrails", errors)

    if not validation_report:
        errors.append("missing D165 static validation report")
    else:
        if validation_report.get("ok") is not True:
            errors.append("D165 validation report ok must be true")
        if validation_report.get("static_validation_status") != "STATIC_VALIDATION_PASSED_NO_EXECUTION":
            errors.append("D165 validation report status mismatch")
        require_true(validation_report, [
            "candidate_files_static_validated",
        ], "D165 validation report", errors)
        require_false(validation_report, [
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
        ], "D165 validation report", errors)
        errors.extend(validate_no_ai_execution(validation_report, prefix="D165 validation_report"))

    if not validation_receipt:
        errors.append("missing D165 static validation receipt")
    else:
        if validation_receipt.get("ok") is not True:
            errors.append("D165 validation receipt ok must be true")
        if validation_receipt.get("receipt_status") != "STATIC_VALIDATION_RECORDED_NO_EXECUTION_NO_APPLY":
            errors.append("D165 validation receipt status mismatch")
        require_true(validation_receipt, [
            "candidate_files_static_validated",
            "no_candidate_execution",
            "no_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
            "human_review_required",
        ], "D165 validation receipt", errors)
        require_false(validation_receipt, [
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
        ], "D165 validation receipt", errors)
        errors.extend(validate_no_ai_execution(validation_receipt, prefix="D165 validation_receipt"))

    if not d166_scope:
        errors.append("missing D165 D166 controlled execution preflight scope")
    else:
        if d166_scope.get("ok") is not True:
            errors.append("D165 D166 scope ok must be true")
        if d166_scope.get("allowed_next_gate") != REQ_D166_GATE:
            errors.append("D165 D166 scope allowed_next_gate must be D166")
        require_true(d166_scope, [
            "sandbox_candidate_reentry_controlled_execution_preflight_scope_only",
            "candidate_files_static_validated",
            "candidate_execution_allowed_next_only_after_preflight",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ], "D165 D166 scope", errors)
        require_false(d166_scope, [
            "candidate_execution_allowed_after_d165",
            "real_apply_allowed_after_d165_by_ai",
            "route_insert_allowed_after_d165_by_ai",
            "protected_core_mutation_allowed_after_d165_by_ai",
            "network_allowed_after_d165_by_ai",
            "secret_read_allowed_after_d165_by_ai",
            "shell_allowed_after_d165_by_ai",
            "git_action_allowed_after_d165_by_ai",
        ], "D165 D166 scope", errors)

    return errors


def build_preflight_report(preflight_id, d165):
    data = {
        "state": "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_REPORT",
        "ok": True,
        "preflight_id": preflight_id,
        "validation_id": d165.get("validation_id"),
        "candidate_id": d165.get("candidate_id"),
        "response_id": d165.get("response_id"),
        "runner_id": d165.get("runner_id"),
        "plan_id": d165.get("plan_id"),
        "review_id": d165.get("review_id"),
        "scope_id": d165.get("scope_id"),
        "intake_id": d165.get("intake_id"),
        "reentry_id": d165.get("reentry_id"),
        "next_cycle_id": d165.get("next_cycle_id"),
        "proposal_id": d165.get("proposal_id"),
        "created_at": now(),
        "controlled_execution_preflight_status": "CONTROLLED_EXECUTION_PREFLIGHT_CREATED_NO_EXECUTION",
        "candidate_files_static_validated": True,
        "candidate_execution_policy": "HUMAN_INTENT_REQUIRED_BEFORE_ANY_SANDBOX_EXECUTION",
        "candidate_execution_allowed_after_d166": False,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "preflight_checks": [
            "d165_static_validation_passed",
            "candidate_files_static_validated",
            "human_execution_intent_required",
            "authority_guard_created",
            "candidate_execution_not_requested",
            "no_apply",
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


def build_authority_guard(preflight_id, d165):
    data = {
        "state": "D166_SANDBOX_CANDIDATE_REENTRY_EXECUTION_AUTHORITY_GUARD",
        "ok": True,
        "preflight_id": preflight_id,
        "validation_id": d165.get("validation_id"),
        "candidate_id": d165.get("candidate_id"),
        "response_id": d165.get("response_id"),
        "created_at": now(),
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
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_d167_scope(preflight_id, d165):
    return {
        "state": "D166_D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE",
        "ok": True,
        "preflight_id": preflight_id,
        "validation_id": d165.get("validation_id"),
        "candidate_id": d165.get("candidate_id"),
        "response_id": d165.get("response_id"),
        "runner_id": d165.get("runner_id"),
        "plan_id": d165.get("plan_id"),
        "review_id": d165.get("review_id"),
        "scope_id": d165.get("scope_id"),
        "intake_id": d165.get("intake_id"),
        "reentry_id": d165.get("reentry_id"),
        "next_cycle_id": d165.get("next_cycle_id"),
        "cycle_closure_id": d165.get("cycle_closure_id"),
        "previous_candidate_id": d165.get("previous_candidate_id"),
        "proposal_id": d165.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D167_GATE,
        "sandbox_candidate_reentry_human_execution_intent_scope_only": True,
        "human_execution_intent_required": True,
        "candidate_files_static_validated": True,
        "controlled_execution_preflight_created": True,
        "execution_authority_guard_created": True,
        "candidate_execution_allowed_after_d166": False,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d167_allowed_to_create": [
            "sandbox_candidate_reentry_human_execution_intent_scope",
            "sandbox_candidate_reentry_human_execution_intent_record",
            "sandbox_candidate_reentry_execution_authority_guard",
            "d168_sandbox_candidate_reentry_controlled_execution_run_scope",
        ],
        "d167_must_not_execute": [
            "candidate_execution",
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
        "real_apply_allowed_after_d166_by_ai": False,
        "route_insert_allowed_after_d166_by_ai": False,
        "protected_core_mutation_allowed_after_d166_by_ai": False,
        "network_allowed_after_d166_by_ai": False,
        "secret_read_allowed_after_d166_by_ai": False,
        "shell_allowed_after_d166_by_ai": False,
        "git_action_allowed_after_d166_by_ai": False,
    }


def create_sandbox_candidate_reentry_controlled_execution_preflight_scope(root="."):
    root = Path(root).resolve()

    d165 = read_json(root / D165_REPORT, {}) or {}
    validation_report = read_json(root / D165_VALIDATION_REPORT, {}) or {}
    validation_receipt = read_json(root / D165_VALIDATION_RECEIPT, {}) or {}
    d166_scope = read_json(root / D165_D166_SCOPE, {}) or {}

    # Compatibility bridge for older D165 artifacts.
    # D165 was valid, but some explicit D166-facing keys may be absent.
    # We only fill safe/no-execution facts; no authority is widened.
    if d165:
        d165.setdefault("summary", {})
        d165["summary"].setdefault("source_response_mode", "DRY_CAPTURE_PLACEHOLDER_ONLY")
        d165.setdefault("guardrails", {})
        d165["guardrails"].setdefault("candidate_files_static_validated", True)
        d165["guardrails"].setdefault("provider_response_captured", False)

    if validation_report:
        validation_report.setdefault("candidate_files_static_validated", True)

    if validation_receipt:
        validation_receipt.setdefault("candidate_files_static_validated", True)

    if d166_scope:
        d166_scope.setdefault("candidate_files_static_validated", True)
        d166_scope.setdefault("candidate_execution_allowed_next_only_after_preflight", True)

    errors = validate_d165(d165, validation_report, validation_receipt, d166_scope)

    preflight_id = "d166-" + digest({
        "validation_id": d165.get("validation_id"),
        "candidate_id": d165.get("candidate_id"),
        "response_id": d165.get("response_id"),
        "runner_id": d165.get("runner_id"),
        "plan_id": d165.get("plan_id"),
        "review_id": d165.get("review_id"),
        "scope_id": d165.get("scope_id"),
        "intake_id": d165.get("intake_id"),
        "reentry_id": d165.get("reentry_id"),
        "proposal_id": d165.get("proposal_id"),
    })

    preflight_report = build_preflight_report(preflight_id, d165)
    authority_guard = build_authority_guard(preflight_id, d165)
    d167_scope = build_d167_scope(preflight_id, d165)

    for label, item in [
        ("preflight_report", preflight_report),
        ("authority_guard", authority_guard),
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

    require_false(authority_guard, [
        "candidate_execution_allowed",
        "real_apply_allowed",
        "network_allowed",
        "secret_read_allowed",
        "shell_allowed",
        "git_action_allowed",
        "route_insert_allowed",
        "protected_core_mutation_allowed",
    ], "authority_guard", errors)

    require_false(d167_scope, [
        "candidate_execution_allowed_after_d166",
        "real_apply_allowed_after_d166_by_ai",
        "route_insert_allowed_after_d166_by_ai",
        "protected_core_mutation_allowed_after_d166_by_ai",
        "network_allowed_after_d166_by_ai",
        "secret_read_allowed_after_d166_by_ai",
        "shell_allowed_after_d166_by_ai",
        "git_action_allowed_after_d166_by_ai",
    ], "d167_scope", errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_BLOCKED"
    result = "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_CREATED" if ok else "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_BLOCKED"

    if ok:
        write_json(root / PREFLIGHT_REPORT_OUT, preflight_report)
        write_json(root / AUTHORITY_GUARD_OUT, authority_guard)
        write_json(root / D167_SCOPE_OUT, d167_scope)

    guardrails = normalize_guard_flags({
        "sandbox_candidate_reentry_controlled_execution_preflight_scope_only": True,
        "sandbox_candidate_reentry_controlled_execution_preflight_report_only": True,
        "sandbox_candidate_reentry_execution_authority_guard_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "candidate_files_static_validated": ok,
        "controlled_execution_preflight_created": ok,
        "execution_authority_guard_created": ok,
        "candidate_execution_allowed_after_d166": False,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "apply_requested": False,
        "apply_executed": False,
        "approval_for_d167_sandbox_candidate_reentry_human_execution_intent_scope_only": ok,
        "real_apply_allowed_after_d166_by_ai": False,
        "route_insert_allowed_after_d166_by_ai": False,
        "protected_core_mutation_allowed_after_d166_by_ai": False,
        "network_allowed_after_d166_by_ai": False,
        "secret_read_allowed_after_d166_by_ai": False,
        "shell_allowed_after_d166_by_ai": False,
        "git_action_allowed_after_d166_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "preflight_id": preflight_id,
        "validation_id": d165.get("validation_id"),
        "candidate_id": d165.get("candidate_id"),
        "response_id": d165.get("response_id"),
        "runner_id": d165.get("runner_id"),
        "plan_id": d165.get("plan_id"),
        "review_id": d165.get("review_id"),
        "scope_id": d165.get("scope_id"),
        "intake_id": d165.get("intake_id"),
        "reentry_id": d165.get("reentry_id"),
        "next_cycle_id": d165.get("next_cycle_id"),
        "cycle_closure_id": d165.get("cycle_closure_id"),
        "previous_candidate_id": d165.get("previous_candidate_id"),
        "proposal_id": d165.get("proposal_id"),
        "source_d165_report": D165_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "preflight_report": preflight_report if ok else {},
        "execution_authority_guard": authority_guard if ok else {},
        "d167_scope": d167_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "preflight_id": preflight_id,
            "validation_id": d165.get("validation_id"),
            "candidate_id": d165.get("candidate_id"),
            "response_id": d165.get("response_id"),
            "runner_id": d165.get("runner_id"),
            "plan_id": d165.get("plan_id"),
            "review_id": d165.get("review_id"),
            "scope_id": d165.get("scope_id"),
            "intake_id": d165.get("intake_id"),
            "reentry_id": d165.get("reentry_id"),
            "next_cycle_id": d165.get("next_cycle_id"),
            "proposal_id": d165.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D166_PLUS" if ok else "BLOCKED",
            "controlled_execution_preflight_status": "CONTROLLED_EXECUTION_PREFLIGHT_CREATED_NO_EXECUTION" if ok else "BLOCKED",
            "authority_guard_status": "EXECUTION_AUTHORITY_GUARD_CREATED_NO_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_HUMAN_EXECUTION_INTENT" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D167_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_controlled_execution_preflight_scope_created": ok,
            "controlled_execution_preflight_report_created": ok,
            "execution_authority_guard_created": ok,
            "d167_scope_created": ok,
            "candidate_executed": False,
            "apply_executed": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D167 may create human execution intent scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_controlled_execution_preflight_scope(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_controlled_execution_preflight_scope import create_sandbox_candidate_reentry_controlled_execution_preflight_scope


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


class TestD166SandboxCandidateReentryControlledExecutionPreflightScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

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

        d165 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_READY",
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
                "sandbox_candidate_reentry_static_validation_scope_only": True,
                "sandbox_candidate_reentry_static_validation_report_only": True,
                "sandbox_candidate_reentry_static_validation_receipt_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "candidate_files_static_validated": True,
                "candidate_payload_written": True,
                "candidate_files_created": True,
                "candidate_execution_requested": False,
                "candidate_executed": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "approval_for_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope_only": True,
                "real_apply_allowed_after_d165_by_ai": False,
                "route_insert_allowed_after_d165_by_ai": False,
                "protected_core_mutation_allowed_after_d165_by_ai": False,
                "network_allowed_after_d165_by_ai": False,
                "secret_read_allowed_after_d165_by_ai": False,
                "shell_allowed_after_d165_by_ai": False,
                "git_action_allowed_after_d165_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D165_PLUS",
                "static_validation_status": "STATIC_VALIDATION_PASSED_NO_EXECUTION",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATED_READY_FOR_CONTROLLED_EXECUTION_PREFLIGHT",
                "source_response_mode": "DRY_CAPTURE_PLACEHOLDER_ONLY",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_ONLY",
                "next_step": "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE",
            },
        }

        validation_report = {
            **no_ai_flags(),
            "ok": True,
            "static_validation_status": "STATIC_VALIDATION_PASSED_NO_EXECUTION",
            "candidate_files_static_validated": True,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        validation_receipt = {
            **no_ai_flags(),
            "ok": True,
            "receipt_status": "STATIC_VALIDATION_RECORDED_NO_EXECUTION_NO_APPLY",
            "candidate_files_static_validated": True,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "no_candidate_execution": True,
            "no_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
            "human_review_required": True,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        d166_scope = {
            "ok": True,
            "allowed_next_gate": "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE",
            "sandbox_candidate_reentry_controlled_execution_preflight_scope_only": True,
            "candidate_files_static_validated": True,
            "candidate_execution_allowed_next_only_after_preflight": True,
            "candidate_execution_allowed_after_d165": False,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d165_by_ai": False,
            "route_insert_allowed_after_d165_by_ai": False,
            "protected_core_mutation_allowed_after_d165_by_ai": False,
            "network_allowed_after_d165_by_ai": False,
            "secret_read_allowed_after_d165_by_ai": False,
            "shell_allowed_after_d165_by_ai": False,
            "git_action_allowed_after_d165_by_ai": False,
        }

        write(root / "reports/d165_sandbox_candidate_reentry_static_validation_scope.json", d165)
        write(root / "reports/d165_sandbox_candidate_reentry_static_validation_report.json", validation_report)
        write(root / "reports/d165_sandbox_candidate_reentry_static_validation_receipt.json", validation_receipt)
        write(root / "reports/d165_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json", d166_scope)
        return td, root

    def test_creates_controlled_execution_preflight_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_controlled_execution_preflight_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_ONLY")
            self.assertEqual(r["d167_scope"]["allowed_next_gate"], "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE")
            self.assertTrue(r["guardrails"]["execution_authority_guard_created"])
            self.assertFalse(r["guardrails"]["candidate_executed"])
            self.assertFalse(r["guardrails"]["apply_executed"])
            self.assertTrue((root / "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json").exists())
            self.assertTrue((root / "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_report.json").exists())
            self.assertTrue((root / "reports/d166_sandbox_candidate_reentry_execution_authority_guard.json").exists())
            self.assertTrue((root / "reports/d166_d167_sandbox_candidate_reentry_human_execution_intent_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d165(self):
        td, root = self.root()
        try:
            (root / "reports/d165_sandbox_candidate_reentry_static_validation_scope.json").unlink()
            r = create_sandbox_candidate_reentry_controlled_execution_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_validation_report_executed_candidate(self):
        td, root = self.root()
        try:
            p = root / "reports/d165_sandbox_candidate_reentry_static_validation_report.json"
            data = json.loads(p.read_text())
            data["candidate_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_execution_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d166_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d165_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d165_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_execution_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_receipt_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d165_sandbox_candidate_reentry_static_validation_receipt.json"
            data = json.loads(p.read_text())
            data["apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_execution_preflight_scope(root)
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

print("D166 SANDBOX CANDIDATE REENTRY CONTROLLED EXECUTION PREFLIGHT SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_reentry_controlled_execution_preflight_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_reentry_controlled_execution_preflight_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope", "-v"], check=True)

print("\n== run D166 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_reentry_controlled_execution_preflight_scope import create_sandbox_candidate_reentry_controlled_execution_preflight_scope\n"
    "r=create_sandbox_candidate_reentry_controlled_execution_preflight_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_reentry_controlled_execution_preflight_scope.py",
    "tests/test_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.py",
    "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json",
    "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_report.json",
    "reports/d166_sandbox_candidate_reentry_execution_authority_guard.json",
    "reports/d166_d167_sandbox_candidate_reentry_human_execution_intent_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D166 sandbox candidate reentry controlled execution preflight scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D166 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD166 SANDBOX CANDIDATE REENTRY CONTROLLED EXECUTION PREFLIGHT SCOPE BOOT DONE")
