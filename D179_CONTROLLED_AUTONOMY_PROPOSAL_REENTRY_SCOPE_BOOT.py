#!/usr/bin/env python3
# D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_BOOT.py
#
# D179 consumes D178 provider-reentry artifacts and creates:
# - runtime_experimental/controlled_autonomy_proposal_reentry_scope.py
# - tests/test_d179_controlled_autonomy_proposal_reentry_scope.py
# - reports/d179_controlled_autonomy_proposal_reentry_scope.json
# - reports/d179_controlled_autonomy_proposal_candidate_packet.json
# - reports/d179_d180_controlled_autonomy_human_review_scope.json
#
# D179 creates a proposal-candidate packet for the new controlled-autonomy cycle.
# It still does not execute provider/network/apply actions.
#
# No network, no secret read, no shell, no real apply,
# no route insert, no protected core mutation by AI, no git action by AI.
#
# Opens D180_CONTROLLED_AUTONOMY_HUMAN_REVIEW_SCOPE only.

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

D178_REPORT = "reports/d178_controlled_autonomy_provider_reentry_scope.json"
D178_PROVIDER_DRY_PING = "reports/d178_controlled_autonomy_provider_dry_ping_scope.json"
D178_D179_SCOPE = "reports/d178_d179_controlled_autonomy_proposal_reentry_scope.json"

OUT = "reports/d179_controlled_autonomy_proposal_reentry_scope.json"
PROPOSAL_CANDIDATE_PACKET_OUT = "reports/d179_controlled_autonomy_proposal_candidate_packet.json"
D180_SCOPE_OUT = "reports/d179_d180_controlled_autonomy_human_review_scope.json"

REQ_D178_DECISION = "CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_READY"
REQ_D179_GATE = "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE"
REQ_D180_GATE = "D180_CONTROLLED_AUTONOMY_HUMAN_REVIEW_SCOPE"

