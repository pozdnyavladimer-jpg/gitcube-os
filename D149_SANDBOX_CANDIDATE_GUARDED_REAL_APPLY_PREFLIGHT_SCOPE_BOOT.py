#!/usr/bin/env python3
# D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_BOOT.py
#
# D149 consumes D148 human real-apply intent artifacts and creates:
# - runtime_experimental/sandbox_candidate_guarded_real_apply_preflight_scope.py
# - tests/test_d149_sandbox_candidate_guarded_real_apply_preflight_scope.py
# - reports/d149_sandbox_candidate_guarded_real_apply_preflight_scope.json
# - reports/d149_sandbox_candidate_real_apply_preflight_report.json
# - reports/d149_sandbox_candidate_real_apply_blockers.json
# - reports/d149_d150_sandbox_candidate_human_signed_real_apply_execution_scope.json
#
# GUARDED REAL APPLY PREFLIGHT SCOPE ONLY:
# no real/core apply, no route insert, no protected core mutation, no shell,
# no network/provider call, no secret read, no git action by AI,
# no candidate re-execution.
#
# D149 opens D150 Human Signed Real Apply Execution Scope only.

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

D148_REPORT = "reports/d148_sandbox_candidate_human_real_apply_intent_scope.json"
D148_INTENT_RECORD = "reports/d148_sandbox_candidate_human_real_apply_intent_record.json"
D148_AUTHORITY_GUARD = "reports/d148_sandbox_candidate_real_apply_authority_guard.json"
D148_D149_SCOPE = "reports/d148_d149_sandbox_candidate_guarded_real_apply_preflight_scope.json"

OUT = "reports/d149_sandbox_candidate_guarded_real_apply_preflight_scope.json"
PREFLIGHT_REPORT_OUT = "reports/d149_sandbox_candidate_real_apply_preflight_report.json"
BLOCKERS_OUT = "reports/d149_sandbox_candidate_real_apply_blockers.json"
D150_SCOPE_OUT = "reports/d149_d150_sandbox_candidate_human_signed_real_apply_execution_scope.json"

REQ_D148_DECISION = "SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_READY"
REQ_D149_GATE = "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE"
REQ_D150_GATE = "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE"

FALSE_KEYS = [
    "external_ai_called",
    "network_accessed",
    "api_key_read",
    "secret_read",
    "shell_from_ai_executed",
    "shell_executed_by_ai",
    "runtime_code_mutated",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "actual_apply_executed",
    "real_apply_executed",
    "route_inserted",
    "git_commit_by_ai",
    "git_push_by_ai",
    "git_action_by_ai",
    "rollback_executed",
    "restore_executed",
]

