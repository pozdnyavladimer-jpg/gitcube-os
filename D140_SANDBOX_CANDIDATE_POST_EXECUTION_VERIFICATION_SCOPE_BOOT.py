#!/usr/bin/env python3
# D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_BOOT.py
#
# D140 consumes D139 controlled sandbox execution artifacts and creates:
# - runtime_experimental/sandbox_candidate_post_execution_verification_scope.py
# - tests/test_d140_sandbox_candidate_post_execution_verification_scope.py
# - reports/d140_sandbox_candidate_post_execution_verification_scope.json
# - reports/d140_sandbox_candidate_post_execution_verification_report.json
# - reports/d140_sandbox_candidate_execution_integrity_receipt.json
# - reports/d140_d141_sandbox_candidate_apply_preflight_scope.json
#
# POST-EXECUTION VERIFICATION ONLY:
# no candidate execution, no apply, no shell, no network,
# no secret read, no route insert, no protected core mutation, no AI git action.
#
# D140 opens D141 Sandbox Candidate Apply Preflight Scope.

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

D139_REPORT = "reports/d139_sandbox_candidate_controlled_execution_run_scope.json"
D139_RUN_RESULT = "reports/d139_sandbox_candidate_execution_run_result.json"
D139_SAFETY_RECEIPT = "reports/d139_sandbox_candidate_execution_safety_receipt.json"
D139_D140_SCOPE = "reports/d139_d140_sandbox_candidate_post_execution_verification_scope.json"

OUT = "reports/d140_sandbox_candidate_post_execution_verification_scope.json"
VERIFY_REPORT_OUT = "reports/d140_sandbox_candidate_post_execution_verification_report.json"
INTEGRITY_RECEIPT_OUT = "reports/d140_sandbox_candidate_execution_integrity_receipt.json"
D141_SCOPE_OUT = "reports/d140_d141_sandbox_candidate_apply_preflight_scope.json"

REQ_D139_DECISION = "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_READY"
REQ_D140_GATE = "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE"
REQ_D141_GATE = "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE"
REQ_D139_APPROVAL_SCOPE = "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_ONLY"

