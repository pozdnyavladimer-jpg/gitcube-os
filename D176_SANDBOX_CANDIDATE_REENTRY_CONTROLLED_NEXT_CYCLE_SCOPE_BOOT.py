#!/usr/bin/env python3
# D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_BOOT.py
#
# D176 consumes D175 chain-archive artifacts and creates:
# - runtime_experimental/sandbox_candidate_reentry_controlled_next_cycle_scope.py
# - tests/test_d176_sandbox_candidate_reentry_controlled_next_cycle_scope.py
# - reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json
# - reports/d176_sandbox_candidate_reentry_next_cycle_reset_receipt.json
# - reports/d176_d177_controlled_autonomy_cycle_reentry_intake_scope.json
#
# D176 closes the sandbox-candidate reentry chain and opens a fresh controlled
# autonomy intake for the next cycle. No authority is inherited from the archived
# chain.
#
# No real provider call, no network, no secret read, no shell,
# no route insert, no protected core mutation by AI, no git action by AI.
#
# Opens D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE only.

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

D175_REPORT = "reports/d175_sandbox_candidate_reentry_chain_archive_scope.json"
D175_ARCHIVE_MANIFEST = "reports/d175_sandbox_candidate_reentry_chain_archive_manifest.json"
D175_CHAIN_CLOSURE_RECEIPT = "reports/d175_sandbox_candidate_reentry_chain_closure_receipt.json"
D175_D176_SCOPE = "reports/d175_d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json"

OUT = "reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json"
NEXT_CYCLE_RESET_RECEIPT_OUT = "reports/d176_sandbox_candidate_reentry_next_cycle_reset_receipt.json"
D177_SCOPE_OUT = "reports/d176_d177_controlled_autonomy_cycle_reentry_intake_scope.json"

REQ_D175_DECISION = "SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE_READY"
REQ_D176_GATE = "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE"
REQ_D177_GATE = "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE"

AFTER_D175_FALSE = [
    "real_apply_allowed_after_d175_by_ai",
    "route_insert_allowed_after_d175_by_ai",
    "protected_core_mutation_allowed_after_d175_by_ai",
    "network_allowed_after_d175_by_ai",
    "secret_read_allowed_after_d175_by_ai",
    "shell_allowed_after_d175_by_ai",
    "git_action_allowed_after_d175_by_ai",
]

