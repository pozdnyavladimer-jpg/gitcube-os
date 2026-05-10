#!/usr/bin/env python3
# D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_BOOT.py
#
# D144 consumes D143 sandbox guarded-apply artifacts and creates:
# - runtime_experimental/sandbox_candidate_post_apply_verification_scope.py
# - tests/test_d144_sandbox_candidate_post_apply_verification_scope.py
# - reports/d144_sandbox_candidate_post_apply_verification_scope.json
# - reports/d144_sandbox_candidate_post_apply_verification_report.json
# - reports/d144_sandbox_candidate_apply_integrity_receipt.json
# - reports/d144_d145_sandbox_candidate_final_audit_scope.json
#
# POST APPLY VERIFICATION SCOPE ONLY:
# verifies sandbox apply evidence after D143. It does NOT execute candidate again,
# does NOT perform real/core apply, route insert, protected-core mutation, shell,
# network/provider call, secret read, or AI git action.
#
# D144 opens D145 Sandbox Candidate Final Audit Scope.

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

D143_REPORT = "reports/d143_sandbox_candidate_guarded_apply_scope.json"
D143_APPLY_PLAN = "reports/d143_sandbox_candidate_guarded_apply_plan.json"
D143_APPLY_RECEIPT = "reports/d143_sandbox_candidate_guarded_apply_receipt.json"
D143_D144_SCOPE = "reports/d143_d144_sandbox_candidate_post_apply_verification_scope.json"

OUT = "reports/d144_sandbox_candidate_post_apply_verification_scope.json"
POST_APPLY_REPORT_OUT = "reports/d144_sandbox_candidate_post_apply_verification_report.json"
APPLY_INTEGRITY_RECEIPT_OUT = "reports/d144_sandbox_candidate_apply_integrity_receipt.json"
D145_SCOPE_OUT = "reports/d144_d145_sandbox_candidate_final_audit_scope.json"

REQ_D143_DECISION = "SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_READY"
REQ_D144_GATE = "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE"
REQ_D145_GATE = "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE"
REQ_D143_APPROVAL_SCOPE = "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_ONLY"

FALSE_GUARD_KEYS = [
    "external_ai_called", "network_accessed", "api_key_read", "secret_read",
    "shell_from_ai_executed", "runtime_code_mutated", "protected_core_mutated",
    "canonical_memory_mutated", "actual_apply_executed", "route_inserted",
    "git_commit_by_ai", "git_push_by_ai", "rollback_executed", "restore_executed",
]

