#!/usr/bin/env python3
# D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_BOOT.py
#
# D138 consumes D137 controlled-execution-scope artifacts and creates:
# - runtime_experimental/sandbox_candidate_human_execution_intent_scope.py
# - tests/test_d138_sandbox_candidate_human_execution_intent_scope.py
# - reports/d138_sandbox_candidate_human_execution_intent_scope.json
# - reports/d138_sandbox_candidate_human_execution_intent_record.json
# - reports/d138_sandbox_candidate_execution_authority_guard.json
# - reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json
#
# HUMAN EXECUTION INTENT SCOPE ONLY:
# no candidate execution yet, no apply, no shell, no network, no secret read,
# no route insert, no protected core mutation, no AI git action.
#
# D138 opens D139 Controlled Sandbox Candidate Execution Run Scope.

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

D137_REPORT = "reports/d137_sandbox_candidate_controlled_execution_scope.json"
D137_RECEIPT = "reports/d137_sandbox_candidate_controlled_execution_receipt.json"
D137_NO_APPLY_GUARD = "reports/d137_sandbox_candidate_no_apply_guard.json"
D137_D138_SCOPE = "reports/d137_d138_sandbox_candidate_human_execution_intent_scope.json"

OUT = "reports/d138_sandbox_candidate_human_execution_intent_scope.json"
HUMAN_INTENT_RECORD_OUT = "reports/d138_sandbox_candidate_human_execution_intent_record.json"
EXECUTION_AUTHORITY_GUARD_OUT = "reports/d138_sandbox_candidate_execution_authority_guard.json"
D139_SCOPE_OUT = "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json"

REQ_D137_DECISION = "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_READY"
REQ_D138_GATE = "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE"
REQ_D139_GATE = "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE"
REQ_D137_APPROVAL_SCOPE = "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_ONLY"
REQ_D139_APPROVAL_SCOPE = "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_ONLY"
REQ_OPERATOR_PHRASE = "APPROVE_D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_ONLY"

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

