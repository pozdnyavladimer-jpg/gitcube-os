#!/usr/bin/env python3
# D100_CONTROLLED_HUMAN_EXECUTION_DECISION_BOOT.py
#
# Creates D100 Controlled Human Execution Decision.
#
# D100 validates D99 final guarded execution capsule and creates a controlled
# human decision request + permission matrix + operator scope statement.
#
# It does NOT apply changes, insert routes, mutate protected core,
# call network/AI, execute rollback, delete candidates, run destructive shell,
# or approve autonomous execution.

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


MODULE = r"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D99_REPORT = "reports/d99_final_guarded_execution_capsule.json"
D99_NO_APPLY = "reports/d99_final_no_apply_blocker_state.json"
D99_CHECKLIST = "reports/d99_post_capsule_manual_review_checklist.json"
D99_D100_SCOPE = "reports/d99_d100_controlled_execution_scope.json"

OUT = "reports/d100_controlled_human_execution_decision_request.json"
PERMISSION_MATRIX_OUT = "reports/d100_final_apply_permission_matrix.json"
OPERATOR_SCOPE_OUT = "reports/d100_human_operator_scope_statement.json"
D101_SCOPE_OUT = "reports/d100_d101_one_shot_manual_execution_capsule_scope.json"

REQ_D99_DECISION = "FINAL_GUARDED_EXECUTION_CAPSULE_READY"
REQ_D100_GATE = "D100_CONTROLLED_HUMAN_EXECUTION_DECISION"
REQ_D100_PHRASE = "APPROVE_D100_CONTROLLED_HUMAN_EXECUTION_DECISION_ONLY"

FALSE_FLAGS = [
    "external_ai_called",
    "network_accessed",
    "runtime_code_mutated",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "actual_apply_executed",
    "route_inserted",
    "git_commit_by_ai",
]

FORBIDDEN_AUTONOMOUS_ACTIONS = [
    "actual_apply_by_ai",
    "route_insert_by_ai",
    "protected_core_mutation_by_ai",
    "canonical_memory_overwrite_by_ai",
    "external_ai_network_execution",
    "git_commit_or_push_by_ai",
    "execute_rollback_by_ai",
    "delete_runtime_candidate_by_ai",
]

