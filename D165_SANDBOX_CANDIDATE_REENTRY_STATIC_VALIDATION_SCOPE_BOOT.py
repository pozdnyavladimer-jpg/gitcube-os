#!/usr/bin/env python3
# D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_BOOT.py
#
# D165 consumes D164 sandbox-candidate reentry materialization artifacts and creates:
# - runtime_experimental/sandbox_candidate_reentry_static_validation_scope.py
# - tests/test_d165_sandbox_candidate_reentry_static_validation_scope.py
# - reports/d165_sandbox_candidate_reentry_static_validation_scope.json
# - reports/d165_sandbox_candidate_reentry_static_validation_report.json
# - reports/d165_sandbox_candidate_reentry_static_validation_receipt.json
# - reports/d165_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json
#
# D165 performs static validation only:
# it reads candidate_manifest.json / candidate_payload.json / candidate_summary.md,
# validates the no-op placeholder contract, and opens D166 preflight.
#
# It does NOT execute candidate code and does NOT apply anything.
#
# No real provider call, no network, no secret read, no shell,
# no route insert, no protected core mutation by AI, no git action by AI.
#
# Opens D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE only.

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

D164_REPORT = "reports/d164_sandbox_candidate_reentry_materialization_scope.json"
D164_MANIFEST = "reports/d164_sandbox_candidate_reentry_materialization_manifest.json"
D164_PREFLIGHT = "reports/d164_sandbox_candidate_reentry_materialization_preflight.json"
D164_D165_SCOPE = "reports/d164_d165_sandbox_candidate_reentry_static_validation_scope.json"

OUT = "reports/d165_sandbox_candidate_reentry_static_validation_scope.json"
STATIC_REPORT_OUT = "reports/d165_sandbox_candidate_reentry_static_validation_report.json"
STATIC_RECEIPT_OUT = "reports/d165_sandbox_candidate_reentry_static_validation_receipt.json"
D166_SCOPE_OUT = "reports/d165_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json"

REQ_D164_DECISION = "SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_READY"
REQ_D165_GATE = "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE"
REQ_D166_GATE = "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE"

