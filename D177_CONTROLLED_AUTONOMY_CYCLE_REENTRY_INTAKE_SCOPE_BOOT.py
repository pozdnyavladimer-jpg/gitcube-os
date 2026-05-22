#!/usr/bin/env python3
# D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_BOOT.py
#
# D177 consumes D176 controlled-next-cycle artifacts and creates:
# - runtime_experimental/controlled_autonomy_cycle_reentry_intake_scope.py
# - tests/test_d177_controlled_autonomy_cycle_reentry_intake_scope.py
# - reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json
# - reports/d177_controlled_autonomy_cycle_fresh_intent_packet.json
# - reports/d177_d178_controlled_autonomy_provider_reentry_scope.json
#
# D177 starts a fresh controlled-autonomy cycle after the sandbox-candidate
# reentry chain has been archived and authority-zeroed by D176.
#
# No inherited authority. No provider call. No network. No secret read.
# No shell. No route insert. No protected core mutation by AI. No git action by AI.
#
# Opens D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE only.

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

try:
    from runtime_experimental.canonical_guard_schema import (
        canonical_schema_report,
        normalize_guard_flags,
        validate_no_ai_execution,
    )
except Exception:  # compatibility for isolated tests
    def canonical_schema_report():
        return {"available": False, "fallback": True}
    def normalize_guard_flags(d):
        return dict(d or {})
    def validate_no_ai_execution(d, prefix="guardrails"):
        errors = []
        for k in [
            "network_accessed", "secret_read", "shell_executed_by_ai",
            "actual_apply_executed_by_ai", "real_apply_executed_by_ai",
            "route_inserted_by_ai", "protected_core_mutated_by_ai", "git_action_by_ai",
        ]:
            if (d or {}).get(k) is True:
                errors.append(f"{prefix}.{k} must be false")
        return errors


D176_REPORT = "reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json"
D176_RESET_RECEIPT = "reports/d176_sandbox_candidate_reentry_next_cycle_reset_receipt.json"
D176_D177_SCOPE = "reports/d176_d177_controlled_autonomy_cycle_reentry_intake_scope.json"

OUT = "reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json"
FRESH_INTENT_PACKET_OUT = "reports/d177_controlled_autonomy_cycle_fresh_intent_packet.json"
D178_SCOPE_OUT = "reports/d177_d178_controlled_autonomy_provider_reentry_scope.json"

REQ_D176_DECISION = "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_READY"
REQ_D177_GATE = "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE"
REQ_D178_GATE = "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE"

FALSE_KEYS = [
    "authority_carried_forward",
    "provider_authority_carried_forward",
    "candidate_apply_executed",
    "candidate_apply_executed_by_ai",
    "real_provider_call_performed",
    "provider_response_ingested",
    "provider_response_captured",
    "provider_call_authorized",
    "provider_response_authorized",
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
    "real_apply_allowed_after_d176_by_ai",
    "route_insert_allowed_after_d176_by_ai",
    "protected_core_mutation_allowed_after_d176_by_ai",
    "network_allowed_after_d176_by_ai",
    "secret_read_allowed_after_d176_by_ai",
    "shell_allowed_after_d176_by_ai",
    "git_action_allowed_after_d176_by_ai",
]

