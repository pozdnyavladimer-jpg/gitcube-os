#!/usr/bin/env python3
# D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE_BOOT.py
#
# Creates D117 Manual Apply Command Review Scope.
#
# D117 consumes D116 manual apply window artifacts and creates command-review-only artifacts:
# - runtime_experimental/manual_apply_command_review_scope.py
# - tests/test_d117_manual_apply_command_review_scope.py
# - reports/d117_manual_apply_command_review_scope.json
# - reports/d117_reviewed_operator_command_packet.json
# - reports/d117_manual_apply_ready_or_blocked_record.json
# - reports/d117_d118_operator_local_execution_evidence_scope.json
#
# This is MANUAL COMMAND REVIEW ONLY.
# It does NOT execute real apply.
# It does NOT execute shell commands.
# It does NOT execute AI proposal commands.
# It does NOT apply patches.
# It does NOT mutate core/runtime/app/memory/routes.
# It does NOT commit/push by AI.
#
# D117 only reviews the D116 local command packet and prepares D118 evidence scope.
# Real apply remains blocked until a later, separate, explicit operator-local gate.

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

D116_REPORT = "reports/d116_manual_apply_window_scope.json"
D116_PREFLIGHT = "reports/d116_manual_apply_preflight_checklist.json"
D116_COMMAND_PACKET = "reports/d116_operator_local_command_packet.json"
D116_D117_SCOPE = "reports/d116_d117_manual_apply_command_review_scope.json"

OUT = "reports/d117_manual_apply_command_review_scope.json"
REVIEWED_COMMAND_PACKET_OUT = "reports/d117_reviewed_operator_command_packet.json"
READY_OR_BLOCKED_OUT = "reports/d117_manual_apply_ready_or_blocked_record.json"
D118_SCOPE_OUT = "reports/d117_d118_operator_local_execution_evidence_scope.json"

REQ_D116_DECISION = "MANUAL_APPLY_WINDOW_SCOPE_READY"
REQ_D117_GATE = "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE"
REQ_D118_GATE = "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE"
REQ_D116_APPROVAL_SCOPE = "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE_ONLY"

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


def validate_d116(d116, preflight, command_packet, d117_scope):
    errors = []

    if not d116:
        errors.append("missing D116 manual apply window scope report")
        return errors

    if d116.get("ok") is not True:
        errors.append("D116 ok must be true")
    if d116.get("decision") != REQ_D116_DECISION:
        errors.append("D116 decision must be MANUAL_APPLY_WINDOW_SCOPE_READY")

    guard = d116.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D116 guardrails.{key} must be false")
    if guard.get("manual_apply_window_scope_only") is not True:
        errors.append("D116 manual_apply_window_scope_only must be true")
    if guard.get("operator_command_packet_documentation_only") is not True:
        errors.append("D116 command packet must be documentation-only")
    if guard.get("approval_for_d117_command_review_only") is not True:
        errors.append("D116 approval_for_d117_command_review_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D116 approval_for_real_apply must be false")
    if guard.get("candidate_execution_allowed") is not False:
        errors.append("D116 candidate_execution_allowed must be false")

    summary = d116.get("summary", {})
    if summary.get("real_apply_current_status") != "BLOCKED":
        errors.append("D116 real_apply_current_status must be BLOCKED")
    if summary.get("approval_scope") != REQ_D116_APPROVAL_SCOPE:
        errors.append("D116 approval_scope must be D117 command review only")
    if summary.get("next_step") != REQ_D117_GATE:
        errors.append("D116 summary next_step must be D117")

    if not preflight:
        errors.append("missing D116 preflight checklist")
    else:
        if preflight.get("ok") is not True:
            errors.append("D116 preflight ok must be true")
        if preflight.get("manual_window_mode") != "LOCAL_OPERATOR_REVIEW_ONLY":
            errors.append("D116 preflight mode must be LOCAL_OPERATOR_REVIEW_ONLY")
        if preflight.get("lock_state") != "REAL_APPLY_STILL_LOCKED":
            errors.append("D116 preflight lock_state must be REAL_APPLY_STILL_LOCKED")
        for key in ["actual_apply_executed", "candidate_executed"]:
            if preflight.get(key) is not False:
                errors.append(f"D116 preflight {key} must be false")
        mf = preflight.get("must_remain_false", {})
        for key in [
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "external_ai_called",
            "network_accessed",
            "candidate_executed",
            "git_commit_by_ai",
            "git_push_by_ai",
        ]:
            if mf.get(key) is not False:
                errors.append(f"D116 preflight must_remain_false.{key} must be false")

    if not command_packet:
        errors.append("missing D116 operator local command packet")
    else:
        if command_packet.get("ok") is not True:
            errors.append("D116 command packet ok must be true")
        if command_packet.get("packet_mode") != "DOCUMENTATION_ONLY_NOT_EXECUTED":
            errors.append("D116 command packet must be documentation-only/not-executed")
        if command_packet.get("commands_are_not_executed_by_ai") is not True:
            errors.append("D116 command packet commands_are_not_executed_by_ai must be true")
        if command_packet.get("human_may_run_manually_after_d117") is not True:
            errors.append("D116 command packet must only allow human after D117")
        for key in [
            "real_apply_command_included",
            "shell_executed_by_ai",
            "actual_apply_executed",
            "candidate_executed",
        ]:
            if command_packet.get(key) is not False:
                errors.append(f"D116 command packet {key} must be false")
        for blocked in ["git apply", "git commit", "git push", "route insert", "execute sandbox candidate"]:
            if blocked not in command_packet.get("blocked_commands", []):
                errors.append(f"D116 command packet missing blocked command: {blocked}")

    if not d117_scope:
        errors.append("missing D116 D117 command review scope")
    else:
        if d117_scope.get("ok") is not True:
            errors.append("D116 D117 scope ok must be true")
        if d117_scope.get("allowed_next_gate") != REQ_D117_GATE:
            errors.append("D116 D117 scope allowed_next_gate must be D117")
        if d117_scope.get("manual_command_review_only") is not True:
            errors.append("D116 D117 scope manual_command_review_only must be true")
        if d117_scope.get("human_review_required") is not True:
            errors.append("D116 D117 scope human_review_required must be true")
        for key in [
            "actual_apply_allowed_after_d116",
            "route_insert_allowed_after_d116",
            "protected_core_mutation_allowed_after_d116",
            "sandbox_candidate_execution_allowed_after_d116",
        ]:
            if d117_scope.get(key) is not False:
                errors.append(f"D116 D117 scope {key} must be false")

    return errors


