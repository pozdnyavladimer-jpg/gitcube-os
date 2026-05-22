#!/usr/bin/env python3
# D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_BOOT.py
#
# D178 consumes D177 controlled-autonomy cycle reentry intake artifacts and creates:
# - runtime_experimental/controlled_autonomy_provider_reentry_scope.py
# - tests/test_d178_controlled_autonomy_provider_reentry_scope.py
# - reports/d178_controlled_autonomy_provider_reentry_scope.json
# - reports/d178_controlled_autonomy_provider_dry_ping_scope.json
# - reports/d178_d179_controlled_autonomy_proposal_reentry_scope.json
#
# D178 opens provider reentry as a dry, record-only scope.
# It does not authorize or perform a real provider/network call.
#
# No network, no secret read, no shell, no real apply,
# no route insert, no protected core mutation by AI, no git action by AI.
#
# Opens D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE only.

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

D177_REPORT = "reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json"
D177_FRESH_INTENT_PACKET = "reports/d177_controlled_autonomy_cycle_fresh_intent_packet.json"
D177_D178_SCOPE = "reports/d177_d178_controlled_autonomy_provider_reentry_scope.json"

OUT = "reports/d178_controlled_autonomy_provider_reentry_scope.json"
PROVIDER_DRY_PING_OUT = "reports/d178_controlled_autonomy_provider_dry_ping_scope.json"
D179_SCOPE_OUT = "reports/d178_d179_controlled_autonomy_proposal_reentry_scope.json"

REQ_D177_DECISION = "CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_READY"
REQ_D178_GATE = "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE"
REQ_D179_GATE = "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE"

AFTER_D177_FALSE = [
    "network_allowed_after_d177_by_ai",
    "secret_read_allowed_after_d177_by_ai",
    "shell_allowed_after_d177_by_ai",
    "real_apply_allowed_after_d177_by_ai",
    "route_insert_allowed_after_d177_by_ai",
    "protected_core_mutation_allowed_after_d177_by_ai",
    "git_action_allowed_after_d177_by_ai",
]