D100_ALLOWED_TO_CREATE = [
    "controlled_human_execution_decision_request",
    "final_apply_permission_matrix",
    "human_operator_scope_statement",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def digest(data) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def check_false_flags(label, data, errors):
    for key in FALSE_FLAGS:
        if data.get(key) is not False:
            errors.append(f"{label}.{key} must be false")


def validate_d99(d99, no_apply, checklist, scope):
    errors = []
    warnings = []

    if not d99:
        errors.append("missing D99 final guarded execution capsule report")
        return errors, warnings

    if d99.get("ok") is not True:
        errors.append("D99 ok must be true")
    if d99.get("decision") != REQ_D99_DECISION:
        errors.append(f"D99 decision invalid: {d99.get('decision')}")

    guard = d99.get("guardrails") if isinstance(d99.get("guardrails"), dict) else {}
    check_false_flags("D99.guardrails", guard, errors)

    if guard.get("rollback_executed") is not False:
        errors.append("D99 rollback_executed must be false")
    if guard.get("restore_executed") is not False:
        errors.append("D99 restore_executed must be false")
    if guard.get("final_guarded_capsule_only") is not True:
        errors.append("D99 final_guarded_capsule_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D99 approval_for_real_apply must be false")

    capsule = d99.get("final_guarded_execution_capsule") if isinstance(d99.get("final_guarded_execution_capsule"), dict) else {}
    if not capsule:
        errors.append("D99 embedded final_guarded_execution_capsule missing")
    else:
        if capsule.get("ok") is not True:
            errors.append("D99 capsule ok must be true")
        if capsule.get("mode") != "FINAL_GUARDED_CAPSULE_REVIEW_ONLY":
            errors.append("D99 capsule mode must be review-only")
        if capsule.get("next_required_gate") != REQ_D100_GATE:
            errors.append("D99 capsule next_required_gate must be D100")
        for key in [
            "apply_allowed_now",
            "route_insert_allowed_now",
            "protected_core_mutation_allowed_now",
            "approval_for_real_apply",
        ]:
            if capsule.get(key) is not False:
                errors.append(f"D99 capsule {key} must be false")

    if not no_apply:
        errors.append("missing D99 no-apply blocker state")
    else:
        if no_apply.get("ok") is not True:
            errors.append("D99 no-apply ok must be true")
        for key in [
            "apply_allowed_now",
            "route_insert_allowed_now",
            "protected_core_mutation_allowed_now",
            "canonical_memory_mutation_allowed_now",
            "external_ai_call_allowed_now",
            "git_action_by_ai_allowed_now",
            "rollback_allowed_now",
            "restore_allowed_now",
        ]:
            if no_apply.get(key) is not False:
                errors.append(f"D99 no-apply {key} must be false")
        if no_apply.get("next_required_gate") != REQ_D100_GATE:
            errors.append("D99 no-apply next_required_gate must be D100")

    if not checklist:
        errors.append("missing D99 post-capsule manual review checklist")
    else:
        if checklist.get("ok") is not True:
            errors.append("D99 checklist ok must be true")
        if checklist.get("human_review_required") is not True:
            errors.append("D99 checklist human_review_required must be true")
        must = checklist.get("must_remain_false") if isinstance(checklist.get("must_remain_false"), dict) else {}
        for key in FALSE_FLAGS:
            if must.get(key) is not False:
                errors.append(f"D99 checklist must_remain_false.{key} must be false")

    if not scope:
        errors.append("missing D99 D100 controlled execution scope")
    else:
        if scope.get("ok") is not True:
            errors.append("D99 D100 scope ok must be true")
        if scope.get("allowed_next_gate") != REQ_D100_GATE:
            errors.append("D99 D100 scope allowed_next_gate must be D100")
        for item in D100_ALLOWED_TO_CREATE:
            if item not in scope.get("d100_allowed_to_create", []):
                errors.append(f"D99 D100 scope missing allowed item: {item}")
        for item in [
            "actual_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "git_commit_or_push_by_ai",
            "execute_rollback_now",
            "delete_runtime_candidate",
        ]:
            if item not in scope.get("d100_must_not_execute", []):
                errors.append(f"D99 D100 scope missing must-not-execute item: {item}")
        if scope.get("apply_allowed_after_d99") is not False:
            errors.append("D99 scope apply_allowed_after_d99 must be false")
        if scope.get("route_insert_allowed_after_d99") is not False:
            errors.append("D99 scope route_insert_allowed_after_d99 must be false")
        if scope.get("protected_core_mutation_allowed_after_d99") is not False:
            errors.append("D99 scope protected_core_mutation_allowed_after_d99 must be false")
        if scope.get("required_phrase_for_later_gate") != REQ_D100_PHRASE:
            errors.append("D99 scope required phrase invalid")

    return errors, warnings


def build_permission_matrix(decision_id, capsule_id):
    return {
        "state": "D100_FINAL_APPLY_PERMISSION_MATRIX",
        "ok": True,
        "decision_id": decision_id,
        "capsule_id": capsule_id,
        "created_at": now(),
        "matrix_mode": "HUMAN_DECISION_REQUEST_ONLY",
        "ai_permissions": {
            "propose_json": True,
            "write_candidate_reports": True,
            "run_real_apply": False,
            "insert_route": False,
            "mutate_protected_core": False,
            "overwrite_canonical_memory": False,
            "call_external_network_for_execution": False,
            "git_commit_or_push": False,
            "execute_rollback": False,
            "delete_runtime_candidate": False,
        },
        "human_permissions": {
            "review_capsule": True,
            "approve_next_gate_d101": True,
            "run_manual_commands_later": "D101_OR_LATER_ONLY",
            "approve_real_apply_now": False,
        },
        "system_permissions": {
            "verify_reports": True,
            "block_on_missing_evidence": True,
            "create_d101_scope": True,
            "execute_apply_now": False,
        },
        "apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
        "next_required_gate": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
    }


def build_operator_scope_statement(decision_id, capsule_id):
    return {
        "state": "D100_HUMAN_OPERATOR_SCOPE_STATEMENT",
        "ok": True,
        "decision_id": decision_id,
        "capsule_id": capsule_id,
        "created_at": now(),
        "required_phrase": REQ_D100_PHRASE,
        "human_statement": (
            "I approve only the creation of a D101 one-shot manual execution capsule. "
            "This does not authorize autonomous AI apply, route insertion, protected-core mutation, "
            "canonical memory overwrite, external AI/network execution, rollback execution, or AI git actions."
        ),
        "approval_scope": "D101_CAPSULE_CREATION_ONLY",
        "not_approved": FORBIDDEN_AUTONOMOUS_ACTIONS,
        "approved_next_gate_if_reviewed": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
    }


def build_decision_request(decision_id, capsule_id, pack_id, regression_id):
    return {
        "state": "D100_CONTROLLED_HUMAN_EXECUTION_DECISION_ARTIFACT",
        "ok": True,
        "decision_id": decision_id,
        "capsule_id": capsule_id,
        "pack_id": pack_id,
        "regression_id": regression_id,
        "created_at": now(),
        "mode": "CONTROLLED_HUMAN_DECISION_REQUEST_ONLY",
        "decision_question": "May this reviewed D99 capsule move to D101 one-shot manual execution capsule planning?",
        "allowed_answer_now": "APPROVE_D100_CONTROLLED_HUMAN_EXECUTION_DECISION_ONLY",
        "approved_next_gate_if_reviewed": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
        "blocked_now": [
            "no autonomous AI apply",
            "no immediate real apply",
            "no route insertion",
            "no protected-core mutation",
            "no canonical memory overwrite",
            "no external AI/network execution",
            "no AI git commit or push",
            "no rollback execution",
        ],
        "required_before_any_future_real_apply": [
            "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
            "D102_POST_EXECUTION_VERIFIER",
            "D103_ROLLBACK_EVIDENCE_BUILDER",
            "D104_FINAL_AUDIT_LEDGER",
        ],
    }


def build_d101_scope(decision_id, capsule_id):
    return {
        "state": "D100_D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE_SCOPE",
        "ok": True,
        "decision_id": decision_id,
        "capsule_id": capsule_id,
        "created_at": now(),
        "allowed_next_gate": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
        "d101_allowed_to_create": [
            "one_shot_manual_execution_capsule",
            "manual_command_preview",
            "post_execution_required_checks",
            "abort_on_mismatch_policy",
        ],
        "d101_must_not_execute": FORBIDDEN_AUTONOMOUS_ACTIONS,
        "apply_allowed_after_d100": False,
        "route_insert_allowed_after_d100": False,
        "protected_core_mutation_allowed_after_d100": False,
        "required_phrase_for_later_gate": "APPROVE_D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE_ONLY",
    }


def create_controlled_human_execution_decision(root="."):
    root = Path(root).resolve()

    d99 = read_json(root / D99_REPORT, {}) or {}
    no_apply = read_json(root / D99_NO_APPLY, {}) or {}
    checklist = read_json(root / D99_CHECKLIST, {}) or {}
    scope = read_json(root / D99_D100_SCOPE, {}) or {}

    errors, warnings = validate_d99(d99, no_apply, checklist, scope)

    capsule_id = str(d99.get("capsule_id") or no_apply.get("capsule_id") or checklist.get("capsule_id") or scope.get("capsule_id") or "")
    pack_id = str(d99.get("pack_id") or no_apply.get("pack_id") or scope.get("pack_id") or "")
    regression_id = str(d99.get("regression_id") or "")
    package_id = str(d99.get("package_id") or "")

    decision_id = "d100-" + digest({
        "capsule_id": capsule_id,
        "pack_id": pack_id,
        "regression_id": regression_id,
        "package_id": package_id,
        "d99_decision": d99.get("decision"),
    })

    ok = not errors
    decision = "CONTROLLED_HUMAN_EXECUTION_DECISION_READY" if ok else "CONTROLLED_HUMAN_EXECUTION_DECISION_BLOCKED"
    result = "D100_CONTROLLED_HUMAN_EXECUTION_DECISION_CREATED" if ok else "D100_CONTROLLED_HUMAN_EXECUTION_DECISION_BLOCKED"

    decision_request = build_decision_request(decision_id, capsule_id, pack_id, regression_id)
    permission_matrix = build_permission_matrix(decision_id, capsule_id)
    operator_scope = build_operator_scope_statement(decision_id, capsule_id)
    d101_scope = build_d101_scope(decision_id, capsule_id)

    if ok:
        write_json(root / PERMISSION_MATRIX_OUT, permission_matrix)
        write_json(root / OPERATOR_SCOPE_OUT, operator_scope)
        write_json(root / D101_SCOPE_OUT, d101_scope)

    report = {
        "state": "D100_CONTROLLED_HUMAN_EXECUTION_DECISION",
        "result": result,
        "route": "FIELD_INTENT_CONTROLLED_HUMAN_EXECUTION_DECISION",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "decision_id": decision_id,
        "capsule_id": capsule_id,
        "pack_id": pack_id,
        "regression_id": regression_id,
        "package_id": package_id,
        "permission_matrix_path": str(root / PERMISSION_MATRIX_OUT) if ok else "",
        "operator_scope_statement_path": str(root / OPERATOR_SCOPE_OUT) if ok else "",
        "d101_scope_path": str(root / D101_SCOPE_OUT) if ok else "",
        "input_reports": {
            "d99_report_path": str(root / D99_REPORT),
            "d99_no_apply_path": str(root / D99_NO_APPLY),
            "d99_checklist_path": str(root / D99_CHECKLIST),
            "d99_d100_scope_path": str(root / D99_D100_SCOPE),
        },
        "controlled_human_execution_decision_request": decision_request if ok else {},
        "final_apply_permission_matrix": permission_matrix if ok else {},
        "human_operator_scope_statement": operator_scope if ok else {},
        "d101_scope": d101_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
            "controlled_human_decision_only": True,
            "approval_for_real_apply": False,
            "approval_for_d101_creation_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "decision_id": decision_id,
            "capsule_id": capsule_id,
            "pack_id": pack_id,
            "regression_id": regression_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "controlled_human_execution_decision_created": ok,
            "permission_matrix_created": ok,
            "operator_scope_statement_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D101 may create a one-shot manual execution capsule. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_controlled_human_execution_decision(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.controlled_human_execution_decision import create_controlled_human_execution_decision


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD100ControlledHumanExecutionDecision(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d99_final_guarded_execution_capsule.json", {
            "ok": True,
            "decision": "FINAL_GUARDED_EXECUTION_CAPSULE_READY",
            "capsule_id": "d99-test",
            "pack_id": "d98-test",
            "regression_id": "d96-test",
            "package_id": "d92-test",
            "final_guarded_execution_capsule": {
                "ok": True,
                "mode": "FINAL_GUARDED_CAPSULE_REVIEW_ONLY",
                "next_required_gate": "D100_CONTROLLED_HUMAN_EXECUTION_DECISION",
                "apply_allowed_now": False,
                "route_insert_allowed_now": False,
                "protected_core_mutation_allowed_now": False,
                "approval_for_real_apply": False,
            },
            "guardrails": {
                "external_ai_called": False,
                "network_accessed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
                "rollback_executed": False,
                "restore_executed": False,
                "final_guarded_capsule_only": True,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d99_final_no_apply_blocker_state.json", {
            "ok": True,
            "capsule_id": "d99-test",
            "pack_id": "d98-test",
            "apply_allowed_now": False,
            "route_insert_allowed_now": False,
            "protected_core_mutation_allowed_now": False,
            "canonical_memory_mutation_allowed_now": False,
            "external_ai_call_allowed_now": False,
            "git_action_by_ai_allowed_now": False,
            "rollback_allowed_now": False,
            "restore_allowed_now": False,
            "next_required_gate": "D100_CONTROLLED_HUMAN_EXECUTION_DECISION",
        })

        write(root / "reports/d99_post_capsule_manual_review_checklist.json", {
            "ok": True,
            "capsule_id": "d99-test",
            "human_review_required": True,
            "must_remain_false": {
                "external_ai_called": False,
                "network_accessed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
            },
        })

        write(root / "reports/d99_d100_controlled_execution_scope.json", {
            "ok": True,
            "capsule_id": "d99-test",
            "pack_id": "d98-test",
            "allowed_next_gate": "D100_CONTROLLED_HUMAN_EXECUTION_DECISION",
            "d100_allowed_to_create": [
                "controlled_human_execution_decision_request",
                "final_apply_permission_matrix",
                "human_operator_scope_statement",
            ],
            "d100_must_not_execute": [
                "actual_apply",
                "route_insert",
                "protected_core_mutation",
                "canonical_memory_overwrite",
                "external_ai_network_call",
                "git_commit_or_push_by_ai",
                "execute_rollback_now",
                "delete_runtime_candidate",
            ],
            "apply_allowed_after_d99": False,
            "route_insert_allowed_after_d99": False,
            "protected_core_mutation_allowed_after_d99": False,
            "required_phrase_for_later_gate": "APPROVE_D100_CONTROLLED_HUMAN_EXECUTION_DECISION_ONLY",
        })

        return td, root

    def test_creates_controlled_human_decision_only(self):
        td, root = self.root()
        try:
            r = create_controlled_human_execution_decision(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "CONTROLLED_HUMAN_EXECUTION_DECISION_READY")
            self.assertTrue(r["guardrails"]["controlled_human_decision_only"])
            self.assertTrue(r["guardrails"]["approval_for_d101_creation_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["final_apply_permission_matrix"]["next_required_gate"], "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE")
            self.assertTrue((root / "reports/d100_controlled_human_execution_decision_request.json").exists())
            self.assertTrue((root / "reports/d100_final_apply_permission_matrix.json").exists())
            self.assertTrue((root / "reports/d100_human_operator_scope_statement.json").exists())
            self.assertTrue((root / "reports/d100_d101_one_shot_manual_execution_capsule_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d99(self):
        td, root = self.root()
        try:
            (root / "reports/d99_final_guarded_execution_capsule.json").unlink()
            r = create_controlled_human_execution_decision(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "CONTROLLED_HUMAN_EXECUTION_DECISION_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_d99_approves_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d99_final_guarded_execution_capsule.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data))
            r = create_controlled_human_execution_decision(root)
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

print("D100 CONTROLLED HUMAN EXECUTION DECISION BOOT: repo =", ROOT)

Path("runtime_experimental/controlled_human_execution_decision.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d100_controlled_human_execution_decision.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/controlled_human_execution_decision.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d100_controlled_human_execution_decision", "-v"], check=True)

print("\n== run D100 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.controlled_human_execution_decision import create_controlled_human_execution_decision\n"
    "r=create_controlled_human_execution_decision()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d100_controlled_human_execution_decision_request.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/controlled_human_execution_decision.py",
    "tests/test_d100_controlled_human_execution_decision.py",
    "reports/d100_controlled_human_execution_decision_request.json",
    "reports/d100_final_apply_permission_matrix.json",
    "reports/d100_human_operator_scope_statement.json",
    "reports/d100_d101_one_shot_manual_execution_capsule_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D100_CONTROLLED_HUMAN_EXECUTION_DECISION_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D100 controlled human execution decision"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D100 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD100 CONTROLLED HUMAN EXECUTION DECISION BOOT DONE")
