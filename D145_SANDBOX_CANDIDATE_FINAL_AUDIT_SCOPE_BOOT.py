#!/usr/bin/env python3
# D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_BOOT.py
#
# D145 consumes D144 post-apply verification artifacts and creates:
# - runtime_experimental/sandbox_candidate_final_audit_scope.py
# - tests/test_d145_sandbox_candidate_final_audit_scope.py
# - reports/d145_sandbox_candidate_final_audit_scope.json
# - reports/d145_sandbox_candidate_final_audit_ledger.json
# - reports/d145_sandbox_candidate_replay_index.json
# - reports/d145_d146_sandbox_candidate_archive_scope.json
#
# FINAL AUDIT SCOPE ONLY:
# creates an audit ledger and replay index for the sandbox candidate chain.
# It does NOT execute candidate again, does NOT perform real/core apply,
# route insert, protected-core mutation, shell, network/provider call,
# secret read, or AI git action.
#
# D145 opens D146 Sandbox Candidate Archive Scope.

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

D144_REPORT = "reports/d144_sandbox_candidate_post_apply_verification_scope.json"
D144_POST_APPLY_REPORT = "reports/d144_sandbox_candidate_post_apply_verification_report.json"
D144_APPLY_INTEGRITY_RECEIPT = "reports/d144_sandbox_candidate_apply_integrity_receipt.json"
D144_D145_SCOPE = "reports/d144_d145_sandbox_candidate_final_audit_scope.json"

OUT = "reports/d145_sandbox_candidate_final_audit_scope.json"
FINAL_AUDIT_LEDGER_OUT = "reports/d145_sandbox_candidate_final_audit_ledger.json"
REPLAY_INDEX_OUT = "reports/d145_sandbox_candidate_replay_index.json"
D146_SCOPE_OUT = "reports/d145_d146_sandbox_candidate_archive_scope.json"

REQ_D144_DECISION = "SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_READY"
REQ_D145_GATE = "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE"
REQ_D146_GATE = "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE"
REQ_D144_APPROVAL_SCOPE = "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_ONLY"

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
    "approved_for_real_apply_by_ai", "route_insert_allowed_by_ai",
    "protected_core_mutation_allowed_by_ai",
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