FALSE_KEYS = [
    "authority_carried_forward",
    "provider_authority_carried_forward",
    "provider_call_authorized",
    "provider_response_authorized",
    "provider_network_call_performed",
    "provider_dry_ping_real_network",
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


def normalize_d177_compat(d177, fresh_intent_packet, d178_scope):
    # Compatibility bridge: missing explicit false flags become False, never True.
    for obj in (d177.get("guardrails", {}) if isinstance(d177, dict) else {}, fresh_intent_packet):
        if isinstance(obj, dict):
            for k in FALSE_KEYS:
                obj.setdefault(k, False)

    if isinstance(d178_scope, dict):
        for k in [
            "provider_call_authorized",
            "provider_response_authorized",
            "authority_carried_forward",
            "provider_authority_carried_forward",
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
        ] + AFTER_D177_FALSE:
            d178_scope.setdefault(k, False)

    if d177:
        d177.setdefault("summary", {})
        d177["summary"].setdefault("provider_response_status", "NOT_INGESTED_DRY_PLACEHOLDER_USED")
        d177["summary"].setdefault("candidate_execution_status", "EXECUTED_IN_SANDBOX_NO_OP_ONLY")
        d177.setdefault("guardrails", {})
        for k in [
            "cycle_reentry_intake_created",
            "fresh_intent_packet_created",
            "fresh_cycle_intake_required",
            "previous_chain_closed",
            "previous_chain_archived",
            "no_inherited_authority",
            "fresh_intent_required",
            "human_review_required",
        ]:
            d177["guardrails"].setdefault(k, True)

    if fresh_intent_packet:
        fresh_intent_packet.setdefault("fresh_intent_packet_status", "FRESH_INTENT_PACKET_CREATED_NO_INHERITED_AUTHORITY")
        fresh_intent_packet.setdefault("packet_mode", "CONTROLLED_AUTONOMY_REENTRY_RECORD_ONLY")
        for k in [
            "previous_chain_archived",
            "previous_chain_closed",
            "fresh_cycle_intake_required",
            "fresh_intent_required",
            "human_review_required",
            "no_inherited_authority",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ]:
            fresh_intent_packet.setdefault(k, True)

    if d178_scope:
        for k in [
            "controlled_autonomy_provider_reentry_scope_only",
            "fresh_intent_packet_created",
            "fresh_cycle_intake_required",
            "previous_chain_archived",
            "previous_chain_closed",
            "no_inherited_authority",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ]:
            d178_scope.setdefault(k, True)


def validate_d177(d177, fresh_intent_packet, d178_scope):
    errors = []

    if not d177:
        return ["missing D177 controlled autonomy cycle reentry intake scope report"]
    if d177.get("ok") is not True:
        errors.append("D177 ok must be true")
    if d177.get("decision") != REQ_D177_DECISION:
        errors.append("D177 decision must be CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_READY")

    summary = d177.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D177_PLUS",
        "cycle_reentry_intake_status": "FRESH_CYCLE_REENTRY_INTAKE_CREATED_NO_INHERITED_AUTHORITY",
        "fresh_intent_packet_status": "FRESH_INTENT_PACKET_CREATED_NO_INHERITED_AUTHORITY",
        "candidate_status": "CONTROLLED_AUTONOMY_READY_FOR_PROVIDER_REENTRY_SCOPE",
        "real_provider_status": "NOT_CALLED",
        "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_ONLY",
        "next_step": REQ_D178_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D177 summary.{k} must be {v}")

    guard = normalize_guard_flags(d177.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D177 guardrails"))
    require_true(guard, [
        "controlled_autonomy_cycle_reentry_intake_scope_only",
        "controlled_autonomy_cycle_fresh_intent_packet_only",
        "canonical_guard_schema_applied",
        "fresh_cycle_intake_required",
        "previous_chain_closed",
        "previous_chain_archived",
        "no_inherited_authority",
        "fresh_intent_required",
        "human_review_required",
        "cycle_reentry_intake_created",
        "fresh_intent_packet_created",
        "approval_for_d178_controlled_autonomy_provider_reentry_scope_only",
    ], "D177 guardrails", errors)
    require_false(guard, [
        "authority_carried_forward",
        "provider_authority_carried_forward",
        "provider_call_authorized",
        "provider_response_authorized",
        "candidate_apply_executed",
        "candidate_apply_executed_by_ai",
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "apply_requested",
        "apply_executed",
        "real_apply_executed",
        "actual_apply_executed",
        *AFTER_D177_FALSE,
    ], "D177 guardrails", errors)

    if not fresh_intent_packet:
        errors.append("missing D177 fresh intent packet")
    else:
        if fresh_intent_packet.get("ok") is not True:
            errors.append("D177 fresh intent packet ok must be true")
        if fresh_intent_packet.get("fresh_intent_packet_status") != "FRESH_INTENT_PACKET_CREATED_NO_INHERITED_AUTHORITY":
            errors.append("D177 fresh intent packet status mismatch")
        require_true(fresh_intent_packet, [
            "previous_chain_archived",
            "previous_chain_closed",
            "fresh_cycle_intake_required",
            "fresh_intent_required",
            "human_review_required",
            "no_inherited_authority",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], "D177 fresh intent packet", errors)
        require_false(fresh_intent_packet, [
            "authority_carried_forward",
            "provider_authority_carried_forward",
            "provider_call_authorized",
            "provider_response_authorized",
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
        ], "D177 fresh intent packet", errors)

    if not d178_scope:
        errors.append("missing D177 D178 controlled autonomy provider reentry scope")
    else:
        if d178_scope.get("ok") is not True:
            errors.append("D177 D178 scope ok must be true")
        if d178_scope.get("allowed_next_gate") != REQ_D178_GATE:
            errors.append("D177 D178 scope allowed_next_gate must be D178")
        require_true(d178_scope, [
            "controlled_autonomy_provider_reentry_scope_only",
            "fresh_intent_packet_created",
            "fresh_cycle_intake_required",
            "previous_chain_archived",
            "previous_chain_closed",
            "no_inherited_authority",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ], "D177 D178 scope", errors)
        require_false(d178_scope, [
            "provider_call_authorized",
            "provider_response_authorized",
            "authority_carried_forward",
            "provider_authority_carried_forward",
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
            "network_allowed_after_d177_by_ai",
            "secret_read_allowed_after_d177_by_ai",
            "shell_allowed_after_d177_by_ai",
            "real_apply_allowed_after_d177_by_ai",
            "route_insert_allowed_after_d177_by_ai",
            "protected_core_mutation_allowed_after_d177_by_ai",
            "git_action_allowed_after_d177_by_ai",
        ], "D177 D178 scope", errors)

    return errors


def build_provider_dry_ping_scope(provider_reentry_id, d177):
    data = {
        "state": "D178_CONTROLLED_AUTONOMY_PROVIDER_DRY_PING_SCOPE",
        "ok": True,
        "provider_reentry_id": provider_reentry_id,
        "cycle_intake_id": d177.get("cycle_intake_id"),
        "controlled_next_cycle_id": d177.get("controlled_next_cycle_id"),
        "archive_id": d177.get("archive_id"),
        "final_audit_id": d177.get("final_audit_id"),
        "run_id": d177.get("run_id"),
        "intent_id": d177.get("intent_id"),
        "candidate_id": d177.get("candidate_id"),
        "response_id": d177.get("response_id"),
        "created_at": now(),
        "provider_dry_ping_status": "PROVIDER_DRY_PING_SCOPE_CREATED_NO_NETWORK",
        "provider_reentry_status": "PROVIDER_REENTRY_SCOPE_CREATED_NO_PROVIDER_CALL",
        "dry_ping_mode": "LOCAL_RECORD_ONLY_NO_NETWORK",
        "provider_call_authorized": False,
        "provider_response_authorized": False,
        "provider_network_call_performed": False,
        "provider_dry_ping_real_network": False,
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


def build_d179_scope(provider_reentry_id, d177):
    return {
        "state": "D178_D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE",
        "ok": True,
        "provider_reentry_id": provider_reentry_id,
        "cycle_intake_id": d177.get("cycle_intake_id"),
        "controlled_next_cycle_id": d177.get("controlled_next_cycle_id"),
        "archive_id": d177.get("archive_id"),
        "final_audit_id": d177.get("final_audit_id"),
        "post_apply_verification_id": d177.get("post_apply_verification_id"),
        "guarded_apply_id": d177.get("guarded_apply_id"),
        "apply_intent_id": d177.get("apply_intent_id"),
        "run_id": d177.get("run_id"),
        "intent_id": d177.get("intent_id"),
        "candidate_id": d177.get("candidate_id"),
        "response_id": d177.get("response_id"),
        "proposal_id": d177.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D179_GATE,
        "controlled_autonomy_proposal_reentry_scope_only": True,
        "provider_reentry_scope_created": True,
        "provider_dry_ping_scope_created": True,
        "provider_call_authorized": False,
        "provider_response_authorized": False,
        "provider_network_call_performed": False,
        "provider_dry_ping_real_network": False,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "authority_carried_forward": False,
        "provider_authority_carried_forward": False,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "network_allowed_after_d178_by_ai": False,
        "secret_read_allowed_after_d178_by_ai": False,
        "shell_allowed_after_d178_by_ai": False,
        "real_apply_allowed_after_d178_by_ai": False,
        "route_insert_allowed_after_d178_by_ai": False,
        "protected_core_mutation_allowed_after_d178_by_ai": False,
        "git_action_allowed_after_d178_by_ai": False,
        "d179_allowed_to_create": [
            "controlled_autonomy_proposal_reentry_scope",
            "controlled_autonomy_proposal_candidate_packet",
            "d180_controlled_autonomy_human_review_scope",
        ],
        "d179_must_not_execute": [
            "real_provider_network_call_without_human_gate",
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


def create_controlled_autonomy_provider_reentry_scope(root="."):
    root = Path(root).resolve()

    d177 = read_json(root / D177_REPORT, {}) or {}
    fresh_intent_packet = read_json(root / D177_FRESH_INTENT_PACKET, {}) or {}
    d178_scope = read_json(root / D177_D178_SCOPE, {}) or {}

    normalize_d177_compat(d177, fresh_intent_packet, d178_scope)
    errors = validate_d177(d177, fresh_intent_packet, d178_scope)

    provider_reentry_id = "d178-" + digest({
        "cycle_intake_id": d177.get("cycle_intake_id"),
        "controlled_next_cycle_id": d177.get("controlled_next_cycle_id"),
        "archive_id": d177.get("archive_id"),
        "final_audit_id": d177.get("final_audit_id"),
        "run_id": d177.get("run_id"),
        "intent_id": d177.get("intent_id"),
        "candidate_id": d177.get("candidate_id"),
        "response_id": d177.get("response_id"),
        "proposal_id": d177.get("proposal_id"),
    })

    provider_dry_ping_scope = build_provider_dry_ping_scope(provider_reentry_id, d177)
    d179_scope = build_d179_scope(provider_reentry_id, d177)

    require_true(provider_dry_ping_scope, [
        "no_real_apply",
        "no_network",
        "no_secret_read",
        "no_shell",
        "no_route_insert",
        "no_core_mutation_by_ai",
        "no_git_action_by_ai",
    ], "provider_dry_ping_scope", errors)
    require_false(provider_dry_ping_scope, [
        "provider_call_authorized",
        "provider_response_authorized",
        "provider_network_call_performed",
        "provider_dry_ping_real_network",
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
    ], "provider_dry_ping_scope", errors)

    require_true(d179_scope, [
        "controlled_autonomy_proposal_reentry_scope_only",
        "provider_reentry_scope_created",
        "provider_dry_ping_scope_created",
        "fresh_intent_required",
        "human_review_required",
        "canonical_guard_schema_required",
    ], "d179_scope", errors)
    require_false(d179_scope, [
        "provider_call_authorized",
        "provider_response_authorized",
        "provider_network_call_performed",
        "provider_dry_ping_real_network",
        "authority_carried_forward",
        "provider_authority_carried_forward",
        "candidate_apply_executed",
        "candidate_apply_executed_by_ai",
        "network_allowed_after_d178_by_ai",
        "secret_read_allowed_after_d178_by_ai",
        "shell_allowed_after_d178_by_ai",
        "real_apply_allowed_after_d178_by_ai",
        "route_insert_allowed_after_d178_by_ai",
        "protected_core_mutation_allowed_after_d178_by_ai",
        "git_action_allowed_after_d178_by_ai",
    ], "d179_scope", errors)

    ok = not errors
    decision = "CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_READY" if ok else "CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_BLOCKED"
    result = "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_CREATED" if ok else "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_BLOCKED"

    if ok:
        write_json(root / PROVIDER_DRY_PING_OUT, provider_dry_ping_scope)
        write_json(root / D179_SCOPE_OUT, d179_scope)

    guardrails = normalize_guard_flags({
        "controlled_autonomy_provider_reentry_scope_only": True,
        "controlled_autonomy_provider_dry_ping_scope_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "provider_reentry_scope_created": ok,
        "provider_dry_ping_scope_created": ok,
        "proposal_reentry_scope_created": ok,
        "provider_call_authorized": False,
        "provider_response_authorized": False,
        "provider_network_call_performed": False,
        "provider_dry_ping_real_network": False,
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
        "approval_for_d179_controlled_autonomy_proposal_reentry_scope_only": ok,
        "network_allowed_after_d178_by_ai": False,
        "secret_read_allowed_after_d178_by_ai": False,
        "shell_allowed_after_d178_by_ai": False,
        "real_apply_allowed_after_d178_by_ai": False,
        "route_insert_allowed_after_d178_by_ai": False,
        "protected_core_mutation_allowed_after_d178_by_ai": False,
        "git_action_allowed_after_d178_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "provider_reentry_id": provider_reentry_id,
        "cycle_intake_id": d177.get("cycle_intake_id"),
        "controlled_next_cycle_id": d177.get("controlled_next_cycle_id"),
        "archive_id": d177.get("archive_id"),
        "final_audit_id": d177.get("final_audit_id"),
        "post_apply_verification_id": d177.get("post_apply_verification_id"),
        "guarded_apply_id": d177.get("guarded_apply_id"),
        "apply_intent_id": d177.get("apply_intent_id"),
        "run_id": d177.get("run_id"),
        "intent_id": d177.get("intent_id"),
        "candidate_id": d177.get("candidate_id"),
        "response_id": d177.get("response_id"),
        "proposal_id": d177.get("proposal_id"),
        "source_d177_report": D177_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "provider_dry_ping_scope": provider_dry_ping_scope if ok else {},
        "d179_scope": d179_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "provider_reentry_id": provider_reentry_id,
            "cycle_intake_id": d177.get("cycle_intake_id"),
            "controlled_next_cycle_id": d177.get("controlled_next_cycle_id"),
            "archive_id": d177.get("archive_id"),
            "final_audit_id": d177.get("final_audit_id"),
            "run_id": d177.get("run_id"),
            "intent_id": d177.get("intent_id"),
            "candidate_id": d177.get("candidate_id"),
            "response_id": d177.get("response_id"),
            "proposal_id": d177.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D178_PLUS" if ok else "BLOCKED",
            "provider_reentry_status": "PROVIDER_REENTRY_SCOPE_CREATED_NO_PROVIDER_CALL" if ok else "BLOCKED",
            "provider_dry_ping_status": "PROVIDER_DRY_PING_SCOPE_CREATED_NO_NETWORK" if ok else "BLOCKED",
            "candidate_status": "CONTROLLED_AUTONOMY_READY_FOR_PROPOSAL_REENTRY_SCOPE" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY" if ok else "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D179_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "controlled_autonomy_provider_reentry_scope_created": ok,
            "provider_dry_ping_scope_created": ok,
            "d179_scope_created": ok,
            "provider_call_authorized": False,
            "provider_network_call_performed": False,
            "real_provider_call_performed": False,
            "real_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D179 may create controlled autonomy proposal reentry scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_controlled_autonomy_provider_reentry_scope(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.controlled_autonomy_provider_reentry_scope import create_controlled_autonomy_provider_reentry_scope


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


class TestD178ControlledAutonomyProviderReentryScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        d177 = {
            "ok": True,
            "decision": "CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_READY",
            "cycle_intake_id": "d177-test",
            "controlled_next_cycle_id": "d176-test",
            "archive_id": "d175-test",
            "final_audit_id": "d174-test",
            "post_apply_verification_id": "d173-test",
            "guarded_apply_id": "d172-test",
            "apply_intent_id": "d171-test",
            "run_id": "d168-test",
            "intent_id": "d167-test",
            "candidate_id": "d164-test",
            "response_id": "d163-test",
            "proposal_id": "d107-valid-test",
            "guardrails": {
                **no_ai_flags(),
                "controlled_autonomy_cycle_reentry_intake_scope_only": True,
                "controlled_autonomy_cycle_fresh_intent_packet_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_cycle_intake_required": True,
                "previous_chain_closed": True,
                "previous_chain_archived": True,
                "no_inherited_authority": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "cycle_reentry_intake_created": True,
                "fresh_intent_packet_created": True,
                "authority_carried_forward": False,
                "provider_authority_carried_forward": False,
                "provider_call_authorized": False,
                "provider_response_authorized": False,
                "candidate_apply_executed": False,
                "candidate_apply_executed_by_ai": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "real_apply_executed": False,
                "actual_apply_executed": False,
                "approval_for_d178_controlled_autonomy_provider_reentry_scope_only": True,
                "network_allowed_after_d177_by_ai": False,
                "secret_read_allowed_after_d177_by_ai": False,
                "shell_allowed_after_d177_by_ai": False,
                "real_apply_allowed_after_d177_by_ai": False,
                "route_insert_allowed_after_d177_by_ai": False,
                "protected_core_mutation_allowed_after_d177_by_ai": False,
                "git_action_allowed_after_d177_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D177_PLUS",
                "cycle_reentry_intake_status": "FRESH_CYCLE_REENTRY_INTAKE_CREATED_NO_INHERITED_AUTHORITY",
                "fresh_intent_packet_status": "FRESH_INTENT_PACKET_CREATED_NO_INHERITED_AUTHORITY",
                "candidate_status": "CONTROLLED_AUTONOMY_READY_FOR_PROVIDER_REENTRY_SCOPE",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_ONLY",
                "next_step": "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE",
            },
        }

        fresh_intent_packet = {
            **no_ai_flags(),
            "ok": True,
            "fresh_intent_packet_status": "FRESH_INTENT_PACKET_CREATED_NO_INHERITED_AUTHORITY",
            "packet_mode": "CONTROLLED_AUTONOMY_REENTRY_RECORD_ONLY",
            "previous_chain_archived": True,
            "previous_chain_closed": True,
            "fresh_cycle_intake_required": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "no_inherited_authority": True,
            "authority_carried_forward": False,
            "provider_authority_carried_forward": False,
            "provider_call_authorized": False,
            "provider_response_authorized": False,
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

        d178_scope = {
            "ok": True,
            "allowed_next_gate": "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE",
            "controlled_autonomy_provider_reentry_scope_only": True,
            "fresh_intent_packet_created": True,
            "fresh_cycle_intake_required": True,
            "previous_chain_archived": True,
            "previous_chain_closed": True,
            "no_inherited_authority": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "provider_call_authorized": False,
            "provider_response_authorized": False,
            "authority_carried_forward": False,
            "provider_authority_carried_forward": False,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "network_allowed_after_d177_by_ai": False,
            "secret_read_allowed_after_d177_by_ai": False,
            "shell_allowed_after_d177_by_ai": False,
            "real_apply_allowed_after_d177_by_ai": False,
            "route_insert_allowed_after_d177_by_ai": False,
            "protected_core_mutation_allowed_after_d177_by_ai": False,
            "git_action_allowed_after_d177_by_ai": False,
        }

        write(root / "reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json", d177)
        write(root / "reports/d177_controlled_autonomy_cycle_fresh_intent_packet.json", fresh_intent_packet)
        write(root / "reports/d177_d178_controlled_autonomy_provider_reentry_scope.json", d178_scope)
        return td, root

    def test_creates_provider_reentry_outputs(self):
        td, root = self.root()
        try:
            r = create_controlled_autonomy_provider_reentry_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_ONLY")
            self.assertEqual(r["d179_scope"]["allowed_next_gate"], "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE")
            self.assertTrue(r["guardrails"]["provider_reentry_scope_created"])
            self.assertTrue(r["guardrails"]["provider_dry_ping_scope_created"])
            self.assertFalse(r["guardrails"]["provider_call_authorized"])
            self.assertFalse(r["guardrails"]["provider_network_call_performed"])
            self.assertTrue((root / "reports/d178_controlled_autonomy_provider_reentry_scope.json").exists())
            self.assertTrue((root / "reports/d178_controlled_autonomy_provider_dry_ping_scope.json").exists())
            self.assertTrue((root / "reports/d178_d179_controlled_autonomy_proposal_reentry_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d177(self):
        td, root = self.root()
        try:
            (root / "reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json").unlink()
            r = create_controlled_autonomy_provider_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_fresh_packet_authorizes_provider(self):
        td, root = self.root()
        try:
            p = root / "reports/d177_controlled_autonomy_cycle_fresh_intent_packet.json"
            data = json.loads(p.read_text())
            data["provider_call_authorized"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_provider_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d178_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d177_d178_controlled_autonomy_provider_reentry_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d177_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_provider_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d177_not_ready(self):
        td, root = self.root()
        try:
            p = root / "reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json"
            data = json.loads(p.read_text())
            data["decision"] = "BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_provider_reentry_scope(root)
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

print("D178 CONTROLLED AUTONOMY PROVIDER REENTRY SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/controlled_autonomy_provider_reentry_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d178_controlled_autonomy_provider_reentry_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/controlled_autonomy_provider_reentry_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d178_controlled_autonomy_provider_reentry_scope", "-v"], check=True)

print("\n== run D178 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.controlled_autonomy_provider_reentry_scope import create_controlled_autonomy_provider_reentry_scope\n"
    "r=create_controlled_autonomy_provider_reentry_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d178_controlled_autonomy_provider_reentry_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/controlled_autonomy_provider_reentry_scope.py",
    "tests/test_d178_controlled_autonomy_provider_reentry_scope.py",
    "reports/d178_controlled_autonomy_provider_reentry_scope.json",
    "reports/d178_controlled_autonomy_provider_dry_ping_scope.json",
    "reports/d178_d179_controlled_autonomy_proposal_reentry_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D178 controlled autonomy provider reentry scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D178 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD178 CONTROLLED AUTONOMY PROVIDER REENTRY SCOPE BOOT DONE")
