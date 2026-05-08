#!/usr/bin/env python3
# D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE_BOOT.py
#
# Creates D101 One-Shot Manual Execution Capsule.
#
# D101 validates D100 controlled human execution decision and creates a
# one-shot manual execution capsule + manual command preview + post-execution
# required checks + abort-on-mismatch policy.
#
# D101 does NOT execute apply, does NOT insert routes, does NOT mutate protected
# core, does NOT call network/AI, does NOT execute rollback, does NOT delete
# candidates, and does NOT permit AI git actions.
#
# The capsule is HUMAN-MANUAL-ONLY documentation for a later, separate decision.

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

D100_REPORT = "reports/d100_controlled_human_execution_decision_request.json"
D100_MATRIX = "reports/d100_final_apply_permission_matrix.json"
D100_OPERATOR = "reports/d100_human_operator_scope_statement.json"
D100_D101_SCOPE = "reports/d100_d101_one_shot_manual_execution_capsule_scope.json"

OUT = "reports/d101_one_shot_manual_execution_capsule.json"
COMMAND_PREVIEW_OUT = "reports/d101_manual_command_preview.json"
POST_CHECKS_OUT = "reports/d101_post_execution_required_checks.json"
ABORT_POLICY_OUT = "reports/d101_abort_on_mismatch_policy.json"
D102_SCOPE_OUT = "reports/d101_d102_post_execution_verifier_scope.json"

REQ_D100_DECISION = "CONTROLLED_HUMAN_EXECUTION_DECISION_READY"
REQ_D101_GATE = "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE"
REQ_D101_PHRASE = "APPROVE_D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE_ONLY"

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