DANGEROUS_AFTER_D164_FALSE = [
    "real_apply_allowed_after_d164_by_ai",
    "route_insert_allowed_after_d164_by_ai",
    "protected_core_mutation_allowed_after_d164_by_ai",
    "network_allowed_after_d164_by_ai",
    "secret_read_allowed_after_d164_by_ai",
    "shell_allowed_after_d164_by_ai",
    "git_action_allowed_after_d164_by_ai",
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


def validate_d164(d164, manifest, preflight, d165_scope, root):
    errors = []

    if not d164:
        return ["missing D164 sandbox candidate reentry materialization scope report"]

    if d164.get("ok") is not True:
        errors.append("D164 ok must be true")
    if d164.get("decision") != REQ_D164_DECISION:
        errors.append("D164 decision must be SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_READY")

    summary = d164.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D164_PLUS",
        "materialization_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_READY_FOR_STATIC_VALIDATION",
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
        "approval_scope": "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_ONLY",
        "next_step": REQ_D165_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D164 summary.{k} must be {v}")

    guard = normalize_guard_flags(d164.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D164 guardrails"))
    require_true(guard, [
        "sandbox_candidate_reentry_materialization_scope_only",
        "sandbox_candidate_reentry_materialization_manifest_only",
        "sandbox_candidate_reentry_materialization_preflight_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "human_review_required",
        "candidate_files_created",
        "candidate_payload_written",
        "candidate_manifest_written",
        "candidate_summary_written",
        "candidate_ready_for_static_validation",
        "approval_for_d165_sandbox_candidate_reentry_static_validation_scope_only",
    ], "D164 guardrails", errors)
    require_false(guard, [
        "candidate_execution_requested",
        "candidate_executed",
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "apply_requested",
        "apply_executed",
        *DANGEROUS_AFTER_D164_FALSE,
    ], "D164 guardrails", errors)

    if not manifest:
        errors.append("missing D164 materialization manifest")
    else:
        if manifest.get("ok") is not True:
            errors.append("D164 materialization manifest ok must be true")
        if manifest.get("materialization_status") != "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION":
            errors.append("D164 materialization manifest status mismatch")
        require_true(manifest, [
            "canonical_guard_schema_applied",
            "sandbox_candidate_reentry_materialization_scope_only",
            "candidate_files_created",
            "candidate_payload_written",
            "candidate_manifest_written",
            "candidate_summary_written",
            "candidate_ready_for_static_validation",
        ], "D164 manifest", errors)
        require_false(manifest, [
            "real_provider_call_performed",
            "provider_response_ingested",
            "provider_response_captured",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
        ], "D164 manifest", errors)
        errors.extend(validate_no_ai_execution(manifest, prefix="D164 manifest"))

    if not preflight:
        errors.append("missing D164 materialization preflight")
    else:
        if preflight.get("ok") is not True:
            errors.append("D164 preflight ok must be true")
        if preflight.get("preflight_status") != "MATERIALIZATION_PREFLIGHT_READY_FOR_STATIC_VALIDATION_NO_EXECUTION":
            errors.append("D164 preflight status mismatch")
        require_true(preflight, [
            "candidate_manifest_exists",
            "candidate_payload_exists",
            "candidate_summary_exists",
            "candidate_files_created",
            "candidate_payload_written",
            "candidate_manifest_written",
            "candidate_summary_written",
            "candidate_ready_for_static_validation",
        ], "D164 preflight", errors)
        require_false(preflight, [
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
        ], "D164 preflight", errors)
        errors.extend(validate_no_ai_execution(preflight, prefix="D164 preflight"))

    if not d165_scope:
        errors.append("missing D164 D165 static validation scope")
    else:
        if d165_scope.get("ok") is not True:
            errors.append("D164 D165 scope ok must be true")
        if d165_scope.get("allowed_next_gate") != REQ_D165_GATE:
            errors.append("D164 D165 scope allowed_next_gate must be D165")
        require_true(d165_scope, [
            "sandbox_candidate_reentry_static_validation_scope_only",
            "candidate_files_required",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ], "D164 D165 scope", errors)
        if d165_scope.get("candidate_execution_allowed") is not False:
            errors.append("D164 D165 scope candidate_execution_allowed must be false")
        require_false(d165_scope, DANGEROUS_AFTER_D164_FALSE, "D164 D165 scope", errors)

    candidate_dir = d164.get("candidate_work_dir") or (manifest or {}).get("candidate_work_dir") or (d165_scope or {}).get("candidate_work_dir")
    if not candidate_dir:
        errors.append("D164 candidate_work_dir missing")
        return errors

    work_dir = root / candidate_dir
    manifest_path = work_dir / "candidate_manifest.json"
    payload_path = work_dir / "candidate_payload.json"
    summary_path = work_dir / "candidate_summary.md"

    if not manifest_path.exists():
        errors.append("candidate_manifest.json missing")
    if not payload_path.exists():
        errors.append("candidate_payload.json missing")
    if not summary_path.exists():
        errors.append("candidate_summary.md missing")

    if payload_path.exists():
        payload = read_json(payload_path, {}) or {}
        if payload.get("payload_kind") != "NO_OP_REENTRY_PLACEHOLDER_FOR_STATIC_VALIDATION":
            errors.append("candidate payload_kind must be no-op static validation placeholder")
        if payload.get("payload_status") != "MATERIALIZED_IN_SANDBOX_ONLY_NO_EXECUTION":
            errors.append("candidate payload_status must be materialized no execution")
        if payload.get("source_response_mode") != "DRY_CAPTURE_PLACEHOLDER_ONLY":
            errors.append("candidate source_response_mode must be dry placeholder")
        require_false(payload, [
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
        ], "candidate payload", errors)
        errors.extend(validate_no_ai_execution(payload, prefix="candidate payload"))

    if manifest_path.exists():
        cand_manifest = read_json(manifest_path, {}) or {}
        if cand_manifest.get("candidate_status") != "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION":
            errors.append("candidate manifest status mismatch")
        require_true(cand_manifest, [
            "candidate_files_created",
            "candidate_payload_written",
            "candidate_manifest_written",
            "candidate_summary_written",
        ], "candidate manifest", errors)
        require_false(cand_manifest, [
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
        ], "candidate manifest", errors)
        errors.extend(validate_no_ai_execution(cand_manifest, prefix="candidate manifest"))

    return errors


def build_static_report(validation_id, d164, candidate_dir, candidate_payload, candidate_manifest):
    data = {
        "state": "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_REPORT",
        "ok": True,
        "validation_id": validation_id,
        "candidate_id": d164.get("candidate_id"),
        "response_id": d164.get("response_id"),
        "runner_id": d164.get("runner_id"),
        "plan_id": d164.get("plan_id"),
        "review_id": d164.get("review_id"),
        "scope_id": d164.get("scope_id"),
        "intake_id": d164.get("intake_id"),
        "reentry_id": d164.get("reentry_id"),
        "next_cycle_id": d164.get("next_cycle_id"),
        "proposal_id": d164.get("proposal_id"),
        "created_at": now(),
        "static_validation_status": "STATIC_VALIDATION_PASSED_NO_EXECUTION",
        "candidate_work_dir": candidate_dir,
        "candidate_payload_kind": candidate_payload.get("payload_kind"),
        "candidate_manifest_status": candidate_manifest.get("candidate_status"),
        "source_response_mode": candidate_payload.get("source_response_mode"),
        "candidate_files_read": True,
        "candidate_payload_read": True,
        "candidate_manifest_read": True,
        "candidate_summary_read": True,
        "candidate_payload_written": True,
        "candidate_files_created": True,
        "static_checks": [
            "candidate files exist",
            "payload is no-op placeholder",
            "provider response was not ingested",
            "candidate execution is not requested",
            "apply is not requested",
            "no AI external-surface flags are active",
        ],
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
    }
    data.update(no_ai_flags())
    return normalize_guard_flags(data)


def build_static_receipt(validation_id, d164):
    data = {
        "state": "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_RECEIPT",
        "ok": True,
        "validation_id": validation_id,
        "candidate_id": d164.get("candidate_id"),
        "response_id": d164.get("response_id"),
        "created_at": now(),
        "receipt_status": "STATIC_VALIDATION_RECORDED_NO_EXECUTION_NO_APPLY",
        "canonical_guard_schema_applied": True,
        "static_validation_only": True,
        "candidate_files_read": True,
        "candidate_payload_written": True,
        "candidate_files_created": True,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "no_candidate_execution": True,
        "no_apply": True,
        "no_provider_call": True,
        "no_network": True,
        "no_secret_read": True,
        "no_shell": True,
        "no_route_insert": True,
        "no_core_mutation_by_ai": True,
        "no_git_action_by_ai": True,
        "human_review_required": True,
    }
    data.update(no_ai_flags())
    return normalize_guard_flags(data)


def build_d166_scope(validation_id, d164, candidate_dir):
    return {
        "state": "D165_D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE",
        "ok": True,
        "validation_id": validation_id,
        "candidate_id": d164.get("candidate_id"),
        "response_id": d164.get("response_id"),
        "runner_id": d164.get("runner_id"),
        "plan_id": d164.get("plan_id"),
        "review_id": d164.get("review_id"),
        "scope_id": d164.get("scope_id"),
        "intake_id": d164.get("intake_id"),
        "reentry_id": d164.get("reentry_id"),
        "next_cycle_id": d164.get("next_cycle_id"),
        "cycle_closure_id": d164.get("cycle_closure_id"),
        "previous_candidate_id": d164.get("previous_candidate_id"),
        "proposal_id": d164.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D166_GATE,
        "sandbox_candidate_reentry_controlled_execution_preflight_scope_only": True,
        "candidate_work_dir": candidate_dir,
        "candidate_static_validation_required": True,
        "candidate_static_validation_passed": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "candidate_execution_allowed_after_d165": False,
        "d166_allowed_to_create": [
            "sandbox_candidate_reentry_controlled_execution_preflight_scope",
            "sandbox_candidate_reentry_controlled_execution_preflight_report",
            "sandbox_candidate_reentry_execution_authority_guard",
            "d167_sandbox_candidate_reentry_controlled_execution_run_scope",
        ],
        "d166_must_not_execute": [
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
        "real_apply_allowed_after_d165_by_ai": False,
        "route_insert_allowed_after_d165_by_ai": False,
        "protected_core_mutation_allowed_after_d165_by_ai": False,
        "network_allowed_after_d165_by_ai": False,
        "secret_read_allowed_after_d165_by_ai": False,
        "shell_allowed_after_d165_by_ai": False,
        "git_action_allowed_after_d165_by_ai": False,
    }


def create_sandbox_candidate_reentry_static_validation_scope(root="."):
    root = Path(root).resolve()

    d164 = read_json(root / D164_REPORT, {}) or {}
    manifest = read_json(root / D164_MANIFEST, {}) or {}
    preflight = read_json(root / D164_PREFLIGHT, {}) or {}
    d165_scope = read_json(root / D164_D165_SCOPE, {}) or {}

    errors = validate_d164(d164, manifest, preflight, d165_scope, root)

    candidate_dir = d164.get("candidate_work_dir") or manifest.get("candidate_work_dir") or d165_scope.get("candidate_work_dir")
    payload = read_json(root / candidate_dir / "candidate_payload.json", {}) if candidate_dir else {}
    cand_manifest = read_json(root / candidate_dir / "candidate_manifest.json", {}) if candidate_dir else {}

    validation_id = "d165-" + digest({
        "candidate_id": d164.get("candidate_id"),
        "response_id": d164.get("response_id"),
        "runner_id": d164.get("runner_id"),
        "plan_id": d164.get("plan_id"),
        "review_id": d164.get("review_id"),
        "scope_id": d164.get("scope_id"),
        "intake_id": d164.get("intake_id"),
        "reentry_id": d164.get("reentry_id"),
        "proposal_id": d164.get("proposal_id"),
    })

    static_report = build_static_report(validation_id, d164, candidate_dir, payload or {}, cand_manifest or {})
    static_receipt = build_static_receipt(validation_id, d164)
    d166_scope = build_d166_scope(validation_id, d164, candidate_dir)

    for label, item in [("static_report", static_report), ("static_receipt", static_receipt)]:
        errors.extend(validate_no_ai_execution(item, prefix=label))
        require_false(item, [
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
        ], label, errors)

    require_false(d166_scope, [
        "candidate_execution_allowed_after_d165",
        "real_apply_allowed_after_d165_by_ai",
        "route_insert_allowed_after_d165_by_ai",
        "protected_core_mutation_allowed_after_d165_by_ai",
        "network_allowed_after_d165_by_ai",
        "secret_read_allowed_after_d165_by_ai",
        "shell_allowed_after_d165_by_ai",
        "git_action_allowed_after_d165_by_ai",
    ], "d166_scope", errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_BLOCKED"
    result = "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_CREATED" if ok else "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_BLOCKED"

    if ok:
        write_json(root / STATIC_REPORT_OUT, static_report)
        write_json(root / STATIC_RECEIPT_OUT, static_receipt)
        write_json(root / D166_SCOPE_OUT, d166_scope)

    guardrails = normalize_guard_flags({
        "sandbox_candidate_reentry_static_validation_scope_only": True,
        "sandbox_candidate_reentry_static_validation_report_only": True,
        "sandbox_candidate_reentry_static_validation_receipt_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "candidate_files_read": ok,
        "candidate_payload_read": ok,
        "candidate_manifest_read": ok,
        "candidate_summary_read": ok,
        "candidate_payload_written": True if ok else False,
        "candidate_files_created": True if ok else False,
        "candidate_static_validation_passed": ok,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "apply_requested": False,
        "apply_executed": False,
        "approval_for_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope_only": ok,
        "real_apply_allowed_after_d165_by_ai": False,
        "route_insert_allowed_after_d165_by_ai": False,
        "protected_core_mutation_allowed_after_d165_by_ai": False,
        "network_allowed_after_d165_by_ai": False,
        "secret_read_allowed_after_d165_by_ai": False,
        "shell_allowed_after_d165_by_ai": False,
        "git_action_allowed_after_d165_by_ai": False,
        **no_ai_flags(),
    })

    report = {
        "state": "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "validation_id": validation_id,
        "candidate_id": d164.get("candidate_id"),
        "response_id": d164.get("response_id"),
        "runner_id": d164.get("runner_id"),
        "plan_id": d164.get("plan_id"),
        "review_id": d164.get("review_id"),
        "scope_id": d164.get("scope_id"),
        "intake_id": d164.get("intake_id"),
        "reentry_id": d164.get("reentry_id"),
        "next_cycle_id": d164.get("next_cycle_id"),
        "cycle_closure_id": d164.get("cycle_closure_id"),
        "previous_candidate_id": d164.get("previous_candidate_id"),
        "proposal_id": d164.get("proposal_id"),
        "candidate_work_dir": candidate_dir,
        "source_d164_report": D164_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "static_validation_report": static_report if ok else {},
        "static_validation_receipt": static_receipt if ok else {},
        "d166_scope": d166_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "validation_id": validation_id,
            "candidate_id": d164.get("candidate_id"),
            "response_id": d164.get("response_id"),
            "runner_id": d164.get("runner_id"),
            "plan_id": d164.get("plan_id"),
            "review_id": d164.get("review_id"),
            "scope_id": d164.get("scope_id"),
            "intake_id": d164.get("intake_id"),
            "reentry_id": d164.get("reentry_id"),
            "next_cycle_id": d164.get("next_cycle_id"),
            "proposal_id": d164.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D165_PLUS" if ok else "BLOCKED",
            "static_validation_status": "STATIC_VALIDATION_PASSED_NO_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATED_READY_FOR_CONTROLLED_EXECUTION_PREFLIGHT" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D166_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_static_validation_scope_created": ok,
            "static_validation_report_created": ok,
            "static_validation_receipt_created": ok,
            "d166_scope_created": ok,
            "candidate_static_validation_passed": ok,
            "candidate_executed": False,
            "apply_executed": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D166 may create sandbox candidate reentry controlled execution preflight scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_static_validation_scope(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_static_validation_scope import create_sandbox_candidate_reentry_static_validation_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD165SandboxCandidateReentryStaticValidationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

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
        work_dir = Path("runtime_experimental/ai_sandbox_work") / candidate_id
        abs_work = root / work_dir
        abs_work.mkdir(parents=True, exist_ok=True)

        no_ai = {
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

        candidate_payload = {
            "ok": True,
            "candidate_id": candidate_id,
            "payload_kind": "NO_OP_REENTRY_PLACEHOLDER_FOR_STATIC_VALIDATION",
            "payload_status": "MATERIALIZED_IN_SANDBOX_ONLY_NO_EXECUTION",
            "source_response_mode": "DRY_CAPTURE_PLACEHOLDER_ONLY",
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            **no_ai,
        }
        candidate_manifest = {
            "ok": True,
            "candidate_id": candidate_id,
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION",
            "candidate_files_created": True,
            "candidate_payload_written": True,
            "candidate_manifest_written": True,
            "candidate_summary_written": True,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            **no_ai,
        }
        write(abs_work / "candidate_payload.json", candidate_payload)
        write(abs_work / "candidate_manifest.json", candidate_manifest)
        (abs_work / "candidate_summary.md").write_text("D164 placeholder", encoding="utf-8")

        d164 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_READY",
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
            "candidate_work_dir": str(work_dir),
            "guardrails": {
                "sandbox_candidate_reentry_materialization_scope_only": True,
                "sandbox_candidate_reentry_materialization_manifest_only": True,
                "sandbox_candidate_reentry_materialization_preflight_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "candidate_files_created": True,
                "candidate_payload_written": True,
                "candidate_manifest_written": True,
                "candidate_summary_written": True,
                "candidate_ready_for_static_validation": True,
                "candidate_execution_requested": False,
                "candidate_executed": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "approval_for_d165_sandbox_candidate_reentry_static_validation_scope_only": True,
                "real_apply_allowed_after_d164_by_ai": False,
                "route_insert_allowed_after_d164_by_ai": False,
                "protected_core_mutation_allowed_after_d164_by_ai": False,
                "network_allowed_after_d164_by_ai": False,
                "secret_read_allowed_after_d164_by_ai": False,
                "shell_allowed_after_d164_by_ai": False,
                "git_action_allowed_after_d164_by_ai": False,
                **no_ai,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D164_PLUS",
                "materialization_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_READY_FOR_STATIC_VALIDATION",
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
                "approval_scope": "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_ONLY",
                "next_step": "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE",
            },
        }

        mat_manifest = {
            "ok": True,
            "materialization_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION",
            "canonical_guard_schema_applied": True,
            "sandbox_candidate_reentry_materialization_scope_only": True,
            "candidate_files_created": True,
            "candidate_payload_written": True,
            "candidate_manifest_written": True,
            "candidate_summary_written": True,
            "candidate_ready_for_static_validation": True,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "provider_response_captured": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "candidate_work_dir": str(work_dir),
            **no_ai,
        }

        preflight = {
            "ok": True,
            "preflight_status": "MATERIALIZATION_PREFLIGHT_READY_FOR_STATIC_VALIDATION_NO_EXECUTION",
            "candidate_work_dir": str(work_dir),
            "candidate_manifest_exists": True,
            "candidate_payload_exists": True,
            "candidate_summary_exists": True,
            "candidate_files_created": True,
            "candidate_payload_written": True,
            "candidate_manifest_written": True,
            "candidate_summary_written": True,
            "candidate_ready_for_static_validation": True,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            **no_ai,
        }

        d165_scope = {
            "ok": True,
            "allowed_next_gate": "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE",
            "sandbox_candidate_reentry_static_validation_scope_only": True,
            "candidate_files_required": True,
            "candidate_work_dir": str(work_dir),
            "candidate_payload_path": str(work_dir / "candidate_payload.json"),
            "candidate_manifest_path": str(work_dir / "candidate_manifest.json"),
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "candidate_execution_allowed": False,
            "real_apply_allowed_after_d164_by_ai": False,
            "route_insert_allowed_after_d164_by_ai": False,
            "protected_core_mutation_allowed_after_d164_by_ai": False,
            "network_allowed_after_d164_by_ai": False,
            "secret_read_allowed_after_d164_by_ai": False,
            "shell_allowed_after_d164_by_ai": False,
            "git_action_allowed_after_d164_by_ai": False,
        }

        write(root / "reports/d164_sandbox_candidate_reentry_materialization_scope.json", d164)
        write(root / "reports/d164_sandbox_candidate_reentry_materialization_manifest.json", mat_manifest)
        write(root / "reports/d164_sandbox_candidate_reentry_materialization_preflight.json", preflight)
        write(root / "reports/d164_d165_sandbox_candidate_reentry_static_validation_scope.json", d165_scope)
        return td, root

    def test_creates_static_validation_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_static_validation_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_ONLY")
            self.assertEqual(r["d166_scope"]["allowed_next_gate"], "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE")
            self.assertTrue(r["guardrails"]["candidate_static_validation_passed"])
            self.assertFalse(r["guardrails"]["candidate_executed"])
            self.assertFalse(r["guardrails"]["apply_executed"])
            self.assertTrue((root / "reports/d165_sandbox_candidate_reentry_static_validation_scope.json").exists())
            self.assertTrue((root / "reports/d165_sandbox_candidate_reentry_static_validation_report.json").exists())
            self.assertTrue((root / "reports/d165_sandbox_candidate_reentry_static_validation_receipt.json").exists())
            self.assertTrue((root / "reports/d165_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d164(self):
        td, root = self.root()
        try:
            (root / "reports/d164_sandbox_candidate_reentry_materialization_scope.json").unlink()
            r = create_sandbox_candidate_reentry_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_missing_candidate_payload(self):
        td, root = self.root()
        try:
            d164 = json.loads((root / "reports/d164_sandbox_candidate_reentry_materialization_scope.json").read_text())
            (root / d164["candidate_work_dir"] / "candidate_payload.json").unlink()
            r = create_sandbox_candidate_reentry_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_payload_requests_execution(self):
        td, root = self.root()
        try:
            d164 = json.loads((root / "reports/d164_sandbox_candidate_reentry_materialization_scope.json").read_text())
            p = root / d164["candidate_work_dir"] / "candidate_payload.json"
            data = json.loads(p.read_text())
            data["candidate_execution_requested"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d165_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d164_d165_sandbox_candidate_reentry_static_validation_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d164_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_static_validation_scope(root)
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

print("D165 SANDBOX CANDIDATE REENTRY STATIC VALIDATION SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_reentry_static_validation_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d165_sandbox_candidate_reentry_static_validation_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_reentry_static_validation_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d165_sandbox_candidate_reentry_static_validation_scope", "-v"], check=True)

print("\n== run D165 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_reentry_static_validation_scope import create_sandbox_candidate_reentry_static_validation_scope\n"
    "r=create_sandbox_candidate_reentry_static_validation_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d165_sandbox_candidate_reentry_static_validation_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_reentry_static_validation_scope.py",
    "tests/test_d165_sandbox_candidate_reentry_static_validation_scope.py",
    "reports/d165_sandbox_candidate_reentry_static_validation_scope.json",
    "reports/d165_sandbox_candidate_reentry_static_validation_report.json",
    "reports/d165_sandbox_candidate_reentry_static_validation_receipt.json",
    "reports/d165_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json",
]

try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D165 sandbox candidate reentry static validation scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D165 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD165 SANDBOX CANDIDATE REENTRY STATIC VALIDATION SCOPE BOOT DONE")