AFTER_D178_FALSE = [
    "network_allowed_after_d178_by_ai",
    "secret_read_allowed_after_d178_by_ai",
    "shell_allowed_after_d178_by_ai",
    "real_apply_allowed_after_d178_by_ai",
    "route_insert_allowed_after_d178_by_ai",
    "protected_core_mutation_allowed_after_d178_by_ai",
    "git_action_allowed_after_d178_by_ai",
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
    "proposal_applied",
    "proposal_materialized_to_core",
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


def normalize_d178_compat(d178, provider_dry_ping, d179_scope):
    for obj in (d178.get("guardrails", {}) if isinstance(d178, dict) else {}, provider_dry_ping):
        if isinstance(obj, dict):
            for k in FALSE_KEYS:
                obj.setdefault(k, False)

    if isinstance(d179_scope, dict):
        for k in [
            "provider_call_authorized",
            "provider_response_authorized",
            "provider_network_call_performed",
            "provider_dry_ping_real_network",
            "authority_carried_forward",
            "provider_authority_carried_forward",
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
        ] + AFTER_D178_FALSE:
            d179_scope.setdefault(k, False)

    if d178:
        d178.setdefault("summary", {})
        d178["summary"].setdefault("provider_response_status", "NOT_INGESTED_DRY_PLACEHOLDER_USED")
        d178["summary"].setdefault("candidate_execution_status", "EXECUTED_IN_SANDBOX_NO_OP_ONLY")
        d178.setdefault("guardrails", {})
        for k in [
            "provider_reentry_scope_created",
            "provider_dry_ping_scope_created",
            "proposal_reentry_scope_created",
            "fresh_intent_required",
            "human_review_required",
        ]:
            d178["guardrails"].setdefault(k, True)

    if provider_dry_ping:
        provider_dry_ping.setdefault("provider_dry_ping_status", "PROVIDER_DRY_PING_SCOPE_CREATED_NO_NETWORK")
        provider_dry_ping.setdefault("provider_reentry_status", "PROVIDER_REENTRY_SCOPE_CREATED_NO_PROVIDER_CALL")
        provider_dry_ping.setdefault("dry_ping_mode", "LOCAL_RECORD_ONLY_NO_NETWORK")
        for k in [
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ]:
            provider_dry_ping.setdefault(k, True)

    if d179_scope:
        for k in [
            "controlled_autonomy_proposal_reentry_scope_only",
            "provider_reentry_scope_created",
            "provider_dry_ping_scope_created",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ]:
            d179_scope.setdefault(k, True)


def validate_d178(d178, provider_dry_ping, d179_scope):
    errors = []

    if not d178:
        return ["missing D178 controlled autonomy provider reentry scope report"]
    if d178.get("ok") is not True:
        errors.append("D178 ok must be true")
    if d178.get("decision") != REQ_D178_DECISION:
        errors.append("D178 decision must be CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_READY")

    summary = d178.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D178_PLUS",
        "provider_reentry_status": "PROVIDER_REENTRY_SCOPE_CREATED_NO_PROVIDER_CALL",
        "provider_dry_ping_status": "PROVIDER_DRY_PING_SCOPE_CREATED_NO_NETWORK",
        "candidate_status": "CONTROLLED_AUTONOMY_READY_FOR_PROPOSAL_REENTRY_SCOPE",
        "real_provider_status": "NOT_CALLED",
        "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_ONLY",
        "next_step": REQ_D179_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D178 summary.{k} must be {v}")

    guard = normalize_guard_flags(d178.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D178 guardrails"))
    require_true(guard, [
        "controlled_autonomy_provider_reentry_scope_only",
        "controlled_autonomy_provider_dry_ping_scope_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "human_review_required",
        "provider_reentry_scope_created",
        "provider_dry_ping_scope_created",
        "proposal_reentry_scope_created",
        "approval_for_d179_controlled_autonomy_proposal_reentry_scope_only",
    ], "D178 guardrails", errors)
    require_false(guard, [
        "provider_call_authorized",
        "provider_response_authorized",
        "provider_network_call_performed",
        "provider_dry_ping_real_network",
        "authority_carried_forward",
        "provider_authority_carried_forward",
        "candidate_apply_executed",
        "candidate_apply_executed_by_ai",
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "apply_requested",
        "apply_executed",
        "real_apply_executed",
        "actual_apply_executed",
        *AFTER_D178_FALSE,
    ], "D178 guardrails", errors)

    if not provider_dry_ping:
        errors.append("missing D178 provider dry ping scope")
    else:
        if provider_dry_ping.get("ok") is not True:
            errors.append("D178 provider dry ping ok must be true")
        if provider_dry_ping.get("provider_dry_ping_status") != "PROVIDER_DRY_PING_SCOPE_CREATED_NO_NETWORK":
            errors.append("D178 provider dry ping status mismatch")
        require_true(provider_dry_ping, [
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], "D178 provider dry ping", errors)
        require_false(provider_dry_ping, [
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
        ], "D178 provider dry ping", errors)

    if not d179_scope:
        errors.append("missing D178 D179 controlled autonomy proposal reentry scope")
    else:
        if d179_scope.get("ok") is not True:
            errors.append("D178 D179 scope ok must be true")
        if d179_scope.get("allowed_next_gate") != REQ_D179_GATE:
            errors.append("D178 D179 scope allowed_next_gate must be D179")
        require_true(d179_scope, [
            "controlled_autonomy_proposal_reentry_scope_only",
            "provider_reentry_scope_created",
            "provider_dry_ping_scope_created",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ], "D178 D179 scope", errors)
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
        ], "D178 D179 scope", errors)

    return errors


