#!/usr/bin/env python3
# D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_BOOT.py
#
# D128 creates Sandbox Candidate Test Plan Scope.
# It consumes D127 human-review artifacts and creates a dry test-plan scope.
#
# No candidate write. No candidate execution. No apply. No shell. No network.
# No API key/secret read. No protected mutation. No git action by AI.

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


MODULE = r"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D127_REPORT = "reports/d127_sandbox_candidate_human_review_scope.json"
D127_REVIEW_PACKET = "reports/d127_sandbox_candidate_review_packet.json"
D127_APPROVAL_RECORD = "reports/d127_sandbox_candidate_approval_or_rejection_record.json"
D127_D128_SCOPE = "reports/d127_d128_sandbox_candidate_test_plan_scope.json"

OUT = "reports/d128_sandbox_candidate_test_plan_scope.json"
TEST_MATRIX_OUT = "reports/d128_sandbox_candidate_test_matrix.json"
NO_TOUCH_OUT = "reports/d128_sandbox_candidate_no_touch_assertions.json"
D129_SCOPE_OUT = "reports/d128_d129_sandbox_candidate_dry_test_runner_scope.json"

REQ_D127_DECISION = "SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_READY"
REQ_D128_GATE = "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE"
REQ_D129_GATE = "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE"

FALSE_KEYS = [
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


def digest(obj):
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
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


def validate_d127(d127, review_packet, approval_record, d128_scope):
    errors = []

    if not d127:
        return ["missing D127 sandbox candidate human review scope report"]

    if d127.get("ok") is not True:
        errors.append("D127 ok must be true")
    if d127.get("decision") != REQ_D127_DECISION:
        errors.append("D127 decision must be SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_READY")

    guard = d127.get("guardrails", {})
    for key in FALSE_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D127 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_human_review_scope_only",
        "review_packet_only",
        "approval_record_template_only",
        "approval_for_d128_test_plan_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D127 guardrails.{key} must be true")

    for key in [
        "candidate_files_written_now",
        "candidate_executed_now",
        "approval_for_candidate_execution",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D127 guardrails.{key} must be false")

    summary = d127.get("summary", {})
    if summary.get("review_status") != "PENDING_HUMAN_REVIEW_PACKET_CREATED":
        errors.append("D127 review_status must be PENDING_HUMAN_REVIEW_PACKET_CREATED")
    if summary.get("candidate_status") != "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED":
        errors.append("D127 candidate_status must be PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED")
    if summary.get("static_scan_status") != "PASS":
        errors.append("D127 static_scan_status must be PASS")
    if summary.get("approval_scope") != "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_ONLY":
        errors.append("D127 approval_scope must be D128 test plan scope only")
    if summary.get("next_step") != REQ_D128_GATE:
        errors.append("D127 next_step must be D128")

    if not review_packet:
        errors.append("missing D127 sandbox candidate review packet")
    else:
        if review_packet.get("ok") is not True:
            errors.append("D127 review packet ok must be true")
        if review_packet.get("packet_mode") != "HUMAN_REVIEW_PACKET_ONLY_NO_EXECUTION":
            errors.append("D127 review packet must be human-review packet only")
        if review_packet.get("static_scan_ok") is not True:
            errors.append("D127 review packet static_scan_ok must be true")
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
        ]:
            if review_packet.get(key) is not False:
                errors.append(f"D127 review packet {key} must be false")

    if not approval_record:
        errors.append("missing D127 approval/rejection record")
    else:
        if approval_record.get("ok") is not True:
            errors.append("D127 approval record ok must be true")
        if approval_record.get("operator_decision") != "PENDING_HUMAN_REVIEW":
            errors.append("D127 operator_decision must be pending human review")
        if approval_record.get("approved_for_d128_test_plan_scope_now") is not True:
            errors.append("D127 must approve D128 test plan scope only")
        for key in [
            "approved_for_candidate_execution",
            "approved_for_real_apply",
            "approved_for_route_insert",
            "approved_for_protected_core_mutation",
            "approved_for_git_action_by_ai",
        ]:
            if approval_record.get(key) is not False:
                errors.append(f"D127 approval record {key} must be false")

    if not d128_scope:
        errors.append("missing D127 D128 sandbox candidate test plan scope")
    else:
        if d128_scope.get("ok") is not True:
            errors.append("D127 D128 scope ok must be true")
        if d128_scope.get("allowed_next_gate") != REQ_D128_GATE:
            errors.append("D127 D128 scope allowed_next_gate must be D128")
        if d128_scope.get("sandbox_candidate_test_plan_scope_only") is not True:
            errors.append("D127 D128 scope must be test-plan-only")
        for key in [
            "candidate_written_after_d127",
            "candidate_executed_after_d127_by_ai",
            "real_apply_allowed_after_d127_by_ai",
            "route_insert_allowed_after_d127_by_ai",
            "protected_core_mutation_allowed_after_d127_by_ai",
        ]:
            if d128_scope.get(key) is not False:
                errors.append(f"D127 D128 scope {key} must be false")

    return errors


