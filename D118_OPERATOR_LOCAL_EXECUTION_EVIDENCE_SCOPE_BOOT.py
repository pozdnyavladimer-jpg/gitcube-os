#!/usr/bin/env python3
# D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_BOOT.py
#
# Creates D118 Operator Local Execution Evidence Scope.
#
# D118 consumes D117 manual command review artifacts and creates evidence-scope-only artifacts:
# - runtime_experimental/operator_local_execution_evidence_scope.py
# - tests/test_d118_operator_local_execution_evidence_scope.py
# - reports/d118_operator_local_execution_evidence_scope.json
# - reports/d118_operator_local_execution_log_template.json
# - reports/d118_operator_local_result_capture.json
# - reports/d118_d119_post_apply_verification_gate_scope.json
#
# This is OPERATOR LOCAL EXECUTION EVIDENCE SCOPE ONLY.
# It does NOT execute real apply by AI.
# It does NOT execute shell commands by AI.
# It does NOT apply patches.
# It does NOT mutate core/runtime/app/memory/routes.
# It does NOT commit/push by AI.
#
# D118 creates the evidence container/template for human local execution.
# Real apply by AI remains blocked. Human local execution evidence is captured as a report structure only.

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

D117_REPORT = "reports/d117_manual_apply_command_review_scope.json"
D117_REVIEWED_PACKET = "reports/d117_reviewed_operator_command_packet.json"
D117_READY_RECORD = "reports/d117_manual_apply_ready_or_blocked_record.json"
D117_D118_SCOPE = "reports/d117_d118_operator_local_execution_evidence_scope.json"

OUT = "reports/d118_operator_local_execution_evidence_scope.json"
LOG_TEMPLATE_OUT = "reports/d118_operator_local_execution_log_template.json"
RESULT_CAPTURE_OUT = "reports/d118_operator_local_result_capture.json"
D119_SCOPE_OUT = "reports/d118_d119_post_apply_verification_gate_scope.json"

REQ_D117_DECISION = "MANUAL_APPLY_COMMAND_REVIEW_SCOPE_READY"
REQ_D118_GATE = "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE"
REQ_D119_GATE = "D119_POST_APPLY_VERIFICATION_GATE_SCOPE"
REQ_D117_APPROVAL_SCOPE = "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_ONLY"

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


def validate_d117(d117, reviewed_packet, ready_record, d118_scope):
    errors = []

    if not d117:
        errors.append("missing D117 manual apply command review scope report")
        return errors

    if d117.get("ok") is not True:
        errors.append("D117 ok must be true")
    if d117.get("decision") != REQ_D117_DECISION:
        errors.append("D117 decision must be MANUAL_APPLY_COMMAND_REVIEW_SCOPE_READY")

    guard = d117.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D117 guardrails.{key} must be false")
    if guard.get("manual_command_review_only") is not True:
        errors.append("D117 manual_command_review_only must be true")
    if guard.get("reviewed_command_packet_documentation_only") is not True:
        errors.append("D117 reviewed command packet must be documentation-only")
    if guard.get("approval_for_d118_evidence_scope_only") is not True:
        errors.append("D117 approval_for_d118_evidence_scope_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D117 approval_for_real_apply must be false")
    if guard.get("candidate_execution_allowed") is not False:
        errors.append("D117 candidate_execution_allowed must be false")
    if guard.get("commands_executed_by_ai") is not False:
        errors.append("D117 commands_executed_by_ai must be false")

    summary = d117.get("summary", {})
    if summary.get("real_apply_current_status") != "BLOCKED":
        errors.append("D117 real_apply_current_status must be BLOCKED")
    if summary.get("approval_scope") != REQ_D117_APPROVAL_SCOPE:
        errors.append("D117 approval_scope must be D118 evidence scope only")
    if summary.get("next_step") != REQ_D118_GATE:
        errors.append("D117 summary next_step must be D118")

    if not reviewed_packet:
        errors.append("missing D117 reviewed operator command packet")
    else:
        if reviewed_packet.get("ok") is not True:
            errors.append("D117 reviewed command packet ok must be true")
        if reviewed_packet.get("review_mode") != "COMMAND_REVIEW_ONLY_NOT_EXECUTED":
            errors.append("D117 reviewed packet mode must be command-review-only")
        if reviewed_packet.get("approved_for_d118_evidence_scope_only") is not True:
            errors.append("D117 reviewed packet must approve D118 evidence scope only")
        for key in [
            "approved_for_real_apply_now",
            "commands_executed_by_ai",
            "shell_executed_by_ai",
            "actual_apply_executed",
            "candidate_executed",
            "git_commit_by_ai",
            "git_push_by_ai",
        ]:
            if reviewed_packet.get(key) is not False:
                errors.append(f"D117 reviewed packet {key} must be false")

    if not ready_record:
        errors.append("missing D117 ready-or-blocked record")
    else:
        if ready_record.get("ok") is not True:
            errors.append("D117 ready-or-blocked record ok must be true")
        if ready_record.get("manual_apply_window_status") != "READY_FOR_D118_EVIDENCE_SCOPE_ONLY":
            errors.append("D117 ready record must be ready for D118 evidence scope only")
        if ready_record.get("real_apply_current_status") != "BLOCKED":
            errors.append("D117 ready record real_apply_current_status must be BLOCKED")
        if ready_record.get("ready_for") != REQ_D118_GATE:
            errors.append("D117 ready record ready_for must be D118")
        for key in [
            "actual_apply_executed",
            "candidate_executed",
            "approval_for_real_apply",
            "commands_executed_by_ai",
        ]:
            if ready_record.get(key) is not False:
                errors.append(f"D117 ready record {key} must be false")

    if not d118_scope:
        errors.append("missing D117 D118 operator local execution evidence scope")
    else:
        if d118_scope.get("ok") is not True:
            errors.append("D117 D118 scope ok must be true")
        if d118_scope.get("allowed_next_gate") != REQ_D118_GATE:
            errors.append("D117 D118 scope allowed_next_gate must be D118")
        if d118_scope.get("operator_local_evidence_scope_only") is not True:
            errors.append("D117 D118 scope operator_local_evidence_scope_only must be true")
        if d118_scope.get("human_review_required") is not True:
            errors.append("D117 D118 scope human_review_required must be true")
        for key in [
            "actual_apply_allowed_after_d117_by_ai",
            "route_insert_allowed_after_d117_by_ai",
            "protected_core_mutation_allowed_after_d117_by_ai",
            "sandbox_candidate_execution_allowed_after_d117_by_ai",
        ]:
            if d118_scope.get(key) is not False:
                errors.append(f"D117 D118 scope {key} must be false")

    return errors


