#!/usr/bin/env python3
# D115_FINAL_APPLY_PHRASE_SCOPE_BOOT.py
#
# Creates D115 Final Apply Phrase Scope.
#
# D115 consumes D114 final human decision artifacts and creates final-phrase-only artifacts:
# - runtime_experimental/final_apply_phrase_scope.py
# - tests/test_d115_final_apply_phrase_scope.py
# - reports/d115_final_apply_phrase_scope.json
# - reports/d115_final_apply_phrase_statement.json
# - reports/d115_final_pre_apply_lock_report.json
# - reports/d115_d116_manual_apply_window_scope.json
#
# FINAL PHRASE SCOPE ONLY.
# No real apply. No route insert. No protected-core mutation. No candidate execution. No AI git action.

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

D114_REPORT = "reports/d114_final_human_apply_decision_scope.json"
D114_PERMISSION_MATRIX = "reports/d114_final_apply_permission_matrix.json"
D114_OPERATOR_STATEMENT = "reports/d114_final_operator_decision_statement.json"
D114_D115_SCOPE = "reports/d114_d115_final_apply_phrase_scope.json"

OUT = "reports/d115_final_apply_phrase_scope.json"
PHRASE_STATEMENT_OUT = "reports/d115_final_apply_phrase_statement.json"
PRE_APPLY_LOCK_OUT = "reports/d115_final_pre_apply_lock_report.json"
D116_SCOPE_OUT = "reports/d115_d116_manual_apply_window_scope.json"

REQ_D114_DECISION = "FINAL_HUMAN_APPLY_DECISION_SCOPE_READY"
REQ_D115_GATE = "D115_FINAL_APPLY_PHRASE_SCOPE"
REQ_D116_GATE = "D116_MANUAL_APPLY_WINDOW_SCOPE"
REQ_D114_APPROVAL_SCOPE = "D115_FINAL_APPLY_PHRASE_SCOPE_ONLY"
D115_REQUIRED_PHRASE = "APPROVE_D115_FINAL_APPLY_PHRASE_SCOPE_ONLY"

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


def validate_d114(d114, permission_matrix, operator_statement, d115_scope):
    errors = []

    if not d114:
        errors.append("missing D114 final human apply decision scope report")
        return errors

    if d114.get("ok") is not True:
        errors.append("D114 ok must be true")
    if d114.get("decision") != REQ_D114_DECISION:
        errors.append("D114 decision must be FINAL_HUMAN_APPLY_DECISION_SCOPE_READY")

    guard = d114.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D114 guardrails.{key} must be false")
    if guard.get("final_human_decision_only") is not True:
        errors.append("D114 final_human_decision_only must be true")
    if guard.get("approval_for_d115_phrase_scope_only") is not True:
        errors.append("D114 approval_for_d115_phrase_scope_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D114 approval_for_real_apply must be false")
    if guard.get("candidate_execution_allowed") is not False:
        errors.append("D114 candidate_execution_allowed must be false")

    summary = d114.get("summary", {})
    if summary.get("real_apply_current_status") != "BLOCKED":
        errors.append("D114 real_apply_current_status must be BLOCKED")
    if summary.get("approval_scope") != REQ_D114_APPROVAL_SCOPE:
        errors.append("D114 approval_scope must be D115 phrase scope only")
    if summary.get("next_step") != REQ_D115_GATE:
        errors.append("D114 summary next_step must be D115")

    if not permission_matrix:
        errors.append("missing D114 permission matrix")
    else:
        if permission_matrix.get("ok") is not True:
            errors.append("D114 permission matrix ok must be true")
        if permission_matrix.get("real_apply_permission") != "NOT_GRANTED":
            errors.append("D114 permission matrix real_apply_permission must be NOT_GRANTED")
        if permission_matrix.get("d115_phrase_scope_permission") != "GRANTED_FOR_PHRASE_SCOPE_ONLY":
            errors.append("D114 D115 phrase scope permission must be phrase-only")
        perms = permission_matrix.get("permissions", {})
        if perms.get("create_d115_final_apply_phrase_scope") is not True:
            errors.append("D114 must allow creation of D115 phrase scope")
        for key in [
            "real_apply_now",
            "auto_apply_now",
            "route_insert_now",
            "protected_core_mutation_now",
            "canonical_memory_overwrite_now",
            "external_ai_or_network_call_now",
            "sandbox_candidate_execution_now",
            "ai_git_commit_or_push_now",
        ]:
            if perms.get(key) is not False:
                errors.append(f"D114 permission matrix permissions.{key} must be false")

    if not operator_statement:
        errors.append("missing D114 final operator decision statement")
    else:
        if operator_statement.get("ok") is not True:
            errors.append("D114 operator statement ok must be true")
        if operator_statement.get("human_decision_scope") != REQ_D114_APPROVAL_SCOPE:
            errors.append("D114 operator statement scope must be D115 phrase scope only")
        if operator_statement.get("d115_phrase_scope_approved") is not True:
            errors.append("D114 operator statement must approve D115 phrase scope")
        if operator_statement.get("real_apply_approved_now") is not False:
            errors.append("D114 operator statement real_apply_approved_now must be false")
        for key in ["actual_apply_executed", "candidate_executed"]:
            if operator_statement.get(key) is not False:
                errors.append(f"D114 operator statement {key} must be false")

    if not d115_scope:
        errors.append("missing D114 D115 final apply phrase scope")
    else:
        if d115_scope.get("ok") is not True:
            errors.append("D114 D115 scope ok must be true")
        if d115_scope.get("allowed_next_gate") != REQ_D115_GATE:
            errors.append("D114 D115 scope allowed_next_gate must be D115")
        if d115_scope.get("final_phrase_scope_only") is not True:
            errors.append("D114 D115 scope final_phrase_scope_only must be true")
        if d115_scope.get("human_review_required") is not True:
            errors.append("D114 D115 scope human_review_required must be true")
        if d115_scope.get("required_phrase_for_later_gate") != D115_REQUIRED_PHRASE:
            errors.append("D114 D115 scope required phrase mismatch")
        for key in [
            "actual_apply_allowed_after_d114",
            "route_insert_allowed_after_d114",
            "protected_core_mutation_allowed_after_d114",
            "sandbox_candidate_execution_allowed_after_d114",
        ]:
            if d115_scope.get(key) is not False:
                errors.append(f"D114 D115 scope {key} must be false")

    return errors


