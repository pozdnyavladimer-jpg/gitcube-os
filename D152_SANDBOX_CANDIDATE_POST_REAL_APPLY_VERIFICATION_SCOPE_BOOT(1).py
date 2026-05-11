#!/usr/bin/env python3
# D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_BOOT.py
#
# D152 consumes D151 guarded real-apply run artifacts and creates:
# - runtime_experimental/sandbox_candidate_post_real_apply_verification_scope.py
# - tests/test_d152_sandbox_candidate_post_real_apply_verification_scope.py
# - reports/d152_sandbox_candidate_post_real_apply_verification_scope.json
# - reports/d152_sandbox_candidate_real_apply_verification_report.json
# - reports/d152_sandbox_candidate_real_apply_integrity_receipt.json
# - reports/d152_d153_sandbox_candidate_final_real_apply_audit_scope.json
#
# POST REAL APPLY VERIFICATION SCOPE ONLY:
# no second apply, no route insert, no protected core mutation by AI, no shell,
# no network/provider call, no secret read, no git action by AI,
# no candidate re-execution.
#
# D152 opens D153 Final Real Apply Audit Scope only.

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

D151_REPORT = "reports/d151_sandbox_candidate_guarded_real_apply_run_scope.json"
D151_RUN_RESULT = "reports/d151_sandbox_candidate_real_apply_run_result.json"
D151_SAFETY_RECEIPT = "reports/d151_sandbox_candidate_real_apply_run_safety_receipt.json"
D151_D152_SCOPE = "reports/d151_d152_sandbox_candidate_post_real_apply_verification_scope.json"

OUT = "reports/d152_sandbox_candidate_post_real_apply_verification_scope.json"
VERIFICATION_REPORT_OUT = "reports/d152_sandbox_candidate_real_apply_verification_report.json"
INTEGRITY_RECEIPT_OUT = "reports/d152_sandbox_candidate_real_apply_integrity_receipt.json"
D153_SCOPE_OUT = "reports/d152_d153_sandbox_candidate_final_real_apply_audit_scope.json"

REQ_D151_DECISION = "SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_READY"
REQ_D152_GATE = "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE"
REQ_D153_GATE = "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE"

STATUS_FALSE_D151 = [
    "real_apply_allowed_after_d151_by_ai",
    "route_insert_allowed_after_d151_by_ai",
    "protected_core_mutation_allowed_after_d151_by_ai",
    "network_allowed_after_d151_by_ai",
    "secret_read_allowed_after_d151_by_ai",
    "shell_allowed_after_d151_by_ai",
    "git_action_allowed_after_d151_by_ai",
]

