#!/usr/bin/env python3
# D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_BOOT.py
#
# D137 consumes D136 execution-preflight artifacts and creates:
# - runtime_experimental/sandbox_candidate_controlled_execution_scope.py
# - tests/test_d137_sandbox_candidate_controlled_execution_scope.py
# - reports/d137_sandbox_candidate_controlled_execution_scope.json
# - reports/d137_sandbox_candidate_controlled_execution_receipt.json
# - reports/d137_sandbox_candidate_no_apply_guard.json
# - reports/d137_d138_sandbox_candidate_human_execution_intent_scope.json
#
# CONTROLLED EXECUTION SCOPE ONLY:
# no candidate execution yet, no apply, no shell, no network, no secret read,
# no route insert, no protected core mutation, no AI git action.
#
# D137 opens D138 Human Execution Intent Scope.

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

D136_REPORT = "reports/d136_sandbox_candidate_execution_preflight_scope.json"
D136_PREFLIGHT_REPORT = "reports/d136_sandbox_candidate_execution_preflight_report.json"
D136_EXECUTION_BLOCKERS = "reports/d136_sandbox_candidate_execution_blockers.json"
D136_D137_SCOPE = "reports/d136_d137_sandbox_candidate_controlled_execution_scope.json"

OUT = "reports/d137_sandbox_candidate_controlled_execution_scope.json"
CONTROLLED_EXECUTION_RECEIPT_OUT = "reports/d137_sandbox_candidate_controlled_execution_receipt.json"
NO_APPLY_GUARD_OUT = "reports/d137_sandbox_candidate_no_apply_guard.json"
D138_SCOPE_OUT = "reports/d137_d138_sandbox_candidate_human_execution_intent_scope.json"