def build_log_template(evidence_id, d117, reviewed_packet):
    return {
        "state": "D118_OPERATOR_LOCAL_EXECUTION_LOG_TEMPLATE",
        "ok": True,
        "evidence_id": evidence_id,
        "review_id": d117.get("review_id"),
        "window_id": d117.get("window_id"),
        "phrase_id": d117.get("phrase_id"),
        "proposal_id": d117.get("proposal_id"),
        "created_at": now(),
        "template_mode": "HUMAN_LOCAL_EVIDENCE_TEMPLATE_ONLY",
        "instructions": [
            "Only a human operator may fill this evidence after local execution.",
            "Do not mark execution as complete unless commands were run locally by the operator.",
            "Capture command, timestamp, exit code, and short output summary.",
            "Do not include secrets, tokens, API keys, or private environment values.",
            "D118 script itself does not execute any command.",
        ],
        "commands_to_capture_from_review": reviewed_packet.get("reviewed_commands", []),
        "required_evidence_fields": [
            "operator",
            "local_timestamp",
            "working_tree_before",
            "commands_run",
            "exit_codes",
            "working_tree_after",
            "tests_summary",
            "manual_notes",
        ],
        "forbidden_evidence_fields": [
            "api_key",
            "api_secret",
            "token",
            "password",
            "private_key",
            "raw_secret_env",
        ],
        "shell_executed_by_ai": False,
        "actual_apply_executed_by_ai": False,
        "candidate_executed_by_ai": False,
    }


def build_result_capture(evidence_id, d117, log_template):
    return {
        "state": "D118_OPERATOR_LOCAL_RESULT_CAPTURE",
        "ok": True,
        "evidence_id": evidence_id,
        "review_id": d117.get("review_id"),
        "window_id": d117.get("window_id"),
        "proposal_id": d117.get("proposal_id"),
        "created_at": now(),
        "capture_status": "AWAITING_OPERATOR_LOCAL_EVIDENCE",
        "operator_local_execution_claimed": False,
        "operator_local_execution_evidence_present": False,
        "commands_run": [],
        "exit_codes": {},
        "tests_summary": "not captured yet",
        "working_tree_before": "not captured yet",
        "working_tree_after": "not captured yet",
        "manual_notes": "",
        "ai_executed_commands": False,
        "shell_executed_by_ai": False,
        "actual_apply_executed_by_ai": False,
        "candidate_executed_by_ai": False,
        "ready_for_d119_verification_scope": True,
        "note": (
            "D118 creates the capture container only. If the operator later runs commands locally, "
            "they must update evidence manually before any post-apply verification decision."
        ),
    }


