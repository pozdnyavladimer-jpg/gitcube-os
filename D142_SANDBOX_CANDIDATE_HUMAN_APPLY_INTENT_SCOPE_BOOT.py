#!/usr/bin/env python3
# D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_BOOT.py
#
# D142 consumes D141 apply-preflight artifacts and creates:
# - runtime_experimental/sandbox_candidate_human_apply_intent_scope.py
# - tests/test_d142_sandbox_candidate_human_apply_intent_scope.py
# - reports/d142_sandbox_candidate_human_apply_intent_scope.json
# - reports/d142_sandbox_candidate_human_apply_intent_record.json
# - reports/d142_sandbox_candidate_apply_authority_guard.json
# - reports/d142_d143_sandbox_candidate_guarded_apply_scope.json
#
# HUMAN APPLY INTENT SCOPE ONLY:
# no apply, no route insert, no protected core mutation, no shell, no network,
# no secret read, no candidate execution, no AI git action.
#
# D142 opens D143 Sandbox Candidate Guarded Apply Scope.

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

D141_REPORT = "reports/d141_sandbox_candidate_apply_preflight_scope.json"
D141_PREFLIGHT_REPORT = "reports/d141_sandbox_candidate_apply_preflight_report.json"
D141_BLOCKERS = "reports/d141_sandbox_candidate_apply_blockers.json"
D141_D142_SCOPE = "reports/d141_d142_sandbox_candidate_human_apply_intent_scope.json"

OUT = "reports/d142_sandbox_candidate_human_apply_intent_scope.json"
HUMAN_APPLY_INTENT_RECORD_OUT = "reports/d142_sandbox_candidate_human_apply_intent_record.json"
APPLY_AUTHORITY_GUARD_OUT = "reports/d142_sandbox_candidate_apply_authority_guard.json"
D143_SCOPE_OUT = "reports/d142_d143_sandbox_candidate_guarded_apply_scope.json"

REQ_D141_DECISION = "SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_READY"
REQ_D142_GATE = "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE"
REQ_D143_GATE = "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE"
REQ_D141_APPROVAL_SCOPE = "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_ONLY"
REQ_OPERATOR_PHRASE = "APPROVE_D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_ONLY"

FALSE_GUARD_KEYS = [
    "external_ai_called", "network_accessed", "api_key_read", "secret_read",
    "shell_from_ai_executed", "runtime_code_mutated", "protected_core_mutated",
    "canonical_memory_mutated", "actual_apply_executed", "route_inserted",
    "git_commit_by_ai", "git_push_by_ai", "rollback_executed", "restore_executed",
]