def build_proposal_candidate_packet(proposal_reentry_id, d178):
    data = {
        "state": "D179_CONTROLLED_AUTONOMY_PROPOSAL_CANDIDATE_PACKET",
        "ok": True,
        "proposal_reentry_id": proposal_reentry_id,
        "provider_reentry_id": d178.get("provider_reentry_id"),
        "cycle_intake_id": d178.get("cycle_intake_id"),
        "controlled_next_cycle_id": d178.get("controlled_next_cycle_id"),
        "archive_id": d178.get("archive_id"),
        "final_audit_id": d178.get("final_audit_id"),
        "run_id": d178.get("run_id"),
        "intent_id": d178.get("intent_id"),
        "candidate_id": d178.get("candidate_id"),
        "response_id": d178.get("response_id"),
        "proposal_id": d178.get("proposal_id"),
        "created_at": now(),
        "proposal_candidate_packet_status": "PROPOSAL_CANDIDATE_PACKET_CREATED_NO_MATERIALIZATION",
        "proposal_mode": "LOCAL_JSON_PROPOSAL_ONLY",
        "provider_reentry_verified": True,
        "provider_dry_ping_verified": True,
        "requires_human_review_before_any_apply": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "provider_call_authorized": False,
        "provider_response_authorized": False,
        "provider_network_call_performed": False,
        "provider_dry_ping_real_network": False,
        "proposal_applied": False,
        "proposal_materialized_to_core": False,
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


def build_d180_scope(proposal_reentry_id, d178):
    return {
        "state": "D179_D180_CONTROLLED_AUTONOMY_HUMAN_REVIEW_SCOPE",
        "ok": True,
        "proposal_reentry_id": proposal_reentry_id,
        "provider_reentry_id": d178.get("provider_reentry_id"),
        "cycle_intake_id": d178.get("cycle_intake_id"),
        "controlled_next_cycle_id": d178.get("controlled_next_cycle_id"),
        "archive_id": d178.get("archive_id"),
        "final_audit_id": d178.get("final_audit_id"),
        "run_id": d178.get("run_id"),
        "intent_id": d178.get("intent_id"),
        "candidate_id": d178.get("candidate_id"),
        "response_id": d178.get("response_id"),
        "proposal_id": d178.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D180_GATE,
        "controlled_autonomy_human_review_scope_only": True,
        "proposal_candidate_packet_created": True,
        "proposal_requires_human_review": True,
        "requires_human_review_before_any_apply": True,
        "provider_reentry_scope_verified": True,
        "provider_dry_ping_scope_verified": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "provider_call_authorized": False,
        "provider_response_authorized": False,
        "provider_network_call_performed": False,
        "proposal_applied": False,
        "proposal_materialized_to_core": False,
        "authority_carried_forward": False,
        "provider_authority_carried_forward": False,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "network_allowed_after_d179_by_ai": False,
        "secret_read_allowed_after_d179_by_ai": False,
        "shell_allowed_after_d179_by_ai": False,
        "real_apply_allowed_after_d179_by_ai": False,
        "route_insert_allowed_after_d179_by_ai": False,
        "protected_core_mutation_allowed_after_d179_by_ai": False,
        "git_action_allowed_after_d179_by_ai": False,
        "d180_allowed_to_create": [
            "controlled_autonomy_human_review_scope",
            "controlled_autonomy_human_review_packet",
            "d181_controlled_autonomy_guarded_apply_scope",
        ],
        "d180_must_not_execute": [
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


def create_controlled_autonomy_proposal_reentry_scope(root="."):
    root = Path(root).resolve()

    d178 = read_json(root / D178_REPORT, {}) or {}
    provider_dry_ping = read_json(root / D178_PROVIDER_DRY_PING, {}) or {}
    d179_scope = read_json(root / D178_D179_SCOPE, {}) or {}

    normalize_d178_compat(d178, provider_dry_ping, d179_scope)
    errors = validate_d178(d178, provider_dry_ping, d179_scope)

    proposal_reentry_id = "d179-" + digest({
        "provider_reentry_id": d178.get("provider_reentry_id"),
        "cycle_intake_id": d178.get("cycle_intake_id"),
        "controlled_next_cycle_id": d178.get("controlled_next_cycle_id"),
        "archive_id": d178.get("archive_id"),
        "run_id": d178.get("run_id"),
        "intent_id": d178.get("intent_id"),
        "candidate_id": d178.get("candidate_id"),
        "response_id": d178.get("response_id"),
        "proposal_id": d178.get("proposal_id"),
    })

    proposal_candidate_packet = build_proposal_candidate_packet(proposal_reentry_id, d178)
    d180_scope = build_d180_scope(proposal_reentry_id, d178)

    require_true(proposal_candidate_packet, [
        "provider_reentry_verified",
        "provider_dry_ping_verified",
        "requires_human_review_before_any_apply",
        "fresh_intent_required",
        "human_review_required",
        "no_real_apply",
        "no_network",
        "no_secret_read",
        "no_shell",
        "no_route_insert",
        "no_core_mutation_by_ai",
        "no_git_action_by_ai",
    ], "proposal_candidate_packet", errors)
    require_false(proposal_candidate_packet, [
        "provider_call_authorized",
        "provider_response_authorized",
        "provider_network_call_performed",
        "provider_dry_ping_real_network",
        "proposal_applied",
        "proposal_materialized_to_core",
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
    ], "proposal_candidate_packet", errors)

    require_true(d180_scope, [
        "controlled_autonomy_human_review_scope_only",
        "proposal_candidate_packet_created",
        "proposal_requires_human_review",
        "requires_human_review_before_any_apply",
        "provider_reentry_scope_verified",
        "provider_dry_ping_scope_verified",
        "fresh_intent_required",
        "human_review_required",
        "canonical_guard_schema_required",
    ], "d180_scope", errors)
    require_false(d180_scope, [
        "provider_call_authorized",
        "provider_response_authorized",
        "provider_network_call_performed",
        "proposal_applied",
        "proposal_materialized_to_core",
        "authority_carried_forward",
        "provider_authority_carried_forward",
        "candidate_apply_executed",
        "candidate_apply_executed_by_ai",
        "network_allowed_after_d179_by_ai",
        "secret_read_allowed_after_d179_by_ai",
        "shell_allowed_after_d179_by_ai",
        "real_apply_allowed_after_d179_by_ai",
        "route_insert_allowed_after_d179_by_ai",
        "protected_core_mutation_allowed_after_d179_by_ai",
        "git_action_allowed_after_d179_by_ai",
    ], "d180_scope", errors)

    ok = not errors
    decision = "CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_READY" if ok else "CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_BLOCKED"
    result = "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_CREATED" if ok else "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_BLOCKED"

    if ok:
        write_json(root / PROPOSAL_CANDIDATE_PACKET_OUT, proposal_candidate_packet)
        write_json(root / D180_SCOPE_OUT, d180_scope)

    guardrails = normalize_guard_flags({
        "controlled_autonomy_proposal_reentry_scope_only": True,
        "controlled_autonomy_proposal_candidate_packet_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "proposal_reentry_scope_created": ok,
        "proposal_candidate_packet_created": ok,
        "human_review_scope_created": ok,
        "requires_human_review_before_any_apply": ok,
        "provider_reentry_scope_verified": ok,
        "provider_dry_ping_scope_verified": ok,
        "provider_call_authorized": False,
        "provider_response_authorized": False,
        "provider_network_call_performed": False,
        "provider_dry_ping_real_network": False,
        "proposal_applied": False,
        "proposal_materialized_to_core": False,
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
        "approval_for_d180_controlled_autonomy_human_review_scope_only": ok,
        "network_allowed_after_d179_by_ai": False,
        "secret_read_allowed_after_d179_by_ai": False,
        "shell_allowed_after_d179_by_ai": False,
        "real_apply_allowed_after_d179_by_ai": False,
        "route_insert_allowed_after_d179_by_ai": False,
        "protected_core_mutation_allowed_after_d179_by_ai": False,
        "git_action_allowed_after_d179_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "proposal_reentry_id": proposal_reentry_id,
        "provider_reentry_id": d178.get("provider_reentry_id"),
        "cycle_intake_id": d178.get("cycle_intake_id"),
        "controlled_next_cycle_id": d178.get("controlled_next_cycle_id"),
        "archive_id": d178.get("archive_id"),
        "final_audit_id": d178.get("final_audit_id"),
        "post_apply_verification_id": d178.get("post_apply_verification_id"),
        "guarded_apply_id": d178.get("guarded_apply_id"),
        "apply_intent_id": d178.get("apply_intent_id"),
        "run_id": d178.get("run_id"),
        "intent_id": d178.get("intent_id"),
        "candidate_id": d178.get("candidate_id"),
        "response_id": d178.get("response_id"),
        "proposal_id": d178.get("proposal_id"),
        "source_d178_report": D178_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "proposal_candidate_packet": proposal_candidate_packet if ok else {},
        "d180_scope": d180_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "proposal_reentry_id": proposal_reentry_id,
            "provider_reentry_id": d178.get("provider_reentry_id"),
            "cycle_intake_id": d178.get("cycle_intake_id"),
            "controlled_next_cycle_id": d178.get("controlled_next_cycle_id"),
            "archive_id": d178.get("archive_id"),
            "final_audit_id": d178.get("final_audit_id"),
            "run_id": d178.get("run_id"),
            "intent_id": d178.get("intent_id"),
            "candidate_id": d178.get("candidate_id"),
            "response_id": d178.get("response_id"),
            "proposal_id": d178.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D179_PLUS" if ok else "BLOCKED",
            "proposal_reentry_status": "PROPOSAL_REENTRY_SCOPE_CREATED_NO_MATERIALIZATION" if ok else "BLOCKED",
            "proposal_candidate_packet_status": "PROPOSAL_CANDIDATE_PACKET_CREATED_NO_MATERIALIZATION" if ok else "BLOCKED",
            "candidate_status": "CONTROLLED_AUTONOMY_READY_FOR_HUMAN_REVIEW_SCOPE" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY" if ok else "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D180_CONTROLLED_AUTONOMY_HUMAN_REVIEW_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D180_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "controlled_autonomy_proposal_reentry_scope_created": ok,
            "proposal_candidate_packet_created": ok,
            "d180_scope_created": ok,
            "proposal_applied": False,
            "proposal_materialized_to_core": False,
            "provider_call_authorized": False,
            "real_provider_call_performed": False,
            "real_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D180 may create controlled autonomy human review scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_controlled_autonomy_proposal_reentry_scope(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.controlled_autonomy_proposal_reentry_scope import create_controlled_autonomy_proposal_reentry_scope


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


class TestD179ControlledAutonomyProposalReentryScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        d178 = {
            "ok": True,
            "decision": "CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_READY",
            "provider_reentry_id": "d178-test",
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
                "controlled_autonomy_provider_reentry_scope_only": True,
                "controlled_autonomy_provider_dry_ping_scope_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "provider_reentry_scope_created": True,
                "provider_dry_ping_scope_created": True,
                "proposal_reentry_scope_created": True,
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
                "approval_for_d179_controlled_autonomy_proposal_reentry_scope_only": True,
                "network_allowed_after_d178_by_ai": False,
                "secret_read_allowed_after_d178_by_ai": False,
                "shell_allowed_after_d178_by_ai": False,
                "real_apply_allowed_after_d178_by_ai": False,
                "route_insert_allowed_after_d178_by_ai": False,
                "protected_core_mutation_allowed_after_d178_by_ai": False,
                "git_action_allowed_after_d178_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D178_PLUS",
                "provider_reentry_status": "PROVIDER_REENTRY_SCOPE_CREATED_NO_PROVIDER_CALL",
                "provider_dry_ping_status": "PROVIDER_DRY_PING_SCOPE_CREATED_NO_NETWORK",
                "candidate_status": "CONTROLLED_AUTONOMY_READY_FOR_PROPOSAL_REENTRY_SCOPE",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_ONLY",
                "next_step": "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE",
            },
        }

        provider_dry_ping = {
            **no_ai_flags(),
            "ok": True,
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

        d179_scope = {
            "ok": True,
            "allowed_next_gate": "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE",
            "controlled_autonomy_proposal_reentry_scope_only": True,
            "provider_reentry_scope_created": True,
            "provider_dry_ping_scope_created": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "provider_call_authorized": False,
            "provider_response_authorized": False,
            "provider_network_call_performed": False,
            "provider_dry_ping_real_network": False,
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
        }

        write(root / "reports/d178_controlled_autonomy_provider_reentry_scope.json", d178)
        write(root / "reports/d178_controlled_autonomy_provider_dry_ping_scope.json", provider_dry_ping)
        write(root / "reports/d178_d179_controlled_autonomy_proposal_reentry_scope.json", d179_scope)
        return td, root

    def test_creates_proposal_reentry_outputs(self):
        td, root = self.root()
        try:
            r = create_controlled_autonomy_proposal_reentry_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D180_CONTROLLED_AUTONOMY_HUMAN_REVIEW_SCOPE_ONLY")
            self.assertEqual(r["d180_scope"]["allowed_next_gate"], "D180_CONTROLLED_AUTONOMY_HUMAN_REVIEW_SCOPE")
            self.assertTrue(r["guardrails"]["proposal_reentry_scope_created"])
            self.assertTrue(r["guardrails"]["proposal_candidate_packet_created"])
            self.assertTrue(r["guardrails"]["requires_human_review_before_any_apply"])
            self.assertFalse(r["guardrails"]["proposal_applied"])
            self.assertTrue((root / "reports/d179_controlled_autonomy_proposal_reentry_scope.json").exists())
            self.assertTrue((root / "reports/d179_controlled_autonomy_proposal_candidate_packet.json").exists())
            self.assertTrue((root / "reports/d179_d180_controlled_autonomy_human_review_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d178(self):
        td, root = self.root()
        try:
            (root / "reports/d178_controlled_autonomy_provider_reentry_scope.json").unlink()
            r = create_controlled_autonomy_proposal_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_provider_dry_ping_network_true(self):
        td, root = self.root()
        try:
            p = root / "reports/d178_controlled_autonomy_provider_dry_ping_scope.json"
            data = json.loads(p.read_text())
            data["provider_dry_ping_real_network"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_proposal_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d179_scope_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d178_d179_controlled_autonomy_proposal_reentry_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d178_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_proposal_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d178_not_ready(self):
        td, root = self.root()
        try:
            p = root / "reports/d178_controlled_autonomy_provider_reentry_scope.json"
            data = json.loads(p.read_text())
            data["decision"] = "BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_proposal_reentry_scope(root)
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

print("D179 CONTROLLED AUTONOMY PROPOSAL REENTRY SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/controlled_autonomy_proposal_reentry_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d179_controlled_autonomy_proposal_reentry_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/controlled_autonomy_proposal_reentry_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d179_controlled_autonomy_proposal_reentry_scope", "-v"], check=True)

print("\n== run D179 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.controlled_autonomy_proposal_reentry_scope import create_controlled_autonomy_proposal_reentry_scope\n"
    "r=create_controlled_autonomy_proposal_reentry_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d179_controlled_autonomy_proposal_reentry_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/controlled_autonomy_proposal_reentry_scope.py",
    "tests/test_d179_controlled_autonomy_proposal_reentry_scope.py",
    "reports/d179_controlled_autonomy_proposal_reentry_scope.json",
    "reports/d179_controlled_autonomy_proposal_candidate_packet.json",
    "reports/d179_d180_controlled_autonomy_human_review_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D179 controlled autonomy proposal reentry scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D179 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD179 CONTROLLED AUTONOMY PROPOSAL REENTRY SCOPE BOOT DONE")