def build_phrase_statement(phrase_id, d114, permission_matrix):
    return {
        "state": "D115_FINAL_APPLY_PHRASE_STATEMENT",
        "ok": True,
        "phrase_id": phrase_id,
        "decision_id": d114.get("decision_id"),
        "review_id": d114.get("review_id"),
        "dry_run_id": d114.get("dry_run_id"),
        "proposal_id": d114.get("proposal_id"),
        "created_at": now(),
        "phrase_scope": "D116_MANUAL_APPLY_WINDOW_SCOPE_ONLY",
        "required_phrase": "APPROVE_D116_MANUAL_APPLY_WINDOW_SCOPE_ONLY",
        "human_statement": (
            "I approve only the creation of the D116 manual apply window scope. "
            "This does not execute real apply. It does not authorize autonomous apply, "
            "route insertion, protected-core mutation, canonical memory overwrite, external AI/network calls, "
            "sandbox candidate execution, rollback/restore, or AI git actions."
        ),
        "source_permission": permission_matrix.get("d115_phrase_scope_permission"),
        "real_apply_approved_now": False,
        "actual_apply_executed": False,
        "candidate_executed": False,
    }


def build_pre_apply_lock_report(phrase_id, d114, permission_matrix, operator_statement):
    return {
        "state": "D115_FINAL_PRE_APPLY_LOCK_REPORT",
        "ok": True,
        "phrase_id": phrase_id,
        "decision_id": d114.get("decision_id"),
        "proposal_id": d114.get("proposal_id"),
        "created_at": now(),
        "lock_state": "REAL_APPLY_STILL_LOCKED",
        "lock_reason": "D115 creates final phrase scope only; D116 manual apply window scope is still required.",
        "permission_matrix_checked": True,
        "operator_statement_checked": True,
        "real_apply_permission": permission_matrix.get("real_apply_permission"),
        "real_apply_approved_now": operator_statement.get("real_apply_approved_now") is True,
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
        "blockers": [
            "no D116 manual apply window scope",
            "no D117 manual apply command packet",
            "no final operator local execution evidence",
            "no post-apply verification gate",
        ],
    }


def build_d116_scope(phrase_id, d114):
    return {
        "state": "D115_D116_MANUAL_APPLY_WINDOW_SCOPE",
        "ok": True,
        "phrase_id": phrase_id,
        "decision_id": d114.get("decision_id"),
        "review_id": d114.get("review_id"),
        "dry_run_id": d114.get("dry_run_id"),
        "proposal_id": d114.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D116_GATE,
        "d116_allowed_to_create": [
            "manual_apply_window_scope",
            "manual_apply_preflight_checklist",
            "operator_local_command_packet",
            "d117_manual_apply_command_review_scope",
        ],
        "d116_must_not_execute": [
            "real_apply",
            "auto_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "shell_exec_from_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute",
            "restore_execute",
            "execute_sandbox_candidate",
            "commit_sandbox_candidate",
        ],
        "manual_apply_window_scope_only": True,
        "human_review_required": True,
        "actual_apply_allowed_after_d115": False,
        "route_insert_allowed_after_d115": False,
        "protected_core_mutation_allowed_after_d115": False,
        "sandbox_candidate_execution_allowed_after_d115": False,
        "required_phrase_for_later_gate": "APPROVE_D116_MANUAL_APPLY_WINDOW_SCOPE_ONLY",
    }