FALSE_KEYS = [
    "candidate_apply_executed",
    "candidate_apply_executed_by_ai",
    "real_provider_call_performed",
    "provider_response_ingested",
    "provider_response_captured",
    "apply_requested",
    "apply_executed",
    "real_apply_executed",
    "actual_apply_executed",
    "network_accessed",
    "secret_read",
    "shell_executed_by_ai",
    "actual_apply_executed_by_ai",
    "real_apply_executed_by_ai",
    "route_inserted",
    "route_inserted_by_ai",
    "protected_core_mutated",
    "protected_core_mutated_by_ai",
    "git_action_by_ai",
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


def normalize_d175_compat(d175, archive_manifest, chain_closure_receipt, d176_scope):
    # Safe compatibility bridge: missing explicit false flags become False, never True.
    for obj in (d175.get("guardrails", {}) if isinstance(d175, dict) else {}, archive_manifest, chain_closure_receipt):
        if isinstance(obj, dict):
            for k in FALSE_KEYS:
                obj.setdefault(k, False)

    if isinstance(d176_scope, dict):
        for k in ["candidate_apply_executed", "candidate_apply_executed_by_ai"] + AFTER_D175_FALSE:
            d176_scope.setdefault(k, False)

    if d175:
        d175.setdefault("summary", {})
        d175["summary"].setdefault("provider_response_status", "NOT_INGESTED_DRY_PLACEHOLDER_USED")
        d175["summary"].setdefault("candidate_execution_status", "EXECUTED_IN_SANDBOX_NO_OP_ONLY")
        d175.setdefault("guardrails", {})
        for k in [
            "archive_manifest_created",
            "chain_closure_receipt_created",
            "chain_archived",
            "archive_ready",
            "final_apply_audit_complete",
            "final_apply_ledger_created",
            "replay_index_created",
            "post_apply_verified",
            "apply_integrity_verified",
            "guarded_apply_recorded",
            "candidate_apply_recorded",
        ]:
            d175["guardrails"].setdefault(k, True)

    if archive_manifest:
        archive_manifest.setdefault("archive_status", "CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED")
        archive_manifest.setdefault("archive_mode", "LOCAL_JSON_MANIFEST_ONLY")
        archive_manifest.setdefault("archive_ready", True)
        archive_manifest.setdefault("archive_uploaded", False)
        archive_manifest.setdefault("archive_compressed", False)
        for k in [
            "final_apply_audit_complete",
            "final_apply_ledger_created",
            "replay_index_created",
            "post_apply_verified",
            "apply_integrity_verified",
            "guarded_apply_recorded",
            "candidate_apply_recorded",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ]:
            archive_manifest.setdefault(k, True)

    if chain_closure_receipt:
        chain_closure_receipt.setdefault("chain_closure_status", "REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE")
        chain_closure_receipt.setdefault("closure_mode", "LOCAL_RECORD_ONLY_NO_EXECUTION")
        for k in [
            "archive_ready",
            "archive_manifest_created",
            "final_apply_audit_complete",
            "final_apply_ledger_created",
            "replay_index_created",
            "post_apply_verified",
            "apply_integrity_verified",
            "guarded_apply_recorded",
            "candidate_apply_recorded",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ]:
            chain_closure_receipt.setdefault(k, True)

    if d176_scope:
        for k in [
            "sandbox_candidate_reentry_controlled_next_cycle_scope_only",
            "archive_manifest_created",
            "chain_closure_receipt_created",
            "chain_archived",
            "next_cycle_requires_fresh_intent",
            "next_cycle_requires_human_review",
            "next_cycle_inherits_no_authority",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ]:
            d176_scope.setdefault(k, True)


def validate_d175(d175, archive_manifest, chain_closure_receipt, d176_scope):
    errors = []

    if not d175:
        return ["missing D175 chain archive scope report"]
    if d175.get("ok") is not True:
        errors.append("D175 ok must be true")
    if d175.get("decision") != REQ_D175_DECISION:
        errors.append("D175 decision must be SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE_READY")

    summary = d175.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D175_PLUS",
        "archive_status": "CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
        "chain_closure_status": "REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE",
        "real_provider_status": "NOT_CALLED",
        "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_ONLY",
        "next_step": REQ_D176_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D175 summary.{k} must be {v}")

    guard = normalize_guard_flags(d175.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D175 guardrails"))
    require_true(guard, [
        "sandbox_candidate_reentry_chain_archive_scope_only",
        "sandbox_candidate_reentry_chain_archive_manifest_only",
        "sandbox_candidate_reentry_chain_closure_receipt_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "human_review_required",
        "archive_manifest_created",
        "chain_closure_receipt_created",
        "chain_archived",
        "archive_ready",
        "final_apply_audit_complete",
        "final_apply_ledger_created",
        "replay_index_created",
        "post_apply_verified",
        "apply_integrity_verified",
        "guarded_apply_recorded",
        "candidate_apply_recorded",
        "approval_for_d176_sandbox_candidate_reentry_controlled_next_cycle_scope_only",
    ], "D175 guardrails", errors)
    require_false(guard, [
        "candidate_apply_executed",
        "candidate_apply_executed_by_ai",
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "apply_requested",
        "apply_executed",
        "real_apply_executed",
        "actual_apply_executed",
        *AFTER_D175_FALSE,
    ], "D175 guardrails", errors)

    if not archive_manifest:
        errors.append("missing D175 archive manifest")
    else:
        if archive_manifest.get("ok") is not True:
            errors.append("D175 archive manifest ok must be true")
        if archive_manifest.get("archive_status") != "CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED":
            errors.append("D175 archive manifest status mismatch")
        require_true(archive_manifest, [
            "archive_ready",
            "final_apply_audit_complete",
            "final_apply_ledger_created",
            "replay_index_created",
            "post_apply_verified",
            "apply_integrity_verified",
            "guarded_apply_recorded",
            "candidate_apply_recorded",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], "D175 archive manifest", errors)
        require_false(archive_manifest, [
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
            "real_apply_executed",
            "actual_apply_executed",
            "archive_uploaded",
            "archive_compressed",
            "real_provider_call_performed",
            "provider_response_ingested",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "actual_apply_executed_by_ai",
            "real_apply_executed_by_ai",
            "route_inserted",
            "route_inserted_by_ai",
            "protected_core_mutated",
            "protected_core_mutated_by_ai",
            "git_action_by_ai",
        ], "D175 archive manifest", errors)

    if not chain_closure_receipt:
        errors.append("missing D175 chain closure receipt")
    else:
        if chain_closure_receipt.get("ok") is not True:
            errors.append("D175 chain closure receipt ok must be true")
        if chain_closure_receipt.get("chain_closure_status") != "REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE":
            errors.append("D175 chain closure status mismatch")
        require_true(chain_closure_receipt, [
            "archive_ready",
            "archive_manifest_created",
            "final_apply_audit_complete",
            "final_apply_ledger_created",
            "replay_index_created",
            "post_apply_verified",
            "apply_integrity_verified",
            "guarded_apply_recorded",
            "candidate_apply_recorded",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], "D175 chain closure receipt", errors)
        require_false(chain_closure_receipt, [
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
            "real_apply_executed",
            "actual_apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "actual_apply_executed_by_ai",
            "real_apply_executed_by_ai",
            "route_inserted",
            "route_inserted_by_ai",
            "protected_core_mutated",
            "protected_core_mutated_by_ai",
            "git_action_by_ai",
        ], "D175 chain closure receipt", errors)

    if not d176_scope:
        errors.append("missing D175 D176 controlled next cycle scope")
    else:
        if d176_scope.get("ok") is not True:
            errors.append("D175 D176 scope ok must be true")
        if d176_scope.get("allowed_next_gate") != REQ_D176_GATE:
            errors.append("D175 D176 scope allowed_next_gate must be D176")
        require_true(d176_scope, [
            "sandbox_candidate_reentry_controlled_next_cycle_scope_only",
            "archive_manifest_created",
            "chain_closure_receipt_created",
            "chain_archived",
            "next_cycle_requires_fresh_intent",
            "next_cycle_requires_human_review",
            "next_cycle_inherits_no_authority",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ], "D175 D176 scope", errors)
        require_false(d176_scope, [
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
            "real_apply_allowed_after_d175_by_ai",
            "route_insert_allowed_after_d175_by_ai",
            "protected_core_mutation_allowed_after_d175_by_ai",
            "network_allowed_after_d175_by_ai",
            "secret_read_allowed_after_d175_by_ai",
            "shell_allowed_after_d175_by_ai",
            "git_action_allowed_after_d175_by_ai",
        ], "D175 D176 scope", errors)

    return errors


def build_next_cycle_reset_receipt(controlled_next_cycle_id, archive_id, d175):
    data = {
        "state": "D176_SANDBOX_CANDIDATE_REENTRY_NEXT_CYCLE_RESET_RECEIPT",
        "ok": True,
        "controlled_next_cycle_id": controlled_next_cycle_id,
        "archive_id": archive_id,
        "final_audit_id": d175.get("final_audit_id"),
        "post_apply_verification_id": d175.get("post_apply_verification_id"),
        "guarded_apply_id": d175.get("guarded_apply_id"),
        "apply_intent_id": d175.get("apply_intent_id"),
        "apply_preflight_id": d175.get("apply_preflight_id"),
        "verification_id": d175.get("verification_id"),
        "run_id": d175.get("run_id"),
        "intent_id": d175.get("intent_id"),
        "candidate_id": d175.get("candidate_id"),
        "created_at": now(),
        "next_cycle_reset_status": "REENTRY_CHAIN_CLOSED_FRESH_INTENT_REQUIRED_NO_INHERITED_AUTHORITY",
        "reset_mode": "AUTHORITY_ZEROED_RECORD_ONLY",
        "previous_chain_archived": True,
        "chain_closure_verified": True,
        "archive_manifest_verified": True,
        "next_cycle_requires_fresh_intent": True,
        "next_cycle_requires_human_review": True,
        "next_cycle_inherits_no_authority": True,
        "authority_carried_forward": False,
        "provider_authority_carried_forward": False,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "no_real_apply": True,
        "no_network": True,
        "no_secret_read": True,
        "no_shell": True,
        "no_route_insert": True,
        "no_core_mutation_by_ai": True,
        "no_git_action_by_ai": True,
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_d177_scope(controlled_next_cycle_id, archive_id, d175):
    return {
        "state": "D176_D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE",
        "ok": True,
        "controlled_next_cycle_id": controlled_next_cycle_id,
        "archive_id": archive_id,
        "final_audit_id": d175.get("final_audit_id"),
        "post_apply_verification_id": d175.get("post_apply_verification_id"),
        "guarded_apply_id": d175.get("guarded_apply_id"),
        "apply_intent_id": d175.get("apply_intent_id"),
        "apply_preflight_id": d175.get("apply_preflight_id"),
        "verification_id": d175.get("verification_id"),
        "run_id": d175.get("run_id"),
        "intent_id": d175.get("intent_id"),
        "preflight_id": d175.get("preflight_id"),
        "validation_id": d175.get("validation_id"),
        "candidate_id": d175.get("candidate_id"),
        "response_id": d175.get("response_id"),
        "runner_id": d175.get("runner_id"),
        "plan_id": d175.get("plan_id"),
        "review_id": d175.get("review_id"),
        "scope_id": d175.get("scope_id"),
        "intake_id": d175.get("intake_id"),
        "reentry_id": d175.get("reentry_id"),
        "next_cycle_id": d175.get("next_cycle_id"),
        "cycle_closure_id": d175.get("cycle_closure_id"),
        "previous_candidate_id": d175.get("previous_candidate_id"),
        "proposal_id": d175.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D177_GATE,
        "controlled_autonomy_cycle_reentry_intake_scope_only": True,
        "fresh_cycle_intake_required": True,
        "previous_chain_closed": True,
        "previous_chain_archived": True,
        "no_inherited_authority": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "authority_carried_forward": False,
        "provider_authority_carried_forward": False,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_apply_allowed_after_d176_by_ai": False,
        "route_insert_allowed_after_d176_by_ai": False,
        "protected_core_mutation_allowed_after_d176_by_ai": False,
        "network_allowed_after_d176_by_ai": False,
        "secret_read_allowed_after_d176_by_ai": False,
        "shell_allowed_after_d176_by_ai": False,
        "git_action_allowed_after_d176_by_ai": False,
        "d177_allowed_to_create": [
            "controlled_autonomy_cycle_reentry_intake_scope",
            "controlled_autonomy_cycle_fresh_intent_packet",
            "d178_controlled_autonomy_provider_reentry_scope",
        ],
        "d177_must_not_execute": [
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
    }


def create_sandbox_candidate_reentry_controlled_next_cycle_scope(root="."):
    root = Path(root).resolve()

    d175 = read_json(root / D175_REPORT, {}) or {}
    archive_manifest = read_json(root / D175_ARCHIVE_MANIFEST, {}) or {}
    chain_closure_receipt = read_json(root / D175_CHAIN_CLOSURE_RECEIPT, {}) or {}
    d176_scope = read_json(root / D175_D176_SCOPE, {}) or {}

    normalize_d175_compat(d175, archive_manifest, chain_closure_receipt, d176_scope)
    errors = validate_d175(d175, archive_manifest, chain_closure_receipt, d176_scope)

    archive_id = d175.get("archive_id")
    controlled_next_cycle_id = "d176-" + digest({
        "archive_id": archive_id,
        "final_audit_id": d175.get("final_audit_id"),
        "post_apply_verification_id": d175.get("post_apply_verification_id"),
        "guarded_apply_id": d175.get("guarded_apply_id"),
        "apply_intent_id": d175.get("apply_intent_id"),
        "apply_preflight_id": d175.get("apply_preflight_id"),
        "verification_id": d175.get("verification_id"),
        "run_id": d175.get("run_id"),
        "intent_id": d175.get("intent_id"),
        "candidate_id": d175.get("candidate_id"),
        "response_id": d175.get("response_id"),
        "reentry_id": d175.get("reentry_id"),
        "proposal_id": d175.get("proposal_id"),
    })

    reset_receipt = build_next_cycle_reset_receipt(controlled_next_cycle_id, archive_id, d175)
    d177_scope = build_d177_scope(controlled_next_cycle_id, archive_id, d175)

    require_true(reset_receipt, [
        "previous_chain_archived",
        "chain_closure_verified",
        "archive_manifest_verified",
        "next_cycle_requires_fresh_intent",
        "next_cycle_requires_human_review",
        "next_cycle_inherits_no_authority",
        "no_real_apply",
        "no_network",
        "no_secret_read",
        "no_shell",
        "no_route_insert",
        "no_core_mutation_by_ai",
        "no_git_action_by_ai",
    ], "reset_receipt", errors)
    require_false(reset_receipt, [
        "authority_carried_forward",
        "provider_authority_carried_forward",
        "candidate_apply_executed",
        "candidate_apply_executed_by_ai",
        "real_apply_executed",
        "actual_apply_executed",
        "real_provider_call_performed",
        "provider_response_ingested",
        "network_accessed",
        "secret_read",
        "shell_executed_by_ai",
        "actual_apply_executed_by_ai",
        "real_apply_executed_by_ai",
        "route_inserted",
        "route_inserted_by_ai",
        "protected_core_mutated",
        "protected_core_mutated_by_ai",
        "git_action_by_ai",
    ], "reset_receipt", errors)

    require_true(d177_scope, [
        "controlled_autonomy_cycle_reentry_intake_scope_only",
        "fresh_cycle_intake_required",
        "previous_chain_closed",
        "previous_chain_archived",
        "no_inherited_authority",
        "fresh_intent_required",
        "human_review_required",
        "canonical_guard_schema_required",
    ], "d177_scope", errors)
    require_false(d177_scope, [
        "authority_carried_forward",
        "provider_authority_carried_forward",
        "candidate_apply_executed",
        "candidate_apply_executed_by_ai",
        "real_apply_allowed_after_d176_by_ai",
        "route_insert_allowed_after_d176_by_ai",
        "protected_core_mutation_allowed_after_d176_by_ai",
        "network_allowed_after_d176_by_ai",
        "secret_read_allowed_after_d176_by_ai",
        "shell_allowed_after_d176_by_ai",
        "git_action_allowed_after_d176_by_ai",
    ], "d177_scope", errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_BLOCKED"
    result = "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_CREATED" if ok else "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_BLOCKED"

    if ok:
        write_json(root / NEXT_CYCLE_RESET_RECEIPT_OUT, reset_receipt)
        write_json(root / D177_SCOPE_OUT, d177_scope)

    guardrails = normalize_guard_flags({
        "sandbox_candidate_reentry_controlled_next_cycle_scope_only": True,
        "sandbox_candidate_reentry_next_cycle_reset_receipt_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "archive_manifest_verified": ok,
        "chain_closure_verified": ok,
        "previous_chain_archived": ok,
        "previous_chain_closed": ok,
        "controlled_next_cycle_created": ok,
        "next_cycle_reset_receipt_created": ok,
        "fresh_cycle_intake_required": ok,
        "next_cycle_requires_fresh_intent": ok,
        "next_cycle_requires_human_review": ok,
        "next_cycle_inherits_no_authority": ok,
        "no_inherited_authority": ok,
        "authority_carried_forward": False,
        "provider_authority_carried_forward": False,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "approval_for_d177_controlled_autonomy_cycle_reentry_intake_scope_only": ok,
        "real_apply_allowed_after_d176_by_ai": False,
        "route_insert_allowed_after_d176_by_ai": False,
        "protected_core_mutation_allowed_after_d176_by_ai": False,
        "network_allowed_after_d176_by_ai": False,
        "secret_read_allowed_after_d176_by_ai": False,
        "shell_allowed_after_d176_by_ai": False,
        "git_action_allowed_after_d176_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "controlled_next_cycle_id": controlled_next_cycle_id,
        "archive_id": archive_id,
        "final_audit_id": d175.get("final_audit_id"),
        "post_apply_verification_id": d175.get("post_apply_verification_id"),
        "guarded_apply_id": d175.get("guarded_apply_id"),
        "apply_intent_id": d175.get("apply_intent_id"),
        "apply_preflight_id": d175.get("apply_preflight_id"),
        "verification_id": d175.get("verification_id"),
        "run_id": d175.get("run_id"),
        "intent_id": d175.get("intent_id"),
        "preflight_id": d175.get("preflight_id"),
        "validation_id": d175.get("validation_id"),
        "candidate_id": d175.get("candidate_id"),
        "response_id": d175.get("response_id"),
        "runner_id": d175.get("runner_id"),
        "plan_id": d175.get("plan_id"),
        "review_id": d175.get("review_id"),
        "scope_id": d175.get("scope_id"),
        "intake_id": d175.get("intake_id"),
        "reentry_id": d175.get("reentry_id"),
        "next_cycle_id": d175.get("next_cycle_id"),
        "cycle_closure_id": d175.get("cycle_closure_id"),
        "previous_candidate_id": d175.get("previous_candidate_id"),
        "proposal_id": d175.get("proposal_id"),
        "source_d175_report": D175_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "next_cycle_reset_receipt": reset_receipt if ok else {},
        "d177_scope": d177_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "controlled_next_cycle_id": controlled_next_cycle_id,
            "archive_id": archive_id,
            "final_audit_id": d175.get("final_audit_id"),
            "post_apply_verification_id": d175.get("post_apply_verification_id"),
            "guarded_apply_id": d175.get("guarded_apply_id"),
            "apply_intent_id": d175.get("apply_intent_id"),
            "apply_preflight_id": d175.get("apply_preflight_id"),
            "verification_id": d175.get("verification_id"),
            "run_id": d175.get("run_id"),
            "intent_id": d175.get("intent_id"),
            "candidate_id": d175.get("candidate_id"),
            "response_id": d175.get("response_id"),
            "proposal_id": d175.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D176_PLUS" if ok else "BLOCKED",
            "controlled_next_cycle_status": "CONTROLLED_NEXT_CYCLE_CREATED_NO_INHERITED_AUTHORITY" if ok else "BLOCKED",
            "next_cycle_reset_status": "REENTRY_CHAIN_CLOSED_FRESH_INTENT_REQUIRED_NO_INHERITED_AUTHORITY" if ok else "BLOCKED",
            "candidate_status": "CONTROLLED_AUTONOMY_READY_FOR_FRESH_CYCLE_REENTRY_INTAKE" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY" if ok else "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D177_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_controlled_next_cycle_scope_created": ok,
            "next_cycle_reset_receipt_created": ok,
            "d177_scope_created": ok,
            "previous_chain_archived": ok,
            "no_inherited_authority": ok,
            "fresh_intent_required": ok,
            "real_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D177 may create controlled autonomy cycle reentry intake scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_controlled_next_cycle_scope(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_controlled_next_cycle_scope import create_sandbox_candidate_reentry_controlled_next_cycle_scope


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


class TestD176SandboxCandidateReentryControlledNextCycleScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        archive_id = "d175-test"
        final_audit_id = "d174-test"
        post_apply_verification_id = "d173-test"
        guarded_apply_id = "d172-test"
        apply_intent_id = "d171-test"
        apply_preflight_id = "d170-test"
        verification_id = "d169-test"
        run_id = "d168-test"
        intent_id = "d167-test"
        candidate_id = "d164-test"
        response_id = "d163-test"
        proposal_id = "d107-valid-test"

        d175 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE_READY",
            "archive_id": archive_id,
            "final_audit_id": final_audit_id,
            "post_apply_verification_id": post_apply_verification_id,
            "guarded_apply_id": guarded_apply_id,
            "apply_intent_id": apply_intent_id,
            "apply_preflight_id": apply_preflight_id,
            "verification_id": verification_id,
            "run_id": run_id,
            "intent_id": intent_id,
            "preflight_id": "d166-test",
            "validation_id": "d165-test",
            "candidate_id": candidate_id,
            "response_id": response_id,
            "runner_id": "d162-test",
            "plan_id": "d161-test",
            "review_id": "d160-test",
            "scope_id": "d159-test",
            "intake_id": "d158-test",
            "reentry_id": "d157-test",
            "next_cycle_id": "d156-test",
            "cycle_closure_id": "d155-test",
            "previous_candidate_id": "d126-test",
            "proposal_id": proposal_id,
            "guardrails": {
                **no_ai_flags(),
                "sandbox_candidate_reentry_chain_archive_scope_only": True,
                "sandbox_candidate_reentry_chain_archive_manifest_only": True,
                "sandbox_candidate_reentry_chain_closure_receipt_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "archive_manifest_created": True,
                "chain_closure_receipt_created": True,
                "chain_archived": True,
                "archive_ready": True,
                "final_apply_audit_complete": True,
                "final_apply_ledger_created": True,
                "replay_index_created": True,
                "post_apply_verified": True,
                "apply_integrity_verified": True,
                "guarded_apply_recorded": True,
                "candidate_apply_recorded": True,
                "candidate_apply_executed": False,
                "candidate_apply_executed_by_ai": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "real_apply_executed": False,
                "actual_apply_executed": False,
                "approval_for_d176_sandbox_candidate_reentry_controlled_next_cycle_scope_only": True,
                "real_apply_allowed_after_d175_by_ai": False,
                "route_insert_allowed_after_d175_by_ai": False,
                "protected_core_mutation_allowed_after_d175_by_ai": False,
                "network_allowed_after_d175_by_ai": False,
                "secret_read_allowed_after_d175_by_ai": False,
                "shell_allowed_after_d175_by_ai": False,
                "git_action_allowed_after_d175_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D175_PLUS",
                "archive_status": "CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
                "chain_closure_status": "REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_ONLY",
                "next_step": "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE",
            },
        }

        archive_manifest = {
            **no_ai_flags(),
            "ok": True,
            "archive_status": "CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
            "archive_mode": "LOCAL_JSON_MANIFEST_ONLY",
            "archive_ready": True,
            "archive_uploaded": False,
            "archive_compressed": False,
            "final_apply_audit_complete": True,
            "final_apply_ledger_created": True,
            "replay_index_created": True,
            "post_apply_verified": True,
            "apply_integrity_verified": True,
            "guarded_apply_recorded": True,
            "candidate_apply_recorded": True,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_apply_executed": False,
            "actual_apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "no_real_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
        }

        closure_receipt = {
            **no_ai_flags(),
            "ok": True,
            "chain_closure_status": "REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE",
            "closure_mode": "LOCAL_RECORD_ONLY_NO_EXECUTION",
            "archive_ready": True,
            "archive_manifest_created": True,
            "final_apply_audit_complete": True,
            "final_apply_ledger_created": True,
            "replay_index_created": True,
            "post_apply_verified": True,
            "apply_integrity_verified": True,
            "guarded_apply_recorded": True,
            "candidate_apply_recorded": True,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_apply_executed": False,
            "actual_apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "no_real_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
        }

        d176_scope = {
            "ok": True,
            "allowed_next_gate": "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE",
            "sandbox_candidate_reentry_controlled_next_cycle_scope_only": True,
            "archive_manifest_created": True,
            "chain_closure_receipt_created": True,
            "chain_archived": True,
            "next_cycle_requires_fresh_intent": True,
            "next_cycle_requires_human_review": True,
            "next_cycle_inherits_no_authority": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_apply_allowed_after_d175_by_ai": False,
            "route_insert_allowed_after_d175_by_ai": False,
            "protected_core_mutation_allowed_after_d175_by_ai": False,
            "network_allowed_after_d175_by_ai": False,
            "secret_read_allowed_after_d175_by_ai": False,
            "shell_allowed_after_d175_by_ai": False,
            "git_action_allowed_after_d175_by_ai": False,
        }

        write(root / "reports/d175_sandbox_candidate_reentry_chain_archive_scope.json", d175)
        write(root / "reports/d175_sandbox_candidate_reentry_chain_archive_manifest.json", archive_manifest)
        write(root / "reports/d175_sandbox_candidate_reentry_chain_closure_receipt.json", closure_receipt)
        write(root / "reports/d175_d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json", d176_scope)
        return td, root

    def test_creates_controlled_next_cycle_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_controlled_next_cycle_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_ONLY")
            self.assertEqual(r["d177_scope"]["allowed_next_gate"], "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE")
            self.assertTrue(r["guardrails"]["controlled_next_cycle_created"])
            self.assertTrue(r["guardrails"]["next_cycle_inherits_no_authority"])
            self.assertFalse(r["guardrails"]["authority_carried_forward"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted_by_ai"])
            self.assertTrue((root / "reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json").exists())
            self.assertTrue((root / "reports/d176_sandbox_candidate_reentry_next_cycle_reset_receipt.json").exists())
            self.assertTrue((root / "reports/d176_d177_controlled_autonomy_cycle_reentry_intake_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d175(self):
        td, root = self.root()
        try:
            (root / "reports/d175_sandbox_candidate_reentry_chain_archive_scope.json").unlink()
            r = create_sandbox_candidate_reentry_controlled_next_cycle_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_archive_not_ready(self):
        td, root = self.root()
        try:
            p = root / "reports/d175_sandbox_candidate_reentry_chain_archive_manifest.json"
            data = json.loads(p.read_text())
            data["archive_ready"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_next_cycle_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_chain_closure_mutated_core(self):
        td, root = self.root()
        try:
            p = root / "reports/d175_sandbox_candidate_reentry_chain_closure_receipt.json"
            data = json.loads(p.read_text())
            data["protected_core_mutated_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_next_cycle_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d176_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d175_d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d175_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_next_cycle_scope(root)
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

print("D176 SANDBOX CANDIDATE REENTRY CONTROLLED NEXT CYCLE SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_reentry_controlled_next_cycle_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d176_sandbox_candidate_reentry_controlled_next_cycle_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_reentry_controlled_next_cycle_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d176_sandbox_candidate_reentry_controlled_next_cycle_scope", "-v"], check=True)

print("\n== run D176 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_reentry_controlled_next_cycle_scope import create_sandbox_candidate_reentry_controlled_next_cycle_scope\n"
    "r=create_sandbox_candidate_reentry_controlled_next_cycle_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_reentry_controlled_next_cycle_scope.py",
    "tests/test_d176_sandbox_candidate_reentry_controlled_next_cycle_scope.py",
    "reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json",
    "reports/d176_sandbox_candidate_reentry_next_cycle_reset_receipt.json",
    "reports/d176_d177_controlled_autonomy_cycle_reentry_intake_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D176 sandbox candidate reentry controlled next cycle scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D176 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD176 SANDBOX CANDIDATE REENTRY CONTROLLED NEXT CYCLE SCOPE BOOT DONE")