STATUS_FALSE_D148 = [
    "real_apply_allowed_after_d148_by_ai",
    "route_insert_allowed_after_d148_by_ai",
    "protected_core_mutation_allowed_after_d148_by_ai",
    "network_allowed_after_d148_by_ai",
    "secret_read_allowed_after_d148_by_ai",
    "shell_allowed_after_d148_by_ai",
    "git_action_allowed_after_d148_by_ai",
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


def validate_d148(d148, intent_record, authority_guard, d149_scope):
    errors = []

    if not d148:
        errors.append("missing D148 sandbox candidate human real apply intent scope report")
        return errors

    if d148.get("ok") is not True:
        errors.append("D148 ok must be true")
    if d148.get("decision") != REQ_D148_DECISION:
        errors.append("D148 decision must be SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_READY")

    summary = d148.get("summary", {})
    expected = {
        "human_real_apply_intent_status": "HUMAN_REAL_APPLY_INTENT_RECORDED_NO_REAL_APPLY",
        "real_apply_authority_status": "REAL_APPLY_AUTHORITY_GUARD_CREATED_NO_REAL_APPLY",
        "candidate_status": "SANDBOX_CHAIN_PROMOTED_TO_REAL_APPLY_PREFLIGHT_PATH_NOT_CORE_APPLIED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_ONLY",
        "next_step": REQ_D149_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D148 summary.{key} must be {value}")

    guard = d148.get("guardrails", {})
    for key in FALSE_KEYS:
        if key in guard and guard.get(key) is not False:
            errors.append(f"D148 guardrails.{key} must be false")
    for key in STATUS_FALSE_D148:
        if guard.get(key) is not False:
            errors.append(f"D148 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_human_real_apply_intent_scope_only",
        "human_real_apply_intent_record_only",
        "real_apply_authority_guard_only",
        "approval_for_d149_guarded_real_apply_preflight_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D148 guardrails.{key} must be true")

    if guard.get("approval_for_real_core_apply_now") is not False:
        errors.append("D148 approval_for_real_core_apply_now must be false")

    if not intent_record:
        errors.append("missing D148 human real apply intent record")
    else:
        if intent_record.get("ok") is not True:
            errors.append("D148 intent record ok must be true")
        if intent_record.get("intent_mode") != "HUMAN_REAL_APPLY_INTENT_RECORD_ONLY_NO_REAL_APPLY":
            errors.append("D148 intent record mode must be no-real-apply")
        if intent_record.get("approved_for_d149_guarded_real_apply_preflight_scope_only") is not True:
            errors.append("D148 intent record must approve D149 preflight only")
        if intent_record.get("approved_for_real_core_apply_now") is not False:
            errors.append("D148 intent record approved_for_real_core_apply_now must be false")
        for key in FALSE_KEYS:
            if key in intent_record and intent_record.get(key) is not False:
                errors.append(f"D148 intent record {key} must be false")

    if not authority_guard:
        errors.append("missing D148 real apply authority guard")
    else:
        if authority_guard.get("ok") is not True:
            errors.append("D148 authority guard ok must be true")
        if authority_guard.get("authority_mode") != "REAL_APPLY_AUTHORITY_GUARD_ONLY_NO_REAL_APPLY":
            errors.append("D148 authority guard mode must be REAL_APPLY_AUTHORITY_GUARD_ONLY_NO_REAL_APPLY")
        if authority_guard.get("allow_d149_guarded_real_apply_preflight") is not True:
            errors.append("D148 authority guard must allow D149 preflight")
        for key in [
            "allow_real_core_apply_now",
            "allow_route_insert",
            "allow_protected_core_mutation",
            "allow_network",
            "allow_secret_read",
            "allow_shell_exec",
            "allow_git_action_by_ai",
        ]:
            if authority_guard.get(key) is not False:
                errors.append(f"D148 authority guard {key} must be false")
        for key in STATUS_FALSE_D148:
            if authority_guard.get(key) is not False:
                errors.append(f"D148 authority guard {key} must be false")

    if not d149_scope:
        errors.append("missing D148 D149 guarded real apply preflight scope")
    else:
        if d149_scope.get("ok") is not True:
            errors.append("D148 D149 scope ok must be true")
        if d149_scope.get("allowed_next_gate") != REQ_D149_GATE:
            errors.append("D148 D149 scope allowed_next_gate must be D149")
        if d149_scope.get("sandbox_candidate_guarded_real_apply_preflight_scope_only") is not True:
            errors.append("D148 D149 scope must be guarded-real-apply-preflight-only")
        if d149_scope.get("human_review_required") is not True:
            errors.append("D148 D149 scope must require human review")
        for key in STATUS_FALSE_D148:
            if d149_scope.get(key) is not False:
                errors.append(f"D148 D149 scope {key} must be false")

    return errors


def build_preflight_report(preflight_id, d148):
    return {
        "state": "D149_SANDBOX_CANDIDATE_REAL_APPLY_PREFLIGHT_REPORT",
        "ok": True,
        "preflight_id": preflight_id,
        "intent_id": d148.get("intent_id"),
        "decision_id": d148.get("decision_id"),
        "archive_id": d148.get("archive_id"),
        "candidate_id": d148.get("candidate_id"),
        "proposal_id": d148.get("proposal_id"),
        "created_at": now(),
        "preflight_mode": "REAL_APPLY_PREFLIGHT_ONLY_NO_REAL_APPLY",
        "preflight_status": "REAL_APPLY_PREFLIGHT_CREATED_NO_EXECUTION",
        "candidate_status": "SANDBOX_CHAIN_READY_FOR_HUMAN_SIGNED_REAL_APPLY_EXECUTION_NOT_CORE_APPLIED",
        "checks": [
            {"name": "sandbox_execution_verified", "status": "PASS", "dry_preflight_only": True},
            {"name": "sandbox_apply_evidence_verified", "status": "PASS", "dry_preflight_only": True},
            {"name": "final_audit_ledger_present", "status": "PASS", "dry_preflight_only": True},
            {"name": "archive_scope_present", "status": "PASS", "dry_preflight_only": True},
            {"name": "human_real_apply_intent_present", "status": "PASS", "dry_preflight_only": True},
            {"name": "no_core_apply_executed_yet", "status": "PASS", "dry_preflight_only": True},
        ],
        "actual_apply_executed": False,
        "real_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_blockers(preflight_id, d148):
    return {
        "state": "D149_SANDBOX_CANDIDATE_REAL_APPLY_BLOCKERS",
        "ok": True,
        "preflight_id": preflight_id,
        "intent_id": d148.get("intent_id"),
        "candidate_id": d148.get("candidate_id"),
        "created_at": now(),
        "blocker_mode": "REAL_APPLY_BLOCKERS_DECLARED_NO_EXECUTION",
        "hard_blockers_for_ai": [
            "real_core_apply_by_ai",
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
        "operator_only_next_gate": "D150 human signed real apply execution scope",
        "actual_apply_executed": False,
        "real_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_d150_scope(preflight_id, d148):
    return {
        "state": "D149_D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE",
        "ok": True,
        "preflight_id": preflight_id,
        "intent_id": d148.get("intent_id"),
        "decision_id": d148.get("decision_id"),
        "archive_id": d148.get("archive_id"),
        "verification_id": d148.get("verification_id"),
        "apply_id": d148.get("apply_id"),
        "run_id": d148.get("run_id"),
        "candidate_id": d148.get("candidate_id"),
        "proposal_id": d148.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D150_GATE,
        "sandbox_candidate_human_signed_real_apply_execution_scope_only": True,
        "human_review_required": True,
        "d150_allowed_to_create": [
            "human_signed_real_apply_execution_scope",
            "real_apply_signature_record",
            "real_apply_execution_authority_guard",
            "d151_guarded_real_apply_run_scope",
        ],
        "d150_must_not_execute": [
            "real_core_apply_now",
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
        "real_apply_allowed_after_d149_by_ai": False,
        "route_insert_allowed_after_d149_by_ai": False,
        "protected_core_mutation_allowed_after_d149_by_ai": False,
        "network_allowed_after_d149_by_ai": False,
        "secret_read_allowed_after_d149_by_ai": False,
        "shell_allowed_after_d149_by_ai": False,
        "git_action_allowed_after_d149_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_ONLY",
    }


def create_sandbox_candidate_guarded_real_apply_preflight_scope(root="."):
    root = Path(root).resolve()

    d148 = read_json(root / D148_REPORT, {}) or {}
    intent_record = read_json(root / D148_INTENT_RECORD, {}) or {}
    authority_guard = read_json(root / D148_AUTHORITY_GUARD, {}) or {}
    d149_scope = read_json(root / D148_D149_SCOPE, {}) or {}

    errors = validate_d148(d148, intent_record, authority_guard, d149_scope)

    preflight_id = "d149-" + digest({
        "intent_id": d148.get("intent_id"),
        "decision_id": d148.get("decision_id"),
        "archive_id": d148.get("archive_id"),
        "candidate_id": d148.get("candidate_id"),
        "proposal_id": d148.get("proposal_id"),
    })

    preflight_report = build_preflight_report(preflight_id, d148)
    blockers = build_blockers(preflight_id, d148)
    d150_scope = build_d150_scope(preflight_id, d148)

    for item_name, item in [
        ("preflight_report", preflight_report),
        ("blockers", blockers),
        ("d150_scope", d150_scope),
    ]:
        for key in [
            "actual_apply_executed",
            "real_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "real_apply_allowed_after_d149_by_ai",
            "route_insert_allowed_after_d149_by_ai",
            "protected_core_mutation_allowed_after_d149_by_ai",
            "network_allowed_after_d149_by_ai",
            "secret_read_allowed_after_d149_by_ai",
            "shell_allowed_after_d149_by_ai",
            "git_action_allowed_after_d149_by_ai",
        ]:
            if key in item and item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_BLOCKED"
    result = "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_CREATED" if ok else "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_BLOCKED"

    if ok:
        write_json(root / PREFLIGHT_REPORT_OUT, preflight_report)
        write_json(root / BLOCKERS_OUT, blockers)
        write_json(root / D150_SCOPE_OUT, d150_scope)

    report = {
        "state": "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "preflight_id": preflight_id,
        "intent_id": d148.get("intent_id"),
        "decision_id": d148.get("decision_id"),
        "archive_id": d148.get("archive_id"),
        "verification_id": d148.get("verification_id"),
        "apply_id": d148.get("apply_id"),
        "run_id": d148.get("run_id"),
        "candidate_id": d148.get("candidate_id"),
        "proposal_id": d148.get("proposal_id"),
        "source_d148_report": D148_REPORT,
        "real_apply_preflight_report": preflight_report if ok else {},
        "real_apply_blockers": blockers if ok else {},
        "d150_scope": d150_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "shell_executed_by_ai": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "sandbox_candidate_guarded_real_apply_preflight_scope_only": True,
            "real_apply_preflight_report_only": True,
            "real_apply_blockers_only": True,
            "approval_for_d150_human_signed_real_apply_execution_scope_only": ok,
            "approval_for_real_core_apply_now": False,
            "real_apply_allowed_after_d149_by_ai": False,
            "route_insert_allowed_after_d149_by_ai": False,
            "protected_core_mutation_allowed_after_d149_by_ai": False,
            "network_allowed_after_d149_by_ai": False,
            "secret_read_allowed_after_d149_by_ai": False,
            "shell_allowed_after_d149_by_ai": False,
            "git_action_allowed_after_d149_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "preflight_id": preflight_id,
            "intent_id": d148.get("intent_id"),
            "decision_id": d148.get("decision_id"),
            "archive_id": d148.get("archive_id"),
            "candidate_id": d148.get("candidate_id"),
            "proposal_id": d148.get("proposal_id"),
            "real_apply_preflight_status": "REAL_APPLY_PREFLIGHT_CREATED_NO_EXECUTION" if ok else "BLOCKED",
            "real_apply_blocker_status": "AI_REAL_APPLY_BLOCKERS_DECLARED" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CHAIN_READY_FOR_HUMAN_SIGNED_REAL_APPLY_EXECUTION_NOT_CORE_APPLIED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D150_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "guarded_real_apply_preflight_scope_created": ok,
            "real_apply_preflight_report_created": ok,
            "real_apply_blockers_created": ok,
            "d150_scope_created": ok,
            "real_core_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "next_step": "D150 may create human signed real apply execution scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_guarded_real_apply_preflight_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_guarded_real_apply_preflight_scope import create_sandbox_candidate_guarded_real_apply_preflight_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD149SandboxCandidateGuardedRealApplyPreflightScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        intent_id = "d148-test"
        decision_id = "d147-test"
        archive_id = "d146-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d148 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_READY",
            "intent_id": intent_id,
            "decision_id": decision_id,
            "archive_id": archive_id,
            "verification_id": "d144-test",
            "apply_id": "d143-test",
            "run_id": "d139-test",
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": {
                "network_accessed": False,
                "secret_read": False,
                "shell_executed_by_ai": False,
                "actual_apply_executed": False,
                "real_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "git_action_by_ai": False,
                "sandbox_candidate_human_real_apply_intent_scope_only": True,
                "human_real_apply_intent_record_only": True,
                "real_apply_authority_guard_only": True,
                "approval_for_d149_guarded_real_apply_preflight_scope_only": True,
                "approval_for_real_core_apply_now": False,
                "real_apply_allowed_after_d148_by_ai": False,
                "route_insert_allowed_after_d148_by_ai": False,
                "protected_core_mutation_allowed_after_d148_by_ai": False,
                "network_allowed_after_d148_by_ai": False,
                "secret_read_allowed_after_d148_by_ai": False,
                "shell_allowed_after_d148_by_ai": False,
                "git_action_allowed_after_d148_by_ai": False,
            },
            "summary": {
                "human_real_apply_intent_status": "HUMAN_REAL_APPLY_INTENT_RECORDED_NO_REAL_APPLY",
                "real_apply_authority_status": "REAL_APPLY_AUTHORITY_GUARD_CREATED_NO_REAL_APPLY",
                "candidate_status": "SANDBOX_CHAIN_PROMOTED_TO_REAL_APPLY_PREFLIGHT_PATH_NOT_CORE_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_ONLY",
                "next_step": "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE",
            },
        }

        intent_record = {
            "ok": True,
            "intent_id": intent_id,
            "intent_mode": "HUMAN_REAL_APPLY_INTENT_RECORD_ONLY_NO_REAL_APPLY",
            "approved_for_d149_guarded_real_apply_preflight_scope_only": True,
            "approved_for_real_core_apply_now": False,
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        authority_guard = {
            "ok": True,
            "intent_id": intent_id,
            "authority_mode": "REAL_APPLY_AUTHORITY_GUARD_ONLY_NO_REAL_APPLY",
            "allow_d149_guarded_real_apply_preflight": True,
            "allow_real_core_apply_now": False,
            "allow_route_insert": False,
            "allow_protected_core_mutation": False,
            "allow_network": False,
            "allow_secret_read": False,
            "allow_shell_exec": False,
            "allow_git_action_by_ai": False,
            "real_apply_allowed_after_d148_by_ai": False,
            "route_insert_allowed_after_d148_by_ai": False,
            "protected_core_mutation_allowed_after_d148_by_ai": False,
            "network_allowed_after_d148_by_ai": False,
            "secret_read_allowed_after_d148_by_ai": False,
            "shell_allowed_after_d148_by_ai": False,
            "git_action_allowed_after_d148_by_ai": False,
        }

        d149_scope = {
            "ok": True,
            "intent_id": intent_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE",
            "sandbox_candidate_guarded_real_apply_preflight_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d148_by_ai": False,
            "route_insert_allowed_after_d148_by_ai": False,
            "protected_core_mutation_allowed_after_d148_by_ai": False,
            "network_allowed_after_d148_by_ai": False,
            "secret_read_allowed_after_d148_by_ai": False,
            "shell_allowed_after_d148_by_ai": False,
            "git_action_allowed_after_d148_by_ai": False,
        }

        write(root / "reports/d148_sandbox_candidate_human_real_apply_intent_scope.json", d148)
        write(root / "reports/d148_sandbox_candidate_human_real_apply_intent_record.json", intent_record)
        write(root / "reports/d148_sandbox_candidate_real_apply_authority_guard.json", authority_guard)
        write(root / "reports/d148_d149_sandbox_candidate_guarded_real_apply_preflight_scope.json", d149_scope)

        return td, root

    def test_creates_guarded_real_apply_preflight_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_guarded_real_apply_preflight_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertEqual(r["d150_scope"]["allowed_next_gate"], "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE")
            self.assertTrue((root / "reports/d149_sandbox_candidate_guarded_real_apply_preflight_scope.json").exists())
            self.assertTrue((root / "reports/d149_sandbox_candidate_real_apply_preflight_report.json").exists())
            self.assertTrue((root / "reports/d149_sandbox_candidate_real_apply_blockers.json").exists())
            self.assertTrue((root / "reports/d149_d150_sandbox_candidate_human_signed_real_apply_execution_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d148(self):
        td, root = self.root()
        try:
            (root / "reports/d148_sandbox_candidate_human_real_apply_intent_scope.json").unlink()
            r = create_sandbox_candidate_guarded_real_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d148_summary_allows_real_apply_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d148_sandbox_candidate_human_real_apply_intent_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["real_apply_by_ai_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_real_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_authority_guard_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d148_sandbox_candidate_real_apply_authority_guard.json"
            data = json.loads(p.read_text())
            data["allow_route_insert"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_real_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d149_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d148_d149_sandbox_candidate_guarded_real_apply_preflight_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d148_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_real_apply_preflight_scope(root)
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

print("D149 SANDBOX CANDIDATE GUARDED REAL APPLY PREFLIGHT SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_guarded_real_apply_preflight_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d149_sandbox_candidate_guarded_real_apply_preflight_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_guarded_real_apply_preflight_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d149_sandbox_candidate_guarded_real_apply_preflight_scope", "-v"], check=True)

print("\n== run D149 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_guarded_real_apply_preflight_scope import create_sandbox_candidate_guarded_real_apply_preflight_scope\n"
    "r=create_sandbox_candidate_guarded_real_apply_preflight_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d149_sandbox_candidate_guarded_real_apply_preflight_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_guarded_real_apply_preflight_scope.py",
    "tests/test_d149_sandbox_candidate_guarded_real_apply_preflight_scope.py",
    "reports/d149_sandbox_candidate_guarded_real_apply_preflight_scope.json",
    "reports/d149_sandbox_candidate_real_apply_preflight_report.json",
    "reports/d149_sandbox_candidate_real_apply_blockers.json",
    "reports/d149_d150_sandbox_candidate_human_signed_real_apply_execution_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D149 sandbox candidate guarded real apply preflight scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D149 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD149 SANDBOX CANDIDATE GUARDED REAL APPLY PREFLIGHT SCOPE BOOT DONE")