EXPECTED_SANDBOX_PREFIX = "runtime_experimental/ai_sandbox_work/"
BLOCKED_NON_EXEC_ACTIONS = [
    "real_apply_by_ai",
    "auto_apply",
    "route_insert_by_ai",
    "protected_core_mutation_by_ai",
    "canonical_memory_overwrite_by_ai",
    "shell_exec_from_ai",
    "git_commit_by_ai",
    "git_push_by_ai",
    "rollback_execute_by_ai",
    "restore_execute_by_ai",
    "network_provider_call_by_ai",
    "secret_read_by_ai",
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


def _paths_from_receipt(receipt):
    paths = []
    for item in receipt.get("materialized_paths", []):
        if isinstance(item, str):
            paths.append(item)
        elif isinstance(item, dict):
            p = item.get("path") or item.get("file") or item.get("name")
            if p:
                paths.append(str(p))
    return paths


def validate_d137(d137, receipt, no_apply_guard, d138_scope):
    errors = []

    if not d137:
        errors.append("missing D137 sandbox candidate controlled execution scope report")
        return errors

    if d137.get("ok") is not True:
        errors.append("D137 ok must be true")
    if d137.get("decision") != REQ_D137_DECISION:
        errors.append("D137 decision must be SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_READY")

    guard = d137.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D137 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_controlled_execution_scope_only",
        "controlled_execution_receipt_only",
        "no_apply_guard_only",
        "approval_for_d138_human_execution_intent_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D137 guardrails.{key} must be true")

    for key in [
        "candidate_executed_now",
        "approval_for_candidate_execution",
        "approval_for_real_apply_by_ai",
        "approval_for_route_insert_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D137 guardrails.{key} must be false")

    summary = d137.get("summary", {})
    expected = {
        "controlled_execution_scope_status": "CONTROLLED_EXECUTION_SCOPE_DECLARED_NO_EXECUTION",
        "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "candidate_execution_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": REQ_D137_APPROVAL_SCOPE,
        "next_step": REQ_D138_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D137 summary.{key} must be {value}")

    if not receipt:
        errors.append("missing D137 controlled execution receipt")
    else:
        if receipt.get("ok") is not True:
            errors.append("D137 receipt ok must be true")
        if receipt.get("receipt_mode") != "CONTROLLED_EXECUTION_SCOPE_RECEIPT_NO_EXECUTION":
            errors.append("D137 receipt must be no-execution receipt")
        if receipt.get("candidate_status") != "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED":
            errors.append("D137 receipt candidate_status must be materialized validated not executed")
        if receipt.get("allowed_execution_zone") != "SANDBOX_ONLY_AFTER_HUMAN_EXECUTION_INTENT":
            errors.append("D137 receipt allowed_execution_zone must require human execution intent")
        for key in [
            "candidate_execution_performed",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "network_accessed",
            "api_key_read",
            "secret_read",
        ]:
            if receipt.get(key) is not False:
                errors.append(f"D137 receipt {key} must be false")
        paths = _paths_from_receipt(receipt)
        if not paths:
            errors.append("D137 receipt must include materialized paths")
        for p in paths:
            if not p.startswith(EXPECTED_SANDBOX_PREFIX):
                errors.append(f"D137 materialized path must stay inside sandbox: {p}")

    if not no_apply_guard:
        errors.append("missing D137 no-apply guard")
    else:
        if no_apply_guard.get("ok") is not True:
            errors.append("D137 no-apply guard ok must be true")
        if no_apply_guard.get("guard_mode") != "NO_APPLY_NO_ROUTE_NO_PROTECTED_MUTATION_GUARD":
            errors.append("D137 no-apply guard mode mismatch")
        for action in BLOCKED_NON_EXEC_ACTIONS:
            if action not in no_apply_guard.get("blocked_actions", []):
                errors.append(f"D137 no-apply guard missing blocked action: {action}")
        for key in [
            "candidate_execution_allowed_now",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
        ]:
            if no_apply_guard.get(key) is not False:
                errors.append(f"D137 no-apply guard {key} must be false")

    if not d138_scope:
        errors.append("missing D137 D138 human execution intent scope")
    else:
        if d138_scope.get("ok") is not True:
            errors.append("D137 D138 scope ok must be true")
        if d138_scope.get("allowed_next_gate") != REQ_D138_GATE:
            errors.append("D137 D138 scope allowed_next_gate must be D138")
        if d138_scope.get("sandbox_candidate_human_execution_intent_scope_only") is not True:
            errors.append("D137 D138 scope must be human execution intent scope only")
        if d138_scope.get("human_review_required") is not True:
            errors.append("D137 D138 scope must require human review")
        for key in [
            "candidate_executed_after_d137_by_ai",
            "real_apply_allowed_after_d137_by_ai",
            "route_insert_allowed_after_d137_by_ai",
            "protected_core_mutation_allowed_after_d137_by_ai",
        ]:
            if d138_scope.get(key) is not False:
                errors.append(f"D137 D138 scope {key} must be false")

    return errors


def build_human_execution_intent_record(intent_id, d137, receipt):
    return {
        "state": "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_RECORD",
        "ok": True,
        "intent_id": intent_id,
        "scope_id": d137.get("scope_id"),
        "preflight_id": d137.get("preflight_id"),
        "validation_id": d137.get("validation_id"),
        "candidate_id": d137.get("candidate_id"),
        "proposal_id": d137.get("proposal_id"),
        "created_at": now(),
        "record_mode": "HUMAN_EXECUTION_INTENT_RECORD_ONLY_NO_EXECUTION",
        "operator_decision": "PENDING_HUMAN_EXECUTION_INTENT_FOR_D139",
        "required_phrase_for_d139": REQ_OPERATOR_PHRASE,
        "approved_for_d139_controlled_execution_run_scope_only": True,
        "approved_for_sandbox_candidate_execution_now": False,
        "approved_for_real_apply": False,
        "approved_for_route_insert": False,
        "approved_for_protected_core_mutation": False,
        "approved_for_git_action_by_ai": False,
        "materialized_paths": _paths_from_receipt(receipt),
        "candidate_execution_performed_now": False,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "human_review_required": True,
    }


def build_execution_authority_guard(intent_id, d137):
    return {
        "state": "D138_SANDBOX_CANDIDATE_EXECUTION_AUTHORITY_GUARD",
        "ok": True,
        "intent_id": intent_id,
        "scope_id": d137.get("scope_id"),
        "candidate_id": d137.get("candidate_id"),
        "created_at": now(),
        "guard_mode": "HUMAN_INTENT_REQUIRED_SANDBOX_EXECUTION_ONLY_NO_APPLY",
        "allowed_after_d138": [
            "create_d139_controlled_execution_run_scope",
            "prepare_sandbox_only_execution_command",
        ],
        "still_blocked": BLOCKED_NON_EXEC_ACTIONS,
        "sandbox_execution_allowed_now": False,
        "sandbox_execution_allowed_next_gate_only": True,
        "candidate_execution_performed_now": False,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
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


def build_d139_scope(intent_id, d137):
    return {
        "state": "D138_D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE",
        "ok": True,
        "intent_id": intent_id,
        "scope_id": d137.get("scope_id"),
        "preflight_id": d137.get("preflight_id"),
        "validation_id": d137.get("validation_id"),
        "write_materialization_id": d137.get("write_materialization_id"),
        "materialization_id": d137.get("materialization_id"),
        "static_validation_id": d137.get("static_validation_id"),
        "write_once_id": d137.get("write_once_id"),
        "window_id": d137.get("window_id"),
        "runner_id": d137.get("runner_id"),
        "plan_id": d137.get("plan_id"),
        "review_id": d137.get("review_id"),
        "candidate_id": d137.get("candidate_id"),
        "intake_id": d137.get("intake_id"),
        "ping_id": d137.get("ping_id"),
        "config_id": d137.get("config_id"),
        "dashboard_id": d137.get("dashboard_id"),
        "adapter_id": d137.get("adapter_id"),
        "seal_id": d137.get("seal_id"),
        "proposal_id": d137.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D139_GATE,
        "d139_allowed_to_create": [
            "sandbox_candidate_controlled_execution_run_scope",
            "sandbox_candidate_execution_command_packet",
            "sandbox_candidate_execution_result",
            "d140_sandbox_candidate_post_execution_verification_scope",
        ],
        "d139_allowed_to_execute": [
            "sandbox_candidate_preview_only_inside_runtime_experimental_ai_sandbox_work",
        ],
        "d139_must_not_execute": [
            "real_apply_by_ai",
            "auto_apply",
            "route_insert_by_ai",
            "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai",
            "shell_exec_from_ai_outside_declared_runner",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute_by_ai",
            "restore_execute_by_ai",
            "network_provider_call_by_ai",
            "secret_read_by_ai",
        ],
        "sandbox_candidate_controlled_execution_run_scope_only": True,
        "human_review_required": True,
        "candidate_execution_allowed_after_d138_only_in_sandbox": True,
        "candidate_executed_after_d138_by_ai": False,
        "real_apply_allowed_after_d138_by_ai": False,
        "route_insert_allowed_after_d138_by_ai": False,
        "protected_core_mutation_allowed_after_d138_by_ai": False,
        "required_phrase_for_later_gate": REQ_OPERATOR_PHRASE,
    }


def create_sandbox_candidate_human_execution_intent_scope(root="."):
    root = Path(root).resolve()

    d137 = read_json(root / D137_REPORT, {}) or {}
    receipt = read_json(root / D137_RECEIPT, {}) or {}
    no_apply_guard = read_json(root / D137_NO_APPLY_GUARD, {}) or {}
    d138_scope = read_json(root / D137_D138_SCOPE, {}) or {}

    errors = validate_d137(d137, receipt, no_apply_guard, d138_scope)

    intent_id = "d138-" + digest({
        "scope_id": d137.get("scope_id"),
        "preflight_id": d137.get("preflight_id"),
        "candidate_id": d137.get("candidate_id"),
        "proposal_id": d137.get("proposal_id"),
    })

    human_intent_record = build_human_execution_intent_record(intent_id, d137, receipt)
    execution_authority_guard = build_execution_authority_guard(intent_id, d137)
    d139_scope = build_d139_scope(intent_id, d137)

    for item_name, item in [
        ("human_intent_record", human_intent_record),
        ("execution_authority_guard", execution_authority_guard),
    ]:
        for key in [
            "candidate_execution_performed_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "network_accessed",
            "api_key_read",
            "secret_read",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
        ]:
            if item.get(key) is True:
                errors.append(f"{item_name} {key} must not be true")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_BLOCKED"
    result = "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_CREATED" if ok else "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_BLOCKED"

    if ok:
        write_json(root / HUMAN_INTENT_RECORD_OUT, human_intent_record)
        write_json(root / EXECUTION_AUTHORITY_GUARD_OUT, execution_authority_guard)
        write_json(root / D139_SCOPE_OUT, d139_scope)

    report = {
        "state": "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "intent_id": intent_id,
        "scope_id": d137.get("scope_id"),
        "preflight_id": d137.get("preflight_id"),
        "validation_id": d137.get("validation_id"),
        "write_materialization_id": d137.get("write_materialization_id"),
        "materialization_id": d137.get("materialization_id"),
        "static_validation_id": d137.get("static_validation_id"),
        "write_once_id": d137.get("write_once_id"),
        "window_id": d137.get("window_id"),
        "runner_id": d137.get("runner_id"),
        "plan_id": d137.get("plan_id"),
        "review_id": d137.get("review_id"),
        "candidate_id": d137.get("candidate_id"),
        "intake_id": d137.get("intake_id"),
        "ping_id": d137.get("ping_id"),
        "config_id": d137.get("config_id"),
        "dashboard_id": d137.get("dashboard_id"),
        "adapter_id": d137.get("adapter_id"),
        "seal_id": d137.get("seal_id"),
        "proposal_id": d137.get("proposal_id"),
        "source_d137_report": D137_REPORT,
        "sandbox_candidate_human_execution_intent_record": human_intent_record if ok else {},
        "sandbox_candidate_execution_authority_guard": execution_authority_guard if ok else {},
        "d139_scope": d139_scope if ok else {},
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
            "sandbox_candidate_human_execution_intent_scope_only": True,
            "human_execution_intent_record_only": True,
            "execution_authority_guard_only": True,
            "candidate_executed_now": False,
            "approval_for_d139_controlled_execution_run_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "approval_for_route_insert_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "intent_id": intent_id,
            "scope_id": d137.get("scope_id"),
            "preflight_id": d137.get("preflight_id"),
            "candidate_id": d137.get("candidate_id"),
            "adapter_id": d137.get("adapter_id"),
            "seal_id": d137.get("seal_id"),
            "proposal_id": d137.get("proposal_id"),
            "human_execution_intent_status": "HUMAN_INTENT_RECORD_CREATED_NO_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "candidate_execution_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": REQ_D139_APPROVAL_SCOPE if ok else "BLOCKED",
            "required_phrase_for_d139": REQ_OPERATOR_PHRASE,
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D139_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_human_execution_intent_scope_created": ok,
            "sandbox_candidate_human_execution_intent_record_created": ok,
            "sandbox_candidate_execution_authority_guard_created": ok,
            "d139_scope_created": ok,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D139 may perform controlled sandbox candidate execution only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_human_execution_intent_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_human_execution_intent_scope import create_sandbox_candidate_human_execution_intent_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD138SandboxCandidateHumanExecutionIntentScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        scope_id = "d137-test"
        preflight_id = "d136-test"
        validation_id = "d135-test"
        write_materialization_id = "d134-test"
        materialization_id = "d133-test"
        static_validation_id = "d132-test"
        write_once_id = "d131-test"
        window_id = "d130-test"
        runner_id = "d129-test"
        plan_id = "d128-test"
        review_id = "d127-test"
        candidate_id = "d126-test"
        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        false_guard = {
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
        }

        d137 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_READY",
            "scope_id": scope_id,
            "preflight_id": preflight_id,
            "validation_id": validation_id,
            "write_materialization_id": write_materialization_id,
            "materialization_id": materialization_id,
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "adapter_id": adapter_id,
            "seal_id": seal_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_controlled_execution_scope_only": True,
                "controlled_execution_receipt_only": True,
                "no_apply_guard_only": True,
                "candidate_executed_now": False,
                "approval_for_d138_human_execution_intent_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "approval_for_route_insert_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "controlled_execution_scope_status": "CONTROLLED_EXECUTION_SCOPE_DECLARED_NO_EXECUTION",
                "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_ONLY",
                "next_step": "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE",
            },
        }

        receipt = {
            "ok": True,
            "scope_id": scope_id,
            "preflight_id": preflight_id,
            "candidate_id": candidate_id,
            "receipt_mode": "CONTROLLED_EXECUTION_SCOPE_RECEIPT_NO_EXECUTION",
            "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
            "materialized_paths": [
                f"runtime_experimental/ai_sandbox_work/{candidate_id}/candidate_manifest.json",
                f"runtime_experimental/ai_sandbox_work/{candidate_id}/candidate_summary.md",
                f"runtime_experimental/ai_sandbox_work/{candidate_id}/candidate_payload.json",
            ],
            "allowed_execution_zone": "SANDBOX_ONLY_AFTER_HUMAN_EXECUTION_INTENT",
            "candidate_execution_performed": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "human_review_required": True,
        }

        no_apply_guard = {
            "ok": True,
            "scope_id": scope_id,
            "candidate_id": candidate_id,
            "guard_mode": "NO_APPLY_NO_ROUTE_NO_PROTECTED_MUTATION_GUARD",
            "blocked_actions": [
                "real_apply_by_ai",
                "auto_apply",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "shell_exec_from_ai",
                "git_commit_by_ai",
                "git_push_by_ai",
                "rollback_execute_by_ai",
                "restore_execute_by_ai",
                "network_provider_call_by_ai",
                "secret_read_by_ai",
            ],
            "candidate_execution_allowed_now": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "human_review_required": True,
        }

        d138_scope = {
            "ok": True,
            "scope_id": scope_id,
            "preflight_id": preflight_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE",
            "sandbox_candidate_human_execution_intent_scope_only": True,
            "human_review_required": True,
            "candidate_executed_after_d137_by_ai": False,
            "real_apply_allowed_after_d137_by_ai": False,
            "route_insert_allowed_after_d137_by_ai": False,
            "protected_core_mutation_allowed_after_d137_by_ai": False,
        }

        write(root / "reports/d137_sandbox_candidate_controlled_execution_scope.json", d137)
        write(root / "reports/d137_sandbox_candidate_controlled_execution_receipt.json", receipt)
        write(root / "reports/d137_sandbox_candidate_no_apply_guard.json", no_apply_guard)
        write(root / "reports/d137_d138_sandbox_candidate_human_execution_intent_scope.json", d138_scope)
        return td, root

    def test_creates_human_execution_intent_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_human_execution_intent_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_READY")
            self.assertEqual(r["summary"]["human_execution_intent_status"], "HUMAN_INTENT_RECORD_CREATED_NO_EXECUTION")
            self.assertEqual(r["summary"]["approval_scope"], "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d139_scope"]["allowed_next_gate"], "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE")
            self.assertTrue((root / "reports/d138_sandbox_candidate_human_execution_intent_scope.json").exists())
            self.assertTrue((root / "reports/d138_sandbox_candidate_human_execution_intent_record.json").exists())
            self.assertTrue((root / "reports/d138_sandbox_candidate_execution_authority_guard.json").exists())
            self.assertTrue((root / "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d137(self):
        td, root = self.root()
        try:
            (root / "reports/d137_sandbox_candidate_controlled_execution_scope.json").unlink()
            r = create_sandbox_candidate_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_receipt_says_candidate_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d137_sandbox_candidate_controlled_execution_receipt.json"
            data = json.loads(p.read_text())
            data["candidate_executed_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_no_apply_guard_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d137_sandbox_candidate_no_apply_guard.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d138_scope_allows_protected_core_mutation(self):
        td, root = self.root()
        try:
            p = root / "reports/d137_d138_sandbox_candidate_human_execution_intent_scope.json"
            data = json.loads(p.read_text())
            data["protected_core_mutation_allowed_after_d137_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_execution_intent_scope(root)
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

print("D138 SANDBOX CANDIDATE HUMAN EXECUTION INTENT SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_human_execution_intent_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d138_sandbox_candidate_human_execution_intent_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_human_execution_intent_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d138_sandbox_candidate_human_execution_intent_scope", "-v"], check=True)

print("\n== run D138 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_human_execution_intent_scope import create_sandbox_candidate_human_execution_intent_scope\n"
    "r=create_sandbox_candidate_human_execution_intent_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d138_sandbox_candidate_human_execution_intent_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_human_execution_intent_scope.py",
    "tests/test_d138_sandbox_candidate_human_execution_intent_scope.py",
    "reports/d138_sandbox_candidate_human_execution_intent_scope.json",
    "reports/d138_sandbox_candidate_human_execution_intent_record.json",
    "reports/d138_sandbox_candidate_execution_authority_guard.json",
    "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D138 sandbox candidate human execution intent scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D138 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD138 SANDBOX CANDIDATE HUMAN EXECUTION INTENT SCOPE BOOT DONE")