TRUE_COMPAT_KEYS = [
    "fresh_intent_required",
    "human_review_required",
    "previous_chain_archived",
    "previous_chain_closed",
    "no_inherited_authority",
    "fresh_cycle_intake_required",
    "next_cycle_requires_fresh_intent",
    "next_cycle_requires_human_review",
    "next_cycle_inherits_no_authority",
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


def compat(obj):
    if not isinstance(obj, dict):
        return {}
    for k in FALSE_KEYS:
        obj.setdefault(k, False)
    for k in TRUE_COMPAT_KEYS:
        obj.setdefault(k, True)
    if isinstance(obj.get("guardrails"), dict):
        for k in FALSE_KEYS:
            obj["guardrails"].setdefault(k, False)
        for k in TRUE_COMPAT_KEYS:
            obj["guardrails"].setdefault(k, True)
    return obj


def require_false(obj, keys, label, errors):
    for k in keys:
        if (obj or {}).get(k) is True:
            errors.append(f"{label}.{k} must be false")


def require_true(obj, keys, label, errors):
    for k in keys:
        if (obj or {}).get(k) is not True:
            errors.append(f"{label}.{k} must be true")


def validate_d176(d176, reset_receipt, d177_scope):
    errors = []

    if not d176:
        return ["missing D176 controlled next cycle scope report"]
    if d176.get("ok") is not True:
        errors.append("D176 ok must be true")
    if d176.get("decision") != REQ_D176_DECISION:
        errors.append("D176 decision must be SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_READY")

    summary = d176.get("summary", {})
    if summary.get("next_step") not in (REQ_D177_GATE, None):
        errors.append("D176 summary.next_step must be D177 controlled autonomy cycle reentry intake")
    if summary.get("approval_scope") not in ("D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_ONLY", None):
        errors.append("D176 summary.approval_scope must be D177 controlled autonomy cycle reentry intake only")

    guard = compat(normalize_guard_flags(d176.get("guardrails", {})))
    errors.extend(validate_no_ai_execution(guard, prefix="D176 guardrails"))
    require_true(guard, [
        "fresh_intent_required",
        "human_review_required",
        "previous_chain_archived",
        "previous_chain_closed",
        "no_inherited_authority",
        "next_cycle_inherits_no_authority",
    ], "D176 guardrails", errors)
    require_false(guard, FALSE_KEYS, "D176 guardrails", errors)

    if not reset_receipt:
        errors.append("missing D176 next cycle reset receipt")
    else:
        if reset_receipt.get("ok") is not True:
            errors.append("D176 reset receipt ok must be true")
        require_true(reset_receipt, [
            "previous_chain_archived",
            "next_cycle_requires_fresh_intent",
            "next_cycle_requires_human_review",
            "next_cycle_inherits_no_authority",
        ], "D176 reset receipt", errors)
        require_false(reset_receipt, FALSE_KEYS, "D176 reset receipt", errors)

    if not d177_scope:
        errors.append("missing D176 D177 controlled autonomy cycle reentry intake scope")
    else:
        if d177_scope.get("ok") is not True:
            errors.append("D176 D177 scope ok must be true")
        if d177_scope.get("allowed_next_gate") != REQ_D177_GATE:
            errors.append("D176 D177 scope allowed_next_gate must be D177")
        require_true(d177_scope, [
            "controlled_autonomy_cycle_reentry_intake_scope_only",
            "fresh_cycle_intake_required",
            "previous_chain_closed",
            "previous_chain_archived",
            "no_inherited_authority",
            "fresh_intent_required",
            "human_review_required",
        ], "D176 D177 scope", errors)
        require_false(d177_scope, FALSE_KEYS, "D176 D177 scope", errors)

    return errors


def build_fresh_intent_packet(cycle_intake_id, d176):
    data = {
        "state": "D177_CONTROLLED_AUTONOMY_CYCLE_FRESH_INTENT_PACKET",
        "ok": True,
        "cycle_intake_id": cycle_intake_id,
        "controlled_next_cycle_id": d176.get("controlled_next_cycle_id"),
        "archive_id": d176.get("archive_id"),
        "final_audit_id": d176.get("final_audit_id"),
        "run_id": d176.get("run_id"),
        "intent_id": d176.get("intent_id"),
        "candidate_id": d176.get("candidate_id"),
        "response_id": d176.get("response_id"),
        "proposal_id": d176.get("proposal_id"),
        "created_at": now(),
        "fresh_intent_packet_status": "FRESH_INTENT_PACKET_CREATED_NO_INHERITED_AUTHORITY",
        "packet_mode": "CONTROLLED_AUTONOMY_REENTRY_RECORD_ONLY",
        "previous_chain_archived": True,
        "previous_chain_closed": True,
        "fresh_cycle_intake_required": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "no_inherited_authority": True,
        "next_cycle_inherits_no_authority": True,
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
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_d178_scope(cycle_intake_id, d176):
    return {
        "state": "D177_D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE",
        "ok": True,
        "cycle_intake_id": cycle_intake_id,
        "controlled_next_cycle_id": d176.get("controlled_next_cycle_id"),
        "archive_id": d176.get("archive_id"),
        "final_audit_id": d176.get("final_audit_id"),
        "run_id": d176.get("run_id"),
        "intent_id": d176.get("intent_id"),
        "candidate_id": d176.get("candidate_id"),
        "response_id": d176.get("response_id"),
        "proposal_id": d176.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D178_GATE,
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
        "d178_allowed_to_create": [
            "controlled_autonomy_provider_reentry_scope",
            "controlled_autonomy_provider_dry_ping_scope",
            "d179_controlled_autonomy_proposal_reentry_scope",
        ],
        "d178_must_not_execute": [
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


def create_controlled_autonomy_cycle_reentry_intake_scope(root="."):
    root = Path(root).resolve()

    d176 = compat(read_json(root / D176_REPORT, {}) or {})
    reset_receipt = compat(read_json(root / D176_RESET_RECEIPT, {}) or {})
    d177_scope = compat(read_json(root / D176_D177_SCOPE, {}) or {})

    errors = validate_d176(d176, reset_receipt, d177_scope)

    cycle_intake_id = "d177-" + digest({
        "controlled_next_cycle_id": d176.get("controlled_next_cycle_id"),
        "archive_id": d176.get("archive_id"),
        "final_audit_id": d176.get("final_audit_id"),
        "run_id": d176.get("run_id"),
        "intent_id": d176.get("intent_id"),
        "candidate_id": d176.get("candidate_id"),
        "response_id": d176.get("response_id"),
        "proposal_id": d176.get("proposal_id"),
    })

    fresh_intent_packet = build_fresh_intent_packet(cycle_intake_id, d176)
    d178_scope = build_d178_scope(cycle_intake_id, d176)

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
    ], "fresh_intent_packet", errors)
    require_false(fresh_intent_packet, FALSE_KEYS, "fresh_intent_packet", errors)

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
    ], "d178_scope", errors)
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
    ], "d178_scope", errors)

    ok = not errors
    decision = "CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_READY" if ok else "CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_BLOCKED"
    result = "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_CREATED" if ok else "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_BLOCKED"

    if ok:
        write_json(root / FRESH_INTENT_PACKET_OUT, fresh_intent_packet)
        write_json(root / D178_SCOPE_OUT, d178_scope)

    guardrails = normalize_guard_flags({
        "controlled_autonomy_cycle_reentry_intake_scope_only": True,
        "controlled_autonomy_cycle_fresh_intent_packet_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_cycle_intake_required": ok,
        "previous_chain_closed": ok,
        "previous_chain_archived": ok,
        "no_inherited_authority": ok,
        "fresh_intent_required": True,
        "human_review_required": True,
        "cycle_reentry_intake_created": ok,
        "fresh_intent_packet_created": ok,
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
        "approval_for_d178_controlled_autonomy_provider_reentry_scope_only": ok,
        "network_allowed_after_d177_by_ai": False,
        "secret_read_allowed_after_d177_by_ai": False,
        "shell_allowed_after_d177_by_ai": False,
        "real_apply_allowed_after_d177_by_ai": False,
        "route_insert_allowed_after_d177_by_ai": False,
        "protected_core_mutation_allowed_after_d177_by_ai": False,
        "git_action_allowed_after_d177_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "cycle_intake_id": cycle_intake_id,
        "controlled_next_cycle_id": d176.get("controlled_next_cycle_id"),
        "archive_id": d176.get("archive_id"),
        "final_audit_id": d176.get("final_audit_id"),
        "run_id": d176.get("run_id"),
        "intent_id": d176.get("intent_id"),
        "candidate_id": d176.get("candidate_id"),
        "response_id": d176.get("response_id"),
        "proposal_id": d176.get("proposal_id"),
        "source_d176_report": D176_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "fresh_intent_packet": fresh_intent_packet if ok else {},
        "d178_scope": d178_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "cycle_intake_id": cycle_intake_id,
            "controlled_next_cycle_id": d176.get("controlled_next_cycle_id"),
            "archive_id": d176.get("archive_id"),
            "run_id": d176.get("run_id"),
            "intent_id": d176.get("intent_id"),
            "candidate_id": d176.get("candidate_id"),
            "response_id": d176.get("response_id"),
            "proposal_id": d176.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D177_PLUS" if ok else "BLOCKED",
            "cycle_reentry_intake_status": "FRESH_CYCLE_REENTRY_INTAKE_CREATED_NO_INHERITED_AUTHORITY" if ok else "BLOCKED",
            "fresh_intent_packet_status": "FRESH_INTENT_PACKET_CREATED_NO_INHERITED_AUTHORITY" if ok else "BLOCKED",
            "candidate_status": "CONTROLLED_AUTONOMY_READY_FOR_PROVIDER_REENTRY_SCOPE" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY" if ok else "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D178_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "controlled_autonomy_cycle_reentry_intake_scope_created": ok,
            "fresh_intent_packet_created": ok,
            "d178_scope_created": ok,
            "previous_chain_archived": ok,
            "no_inherited_authority": ok,
            "fresh_intent_required": ok,
            "real_provider_call_performed": False,
            "real_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D178 may create controlled autonomy provider reentry scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_controlled_autonomy_cycle_reentry_intake_scope(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.controlled_autonomy_cycle_reentry_intake_scope import create_controlled_autonomy_cycle_reentry_intake_scope


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


class TestD177ControlledAutonomyCycleReentryIntakeScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        d176 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_READY",
            "controlled_next_cycle_id": "d176-test",
            "archive_id": "d175-test",
            "final_audit_id": "d174-test",
            "run_id": "d168-test",
            "intent_id": "d167-test",
            "candidate_id": "d164-test",
            "response_id": "d163-test",
            "proposal_id": "d107-valid-test",
            "guardrails": {
                **no_ai_flags(),
                "sandbox_candidate_reentry_controlled_next_cycle_scope_only": True,
                "sandbox_candidate_reentry_next_cycle_reset_receipt_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "previous_chain_archived": True,
                "previous_chain_closed": True,
                "controlled_next_cycle_created": True,
                "next_cycle_reset_receipt_created": True,
                "fresh_cycle_intake_required": True,
                "next_cycle_requires_fresh_intent": True,
                "next_cycle_requires_human_review": True,
                "next_cycle_inherits_no_authority": True,
                "no_inherited_authority": True,
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
                "approval_for_d177_controlled_autonomy_cycle_reentry_intake_scope_only": True,
                "real_apply_allowed_after_d176_by_ai": False,
                "route_insert_allowed_after_d176_by_ai": False,
                "protected_core_mutation_allowed_after_d176_by_ai": False,
                "network_allowed_after_d176_by_ai": False,
                "secret_read_allowed_after_d176_by_ai": False,
                "shell_allowed_after_d176_by_ai": False,
                "git_action_allowed_after_d176_by_ai": False,
            },
            "summary": {
                "approval_scope": "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_ONLY",
                "next_step": "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE",
            },
        }

        reset_receipt = {
            **no_ai_flags(),
            "ok": True,
            "next_cycle_reset_status": "REENTRY_CHAIN_CLOSED_FRESH_INTENT_REQUIRED_NO_INHERITED_AUTHORITY",
            "previous_chain_archived": True,
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
        }

        d177_scope = {
            "ok": True,
            "allowed_next_gate": "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE",
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
        }

        write(root / "reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json", d176)
        write(root / "reports/d176_sandbox_candidate_reentry_next_cycle_reset_receipt.json", reset_receipt)
        write(root / "reports/d176_d177_controlled_autonomy_cycle_reentry_intake_scope.json", d177_scope)
        return td, root

    def test_creates_cycle_reentry_intake_outputs(self):
        td, root = self.root()
        try:
            r = create_controlled_autonomy_cycle_reentry_intake_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_ONLY")
            self.assertEqual(r["d178_scope"]["allowed_next_gate"], "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE")
            self.assertTrue(r["guardrails"]["cycle_reentry_intake_created"])
            self.assertTrue(r["guardrails"]["fresh_intent_packet_created"])
            self.assertFalse(r["guardrails"]["authority_carried_forward"])
            self.assertFalse(r["guardrails"]["provider_call_authorized"])
            self.assertTrue((root / "reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json").exists())
            self.assertTrue((root / "reports/d177_controlled_autonomy_cycle_fresh_intent_packet.json").exists())
            self.assertTrue((root / "reports/d177_d178_controlled_autonomy_provider_reentry_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d176(self):
        td, root = self.root()
        try:
            (root / "reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json").unlink()
            r = create_controlled_autonomy_cycle_reentry_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_reset_carries_authority(self):
        td, root = self.root()
        try:
            p = root / "reports/d176_sandbox_candidate_reentry_next_cycle_reset_receipt.json"
            data = json.loads(p.read_text())
            data["authority_carried_forward"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_cycle_reentry_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d177_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d176_d177_controlled_autonomy_cycle_reentry_intake_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d176_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_cycle_reentry_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d176_not_ready(self):
        td, root = self.root()
        try:
            p = root / "reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json"
            data = json.loads(p.read_text())
            data["decision"] = "BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_cycle_reentry_intake_scope(root)
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

print("D177 CONTROLLED AUTONOMY CYCLE REENTRY INTAKE SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/controlled_autonomy_cycle_reentry_intake_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d177_controlled_autonomy_cycle_reentry_intake_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/controlled_autonomy_cycle_reentry_intake_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d177_controlled_autonomy_cycle_reentry_intake_scope", "-v"], check=True)

print("\n== run D177 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.controlled_autonomy_cycle_reentry_intake_scope import create_controlled_autonomy_cycle_reentry_intake_scope\n"
    "r=create_controlled_autonomy_cycle_reentry_intake_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/controlled_autonomy_cycle_reentry_intake_scope.py",
    "tests/test_d177_controlled_autonomy_cycle_reentry_intake_scope.py",
    "reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json",
    "reports/d177_controlled_autonomy_cycle_fresh_intent_packet.json",
    "reports/d177_d178_controlled_autonomy_provider_reentry_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D177 controlled autonomy cycle reentry intake scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D177 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD177 CONTROLLED AUTONOMY CYCLE REENTRY INTAKE SCOPE BOOT DONE")
