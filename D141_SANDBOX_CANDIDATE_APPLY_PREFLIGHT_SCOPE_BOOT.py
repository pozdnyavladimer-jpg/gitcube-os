#!/usr/bin/env python3
# D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_BOOT.py
#
# D141 consumes D140 post-execution verification artifacts and creates:
# - runtime_experimental/sandbox_candidate_apply_preflight_scope.py
# - tests/test_d141_sandbox_candidate_apply_preflight_scope.py
# - reports/d141_sandbox_candidate_apply_preflight_scope.json
# - reports/d141_sandbox_candidate_apply_preflight_report.json
# - reports/d141_sandbox_candidate_apply_blockers.json
# - reports/d141_d142_sandbox_candidate_human_apply_intent_scope.json
#
# APPLY PREFLIGHT ONLY:
# no apply, no route insert, no protected core mutation, no shell, no network,
# no secret read, no candidate execution, no AI git action.
#
# D141 opens D142 Sandbox Candidate Human Apply Intent Scope.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE = r'''
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D140_REPORT = "reports/d140_sandbox_candidate_post_execution_verification_scope.json"
D140_VERIFY_REPORT = "reports/d140_sandbox_candidate_post_execution_verification_report.json"
D140_INTEGRITY_RECEIPT = "reports/d140_sandbox_candidate_execution_integrity_receipt.json"
D140_D141_SCOPE = "reports/d140_d141_sandbox_candidate_apply_preflight_scope.json"

OUT = "reports/d141_sandbox_candidate_apply_preflight_scope.json"
APPLY_PREFLIGHT_REPORT_OUT = "reports/d141_sandbox_candidate_apply_preflight_report.json"
APPLY_BLOCKERS_OUT = "reports/d141_sandbox_candidate_apply_blockers.json"
D142_SCOPE_OUT = "reports/d141_d142_sandbox_candidate_human_apply_intent_scope.json"

REQ_D140_DECISION = "SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_READY"
REQ_D141_GATE = "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE"
REQ_D142_GATE = "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE"
REQ_D140_APPROVAL_SCOPE = "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_ONLY"

FALSE_GUARD_KEYS = [
    "external_ai_called", "network_accessed", "api_key_read", "secret_read",
    "shell_from_ai_executed", "runtime_code_mutated", "protected_core_mutated",
    "canonical_memory_mutated", "actual_apply_executed", "route_inserted",
    "git_commit_by_ai", "git_push_by_ai", "rollback_executed", "restore_executed",
]

UNSAFE_STATUS_EXPECTED = {
    "real_provider_status": "NOT_CALLED",
    "network_status": "NOT_ACCESSED",
    "secret_status": "NOT_READ",
    "shell_status": "NOT_EXECUTED",
    "real_apply_by_ai_status": "BLOCKED",
    "route_insert_status": "BLOCKED",
    "protected_core_status": "UNTOUCHED_BY_AI",
}