UNSAFE_BOOLEAN_KEYS = [
    "actual_apply_executed", "real_apply_executed", "route_inserted",
    "protected_core_mutated", "canonical_memory_mutated", "external_ai_called",
    "network_accessed", "api_key_read", "secret_read", "shell_from_ai_executed",
    "shell_executed_by_ai", "git_commit_by_ai", "git_push_by_ai", "git_action_by_ai",
    "rollback_executed", "restore_executed", "candidate_executed_now", "candidate_executed_by_ai",
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

BLOCKED_NON_APPLY_ACTIONS = [
    "auto_apply_by_ai", "route_insert_by_ai", "protected_core_mutation_by_ai",
    "canonical_memory_overwrite_by_ai", "shell_exec_from_ai", "external_network_call_by_ai",
    "secret_read_by_ai", "git_commit_by_ai", "git_push_by_ai", "rollback_execute_by_ai",
    "restore_execute_by_ai", "candidate_reexecution_by_ai",
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


def validate_d141(d141, preflight_report, blockers, d142_scope):
    errors = []
    if not d141:
        return ["missing D141 sandbox candidate apply preflight scope report"]

    if d141.get("ok") is not True:
        errors.append("D141 ok must be true")
    if d141.get("decision") != REQ_D141_DECISION:
        errors.append("D141 decision must be SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_READY")

    summary = d141.get("summary", {})
    expected = {
        "apply_preflight_status": "APPLY_PREFLIGHT_CREATED_NO_APPLY",
        "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
        "execution_result_status": "PRESENT_AND_VALIDATED",
        "approval_scope": REQ_D141_APPROVAL_SCOPE,
        "next_step": REQ_D142_GATE,
    }
    expected.update(UNSAFE_STATUS_EXPECTED)
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D141 summary.{key} must be {value}")

    guard = d141.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D141 guardrails.{key} must be false")
    for key in [
        "sandbox_candidate_apply_preflight_scope_only", "apply_preflight_report_only",
        "apply_blockers_only", "approval_for_d142_human_apply_intent_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D141 guardrails.{key} must be true")
    for key in [
        "candidate_executed_now", "approval_for_real_apply_by_ai", "approval_for_route_insert_by_ai",
        "approval_for_protected_core_mutation_by_ai", "candidate_execution_allowed_by_ai", "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D141 guardrails.{key} must be false")

    if not preflight_report:
        errors.append("missing D141 sandbox candidate apply preflight report")
    else:
        if preflight_report.get("ok") is not True:
            errors.append("D141 apply preflight report ok must be true")
        if preflight_report.get("preflight_mode") != "APPLY_PREFLIGHT_ONLY_NO_APPLY":
            errors.append("D141 apply preflight report mode must be APPLY_PREFLIGHT_ONLY_NO_APPLY")
        for key in ["candidate_executed_in_sandbox", "human_review_required"]:
            if preflight_report.get(key) is not True:
                errors.append(f"D141 apply preflight report {key} must be true")
        if preflight_report.get("post_execution_validation_status") != "SANDBOX_EXECUTION_VERIFIED_NO_APPLY":
            errors.append("D141 apply preflight report post_execution_validation_status must be SANDBOX_EXECUTION_VERIFIED_NO_APPLY")
        if preflight_report.get("apply_preflight_status") != "APPLY_PREFLIGHT_CREATED_NO_APPLY":
            errors.append("D141 apply preflight report apply_preflight_status must be APPLY_PREFLIGHT_CREATED_NO_APPLY")
        if preflight_report.get("apply_readiness_status") != "READY_FOR_HUMAN_APPLY_INTENT_SCOPE_ONLY":
            errors.append("D141 apply preflight report apply_readiness_status must be READY_FOR_HUMAN_APPLY_INTENT_SCOPE_ONLY")
        check_false_map("D141 apply preflight report", preflight_report, errors)

    if not blockers:
        errors.append("missing D141 sandbox candidate apply blockers")
    else:
        if blockers.get("ok") is not True:
            errors.append("D141 apply blockers ok must be true")
        if blockers.get("blocker_mode") != "APPLY_BLOCKERS_ONLY_NO_APPLY":
            errors.append("D141 apply blockers mode must be APPLY_BLOCKERS_ONLY_NO_APPLY")
        if blockers.get("human_review_required") is not True:
            errors.append("D141 apply blockers human_review_required must be true")
        for key, value in blockers.get("must_remain_false_now", {}).items():
            if value is not False:
                errors.append(f"D141 apply blockers must_remain_false_now.{key} must be false")
        for key, value in blockers.get("must_remain_blocked_until_d142_or_later", {}).items():
            if value is not True:
                errors.append(f"D141 apply blockers must_remain_blocked_until_d142_or_later.{key} must be true")

    if not d142_scope:
        errors.append("missing D141 D142 sandbox candidate human apply intent scope")
    else:
        if d142_scope.get("ok") is not True:
            errors.append("D141 D142 scope ok must be true")
        if d142_scope.get("allowed_next_gate") != REQ_D142_GATE:
            errors.append("D141 D142 scope allowed_next_gate must be D142")
        if d142_scope.get("sandbox_candidate_human_apply_intent_scope_only") is not True:
            errors.append("D141 D142 scope must be human apply intent only")
        if d142_scope.get("human_review_required") is not True:
            errors.append("D141 D142 scope must require human review")
        if d142_scope.get("candidate_executed_in_sandbox_after_d139") is not True:
            errors.append("D141 D142 scope must confirm candidate was executed in sandbox after D139")
        for key in [
            "candidate_executed_after_d141_by_ai", "real_apply_allowed_after_d141_by_ai",
            "route_insert_allowed_after_d141_by_ai", "protected_core_mutation_allowed_after_d141_by_ai",
            "network_allowed_after_d141_by_ai", "secret_read_allowed_after_d141_by_ai",
            "shell_allowed_after_d141_by_ai", "git_action_allowed_after_d141_by_ai",
        ]:
            if d142_scope.get(key) is not False:
                errors.append(f"D141 D142 scope {key} must be false")
    return errors


def build_human_apply_intent_record(intent_id, d141):
    summary = d141.get("summary", {})
    return {
        "state": "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_RECORD",
        "ok": True,
        "intent_id": intent_id,
        "preflight_id": d141.get("preflight_id") or summary.get("preflight_id"),
        "verification_id": d141.get("verification_id") or summary.get("verification_id"),
        "run_id": d141.get("run_id") or summary.get("run_id"),
        "candidate_id": d141.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d141.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "record_mode": "HUMAN_APPLY_INTENT_RECORD_ONLY_NO_APPLY",
        "operator_decision": "PENDING_HUMAN_APPLY_INTENT_FOR_D143",
        "required_phrase_for_d143": REQ_OPERATOR_PHRASE,
        "approved_for_d143_guarded_apply_scope_only": True,
        "approved_for_real_apply_now": False,
        "approved_for_real_apply_by_ai": False,
        "approved_for_auto_apply": False,
        "approved_for_route_insert": False,
        "approved_for_protected_core_mutation": False,
        "approved_for_git_action_by_ai": False,
        "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
        "candidate_execution_performed_now": False,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "real_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "human_review_required": True,
    }


def build_apply_authority_guard(intent_id, d141):
    summary = d141.get("summary", {})
    return {
        "state": "D142_SANDBOX_CANDIDATE_APPLY_AUTHORITY_GUARD",
        "ok": True,
        "intent_id": intent_id,
        "preflight_id": d141.get("preflight_id") or summary.get("preflight_id"),
        "candidate_id": d141.get("candidate_id") or summary.get("candidate_id"),
        "created_at": now(),
        "authority_mode": "SANDBOX_GUARDED_APPLY_AUTHORITY_GUARD_ONLY",
        "guard_mode": "SANDBOX_GUARDED_APPLY_AUTHORITY_GUARD_ONLY",
        "allowed_after_d142": ["create_d143_guarded_apply_scope", "prepare_guarded_apply_plan_for_operator_review"],
        "still_blocked": BLOCKED_NON_APPLY_ACTIONS,
        "guarded_apply_allowed_now": False,
        "guarded_apply_allowed_next_gate_only": True,
        "real_apply_allowed_now": False,
        "real_apply_allowed_by_ai": False,
        "auto_apply_allowed": False,
        "candidate_execution_performed_now": False,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "real_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "human_review_required": True,
    }


def build_d143_scope(intent_id, d141):
    summary = d141.get("summary", {})
    return {
        "state": "D142_D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE",
        "ok": True,
        "intent_id": intent_id,
        "preflight_id": d141.get("preflight_id") or summary.get("preflight_id"),
        "verification_id": d141.get("verification_id") or summary.get("verification_id"),
        "run_id": d141.get("run_id") or summary.get("run_id"),
        "candidate_id": d141.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d141.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D143_GATE,
        "d143_allowed_to_create": [
            "sandbox_candidate_guarded_apply_scope", "sandbox_candidate_guarded_apply_plan",
            "sandbox_candidate_guarded_apply_receipt", "d144_sandbox_candidate_post_apply_verification_scope",
        ],
        "d143_allowed_to_apply": ["guarded_candidate_changes_declared_in_sandbox_payload_only_if_operator_runs_d143_boot"],
        "d143_must_not_execute": BLOCKED_NON_APPLY_ACTIONS,
        "sandbox_candidate_guarded_apply_scope_only": True,
        "human_review_required": True,
        "candidate_executed_in_sandbox_after_d139": True,
        "candidate_executed_after_d142_by_ai": False,
        "guarded_apply_allowed_after_d142_operator_only": True,
        "real_apply_allowed_after_d142_by_ai": False,
        "auto_apply_allowed_after_d142_by_ai": False,
        "route_insert_allowed_after_d142_by_ai": False,
        "protected_core_mutation_allowed_after_d142_by_ai": False,
        "network_allowed_after_d142_by_ai": False,
        "secret_read_allowed_after_d142_by_ai": False,
        "shell_allowed_after_d142_by_ai": False,
        "git_action_allowed_after_d142_by_ai": False,
        "required_phrase_for_later_gate": REQ_OPERATOR_PHRASE,
    }


def create_sandbox_candidate_human_apply_intent_scope(root="."):
    root = Path(root).resolve()
    d141 = read_json(root / D141_REPORT, {}) or {}
    preflight_report = read_json(root / D141_PREFLIGHT_REPORT, {}) or {}
    blockers = read_json(root / D141_BLOCKERS, {}) or {}
    d142_scope = read_json(root / D141_D142_SCOPE, {}) or {}

    errors = validate_d141(d141, preflight_report, blockers, d142_scope)
    summary = d141.get("summary", {})
    intent_id = "d142-" + digest({
        "preflight_id": d141.get("preflight_id") or summary.get("preflight_id"),
        "verification_id": d141.get("verification_id") or summary.get("verification_id"),
        "candidate_id": d141.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d141.get("proposal_id") or summary.get("proposal_id"),
    })

    human_apply_intent_record = build_human_apply_intent_record(intent_id, d141)
    apply_authority_guard = build_apply_authority_guard(intent_id, d141)
    d143_scope = build_d143_scope(intent_id, d141)

    for item_name, item in [("human_apply_intent_record", human_apply_intent_record), ("apply_authority_guard", apply_authority_guard)]:
        for key in UNSAFE_BOOLEAN_KEYS:
            if item.get(key) is True:
                errors.append(f"{item_name} {key} must not be true")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_BLOCKED"
    result = "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_CREATED" if ok else "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_BLOCKED"

    if ok:
        write_json(root / HUMAN_APPLY_INTENT_RECORD_OUT, human_apply_intent_record)
        write_json(root / APPLY_AUTHORITY_GUARD_OUT, apply_authority_guard)
        write_json(root / D143_SCOPE_OUT, d143_scope)

    report = {
        "state": "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "intent_id": intent_id,
        "preflight_id": d141.get("preflight_id") or summary.get("preflight_id"),
        "verification_id": d141.get("verification_id") or summary.get("verification_id"),
        "run_id": d141.get("run_id") or summary.get("run_id"),
        "candidate_id": d141.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d141.get("proposal_id") or summary.get("proposal_id"),
        "source_d141_report": D141_REPORT,
        "sandbox_candidate_human_apply_intent_record": human_apply_intent_record if ok else {},
        "sandbox_candidate_apply_authority_guard": apply_authority_guard if ok else {},
        "d143_scope": d143_scope if ok else {},
        "guardrails": {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False, "secret_read": False,
            "shell_from_ai_executed": False, "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False, "route_inserted": False,
            "git_commit_by_ai": False, "git_push_by_ai": False, "rollback_executed": False, "restore_executed": False,
            "sandbox_candidate_human_apply_intent_scope_only": True,
            "human_apply_intent_record_only": True,
            "apply_authority_guard_only": True,
            "candidate_executed_now": False,
            "approval_for_d143_guarded_apply_scope_only": ok,
            "approval_for_real_apply_now": False,
            "approval_for_real_apply_by_ai": False,
            "approval_for_route_insert_by_ai": False,
            "approval_for_protected_core_mutation_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "intent_id": intent_id,
            "preflight_id": d141.get("preflight_id") or summary.get("preflight_id"),
            "verification_id": d141.get("verification_id") or summary.get("verification_id"),
            "run_id": d141.get("run_id") or summary.get("run_id"),
            "candidate_id": d141.get("candidate_id") or summary.get("candidate_id"),
            "proposal_id": d141.get("proposal_id") or summary.get("proposal_id"),
            "human_apply_intent_status": "HUMAN_APPLY_INTENT_RECORD_CREATED_NO_APPLY" if ok else "BLOCKED",
            "apply_authority_status": "APPLY_AUTHORITY_GUARD_CREATED_NO_APPLY" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED" if ok else "BLOCKED",
            "execution_result_status": "PRESENT_AND_VALIDATED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D143_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_human_apply_intent_scope_created": ok,
            "sandbox_candidate_human_apply_intent_record_created": ok,
            "sandbox_candidate_apply_authority_guard_created": ok,
            "d143_scope_created": ok,
            "candidate_executed_in_sandbox": ok,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_now": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D143 may create sandbox candidate guarded apply scope only.",
        },
    }
    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_human_apply_intent_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_human_apply_intent_scope import create_sandbox_candidate_human_apply_intent_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD142SandboxCandidateHumanApplyIntentScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        preflight_id = "d141-test"
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
        d141 = {
            "ok": True, "decision": "SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_READY",
            "preflight_id": preflight_id, "verification_id": verification_id, "run_id": run_id,
            "candidate_id": candidate_id, "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_apply_preflight_scope_only": True, "apply_preflight_report_only": True,
                "apply_blockers_only": True, "candidate_executed_now": False,
                "approval_for_d142_human_apply_intent_scope_only": True, "approval_for_real_apply_by_ai": False,
                "approval_for_route_insert_by_ai": False, "approval_for_protected_core_mutation_by_ai": False,
                "candidate_execution_allowed_by_ai": False, "commands_executed_by_ai": False,
            }),
            "summary": {
                "apply_preflight_status": "APPLY_PREFLIGHT_CREATED_NO_APPLY",
                "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
                "execution_result_status": "PRESENT_AND_VALIDATED",
                "real_provider_status": "NOT_CALLED", "network_status": "NOT_ACCESSED", "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED", "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED", "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_ONLY",
                "next_step": "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE",
            },
        }
        preflight_report = {
            "ok": True, "preflight_id": preflight_id, "verification_id": verification_id, "run_id": run_id,
            "candidate_id": candidate_id, "proposal_id": proposal_id,
            "preflight_mode": "APPLY_PREFLIGHT_ONLY_NO_APPLY",
            "post_execution_validation_required": True,
            "post_execution_validation_status": "SANDBOX_EXECUTION_VERIFIED_NO_APPLY",
            "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
            "apply_preflight_status": "APPLY_PREFLIGHT_CREATED_NO_APPLY",
            "apply_readiness_status": "READY_FOR_HUMAN_APPLY_INTENT_SCOPE_ONLY",
            "candidate_executed_in_sandbox": True,
            "candidate_executed_now": False, "candidate_executed_by_ai": False,
            "actual_apply_executed": False, "real_apply_executed": False, "route_inserted": False,
            "protected_core_mutated": False, "canonical_memory_mutated": False, "network_accessed": False,
            "secret_read": False, "shell_executed_by_ai": False, "git_action_by_ai": False,
            "human_review_required": True,
        }
        blockers = {
            "ok": True, "preflight_id": preflight_id, "verification_id": verification_id, "candidate_id": candidate_id,
            "blocker_mode": "APPLY_BLOCKERS_ONLY_NO_APPLY",
            "must_remain_blocked_until_d142_or_later": {
                "real_apply_by_ai": True, "auto_apply": True, "route_insert_by_ai": True,
                "protected_core_mutation_by_ai": True, "canonical_memory_overwrite_by_ai": True,
                "shell_exec_from_ai": True, "external_network_call_by_ai": True, "secret_read_by_ai": True,
                "git_commit_by_ai": True, "git_push_by_ai": True,
            },
            "must_remain_false_now": {
                "actual_apply_executed": False, "real_apply_executed": False, "route_inserted": False,
                "protected_core_mutated": False, "canonical_memory_mutated": False, "network_accessed": False,
                "secret_read": False, "shell_executed_by_ai": False, "git_action_by_ai": False,
                "candidate_executed_now": False,
            },
            "human_review_required": True,
        }
        d142_scope = {
            "ok": True, "preflight_id": preflight_id, "verification_id": verification_id, "run_id": run_id,
            "candidate_id": candidate_id, "proposal_id": proposal_id,
            "allowed_next_gate": "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE",
            "sandbox_candidate_human_apply_intent_scope_only": True, "human_review_required": True,
            "candidate_executed_in_sandbox_after_d139": True,
            "candidate_executed_after_d141_by_ai": False, "real_apply_allowed_after_d141_by_ai": False,
            "route_insert_allowed_after_d141_by_ai": False, "protected_core_mutation_allowed_after_d141_by_ai": False,
            "network_allowed_after_d141_by_ai": False, "secret_read_allowed_after_d141_by_ai": False,
            "shell_allowed_after_d141_by_ai": False, "git_action_allowed_after_d141_by_ai": False,
        }
        write(root / "reports/d141_sandbox_candidate_apply_preflight_scope.json", d141)
        write(root / "reports/d141_sandbox_candidate_apply_preflight_report.json", preflight_report)
        write(root / "reports/d141_sandbox_candidate_apply_blockers.json", blockers)
        write(root / "reports/d141_d142_sandbox_candidate_human_apply_intent_scope.json", d142_scope)
        return td, root

    def test_creates_human_apply_intent_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_human_apply_intent_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_READY")
            self.assertEqual(r["summary"]["human_apply_intent_status"], "HUMAN_APPLY_INTENT_RECORD_CREATED_NO_APPLY")
            self.assertEqual(r["summary"]["approval_scope"], "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply_now"])
            self.assertEqual(r["d143_scope"]["allowed_next_gate"], "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE")
            self.assertTrue((root / "reports/d142_sandbox_candidate_human_apply_intent_scope.json").exists())
            self.assertTrue((root / "reports/d142_sandbox_candidate_human_apply_intent_record.json").exists())
            self.assertTrue((root / "reports/d142_sandbox_candidate_apply_authority_guard.json").exists())
            self.assertTrue((root / "reports/d142_d143_sandbox_candidate_guarded_apply_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d141(self):
        td, root = self.root()
        try:
            (root / "reports/d141_sandbox_candidate_apply_preflight_scope.json").unlink()
            r = create_sandbox_candidate_human_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_preflight_report_says_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d141_sandbox_candidate_apply_preflight_report.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_apply_blocker_false(self):
        td, root = self.root()
        try:
            p = root / "reports/d141_sandbox_candidate_apply_blockers.json"
            data = json.loads(p.read_text())
            data["must_remain_blocked_until_d142_or_later"]["route_insert_by_ai"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d142_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d141_d142_sandbox_candidate_human_apply_intent_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d141_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_apply_intent_scope(root)
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

print("D142 SANDBOX CANDIDATE HUMAN APPLY INTENT SCOPE BOOT: repo =", ROOT)
Path("runtime_experimental/sandbox_candidate_human_apply_intent_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d142_sandbox_candidate_human_apply_intent_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_human_apply_intent_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d142_sandbox_candidate_human_apply_intent_scope", "-v"], check=True)

print("\n== run D142 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_human_apply_intent_scope import create_sandbox_candidate_human_apply_intent_scope\n"
    "r=create_sandbox_candidate_human_apply_intent_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d142_sandbox_candidate_human_apply_intent_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_human_apply_intent_scope.py",
    "tests/test_d142_sandbox_candidate_human_apply_intent_scope.py",
    "reports/d142_sandbox_candidate_human_apply_intent_scope.json",
    "reports/d142_sandbox_candidate_human_apply_intent_record.json",
    "reports/d142_sandbox_candidate_apply_authority_guard.json",
    "reports/d142_d143_sandbox_candidate_guarded_apply_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D142 sandbox candidate human apply intent scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D142 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD142 SANDBOX CANDIDATE HUMAN APPLY INTENT SCOPE BOOT DONE")