D101_ALLOWED_TO_CREATE = [
    "one_shot_manual_execution_capsule",
    "manual_command_preview",
    "post_execution_required_checks",
    "abort_on_mismatch_policy",
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


def validate_d100(d100, matrix, operator, scope):
    errors = []
    warnings = []

    if not d100:
        errors.append("missing D100 controlled human execution decision request")
        return errors, warnings

    if d100.get("ok") is not True:
        errors.append("D100 ok must be true")
    if d100.get("decision") != REQ_D100_DECISION:
        errors.append(f"D100 decision invalid: {d100.get('decision')}")

    guard = d100.get("guardrails") if isinstance(d100.get("guardrails"), dict) else {}
    check_false_flags("D100.guardrails", guard, errors)

    if guard.get("rollback_executed") is not False:
        errors.append("D100 rollback_executed must be false")
    if guard.get("restore_executed") is not False:
        errors.append("D100 restore_executed must be false")
    if guard.get("controlled_human_decision_only") is not True:
        errors.append("D100 controlled_human_decision_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D100 approval_for_real_apply must be false")
    if guard.get("approval_for_d101_creation_only") is not True:
        errors.append("D100 approval_for_d101_creation_only must be true")

    decision_request = d100.get("controlled_human_execution_decision_request") if isinstance(d100.get("controlled_human_execution_decision_request"), dict) else {}
    if not decision_request:
        errors.append("D100 embedded decision request missing")
    else:
        if decision_request.get("ok") is not True:
            errors.append("D100 decision request ok must be true")
        if decision_request.get("mode") != "CONTROLLED_HUMAN_DECISION_REQUEST_ONLY":
            errors.append("D100 decision request mode invalid")
        if decision_request.get("approved_next_gate_if_reviewed") != REQ_D101_GATE:
            errors.append("D100 approved_next_gate_if_reviewed must be D101")
        if decision_request.get("allowed_answer_now") != "APPROVE_D100_CONTROLLED_HUMAN_EXECUTION_DECISION_ONLY":
            errors.append("D100 allowed_answer_now invalid")

    if not matrix:
        errors.append("missing D100 final apply permission matrix")
    else:
        if matrix.get("ok") is not True:
            errors.append("D100 permission matrix ok must be true")
        if matrix.get("matrix_mode") != "HUMAN_DECISION_REQUEST_ONLY":
            errors.append("D100 permission matrix mode invalid")
        if matrix.get("next_required_gate") != REQ_D101_GATE:
            errors.append("D100 matrix next_required_gate must be D101")
        ai = matrix.get("ai_permissions") if isinstance(matrix.get("ai_permissions"), dict) else {}
        for key in [
            "run_real_apply",
            "insert_route",
            "mutate_protected_core",
            "overwrite_canonical_memory",
            "call_external_network_for_execution",
            "git_commit_or_push",
            "execute_rollback",
            "delete_runtime_candidate",
        ]:
            if ai.get(key) is not False:
                errors.append(f"D100 matrix ai_permissions.{key} must be false")
        for key in [
            "apply_allowed_now",
            "route_insert_allowed_now",
            "protected_core_mutation_allowed_now",
        ]:
            if matrix.get(key) is not False:
                errors.append(f"D100 matrix {key} must be false")

    if not operator:
        errors.append("missing D100 human operator scope statement")
    else:
        if operator.get("ok") is not True:
            errors.append("D100 operator scope ok must be true")
        if operator.get("required_phrase") != "APPROVE_D100_CONTROLLED_HUMAN_EXECUTION_DECISION_ONLY":
            errors.append("D100 operator required phrase invalid")
        if operator.get("approval_scope") != "D101_CAPSULE_CREATION_ONLY":
            errors.append("D100 operator approval_scope invalid")
        if operator.get("approved_next_gate_if_reviewed") != REQ_D101_GATE:
            errors.append("D100 operator approved_next_gate_if_reviewed must be D101")
        for item in FORBIDDEN_AUTONOMOUS_ACTIONS:
            if item not in operator.get("not_approved", []):
                errors.append(f"D100 operator not_approved missing {item}")

    if not scope:
        errors.append("missing D100 D101 one-shot manual execution capsule scope")
    else:
        if scope.get("ok") is not True:
            errors.append("D100 D101 scope ok must be true")
        if scope.get("allowed_next_gate") != REQ_D101_GATE:
            errors.append("D100 D101 scope allowed_next_gate must be D101")
        for item in D101_ALLOWED_TO_CREATE:
            if item not in scope.get("d101_allowed_to_create", []):
                errors.append(f"D100 D101 scope missing allowed item: {item}")
        for item in FORBIDDEN_AUTONOMOUS_ACTIONS:
            if item not in scope.get("d101_must_not_execute", []):
                errors.append(f"D100 D101 scope missing must-not-execute item: {item}")
        if scope.get("apply_allowed_after_d100") is not False:
            errors.append("D100 scope apply_allowed_after_d100 must be false")
        if scope.get("route_insert_allowed_after_d100") is not False:
            errors.append("D100 scope route_insert_allowed_after_d100 must be false")
        if scope.get("protected_core_mutation_allowed_after_d100") is not False:
            errors.append("D100 scope protected_core_mutation_allowed_after_d100 must be false")
        if scope.get("required_phrase_for_later_gate") != REQ_D101_PHRASE:
            errors.append("D100 scope required phrase invalid")

    return errors, warnings


def build_manual_command_preview(capsule_id, decision_id):
    return {
        "state": "D101_MANUAL_COMMAND_PREVIEW",
        "ok": True,
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "created_at": now(),
        "commands_are_preview_only": True,
        "commands_must_be_run_by_human_only": True,
        "ai_must_not_execute": True,
        "manual_preflight_commands": [
            "git status --short",
            "git diff --stat",
            "python -m unittest discover -s tests -v",
            "cat reports/d99_final_guarded_execution_capsule.json",
            "cat reports/d100_final_apply_permission_matrix.json",
        ],
        "manual_execution_placeholder": [
            "# Human operator may define exact one-shot command in a later gate.",
            "# D101 does not provide a real apply command.",
            "# No git apply / route insert / protected-core mutation is authorized here.",
        ],
        "blocked_commands": [
            "git apply",
            "git commit",
            "git push",
            "route insert",
            "git reset --hard",
            "git checkout -- <protected-core-path>",
            "python -c '<runtime mutation>'",
            "curl",
            "wget",
            "ssh",
        ],
    }


def build_post_execution_checks(capsule_id):
    return {
        "state": "D101_POST_EXECUTION_REQUIRED_CHECKS",
        "ok": True,
        "capsule_id": capsule_id,
        "created_at": now(),
        "required_after_any_future_manual_execution": [
            "git status --short",
            "git diff --stat",
            "python -m unittest discover -s tests -v",
            "python -m py_compile runtime_experimental/*.py",
            "confirm protected-core hash snapshot has expected relationship to approved scope",
            "confirm no route insertion occurred unless separately approved by later gate",
            "confirm no external AI/network execution occurred",
            "confirm rollback evidence is preserved",
            "create D102 post-execution verifier report",
        ],
        "must_remain_false_until_later_gate": {
            "ai_executed_apply": False,
            "ai_inserted_route": False,
            "ai_committed_or_pushed": False,
            "external_ai_called_for_execution": False,
        },
    }


def build_abort_policy(capsule_id):
    return {
        "state": "D101_ABORT_ON_MISMATCH_POLICY",
        "ok": True,
        "capsule_id": capsule_id,
        "created_at": now(),
        "abort_if": [
            "D100 permission matrix is missing",
            "D99 capsule is missing",
            "manual command differs from reviewed capsule scope",
            "manual command touches protected core without explicit later approval",
            "manual command inserts route without explicit later approval",
            "manual command requires network/external AI execution",
            "manual command would git commit or push automatically",
            "post-execution verifier cannot be created",
        ],
        "abort_action": "STOP_AND_REQUEST_HUMAN_REVIEW",
        "rollback_may_be_considered_only_after": "D102_POST_EXECUTION_VERIFIER",
        "rollback_not_executed_here": True,
    }


def build_capsule(capsule_id, decision_id, d100):
    return {
        "state": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE_ARTIFACT",
        "ok": True,
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "created_at": now(),
        "mode": "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_PREVIEW_ONLY",
        "manual_only": True,
        "ai_execution_allowed": False,
        "real_apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
        "capsule_basis": [
            "D99_FINAL_GUARDED_EXECUTION_CAPSULE_READY",
            "D100_CONTROLLED_HUMAN_EXECUTION_DECISION_READY",
            "D100_PERMISSION_MATRIX_REVIEWED",
        ],
        "approved_scope": "CREATE_MANUAL_ONE_SHOT_CAPSULE_ONLY",
        "not_approved": FORBIDDEN_AUTONOMOUS_ACTIONS,
        "source_decision_id": d100.get("decision_id"),
        "next_required_gate": "D102_POST_EXECUTION_VERIFIER",
    }


def build_d102_scope(capsule_id, decision_id):
    return {
        "state": "D101_D102_POST_EXECUTION_VERIFIER_SCOPE",
        "ok": True,
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "created_at": now(),
        "allowed_next_gate": "D102_POST_EXECUTION_VERIFIER",
        "d102_allowed_to_create": [
            "post_execution_verifier",
            "post_execution_evidence_report",
            "changed_files_manifest",
            "execution_integrity_summary",
        ],
        "d102_must_not_execute": FORBIDDEN_AUTONOMOUS_ACTIONS + [
            "run_manual_apply_now",
            "execute_post_fix_mutation",
        ],
        "apply_allowed_after_d101": False,
        "route_insert_allowed_after_d101": False,
        "protected_core_mutation_allowed_after_d101": False,
        "required_phrase_for_later_gate": "APPROVE_D102_POST_EXECUTION_VERIFIER_ONLY",
    }


def create_one_shot_manual_execution_capsule(root="."):
    root = Path(root).resolve()

    d100 = read_json(root / D100_REPORT, {}) or {}
    matrix = read_json(root / D100_MATRIX, {}) or {}
    operator = read_json(root / D100_OPERATOR, {}) or {}
    scope = read_json(root / D100_D101_SCOPE, {}) or {}

    errors, warnings = validate_d100(d100, matrix, operator, scope)

    decision_id = str(d100.get("decision_id") or matrix.get("decision_id") or operator.get("decision_id") or scope.get("decision_id") or "")
    capsule_source_id = str(d100.get("capsule_id") or matrix.get("capsule_id") or operator.get("capsule_id") or scope.get("capsule_id") or "")
    pack_id = str(d100.get("pack_id") or "")
    regression_id = str(d100.get("regression_id") or "")

    capsule_id = "d101-" + digest({
        "decision_id": decision_id,
        "capsule_source_id": capsule_source_id,
        "pack_id": pack_id,
        "regression_id": regression_id,
        "d100_decision": d100.get("decision"),
    })

    ok = not errors
    decision = "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_READY" if ok else "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_BLOCKED"
    result = "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE_CREATED" if ok else "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE_BLOCKED"

    capsule = build_capsule(capsule_id, decision_id, d100)
    command_preview = build_manual_command_preview(capsule_id, decision_id)
    post_checks = build_post_execution_checks(capsule_id)
    abort_policy = build_abort_policy(capsule_id)
    d102_scope = build_d102_scope(capsule_id, decision_id)

    if ok:
        write_json(root / COMMAND_PREVIEW_OUT, command_preview)
        write_json(root / POST_CHECKS_OUT, post_checks)
        write_json(root / ABORT_POLICY_OUT, abort_policy)
        write_json(root / D102_SCOPE_OUT, d102_scope)

    report = {
        "state": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
        "result": result,
        "route": "FIELD_INTENT_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "source_capsule_id": capsule_source_id,
        "pack_id": pack_id,
        "regression_id": regression_id,
        "manual_command_preview_path": str(root / COMMAND_PREVIEW_OUT) if ok else "",
        "post_execution_required_checks_path": str(root / POST_CHECKS_OUT) if ok else "",
        "abort_on_mismatch_policy_path": str(root / ABORT_POLICY_OUT) if ok else "",
        "d102_scope_path": str(root / D102_SCOPE_OUT) if ok else "",
        "input_reports": {
            "d100_report_path": str(root / D100_REPORT),
            "d100_matrix_path": str(root / D100_MATRIX),
            "d100_operator_path": str(root / D100_OPERATOR),
            "d100_d101_scope_path": str(root / D100_D101_SCOPE),
        },
        "one_shot_manual_execution_capsule": capsule if ok else {},
        "manual_command_preview": command_preview if ok else {},
        "post_execution_required_checks": post_checks if ok else {},
        "abort_on_mismatch_policy": abort_policy if ok else {},
        "d102_scope": d102_scope if ok else {},
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
            "manual_capsule_preview_only": True,
            "human_manual_only": True,
            "approval_for_real_apply": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "capsule_id": capsule_id,
            "decision_id": decision_id,
            "source_capsule_id": capsule_source_id,
            "pack_id": pack_id,
            "regression_id": regression_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "one_shot_manual_execution_capsule_created": ok,
            "manual_command_preview_created": ok,
            "post_execution_required_checks_created": ok,
            "abort_policy_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D102 may create a post-execution verifier. Real apply remains blocked here.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_one_shot_manual_execution_capsule(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.one_shot_manual_execution_capsule import create_one_shot_manual_execution_capsule


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD101OneShotManualExecutionCapsule(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d100_controlled_human_execution_decision_request.json", {
            "ok": True,
            "decision": "CONTROLLED_HUMAN_EXECUTION_DECISION_READY",
            "decision_id": "d100-test",
            "capsule_id": "d99-test",
            "pack_id": "d98-test",
            "regression_id": "d96-test",
            "controlled_human_execution_decision_request": {
                "ok": True,
                "mode": "CONTROLLED_HUMAN_DECISION_REQUEST_ONLY",
                "approved_next_gate_if_reviewed": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
                "allowed_answer_now": "APPROVE_D100_CONTROLLED_HUMAN_EXECUTION_DECISION_ONLY",
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
                "controlled_human_decision_only": True,
                "approval_for_real_apply": False,
                "approval_for_d101_creation_only": True,
            },
        })

        write(root / "reports/d100_final_apply_permission_matrix.json", {
            "ok": True,
            "decision_id": "d100-test",
            "capsule_id": "d99-test",
            "matrix_mode": "HUMAN_DECISION_REQUEST_ONLY",
            "ai_permissions": {
                "run_real_apply": False,
                "insert_route": False,
                "mutate_protected_core": False,
                "overwrite_canonical_memory": False,
                "call_external_network_for_execution": False,
                "git_commit_or_push": False,
                "execute_rollback": False,
                "delete_runtime_candidate": False,
            },
            "apply_allowed_now": False,
            "route_insert_allowed_now": False,
            "protected_core_mutation_allowed_now": False,
            "next_required_gate": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
        })

        write(root / "reports/d100_human_operator_scope_statement.json", {
            "ok": True,
            "decision_id": "d100-test",
            "capsule_id": "d99-test",
            "required_phrase": "APPROVE_D100_CONTROLLED_HUMAN_EXECUTION_DECISION_ONLY",
            "approval_scope": "D101_CAPSULE_CREATION_ONLY",
            "approved_next_gate_if_reviewed": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
            "not_approved": [
                "actual_apply_by_ai",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "external_ai_network_execution",
                "git_commit_or_push_by_ai",
                "execute_rollback_by_ai",
                "delete_runtime_candidate_by_ai",
            ],
        })

        write(root / "reports/d100_d101_one_shot_manual_execution_capsule_scope.json", {
            "ok": True,
            "decision_id": "d100-test",
            "capsule_id": "d99-test",
            "allowed_next_gate": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
            "d101_allowed_to_create": [
                "one_shot_manual_execution_capsule",
                "manual_command_preview",
                "post_execution_required_checks",
                "abort_on_mismatch_policy",
            ],
            "d101_must_not_execute": [
                "actual_apply_by_ai",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "external_ai_network_execution",
                "git_commit_or_push_by_ai",
                "execute_rollback_by_ai",
                "delete_runtime_candidate_by_ai",
            ],
            "apply_allowed_after_d100": False,
            "route_insert_allowed_after_d100": False,
            "protected_core_mutation_allowed_after_d100": False,
            "required_phrase_for_later_gate": "APPROVE_D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE_ONLY",
        })

        return td, root

    def test_creates_manual_capsule_preview_only(self):
        td, root = self.root()
        try:
            r = create_one_shot_manual_execution_capsule(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_READY")
            self.assertTrue(r["guardrails"]["manual_capsule_preview_only"])
            self.assertTrue(r["guardrails"]["human_manual_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertFalse(r["one_shot_manual_execution_capsule"]["real_apply_allowed_now"])
            self.assertEqual(r["one_shot_manual_execution_capsule"]["next_required_gate"], "D102_POST_EXECUTION_VERIFIER")
            self.assertTrue((root / "reports/d101_one_shot_manual_execution_capsule.json").exists())
            self.assertTrue((root / "reports/d101_manual_command_preview.json").exists())
            self.assertTrue((root / "reports/d101_post_execution_required_checks.json").exists())
            self.assertTrue((root / "reports/d101_abort_on_mismatch_policy.json").exists())
            self.assertTrue((root / "reports/d101_d102_post_execution_verifier_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d100(self):
        td, root = self.root()
        try:
            (root / "reports/d100_controlled_human_execution_decision_request.json").unlink()
            r = create_one_shot_manual_execution_capsule(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_ai_apply_allowed(self):
        td, root = self.root()
        try:
            p = root / "reports/d100_final_apply_permission_matrix.json"
            data = json.loads(p.read_text())
            data["ai_permissions"]["run_real_apply"] = True
            p.write_text(json.dumps(data))
            r = create_one_shot_manual_execution_capsule(root)
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

print("D101 ONE-SHOT MANUAL EXECUTION CAPSULE BOOT: repo =", ROOT)

Path("runtime_experimental/one_shot_manual_execution_capsule.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d101_one_shot_manual_execution_capsule.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/one_shot_manual_execution_capsule.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d101_one_shot_manual_execution_capsule", "-v"], check=True)

print("\n== run D101 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.one_shot_manual_execution_capsule import create_one_shot_manual_execution_capsule\n"
    "r=create_one_shot_manual_execution_capsule()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d101_one_shot_manual_execution_capsule.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/one_shot_manual_execution_capsule.py",
    "tests/test_d101_one_shot_manual_execution_capsule.py",
    "reports/d101_one_shot_manual_execution_capsule.json",
    "reports/d101_manual_command_preview.json",
    "reports/d101_post_execution_required_checks.json",
    "reports/d101_abort_on_mismatch_policy.json",
    "reports/d101_d102_post_execution_verifier_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D101 one-shot manual execution capsule"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D101 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD101 ONE-SHOT MANUAL EXECUTION CAPSULE BOOT DONE")