UNSAFE_BOOLEAN_KEYS = [
    "actual_apply_executed", "real_apply_executed", "real_core_apply_executed",
    "route_inserted", "protected_core_mutated", "canonical_memory_mutated",
    "runtime_code_mutated", "external_ai_called", "network_accessed", "api_key_read",
    "secret_read", "shell_from_ai_executed", "shell_executed_by_ai",
    "git_commit_by_ai", "git_push_by_ai", "git_action_by_ai", "rollback_executed",
    "restore_executed", "candidate_executed_now", "candidate_executed_by_ai",
    "candidate_reexecuted_now", "auto_apply_allowed", "real_apply_allowed_by_ai",
    "approved_for_real_apply_by_ai",
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

BLOCKED_ACTIONS = [
    "real_apply_by_ai", "auto_apply_by_ai", "route_insert_by_ai",
    "protected_core_mutation_by_ai", "canonical_memory_overwrite_by_ai",
    "shell_exec_from_ai", "external_network_call_by_ai", "secret_read_by_ai",
    "git_commit_by_ai", "git_push_by_ai", "rollback_execute_by_ai",
    "restore_execute_by_ai", "candidate_reexecution_by_ai",
]

REQUIRED_CANDIDATE_FILES = [
    "candidate_manifest.json",
    "candidate_payload.json",
    "candidate_summary.md",
    "sandbox_execution_result.json",
    "sandbox_apply_result.json",
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


def candidate_dir(root, candidate_id):
    if not candidate_id:
        return None
    return root / "runtime_experimental" / "ai_sandbox_work" / candidate_id


def check_false_map(name, obj, errors):
    if not isinstance(obj, dict):
        return
    for key in UNSAFE_BOOLEAN_KEYS:
        if key in obj and obj.get(key) is not False:
            errors.append(f"{name} {key} must be false")


def validate_candidate_files(root, candidate_id, errors):
    cdir = candidate_dir(root, candidate_id)
    if cdir is None:
        errors.append("missing candidate_id")
        return None
    if not cdir.exists():
        errors.append(f"missing sandbox candidate directory: {cdir}")
        return cdir
    for name in REQUIRED_CANDIDATE_FILES:
        if not (cdir / name).exists():
            errors.append(f"missing sandbox candidate file: {name}")
    return cdir


def validate_d143(root, d143, apply_plan, apply_receipt, d144_scope):
    errors = []
    if not d143:
        return ["missing D143 sandbox candidate guarded apply scope report"]

    if d143.get("ok") is not True:
        errors.append("D143 ok must be true")
    if d143.get("decision") != REQ_D143_DECISION:
        errors.append("D143 decision must be SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_READY")

    summary = d143.get("summary", {})
    expected = {
        "guarded_apply_status": "SANDBOX_GUARDED_APPLY_RECORDED_NO_CORE_MUTATION",
        "sandbox_apply_result_status": "CREATED",
        "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_RECORDED_NOT_CORE_APPLIED",
        "execution_result_status": "PRESENT_AND_VALIDATED",
        "approval_scope": REQ_D143_APPROVAL_SCOPE,
        "next_step": REQ_D144_GATE,
    }
    expected.update(UNSAFE_STATUS_EXPECTED)
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D143 summary.{key} must be {value}")

    guard = d143.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D143 guardrails.{key} must be false")
    for key in [
        "sandbox_candidate_guarded_apply_scope_only", "guarded_apply_plan_only",
        "guarded_apply_receipt_only", "approval_for_d144_post_apply_verification_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D143 guardrails.{key} must be true")
    if guard.get("sandbox_apply_result_written") is not True:
        errors.append("D143 guardrails.sandbox_apply_result_written must be true")
    for key in [
        "candidate_executed_now", "approval_for_real_apply_by_ai",
        "approval_for_route_insert_by_ai", "approval_for_protected_core_mutation_by_ai",
        "candidate_execution_allowed_by_ai", "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D143 guardrails.{key} must be false")

    candidate_id = d143.get("candidate_id") or summary.get("candidate_id")
    cdir = validate_candidate_files(root, candidate_id, errors)
    sandbox_apply_result = read_json((cdir / "sandbox_apply_result.json") if cdir else "", {}) or {}
    if sandbox_apply_result:
        if sandbox_apply_result.get("ok") is not True:
            errors.append("sandbox_apply_result ok must be true")
        if sandbox_apply_result.get("result_mode") != "SANDBOX_APPLY_RESULT_ONLY_NO_CORE_MUTATION":
            errors.append("sandbox_apply_result mode must be SANDBOX_APPLY_RESULT_ONLY_NO_CORE_MUTATION")
        if sandbox_apply_result.get("sandbox_apply_status") != "SANDBOX_APPLY_RESULT_RECORDED":
            errors.append("sandbox_apply_result sandbox_apply_status must be recorded")
        if sandbox_apply_result.get("candidate_status") != "MATERIALIZED_EXECUTED_SANDBOX_APPLY_RECORDED_NOT_CORE_APPLIED":
            errors.append("sandbox_apply_result candidate_status must be sandbox apply recorded not core applied")
        check_false_map("sandbox_apply_result", sandbox_apply_result, errors)

    if not apply_plan:
        errors.append("missing D143 sandbox candidate guarded apply plan")
    else:
        if apply_plan.get("ok") is not True:
            errors.append("D143 guarded apply plan ok must be true")
        if apply_plan.get("plan_mode") != "SANDBOX_GUARDED_APPLY_PLAN_WITHOUT_CORE_MUTATION":
            errors.append("D143 guarded apply plan mode must be sandbox/no-core-mutation")
        if apply_plan.get("apply_target_scope") != "SANDBOX_EVIDENCE_ONLY":
            errors.append("D143 guarded apply plan target must be sandbox evidence only")
        if apply_plan.get("guarded_apply_allowed_by_operator_scope") is not True:
            errors.append("D143 guarded apply plan must be operator scope only")
        if apply_plan.get("human_review_required") is not True:
            errors.append("D143 guarded apply plan must require human review")
        check_false_map("D143 guarded apply plan", apply_plan, errors)

    if not apply_receipt:
        errors.append("missing D143 sandbox candidate guarded apply receipt")
    else:
        if apply_receipt.get("ok") is not True:
            errors.append("D143 guarded apply receipt ok must be true")
        if apply_receipt.get("receipt_mode") != "SANDBOX_GUARDED_APPLY_RECEIPT_NO_CORE_MUTATION":
            errors.append("D143 guarded apply receipt mode must be no-core-mutation")
        if apply_receipt.get("sandbox_apply_result_created") is not True:
            errors.append("D143 guarded apply receipt must confirm sandbox apply result created")
        if apply_receipt.get("guarded_apply_status") != "SANDBOX_GUARDED_APPLY_RECORDED_NO_CORE_MUTATION":
            errors.append("D143 guarded apply receipt status must be no-core-mutation")
        if apply_receipt.get("human_review_required") is not True:
            errors.append("D143 guarded apply receipt must require human review")
        check_false_map("D143 guarded apply receipt", apply_receipt, errors)

    if not d144_scope:
        errors.append("missing D143 D144 sandbox candidate post apply verification scope")
    else:
        if d144_scope.get("ok") is not True:
            errors.append("D143 D144 scope ok must be true")
        if d144_scope.get("allowed_next_gate") != REQ_D144_GATE:
            errors.append("D143 D144 scope allowed_next_gate must be D144")
        if d144_scope.get("sandbox_candidate_post_apply_verification_scope_only") is not True:
            errors.append("D143 D144 scope must be post-apply verification scope only")
        if d144_scope.get("human_review_required") is not True:
            errors.append("D143 D144 scope must require human review")
        if d144_scope.get("sandbox_apply_result_created_after_d143") is not True:
            errors.append("D143 D144 scope must confirm sandbox apply result after D143")
        for key in [
            "candidate_executed_after_d143_by_ai", "real_apply_allowed_after_d143_by_ai",
            "auto_apply_allowed_after_d143_by_ai", "route_insert_allowed_after_d143_by_ai",
            "protected_core_mutation_allowed_after_d143_by_ai", "network_allowed_after_d143_by_ai",
            "secret_read_allowed_after_d143_by_ai", "shell_allowed_after_d143_by_ai",
            "git_action_allowed_after_d143_by_ai",
        ]:
            if d144_scope.get(key) is not False:
                errors.append(f"D143 D144 scope {key} must be false")

    return errors


def build_post_apply_report(verification_id, d143, sandbox_apply_result):
    summary = d143.get("summary", {})
    return {
        "state": "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_REPORT",
        "ok": True,
        "verification_id": verification_id,
        "apply_id": d143.get("apply_id") or summary.get("apply_id"),
        "intent_id": d143.get("intent_id") or summary.get("intent_id"),
        "candidate_id": d143.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d143.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "report_mode": "POST_SANDBOX_APPLY_VERIFICATION_ONLY_NO_CORE_MUTATION",
        "sandbox_apply_result_present": bool(sandbox_apply_result),
        "sandbox_apply_result_ok": sandbox_apply_result.get("ok") is True,
        "sandbox_apply_status": sandbox_apply_result.get("sandbox_apply_status"),
        "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_NOT_CORE_APPLIED",
        "post_apply_verification_status": "SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION",
        "actual_apply_executed": False,
        "real_apply_executed": False,
        "real_core_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "shell_from_ai_executed": False,
        "shell_executed_by_ai": False,
        "git_commit_by_ai": False,
        "git_push_by_ai": False,
        "git_action_by_ai": False,
        "candidate_executed_now": False,
        "candidate_executed_by_ai": False,
        "human_review_required": True,
    }


def build_apply_integrity_receipt(verification_id, d143, cdir):
    summary = d143.get("summary", {})
    existing = {}
    if cdir and cdir.exists():
        for name in REQUIRED_CANDIDATE_FILES:
            existing[name] = (cdir / name).exists()
    return {
        "state": "D144_SANDBOX_CANDIDATE_APPLY_INTEGRITY_RECEIPT",
        "ok": True,
        "verification_id": verification_id,
        "apply_id": d143.get("apply_id") or summary.get("apply_id"),
        "run_id": d143.get("run_id") or summary.get("run_id"),
        "candidate_id": d143.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d143.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "receipt_mode": "SANDBOX_APPLY_INTEGRITY_RECEIPT_NO_CORE_MUTATION",
        "candidate_files_present": existing,
        "candidate_files_all_present": bool(existing) and all(existing.values()),
        "sandbox_apply_integrity_status": "SANDBOX_APPLY_EVIDENCE_PRESENT_AND_VALIDATED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "route_insert_status": "BLOCKED",
        "actual_apply_executed": False,
        "real_apply_executed": False,
        "real_core_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "shell_from_ai_executed": False,
        "shell_executed_by_ai": False,
        "git_commit_by_ai": False,
        "git_push_by_ai": False,
        "git_action_by_ai": False,
        "candidate_executed_now": False,
        "candidate_executed_by_ai": False,
        "human_review_required": True,
    }


def build_d145_scope(verification_id, d143):
    summary = d143.get("summary", {})
    return {
        "state": "D144_D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE",
        "ok": True,
        "verification_id": verification_id,
        "apply_id": d143.get("apply_id") or summary.get("apply_id"),
        "intent_id": d143.get("intent_id") or summary.get("intent_id"),
        "preflight_id": d143.get("preflight_id") or summary.get("preflight_id"),
        "run_id": d143.get("run_id") or summary.get("run_id"),
        "candidate_id": d143.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d143.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D145_GATE,
        "d145_allowed_to_create": [
            "sandbox_candidate_final_audit_scope",
            "sandbox_candidate_final_audit_ledger",
            "sandbox_candidate_replay_index",
            "d146_sandbox_candidate_archive_scope",
        ],
        "d145_must_not_execute": BLOCKED_ACTIONS,
        "sandbox_candidate_final_audit_scope_only": True,
        "human_review_required": True,
        "sandbox_apply_verified_after_d144": True,
        "candidate_executed_after_d144_by_ai": False,
        "real_apply_allowed_after_d144_by_ai": False,
        "auto_apply_allowed_after_d144_by_ai": False,
        "route_insert_allowed_after_d144_by_ai": False,
        "protected_core_mutation_allowed_after_d144_by_ai": False,
        "network_allowed_after_d144_by_ai": False,
        "secret_read_allowed_after_d144_by_ai": False,
        "shell_allowed_after_d144_by_ai": False,
        "git_action_allowed_after_d144_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_ONLY",
    }


def create_sandbox_candidate_post_apply_verification_scope(root="."):
    root = Path(root).resolve()
    d143 = read_json(root / D143_REPORT, {}) or {}
    apply_plan = read_json(root / D143_APPLY_PLAN, {}) or {}
    apply_receipt = read_json(root / D143_APPLY_RECEIPT, {}) or {}
    d144_scope_in = read_json(root / D143_D144_SCOPE, {}) or {}

    errors = validate_d143(root, d143, apply_plan, apply_receipt, d144_scope_in)
    summary = d143.get("summary", {})
    candidate_id = d143.get("candidate_id") or summary.get("candidate_id")
    cdir = candidate_dir(root, candidate_id) if candidate_id else None
    sandbox_apply_result = read_json((cdir / "sandbox_apply_result.json") if cdir else "", {}) or {}

    verification_id = "d144-" + digest({
        "apply_id": d143.get("apply_id") or summary.get("apply_id"),
        "run_id": d143.get("run_id") or summary.get("run_id"),
        "candidate_id": candidate_id,
        "proposal_id": d143.get("proposal_id") or summary.get("proposal_id"),
    })

    post_apply_report = build_post_apply_report(verification_id, d143, sandbox_apply_result)
    integrity_receipt = build_apply_integrity_receipt(verification_id, d143, cdir)
    d145_scope = build_d145_scope(verification_id, d143)

    for item_name, item in [
        ("post_apply_report", post_apply_report),
        ("apply_integrity_receipt", integrity_receipt),
    ]:
        check_false_map(item_name, item, errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_BLOCKED"
    result = "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_CREATED" if ok else "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_BLOCKED"

    if ok:
        write_json(root / POST_APPLY_REPORT_OUT, post_apply_report)
        write_json(root / APPLY_INTEGRITY_RECEIPT_OUT, integrity_receipt)
        write_json(root / D145_SCOPE_OUT, d145_scope)

    report = {
        "state": "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "verification_id": verification_id,
        "apply_id": d143.get("apply_id") or summary.get("apply_id"),
        "intent_id": d143.get("intent_id") or summary.get("intent_id"),
        "preflight_id": d143.get("preflight_id") or summary.get("preflight_id"),
        "run_id": d143.get("run_id") or summary.get("run_id"),
        "candidate_id": candidate_id,
        "proposal_id": d143.get("proposal_id") or summary.get("proposal_id"),
        "source_d143_report": D143_REPORT,
        "sandbox_candidate_post_apply_verification_report": post_apply_report if ok else {},
        "sandbox_candidate_apply_integrity_receipt": integrity_receipt if ok else {},
        "d145_scope": d145_scope if ok else {},
        "guardrails": {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False, "secret_read": False,
            "shell_from_ai_executed": False, "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False, "route_inserted": False,
            "git_commit_by_ai": False, "git_push_by_ai": False, "rollback_executed": False, "restore_executed": False,
            "sandbox_candidate_post_apply_verification_scope_only": True,
            "post_apply_verification_report_only": True,
            "apply_integrity_receipt_only": True,
            "candidate_executed_now": False,
            "approval_for_d145_final_audit_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "approval_for_route_insert_by_ai": False,
            "approval_for_protected_core_mutation_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "verification_id": verification_id,
            "apply_id": d143.get("apply_id") or summary.get("apply_id"),
            "run_id": d143.get("run_id") or summary.get("run_id"),
            "candidate_id": candidate_id,
            "proposal_id": d143.get("proposal_id") or summary.get("proposal_id"),
            "post_apply_verification_status": "SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION" if ok else "BLOCKED",
            "sandbox_apply_integrity_status": "SANDBOX_APPLY_EVIDENCE_PRESENT_AND_VALIDATED" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_NOT_CORE_APPLIED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D145_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_post_apply_verification_scope_created": ok,
            "sandbox_candidate_post_apply_verification_report_created": ok,
            "sandbox_candidate_apply_integrity_receipt_created": ok,
            "d145_scope_created": ok,
            "sandbox_apply_verified": ok,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "real_core_apply_executed": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D145 may create final audit scope only.",
        },
    }
    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_post_apply_verification_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_post_apply_verification_scope import create_sandbox_candidate_post_apply_verification_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD144SandboxCandidatePostApplyVerificationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        apply_id = "d143-test"
        intent_id = "d142-test"
        preflight_id = "d141-test"
        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"
        cdir = root / "runtime_experimental" / "ai_sandbox_work" / candidate_id
        cdir.mkdir(parents=True, exist_ok=True)
        write(cdir / "candidate_manifest.json", {"ok": True, "candidate_id": candidate_id})
        write(cdir / "candidate_payload.json", {"ok": True, "candidate_id": candidate_id})
        (cdir / "candidate_summary.md").write_text("# candidate summary\n", encoding="utf-8")
        write(cdir / "sandbox_execution_result.json", {"ok": True, "candidate_id": candidate_id})
        write(cdir / "sandbox_apply_result.json", {
            "ok": True,
            "apply_id": apply_id,
            "candidate_id": candidate_id,
            "result_mode": "SANDBOX_APPLY_RESULT_ONLY_NO_CORE_MUTATION",
            "sandbox_apply_status": "SANDBOX_APPLY_RESULT_RECORDED",
            "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_RECORDED_NOT_CORE_APPLIED",
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "candidate_executed_now": False,
            "human_review_required": True,
        })

        false_guard = {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False, "secret_read": False,
            "shell_from_ai_executed": False, "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False, "route_inserted": False,
            "git_commit_by_ai": False, "git_push_by_ai": False, "rollback_executed": False, "restore_executed": False,
        }
        d143 = {
            "ok": True, "decision": "SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_READY",
            "apply_id": apply_id, "intent_id": intent_id, "preflight_id": preflight_id,
            "run_id": run_id, "candidate_id": candidate_id, "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_guarded_apply_scope_only": True,
                "guarded_apply_plan_only": True,
                "guarded_apply_receipt_only": True,
                "sandbox_apply_result_written": True,
                "candidate_executed_now": False,
                "approval_for_d144_post_apply_verification_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "approval_for_route_insert_by_ai": False,
                "approval_for_protected_core_mutation_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "guarded_apply_status": "SANDBOX_GUARDED_APPLY_RECORDED_NO_CORE_MUTATION",
                "sandbox_apply_result_status": "CREATED",
                "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_RECORDED_NOT_CORE_APPLIED",
                "execution_result_status": "PRESENT_AND_VALIDATED",
                "real_provider_status": "NOT_CALLED", "network_status": "NOT_ACCESSED", "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED", "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED", "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_ONLY",
                "next_step": "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE",
            },
        }
        apply_plan = {
            "ok": True, "apply_id": apply_id, "candidate_id": candidate_id,
            "plan_mode": "SANDBOX_GUARDED_APPLY_PLAN_WITHOUT_CORE_MUTATION",
            "apply_target_scope": "SANDBOX_EVIDENCE_ONLY",
            "guarded_apply_allowed_by_operator_scope": True,
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "candidate_executed_now": False,
            "human_review_required": True,
        }
        apply_receipt = {
            "ok": True, "apply_id": apply_id, "candidate_id": candidate_id,
            "receipt_mode": "SANDBOX_GUARDED_APPLY_RECEIPT_NO_CORE_MUTATION",
            "sandbox_apply_result_created": True,
            "guarded_apply_status": "SANDBOX_GUARDED_APPLY_RECORDED_NO_CORE_MUTATION",
            "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_RECORDED_NOT_CORE_APPLIED",
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "shell_executed_by_ai": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "candidate_executed_now": False,
            "candidate_executed_by_ai": False,
            "human_review_required": True,
        }
        d144_scope = {
            "ok": True, "apply_id": apply_id, "candidate_id": candidate_id,
            "allowed_next_gate": "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE",
            "sandbox_candidate_post_apply_verification_scope_only": True,
            "human_review_required": True,
            "sandbox_apply_result_created_after_d143": True,
            "candidate_executed_after_d143_by_ai": False,
            "real_apply_allowed_after_d143_by_ai": False,
            "auto_apply_allowed_after_d143_by_ai": False,
            "route_insert_allowed_after_d143_by_ai": False,
            "protected_core_mutation_allowed_after_d143_by_ai": False,
            "network_allowed_after_d143_by_ai": False,
            "secret_read_allowed_after_d143_by_ai": False,
            "shell_allowed_after_d143_by_ai": False,
            "git_action_allowed_after_d143_by_ai": False,
        }
        write(root / "reports/d143_sandbox_candidate_guarded_apply_scope.json", d143)
        write(root / "reports/d143_sandbox_candidate_guarded_apply_plan.json", apply_plan)
        write(root / "reports/d143_sandbox_candidate_guarded_apply_receipt.json", apply_receipt)
        write(root / "reports/d143_d144_sandbox_candidate_post_apply_verification_scope.json", d144_scope)
        return td, root

    def test_creates_post_apply_verification_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_post_apply_verification_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_READY")
            self.assertEqual(r["summary"]["post_apply_verification_status"], "SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION")
            self.assertEqual(r["summary"]["approval_scope"], "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted"])
            self.assertEqual(r["d145_scope"]["allowed_next_gate"], "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE")
            self.assertTrue((root / "reports/d144_sandbox_candidate_post_apply_verification_scope.json").exists())
            self.assertTrue((root / "reports/d144_sandbox_candidate_post_apply_verification_report.json").exists())
            self.assertTrue((root / "reports/d144_sandbox_candidate_apply_integrity_receipt.json").exists())
            self.assertTrue((root / "reports/d144_d145_sandbox_candidate_final_audit_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d143(self):
        td, root = self.root()
        try:
            (root / "reports/d143_sandbox_candidate_guarded_apply_scope.json").unlink()
            r = create_sandbox_candidate_post_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_apply_plan_says_core_mutated(self):
        td, root = self.root()
        try:
            p = root / "reports/d143_sandbox_candidate_guarded_apply_plan.json"
            data = json.loads(p.read_text())
            data["protected_core_mutated"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_sandbox_apply_result_says_real_apply(self):
        td, root = self.root()
        try:
            p = root / "runtime_experimental/ai_sandbox_work/d126-test/sandbox_apply_result.json"
            data = json.loads(p.read_text())
            data["real_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d144_scope_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d143_d144_sandbox_candidate_post_apply_verification_scope.json"
            data = json.loads(p.read_text())
            data["route_insert_allowed_after_d143_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_apply_verification_scope(root)
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

print("D144 SANDBOX CANDIDATE POST APPLY VERIFICATION SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_post_apply_verification_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d144_sandbox_candidate_post_apply_verification_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_post_apply_verification_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d144_sandbox_candidate_post_apply_verification_scope", "-v"], check=True)

print("\n== run D144 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_post_apply_verification_scope import create_sandbox_candidate_post_apply_verification_scope\n"
    "r=create_sandbox_candidate_post_apply_verification_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d144_sandbox_candidate_post_apply_verification_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_post_apply_verification_scope.py",
    "tests/test_d144_sandbox_candidate_post_apply_verification_scope.py",
    "reports/d144_sandbox_candidate_post_apply_verification_scope.json",
    "reports/d144_sandbox_candidate_post_apply_verification_report.json",
    "reports/d144_sandbox_candidate_apply_integrity_receipt.json",
    "reports/d144_d145_sandbox_candidate_final_audit_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D144 sandbox candidate post apply verification scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D144 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD144 SANDBOX CANDIDATE POST APPLY VERIFICATION SCOPE BOOT DONE")