def build_d119_scope(evidence_id, d117):
    return {
        "state": "D118_D119_POST_APPLY_VERIFICATION_GATE_SCOPE",
        "ok": True,
        "evidence_id": evidence_id,
        "review_id": d117.get("review_id"),
        "window_id": d117.get("window_id"),
        "phrase_id": d117.get("phrase_id"),
        "decision_id": d117.get("decision_id"),
        "dry_run_id": d117.get("dry_run_id"),
        "proposal_id": d117.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D119_GATE,
        "d119_allowed_to_create": [
            "post_apply_verification_gate_scope",
            "post_apply_test_results_summary",
            "post_apply_git_state_summary",
            "d120_first_controlled_run_seal_scope",
        ],
        "d119_must_not_execute": [
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
        "post_apply_verification_scope_only": True,
        "human_review_required": True,
        "actual_apply_allowed_after_d118_by_ai": False,
        "route_insert_allowed_after_d118_by_ai": False,
        "protected_core_mutation_allowed_after_d118_by_ai": False,
        "sandbox_candidate_execution_allowed_after_d118_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D119_POST_APPLY_VERIFICATION_GATE_SCOPE_ONLY",
    }


def create_operator_local_execution_evidence_scope(root="."):
    root = Path(root).resolve()

    d117 = read_json(root / D117_REPORT, {}) or {}
    reviewed_packet = read_json(root / D117_REVIEWED_PACKET, {}) or {}
    ready_record = read_json(root / D117_READY_RECORD, {}) or {}
    d118_scope = read_json(root / D117_D118_SCOPE, {}) or {}

    errors = validate_d117(d117, reviewed_packet, ready_record, d118_scope)

    evidence_id = "d118-" + digest({
        "review_id": d117.get("review_id"),
        "window_id": d117.get("window_id"),
        "proposal_id": d117.get("proposal_id"),
    })

    log_template = build_log_template(evidence_id, d117, reviewed_packet)
    result_capture = build_result_capture(evidence_id, d117, log_template)
    d119_scope = build_d119_scope(evidence_id, d117)

    if log_template.get("shell_executed_by_ai") is not False:
        errors.append("log template shell_executed_by_ai must be false")
    if result_capture.get("ai_executed_commands") is not False:
        errors.append("result capture ai_executed_commands must be false")
    if result_capture.get("actual_apply_executed_by_ai") is not False:
        errors.append("result capture actual_apply_executed_by_ai must be false")

    ok = not errors
    decision = "OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_READY" if ok else "OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_BLOCKED"
    result = "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_CREATED" if ok else "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_BLOCKED"

    if ok:
        write_json(root / LOG_TEMPLATE_OUT, log_template)
        write_json(root / RESULT_CAPTURE_OUT, result_capture)
        write_json(root / D119_SCOPE_OUT, d119_scope)

    report = {
        "state": "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "evidence_id": evidence_id,
        "review_id": d117.get("review_id"),
        "window_id": d117.get("window_id"),
        "phrase_id": d117.get("phrase_id"),
        "decision_id": d117.get("decision_id"),
        "dry_run_id": d117.get("dry_run_id"),
        "proposal_id": d117.get("proposal_id"),
        "source_d117_report": D117_REPORT,
        "operator_local_execution_log_template": log_template if ok else {},
        "operator_local_result_capture": result_capture if ok else {},
        "d119_scope": d119_scope if ok else {},
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
            "operator_local_evidence_scope_only": True,
            "evidence_template_only": True,
            "approval_for_d119_verification_scope_only": ok,
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
            "evidence_id": evidence_id,
            "review_id": d117.get("review_id"),
            "proposal_id": d117.get("proposal_id"),
            "real_apply_by_ai_status": "BLOCKED",
            "operator_local_evidence_status": "TEMPLATE_CREATED_AWAITING_OPERATOR_EVIDENCE" if ok else "BLOCKED",
            "approval_scope": "D119_POST_APPLY_VERIFICATION_GATE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D119_GATE,
        },
        "success_condition": {
            "operator_local_execution_evidence_scope_created": ok,
            "log_template_created": ok,
            "result_capture_created": ok,
            "d119_scope_created": ok,
            "approval_for_d119_verification_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "real_ai_called": False,
            "actual_apply_executed_by_ai": False,
            "candidate_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D119 may create post-apply verification gate scope only. Real apply by AI remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_operator_local_execution_evidence_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.operator_local_execution_evidence_scope import create_operator_local_execution_evidence_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD118OperatorLocalExecutionEvidenceScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        review_id = "d117-test"

        d117 = {
            "ok": True,
            "decision": "MANUAL_APPLY_COMMAND_REVIEW_SCOPE_READY",
            "review_id": review_id,
            "window_id": "d116-test",
            "phrase_id": "d115-test",
            "decision_id": "d114-test",
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
                "manual_command_review_only": True,
                "reviewed_command_packet_documentation_only": True,
                "approval_for_d118_evidence_scope_only": True,
                "approval_for_real_apply": False,
                "candidate_execution_allowed": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "real_apply_current_status": "BLOCKED",
                "approval_scope": "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_ONLY",
                "next_step": "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE",
            },
        }

        reviewed_packet = {
            "ok": True,
            "review_id": review_id,
            "review_mode": "COMMAND_REVIEW_ONLY_NOT_EXECUTED",
            "reviewed_commands": [
                "git status --short",
                "python -m unittest discover -s tests -v",
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

        ready_record = {
            "ok": True,
            "review_id": review_id,
            "manual_apply_window_status": "READY_FOR_D118_EVIDENCE_SCOPE_ONLY",
            "real_apply_current_status": "BLOCKED",
            "ready_for": "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE",
            "actual_apply_executed": False,
            "candidate_executed": False,
            "approval_for_real_apply": False,
            "commands_executed_by_ai": False,
        }

        d118_scope = {
            "ok": True,
            "review_id": review_id,
            "allowed_next_gate": "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE",
            "operator_local_evidence_scope_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d117_by_ai": False,
            "route_insert_allowed_after_d117_by_ai": False,
            "protected_core_mutation_allowed_after_d117_by_ai": False,
            "sandbox_candidate_execution_allowed_after_d117_by_ai": False,
        }

        write(root / "reports/d117_manual_apply_command_review_scope.json", d117)
        write(root / "reports/d117_reviewed_operator_command_packet.json", reviewed_packet)
        write(root / "reports/d117_manual_apply_ready_or_blocked_record.json", ready_record)
        write(root / "reports/d117_d118_operator_local_execution_evidence_scope.json", d118_scope)

        return td, root

    def test_creates_evidence_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_operator_local_execution_evidence_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_READY")
            self.assertEqual(r["summary"]["real_apply_by_ai_status"], "BLOCKED")
            self.assertEqual(r["summary"]["approval_scope"], "D119_POST_APPLY_VERIFICATION_GATE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["commands_executed_by_ai"])
            self.assertEqual(r["d119_scope"]["allowed_next_gate"], "D119_POST_APPLY_VERIFICATION_GATE_SCOPE")
            self.assertTrue((root / "reports/d118_operator_local_execution_evidence_scope.json").exists())
            self.assertTrue((root / "reports/d118_operator_local_execution_log_template.json").exists())
            self.assertTrue((root / "reports/d118_operator_local_result_capture.json").exists())
            self.assertTrue((root / "reports/d118_d119_post_apply_verification_gate_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d117(self):
        td, root = self.root()
        try:
            (root / "reports/d117_manual_apply_command_review_scope.json").unlink()
            r = create_operator_local_execution_evidence_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_reviewed_packet_executed_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d117_reviewed_operator_command_packet.json"
            data = json.loads(p.read_text())
            data["commands_executed_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_operator_local_execution_evidence_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_ready_record_claims_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d117_manual_apply_ready_or_blocked_record.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_operator_local_execution_evidence_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_scope_allows_apply_by_ai_after_d117(self):
        td, root = self.root()
        try:
            p = root / "reports/d117_d118_operator_local_execution_evidence_scope.json"
            data = json.loads(p.read_text())
            data["actual_apply_allowed_after_d117_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_operator_local_execution_evidence_scope(root)
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

print("D118 OPERATOR LOCAL EXECUTION EVIDENCE SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/operator_local_execution_evidence_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d118_operator_local_execution_evidence_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/operator_local_execution_evidence_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d118_operator_local_execution_evidence_scope", "-v"], check=True)

print("\n== run D118 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.operator_local_execution_evidence_scope import create_operator_local_execution_evidence_scope\n"
    "r=create_operator_local_execution_evidence_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d118_operator_local_execution_evidence_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/operator_local_execution_evidence_scope.py",
    "tests/test_d118_operator_local_execution_evidence_scope.py",
    "reports/d118_operator_local_execution_evidence_scope.json",
    "reports/d118_operator_local_execution_log_template.json",
    "reports/d118_operator_local_result_capture.json",
    "reports/d118_d119_post_apply_verification_gate_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D118 operator local execution evidence scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D118 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD118 OPERATOR LOCAL EXECUTION EVIDENCE SCOPE BOOT DONE")