UNSAFE_BOOLEAN_KEYS = [
    "actual_apply_executed", "real_apply_executed", "route_inserted",
    "protected_core_mutated", "canonical_memory_mutated", "external_ai_called",
    "network_accessed", "api_key_read", "secret_read", "shell_from_ai_executed",
    "shell_executed_by_ai", "git_commit_by_ai", "git_push_by_ai", "git_action_by_ai",
    "rollback_executed", "restore_executed",
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


def check_false_map(name, obj, errors):
    if not isinstance(obj, dict):
        return
    for key in UNSAFE_BOOLEAN_KEYS:
        if key in obj and obj.get(key) is not False:
            errors.append(f"{name} {key} must be false")


def validate_d140(d140, verify_report, integrity_receipt, d141_scope):
    errors = []

    if not d140:
        return ["missing D140 sandbox candidate post execution verification scope report"]

    if d140.get("ok") is not True:
        errors.append("D140 ok must be true")
    if d140.get("decision") != REQ_D140_DECISION:
        errors.append("D140 decision must be SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_READY")

    summary = d140.get("summary", {})
    expected = {
        "post_execution_validation_status": "SANDBOX_EXECUTION_VERIFIED_NO_APPLY",
        "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
        "execution_result_status": "PRESENT_AND_VALIDATED",
        "approval_scope": REQ_D140_APPROVAL_SCOPE,
        "next_step": REQ_D141_GATE,
    }
    expected.update(UNSAFE_STATUS_EXPECTED)
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D140 summary.{key} must be {value}")

    guard = d140.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D140 guardrails.{key} must be false")
    for key in [
        "sandbox_candidate_post_execution_verification_scope_only",
        "post_execution_verification_report_only",
        "execution_integrity_receipt_only",
        "approval_for_d141_apply_preflight_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D140 guardrails.{key} must be true")
    for key in ["candidate_executed_now", "approval_for_real_apply_by_ai", "candidate_execution_allowed_by_ai", "commands_executed_by_ai"]:
        if guard.get(key) is not False:
            errors.append(f"D140 guardrails.{key} must be false")

    if not verify_report:
        errors.append("missing D140 sandbox candidate post execution verification report")
    else:
        if verify_report.get("ok") is not True:
            errors.append("D140 verification report ok must be true")
        if verify_report.get("verification_mode") != "POST_EXECUTION_VERIFICATION_ONLY_NO_APPLY":
            errors.append("D140 verification report mode must be post-execution only/no apply")
        for key in ["sandbox_result_present", "execution_status_verified", "candidate_status_verified", "candidate_executed_in_sandbox", "human_review_required"]:
            if verify_report.get(key) is not True:
                errors.append(f"D140 verification report {key} must be true")
        if verify_report.get("post_execution_validation_status") != "SANDBOX_EXECUTION_VERIFIED_NO_APPLY":
            errors.append("D140 verification report post_execution_validation_status must be SANDBOX_EXECUTION_VERIFIED_NO_APPLY")
        if verify_report.get("result_integrity_status") != "PASS":
            errors.append("D140 verification report result_integrity_status must be PASS")
        check_false_map("D140 verification report", verify_report, errors)

    if not integrity_receipt:
        errors.append("missing D140 sandbox candidate execution integrity receipt")
    else:
        if integrity_receipt.get("ok") is not True:
            errors.append("D140 integrity receipt ok must be true")
        if integrity_receipt.get("receipt_mode") != "EXECUTION_INTEGRITY_RECEIPT_ONLY_NO_APPLY":
            errors.append("D140 integrity receipt mode must be execution integrity receipt only/no apply")
        if integrity_receipt.get("sandbox_execution_completed") is not True:
            errors.append("D140 integrity receipt sandbox_execution_completed must be true")
        if integrity_receipt.get("candidate_status") != "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED":
            errors.append("D140 integrity receipt candidate_status must be materialized executed in sandbox not applied")
        for key, value in UNSAFE_STATUS_EXPECTED.items():
            if integrity_receipt.get(key) != value:
                errors.append(f"D140 integrity receipt {key} must be {value}")
        check_false_map("D140 integrity receipt", integrity_receipt, errors)

    if not d141_scope:
        errors.append("missing D140 D141 sandbox candidate apply preflight scope")
    else:
        if d141_scope.get("ok") is not True:
            errors.append("D140 D141 scope ok must be true")
        if d141_scope.get("allowed_next_gate") != REQ_D141_GATE:
            errors.append("D140 D141 scope allowed_next_gate must be D141")
        if d141_scope.get("sandbox_candidate_apply_preflight_scope_only") is not True:
            errors.append("D140 D141 scope must be apply preflight only")
        if d141_scope.get("human_review_required") is not True:
            errors.append("D140 D141 scope must require human review")
        if d141_scope.get("candidate_executed_in_sandbox_after_d139") is not True:
            errors.append("D140 D141 scope must confirm candidate was executed in sandbox after D139")
        for key in [
            "candidate_executed_after_d140_by_ai", "real_apply_allowed_after_d140_by_ai",
            "route_insert_allowed_after_d140_by_ai", "protected_core_mutation_allowed_after_d140_by_ai",
            "network_allowed_after_d140_by_ai", "secret_read_allowed_after_d140_by_ai",
            "shell_allowed_after_d140_by_ai", "git_action_allowed_after_d140_by_ai",
        ]:
            if d141_scope.get(key) is not False:
                errors.append(f"D140 D141 scope {key} must be false")

    return errors


def build_apply_preflight_report(preflight_id, d140):
    summary = d140.get("summary", {})
    return {
        "state": "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_REPORT",
        "ok": True,
        "preflight_id": preflight_id,
        "verification_id": d140.get("verification_id") or summary.get("verification_id"),
        "run_id": d140.get("run_id") or summary.get("run_id"),
        "candidate_id": d140.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d140.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "preflight_mode": "APPLY_PREFLIGHT_ONLY_NO_APPLY",
        "post_execution_validation_required": True,
        "post_execution_validation_status": "SANDBOX_EXECUTION_VERIFIED_NO_APPLY",
        "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
        "apply_preflight_status": "APPLY_PREFLIGHT_CREATED_NO_APPLY",
        "apply_readiness_status": "READY_FOR_HUMAN_APPLY_INTENT_SCOPE_ONLY",
        "candidate_executed_in_sandbox": True,
        "candidate_executed_now": False,
        "candidate_executed_by_ai": False,
        "actual_apply_executed": False,
        "real_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_apply_blockers(preflight_id, d140):
    summary = d140.get("summary", {})
    return {
        "state": "D141_SANDBOX_CANDIDATE_APPLY_BLOCKERS",
        "ok": True,
        "preflight_id": preflight_id,
        "verification_id": d140.get("verification_id") or summary.get("verification_id"),
        "candidate_id": d140.get("candidate_id") or summary.get("candidate_id"),
        "created_at": now(),
        "blocker_mode": "APPLY_BLOCKERS_ONLY_NO_APPLY",
        "must_remain_blocked_until_d142_or_later": {
            "real_apply_by_ai": True,
            "auto_apply": True,
            "route_insert_by_ai": True,
            "protected_core_mutation_by_ai": True,
            "canonical_memory_overwrite_by_ai": True,
            "shell_exec_from_ai": True,
            "external_network_call_by_ai": True,
            "secret_read_by_ai": True,
            "git_commit_by_ai": True,
            "git_push_by_ai": True,
        },
        "must_remain_false_now": {
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "candidate_executed_now": False,
        },
        "human_review_required": True,
    }


def build_d142_scope(preflight_id, d140):
    summary = d140.get("summary", {})
    return {
        "state": "D141_D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE",
        "ok": True,
        "preflight_id": preflight_id,
        "verification_id": d140.get("verification_id") or summary.get("verification_id"),
        "run_id": d140.get("run_id") or summary.get("run_id"),
        "candidate_id": d140.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d140.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D142_GATE,
        "d142_allowed_to_create": [
            "sandbox_candidate_human_apply_intent_scope",
            "sandbox_candidate_human_apply_intent_record",
            "sandbox_candidate_apply_authority_guard",
            "d143_sandbox_candidate_guarded_apply_scope",
        ],
        "d142_must_not_execute": [
            "real_apply_by_ai", "auto_apply", "route_insert_by_ai", "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai", "shell_exec_from_ai", "external_network_call_by_ai",
            "secret_read_by_ai", "git_commit_by_ai", "git_push_by_ai", "rollback_execute_by_ai", "restore_execute_by_ai",
        ],
        "sandbox_candidate_human_apply_intent_scope_only": True,
        "human_review_required": True,
        "candidate_executed_in_sandbox_after_d139": True,
        "candidate_executed_after_d141_by_ai": False,
        "real_apply_allowed_after_d141_by_ai": False,
        "route_insert_allowed_after_d141_by_ai": False,
        "protected_core_mutation_allowed_after_d141_by_ai": False,
        "network_allowed_after_d141_by_ai": False,
        "secret_read_allowed_after_d141_by_ai": False,
        "shell_allowed_after_d141_by_ai": False,
        "git_action_allowed_after_d141_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_ONLY",
    }


def create_sandbox_candidate_apply_preflight_scope(root="."):
    root = Path(root).resolve()

    d140 = read_json(root / D140_REPORT, {}) or {}
    verify_report = read_json(root / D140_VERIFY_REPORT, {}) or {}
    integrity_receipt = read_json(root / D140_INTEGRITY_RECEIPT, {}) or {}
    d141_scope = read_json(root / D140_D141_SCOPE, {}) or {}

    errors = validate_d140(d140, verify_report, integrity_receipt, d141_scope)

    preflight_id = "d141-" + digest({
        "verification_id": d140.get("verification_id") or d140.get("summary", {}).get("verification_id"),
        "run_id": d140.get("run_id") or d140.get("summary", {}).get("run_id"),
        "candidate_id": d140.get("candidate_id") or d140.get("summary", {}).get("candidate_id"),
        "proposal_id": d140.get("proposal_id") or d140.get("summary", {}).get("proposal_id"),
    })

    apply_preflight_report = build_apply_preflight_report(preflight_id, d140)
    apply_blockers = build_apply_blockers(preflight_id, d140)
    d142_scope = build_d142_scope(preflight_id, d140)

    for key in [
        "candidate_executed_now", "candidate_executed_by_ai", "actual_apply_executed", "real_apply_executed",
        "route_inserted", "protected_core_mutated", "canonical_memory_mutated", "network_accessed",
        "secret_read", "shell_executed_by_ai", "git_action_by_ai",
    ]:
        if apply_preflight_report.get(key) is not False:
            errors.append(f"apply_preflight_report {key} must be false")

    for key, value in apply_blockers.get("must_remain_false_now", {}).items():
        if value is not False:
            errors.append(f"apply_blockers must_remain_false_now.{key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_BLOCKED"
    result = "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_CREATED" if ok else "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_BLOCKED"

    if ok:
        write_json(root / APPLY_PREFLIGHT_REPORT_OUT, apply_preflight_report)
        write_json(root / APPLY_BLOCKERS_OUT, apply_blockers)
        write_json(root / D142_SCOPE_OUT, d142_scope)

    summary = d140.get("summary", {})
    report = {
        "state": "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "preflight_id": preflight_id,
        "verification_id": d140.get("verification_id") or summary.get("verification_id"),
        "run_id": d140.get("run_id") or summary.get("run_id"),
        "candidate_id": d140.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d140.get("proposal_id") or summary.get("proposal_id"),
        "source_d140_report": D140_REPORT,
        "sandbox_candidate_apply_preflight_report": apply_preflight_report if ok else {},
        "sandbox_candidate_apply_blockers": apply_blockers if ok else {},
        "d142_scope": d142_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
            "sandbox_candidate_apply_preflight_scope_only": True,
            "apply_preflight_report_only": True,
            "apply_blockers_only": True,
            "candidate_executed_now": False,
            "approval_for_d142_human_apply_intent_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "approval_for_route_insert_by_ai": False,
            "approval_for_protected_core_mutation_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "preflight_id": preflight_id,
            "verification_id": d140.get("verification_id") or summary.get("verification_id"),
            "run_id": d140.get("run_id") or summary.get("run_id"),
            "candidate_id": d140.get("candidate_id") or summary.get("candidate_id"),
            "proposal_id": d140.get("proposal_id") or summary.get("proposal_id"),
            "apply_preflight_status": "APPLY_PREFLIGHT_CREATED_NO_APPLY" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED" if ok else "BLOCKED",
            "execution_result_status": "PRESENT_AND_VALIDATED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D142_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_apply_preflight_scope_created": ok,
            "sandbox_candidate_apply_preflight_report_created": ok,
            "sandbox_candidate_apply_blockers_created": ok,
            "d142_scope_created": ok,
            "candidate_executed_in_sandbox": ok,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D142 may create sandbox candidate human apply intent scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_apply_preflight_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_apply_preflight_scope import create_sandbox_candidate_apply_preflight_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD141SandboxCandidateApplyPreflightScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        verification_id = "d140-test"
        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        false_guard = {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False, "secret_read": False,
            "shell_from_ai_executed": False, "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False, "route_inserted": False,
            "git_commit_by_ai": False, "git_push_by_ai": False, "rollback_executed": False, "restore_executed": False,
        }

        d140 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_READY",
            "verification_id": verification_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_post_execution_verification_scope_only": True,
                "post_execution_verification_report_only": True,
                "execution_integrity_receipt_only": True,
                "candidate_executed_now": False,
                "approval_for_d141_apply_preflight_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "post_execution_validation_status": "SANDBOX_EXECUTION_VERIFIED_NO_APPLY",
                "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
                "execution_result_status": "PRESENT_AND_VALIDATED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_ONLY",
                "next_step": "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE",
            },
        }

        verify_report = {
            "ok": True,
            "verification_id": verification_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "verification_mode": "POST_EXECUTION_VERIFICATION_ONLY_NO_APPLY",
            "sandbox_result_present": True,
            "sandbox_result_ok": True,
            "execution_status_verified": True,
            "candidate_status_verified": True,
            "post_execution_validation_status": "SANDBOX_EXECUTION_VERIFIED_NO_APPLY",
            "result_integrity_status": "PASS",
            "candidate_executed_in_sandbox": True,
            "candidate_executed_by_ai": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "human_review_required": True,
        }

        integrity_receipt = {
            "ok": True,
            "verification_id": verification_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "receipt_mode": "EXECUTION_INTEGRITY_RECEIPT_ONLY_NO_APPLY",
            "sandbox_execution_completed": True,
            "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "candidate_executed_by_ai": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "shell_executed_by_ai": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "human_review_required": True,
        }

        d141_scope = {
            "ok": True,
            "verification_id": verification_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "allowed_next_gate": "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE",
            "sandbox_candidate_apply_preflight_scope_only": True,
            "human_review_required": True,
            "candidate_executed_in_sandbox_after_d139": True,
            "candidate_executed_after_d140_by_ai": False,
            "real_apply_allowed_after_d140_by_ai": False,
            "route_insert_allowed_after_d140_by_ai": False,
            "protected_core_mutation_allowed_after_d140_by_ai": False,
            "network_allowed_after_d140_by_ai": False,
            "secret_read_allowed_after_d140_by_ai": False,
            "shell_allowed_after_d140_by_ai": False,
            "git_action_allowed_after_d140_by_ai": False,
        }

        write(root / "reports/d140_sandbox_candidate_post_execution_verification_scope.json", d140)
        write(root / "reports/d140_sandbox_candidate_post_execution_verification_report.json", verify_report)
        write(root / "reports/d140_sandbox_candidate_execution_integrity_receipt.json", integrity_receipt)
        write(root / "reports/d140_d141_sandbox_candidate_apply_preflight_scope.json", d141_scope)
        return td, root

    def test_creates_apply_preflight_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_apply_preflight_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_READY")
            self.assertEqual(r["summary"]["apply_preflight_status"], "APPLY_PREFLIGHT_CREATED_NO_APPLY")
            self.assertEqual(r["summary"]["approval_scope"], "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertEqual(r["d142_scope"]["allowed_next_gate"], "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE")
            self.assertTrue((root / "reports/d141_sandbox_candidate_apply_preflight_scope.json").exists())
            self.assertTrue((root / "reports/d141_sandbox_candidate_apply_preflight_report.json").exists())
            self.assertTrue((root / "reports/d141_sandbox_candidate_apply_blockers.json").exists())
            self.assertTrue((root / "reports/d141_d142_sandbox_candidate_human_apply_intent_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d140(self):
        td, root = self.root()
        try:
            (root / "reports/d140_sandbox_candidate_post_execution_verification_scope.json").unlink()
            r = create_sandbox_candidate_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_verification_report_says_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d140_sandbox_candidate_post_execution_verification_report.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d141_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d140_d141_sandbox_candidate_apply_preflight_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d140_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d140_summary_not_validated(self):
        td, root = self.root()
        try:
            p = root / "reports/d140_sandbox_candidate_post_execution_verification_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["execution_result_status"] = "BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
'''


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

print("D141 SANDBOX CANDIDATE APPLY PREFLIGHT SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_apply_preflight_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d141_sandbox_candidate_apply_preflight_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_apply_preflight_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d141_sandbox_candidate_apply_preflight_scope", "-v"], check=True)

print("\n== run D141 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_apply_preflight_scope import create_sandbox_candidate_apply_preflight_scope\n"
    "r=create_sandbox_candidate_apply_preflight_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d141_sandbox_candidate_apply_preflight_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_apply_preflight_scope.py",
    "tests/test_d141_sandbox_candidate_apply_preflight_scope.py",
    "reports/d141_sandbox_candidate_apply_preflight_scope.json",
    "reports/d141_sandbox_candidate_apply_preflight_report.json",
    "reports/d141_sandbox_candidate_apply_blockers.json",
    "reports/d141_d142_sandbox_candidate_human_apply_intent_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D141 sandbox candidate apply preflight scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D141 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD141 SANDBOX CANDIDATE APPLY PREFLIGHT SCOPE BOOT DONE")