FALSE_BY_AI_KEYS = [
    "actual_apply_executed_by_ai",
    "real_apply_executed_by_ai",
    "route_inserted_by_ai",
    "protected_core_mutated_by_ai",
    "network_accessed",
    "secret_read",
    "shell_executed_by_ai",
    "shell_from_ai_executed",
    "git_action_by_ai",
    "git_commit_by_ai",
    "git_push_by_ai",
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


def check_false(data, keys, errors, prefix):
    for key in keys:
        if key in data and data.get(key) is not False:
            errors.append(f"{prefix} {key} must be false")


def validate_d151(d151, run_result, safety_receipt, d152_scope):
    errors = []

    if not d151:
        errors.append("missing D151 sandbox candidate guarded real apply run scope report")
        return errors

    if d151.get("ok") is not True:
        errors.append("D151 ok must be true")
    if d151.get("decision") != REQ_D151_DECISION:
        errors.append("D151 decision must be SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_READY")

    summary = d151.get("summary", {})
    expected = {
        "real_apply_run_status": "GUARDED_REAL_APPLY_RUN_SCOPE_RECORDED_NO_AI_CORE_MUTATION",
        "safety_receipt_status": "AI_DID_NOT_EXECUTE_REAL_CORE_APPLY",
        "candidate_status": "REAL_APPLY_RUN_SCOPE_RECORDED_POST_VERIFICATION_REQUIRED_NOT_CORE_MUTATED_BY_AI",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_ONLY",
        "next_step": REQ_D152_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D151 summary.{key} must be {value}")

    guard = d151.get("guardrails", {})
    check_false(guard, FALSE_BY_AI_KEYS, errors, "D151 guardrails")
    for key in STATUS_FALSE_D151:
        if guard.get(key) is not False:
            errors.append(f"D151 guardrails.{key} must be false")
    for key in [
        "sandbox_candidate_guarded_real_apply_run_scope_only",
        "real_apply_run_result_only",
        "real_apply_run_safety_receipt_only",
        "approval_for_d152_post_real_apply_verification_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D151 guardrails.{key} must be true")

    if not run_result:
        errors.append("missing D151 real apply run result")
    else:
        if run_result.get("ok") is not True:
            errors.append("D151 run result ok must be true")
        if run_result.get("real_apply_run_status") != "GUARDED_REAL_APPLY_RUN_RECORDED_NO_AI_EXECUTION":
            errors.append("D151 run result status must be no-AI-execution")
        if run_result.get("operator_authorized_run_scope") is not True:
            errors.append("D151 run result must show operator authorized run scope")
        if run_result.get("operator_actual_core_apply_executed") not in (False, None):
            errors.append("D151 operator_actual_core_apply_executed must be false or absent at scope stage")
        check_false(run_result, FALSE_BY_AI_KEYS, errors, "D151 run result")

    if not safety_receipt:
        errors.append("missing D151 real apply run safety receipt")
    else:
        if safety_receipt.get("ok") is not True:
            errors.append("D151 safety receipt ok must be true")
        if safety_receipt.get("safety_status") != "AI_DID_NOT_EXECUTE_REAL_CORE_APPLY":
            errors.append("D151 safety status must be AI_DID_NOT_EXECUTE_REAL_CORE_APPLY")
        for key in [
            "no_ai_apply",
            "no_ai_route_insert",
            "no_ai_protected_core_mutation",
            "no_ai_network",
            "no_ai_secret_read",
            "no_ai_shell",
            "no_ai_git_action",
        ]:
            if safety_receipt.get(key) is not True:
                errors.append(f"D151 safety receipt {key} must be true")
        check_false(safety_receipt, FALSE_BY_AI_KEYS, errors, "D151 safety receipt")

    if not d152_scope:
        errors.append("missing D151 D152 post real apply verification scope")
    else:
        if d152_scope.get("ok") is not True:
            errors.append("D151 D152 scope ok must be true")
        if d152_scope.get("allowed_next_gate") != REQ_D152_GATE:
            errors.append("D151 D152 scope allowed_next_gate must be D152")
        if d152_scope.get("sandbox_candidate_post_real_apply_verification_scope_only") is not True:
            errors.append("D151 D152 scope must be post-real-apply-verification-only")
        if d152_scope.get("human_review_required") is not True:
            errors.append("D151 D152 scope must require human review")
        for key in STATUS_FALSE_D151:
            if d152_scope.get(key) is not False:
                errors.append(f"D151 D152 scope {key} must be false")

    return errors


def build_verification_report(verification_id, d151):
    return {
        "state": "D152_SANDBOX_CANDIDATE_REAL_APPLY_VERIFICATION_REPORT",
        "ok": True,
        "verification_id": verification_id,
        "run_apply_id": d151.get("run_apply_id"),
        "signature_id": d151.get("signature_id"),
        "preflight_id": d151.get("preflight_id"),
        "intent_id": d151.get("intent_id"),
        "decision_id": d151.get("decision_id"),
        "archive_id": d151.get("archive_id"),
        "candidate_id": d151.get("candidate_id"),
        "proposal_id": d151.get("proposal_id"),
        "created_at": now(),
        "verification_mode": "POST_REAL_APPLY_VERIFICATION_ONLY_NO_SECOND_APPLY",
        "verification_status": "REAL_APPLY_RUN_SCOPE_VERIFIED_NO_AI_CORE_MUTATION",
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "route_inserted_by_ai": False,
        "protected_core_mutated": False,
        "protected_core_mutated_by_ai": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_integrity_receipt(verification_id, d151):
    return {
        "state": "D152_SANDBOX_CANDIDATE_REAL_APPLY_INTEGRITY_RECEIPT",
        "ok": True,
        "verification_id": verification_id,
        "run_apply_id": d151.get("run_apply_id"),
        "candidate_id": d151.get("candidate_id"),
        "created_at": now(),
        "receipt_mode": "REAL_APPLY_INTEGRITY_RECEIPT_NO_AI_CORE_ACTION",
        "integrity_status": "NO_AI_CORE_MUTATION_VERIFIED",
        "ai_apply_status": "BLOCKED",
        "ai_route_insert_status": "BLOCKED",
        "ai_protected_core_status": "UNTOUCHED_BY_AI",
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "route_inserted_by_ai": False,
        "protected_core_mutated": False,
        "protected_core_mutated_by_ai": False,
        "canonical_memory_mutated": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_d153_scope(verification_id, d151):
    return {
        "state": "D152_D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE",
        "ok": True,
        "verification_id": verification_id,
        "run_apply_id": d151.get("run_apply_id"),
        "signature_id": d151.get("signature_id"),
        "preflight_id": d151.get("preflight_id"),
        "intent_id": d151.get("intent_id"),
        "decision_id": d151.get("decision_id"),
        "archive_id": d151.get("archive_id"),
        "candidate_id": d151.get("candidate_id"),
        "proposal_id": d151.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D153_GATE,
        "sandbox_candidate_final_real_apply_audit_scope_only": True,
        "human_review_required": True,
        "d153_allowed_to_create": [
            "final_real_apply_audit_scope",
            "real_apply_audit_ledger",
            "real_apply_replay_index",
            "d154_real_apply_chain_archive_scope",
        ],
        "d153_must_not_execute": [
            "real_core_apply_again",
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
        "real_apply_allowed_after_d152_by_ai": False,
        "route_insert_allowed_after_d152_by_ai": False,
        "protected_core_mutation_allowed_after_d152_by_ai": False,
        "network_allowed_after_d152_by_ai": False,
        "secret_read_allowed_after_d152_by_ai": False,
        "shell_allowed_after_d152_by_ai": False,
        "git_action_allowed_after_d152_by_ai": False,
    }


def create_sandbox_candidate_post_real_apply_verification_scope(root="."):
    root = Path(root).resolve()

    d151 = read_json(root / D151_REPORT, {}) or {}
    run_result = read_json(root / D151_RUN_RESULT, {}) or {}
    safety_receipt = read_json(root / D151_SAFETY_RECEIPT, {}) or {}
    d152_scope = read_json(root / D151_D152_SCOPE, {}) or {}

    errors = validate_d151(d151, run_result, safety_receipt, d152_scope)

    verification_id = "d152-" + digest({
        "run_apply_id": d151.get("run_apply_id"),
        "signature_id": d151.get("signature_id"),
        "preflight_id": d151.get("preflight_id"),
        "candidate_id": d151.get("candidate_id"),
        "proposal_id": d151.get("proposal_id"),
    })

    verification_report = build_verification_report(verification_id, d151)
    integrity_receipt = build_integrity_receipt(verification_id, d151)
    d153_scope = build_d153_scope(verification_id, d151)

    for item_name, item in [
        ("verification_report", verification_report),
        ("integrity_receipt", integrity_receipt),
        ("d153_scope", d153_scope),
    ]:
        for key in [
            "actual_apply_executed_by_ai",
            "real_apply_executed_by_ai",
            "route_inserted",
            "route_inserted_by_ai",
            "protected_core_mutated",
            "protected_core_mutated_by_ai",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "real_apply_allowed_after_d152_by_ai",
            "route_insert_allowed_after_d152_by_ai",
            "protected_core_mutation_allowed_after_d152_by_ai",
            "network_allowed_after_d152_by_ai",
            "secret_read_allowed_after_d152_by_ai",
            "shell_allowed_after_d152_by_ai",
            "git_action_allowed_after_d152_by_ai",
        ]:
            if key in item and item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_BLOCKED"
    result = "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_CREATED" if ok else "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_BLOCKED"

    if ok:
        write_json(root / VERIFICATION_REPORT_OUT, verification_report)
        write_json(root / INTEGRITY_RECEIPT_OUT, integrity_receipt)
        write_json(root / D153_SCOPE_OUT, d153_scope)

    report = {
        "state": "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "verification_id": verification_id,
        "run_apply_id": d151.get("run_apply_id"),
        "signature_id": d151.get("signature_id"),
        "preflight_id": d151.get("preflight_id"),
        "intent_id": d151.get("intent_id"),
        "decision_id": d151.get("decision_id"),
        "archive_id": d151.get("archive_id"),
        "candidate_id": d151.get("candidate_id"),
        "proposal_id": d151.get("proposal_id"),
        "source_d151_report": D151_REPORT,
        "real_apply_verification_report": verification_report if ok else {},
        "real_apply_integrity_receipt": integrity_receipt if ok else {},
        "d153_scope": d153_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "shell_executed_by_ai": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "route_inserted_by_ai": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "sandbox_candidate_post_real_apply_verification_scope_only": True,
            "real_apply_verification_report_only": True,
            "real_apply_integrity_receipt_only": True,
            "approval_for_d153_final_real_apply_audit_scope_only": ok,
            "real_apply_allowed_after_d152_by_ai": False,
            "route_insert_allowed_after_d152_by_ai": False,
            "protected_core_mutation_allowed_after_d152_by_ai": False,
            "network_allowed_after_d152_by_ai": False,
            "secret_read_allowed_after_d152_by_ai": False,
            "shell_allowed_after_d152_by_ai": False,
            "git_action_allowed_after_d152_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "verification_id": verification_id,
            "run_apply_id": d151.get("run_apply_id"),
            "signature_id": d151.get("signature_id"),
            "candidate_id": d151.get("candidate_id"),
            "proposal_id": d151.get("proposal_id"),
            "verification_status": "REAL_APPLY_RUN_SCOPE_VERIFIED_NO_AI_CORE_MUTATION" if ok else "BLOCKED",
            "integrity_status": "NO_AI_CORE_MUTATION_VERIFIED" if ok else "BLOCKED",
            "candidate_status": "POST_REAL_APPLY_VERIFICATION_READY_FOR_FINAL_AUDIT_NOT_CORE_MUTATED_BY_AI" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D153_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "post_real_apply_verification_scope_created": ok,
            "real_apply_verification_report_created": ok,
            "real_apply_integrity_receipt_created": ok,
            "d153_scope_created": ok,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D153 may create final real apply audit scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_post_real_apply_verification_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_post_real_apply_verification_scope import create_sandbox_candidate_post_real_apply_verification_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD152SandboxCandidatePostRealApplyVerificationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        run_apply_id = "d151-test"
        signature_id = "d150-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d151 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_READY",
            "run_apply_id": run_apply_id,
            "signature_id": signature_id,
            "preflight_id": "d149-test",
            "intent_id": "d148-test",
            "decision_id": "d147-test",
            "archive_id": "d146-test",
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": {
                "network_accessed": False,
                "secret_read": False,
                "shell_executed_by_ai": False,
                "actual_apply_executed_by_ai": False,
                "real_apply_executed_by_ai": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "protected_core_mutated_by_ai": False,
                "git_action_by_ai": False,
                "sandbox_candidate_guarded_real_apply_run_scope_only": True,
                "real_apply_run_result_only": True,
                "real_apply_run_safety_receipt_only": True,
                "approval_for_d152_post_real_apply_verification_scope_only": True,
                "approval_for_real_core_apply_by_ai": False,
                "real_apply_allowed_after_d151_by_ai": False,
                "route_insert_allowed_after_d151_by_ai": False,
                "protected_core_mutation_allowed_after_d151_by_ai": False,
                "network_allowed_after_d151_by_ai": False,
                "secret_read_allowed_after_d151_by_ai": False,
                "shell_allowed_after_d151_by_ai": False,
                "git_action_allowed_after_d151_by_ai": False,
            },
            "summary": {
                "real_apply_run_status": "GUARDED_REAL_APPLY_RUN_SCOPE_RECORDED_NO_AI_CORE_MUTATION",
                "safety_receipt_status": "AI_DID_NOT_EXECUTE_REAL_CORE_APPLY",
                "candidate_status": "REAL_APPLY_RUN_SCOPE_RECORDED_POST_VERIFICATION_REQUIRED_NOT_CORE_MUTATED_BY_AI",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_ONLY",
                "next_step": "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE",
            },
        }

        run_result = {
            "ok": True,
            "run_apply_id": run_apply_id,
            "real_apply_run_status": "GUARDED_REAL_APPLY_RUN_RECORDED_NO_AI_EXECUTION",
            "operator_authorized_run_scope": True,
            "operator_actual_core_apply_executed": False,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        safety_receipt = {
            "ok": True,
            "run_apply_id": run_apply_id,
            "safety_status": "AI_DID_NOT_EXECUTE_REAL_CORE_APPLY",
            "no_ai_apply": True,
            "no_ai_route_insert": True,
            "no_ai_protected_core_mutation": True,
            "no_ai_network": True,
            "no_ai_secret_read": True,
            "no_ai_shell": True,
            "no_ai_git_action": True,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        d152_scope = {
            "ok": True,
            "run_apply_id": run_apply_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE",
            "sandbox_candidate_post_real_apply_verification_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d151_by_ai": False,
            "route_insert_allowed_after_d151_by_ai": False,
            "protected_core_mutation_allowed_after_d151_by_ai": False,
            "network_allowed_after_d151_by_ai": False,
            "secret_read_allowed_after_d151_by_ai": False,
            "shell_allowed_after_d151_by_ai": False,
            "git_action_allowed_after_d151_by_ai": False,
        }

        write(root / "reports/d151_sandbox_candidate_guarded_real_apply_run_scope.json", d151)
        write(root / "reports/d151_sandbox_candidate_real_apply_run_result.json", run_result)
        write(root / "reports/d151_sandbox_candidate_real_apply_run_safety_receipt.json", safety_receipt)
        write(root / "reports/d151_d152_sandbox_candidate_post_real_apply_verification_scope.json", d152_scope)

        return td, root

    def test_creates_post_real_apply_verification_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_post_real_apply_verification_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["real_apply_executed_by_ai"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertFalse(r["guardrails"]["git_action_by_ai"])
            self.assertEqual(r["d153_scope"]["allowed_next_gate"], "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE")
            self.assertTrue((root / "reports/d152_sandbox_candidate_post_real_apply_verification_scope.json").exists())
            self.assertTrue((root / "reports/d152_sandbox_candidate_real_apply_verification_report.json").exists())
            self.assertTrue((root / "reports/d152_sandbox_candidate_real_apply_integrity_receipt.json").exists())
            self.assertTrue((root / "reports/d152_d153_sandbox_candidate_final_real_apply_audit_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d151(self):
        td, root = self.root()
        try:
            (root / "reports/d151_sandbox_candidate_guarded_real_apply_run_scope.json").unlink()
            r = create_sandbox_candidate_post_real_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d151_summary_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d151_sandbox_candidate_guarded_real_apply_run_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["route_insert_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_real_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_run_result_says_core_mutated_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d151_sandbox_candidate_real_apply_run_result.json"
            data = json.loads(p.read_text())
            data["protected_core_mutated_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_real_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d152_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d151_d152_sandbox_candidate_post_real_apply_verification_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d151_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_real_apply_verification_scope(root)
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

print("D152 SANDBOX CANDIDATE POST REAL APPLY VERIFICATION SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_post_real_apply_verification_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d152_sandbox_candidate_post_real_apply_verification_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_post_real_apply_verification_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d152_sandbox_candidate_post_real_apply_verification_scope", "-v"], check=True)

print("\n== run D152 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_post_real_apply_verification_scope import create_sandbox_candidate_post_real_apply_verification_scope\n"
    "r=create_sandbox_candidate_post_real_apply_verification_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d152_sandbox_candidate_post_real_apply_verification_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_post_real_apply_verification_scope.py",
    "tests/test_d152_sandbox_candidate_post_real_apply_verification_scope.py",
    "reports/d152_sandbox_candidate_post_real_apply_verification_scope.json",
    "reports/d152_sandbox_candidate_real_apply_verification_report.json",
    "reports/d152_sandbox_candidate_real_apply_integrity_receipt.json",
    "reports/d152_d153_sandbox_candidate_final_real_apply_audit_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D152 sandbox candidate post real apply verification scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D152 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD152 SANDBOX CANDIDATE POST REAL APPLY VERIFICATION SCOPE BOOT DONE")