def build_reviewed_command_packet(review_id, d116, command_packet):
    original_commands = list(command_packet.get("commands", []))
    blocked_commands = list(command_packet.get("blocked_commands", []))
    return {
        "state": "D117_REVIEWED_OPERATOR_COMMAND_PACKET",
        "ok": True,
        "review_id": review_id,
        "window_id": d116.get("window_id"),
        "phrase_id": d116.get("phrase_id"),
        "proposal_id": d116.get("proposal_id"),
        "created_at": now(),
        "review_mode": "COMMAND_REVIEW_ONLY_NOT_EXECUTED",
        "original_packet": D116_COMMAND_PACKET,
        "reviewed_commands": original_commands,
        "blocked_commands": blocked_commands,
        "review_notes": [
            "Commands are documentation-only at D117.",
            "No command is executed by this module.",
            "No real apply command is included.",
            "Manual execution evidence must be captured by D118 if a human later runs commands.",
        ],
        "approved_for_d118_evidence_scope_only": True,
        "approved_for_real_apply_now": False,
        "commands_executed_by_ai": False,
        "shell_executed_by_ai": False,
        "actual_apply_executed": False,
        "candidate_executed": False,
        "git_commit_by_ai": False,
        "git_push_by_ai": False,
    }


def build_ready_or_blocked_record(review_id, reviewed_packet):
    return {
        "state": "D117_MANUAL_APPLY_READY_OR_BLOCKED_RECORD",
        "ok": True,
        "review_id": review_id,
        "created_at": now(),
        "manual_apply_window_status": "READY_FOR_D118_EVIDENCE_SCOPE_ONLY",
        "real_apply_current_status": "BLOCKED",
        "ready_for": "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE",
        "not_ready_for": [
            "real_apply",
            "auto_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "sandbox_candidate_execution",
            "git_commit_or_push_by_ai",
        ],
        "blocking_reasons": [
            "D118 operator local execution evidence scope does not exist yet",
            "No operator local execution evidence exists yet",
            "No post-apply verification exists yet",
            "No D120 controlled run seal exists yet",
        ],
        "actual_apply_executed": False,
        "candidate_executed": False,
        "approval_for_real_apply": False,
        "commands_executed_by_ai": False,
    }


