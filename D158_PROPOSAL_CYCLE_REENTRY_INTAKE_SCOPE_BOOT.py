#!/usr/bin/env python3
# D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_BOOT.py
# Installs canonical_guard_schema.py and creates D158 proposal cycle reentry intake scope.
# D158 keeps provider/proposal reentry dry only:
# no provider call, no network, no secret read, no shell, no apply, no route insert,
# no protected core mutation by AI, no git action by AI.
# Opens D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE only.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


CANONICAL_SCHEMA = r'''
from __future__ import annotations

from copy import deepcopy

CANONICAL_FALSE_FLAGS = [
    "external_ai_called",
    "network_accessed",
    "api_key_read",
    "secret_read",
    "shell_from_ai_executed",
    "shell_executed_by_ai",
    "runtime_code_mutated",
    "protected_core_mutated",
    "protected_core_mutated_by_ai",
    "canonical_memory_mutated",
    "actual_apply_executed",
    "actual_apply_executed_by_ai",
    "real_apply_executed_by_ai",
    "route_inserted",
    "route_inserted_by_ai",
    "git_commit_by_ai",
    "git_push_by_ai",
    "git_action_by_ai",
    "rollback_executed",
    "restore_executed",
]

SAFE_ALIAS_GROUPS = {
    "shell": ["shell_from_ai_executed", "shell_executed_by_ai"],
    "git": ["git_commit_by_ai", "git_push_by_ai", "git_action_by_ai"],
    "route": ["route_inserted", "route_inserted_by_ai"],
    "protected_core": ["protected_core_mutated", "protected_core_mutated_by_ai"],
    "apply": ["actual_apply_executed", "actual_apply_executed_by_ai", "real_apply_executed_by_ai"],
    "network": ["network_accessed"],
    "secret": ["secret_read", "api_key_read"],
}

def normalize_guard_flags(data, *, add_missing_aliases=True):
    item = deepcopy(data or {})
    if add_missing_aliases:
        for group in SAFE_ALIAS_GROUPS.values():
            if any(item.get(k) is True for k in group):
                continue
            for k in group:
                item.setdefault(k, False)
        for k in CANONICAL_FALSE_FLAGS:
            item.setdefault(k, False)
    return item

def validate_no_ai_execution(data, *, prefix="guard"):
    item = normalize_guard_flags(data)
    errors = []
    for k in CANONICAL_FALSE_FLAGS:
        if item.get(k) is not False:
            errors.append(f"{prefix}.{k} must be false")
    return errors

def build_no_touch_guardrails(**extra):
    base = {k: False for k in CANONICAL_FALSE_FLAGS}
    base.update({
        "canonical_guard_schema_applied": True,
        "missing_safe_aliases_normalized": True,
        "dangerous_true_flags_block": True,
    })
    base.update(extra)
    return normalize_guard_flags(base)

def canonical_schema_report():
    return {
        "state": "D158_CANONICAL_GUARD_SCHEMA",
        "ok": True,
        "schema_status": "CANONICAL_GUARD_SCHEMA_CREATED_FOR_D158_PLUS",
        "normalization_rule": "MISSING_SAFE_ALIASES_NORMALIZE_TO_FALSE_DANGEROUS_TRUE_FLAGS_BLOCK",
        "canonical_false_flags": CANONICAL_FALSE_FLAGS,
        "safe_alias_groups": SAFE_ALIAS_GROUPS,
    }
'''