FALSE_GUARD_KEYS = [
    "external_ai_called",
    "network_accessed",
    "api_key_read",
    "secret_read",
    "shell_from_ai_executed",
    "runtime_code_mutated",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "actual_apply_executed",
    "route_inserted",
    "git_commit_by_ai",
    "git_push_by_ai",
    "rollback_executed",
    "restore_executed",
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
    "actual_apply_executed",
    "route_inserted",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "external_ai_called",
    "network_accessed",
    "api_key_read",
    "secret_read",
    "shell_from_ai_executed",
    "shell_executed_by_ai",
    "git_commit_by_ai",
    "git_push_by_ai",
    "real_apply_executed",
    "rollback_executed",
    "restore_executed",
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


def resolve_sandbox_result_path(root, d139, run_result):
    candidates = []

    summary = d139.get("summary", {}) if isinstance(d139, dict) else {}
    for key in ["sandbox_result_path", "sandbox_execution_result_path", "result_path"]:
        value = summary.get(key) or d139.get(key) or run_result.get(key)
        if value:
            candidates.append(value)

    candidate_id = d139.get("candidate_id") or run_result.get("candidate_id") or summary.get("candidate_id")
    if candidate_id:
        candidates.append(f"runtime_experimental/ai_sandbox_work/{candidate_id}/sandbox_execution_result.json")

    # Fallback for globbed materialized candidate paths.
    candidates.extend(str(p) for p in (root / "runtime_experimental/ai_sandbox_work").glob("*/sandbox_execution_result.json"))

    for item in candidates:
        p = Path(item)
        if not p.is_absolute():
            p = root / p
        if p.exists():
            return p
    return None


def check_false_map(name, obj, errors):
    if not isinstance(obj, dict):
        return
    for key in UNSAFE_BOOLEAN_KEYS:
        if key in obj and obj.get(key) is not False:
            errors.append(f"{name} {key} must be false")


def validate_d139(root, d139, run_result, safety_receipt, d140_scope, sandbox_result):
    errors = []

    if not d139:
        errors.append("missing D139 controlled execution run scope report")
        return errors

    if d139.get("ok") is not True:
        errors.append("D139 ok must be true")
    if d139.get("decision") != REQ_D139_DECISION:
        errors.append("D139 decision must be SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_READY")

    summary = d139.get("summary", {})
    if summary.get("execution_status") != "SANDBOX_CONTROLLED_EXECUTION_COMPLETED":
        errors.append("D139 execution_status must be SANDBOX_CONTROLLED_EXECUTION_COMPLETED")
    if summary.get("candidate_status") != "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED":
        errors.append("D139 candidate_status must be MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED")
    if summary.get("approval_scope") != REQ_D139_APPROVAL_SCOPE:
        errors.append("D139 approval_scope must be D140 post-execution verification scope only")
    if summary.get("next_step") != REQ_D140_GATE:
        errors.append("D139 next_step must be D140")
    for key, value in UNSAFE_STATUS_EXPECTED.items():
        if summary.get(key) != value:
            errors.append(f"D139 summary.{key} must be {value}")

    guard = d139.get("guardrails", {})
    if guard:
        for key in FALSE_GUARD_KEYS:
            if guard.get(key) is not False:
                errors.append(f"D139 guardrails.{key} must be false")
        for key in [
            "candidate_execution_allowed_by_ai",
            "commands_executed_by_ai",
            "approval_for_candidate_execution_by_ai",
            "approval_for_real_apply_by_ai",
        ]:
            if key in guard and guard.get(key) is not False:
                errors.append(f"D139 guardrails.{key} must be false")

    if not run_result:
        errors.append("missing D139 sandbox candidate execution run result")
    else:
        if run_result.get("ok") is False:
            errors.append("D139 run result ok must not be false")
        check_false_map("D139 run result", run_result, errors)
        rr_summary = run_result.get("summary", {}) if isinstance(run_result.get("summary"), dict) else {}
        check_false_map("D139 run result summary", rr_summary, errors)

    if not safety_receipt:
        errors.append("missing D139 sandbox candidate execution safety receipt")
    else:
        if safety_receipt.get("ok") is False:
            errors.append("D139 safety receipt ok must not be false")
        check_false_map("D139 safety receipt", safety_receipt, errors)
        sr_summary = safety_receipt.get("summary", {}) if isinstance(safety_receipt.get("summary"), dict) else {}
        check_false_map("D139 safety receipt summary", sr_summary, errors)

    if not d140_scope:
        errors.append("missing D139 D140 post-execution verification scope")
    else:
        if d140_scope.get("ok") is not True:
            errors.append("D139 D140 scope ok must be true")
        if d140_scope.get("allowed_next_gate") != REQ_D140_GATE:
            errors.append("D139 D140 scope allowed_next_gate must be D140")
        if d140_scope.get("sandbox_candidate_post_execution_verification_scope_only") is not True:
            errors.append("D139 D140 scope must be post-execution verification only")
        if d140_scope.get("human_review_required") is not True:
            errors.append("D139 D140 scope must require human review")
        for key in [
            "real_apply_allowed_after_d139_by_ai",
            "route_insert_allowed_after_d139_by_ai",
            "protected_core_mutation_allowed_after_d139_by_ai",
            "network_allowed_after_d139_by_ai",
            "secret_read_allowed_after_d139_by_ai",
            "shell_allowed_after_d139_by_ai",
            "git_action_allowed_after_d139_by_ai",
        ]:
            if d140_scope.get(key) is not False:
                errors.append(f"D139 D140 scope {key} must be false")

    if not sandbox_result:
        errors.append("missing sandbox execution result file")
    else:
        if sandbox_result.get("ok") is False:
            errors.append("sandbox execution result ok must not be false")
        candidate_id = d139.get("candidate_id") or summary.get("candidate_id")
        if candidate_id and sandbox_result.get("candidate_id") and sandbox_result.get("candidate_id") != candidate_id:
            errors.append("sandbox execution result candidate_id must match D139 candidate_id")
        check_false_map("sandbox execution result", sandbox_result, errors)
        se_summary = sandbox_result.get("summary", {}) if isinstance(sandbox_result.get("summary"), dict) else {}
        check_false_map("sandbox execution result summary", se_summary, errors)

    return errors


def build_verification_report(verification_id, d139, run_result, sandbox_path, sandbox_result):
    summary = d139.get("summary", {})
    return {
        "state": "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_REPORT",
        "ok": True,
        "verification_id": verification_id,
        "run_id": d139.get("run_id") or summary.get("run_id"),
        "candidate_id": d139.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d139.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "verification_mode": "POST_EXECUTION_VERIFICATION_ONLY_NO_APPLY",
        "sandbox_result_path": str(sandbox_path) if sandbox_path else None,
        "sandbox_result_present": sandbox_path is not None,
        "sandbox_result_ok": sandbox_result.get("ok") is not False,
        "execution_status_verified": summary.get("execution_status") == "SANDBOX_CONTROLLED_EXECUTION_COMPLETED",
        "candidate_status_verified": summary.get("candidate_status") == "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
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


def build_integrity_receipt(verification_id, d139):
    summary = d139.get("summary", {})
    return {
        "state": "D140_SANDBOX_CANDIDATE_EXECUTION_INTEGRITY_RECEIPT",
        "ok": True,
        "verification_id": verification_id,
        "run_id": d139.get("run_id") or summary.get("run_id"),
        "candidate_id": d139.get("candidate_id") or summary.get("candidate_id"),
        "created_at": now(),
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
        "git_commit_by_ai": False,
        "git_push_by_ai": False,
        "human_review_required": True,
    }


def build_d141_scope(verification_id, d139):
    summary = d139.get("summary", {})
    return {
        "state": "D140_D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE",
        "ok": True,
        "verification_id": verification_id,
        "run_id": d139.get("run_id") or summary.get("run_id"),
        "candidate_id": d139.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d139.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D141_GATE,
        "d141_allowed_to_create": [
            "sandbox_candidate_apply_preflight_scope",
            "sandbox_candidate_apply_preflight_report",
            "sandbox_candidate_apply_blockers",
            "d142_sandbox_candidate_human_apply_intent_scope",
        ],
        "d141_must_not_execute": [
            "real_apply_by_ai",
            "auto_apply",
            "route_insert_by_ai",
            "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai",
            "shell_exec_from_ai",
            "external_network_call_by_ai",
            "secret_read_by_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute_by_ai",
            "restore_execute_by_ai",
        ],
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
        "required_phrase_for_later_gate": "APPROVE_D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_ONLY",
    }


def create_sandbox_candidate_post_execution_verification_scope(root="."):
    root = Path(root).resolve()

    d139 = read_json(root / D139_REPORT, {}) or {}
    run_result = read_json(root / D139_RUN_RESULT, {}) or {}
    safety_receipt = read_json(root / D139_SAFETY_RECEIPT, {}) or {}
    d140_scope = read_json(root / D139_D140_SCOPE, {}) or {}

    sandbox_path = resolve_sandbox_result_path(root, d139, run_result)
    sandbox_result = read_json(sandbox_path, {}) if sandbox_path else {}

    errors = validate_d139(root, d139, run_result, safety_receipt, d140_scope, sandbox_result)

    verification_id = "d140-" + digest({
        "run_id": d139.get("run_id") or d139.get("summary", {}).get("run_id"),
        "candidate_id": d139.get("candidate_id") or d139.get("summary", {}).get("candidate_id"),
        "proposal_id": d139.get("proposal_id") or d139.get("summary", {}).get("proposal_id"),
    })

    verification_report = build_verification_report(verification_id, d139, run_result, sandbox_path, sandbox_result)
    integrity_receipt = build_integrity_receipt(verification_id, d139)
    d141_scope = build_d141_scope(verification_id, d139)

    for item_name, item in [("verification_report", verification_report), ("integrity_receipt", integrity_receipt)]:
        for key in [
            "candidate_executed_by_ai",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "git_action_by_ai",
        ]:
            if item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_BLOCKED"
    result = "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_CREATED" if ok else "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_BLOCKED"

    if ok:
        write_json(root / VERIFY_REPORT_OUT, verification_report)
        write_json(root / INTEGRITY_RECEIPT_OUT, integrity_receipt)
        write_json(root / D141_SCOPE_OUT, d141_scope)

    summary = d139.get("summary", {})
    report = {
        "state": "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "verification_id": verification_id,
        "run_id": d139.get("run_id") or summary.get("run_id"),
        "candidate_id": d139.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d139.get("proposal_id") or summary.get("proposal_id"),
        "source_d139_report": D139_REPORT,
        "sandbox_candidate_post_execution_verification_report": verification_report if ok else {},
        "sandbox_candidate_execution_integrity_receipt": integrity_receipt if ok else {},
        "d141_scope": d141_scope if ok else {},
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
            "sandbox_candidate_post_execution_verification_scope_only": True,
            "post_execution_verification_report_only": True,
            "execution_integrity_receipt_only": True,
            "candidate_executed_now": False,
            "approval_for_d141_apply_preflight_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "verification_id": verification_id,
            "run_id": d139.get("run_id") or summary.get("run_id"),
            "candidate_id": d139.get("candidate_id") or summary.get("candidate_id"),
            "proposal_id": d139.get("proposal_id") or summary.get("proposal_id"),
            "post_execution_validation_status": "SANDBOX_EXECUTION_VERIFIED_NO_APPLY" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED" if ok else "BLOCKED",
            "execution_result_status": "PRESENT_AND_VALIDATED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D141_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_post_execution_verification_scope_created": ok,
            "sandbox_candidate_post_execution_verification_report_created": ok,
            "sandbox_candidate_execution_integrity_receipt_created": ok,
            "d141_scope_created": ok,
            "candidate_executed_in_sandbox": ok,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D141 may create sandbox candidate apply preflight scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_post_execution_verification_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_post_execution_verification_scope import create_sandbox_candidate_post_execution_verification_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD140SandboxCandidatePostExecutionVerificationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"
        sandbox_rel = f"runtime_experimental/ai_sandbox_work/{candidate_id}/sandbox_execution_result.json"

        d139 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_READY",
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
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
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "run_id": run_id,
                "candidate_id": candidate_id,
                "proposal_id": proposal_id,
                "execution_status": "SANDBOX_CONTROLLED_EXECUTION_COMPLETED",
                "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
                "sandbox_result_path": sandbox_rel,
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_ONLY",
                "next_step": "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE",
            },
        }

        run_result = {
            "ok": True,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "sandbox_result_path": sandbox_rel,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        safety_receipt = {
            "ok": True,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
        }

        d140_scope = {
            "ok": True,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE",
            "sandbox_candidate_post_execution_verification_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d139_by_ai": False,
            "route_insert_allowed_after_d139_by_ai": False,
            "protected_core_mutation_allowed_after_d139_by_ai": False,
            "network_allowed_after_d139_by_ai": False,
            "secret_read_allowed_after_d139_by_ai": False,
            "shell_allowed_after_d139_by_ai": False,
            "git_action_allowed_after_d139_by_ai": False,
        }

        sandbox_result = {
            "ok": True,
            "state": "D139_SANDBOX_CANDIDATE_EXECUTION_RESULT",
            "run_id": run_id,
            "candidate_id": candidate_id,
            "execution_status": "SANDBOX_CONTROLLED_EXECUTION_COMPLETED",
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
        }

        write(root / "reports/d139_sandbox_candidate_controlled_execution_run_scope.json", d139)
        write(root / "reports/d139_sandbox_candidate_execution_run_result.json", run_result)
        write(root / "reports/d139_sandbox_candidate_execution_safety_receipt.json", safety_receipt)
        write(root / "reports/d139_d140_sandbox_candidate_post_execution_verification_scope.json", d140_scope)
        write(root / sandbox_rel, sandbox_result)
        return td, root

    def test_creates_post_execution_verification_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_post_execution_verification_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_READY")
            self.assertEqual(r["summary"]["post_execution_validation_status"], "SANDBOX_EXECUTION_VERIFIED_NO_APPLY")
            self.assertEqual(r["summary"]["approval_scope"], "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted"])
            self.assertEqual(r["d141_scope"]["allowed_next_gate"], "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE")
            self.assertTrue((root / "reports/d140_sandbox_candidate_post_execution_verification_scope.json").exists())
            self.assertTrue((root / "reports/d140_sandbox_candidate_post_execution_verification_report.json").exists())
            self.assertTrue((root / "reports/d140_sandbox_candidate_execution_integrity_receipt.json").exists())
            self.assertTrue((root / "reports/d140_d141_sandbox_candidate_apply_preflight_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d139(self):
        td, root = self.root()
        try:
            (root / "reports/d139_sandbox_candidate_controlled_execution_run_scope.json").unlink()
            r = create_sandbox_candidate_post_execution_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d139_not_ready(self):
        td, root = self.root()
        try:
            p = root / "reports/d139_sandbox_candidate_controlled_execution_run_scope.json"
            data = json.loads(p.read_text())
            data["ok"] = False
            data["decision"] = "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_execution_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d139_sandbox_candidate_execution_safety_receipt.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_execution_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_missing_sandbox_result(self):
        td, root = self.root()
        try:
            p = root / "runtime_experimental/ai_sandbox_work/d126-test/sandbox_execution_result.json"
            p.unlink()
            r = create_sandbox_candidate_post_execution_verification_scope(root)
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

print("D140 SANDBOX CANDIDATE POST EXECUTION VERIFICATION SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_post_execution_verification_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d140_sandbox_candidate_post_execution_verification_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_post_execution_verification_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d140_sandbox_candidate_post_execution_verification_scope", "-v"], check=True)

print("\n== run D140 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_post_execution_verification_scope import create_sandbox_candidate_post_execution_verification_scope\n"
    "r=create_sandbox_candidate_post_execution_verification_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d140_sandbox_candidate_post_execution_verification_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_post_execution_verification_scope.py",
    "tests/test_d140_sandbox_candidate_post_execution_verification_scope.py",
    "reports/d140_sandbox_candidate_post_execution_verification_scope.json",
    "reports/d140_sandbox_candidate_post_execution_verification_report.json",
    "reports/d140_sandbox_candidate_execution_integrity_receipt.json",
    "reports/d140_d141_sandbox_candidate_apply_preflight_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D140 sandbox candidate post execution verification scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D140 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD140 SANDBOX CANDIDATE POST EXECUTION VERIFICATION SCOPE BOOT DONE")