def create_final_apply_phrase_scope(root="."):
    root = Path(root).resolve()

    d114 = read_json(root / D114_REPORT, {}) or {}
    permission_matrix = read_json(root / D114_PERMISSION_MATRIX, {}) or {}
    operator_statement = read_json(root / D114_OPERATOR_STATEMENT, {}) or {}
    d115_scope = read_json(root / D114_D115_SCOPE, {}) or {}

    errors = validate_d114(d114, permission_matrix, operator_statement, d115_scope)

    phrase_id = "d115-" + digest({
        "decision_id": d114.get("decision_id"),
        "review_id": d114.get("review_id"),
        "proposal_id": d114.get("proposal_id"),
    })

    phrase_statement = build_phrase_statement(phrase_id, d114, permission_matrix)
    pre_apply_lock = build_pre_apply_lock_report(phrase_id, d114, permission_matrix, operator_statement)
    d116_scope = build_d116_scope(phrase_id, d114)

    if pre_apply_lock.get("real_apply_permission") != "NOT_GRANTED":
        errors.append("pre-apply lock report expected real_apply_permission NOT_GRANTED")
    if pre_apply_lock.get("real_apply_approved_now") is not False:
        errors.append("pre-apply lock report real_apply_approved_now must be false")

    ok = not errors
    decision = "FINAL_APPLY_PHRASE_SCOPE_READY" if ok else "FINAL_APPLY_PHRASE_SCOPE_BLOCKED"
    result = "D115_FINAL_APPLY_PHRASE_SCOPE_CREATED" if ok else "D115_FINAL_APPLY_PHRASE_SCOPE_BLOCKED"

    if ok:
        write_json(root / PHRASE_STATEMENT_OUT, phrase_statement)
        write_json(root / PRE_APPLY_LOCK_OUT, pre_apply_lock)
        write_json(root / D116_SCOPE_OUT, d116_scope)

    report = {
        "state": "D115_FINAL_APPLY_PHRASE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_FINAL_APPLY_PHRASE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "phrase_id": phrase_id,
        "decision_id": d114.get("decision_id"),
        "review_id": d114.get("review_id"),
        "dry_run_id": d114.get("dry_run_id"),
        "proposal_id": d114.get("proposal_id"),
        "source_d114_report": D114_REPORT,
        "phrase_statement": phrase_statement if ok else {},
        "pre_apply_lock_report": pre_apply_lock if ok else {},
        "d116_scope": d116_scope if ok else {},
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
            "final_phrase_scope_only": True,
            "approval_for_d116_manual_window_only": ok,
            "approval_for_real_apply": False,
            "candidate_execution_allowed": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": [],
        },
        "summary": {
            "decision": decision,
            "phrase_id": phrase_id,
            "decision_id": d114.get("decision_id"),
            "proposal_id": d114.get("proposal_id"),
            "real_apply_current_status": "BLOCKED",
            "approval_scope": "D116_MANUAL_APPLY_WINDOW_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D116_GATE,
        },
        "success_condition": {
            "final_apply_phrase_scope_created": ok,
            "phrase_statement_created": ok,
            "pre_apply_lock_report_created": ok,
            "d116_scope_created": ok,
            "approval_for_d116_manual_window_only": ok,
            "approval_for_real_apply": False,
            "real_ai_called": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "protected_core_untouched": True,
            "next_step": "D116 may create manual apply window scope only. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_final_apply_phrase_scope(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.final_apply_phrase_scope import create_final_apply_phrase_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD115FinalApplyPhraseScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        decision_id = "d114-test"

        d114 = {
            "ok": True,
            "decision": "FINAL_HUMAN_APPLY_DECISION_SCOPE_READY",
            "decision_id": decision_id,
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
                "final_human_decision_only": True,
                "approval_for_d115_phrase_scope_only": True,
                "approval_for_real_apply": False,
                "candidate_execution_allowed": False,
            },
            "summary": {
                "real_apply_current_status": "BLOCKED",
                "approval_scope": "D115_FINAL_APPLY_PHRASE_SCOPE_ONLY",
                "next_step": "D115_FINAL_APPLY_PHRASE_SCOPE",
            },
        }

        permission_matrix = {
            "ok": True,
            "decision_id": decision_id,
            "real_apply_permission": "NOT_GRANTED",
            "d115_phrase_scope_permission": "GRANTED_FOR_PHRASE_SCOPE_ONLY",
            "permissions": {
                "create_d115_final_apply_phrase_scope": True,
                "prepare_final_apply_phrase_text": True,
                "prepare_operator_final_decision_statement": True,
                "real_apply_now": False,
                "auto_apply_now": False,
                "route_insert_now": False,
                "protected_core_mutation_now": False,
                "canonical_memory_overwrite_now": False,
                "external_ai_or_network_call_now": False,
                "sandbox_candidate_execution_now": False,
                "ai_git_commit_or_push_now": False,
            },
        }

        operator_statement = {
            "ok": True,
            "decision_id": decision_id,
            "human_decision_scope": "D115_FINAL_APPLY_PHRASE_SCOPE_ONLY",
            "d115_phrase_scope_approved": True,
            "real_apply_approved_now": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        d115_scope = {
            "ok": True,
            "decision_id": decision_id,
            "allowed_next_gate": "D115_FINAL_APPLY_PHRASE_SCOPE",
            "final_phrase_scope_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d114": False,
            "route_insert_allowed_after_d114": False,
            "protected_core_mutation_allowed_after_d114": False,
            "sandbox_candidate_execution_allowed_after_d114": False,
            "required_phrase_for_later_gate": "APPROVE_D115_FINAL_APPLY_PHRASE_SCOPE_ONLY",
        }

        write(root / "reports/d114_final_human_apply_decision_scope.json", d114)
        write(root / "reports/d114_final_apply_permission_matrix.json", permission_matrix)
        write(root / "reports/d114_final_operator_decision_statement.json", operator_statement)
        write(root / "reports/d114_d115_final_apply_phrase_scope.json", d115_scope)

        return td, root

    def test_creates_final_phrase_outputs(self):
        td, root = self.root()
        try:
            r = create_final_apply_phrase_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "FINAL_APPLY_PHRASE_SCOPE_READY")
            self.assertEqual(r["summary"]["real_apply_current_status"], "BLOCKED")
            self.assertEqual(r["summary"]["approval_scope"], "D116_MANUAL_APPLY_WINDOW_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["d116_scope"]["allowed_next_gate"], "D116_MANUAL_APPLY_WINDOW_SCOPE")
            self.assertTrue((root / "reports/d115_final_apply_phrase_scope.json").exists())
            self.assertTrue((root / "reports/d115_final_apply_phrase_statement.json").exists())
            self.assertTrue((root / "reports/d115_final_pre_apply_lock_report.json").exists())
            self.assertTrue((root / "reports/d115_d116_manual_apply_window_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d114(self):
        td, root = self.root()
        try:
            (root / "reports/d114_final_human_apply_decision_scope.json").unlink()
            r = create_final_apply_phrase_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_real_apply_permission_granted(self):
        td, root = self.root()
        try:
            p = root / "reports/d114_final_apply_permission_matrix.json"
            data = json.loads(p.read_text())
            data["real_apply_permission"] = "GRANTED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_final_apply_phrase_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_operator_claims_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d114_final_operator_decision_statement.json"
            data = json.loads(p.read_text())
            data["real_apply_approved_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_final_apply_phrase_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_scope_allows_apply_after_d114(self):
        td, root = self.root()
        try:
            p = root / "reports/d114_d115_final_apply_phrase_scope.json"
            data = json.loads(p.read_text())
            data["actual_apply_allowed_after_d114"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_final_apply_phrase_scope(root)
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

print("D115 FINAL APPLY PHRASE SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/final_apply_phrase_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d115_final_apply_phrase_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/final_apply_phrase_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d115_final_apply_phrase_scope", "-v"], check=True)

print("\n== run D115 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.final_apply_phrase_scope import create_final_apply_phrase_scope\n"
    "r=create_final_apply_phrase_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d115_final_apply_phrase_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/final_apply_phrase_scope.py",
    "tests/test_d115_final_apply_phrase_scope.py",
    "reports/d115_final_apply_phrase_scope.json",
    "reports/d115_final_apply_phrase_statement.json",
    "reports/d115_final_pre_apply_lock_report.json",
    "reports/d115_d116_manual_apply_window_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D115_FINAL_APPLY_PHRASE_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D115 final apply phrase scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D115 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD115 FINAL APPLY PHRASE SCOPE BOOT DONE")
