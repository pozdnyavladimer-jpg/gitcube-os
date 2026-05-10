#!/usr/bin/env python3
# D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_BOOT.py
#
# D143 consumes D142 human-apply-intent artifacts and creates:
# - runtime_experimental/sandbox_candidate_guarded_apply_scope.py
# - tests/test_d143_sandbox_candidate_guarded_apply_scope.py
# - reports/d143_sandbox_candidate_guarded_apply_scope.json
# - reports/d143_sandbox_candidate_guarded_apply_plan.json
# - reports/d143_sandbox_candidate_guarded_apply_receipt.json
# - reports/d143_d144_sandbox_candidate_post_apply_verification_scope.json
# - runtime_experimental/ai_sandbox_work/<candidate_id>/sandbox_apply_result.json
#
# GUARDED APPLY SCOPE:
# D143 records/applies the already-executed candidate ONLY inside sandbox evidence.
# It does NOT mutate protected core, insert routes, call network/providers,
# read secrets, execute shell, re-execute candidate, or perform AI git action.
#
# D143 opens D144 Sandbox Candidate Post Apply Verification Scope.

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

D142_REPORT = "reports/d142_sandbox_candidate_human_apply_intent_scope.json"
D142_INTENT_RECORD = "reports/d142_sandbox_candidate_human_apply_intent_record.json"
D142_AUTHORITY_GUARD = "reports/d142_sandbox_candidate_apply_authority_guard.json"
D142_D143_SCOPE = "reports/d142_d143_sandbox_candidate_guarded_apply_scope.json"

OUT = "reports/d143_sandbox_candidate_guarded_apply_scope.json"
GUARDED_APPLY_PLAN_OUT = "reports/d143_sandbox_candidate_guarded_apply_plan.json"
GUARDED_APPLY_RECEIPT_OUT = "reports/d143_sandbox_candidate_guarded_apply_receipt.json"
D144_SCOPE_OUT = "reports/d143_d144_sandbox_candidate_post_apply_verification_scope.json"

REQ_D142_DECISION = "SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_READY"
REQ_D143_GATE = "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE"
REQ_D144_GATE = "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE"
REQ_D142_APPROVAL_SCOPE = "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_ONLY"

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
    "auto_apply_allowed", "real_apply_allowed_by_ai", "approved_for_real_apply_by_ai",
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

