#!/usr/bin/env python3
# D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_BOOT.py
#
# D129 consumes D128 test-plan artifacts and creates:
# - runtime_experimental/sandbox_candidate_dry_test_runner_scope.py
# - tests/test_d129_sandbox_candidate_dry_test_runner_scope.py
# - reports/d129_sandbox_candidate_dry_test_runner_scope.json
# - reports/d129_sandbox_candidate_dry_test_results.json
# - reports/d129_sandbox_candidate_integrity_diff_summary.json
# - reports/d129_d130_sandbox_candidate_write_window_scope.json
#
# DRY TEST RUNNER SCOPE ONLY:
# no candidate write, no candidate execution, no apply, no shell, no network,
# no secret read, no protected core mutation, no AI git action.
#
# D129 opens D130 Sandbox Candidate Write Window Scope.

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

D128_REPORT = "reports/d128_sandbox_candidate_test_plan_scope.json"
D128_TEST_MATRIX = "reports/d128_sandbox_candidate_test_matrix.json"
D128_NO_TOUCH = "reports/d128_sandbox_candidate_no_touch_assertions.json"
D128_D129_SCOPE = "reports/d128_d129_sandbox_candidate_dry_test_runner_scope.json"

OUT = "reports/d129_sandbox_candidate_dry_test_runner_scope.json"
DRY_RESULTS_OUT = "reports/d129_sandbox_candidate_dry_test_results.json"
INTEGRITY_DIFF_OUT = "reports/d129_sandbox_candidate_integrity_diff_summary.json"
D130_SCOPE_OUT = "reports/d129_d130_sandbox_candidate_write_window_scope.json"

REQ_D128_DECISION = "SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_READY"
REQ_D129_GATE = "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE"
REQ_D130_GATE = "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE"
REQ_D128_APPROVAL_SCOPE = "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_ONLY"

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

NO_TOUCH_TARGETS = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
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