def build_test_matrix(plan_id, d127, review_packet):
    return {
        "state": "D128_SANDBOX_CANDIDATE_TEST_MATRIX",
        "ok": True,
        "plan_id": plan_id,
        "review_id": d127.get("review_id"),
        "candidate_id": d127.get("candidate_id"),
        "proposal_id": d127.get("proposal_id"),
        "created_at": now(),
        "matrix_mode": "TEST_PLAN_ONLY_NO_EXECUTION",
        "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
        "test_groups": [
            {
                "name": "schema_and_manifest_checks",
                "purpose": "Confirm candidate manifest and summary shape before any candidate write.",
                "dry_only": True,
            },
            {
                "name": "path_boundary_checks",
                "purpose": "Confirm planned files stay inside allowed sandbox/report/test/doc paths.",
                "dry_only": True,
            },
            {
                "name": "no_touch_assertions",
                "purpose": "Confirm protected targets remain untouched.",
                "dry_only": True,
            },
            {
                "name": "no_execution_assertions",
                "purpose": "Confirm no provider/network/shell/apply/git/candidate execution occurs.",
                "dry_only": True,
            },
        ],
        "planned_files_reference": review_packet.get("planned_files", []),
        "candidate_files_written_now": False,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_no_touch_assertions(plan_id, d127):
    return {
        "state": "D128_SANDBOX_CANDIDATE_NO_TOUCH_ASSERTIONS",
        "ok": True,
        "plan_id": plan_id,
        "review_id": d127.get("review_id"),
        "candidate_id": d127.get("candidate_id"),
        "created_at": now(),
        "assertion_mode": "NO_TOUCH_ASSERTIONS_ONLY_NO_EXECUTION",
        "no_touch_targets": NO_TOUCH_TARGETS,
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


def build_d129_scope(plan_id, d127):
    return {
        "state": "D128_D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE",
        "ok": True,
        "plan_id": plan_id,
        "review_id": d127.get("review_id"),
        "candidate_id": d127.get("candidate_id"),
        "intake_id": d127.get("intake_id"),
        "ping_id": d127.get("ping_id"),
        "config_id": d127.get("config_id"),
        "dashboard_id": d127.get("dashboard_id"),
        "adapter_id": d127.get("adapter_id"),
        "seal_id": d127.get("seal_id"),
        "proposal_id": d127.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D129_GATE,
        "d129_allowed_to_create": [
            "sandbox_candidate_dry_test_runner_scope",
            "sandbox_candidate_dry_test_results",
            "sandbox_candidate_integrity_diff_summary",
            "d130_sandbox_candidate_write_window_scope",
        ],
        "d129_must_not_execute": [
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
        "sandbox_candidate_dry_test_runner_scope_only": True,
        "human_review_required": True,
        "candidate_written_after_d128": False,
        "candidate_executed_after_d128_by_ai": False,
        "real_apply_allowed_after_d128_by_ai": False,
        "route_insert_allowed_after_d128_by_ai": False,
        "protected_core_mutation_allowed_after_d128_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_ONLY",
    }


def create_sandbox_candidate_test_plan_scope(root="."):
    root = Path(root).resolve()

    d127 = read_json(root / D127_REPORT, {}) or {}
    review_packet = read_json(root / D127_REVIEW_PACKET, {}) or {}
    approval_record = read_json(root / D127_APPROVAL_RECORD, {}) or {}
    d128_scope = read_json(root / D127_D128_SCOPE, {}) or {}

    errors = validate_d127(d127, review_packet, approval_record, d128_scope)

    plan_id = "d128-" + digest({
        "review_id": d127.get("review_id"),
        "candidate_id": d127.get("candidate_id"),
        "adapter_id": d127.get("adapter_id"),
        "proposal_id": d127.get("proposal_id"),
    })

    test_matrix = build_test_matrix(plan_id, d127, review_packet)
    no_touch_assertions = build_no_touch_assertions(plan_id, d127)
    d129_scope = build_d129_scope(plan_id, d127)

    for item_name, item in [("test_matrix", test_matrix)]:
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
        ]:
            if item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    for key, value in no_touch_assertions.get("must_remain_false", {}).items():
        if value is not False:
            errors.append(f"no_touch_assertions {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_BLOCKED"
    result = "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_CREATED" if ok else "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_BLOCKED"

    if ok:
        write_json(root / TEST_MATRIX_OUT, test_matrix)
        write_json(root / NO_TOUCH_OUT, no_touch_assertions)
        write_json(root / D129_SCOPE_OUT, d129_scope)

    report = {
        "state": "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "plan_id": plan_id,
        "review_id": d127.get("review_id"),
        "candidate_id": d127.get("candidate_id"),
        "intake_id": d127.get("intake_id"),
        "ping_id": d127.get("ping_id"),
        "config_id": d127.get("config_id"),
        "dashboard_id": d127.get("dashboard_id"),
        "adapter_id": d127.get("adapter_id"),
        "seal_id": d127.get("seal_id"),
        "proposal_id": d127.get("proposal_id"),
        "source_d127_report": D127_REPORT,
        "sandbox_candidate_test_matrix": test_matrix if ok else {},
        "sandbox_candidate_no_touch_assertions": no_touch_assertions if ok else {},
        "d129_scope": d129_scope if ok else {},
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
            "sandbox_candidate_test_plan_scope_only": True,
            "test_matrix_only": True,
            "no_touch_assertions_only": True,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "approval_for_d129_dry_test_runner_scope_only": ok,
            "approval_for_candidate_execution": False,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": [],
        },
        "summary": {
            "decision": decision,
            "plan_id": plan_id,
            "review_id": d127.get("review_id"),
            "candidate_id": d127.get("candidate_id"),
            "adapter_id": d127.get("adapter_id"),
            "seal_id": d127.get("seal_id"),
            "proposal_id": d127.get("proposal_id"),
            "test_plan_status": "PLAN_CREATED_NOT_RUN",
            "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
            "no_touch_status": "ASSERTIONS_CREATED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "approval_scope": "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D129_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_test_plan_scope_created": ok,
            "sandbox_candidate_test_matrix_created": ok,
            "sandbox_candidate_no_touch_assertions_created": ok,
            "d129_scope_created": ok,
            "candidate_files_written": False,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D129 may create sandbox candidate dry test runner scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_test_plan_scope(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_test_plan_scope import create_sandbox_candidate_test_plan_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD128SandboxCandidateTestPlanScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        review_id = "d127-test"
        candidate_id = "d126-test"
        intake_id = "d125-test"
        ping_id = "d124-test"
        config_id = "d123-test"
        dashboard_id = "d122-test"
        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        d127 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_READY",
            "review_id": review_id,
            "candidate_id": candidate_id,
            "intake_id": intake_id,
            "ping_id": ping_id,
            "config_id": config_id,
            "dashboard_id": dashboard_id,
            "adapter_id": adapter_id,
            "seal_id": seal_id,
            "proposal_id": proposal_id,
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
                "sandbox_candidate_human_review_scope_only": True,
                "review_packet_only": True,
                "approval_record_template_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d128_test_plan_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "review_status": "PENDING_HUMAN_REVIEW_PACKET_CREATED",
                "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
                "static_scan_status": "PASS",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "approval_scope": "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_ONLY",
                "next_step": "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE",
            },
        }

        review_packet = {
            "ok": True,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "packet_mode": "HUMAN_REVIEW_PACKET_ONLY_NO_EXECUTION",
            "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
            "planned_files": [
                {"path": f"runtime_experimental/ai_sandbox_work/{candidate_id}/candidate_manifest.json"},
                {"path": f"runtime_experimental/ai_sandbox_work/{candidate_id}/candidate_summary.md"},
            ],
            "static_scan_ok": True,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "human_review_required": True,
        }

        approval_record = {
            "ok": True,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "record_mode": "REVIEW_RECORD_TEMPLATE_ONLY",
            "operator_decision": "PENDING_HUMAN_REVIEW",
            "approved_for_d128_test_plan_scope_now": True,
            "approved_for_candidate_execution": False,
            "approved_for_real_apply": False,
            "approved_for_route_insert": False,
            "approved_for_protected_core_mutation": False,
            "approved_for_git_action_by_ai": False,
            "human_review_required": True,
        }

        d128_scope = {
            "ok": True,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE",
            "sandbox_candidate_test_plan_scope_only": True,
            "human_review_required": True,
            "candidate_written_after_d127": False,
            "candidate_executed_after_d127_by_ai": False,
            "real_apply_allowed_after_d127_by_ai": False,
            "route_insert_allowed_after_d127_by_ai": False,
            "protected_core_mutation_allowed_after_d127_by_ai": False,
        }

        write(root / "reports/d127_sandbox_candidate_human_review_scope.json", d127)
        write(root / "reports/d127_sandbox_candidate_review_packet.json", review_packet)
        write(root / "reports/d127_sandbox_candidate_approval_or_rejection_record.json", approval_record)
        write(root / "reports/d127_d128_sandbox_candidate_test_plan_scope.json", d128_scope)

        return td, root

    def test_creates_test_plan_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_test_plan_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_READY")
            self.assertEqual(r["summary"]["test_plan_status"], "PLAN_CREATED_NOT_RUN")
            self.assertEqual(r["summary"]["approval_scope"], "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d129_scope"]["allowed_next_gate"], "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE")
            self.assertTrue((root / "reports/d128_sandbox_candidate_test_plan_scope.json").exists())
            self.assertTrue((root / "reports/d128_sandbox_candidate_test_matrix.json").exists())
            self.assertTrue((root / "reports/d128_sandbox_candidate_no_touch_assertions.json").exists())
            self.assertTrue((root / "reports/d128_d129_sandbox_candidate_dry_test_runner_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d127(self):
        td, root = self.root()
        try:
            (root / "reports/d127_sandbox_candidate_human_review_scope.json").unlink()
            r = create_sandbox_candidate_test_plan_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_review_packet_says_candidate_written(self):
        td, root = self.root()
        try:
            p = root / "reports/d127_sandbox_candidate_review_packet.json"
            data = json.loads(p.read_text())
            data["candidate_files_written_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_test_plan_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_approval_record_allows_execution(self):
        td, root = self.root()
        try:
            p = root / "reports/d127_sandbox_candidate_approval_or_rejection_record.json"
            data = json.loads(p.read_text())
            data["approved_for_candidate_execution"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_test_plan_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d128_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d127_d128_sandbox_candidate_test_plan_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d127_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_test_plan_scope(root)
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

print("D128 SANDBOX CANDIDATE TEST PLAN SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_test_plan_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d128_sandbox_candidate_test_plan_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_test_plan_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d128_sandbox_candidate_test_plan_scope", "-v"], check=True)

print("\n== run D128 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_test_plan_scope import create_sandbox_candidate_test_plan_scope\n"
    "r=create_sandbox_candidate_test_plan_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d128_sandbox_candidate_test_plan_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_test_plan_scope.py",
    "tests/test_d128_sandbox_candidate_test_plan_scope.py",
    "reports/d128_sandbox_candidate_test_plan_scope.json",
    "reports/d128_sandbox_candidate_test_matrix.json",
    "reports/d128_sandbox_candidate_no_touch_assertions.json",
    "reports/d128_d129_sandbox_candidate_dry_test_runner_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D128 sandbox candidate test plan scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D128 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD128 SANDBOX CANDIDATE TEST PLAN SCOPE BOOT DONE")