BLOCKED_NON_SANDBOX_ACTIONS = [
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


def validate_d142(root, d142, intent_record, authority_guard, d143_scope):
    errors = []
    if not d142:
        return ["missing D142 sandbox candidate human apply intent scope report"]

    if d142.get("ok") is not True:
        errors.append("D142 ok must be true")
    if d142.get("decision") != REQ_D142_DECISION:
        errors.append("D142 decision must be SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_READY")

    summary = d142.get("summary", {})
    expected = {
        "human_apply_intent_status": "HUMAN_APPLY_INTENT_RECORD_CREATED_NO_APPLY",
        "apply_authority_status": "APPLY_AUTHORITY_GUARD_CREATED_NO_APPLY",
        "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
        "execution_result_status": "PRESENT_AND_VALIDATED",
        "approval_scope": REQ_D142_APPROVAL_SCOPE,
        "next_step": REQ_D143_GATE,
    }
    expected.update(UNSAFE_STATUS_EXPECTED)
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D142 summary.{key} must be {value}")

    guard = d142.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D142 guardrails.{key} must be false")
    for key in [
        "sandbox_candidate_human_apply_intent_scope_only", "human_apply_intent_record_only",
        "apply_authority_guard_only", "approval_for_d143_guarded_apply_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D142 guardrails.{key} must be true")
    for key in [
        "candidate_executed_now", "approval_for_real_apply_now", "approval_for_real_apply_by_ai",
        "approval_for_route_insert_by_ai", "approval_for_protected_core_mutation_by_ai",
        "candidate_execution_allowed_by_ai", "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D142 guardrails.{key} must be false")

    candidate_id = d142.get("candidate_id") or summary.get("candidate_id")
    validate_candidate_files(root, candidate_id, errors)

    if not intent_record:
        errors.append("missing D142 human apply intent record")
    else:
        if intent_record.get("ok") is not True:
            errors.append("D142 human apply intent record ok must be true")
        if intent_record.get("record_mode") != "HUMAN_APPLY_INTENT_RECORD_ONLY_NO_APPLY":
            errors.append("D142 human apply intent record mode must be no-apply")
        if intent_record.get("operator_decision") != "PENDING_HUMAN_APPLY_INTENT_FOR_D143":
            errors.append("D142 human apply intent operator_decision must be pending for D143")
        if intent_record.get("approved_for_d143_guarded_apply_scope_only") is not True:
            errors.append("D142 human apply intent must approve D143 scope only")
        if intent_record.get("human_review_required") is not True:
            errors.append("D142 human apply intent must require human review")
        check_false_map("D142 human apply intent", intent_record, errors)

    if not authority_guard:
        errors.append("missing D142 sandbox candidate apply authority guard")
    else:
        if authority_guard.get("ok") is not True:
            errors.append("D142 apply authority guard ok must be true")
        mode = authority_guard.get("authority_mode") or authority_guard.get("guard_mode")
        if mode != "SANDBOX_GUARDED_APPLY_AUTHORITY_GUARD_ONLY":
            errors.append("D142 apply authority guard mode must be SANDBOX_GUARDED_APPLY_AUTHORITY_GUARD_ONLY")
        if authority_guard.get("guarded_apply_allowed_next_gate_only") is not True:
            errors.append("D142 authority guard must allow guarded apply next gate only")
        if authority_guard.get("guarded_apply_allowed_now") is not False:
            errors.append("D142 authority guard guarded_apply_allowed_now must be false")
        if authority_guard.get("real_apply_allowed_now") is not False:
            errors.append("D142 authority guard real_apply_allowed_now must be false")
        if authority_guard.get("human_review_required") is not True:
            errors.append("D142 authority guard must require human review")
        check_false_map("D142 authority guard", authority_guard, errors)

    if not d143_scope:
        errors.append("missing D142 D143 sandbox candidate guarded apply scope")
    else:
        if d143_scope.get("ok") is not True:
            errors.append("D142 D143 scope ok must be true")
        if d143_scope.get("allowed_next_gate") != REQ_D143_GATE:
            errors.append("D142 D143 scope allowed_next_gate must be D143")
        if d143_scope.get("sandbox_candidate_guarded_apply_scope_only") is not True:
            errors.append("D142 D143 scope must be guarded apply scope only")
        if d143_scope.get("human_review_required") is not True:
            errors.append("D142 D143 scope must require human review")
        if d143_scope.get("candidate_executed_in_sandbox_after_d139") is not True:
            errors.append("D142 D143 scope must confirm D139 sandbox execution")
        if d143_scope.get("guarded_apply_allowed_after_d142_operator_only") is not True:
            errors.append("D142 D143 scope must allow guarded apply operator only")
        for key in [
            "candidate_executed_after_d142_by_ai", "real_apply_allowed_after_d142_by_ai",
            "auto_apply_allowed_after_d142_by_ai", "route_insert_allowed_after_d142_by_ai",
            "protected_core_mutation_allowed_after_d142_by_ai", "network_allowed_after_d142_by_ai",
            "secret_read_allowed_after_d142_by_ai", "shell_allowed_after_d142_by_ai",
            "git_action_allowed_after_d142_by_ai",
        ]:
            if d143_scope.get(key) is not False:
                errors.append(f"D142 D143 scope {key} must be false")

    return errors


def build_guarded_apply_plan(apply_id, d142, cdir):
    summary = d142.get("summary", {})
    files = [str((cdir / name).as_posix()) for name in REQUIRED_CANDIDATE_FILES]
    return {
        "state": "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_PLAN",
        "ok": True,
        "apply_id": apply_id,
        "intent_id": d142.get("intent_id") or summary.get("intent_id"),
        "preflight_id": d142.get("preflight_id") or summary.get("preflight_id"),
        "verification_id": d142.get("verification_id") or summary.get("verification_id"),
        "run_id": d142.get("run_id") or summary.get("run_id"),
        "candidate_id": d142.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d142.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "plan_mode": "SANDBOX_GUARDED_APPLY_PLAN_WITHOUT_CORE_MUTATION",
        "apply_target_scope": "SANDBOX_EVIDENCE_ONLY",
        "candidate_files_reference": files,
        "sandbox_apply_result_path": str((cdir / "sandbox_apply_result.json").as_posix()),
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


def build_sandbox_apply_result(apply_id, d142, cdir):
    summary = d142.get("summary", {})
    manifest = read_json(cdir / "candidate_manifest.json", {}) or {}
    payload = read_json(cdir / "candidate_payload.json", {}) or {}
    execution_result = read_json(cdir / "sandbox_execution_result.json", {}) or {}
    return {
        "state": "D143_SANDBOX_CANDIDATE_SANDBOX_APPLY_RESULT",
        "ok": True,
        "apply_id": apply_id,
        "intent_id": d142.get("intent_id") or summary.get("intent_id"),
        "candidate_id": d142.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d142.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "result_mode": "SANDBOX_APPLY_RESULT_ONLY_NO_CORE_MUTATION",
        "source_manifest_present": bool(manifest),
        "source_payload_present": bool(payload),
        "source_execution_result_present": bool(execution_result),
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
    }


def build_guarded_apply_receipt(apply_id, d142, sandbox_apply_result_path):
    summary = d142.get("summary", {})
    return {
        "state": "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_RECEIPT",
        "ok": True,
        "apply_id": apply_id,
        "intent_id": d142.get("intent_id") or summary.get("intent_id"),
        "preflight_id": d142.get("preflight_id") or summary.get("preflight_id"),
        "verification_id": d142.get("verification_id") or summary.get("verification_id"),
        "run_id": d142.get("run_id") or summary.get("run_id"),
        "candidate_id": d142.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d142.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "receipt_mode": "SANDBOX_GUARDED_APPLY_RECEIPT_NO_CORE_MUTATION",
        "sandbox_apply_result_path": sandbox_apply_result_path,
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


def build_d144_scope(apply_id, d142):
    summary = d142.get("summary", {})
    return {
        "state": "D143_D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE",
        "ok": True,
        "apply_id": apply_id,
        "intent_id": d142.get("intent_id") or summary.get("intent_id"),
        "preflight_id": d142.get("preflight_id") or summary.get("preflight_id"),
        "verification_id": d142.get("verification_id") or summary.get("verification_id"),
        "run_id": d142.get("run_id") or summary.get("run_id"),
        "candidate_id": d142.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d142.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D144_GATE,
        "d144_allowed_to_create": [
            "sandbox_candidate_post_apply_verification_scope",
            "sandbox_candidate_post_apply_verification_report",
            "sandbox_candidate_apply_integrity_receipt",
            "d145_sandbox_candidate_final_audit_scope",
        ],
        "d144_must_not_execute": BLOCKED_NON_SANDBOX_ACTIONS,
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
        "required_phrase_for_later_gate": "APPROVE_D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_ONLY",
    }


def create_sandbox_candidate_guarded_apply_scope(root="."):
    root = Path(root).resolve()
    d142 = read_json(root / D142_REPORT, {}) or {}
    intent_record = read_json(root / D142_INTENT_RECORD, {}) or {}
    authority_guard = read_json(root / D142_AUTHORITY_GUARD, {}) or {}
    d143_scope_in = read_json(root / D142_D143_SCOPE, {}) or {}

    errors = validate_d142(root, d142, intent_record, authority_guard, d143_scope_in)
    summary = d142.get("summary", {})
    candidate_id = d142.get("candidate_id") or summary.get("candidate_id")
    cdir = candidate_dir(root, candidate_id) if candidate_id else None

    apply_id = "d143-" + digest({
        "intent_id": d142.get("intent_id") or summary.get("intent_id"),
        "preflight_id": d142.get("preflight_id") or summary.get("preflight_id"),
        "candidate_id": candidate_id,
        "proposal_id": d142.get("proposal_id") or summary.get("proposal_id"),
    })

    guarded_apply_plan = build_guarded_apply_plan(apply_id, d142, cdir or Path("runtime_experimental/ai_sandbox_work/unknown"))
    sandbox_apply_result = build_sandbox_apply_result(apply_id, d142, cdir or Path("runtime_experimental/ai_sandbox_work/unknown"))
    sandbox_apply_result_path = str(((cdir or Path("runtime_experimental/ai_sandbox_work/unknown")) / "sandbox_apply_result.json").as_posix())
    guarded_apply_receipt = build_guarded_apply_receipt(apply_id, d142, sandbox_apply_result_path)
    d144_scope = build_d144_scope(apply_id, d142)

    for item_name, item in [
        ("guarded_apply_plan", guarded_apply_plan),
        ("sandbox_apply_result", sandbox_apply_result),
        ("guarded_apply_receipt", guarded_apply_receipt),
    ]:
        check_false_map(item_name, item, errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_BLOCKED"
    result = "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_CREATED" if ok else "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_BLOCKED"

    if ok:
        write_json(root / GUARDED_APPLY_PLAN_OUT, guarded_apply_plan)
        write_json(root / GUARDED_APPLY_RECEIPT_OUT, guarded_apply_receipt)
        write_json(root / D144_SCOPE_OUT, d144_scope)
        if cdir:
            write_json(cdir / "sandbox_apply_result.json", sandbox_apply_result)

    report = {
        "state": "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "apply_id": apply_id,
        "intent_id": d142.get("intent_id") or summary.get("intent_id"),
        "preflight_id": d142.get("preflight_id") or summary.get("preflight_id"),
        "verification_id": d142.get("verification_id") or summary.get("verification_id"),
        "run_id": d142.get("run_id") or summary.get("run_id"),
        "candidate_id": candidate_id,
        "proposal_id": d142.get("proposal_id") or summary.get("proposal_id"),
        "source_d142_report": D142_REPORT,
        "sandbox_candidate_guarded_apply_plan": guarded_apply_plan if ok else {},
        "sandbox_candidate_guarded_apply_receipt": guarded_apply_receipt if ok else {},
        "d144_scope": d144_scope if ok else {},
        "guardrails": {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False, "secret_read": False,
            "shell_from_ai_executed": False, "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False, "route_inserted": False,
            "git_commit_by_ai": False, "git_push_by_ai": False, "rollback_executed": False, "restore_executed": False,
            "sandbox_candidate_guarded_apply_scope_only": True,
            "guarded_apply_plan_only": True,
            "guarded_apply_receipt_only": True,
            "sandbox_apply_result_written": ok,
            "candidate_executed_now": False,
            "approval_for_d144_post_apply_verification_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "approval_for_route_insert_by_ai": False,
            "approval_for_protected_core_mutation_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "apply_id": apply_id,
            "intent_id": d142.get("intent_id") or summary.get("intent_id"),
            "preflight_id": d142.get("preflight_id") or summary.get("preflight_id"),
            "verification_id": d142.get("verification_id") or summary.get("verification_id"),
            "run_id": d142.get("run_id") or summary.get("run_id"),
            "candidate_id": candidate_id,
            "proposal_id": d142.get("proposal_id") or summary.get("proposal_id"),
            "guarded_apply_status": "SANDBOX_GUARDED_APPLY_RECORDED_NO_CORE_MUTATION" if ok else "BLOCKED",
            "sandbox_apply_result_status": "CREATED" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_RECORDED_NOT_CORE_APPLIED" if ok else "BLOCKED",
            "execution_result_status": "PRESENT_AND_VALIDATED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D144_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_guarded_apply_scope_created": ok,
            "sandbox_candidate_guarded_apply_plan_created": ok,
            "sandbox_candidate_guarded_apply_receipt_created": ok,
            "sandbox_apply_result_created": ok,
            "d144_scope_created": ok,
            "candidate_executed_in_sandbox": ok,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "real_core_apply_executed": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D144 may create post-apply verification scope only.",
        },
    }
    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_guarded_apply_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_guarded_apply_scope import create_sandbox_candidate_guarded_apply_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD143SandboxCandidateGuardedApplyScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        intent_id = "d142-test"
        preflight_id = "d141-test"
        verification_id = "d140-test"
        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"
        cdir = root / "runtime_experimental" / "ai_sandbox_work" / candidate_id
        cdir.mkdir(parents=True, exist_ok=True)
        write(cdir / "candidate_manifest.json", {"ok": True, "candidate_id": candidate_id})
        write(cdir / "candidate_payload.json", {"ok": True, "candidate_id": candidate_id})
        (cdir / "candidate_summary.md").write_text("# candidate summary\n", encoding="utf-8")
        write(cdir / "sandbox_execution_result.json", {"ok": True, "candidate_id": candidate_id})

        false_guard = {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False, "secret_read": False,
            "shell_from_ai_executed": False, "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False, "route_inserted": False,
            "git_commit_by_ai": False, "git_push_by_ai": False, "rollback_executed": False, "restore_executed": False,
        }
        d142 = {
            "ok": True, "decision": "SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_READY",
            "intent_id": intent_id, "preflight_id": preflight_id, "verification_id": verification_id,
            "run_id": run_id, "candidate_id": candidate_id, "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_human_apply_intent_scope_only": True,
                "human_apply_intent_record_only": True,
                "apply_authority_guard_only": True,
                "candidate_executed_now": False,
                "approval_for_d143_guarded_apply_scope_only": True,
                "approval_for_real_apply_now": False,
                "approval_for_real_apply_by_ai": False,
                "approval_for_route_insert_by_ai": False,
                "approval_for_protected_core_mutation_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "human_apply_intent_status": "HUMAN_APPLY_INTENT_RECORD_CREATED_NO_APPLY",
                "apply_authority_status": "APPLY_AUTHORITY_GUARD_CREATED_NO_APPLY",
                "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
                "execution_result_status": "PRESENT_AND_VALIDATED",
                "real_provider_status": "NOT_CALLED", "network_status": "NOT_ACCESSED", "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED", "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED", "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_ONLY",
                "next_step": "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE",
            },
        }
        intent_record = {
            "ok": True, "intent_id": intent_id, "candidate_id": candidate_id,
            "record_mode": "HUMAN_APPLY_INTENT_RECORD_ONLY_NO_APPLY",
            "operator_decision": "PENDING_HUMAN_APPLY_INTENT_FOR_D143",
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
        authority_guard = {
            "ok": True, "intent_id": intent_id, "candidate_id": candidate_id,
            "authority_mode": "SANDBOX_GUARDED_APPLY_AUTHORITY_GUARD_ONLY",
            "guard_mode": "SANDBOX_GUARDED_APPLY_AUTHORITY_GUARD_ONLY",
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
        d143_scope = {
            "ok": True, "intent_id": intent_id, "candidate_id": candidate_id,
            "allowed_next_gate": "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE",
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
        }
        write(root / "reports/d142_sandbox_candidate_human_apply_intent_scope.json", d142)
        write(root / "reports/d142_sandbox_candidate_human_apply_intent_record.json", intent_record)
        write(root / "reports/d142_sandbox_candidate_apply_authority_guard.json", authority_guard)
        write(root / "reports/d142_d143_sandbox_candidate_guarded_apply_scope.json", d143_scope)
        return td, root

    def test_creates_guarded_apply_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_guarded_apply_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_READY")
            self.assertEqual(r["summary"]["guarded_apply_status"], "SANDBOX_GUARDED_APPLY_RECORDED_NO_CORE_MUTATION")
            self.assertEqual(r["summary"]["approval_scope"], "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted"])
            self.assertEqual(r["d144_scope"]["allowed_next_gate"], "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE")
            self.assertTrue((root / "reports/d143_sandbox_candidate_guarded_apply_scope.json").exists())
            self.assertTrue((root / "reports/d143_sandbox_candidate_guarded_apply_plan.json").exists())
            self.assertTrue((root / "reports/d143_sandbox_candidate_guarded_apply_receipt.json").exists())
            self.assertTrue((root / "reports/d143_d144_sandbox_candidate_post_apply_verification_scope.json").exists())
            self.assertTrue((root / "runtime_experimental/ai_sandbox_work/d126-test/sandbox_apply_result.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d142(self):
        td, root = self.root()
        try:
            (root / "reports/d142_sandbox_candidate_human_apply_intent_scope.json").unlink()
            r = create_sandbox_candidate_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_intent_record_says_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d142_sandbox_candidate_human_apply_intent_record.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_authority_guard_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d142_sandbox_candidate_apply_authority_guard.json"
            data = json.loads(p.read_text())
            data["network_accessed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d143_scope_allows_core_mutation(self):
        td, root = self.root()
        try:
            p = root / "reports/d142_d143_sandbox_candidate_guarded_apply_scope.json"
            data = json.loads(p.read_text())
            data["protected_core_mutation_allowed_after_d142_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_apply_scope(root)
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

print("D143 SANDBOX CANDIDATE GUARDED APPLY SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_guarded_apply_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d143_sandbox_candidate_guarded_apply_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_guarded_apply_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d143_sandbox_candidate_guarded_apply_scope", "-v"], check=True)

print("\n== run D143 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_guarded_apply_scope import create_sandbox_candidate_guarded_apply_scope\n"
    "r=create_sandbox_candidate_guarded_apply_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d143_sandbox_candidate_guarded_apply_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_guarded_apply_scope.py",
    "tests/test_d143_sandbox_candidate_guarded_apply_scope.py",
    "reports/d143_sandbox_candidate_guarded_apply_scope.json",
    "reports/d143_sandbox_candidate_guarded_apply_plan.json",
    "reports/d143_sandbox_candidate_guarded_apply_receipt.json",
    "reports/d143_d144_sandbox_candidate_post_apply_verification_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)
for item in Path("runtime_experimental/ai_sandbox_work").glob("*/sandbox_apply_result.json"):
    sh(["git", "add", "-f", str(item)], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D143 sandbox candidate guarded apply scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D143 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD143 SANDBOX CANDIDATE GUARDED APPLY SCOPE BOOT DONE")