REQ_D136_DECISION = "SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_READY"
REQ_D137_GATE = "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE"
REQ_D138_GATE = "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE"
REQ_D136_APPROVAL_SCOPE = "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_ONLY"

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
CRITICAL_BLOCKERS = [
    "real_apply_by_ai",
    "auto_apply",
    "route_insert_by_ai",
    "protected_core_mutation_by_ai",
    "canonical_memory_overwrite_by_ai",
    "shell_exec_from_ai",
    "git_commit_by_ai",
    "git_push_by_ai",
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


def _paths_from_preflight(preflight_report):
    paths = []
    if not isinstance(preflight_report, dict):
        return paths
    for key in ["materialized_paths", "candidate_files", "files"]:
        value = preflight_report.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    paths.append(item)
                elif isinstance(item, dict):
                    p = item.get("path") or item.get("file") or item.get("name")
                    if p:
                        paths.append(str(p))
    return paths


def validate_d136(d136, preflight_report, execution_blockers, d137_scope):
    errors = []

    if not d136:
        errors.append("missing D136 sandbox candidate execution preflight scope report")
        return errors

    if d136.get("ok") is not True:
        errors.append("D136 ok must be true")
    if d136.get("decision") != REQ_D136_DECISION:
        errors.append("D136 decision must be SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_READY")

    guard = d136.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D136 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_execution_preflight_scope_only",
        "execution_preflight_report_only",
        "execution_blockers_only",
        "approval_for_d137_controlled_execution_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D136 guardrails.{key} must be true")

    for key in [
        "candidate_executed_now",
        "approval_for_real_apply_by_ai",
        "approval_for_route_insert_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D136 guardrails.{key} must be false")

    summary = d136.get("summary", {})
    expected = {
        "execution_preflight_status": "PREFLIGHT_PASS_NO_EXECUTION",
        "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "candidate_execution_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": REQ_D136_APPROVAL_SCOPE,
        "next_step": REQ_D137_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D136 summary.{key} must be {value}")

    if not preflight_report:
        errors.append("missing D136 execution preflight report")
    else:
        if preflight_report.get("ok") is not True:
            errors.append("D136 preflight report ok must be true")
        if preflight_report.get("preflight_mode") != "EXECUTION_PREFLIGHT_ONLY_NO_CANDIDATE_EXECUTION":
            errors.append("D136 preflight mode must be no-candidate-execution")
        if preflight_report.get("candidate_status") != "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED":
            errors.append("D136 preflight candidate_status must be materialized validated not executed")
        for key in [
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "network_accessed",
            "api_key_read",
            "secret_read",
        ]:
            if preflight_report.get(key) is not False:
                errors.append(f"D136 preflight report {key} must be false")
        for check in preflight_report.get("required_checks", []):
            if check.get("status") != "PREFLIGHT_PASS":
                errors.append(f"D136 preflight required check failed: {check.get('name')}")
        paths = _paths_from_preflight(preflight_report)
        if not paths:
            errors.append("D136 preflight report must include materialized paths")
        for p in paths:
            if not p.startswith(EXPECTED_SANDBOX_PREFIX):
                errors.append(f"D136 materialized path must stay inside sandbox: {p}")

    if not execution_blockers:
        errors.append("missing D136 execution blockers")
    else:
        if execution_blockers.get("ok") is not True:
            errors.append("D136 execution blockers ok must be true")
        if execution_blockers.get("blocker_mode") != "DECLARE_EXECUTION_BOUNDARIES_NO_EXECUTION":
            errors.append("D136 blockers mode must declare boundaries with no execution")
        still_blocked = execution_blockers.get("still_blocked", [])
        for blocker in CRITICAL_BLOCKERS:
            if blocker not in still_blocked:
                errors.append(f"D136 execution blockers missing {blocker}")
        for key in [
            "candidate_execution_performed",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
        ]:
            if execution_blockers.get(key) is not False:
                errors.append(f"D136 execution blockers {key} must be false")

    if not d137_scope:
        errors.append("missing D136 D137 controlled execution scope")
    else:
        if d137_scope.get("ok") is not True:
            errors.append("D136 D137 scope ok must be true")
        if d137_scope.get("allowed_next_gate") != REQ_D137_GATE:
            errors.append("D136 D137 scope allowed_next_gate must be D137")
        if d137_scope.get("sandbox_candidate_controlled_execution_scope_only") is not True:
            errors.append("D136 D137 scope must be controlled execution scope only")
        if d137_scope.get("human_review_required") is not True:
            errors.append("D136 D137 scope must require human review")
        for key in [
            "candidate_executed_after_d136_by_ai",
            "real_apply_allowed_after_d136_by_ai",
            "route_insert_allowed_after_d136_by_ai",
            "protected_core_mutation_allowed_after_d136_by_ai",
        ]:
            if d137_scope.get(key) is not False:
                errors.append(f"D136 D137 scope {key} must be false")

    return errors


def build_controlled_execution_receipt(scope_id, d136, preflight_report):
    paths = _paths_from_preflight(preflight_report)
    return {
        "state": "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RECEIPT",
        "ok": True,
        "scope_id": scope_id,
        "preflight_id": d136.get("preflight_id"),
        "validation_id": d136.get("validation_id"),
        "candidate_id": d136.get("candidate_id"),
        "proposal_id": d136.get("proposal_id"),
        "created_at": now(),
        "receipt_mode": "CONTROLLED_EXECUTION_SCOPE_RECEIPT_NO_EXECUTION",
        "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
        "materialized_paths": paths,
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


def build_no_apply_guard(scope_id, d136):
    return {
        "state": "D137_SANDBOX_CANDIDATE_NO_APPLY_GUARD",
        "ok": True,
        "scope_id": scope_id,
        "preflight_id": d136.get("preflight_id"),
        "candidate_id": d136.get("candidate_id"),
        "created_at": now(),
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


def build_d138_scope(scope_id, d136):
    return {
        "state": "D137_D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE",
        "ok": True,
        "scope_id": scope_id,
        "preflight_id": d136.get("preflight_id"),
        "validation_id": d136.get("validation_id"),
        "write_materialization_id": d136.get("write_materialization_id"),
        "materialization_id": d136.get("materialization_id"),
        "static_validation_id": d136.get("static_validation_id"),
        "write_once_id": d136.get("write_once_id"),
        "window_id": d136.get("window_id"),
        "runner_id": d136.get("runner_id"),
        "plan_id": d136.get("plan_id"),
        "review_id": d136.get("review_id"),
        "candidate_id": d136.get("candidate_id"),
        "intake_id": d136.get("intake_id"),
        "ping_id": d136.get("ping_id"),
        "config_id": d136.get("config_id"),
        "dashboard_id": d136.get("dashboard_id"),
        "adapter_id": d136.get("adapter_id"),
        "seal_id": d136.get("seal_id"),
        "proposal_id": d136.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D138_GATE,
        "d138_allowed_to_create": [
            "sandbox_candidate_human_execution_intent_scope",
            "sandbox_candidate_human_execution_intent_record",
            "d139_sandbox_candidate_execute_once_scope",
        ],
        "d138_must_not_execute": [
            "execute_sandbox_candidate_without_human_phrase",
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
        "sandbox_candidate_human_execution_intent_scope_only": True,
        "human_review_required": True,
        "candidate_executed_after_d137_by_ai": False,
        "real_apply_allowed_after_d137_by_ai": False,
        "route_insert_allowed_after_d137_by_ai": False,
        "protected_core_mutation_allowed_after_d137_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_ONLY",
    }


def create_sandbox_candidate_controlled_execution_scope(root="."):
    root = Path(root).resolve()

    d136 = read_json(root / D136_REPORT, {}) or {}
    preflight_report = read_json(root / D136_PREFLIGHT_REPORT, {}) or {}
    execution_blockers = read_json(root / D136_EXECUTION_BLOCKERS, {}) or {}
    d137_scope = read_json(root / D136_D137_SCOPE, {}) or {}

    errors = validate_d136(d136, preflight_report, execution_blockers, d137_scope)

    scope_id = "d137-" + digest({
        "preflight_id": d136.get("preflight_id"),
        "validation_id": d136.get("validation_id"),
        "candidate_id": d136.get("candidate_id"),
        "proposal_id": d136.get("proposal_id"),
    })

    receipt = build_controlled_execution_receipt(scope_id, d136, preflight_report)
    no_apply_guard = build_no_apply_guard(scope_id, d136)
    d138_scope = build_d138_scope(scope_id, d136)

    for item_name, item in [("receipt", receipt), ("no_apply_guard", no_apply_guard)]:
        for key in [
            "candidate_executed_now",
            "candidate_execution_performed",
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
    decision = "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_BLOCKED"
    result = "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_CREATED" if ok else "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_BLOCKED"

    if ok:
        write_json(root / CONTROLLED_EXECUTION_RECEIPT_OUT, receipt)
        write_json(root / NO_APPLY_GUARD_OUT, no_apply_guard)
        write_json(root / D138_SCOPE_OUT, d138_scope)

    report = {
        "state": "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "scope_id": scope_id,
        "preflight_id": d136.get("preflight_id"),
        "validation_id": d136.get("validation_id"),
        "write_materialization_id": d136.get("write_materialization_id"),
        "materialization_id": d136.get("materialization_id"),
        "static_validation_id": d136.get("static_validation_id"),
        "write_once_id": d136.get("write_once_id"),
        "window_id": d136.get("window_id"),
        "runner_id": d136.get("runner_id"),
        "plan_id": d136.get("plan_id"),
        "review_id": d136.get("review_id"),
        "candidate_id": d136.get("candidate_id"),
        "intake_id": d136.get("intake_id"),
        "ping_id": d136.get("ping_id"),
        "config_id": d136.get("config_id"),
        "dashboard_id": d136.get("dashboard_id"),
        "adapter_id": d136.get("adapter_id"),
        "seal_id": d136.get("seal_id"),
        "proposal_id": d136.get("proposal_id"),
        "source_d136_report": D136_REPORT,
        "sandbox_candidate_controlled_execution_receipt": receipt if ok else {},
        "sandbox_candidate_no_apply_guard": no_apply_guard if ok else {},
        "d138_scope": d138_scope if ok else {},
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
            "sandbox_candidate_controlled_execution_scope_only": True,
            "controlled_execution_receipt_only": True,
            "no_apply_guard_only": True,
            "candidate_executed_now": False,
            "approval_for_d138_human_execution_intent_scope_only": ok,
            "approval_for_candidate_execution": False,
            "approval_for_real_apply_by_ai": False,
            "approval_for_route_insert_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "scope_id": scope_id,
            "preflight_id": d136.get("preflight_id"),
            "validation_id": d136.get("validation_id"),
            "candidate_id": d136.get("candidate_id"),
            "adapter_id": d136.get("adapter_id"),
            "seal_id": d136.get("seal_id"),
            "proposal_id": d136.get("proposal_id"),
            "controlled_execution_scope_status": "CONTROLLED_EXECUTION_SCOPE_DECLARED_NO_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "candidate_execution_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D138_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_controlled_execution_scope_created": ok,
            "sandbox_candidate_controlled_execution_receipt_created": ok,
            "sandbox_candidate_no_apply_guard_created": ok,
            "d138_scope_created": ok,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D138 may create human execution intent scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_controlled_execution_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_controlled_execution_scope import create_sandbox_candidate_controlled_execution_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD137SandboxCandidateControlledExecutionScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        preflight_id = "d136-test"
        validation_id = "d135-test"
        candidate_id = "d126-test"
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

        d136 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_READY",
            "preflight_id": preflight_id,
            "validation_id": validation_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_execution_preflight_scope_only": True,
                "execution_preflight_report_only": True,
                "execution_blockers_only": True,
                "candidate_executed_now": False,
                "approval_for_d137_controlled_execution_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "approval_for_route_insert_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "execution_preflight_status": "PREFLIGHT_PASS_NO_EXECUTION",
                "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_ONLY",
                "next_step": "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE",
            },
        }

        base = f"runtime_experimental/ai_sandbox_work/{candidate_id}"
        preflight_report = {
            "ok": True,
            "preflight_id": preflight_id,
            "candidate_id": candidate_id,
            "preflight_mode": "EXECUTION_PREFLIGHT_ONLY_NO_CANDIDATE_EXECUTION",
            "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
            "materialized_paths": [
                f"{base}/candidate_manifest.json",
                f"{base}/candidate_summary.md",
                f"{base}/candidate_payload.json",
            ],
            "required_checks": [
                {"name": "required_file_candidate_manifest.json", "status": "PREFLIGHT_PASS"},
                {"name": "required_file_candidate_summary.md", "status": "PREFLIGHT_PASS"},
                {"name": "required_file_candidate_payload.json", "status": "PREFLIGHT_PASS"},
            ],
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
        }

        execution_blockers = {
            "ok": True,
            "preflight_id": preflight_id,
            "candidate_id": candidate_id,
            "blocker_mode": "DECLARE_EXECUTION_BOUNDARIES_NO_EXECUTION",
            "still_blocked": [
                "real_apply_by_ai",
                "auto_apply",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "shell_exec_from_ai",
                "git_commit_by_ai",
                "git_push_by_ai",
                "network_provider_call_by_ai",
                "secret_read_by_ai",
            ],
            "candidate_execution_performed": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
        }

        d137_scope = {
            "ok": True,
            "preflight_id": preflight_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE",
            "sandbox_candidate_controlled_execution_scope_only": True,
            "human_review_required": True,
            "candidate_executed_after_d136_by_ai": False,
            "real_apply_allowed_after_d136_by_ai": False,
            "route_insert_allowed_after_d136_by_ai": False,
            "protected_core_mutation_allowed_after_d136_by_ai": False,
        }

        write(root / "reports/d136_sandbox_candidate_execution_preflight_scope.json", d136)
        write(root / "reports/d136_sandbox_candidate_execution_preflight_report.json", preflight_report)
        write(root / "reports/d136_sandbox_candidate_execution_blockers.json", execution_blockers)
        write(root / "reports/d136_d137_sandbox_candidate_controlled_execution_scope.json", d137_scope)
        return td, root

    def test_creates_controlled_execution_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_controlled_execution_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_READY")
            self.assertEqual(r["summary"]["controlled_execution_scope_status"], "CONTROLLED_EXECUTION_SCOPE_DECLARED_NO_EXECUTION")
            self.assertEqual(r["summary"]["approval_scope"], "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d138_scope"]["allowed_next_gate"], "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE")
            self.assertTrue((root / "reports/d137_sandbox_candidate_controlled_execution_scope.json").exists())
            self.assertTrue((root / "reports/d137_sandbox_candidate_controlled_execution_receipt.json").exists())
            self.assertTrue((root / "reports/d137_sandbox_candidate_no_apply_guard.json").exists())
            self.assertTrue((root / "reports/d137_d138_sandbox_candidate_human_execution_intent_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d136(self):
        td, root = self.root()
        try:
            (root / "reports/d136_sandbox_candidate_execution_preflight_scope.json").unlink()
            r = create_sandbox_candidate_controlled_execution_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_preflight_says_candidate_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d136_sandbox_candidate_execution_preflight_report.json"
            data = json.loads(p.read_text())
            data["candidate_executed_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_controlled_execution_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_blocker_missing_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d136_sandbox_candidate_execution_blockers.json"
            data = json.loads(p.read_text())
            data["still_blocked"].remove("real_apply_by_ai")
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_controlled_execution_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d137_scope_allows_protected_core_mutation(self):
        td, root = self.root()
        try:
            p = root / "reports/d136_d137_sandbox_candidate_controlled_execution_scope.json"
            data = json.loads(p.read_text())
            data["protected_core_mutation_allowed_after_d136_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_controlled_execution_scope(root)
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

print("D137 SANDBOX CANDIDATE CONTROLLED EXECUTION SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_controlled_execution_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d137_sandbox_candidate_controlled_execution_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_controlled_execution_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d137_sandbox_candidate_controlled_execution_scope", "-v"], check=True)

print("\n== run D137 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_controlled_execution_scope import create_sandbox_candidate_controlled_execution_scope\n"
    "r=create_sandbox_candidate_controlled_execution_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d137_sandbox_candidate_controlled_execution_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_controlled_execution_scope.py",
    "tests/test_d137_sandbox_candidate_controlled_execution_scope.py",
    "reports/d137_sandbox_candidate_controlled_execution_scope.json",
    "reports/d137_sandbox_candidate_controlled_execution_receipt.json",
    "reports/d137_sandbox_candidate_no_apply_guard.json",
    "reports/d137_d138_sandbox_candidate_human_execution_intent_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D137 sandbox candidate controlled execution scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D137 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD137 SANDBOX CANDIDATE CONTROLLED EXECUTION SCOPE BOOT DONE")