def build_d118_scope(review_id, d116):
    return {
        "state": "D117_D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE",
        "ok": True,
        "review_id": review_id,
        "window_id": d116.get("window_id"),
        "phrase_id": d116.get("phrase_id"),
        "decision_id": d116.get("decision_id"),
        "review_id_from_d113": d116.get("review_id"),
        "dry_run_id": d116.get("dry_run_id"),
        "proposal_id": d116.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D118_GATE,
        "d118_allowed_to_create": [
            "operator_local_execution_evidence_scope",
            "operator_local_execution_log_template",
            "operator_local_result_capture",
            "d119_post_apply_verification_gate_scope",
        ],
        "d118_must_not_execute": [
            "real_apply_by_ai",
            "auto_apply",
            "route_insert_by_ai",
            "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai",
            "external_ai_network_call",
            "shell_exec_from_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute_by_ai",
            "restore_execute_by_ai",
            "execute_sandbox_candidate_by_ai",
            "commit_sandbox_candidate_by_ai",
        ],
        "operator_local_evidence_scope_only": True,
        "human_review_required": True,
        "actual_apply_allowed_after_d117_by_ai": False,
        "route_insert_allowed_after_d117_by_ai": False,
        "protected_core_mutation_allowed_after_d117_by_ai": False,
        "sandbox_candidate_execution_allowed_after_d117_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_ONLY",
    }