MODULE = r'''
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from runtime_experimental.canonical_guard_schema import (
    canonical_schema_report,
    normalize_guard_flags,
    validate_no_ai_execution,
    build_no_touch_guardrails,
)

D157_REPORT = "reports/d157_provider_cycle_reentry_scope.json"
D157_CONFIG = "reports/d157_provider_reentry_config_manifest.json"
D157_DRY_PING = "reports/d157_provider_reentry_dry_ping_scope.json"
D157_D158_SCOPE = "reports/d157_d158_proposal_cycle_reentry_intake_scope.json"

CANONICAL_SCHEMA_OUT = "reports/d158_canonical_guard_schema.json"
OUT = "reports/d158_proposal_cycle_reentry_intake_scope.json"
INTAKE_MANIFEST_OUT = "reports/d158_proposal_reentry_intake_manifest.json"
NO_EXEC_ASSERTIONS_OUT = "reports/d158_proposal_reentry_no_execution_assertions.json"
D159_SCOPE_OUT = "reports/d158_d159_proposal_to_sandbox_candidate_reentry_scope.json"

REQ_D157_DECISION = "PROVIDER_CYCLE_REENTRY_SCOPE_READY"
REQ_D158_GATE = "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE"
REQ_D159_GATE = "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE"

STATUS_FALSE_D157 = [
    "real_apply_allowed_after_d157_by_ai",
    "route_insert_allowed_after_d157_by_ai",
    "protected_core_mutation_allowed_after_d157_by_ai",
    "network_allowed_after_d157_by_ai",
    "secret_read_allowed_after_d157_by_ai",
    "shell_allowed_after_d157_by_ai",
    "git_action_allowed_after_d157_by_ai",
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

def validate_d157(d157, config, dry_ping, d158_scope):
    errors = []
    if not d157:
        return ["missing D157 provider cycle reentry scope report"]

    if d157.get("ok") is not True:
        errors.append("D157 ok must be true")
    if d157.get("decision") != REQ_D157_DECISION:
        errors.append("D157 decision must be PROVIDER_CYCLE_REENTRY_SCOPE_READY")

    summary = d157.get("summary", {})
    expected = {
        "provider_reentry_status": "PROVIDER_REENTRY_CONFIG_CREATED_NO_NETWORK_NO_SECRET",
        "dry_ping_status": "DRY_PING_SCOPE_CREATED_PROVIDER_NOT_CALLED",
        "candidate_status": "NEXT_CYCLE_PROVIDER_REENTRY_READY_NO_PROVIDER_CALL",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_ONLY",
        "next_step": REQ_D158_GATE,
    }
    for k, v in expected.items():
        if summary.get(k) != v:
            errors.append(f"D157 summary.{k} must be {v}")

    guard = normalize_guard_flags(d157.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D157 guardrails"))
    for k in STATUS_FALSE_D157:
        if guard.get(k) is not False:
            errors.append(f"D157 guardrails.{k} must be false")
    for k in [
        "provider_cycle_reentry_scope_only",
        "provider_reentry_config_manifest_only",
        "provider_reentry_dry_ping_scope_only",
        "fresh_intent_required",
        "approval_for_d158_proposal_cycle_reentry_intake_scope_only",
    ]:
        if guard.get(k) is not True:
            errors.append(f"D157 guardrails.{k} must be true")
    for k in ["real_provider_call_performed", "provider_network_call_performed", "provider_secret_read_performed", "provider_response_ingested"]:
        if guard.get(k) is not False:
            errors.append(f"D157 guardrails.{k} must be false")

    if not config:
        errors.append("missing D157 provider reentry config manifest")
    else:
        if config.get("ok") is not True:
            errors.append("D157 config ok must be true")
        if config.get("provider_reentry_status") != "PROVIDER_REENTRY_CONFIG_CREATED_NO_NETWORK_NO_SECRET":
            errors.append("D157 config provider_reentry_status must be no-network/no-secret")
        for k in ["fresh_intent_required", "manual_provider_enable_required", "dry_ping_scope_required", "human_review_required"]:
            if config.get(k) is not True:
                errors.append(f"D157 config {k} must be true")
        for k in ["real_provider_call_performed", "provider_network_call_performed", "provider_secret_read_performed", "provider_response_ingested"]:
            if config.get(k) is not False:
                errors.append(f"D157 config {k} must be false")
        errors.extend(validate_no_ai_execution(config, prefix="D157 config"))

    if not dry_ping:
        errors.append("missing D157 provider reentry dry ping scope")
    else:
        if dry_ping.get("ok") is not True:
            errors.append("D157 dry ping ok must be true")
        if dry_ping.get("dry_ping_status") != "DRY_PING_SCOPE_CREATED_PROVIDER_NOT_CALLED":
            errors.append("D157 dry ping status must be provider-not-called")
        for k in ["dry_ping_executes_provider", "real_provider_call_performed", "network_accessed", "secret_read"]:
            if dry_ping.get(k) is not False:
                errors.append(f"D157 dry ping {k} must be false")
        errors.extend(validate_no_ai_execution(dry_ping, prefix="D157 dry_ping"))

    if not d158_scope:
        errors.append("missing D157 D158 proposal cycle reentry intake scope")
    else:
        if d158_scope.get("ok") is not True:
            errors.append("D157 D158 scope ok must be true")
        if d158_scope.get("allowed_next_gate") != REQ_D158_GATE:
            errors.append("D157 D158 scope allowed_next_gate must be D158")
        if d158_scope.get("proposal_cycle_reentry_intake_scope_only") is not True:
            errors.append("D157 D158 scope must be proposal-cycle-reentry-intake-only")
        if d158_scope.get("fresh_intent_required") is not True:
            errors.append("D157 D158 scope must require fresh intent")
        if d158_scope.get("provider_response_must_be_dry_or_manual") is not True:
            errors.append("D157 D158 scope provider response must be dry/manual")
        if d158_scope.get("human_review_required") is not True:
            errors.append("D157 D158 scope must require human review")
        for k in STATUS_FALSE_D157:
            if d158_scope.get(k) is not False:
                errors.append(f"D157 D158 scope {k} must be false")

    return errors

def build_intake_manifest(intake_id, d157):
    return normalize_guard_flags({
        "state": "D158_PROPOSAL_REENTRY_INTAKE_MANIFEST",
        "ok": True,
        "intake_id": intake_id,
        "reentry_id": d157.get("reentry_id"),
        "next_cycle_id": d157.get("next_cycle_id"),
        "cycle_closure_id": d157.get("cycle_closure_id"),
        "candidate_id": d157.get("candidate_id"),
        "proposal_id": d157.get("proposal_id"),
        "created_at": now(),
        "intake_mode": "PROPOSAL_REENTRY_INTAKE_MANIFEST_ONLY_NO_EXECUTION",
        "proposal_reentry_status": "PROPOSAL_REENTRY_INTAKE_CREATED_NO_PROVIDER_RESPONSE_NO_EXECUTION",
        "fresh_intent_required": True,
        "provider_response_required_before_candidate": True,
        "provider_response_ingested": False,
        "proposal_materialized": False,
        "candidate_created": False,
        "human_review_required": True,
    })

def build_no_execution_assertions(intake_id, d157):
    return normalize_guard_flags({
        "state": "D158_PROPOSAL_REENTRY_NO_EXECUTION_ASSERTIONS",
        "ok": True,
        "intake_id": intake_id,
        "reentry_id": d157.get("reentry_id"),
        "next_cycle_id": d157.get("next_cycle_id"),
        "created_at": now(),
        "assertion_mode": "PROPOSAL_REENTRY_NO_EXECUTION_ASSERTIONS",
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "proposal_materialized": False,
        "candidate_created": False,
        "no_network": True,
        "no_secret_read": True,
        "no_shell": True,
        "no_apply": True,
        "no_route_insert": True,
        "no_core_mutation_by_ai": True,
        "no_git_action_by_ai": True,
        "human_review_required": True,
    })

def build_d159_scope(intake_id, d157):
    return {
        "state": "D158_D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE",
        "ok": True,
        "intake_id": intake_id,
        "reentry_id": d157.get("reentry_id"),
        "next_cycle_id": d157.get("next_cycle_id"),
        "cycle_closure_id": d157.get("cycle_closure_id"),
        "candidate_id": d157.get("candidate_id"),
        "proposal_id": d157.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D159_GATE,
        "proposal_to_sandbox_candidate_reentry_scope_only": True,
        "fresh_intent_required": True,
        "provider_response_required_before_candidate": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d159_allowed_to_create": [
            "proposal_to_sandbox_candidate_reentry_scope",
            "sandbox_candidate_reentry_manifest",
            "sandbox_candidate_reentry_no_touch_assertions",
            "d160_sandbox_candidate_reentry_human_review_scope",
        ],
        "d159_must_not_execute": [
            "real_provider_call",
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
        "real_apply_allowed_after_d158_by_ai": False,
        "route_insert_allowed_after_d158_by_ai": False,
        "protected_core_mutation_allowed_after_d158_by_ai": False,
        "network_allowed_after_d158_by_ai": False,
        "secret_read_allowed_after_d158_by_ai": False,
        "shell_allowed_after_d158_by_ai": False,
        "git_action_allowed_after_d158_by_ai": False,
    }

def create_proposal_cycle_reentry_intake_scope(root="."):
    root = Path(root).resolve()

    d157 = read_json(root / D157_REPORT, {}) or {}
    config = read_json(root / D157_CONFIG, {}) or {}
    dry_ping = read_json(root / D157_DRY_PING, {}) or {}
    d158_scope = read_json(root / D157_D158_SCOPE, {}) or {}

    errors = validate_d157(d157, config, dry_ping, d158_scope)

    intake_id = "d158-" + digest({
        "reentry_id": d157.get("reentry_id"),
        "next_cycle_id": d157.get("next_cycle_id"),
        "candidate_id": d157.get("candidate_id"),
        "proposal_id": d157.get("proposal_id"),
    })

    schema_report = canonical_schema_report()
    intake_manifest = build_intake_manifest(intake_id, d157)
    assertions = build_no_execution_assertions(intake_id, d157)
    d159_scope = build_d159_scope(intake_id, d157)

    for name, item in [("intake_manifest", intake_manifest), ("assertions", assertions)]:
        errors.extend(validate_no_ai_execution(item, prefix=name))
        for k in ["real_provider_call_performed", "provider_response_ingested", "proposal_materialized", "candidate_created"]:
            if item.get(k) is not False:
                errors.append(f"{name}.{k} must be false")

    for k in [
        "real_apply_allowed_after_d158_by_ai",
        "route_insert_allowed_after_d158_by_ai",
        "protected_core_mutation_allowed_after_d158_by_ai",
        "network_allowed_after_d158_by_ai",
        "secret_read_allowed_after_d158_by_ai",
        "shell_allowed_after_d158_by_ai",
        "git_action_allowed_after_d158_by_ai",
    ]:
        if d159_scope.get(k) is not False:
            errors.append(f"d159_scope.{k} must be false")

    ok = not errors
    decision = "PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_READY" if ok else "PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_BLOCKED"
    result = "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_CREATED" if ok else "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_BLOCKED"

    if ok:
        write_json(root / CANONICAL_SCHEMA_OUT, schema_report)
        write_json(root / INTAKE_MANIFEST_OUT, intake_manifest)
        write_json(root / NO_EXEC_ASSERTIONS_OUT, assertions)
        write_json(root / D159_SCOPE_OUT, d159_scope)

    report = {
        "state": "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "intake_id": intake_id,
        "reentry_id": d157.get("reentry_id"),
        "next_cycle_id": d157.get("next_cycle_id"),
        "cycle_closure_id": d157.get("cycle_closure_id"),
        "candidate_id": d157.get("candidate_id"),
        "proposal_id": d157.get("proposal_id"),
        "source_d157_report": D157_REPORT,
        "canonical_guard_schema": schema_report if ok else {},
        "proposal_reentry_intake_manifest": intake_manifest if ok else {},
        "proposal_reentry_no_execution_assertions": assertions if ok else {},
        "d159_scope": d159_scope if ok else {},
        "guardrails": build_no_touch_guardrails(
            proposal_cycle_reentry_intake_scope_only=True,
            proposal_reentry_intake_manifest_only=True,
            proposal_reentry_no_execution_assertions_only=True,
            canonical_guard_schema_applied=True,
            fresh_intent_required=True,
            provider_response_ingested=False,
            proposal_materialized=False,
            candidate_created=False,
            approval_for_d159_proposal_to_sandbox_candidate_reentry_scope_only=ok,
            real_apply_allowed_after_d158_by_ai=False,
            route_insert_allowed_after_d158_by_ai=False,
            protected_core_mutation_allowed_after_d158_by_ai=False,
            network_allowed_after_d158_by_ai=False,
            secret_read_allowed_after_d158_by_ai=False,
            shell_allowed_after_d158_by_ai=False,
            git_action_allowed_after_d158_by_ai=False,
        ),
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "intake_id": intake_id,
            "reentry_id": d157.get("reentry_id"),
            "next_cycle_id": d157.get("next_cycle_id"),
            "candidate_id": d157.get("candidate_id"),
            "proposal_id": d157.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_CREATED_FOR_D158_PLUS" if ok else "BLOCKED",
            "proposal_reentry_status": "PROPOSAL_REENTRY_INTAKE_CREATED_NO_PROVIDER_RESPONSE_NO_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "PROPOSAL_REENTRY_READY_FOR_SANDBOX_CANDIDATE_REENTRY_NOT_CREATED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D159_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "proposal_cycle_reentry_intake_scope_created": ok,
            "canonical_guard_schema_created": ok,
            "proposal_reentry_intake_manifest_created": ok,
            "proposal_reentry_no_execution_assertions_created": ok,
            "d159_scope_created": ok,
            "provider_response_ingested": False,
            "candidate_created": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D159 may create proposal to sandbox candidate reentry scope only.",
        },
    }

    write_json(root / OUT, report)
    return report

if __name__ == "__main__":
    print(json.dumps(create_proposal_cycle_reentry_intake_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.proposal_cycle_reentry_intake_scope import create_proposal_cycle_reentry_intake_scope
from runtime_experimental.canonical_guard_schema import normalize_guard_flags

def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")

class TestD158ProposalCycleReentryIntakeScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        reentry_id = "d157-test"
        next_cycle_id = "d156-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d157 = {
            "ok": True,
            "decision": "PROVIDER_CYCLE_REENTRY_SCOPE_READY",
            "reentry_id": reentry_id,
            "next_cycle_id": next_cycle_id,
            "cycle_closure_id": "d155-test",
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": {
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
                "real_provider_call_performed": False,
                "provider_network_call_performed": False,
                "provider_secret_read_performed": False,
                "provider_response_ingested": False,
                "provider_cycle_reentry_scope_only": True,
                "provider_reentry_config_manifest_only": True,
                "provider_reentry_dry_ping_scope_only": True,
                "fresh_intent_required": True,
                "approval_for_d158_proposal_cycle_reentry_intake_scope_only": True,
                "real_apply_allowed_after_d157_by_ai": False,
                "route_insert_allowed_after_d157_by_ai": False,
                "protected_core_mutation_allowed_after_d157_by_ai": False,
                "network_allowed_after_d157_by_ai": False,
                "secret_read_allowed_after_d157_by_ai": False,
                "shell_allowed_after_d157_by_ai": False,
                "git_action_allowed_after_d157_by_ai": False,
            },
            "summary": {
                "provider_reentry_status": "PROVIDER_REENTRY_CONFIG_CREATED_NO_NETWORK_NO_SECRET",
                "dry_ping_status": "DRY_PING_SCOPE_CREATED_PROVIDER_NOT_CALLED",
                "candidate_status": "NEXT_CYCLE_PROVIDER_REENTRY_READY_NO_PROVIDER_CALL",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_ONLY",
                "next_step": "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE",
            },
        }

        config = {
            "ok": True,
            "provider_reentry_status": "PROVIDER_REENTRY_CONFIG_CREATED_NO_NETWORK_NO_SECRET",
            "fresh_intent_required": True,
            "manual_provider_enable_required": True,
            "dry_ping_scope_required": True,
            "human_review_required": True,
            "real_provider_call_performed": False,
            "provider_network_call_performed": False,
            "provider_secret_read_performed": False,
            "provider_response_ingested": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
        }

        dry_ping = {
            "ok": True,
            "dry_ping_status": "DRY_PING_SCOPE_CREATED_PROVIDER_NOT_CALLED",
            "dry_ping_executes_provider": False,
            "real_provider_call_performed": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
        }

        d158_scope = {
            "ok": True,
            "allowed_next_gate": "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE",
            "proposal_cycle_reentry_intake_scope_only": True,
            "fresh_intent_required": True,
            "provider_response_must_be_dry_or_manual": True,
            "human_review_required": True,
            "real_apply_allowed_after_d157_by_ai": False,
            "route_insert_allowed_after_d157_by_ai": False,
            "protected_core_mutation_allowed_after_d157_by_ai": False,
            "network_allowed_after_d157_by_ai": False,
            "secret_read_allowed_after_d157_by_ai": False,
            "shell_allowed_after_d157_by_ai": False,
            "git_action_allowed_after_d157_by_ai": False,
        }

        write(root / "reports/d157_provider_cycle_reentry_scope.json", d157)
        write(root / "reports/d157_provider_reentry_config_manifest.json", config)
        write(root / "reports/d157_provider_reentry_dry_ping_scope.json", dry_ping)
        write(root / "reports/d157_d158_proposal_cycle_reentry_intake_scope.json", d158_scope)
        return td, root

    def test_creates_proposal_cycle_reentry_intake_outputs(self):
        td, root = self.root()
        try:
            r = create_proposal_cycle_reentry_intake_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE_ONLY")
            self.assertTrue(r["guardrails"]["canonical_guard_schema_applied"])
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["route_inserted_by_ai"])
            self.assertEqual(r["d159_scope"]["allowed_next_gate"], "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE")
            self.assertTrue((root / "reports/d158_canonical_guard_schema.json").exists())
            self.assertTrue((root / "reports/d158_proposal_cycle_reentry_intake_scope.json").exists())
            self.assertTrue((root / "reports/d158_proposal_reentry_intake_manifest.json").exists())
            self.assertTrue((root / "reports/d158_proposal_reentry_no_execution_assertions.json").exists())
            self.assertTrue((root / "reports/d158_d159_proposal_to_sandbox_candidate_reentry_scope.json").exists())
        finally:
            td.cleanup()

    def test_canonical_schema_normalizes_missing_safe_aliases(self):
        d = normalize_guard_flags({"network_accessed": False})
        self.assertFalse(d["route_inserted_by_ai"])
        self.assertFalse(d["protected_core_mutated_by_ai"])
        self.assertFalse(d["shell_executed_by_ai"])
        self.assertFalse(d["git_action_by_ai"])

    def test_blocks_missing_d157(self):
        td, root = self.root()
        try:
            (root / "reports/d157_provider_cycle_reentry_scope.json").unlink()
            r = create_proposal_cycle_reentry_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d157_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d157_provider_cycle_reentry_scope.json"
            data = json.loads(p.read_text())
            data["guardrails"]["network_allowed_after_d157_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_proposal_cycle_reentry_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_dry_ping_executes_provider(self):
        td, root = self.root()
        try:
            p = root / "reports/d157_provider_reentry_dry_ping_scope.json"
            data = json.loads(p.read_text())
            data["dry_ping_executes_provider"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_proposal_cycle_reentry_intake_scope(root)
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

print("D158 PROPOSAL CYCLE REENTRY INTAKE SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/canonical_guard_schema.py").write_text(CANONICAL_SCHEMA, encoding="utf-8")
Path("runtime_experimental/proposal_cycle_reentry_intake_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d158_proposal_cycle_reentry_intake_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/canonical_guard_schema.py"], check=True)
sh([sys.executable, "-m", "py_compile", "runtime_experimental/proposal_cycle_reentry_intake_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d158_proposal_cycle_reentry_intake_scope", "-v"], check=True)

print("\n== run D158 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.proposal_cycle_reentry_intake_scope import create_proposal_cycle_reentry_intake_scope\n"
    "r=create_proposal_cycle_reentry_intake_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d158_proposal_cycle_reentry_intake_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/canonical_guard_schema.py",
    "runtime_experimental/proposal_cycle_reentry_intake_scope.py",
    "tests/test_d158_proposal_cycle_reentry_intake_scope.py",
    "reports/d158_canonical_guard_schema.json",
    "reports/d158_proposal_cycle_reentry_intake_scope.json",
    "reports/d158_proposal_reentry_intake_manifest.json",
    "reports/d158_proposal_reentry_no_execution_assertions.json",
    "reports/d158_d159_proposal_to_sandbox_candidate_reentry_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D158 proposal cycle reentry intake scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D158 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD158 PROPOSAL CYCLE REENTRY INTAKE SCOPE BOOT DONE")