AUDIT_CHAIN_ARTIFACTS = [
    "reports/d126_sandbox_candidate_scope.json",
    "reports/d127_sandbox_candidate_human_review_scope.json",
    "reports/d128_sandbox_candidate_test_plan_scope.json",
    "reports/d129_sandbox_candidate_dry_test_runner_scope.json",
    "reports/d130_sandbox_candidate_write_window_scope.json",
    "reports/d131_sandbox_candidate_write_once_scope.json",
    "reports/d132_sandbox_candidate_static_validation_scope.json",
    "reports/d133_sandbox_candidate_materialization_scope.json",
    "reports/d134_sandbox_candidate_write_materialization_scope.json",
    "reports/d135_sandbox_candidate_post_write_validation_scope.json",
    "reports/d136_sandbox_candidate_execution_preflight_scope.json",
    "reports/d137_sandbox_candidate_controlled_execution_scope.json",
    "reports/d138_sandbox_candidate_human_execution_intent_scope.json",
    "reports/d139_sandbox_candidate_controlled_execution_run_scope.json",
    "reports/d140_sandbox_candidate_post_execution_verification_scope.json",
    "reports/d141_sandbox_candidate_apply_preflight_scope.json",
    "reports/d142_sandbox_candidate_human_apply_intent_scope.json",
    "reports/d143_sandbox_candidate_guarded_apply_scope.json",
    "reports/d144_sandbox_candidate_post_apply_verification_scope.json",
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


def check_statuses(name, obj, errors):
    if not isinstance(obj, dict):
        return
    for key, value in UNSAFE_STATUS_EXPECTED.items():
        if key in obj and obj.get(key) != value:
            errors.append(f"{name} {key} must be {value}")


def file_digest(path):
    p = Path(path)
    if not p.exists():
        return None
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except Exception:
        return None


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


def validate_d144(root, d144, post_apply_report, integrity_receipt, d145_scope):
    errors = []
    if not d144:
        return ["missing D144 sandbox candidate post apply verification scope report"]

    if d144.get("ok") is not True:
        errors.append("D144 ok must be true")
    if d144.get("decision") != REQ_D144_DECISION:
        errors.append("D144 decision must be SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_READY")

    summary = d144.get("summary", {})
    expected = {
        "post_apply_verification_status": "SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION",
        "sandbox_apply_integrity_status": "SANDBOX_APPLY_EVIDENCE_PRESENT_AND_VALIDATED",
        "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_NOT_CORE_APPLIED",
        "approval_scope": REQ_D144_APPROVAL_SCOPE,
        "next_step": REQ_D145_GATE,
    }
    expected.update(UNSAFE_STATUS_EXPECTED)
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D144 summary.{key} must be {value}")

    guard = d144.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D144 guardrails.{key} must be false")
    for key in [
        "sandbox_candidate_post_apply_verification_scope_only",
        "post_apply_verification_report_only",
        "apply_integrity_receipt_only",
        "approval_for_d145_final_audit_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D144 guardrails.{key} must be true")
    for key in [
        "candidate_executed_now", "approval_for_real_apply_by_ai",
        "approval_for_route_insert_by_ai", "approval_for_protected_core_mutation_by_ai",
        "candidate_execution_allowed_by_ai", "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D144 guardrails.{key} must be false")

    candidate_id = d144.get("candidate_id") or summary.get("candidate_id")
    cdir = validate_candidate_files(root, candidate_id, errors)

    if not post_apply_report:
        errors.append("missing D144 sandbox candidate post apply verification report")
    else:
        if post_apply_report.get("ok") is not True:
            errors.append("D144 post apply report ok must be true")
        if post_apply_report.get("report_mode") != "POST_SANDBOX_APPLY_VERIFICATION_ONLY_NO_CORE_MUTATION":
            errors.append("D144 post apply report mode must be post verification only/no core mutation")
        if post_apply_report.get("post_apply_verification_status") != "SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION":
            errors.append("D144 post apply verification status must be SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION")
        if post_apply_report.get("candidate_status") != "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_NOT_CORE_APPLIED":
            errors.append("D144 post apply report candidate_status must be verified not core applied")
        if post_apply_report.get("human_review_required") is not True:
            errors.append("D144 post apply report must require human review")
        check_false_map("D144 post apply report", post_apply_report, errors)

    if not integrity_receipt:
        errors.append("missing D144 sandbox candidate apply integrity receipt")
    else:
        if integrity_receipt.get("ok") is not True:
            errors.append("D144 apply integrity receipt ok must be true")
        if integrity_receipt.get("receipt_mode") != "SANDBOX_APPLY_INTEGRITY_RECEIPT_NO_CORE_MUTATION":
            errors.append("D144 apply integrity receipt mode must be no core mutation")
        if integrity_receipt.get("sandbox_apply_integrity_status") != "SANDBOX_APPLY_EVIDENCE_PRESENT_AND_VALIDATED":
            errors.append("D144 apply integrity status must be evidence present and validated")
        if integrity_receipt.get("protected_core_status") != "UNTOUCHED_BY_AI":
            errors.append("D144 apply integrity protected_core_status must be UNTOUCHED_BY_AI")
        if integrity_receipt.get("route_insert_status") != "BLOCKED":
            errors.append("D144 apply integrity route_insert_status must be BLOCKED")
        if integrity_receipt.get("candidate_files_all_present") is not True:
            errors.append("D144 apply integrity candidate_files_all_present must be true")
        if integrity_receipt.get("human_review_required") is not True:
            errors.append("D144 apply integrity receipt must require human review")
        check_false_map("D144 apply integrity receipt", integrity_receipt, errors)

    if not d145_scope:
        errors.append("missing D144 D145 final audit scope")
    else:
        if d145_scope.get("ok") is not True:
            errors.append("D144 D145 scope ok must be true")
        if d145_scope.get("allowed_next_gate") != REQ_D145_GATE:
            errors.append("D144 D145 scope allowed_next_gate must be D145")
        if d145_scope.get("sandbox_candidate_final_audit_scope_only") is not True:
            errors.append("D144 D145 scope must be final audit scope only")
        if d145_scope.get("sandbox_apply_verified_after_d144") is not True:
            errors.append("D144 D145 scope sandbox_apply_verified_after_d144 must be true")
        if d145_scope.get("human_review_required") is not True:
            errors.append("D144 D145 scope must require human review")
        for key in [
            "candidate_executed_after_d144_by_ai", "real_apply_allowed_after_d144_by_ai",
            "auto_apply_allowed_after_d144_by_ai", "route_insert_allowed_after_d144_by_ai",
            "protected_core_mutation_allowed_after_d144_by_ai", "network_allowed_after_d144_by_ai",
            "secret_read_allowed_after_d144_by_ai", "shell_allowed_after_d144_by_ai",
            "git_action_allowed_after_d144_by_ai",
        ]:
            if d145_scope.get(key) is not False:
                errors.append(f"D144 D145 scope {key} must be false")

    return errors


def build_final_audit_ledger(root, audit_id, d144, post_apply_report, integrity_receipt):
    summary = d144.get("summary", {})
    candidate_id = d144.get("candidate_id") or summary.get("candidate_id")
    artifact_entries = []
    for item in AUDIT_CHAIN_ARTIFACTS:
        p = root / item
        artifact_entries.append({
            "path": item,
            "present": p.exists(),
            "digest16": file_digest(p),
        })
    return {
        "state": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_LEDGER",
        "ok": True,
        "audit_id": audit_id,
        "verification_id": d144.get("verification_id") or summary.get("verification_id"),
        "apply_id": d144.get("apply_id") or summary.get("apply_id"),
        "run_id": d144.get("run_id") or summary.get("run_id"),
        "candidate_id": candidate_id,
        "proposal_id": d144.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "ledger_mode": "FINAL_AUDIT_LEDGER_ONLY_NO_EXECUTION_NO_CORE_MUTATION",
        "audited_range": "D126_D145_SANDBOX_CANDIDATE_CHAIN",
        "artifact_entries": artifact_entries,
        "artifacts_present_count": sum(1 for x in artifact_entries if x["present"]),
        "artifacts_total": len(artifact_entries),
        "post_apply_verification_status": post_apply_report.get("post_apply_verification_status"),
        "sandbox_apply_integrity_status": integrity_receipt.get("sandbox_apply_integrity_status"),
        "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_FINAL_AUDIT_READY_NOT_CORE_APPLIED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
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


def build_replay_index(root, audit_id, d144):
    summary = d144.get("summary", {})
    candidate_id = d144.get("candidate_id") or summary.get("candidate_id")
    cdir = candidate_dir(root, candidate_id)
    replay_files = []
    for name in REQUIRED_CANDIDATE_FILES:
        p = cdir / name if cdir else None
        replay_files.append({
            "path": str(Path("runtime_experimental/ai_sandbox_work") / candidate_id / name) if candidate_id else name,
            "present": p.exists() if p else False,
            "digest16": file_digest(p) if p else None,
        })
    return {
        "state": "D145_SANDBOX_CANDIDATE_REPLAY_INDEX",
        "ok": True,
        "audit_id": audit_id,
        "verification_id": d144.get("verification_id") or summary.get("verification_id"),
        "apply_id": d144.get("apply_id") or summary.get("apply_id"),
        "run_id": d144.get("run_id") or summary.get("run_id"),
        "candidate_id": candidate_id,
        "proposal_id": d144.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "replay_mode": "REPLAY_INDEX_ONLY_NO_EXECUTION",
        "replay_order": [
            "candidate_manifest.json",
            "candidate_payload.json",
            "sandbox_execution_result.json",
            "sandbox_apply_result.json",
            "d139_execution_scope_report",
            "d140_post_execution_verification_report",
            "d143_guarded_apply_report",
            "d144_post_apply_verification_report",
        ],
        "candidate_replay_files": replay_files,
        "candidate_replay_files_all_present": bool(replay_files) and all(x["present"] for x in replay_files),
        "replay_status": "INDEX_CREATED_NOT_REPLAYED",
        "actual_replay_executed": False,
        "actual_apply_executed": False,
        "real_core_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "network_accessed": False,
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


def build_d146_scope(audit_id, d144):
    summary = d144.get("summary", {})
    return {
        "state": "D145_D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE",
        "ok": True,
        "audit_id": audit_id,
        "verification_id": d144.get("verification_id") or summary.get("verification_id"),
        "apply_id": d144.get("apply_id") or summary.get("apply_id"),
        "run_id": d144.get("run_id") or summary.get("run_id"),
        "candidate_id": d144.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d144.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D146_GATE,
        "d146_allowed_to_create": [
            "sandbox_candidate_archive_scope",
            "sandbox_candidate_archive_manifest",
            "sandbox_candidate_archive_receipt",
            "d147_sandbox_candidate_chain_closeout_scope",
        ],
        "d146_must_not_execute": BLOCKED_ACTIONS,
        "sandbox_candidate_archive_scope_only": True,
        "human_review_required": True,
        "final_audit_created_after_d145": True,
        "candidate_executed_after_d145_by_ai": False,
        "real_apply_allowed_after_d145_by_ai": False,
        "auto_apply_allowed_after_d145_by_ai": False,
        "route_insert_allowed_after_d145_by_ai": False,
        "protected_core_mutation_allowed_after_d145_by_ai": False,
        "network_allowed_after_d145_by_ai": False,
        "secret_read_allowed_after_d145_by_ai": False,
        "shell_allowed_after_d145_by_ai": False,
        "git_action_allowed_after_d145_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_ONLY",
    }


def create_sandbox_candidate_final_audit_scope(root="."):
    root = Path(root).resolve()
    d144 = read_json(root / D144_REPORT, {}) or {}
    post_apply_report = read_json(root / D144_POST_APPLY_REPORT, {}) or {}
    integrity_receipt = read_json(root / D144_APPLY_INTEGRITY_RECEIPT, {}) or {}
    d145_scope_in = read_json(root / D144_D145_SCOPE, {}) or {}

    errors = validate_d144(root, d144, post_apply_report, integrity_receipt, d145_scope_in)
    summary = d144.get("summary", {})
    candidate_id = d144.get("candidate_id") or summary.get("candidate_id")

    audit_id = "d145-" + digest({
        "verification_id": d144.get("verification_id") or summary.get("verification_id"),
        "apply_id": d144.get("apply_id") or summary.get("apply_id"),
        "candidate_id": candidate_id,
        "proposal_id": d144.get("proposal_id") or summary.get("proposal_id"),
    })

    final_audit_ledger = build_final_audit_ledger(root, audit_id, d144, post_apply_report, integrity_receipt)
    replay_index = build_replay_index(root, audit_id, d144)
    d146_scope = build_d146_scope(audit_id, d144)

    for item_name, item in [("final_audit_ledger", final_audit_ledger), ("replay_index", replay_index)]:
        check_false_map(item_name, item, errors)
        check_statuses(item_name, item, errors)
    if replay_index.get("candidate_replay_files_all_present") is not True:
        errors.append("replay_index candidate_replay_files_all_present must be true")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_BLOCKED"
    result = "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_CREATED" if ok else "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_BLOCKED"

    if ok:
        write_json(root / FINAL_AUDIT_LEDGER_OUT, final_audit_ledger)
        write_json(root / REPLAY_INDEX_OUT, replay_index)
        write_json(root / D146_SCOPE_OUT, d146_scope)

    report = {
        "state": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "audit_id": audit_id,
        "verification_id": d144.get("verification_id") or summary.get("verification_id"),
        "apply_id": d144.get("apply_id") or summary.get("apply_id"),
        "run_id": d144.get("run_id") or summary.get("run_id"),
        "candidate_id": candidate_id,
        "proposal_id": d144.get("proposal_id") or summary.get("proposal_id"),
        "source_d144_report": D144_REPORT,
        "sandbox_candidate_final_audit_ledger": final_audit_ledger if ok else {},
        "sandbox_candidate_replay_index": replay_index if ok else {},
        "d146_scope": d146_scope if ok else {},
        "guardrails": {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False, "secret_read": False,
            "shell_from_ai_executed": False, "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False, "route_inserted": False,
            "git_commit_by_ai": False, "git_push_by_ai": False, "rollback_executed": False, "restore_executed": False,
            "sandbox_candidate_final_audit_scope_only": True,
            "final_audit_ledger_only": True,
            "replay_index_only": True,
            "candidate_executed_now": False,
            "approval_for_d146_archive_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "approval_for_route_insert_by_ai": False,
            "approval_for_protected_core_mutation_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "audit_id": audit_id,
            "verification_id": d144.get("verification_id") or summary.get("verification_id"),
            "apply_id": d144.get("apply_id") or summary.get("apply_id"),
            "run_id": d144.get("run_id") or summary.get("run_id"),
            "candidate_id": candidate_id,
            "proposal_id": d144.get("proposal_id") or summary.get("proposal_id"),
            "final_audit_status": "FINAL_AUDIT_LEDGER_CREATED" if ok else "BLOCKED",
            "replay_index_status": "INDEX_CREATED_NOT_REPLAYED" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_FINAL_AUDIT_READY_NOT_CORE_APPLIED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D146_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_final_audit_scope_created": ok,
            "sandbox_candidate_final_audit_ledger_created": ok,
            "sandbox_candidate_replay_index_created": ok,
            "d146_scope_created": ok,
            "final_audit_ready": ok,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "real_core_apply_executed": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D146 may create archive scope only.",
        },
    }
    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_final_audit_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_final_audit_scope import create_sandbox_candidate_final_audit_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD145SandboxCandidateFinalAuditScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        verification_id = "d144-test"
        apply_id = "d143-test"
        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"
        cdir = root / "runtime_experimental" / "ai_sandbox_work" / candidate_id
        cdir.mkdir(parents=True, exist_ok=True)
        for name in ["candidate_manifest.json", "candidate_payload.json", "sandbox_execution_result.json", "sandbox_apply_result.json"]:
            write(cdir / name, {"ok": True, "name": name})
        (cdir / "candidate_summary.md").write_text("# candidate\n", encoding="utf-8")

        false_guard = {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False,
            "secret_read": False, "shell_from_ai_executed": False,
            "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False,
            "route_inserted": False, "git_commit_by_ai": False, "git_push_by_ai": False,
            "rollback_executed": False, "restore_executed": False,
        }
        d144 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_READY",
            "verification_id": verification_id,
            "apply_id": apply_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_post_apply_verification_scope_only": True,
                "post_apply_verification_report_only": True,
                "apply_integrity_receipt_only": True,
                "candidate_executed_now": False,
                "approval_for_d145_final_audit_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "approval_for_route_insert_by_ai": False,
                "approval_for_protected_core_mutation_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "post_apply_verification_status": "SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION",
                "sandbox_apply_integrity_status": "SANDBOX_APPLY_EVIDENCE_PRESENT_AND_VALIDATED",
                "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_NOT_CORE_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_ONLY",
                "next_step": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE",
            },
        }
        post_apply_report = {
            "ok": True,
            "verification_id": verification_id,
            "candidate_id": candidate_id,
            "report_mode": "POST_SANDBOX_APPLY_VERIFICATION_ONLY_NO_CORE_MUTATION",
            "post_apply_verification_status": "SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION",
            "sandbox_apply_result_present": True,
            "sandbox_apply_result_ok": True,
            "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_NOT_CORE_APPLIED",
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
        integrity = {
            "ok": True,
            "verification_id": verification_id,
            "candidate_id": candidate_id,
            "receipt_mode": "SANDBOX_APPLY_INTEGRITY_RECEIPT_NO_CORE_MUTATION",
            "candidate_files_all_present": True,
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
        d145_scope = {
            "ok": True,
            "verification_id": verification_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE",
            "sandbox_candidate_final_audit_scope_only": True,
            "sandbox_apply_verified_after_d144": True,
            "human_review_required": True,
            "candidate_executed_after_d144_by_ai": False,
            "real_apply_allowed_after_d144_by_ai": False,
            "auto_apply_allowed_after_d144_by_ai": False,
            "route_insert_allowed_after_d144_by_ai": False,
            "protected_core_mutation_allowed_after_d144_by_ai": False,
            "network_allowed_after_d144_by_ai": False,
            "secret_read_allowed_after_d144_by_ai": False,
            "shell_allowed_after_d144_by_ai": False,
            "git_action_allowed_after_d144_by_ai": False,
        }
        write(root / "reports/d144_sandbox_candidate_post_apply_verification_scope.json", d144)
        write(root / "reports/d144_sandbox_candidate_post_apply_verification_report.json", post_apply_report)
        write(root / "reports/d144_sandbox_candidate_apply_integrity_receipt.json", integrity)
        write(root / "reports/d144_d145_sandbox_candidate_final_audit_scope.json", d145_scope)
        # Some previous audit files are optional but present entries become richer.
        for i in range(126, 145):
            write(root / f"reports/d{i}_dummy_chain_marker.json", {"ok": True, "d": i})
        return td, root

    def test_creates_final_audit_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_final_audit_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_READY")
            self.assertEqual(r["summary"]["final_audit_status"], "FINAL_AUDIT_LEDGER_CREATED")
            self.assertEqual(r["summary"]["approval_scope"], "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted"])
            self.assertEqual(r["d146_scope"]["allowed_next_gate"], "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE")
            self.assertTrue((root / "reports/d145_sandbox_candidate_final_audit_scope.json").exists())
            self.assertTrue((root / "reports/d145_sandbox_candidate_final_audit_ledger.json").exists())
            self.assertTrue((root / "reports/d145_sandbox_candidate_replay_index.json").exists())
            self.assertTrue((root / "reports/d145_d146_sandbox_candidate_archive_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d144(self):
        td, root = self.root()
        try:
            (root / "reports/d144_sandbox_candidate_post_apply_verification_scope.json").unlink()
            r = create_sandbox_candidate_final_audit_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d144_summary_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d144_sandbox_candidate_post_apply_verification_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["route_insert_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_final_audit_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_post_apply_report_says_core_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d144_sandbox_candidate_post_apply_verification_report.json"
            data = json.loads(p.read_text())
            data["real_core_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_final_audit_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d145_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d144_d145_sandbox_candidate_final_audit_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d144_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_final_audit_scope(root)
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

print("D145 SANDBOX CANDIDATE FINAL AUDIT SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_final_audit_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d145_sandbox_candidate_final_audit_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_final_audit_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d145_sandbox_candidate_final_audit_scope", "-v"], check=True)

print("\n== run D145 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_final_audit_scope import create_sandbox_candidate_final_audit_scope\n"
    "r=create_sandbox_candidate_final_audit_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d145_sandbox_candidate_final_audit_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_final_audit_scope.py",
    "tests/test_d145_sandbox_candidate_final_audit_scope.py",
    "reports/d145_sandbox_candidate_final_audit_scope.json",
    "reports/d145_sandbox_candidate_final_audit_ledger.json",
    "reports/d145_sandbox_candidate_replay_index.json",
    "reports/d145_d146_sandbox_candidate_archive_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D145 sandbox candidate final audit scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D145 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD145 SANDBOX CANDIDATE FINAL AUDIT SCOPE BOOT DONE")