def create_manual_apply_command_review_scope(root="."):
    root = Path(root).resolve()

    d116 = read_json(root / D116_REPORT, {}) or {}
    preflight = read_json(root / D116_PREFLIGHT, {}) or {}
    command_packet = read_json(root / D116_COMMAND_PACKET, {}) or {}
    d117_scope = read_json(root / D116_D117_SCOPE, {}) or {}

    errors = validate_d116(d116, preflight, command_packet, d117_scope)

    review_id = "d117-" + digest({
        "window_id": d116.get("window_id"),
        "phrase_id": d116.get("phrase_id"),
        "proposal_id": d116.get("proposal_id"),
    })

    reviewed_packet = build_reviewed_command_packet(review_id, d116, command_packet)
    ready_or_blocked = build_ready_or_blocked_record(review_id, reviewed_packet)
    d118_scope = build_d118_scope(review_id, d116)

    if reviewed_packet.get("commands_executed_by_ai") is not False:
        errors.append("reviewed command packet commands_executed_by_ai must be false")
    if reviewed_packet.get("approved_for_real_apply_now") is not False:
        errors.append("reviewed command packet approved_for_real_apply_now must be false")
    if ready_or_blocked.get("real_apply_current_status") != "BLOCKED":
        errors.append("ready-or-blocked record real apply must remain BLOCKED")

    ok = not errors
    decision = "MANUAL_APPLY_COMMAND_REVIEW_SCOPE_READY" if ok else "MANUAL_APPLY_COMMAND_REVIEW_SCOPE_BLOCKED"
    result = "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE_CREATED" if ok else "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE_BLOCKED"

    if ok:
        write_json(root / REVIEWED_COMMAND_PACKET_OUT, reviewed_packet)
        write_json(root / READY_OR_BLOCKED_OUT, ready_or_blocked)
        write_json(root / D118_SCOPE_OUT, d118_scope)

    report = {
        "state": "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_MANUAL_APPLY_COMMAND_REVIEW_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "review_id": review_id,
        "window_id": d116.get("window_id"),
        "phrase_id": d116.get("phrase_id"),
        "decision_id": d116.get("decision_id"),
        "dry_run_id": d116.get("dry_run_id"),
        "proposal_id": d116.get("proposal_id"),
        "source_d116_report": D116_REPORT,
        "reviewed_operator_command_packet": reviewed_packet if ok else {},
        "manual_apply_ready_or_blocked_record": ready_or_blocked if ok else {},
        "d118_scope": d118_scope if ok else {},
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
            "manual_command_review_only": True,
            "reviewed_command_packet_documentation_only": True,
            "approval_for_d118_evidence_scope_only": ok,
            "approval_for_real_apply": False,
            "candidate_execution_allowed": False,
            "commands_executed_by_ai": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": [],
        },
        "summary": {
            "decision": decision,
            "review_id": review_id,
            "window_id": d116.get("window_id"),
            "proposal_id": d116.get("proposal_id"),
            "real_apply_current_status": "BLOCKED",
            "approval_scope": "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D118_GATE,
        },
        "success_condition": {
            "manual_apply_command_review_scope_created": ok,
            "reviewed_operator_command_packet_created": ok,
            "ready_or_blocked_record_created": ok,
            "d118_scope_created": ok,
            "approval_for_d118_evidence_scope_only": ok,
            "approval_for_real_apply": False,
            "real_ai_called": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "protected_core_untouched": True,
            "next_step": "D118 may create operator local execution evidence scope only. Real apply by AI remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_manual_apply_command_review_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.manual_apply_command_review_scope import create_manual_apply_command_review_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD117ManualApplyCommandReviewScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        window_id = "d116-test"

        d116 = {
            "ok": True,
            "decision": "MANUAL_APPLY_WINDOW_SCOPE_READY",
            "window_id": window_id,
            "phrase_id": "d115-test",
            "decision_id": "d114-test",
            "review_id": "d113-test",
            "dry_run_id": "d112-test",
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
                "manual_apply_window_scope_only": True,
                "operator_command_packet_documentation_only": True,
                "approval_for_d117_command_review_only": True,
                "approval_for_real_apply": False,
                "candidate_execution_allowed": False,
            },
            "summary": {
                "real_apply_current_status": "BLOCKED",
                "approval_scope": "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE_ONLY",
                "next_step": "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE",
            },
        }

        preflight = {
            "ok": True,
            "window_id": window_id,
            "manual_window_mode": "LOCAL_OPERATOR_REVIEW_ONLY",
            "lock_state": "REAL_APPLY_STILL_LOCKED",
            "must_remain_false": {
                "actual_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "external_ai_called": False,
                "network_accessed": False,
                "candidate_executed": False,
                "git_commit_by_ai": False,
                "git_push_by_ai": False,
            },
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        command_packet = {
            "ok": True,
            "window_id": window_id,
            "packet_mode": "DOCUMENTATION_ONLY_NOT_EXECUTED",
            "commands_are_not_executed_by_ai": True,
            "human_may_run_manually_after_d117": True,
            "commands": [
                "git status --short",
                "python -m unittest discover -s tests -v",
                "python -m py_compile runtime_experimental/*.py",
            ],
            "blocked_commands": [
                "git apply",
                "git commit",
                "git push",
                "route insert",
                "execute sandbox candidate",
            ],
            "real_apply_command_included": False,
            "shell_executed_by_ai": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        d117_scope = {
            "ok": True,
            "window_id": window_id,
            "allowed_next_gate": "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE",
            "manual_command_review_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d116": False,
            "route_insert_allowed_after_d116": False,
            "protected_core_mutation_allowed_after_d116": False,
            "sandbox_candidate_execution_allowed_after_d116": False,
        }

        write(root / "reports/d116_manual_apply_window_scope.json", d116)
        write(root / "reports/d116_manual_apply_preflight_checklist.json", preflight)
        write(root / "reports/d116_operator_local_command_packet.json", command_packet)
        write(root / "reports/d116_d117_manual_apply_command_review_scope.json", d117_scope)

        return td, root

    def test_creates_command_review_outputs(self):
        td, root = self.root()
        try:
            r = create_manual_apply_command_review_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "MANUAL_APPLY_COMMAND_REVIEW_SCOPE_READY")
            self.assertEqual(r["summary"]["real_apply_current_status"], "BLOCKED")
            self.assertEqual(r["summary"]["approval_scope"], "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertFalse(r["guardrails"]["commands_executed_by_ai"])
            self.assertEqual(r["d118_scope"]["allowed_next_gate"], "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE")
            self.assertTrue((root / "reports/d117_manual_apply_command_review_scope.json").exists())
            self.assertTrue((root / "reports/d117_reviewed_operator_command_packet.json").exists())
            self.assertTrue((root / "reports/d117_manual_apply_ready_or_blocked_record.json").exists())
            self.assertTrue((root / "reports/d117_d118_operator_local_execution_evidence_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d116(self):
        td, root = self.root()
        try:
            (root / "reports/d116_manual_apply_window_scope.json").unlink()
            r = create_manual_apply_command_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_command_packet_executed_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d116_operator_local_command_packet.json"
            data = json.loads(p.read_text())
            data["shell_executed_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_manual_apply_command_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_real_apply_command_included(self):
        td, root = self.root()
        try:
            p = root / "reports/d116_operator_local_command_packet.json"
            data = json.loads(p.read_text())
            data["real_apply_command_included"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_manual_apply_command_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_scope_allows_apply_after_d116(self):
        td, root = self.root()
        try:
            p = root / "reports/d116_d117_manual_apply_command_review_scope.json"
            data = json.loads(p.read_text())
            data["actual_apply_allowed_after_d116"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_manual_apply_command_review_scope(root)
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

print("D117 MANUAL APPLY COMMAND REVIEW SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/manual_apply_command_review_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d117_manual_apply_command_review_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/manual_apply_command_review_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d117_manual_apply_command_review_scope", "-v"], check=True)

print("\n== run D117 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.manual_apply_command_review_scope import create_manual_apply_command_review_scope\n"
    "r=create_manual_apply_command_review_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d117_manual_apply_command_review_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/manual_apply_command_review_scope.py",
    "tests/test_d117_manual_apply_command_review_scope.py",
    "reports/d117_manual_apply_command_review_scope.json",
    "reports/d117_reviewed_operator_command_packet.json",
    "reports/d117_manual_apply_ready_or_blocked_record.json",
    "reports/d117_d118_operator_local_execution_evidence_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D117 manual apply command review scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D117 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD117 MANUAL APPLY COMMAND REVIEW SCOPE BOOT DONE")