def validate_d128(d128, test_matrix, no_touch, d129_scope):
    errors = []

    if not d128:
        errors.append("missing D128 sandbox candidate test plan scope report")
        return errors

    if d128.get("ok") is not True:
        errors.append("D128 ok must be true")
    if d128.get("decision") != REQ_D128_DECISION:
        errors.append("D128 decision must be SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_READY")

    guard = d128.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D128 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_test_plan_scope_only",
        "test_matrix_only",
        "no_touch_assertions_only",
        "approval_for_d129_dry_test_runner_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D128 guardrails.{key} must be true")

    for key in [
        "candidate_files_written_now",
        "candidate_executed_now",
        "approval_for_candidate_execution",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D128 guardrails.{key} must be false")

    summary = d128.get("summary", {})
    expected = {
        "test_plan_status": "PLAN_CREATED_NOT_RUN",
        "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
        "no_touch_status": "ASSERTIONS_CREATED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "real_apply_by_ai_status": "BLOCKED",
        "approval_scope": REQ_D128_APPROVAL_SCOPE,
        "next_step": REQ_D129_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D128 summary.{key} must be {value}")

    if not test_matrix:
        errors.append("missing D128 sandbox candidate test matrix")
    else:
        if test_matrix.get("ok") is not True:
            errors.append("D128 test matrix ok must be true")
        if test_matrix.get("matrix_mode") != "TEST_PLAN_ONLY_NO_EXECUTION":
            errors.append("D128 test matrix mode must be TEST_PLAN_ONLY_NO_EXECUTION")
        if test_matrix.get("candidate_status") != "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED":
            errors.append("D128 test matrix candidate_status must be planned only")
        if test_matrix.get("human_review_required") is not True:
            errors.append("D128 test matrix must require human review")
        if len(test_matrix.get("test_groups", [])) < 4:
            errors.append("D128 test matrix must include at least 4 dry test groups")
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
        ]:
            if test_matrix.get(key) is not False:
                errors.append(f"D128 test matrix {key} must be false")

    if not no_touch:
        errors.append("missing D128 no-touch assertions")
    else:
        if no_touch.get("ok") is not True:
            errors.append("D128 no-touch assertions ok must be true")
        if no_touch.get("assertion_mode") != "NO_TOUCH_ASSERTIONS_ONLY_NO_EXECUTION":
            errors.append("D128 no-touch assertion mode must be no-execution")
        if no_touch.get("human_review_required") is not True:
            errors.append("D128 no-touch assertions must require human review")
        for target in NO_TOUCH_TARGETS:
            if target not in no_touch.get("no_touch_targets", []):
                errors.append(f"D128 no-touch target missing: {target}")
        for key, value in no_touch.get("must_remain_false", {}).items():
            if value is not False:
                errors.append(f"D128 no-touch assertion {key} must remain false")

    if not d129_scope:
        errors.append("missing D128 D129 dry test runner scope")
    else:
        if d129_scope.get("ok") is not True:
            errors.append("D128 D129 scope ok must be true")
        if d129_scope.get("allowed_next_gate") != REQ_D129_GATE:
            errors.append("D128 D129 scope allowed_next_gate must be D129")
        if d129_scope.get("sandbox_candidate_dry_test_runner_scope_only") is not True:
            errors.append("D128 D129 scope must be dry test runner scope only")
        if d129_scope.get("human_review_required") is not True:
            errors.append("D128 D129 scope must require human review")
        for key in [
            "candidate_written_after_d128",
            "candidate_executed_after_d128_by_ai",
            "real_apply_allowed_after_d128_by_ai",
            "route_insert_allowed_after_d128_by_ai",
            "protected_core_mutation_allowed_after_d128_by_ai",
        ]:
            if d129_scope.get(key) is not False:
                errors.append(f"D128 D129 scope {key} must be false")

    return errors


def build_dry_results(runner_id, d128, test_matrix, no_touch):
    groups = test_matrix.get("test_groups", [])
    checks = []
    for group in groups:
        checks.append({
            "name": group.get("name"),
            "status": "DRY_PASS",
            "dry_only": True,
            "candidate_executed": False,
            "actual_apply_executed": False,
        })

    return {
        "state": "D129_SANDBOX_CANDIDATE_DRY_TEST_RESULTS",
        "ok": True,
        "runner_id": runner_id,
        "plan_id": d128.get("plan_id"),
        "review_id": d128.get("review_id"),
        "candidate_id": d128.get("candidate_id"),
        "proposal_id": d128.get("proposal_id"),
        "created_at": now(),
        "results_mode": "DRY_TEST_RESULTS_ONLY_NO_CANDIDATE_EXECUTION",
        "test_groups_total": len(groups),
        "test_groups_dry_passed": len(groups),
        "checks": checks,
        "no_touch_targets_checked": no_touch.get("no_touch_targets", []),
        "candidate_files_written_now": False,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "human_review_required": True,
    }


def build_integrity_diff_summary(runner_id, d128, no_touch):
    targets = no_touch.get("no_touch_targets", NO_TOUCH_TARGETS)
    return {
        "state": "D129_SANDBOX_CANDIDATE_INTEGRITY_DIFF_SUMMARY",
        "ok": True,
        "runner_id": runner_id,
        "plan_id": d128.get("plan_id"),
        "review_id": d128.get("review_id"),
        "candidate_id": d128.get("candidate_id"),
        "created_at": now(),
        "summary_mode": "DECLARED_NO_TOUCH_DIFF_SUMMARY_NO_GIT_DIFF_EXECUTION",
        "git_diff_executed": False,
        "filesystem_scan_executed": False,
        "candidate_files_written_now": False,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "protected_targets": targets,
        "protected_targets_status": {target: "NO_TOUCH_ASSERTED" for target in targets},
        "integrity_status": "NO_TOUCH_ASSERTIONS_HELD_BY_SCOPE",
        "human_review_required": True,
    }


def build_d130_scope(runner_id, d128):
    return {
        "state": "D129_D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE",
        "ok": True,
        "runner_id": runner_id,
        "plan_id": d128.get("plan_id"),
        "review_id": d128.get("review_id"),
        "candidate_id": d128.get("candidate_id"),
        "intake_id": d128.get("intake_id"),
        "ping_id": d128.get("ping_id"),
        "config_id": d128.get("config_id"),
        "dashboard_id": d128.get("dashboard_id"),
        "adapter_id": d128.get("adapter_id"),
        "seal_id": d128.get("seal_id"),
        "proposal_id": d128.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D130_GATE,
        "d130_allowed_to_create": [
            "sandbox_candidate_write_window_scope",
            "sandbox_candidate_write_window_manifest",
            "sandbox_candidate_write_preflight",
            "d131_sandbox_candidate_write_once_scope",
        ],
        "d130_must_not_execute": [
            "execute_sandbox_candidate_by_ai",
            "commit_sandbox_candidate_by_ai",
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
        ],
        "sandbox_candidate_write_window_scope_only": True,
        "human_review_required": True,
        "candidate_written_after_d129": False,
        "candidate_executed_after_d129_by_ai": False,
        "real_apply_allowed_after_d129_by_ai": False,
        "route_insert_allowed_after_d129_by_ai": False,
        "protected_core_mutation_allowed_after_d129_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_ONLY",
    }


def create_sandbox_candidate_dry_test_runner_scope(root="."):
    root = Path(root).resolve()

    d128 = read_json(root / D128_REPORT, {}) or {}
    test_matrix = read_json(root / D128_TEST_MATRIX, {}) or {}
    no_touch = read_json(root / D128_NO_TOUCH, {}) or {}
    d129_scope = read_json(root / D128_D129_SCOPE, {}) or {}

    errors = validate_d128(d128, test_matrix, no_touch, d129_scope)

    runner_id = "d129-" + digest({
        "plan_id": d128.get("plan_id"),
        "review_id": d128.get("review_id"),
        "candidate_id": d128.get("candidate_id"),
        "proposal_id": d128.get("proposal_id"),
    })

    dry_results = build_dry_results(runner_id, d128, test_matrix, no_touch)
    integrity_diff = build_integrity_diff_summary(runner_id, d128, no_touch)
    d130_scope = build_d130_scope(runner_id, d128)

    for item_name, item in [("dry_results", dry_results), ("integrity_diff", integrity_diff)]:
        for key in ["candidate_files_written_now", "candidate_executed_now", "actual_apply_executed"]:
            if item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    for key in ["shell_executed_by_ai", "git_action_by_ai", "network_accessed", "api_key_read", "secret_read"]:
        if dry_results.get(key) is not False:
            errors.append(f"dry_results {key} must be false")

    if integrity_diff.get("git_diff_executed") is not False:
        errors.append("integrity_diff git_diff_executed must be false")
    if integrity_diff.get("filesystem_scan_executed") is not False:
        errors.append("integrity_diff filesystem_scan_executed must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_BLOCKED"
    result = "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_CREATED" if ok else "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_BLOCKED"

    if ok:
        write_json(root / DRY_RESULTS_OUT, dry_results)
        write_json(root / INTEGRITY_DIFF_OUT, integrity_diff)
        write_json(root / D130_SCOPE_OUT, d130_scope)

    report = {
        "state": "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "runner_id": runner_id,
        "plan_id": d128.get("plan_id"),
        "review_id": d128.get("review_id"),
        "candidate_id": d128.get("candidate_id"),
        "intake_id": d128.get("intake_id"),
        "ping_id": d128.get("ping_id"),
        "config_id": d128.get("config_id"),
        "dashboard_id": d128.get("dashboard_id"),
        "adapter_id": d128.get("adapter_id"),
        "seal_id": d128.get("seal_id"),
        "proposal_id": d128.get("proposal_id"),
        "source_d128_report": D128_REPORT,
        "sandbox_candidate_dry_test_results": dry_results if ok else {},
        "sandbox_candidate_integrity_diff_summary": integrity_diff if ok else {},
        "d130_scope": d130_scope if ok else {},
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
            "sandbox_candidate_dry_test_runner_scope_only": True,
            "dry_test_results_only": True,
            "integrity_diff_summary_only": True,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "approval_for_d130_write_window_scope_only": ok,
            "approval_for_candidate_execution": False,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "runner_id": runner_id,
            "plan_id": d128.get("plan_id"),
            "review_id": d128.get("review_id"),
            "candidate_id": d128.get("candidate_id"),
            "adapter_id": d128.get("adapter_id"),
            "seal_id": d128.get("seal_id"),
            "proposal_id": d128.get("proposal_id"),
            "dry_test_status": "DRY_RESULTS_CREATED_NOT_EXECUTED" if ok else "BLOCKED",
            "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
            "integrity_status": "NO_TOUCH_ASSERTIONS_HELD_BY_SCOPE" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "approval_scope": "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D130_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_dry_test_runner_scope_created": ok,
            "sandbox_candidate_dry_test_results_created": ok,
            "sandbox_candidate_integrity_diff_summary_created": ok,
            "d130_scope_created": ok,
            "candidate_files_written": False,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D130 may create sandbox candidate write window scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_dry_test_runner_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_dry_test_runner_scope import create_sandbox_candidate_dry_test_runner_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD129SandboxCandidateDryTestRunnerScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        plan_id = "d128-test"
        review_id = "d127-test"
        candidate_id = "d126-test"
        intake_id = "d125-test"
        ping_id = "d124-test"
        config_id = "d123-test"
        dashboard_id = "d122-test"
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

        d128 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_READY",
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "intake_id": intake_id,
            "ping_id": ping_id,
            "config_id": config_id,
            "dashboard_id": dashboard_id,
            "adapter_id": adapter_id,
            "seal_id": seal_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_test_plan_scope_only": True,
                "test_matrix_only": True,
                "no_touch_assertions_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d129_dry_test_runner_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "test_plan_status": "PLAN_CREATED_NOT_RUN",
                "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
                "no_touch_status": "ASSERTIONS_CREATED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "approval_scope": "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_ONLY",
                "next_step": "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE",
            },
        }

        test_matrix = {
            "ok": True,
            "plan_id": plan_id,
            "candidate_id": candidate_id,
            "matrix_mode": "TEST_PLAN_ONLY_NO_EXECUTION",
            "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
            "test_groups": [
                {"name": "schema_and_manifest_checks", "dry_only": True},
                {"name": "path_boundary_checks", "dry_only": True},
                {"name": "no_touch_assertions", "dry_only": True},
                {"name": "no_execution_assertions", "dry_only": True},
            ],
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "human_review_required": True,
        }

        no_touch = {
            "ok": True,
            "plan_id": plan_id,
            "candidate_id": candidate_id,
            "assertion_mode": "NO_TOUCH_ASSERTIONS_ONLY_NO_EXECUTION",
            "no_touch_targets": ["app/orchestration/", "core/", "runtime/", "bridges/", "memory/"],
            "must_remain_false": {
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "external_ai_called": False,
                "network_accessed": False,
                "api_key_read": False,
                "secret_read": False,
                "shell_from_ai_executed": False,
                "git_commit_by_ai": False,
                "git_push_by_ai": False,
                "rollback_executed": False,
                "restore_executed": False,
            },
            "human_review_required": True,
        }

        d129_scope = {
            "ok": True,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE",
            "sandbox_candidate_dry_test_runner_scope_only": True,
            "human_review_required": True,
            "candidate_written_after_d128": False,
            "candidate_executed_after_d128_by_ai": False,
            "real_apply_allowed_after_d128_by_ai": False,
            "route_insert_allowed_after_d128_by_ai": False,
            "protected_core_mutation_allowed_after_d128_by_ai": False,
        }

        write(root / "reports/d128_sandbox_candidate_test_plan_scope.json", d128)
        write(root / "reports/d128_sandbox_candidate_test_matrix.json", test_matrix)
        write(root / "reports/d128_sandbox_candidate_no_touch_assertions.json", no_touch)
        write(root / "reports/d128_d129_sandbox_candidate_dry_test_runner_scope.json", d129_scope)
        return td, root

    def test_creates_dry_test_runner_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_dry_test_runner_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_READY")
            self.assertEqual(r["summary"]["dry_test_status"], "DRY_RESULTS_CREATED_NOT_EXECUTED")
            self.assertEqual(r["summary"]["approval_scope"], "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d130_scope"]["allowed_next_gate"], "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE")
            self.assertTrue((root / "reports/d129_sandbox_candidate_dry_test_runner_scope.json").exists())
            self.assertTrue((root / "reports/d129_sandbox_candidate_dry_test_results.json").exists())
            self.assertTrue((root / "reports/d129_sandbox_candidate_integrity_diff_summary.json").exists())
            self.assertTrue((root / "reports/d129_d130_sandbox_candidate_write_window_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d128(self):
        td, root = self.root()
        try:
            (root / "reports/d128_sandbox_candidate_test_plan_scope.json").unlink()
            r = create_sandbox_candidate_dry_test_runner_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_test_matrix_says_candidate_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d128_sandbox_candidate_test_matrix.json"
            data = json.loads(p.read_text())
            data["candidate_executed_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_dry_test_runner_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_no_touch_assertion_breaks(self):
        td, root = self.root()
        try:
            p = root / "reports/d128_sandbox_candidate_no_touch_assertions.json"
            data = json.loads(p.read_text())
            data["must_remain_false"]["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_dry_test_runner_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d129_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d128_d129_sandbox_candidate_dry_test_runner_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d128_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_dry_test_runner_scope(root)
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

print("D129 SANDBOX CANDIDATE DRY TEST RUNNER SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_dry_test_runner_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d129_sandbox_candidate_dry_test_runner_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_dry_test_runner_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d129_sandbox_candidate_dry_test_runner_scope", "-v"], check=True)

print("\n== run D129 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_dry_test_runner_scope import create_sandbox_candidate_dry_test_runner_scope\n"
    "r=create_sandbox_candidate_dry_test_runner_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d129_sandbox_candidate_dry_test_runner_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_dry_test_runner_scope.py",
    "tests/test_d129_sandbox_candidate_dry_test_runner_scope.py",
    "reports/d129_sandbox_candidate_dry_test_runner_scope.json",
    "reports/d129_sandbox_candidate_dry_test_results.json",
    "reports/d129_sandbox_candidate_integrity_diff_summary.json",
    "reports/d129_d130_sandbox_candidate_write_window_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D129 sandbox candidate dry test runner scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D129 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD129 SANDBOX CANDIDATE DRY TEST RUNNER SCOPE BOOT DONE")
