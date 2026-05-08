#!/usr/bin/env python3
# D99_FINAL_GUARDED_EXECUTION_CAPSULE_BOOT.py
#
# Creates D99 Final Guarded Execution Capsule.
#
# D99 validates D98 rollback/restore command pack and creates final capsule
# documentation for human review.
#
# It does NOT apply changes, insert routes, mutate protected core,
# execute rollback, delete candidates, call network/AI, run shell commands,
# or approve real apply.

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

D98_REPORT = "reports/d98_rollback_restore_command_pack.json"
D98_RESTORE = "reports/d98_restore_manifest_reference.json"
D98_ABORT = "reports/d98_pre_execution_abort_plan.json"
D98_D99_SCOPE = "reports/d98_d99_final_guarded_execution_capsule_scope.json"

OUT = "reports/d99_final_guarded_execution_capsule.json"
NO_APPLY_OUT = "reports/d99_final_no_apply_blocker_state.json"
CHECKLIST_OUT = "reports/d99_post_capsule_manual_review_checklist.json"
D100_SCOPE_OUT = "reports/d99_d100_controlled_execution_scope.json"

REQ_D98_DECISION = "ROLLBACK_RESTORE_COMMAND_PACK_READY"
REQ_D99_GATE = "D99_FINAL_GUARDED_EXECUTION_CAPSULE"
REQ_D99_PHRASE = "APPROVE_D99_FINAL_GUARDED_EXECUTION_CAPSULE_ONLY"

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

FORBIDDEN_REAL_ACTIONS = [
    "actual_apply",
    "route_insert",
    "protected_core_mutation",
    "canonical_memory_overwrite",
    "external_ai_network_call",
    "git_commit_or_push_by_ai",
    "execute_rollback_now",
    "delete_runtime_candidate",
]

D99_ALLOWED_TO_CREATE = [
    "final_guarded_execution_capsule",
    "final_no_apply_blocker_state",
    "post_capsule_manual_review_checklist",
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


def validate_d98(d98, restore, abort, scope):
    errors = []
    warnings = []

    if not d98:
        errors.append("missing D98 rollback restore command pack report")
        return errors, warnings

    if d98.get("ok") is not True:
        errors.append("D98 ok must be true")
    if d98.get("decision") != REQ_D98_DECISION:
        errors.append(f"D98 decision invalid: {d98.get('decision')}")

    guard = d98.get("guardrails") if isinstance(d98.get("guardrails"), dict) else {}
    check_false_flags("D98.guardrails", guard, errors)
    if guard.get("rollback_executed") is not False:
        errors.append("D98 rollback_executed must be false")
    if guard.get("restore_executed") is not False:
        errors.append("D98 restore_executed must be false")
    if guard.get("rollback_restore_documentation_only") is not True:
        errors.append("D98 rollback_restore_documentation_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D98 approval_for_real_apply must be false")

    pack = d98.get("rollback_restore_command_pack") if isinstance(d98.get("rollback_restore_command_pack"), dict) else {}
    if not pack:
        errors.append("D98 embedded rollback_restore_command_pack missing")
    else:
        if pack.get("ok") is not True:
            errors.append("D98 command pack ok must be true")
        if pack.get("commands_are_documentation_only") is not True:
            errors.append("D98 commands_are_documentation_only must be true")
        if pack.get("commands_must_not_be_executed_by_ai") is not True:
            errors.append("D98 commands_must_not_be_executed_by_ai must be true")
        if pack.get("next_required_gate") != REQ_D99_GATE:
            errors.append("D98 command pack next_required_gate must be D99")
        for item in FORBIDDEN_REAL_ACTIONS:
            if item not in pack.get("not_approved", []):
                errors.append(f"D98 command pack not_approved missing {item}")

    if not restore:
        errors.append("missing D98 restore manifest reference")
    else:
        if restore.get("ok") is not True:
            errors.append("D98 restore reference ok must be true")
        if restore.get("restore_reference_mode") != "DOCUMENTATION_ONLY":
            errors.append("D98 restore reference mode must be DOCUMENTATION_ONLY")
        if restore.get("restore_not_executed") is not True:
            errors.append("D98 restore_not_executed must be true")
        if not restore.get("source_snapshot_sha256"):
            errors.append("D98 restore source snapshot sha missing")

    if not abort:
        errors.append("missing D98 pre-execution abort plan")
    else:
        if abort.get("ok") is not True:
            errors.append("D98 abort plan ok must be true")
        must = abort.get("must_remain_false") if isinstance(abort.get("must_remain_false"), dict) else {}
        for key in [
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "runtime_code_mutated",
            "external_ai_called",
            "network_accessed",
            "git_commit_by_ai",
            "rollback_executed",
        ]:
            if must.get(key) is not False:
                errors.append(f"D98 abort plan must_remain_false.{key} must be false")
        if abort.get("human_review_required") is not True:
            errors.append("D98 abort human_review_required must be true")

    if not scope:
        errors.append("missing D98 D99 final guarded execution capsule scope")
    else:
        if scope.get("ok") is not True:
            errors.append("D98 D99 scope ok must be true")
        if scope.get("allowed_next_gate") != REQ_D99_GATE:
            errors.append("D98 D99 scope allowed_next_gate must be D99")
        for item in D99_ALLOWED_TO_CREATE:
            if item not in scope.get("d99_allowed_to_create", []):
                errors.append(f"D98 D99 scope missing allowed item: {item}")
        for item in FORBIDDEN_REAL_ACTIONS:
            if item not in scope.get("d99_must_not_execute", []):
                errors.append(f"D98 D99 scope missing must-not-execute item: {item}")
        if scope.get("apply_allowed_after_d98") is not False:
            errors.append("D98 scope apply_allowed_after_d98 must be false")
        if scope.get("route_insert_allowed_after_d98") is not False:
            errors.append("D98 scope route_insert_allowed_after_d98 must be false")
        if scope.get("protected_core_mutation_allowed_after_d98") is not False:
            errors.append("D98 scope protected_core_mutation_allowed_after_d98 must be false")
        if scope.get("required_phrase_for_later_gate") != REQ_D99_PHRASE:
            errors.append("D98 scope required phrase invalid")

    return errors, warnings


def build_no_apply_state(capsule_id, pack_id):
    return {
        "state": "D99_FINAL_NO_APPLY_BLOCKER_STATE",
        "ok": True,
        "capsule_id": capsule_id,
        "pack_id": pack_id,
        "created_at": now(),
        "apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
        "canonical_memory_mutation_allowed_now": False,
        "external_ai_call_allowed_now": False,
        "git_action_by_ai_allowed_now": False,
        "rollback_allowed_now": False,
        "restore_allowed_now": False,
        "reason": "D99 creates a final guarded execution capsule only. It does not grant execution permission.",
        "next_required_gate": "D100_CONTROLLED_HUMAN_EXECUTION_DECISION",
    }


def build_manual_checklist(capsule_id):
    return {
        "state": "D99_POST_CAPSULE_MANUAL_REVIEW_CHECKLIST",
        "ok": True,
        "capsule_id": capsule_id,
        "created_at": now(),
        "human_review_required": True,
        "checklist": [
            "Confirm D96 final local full regression passed.",
            "Confirm D97 protected-core no-touch hash snapshot exists.",
            "Confirm D97 no-route-insert reconfirmation exists.",
            "Confirm D98 rollback/restore pack is documentation-only.",
            "Confirm no actual apply was executed.",
            "Confirm no route insertion was executed.",
            "Confirm no protected-core mutation was executed.",
            "Confirm no external AI/network call is required.",
            "Confirm no AI git commit/push is allowed.",
            "Confirm D100 must be a separate explicit human decision gate.",
        ],
        "must_remain_false": {
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "runtime_code_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
        },
    }


def build_capsule(capsule_id, pack_id, reconfirmation_id, regression_id, d98, restore):
    return {
        "state": "D99_FINAL_GUARDED_EXECUTION_CAPSULE_ARTIFACT",
        "ok": True,
        "capsule_id": capsule_id,
        "pack_id": pack_id,
        "reconfirmation_id": reconfirmation_id,
        "regression_id": regression_id,
        "created_at": now(),
        "mode": "FINAL_GUARDED_CAPSULE_REVIEW_ONLY",
        "capsule_scope": "COLLECTED_EVIDENCE_AND_BLOCKERS_ONLY",
        "evidence_chain": [
            "D96_FINAL_LOCAL_FULL_REGRESSION_PASSED",
            "D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMED",
            "D98_ROLLBACK_RESTORE_COMMAND_PACK_READY",
        ],
        "source_snapshot_sha256": restore.get("source_snapshot_sha256"),
        "source_pack_decision": d98.get("decision"),
        "allowed_now": [
            "manual_review",
            "status_inspection",
            "prepare_D100_controlled_human_decision",
        ],
        "not_allowed_now": FORBIDDEN_REAL_ACTIONS,
        "apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
        "approval_for_real_apply": False,
        "next_required_gate": "D100_CONTROLLED_HUMAN_EXECUTION_DECISION",
    }


def build_d100_scope(capsule_id, pack_id):
    return {
        "state": "D99_D100_CONTROLLED_EXECUTION_SCOPE",
        "ok": True,
        "capsule_id": capsule_id,
        "pack_id": pack_id,
        "created_at": now(),
        "allowed_next_gate": "D100_CONTROLLED_HUMAN_EXECUTION_DECISION",
        "d100_allowed_to_create": [
            "controlled_human_execution_decision_request",
            "final_apply_permission_matrix",
            "human_operator_scope_statement",
        ],
        "d100_must_not_execute": FORBIDDEN_REAL_ACTIONS,
        "apply_allowed_after_d99": False,
        "route_insert_allowed_after_d99": False,
        "protected_core_mutation_allowed_after_d99": False,
        "required_phrase_for_later_gate": "APPROVE_D100_CONTROLLED_HUMAN_EXECUTION_DECISION_ONLY",
    }


def create_final_guarded_execution_capsule(root="."):
    root = Path(root).resolve()

    d98 = read_json(root / D98_REPORT, {}) or {}
    restore = read_json(root / D98_RESTORE, {}) or {}
    abort = read_json(root / D98_ABORT, {}) or {}
    scope = read_json(root / D98_D99_SCOPE, {}) or {}

    errors, warnings = validate_d98(d98, restore, abort, scope)

    pack_id = str(d98.get("pack_id") or restore.get("pack_id") or scope.get("pack_id") or "")
    reconfirmation_id = str(d98.get("reconfirmation_id") or scope.get("reconfirmation_id") or "")
    regression_id = str(d98.get("regression_id") or scope.get("regression_id") or "")
    package_id = str(d98.get("package_id") or "")

    capsule_id = "d99-" + digest({
        "pack_id": pack_id,
        "reconfirmation_id": reconfirmation_id,
        "regression_id": regression_id,
        "package_id": package_id,
        "d98_decision": d98.get("decision"),
        "source_snapshot_sha256": restore.get("source_snapshot_sha256"),
    })

    ok = not errors
    decision = "FINAL_GUARDED_EXECUTION_CAPSULE_READY" if ok else "FINAL_GUARDED_EXECUTION_CAPSULE_BLOCKED"
    result = "D99_FINAL_GUARDED_EXECUTION_CAPSULE_CREATED" if ok else "D99_FINAL_GUARDED_EXECUTION_CAPSULE_BLOCKED"

    capsule = build_capsule(capsule_id, pack_id, reconfirmation_id, regression_id, d98, restore)
    no_apply = build_no_apply_state(capsule_id, pack_id)
    checklist = build_manual_checklist(capsule_id)
    d100_scope = build_d100_scope(capsule_id, pack_id)

    if ok:
        write_json(root / NO_APPLY_OUT, no_apply)
        write_json(root / CHECKLIST_OUT, checklist)
        write_json(root / D100_SCOPE_OUT, d100_scope)

    report = {
        "state": "D99_FINAL_GUARDED_EXECUTION_CAPSULE",
        "result": result,
        "route": "FIELD_INTENT_FINAL_GUARDED_EXECUTION_CAPSULE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "capsule_id": capsule_id,
        "pack_id": pack_id,
        "reconfirmation_id": reconfirmation_id,
        "regression_id": regression_id,
        "package_id": package_id,
        "no_apply_blocker_path": str(root / NO_APPLY_OUT) if ok else "",
        "manual_review_checklist_path": str(root / CHECKLIST_OUT) if ok else "",
        "d100_scope_path": str(root / D100_SCOPE_OUT) if ok else "",
        "input_reports": {
            "d98_report_path": str(root / D98_REPORT),
            "d98_restore_path": str(root / D98_RESTORE),
            "d98_abort_path": str(root / D98_ABORT),
            "d98_d99_scope_path": str(root / D98_D99_SCOPE),
        },
        "final_guarded_execution_capsule": capsule if ok else {},
        "final_no_apply_blocker_state": no_apply if ok else {},
        "post_capsule_manual_review_checklist": checklist if ok else {},
        "d100_scope": d100_scope if ok else {},
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
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "capsule_id": capsule_id,
            "pack_id": pack_id,
            "reconfirmation_id": reconfirmation_id,
            "regression_id": regression_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "final_guarded_execution_capsule_created": ok,
            "final_no_apply_blocker_created": ok,
            "manual_review_checklist_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D100 may create a controlled human execution decision request. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_final_guarded_execution_capsule(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.final_guarded_execution_capsule import create_final_guarded_execution_capsule


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD99FinalGuardedExecutionCapsule(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d98_rollback_restore_command_pack.json", {
            "ok": True,
            "decision": "ROLLBACK_RESTORE_COMMAND_PACK_READY",
            "pack_id": "d98-test",
            "reconfirmation_id": "d97-test",
            "regression_id": "d96-test",
            "package_id": "d92-test",
            "rollback_restore_command_pack": {
                "ok": True,
                "commands_are_documentation_only": True,
                "commands_must_not_be_executed_by_ai": True,
                "next_required_gate": "D99_FINAL_GUARDED_EXECUTION_CAPSULE",
                "not_approved": [
                    "actual_apply",
                    "route_insert",
                    "protected_core_mutation",
                    "canonical_memory_overwrite",
                    "external_ai_network_call",
                    "git_commit_or_push_by_ai",
                    "execute_rollback_now",
                    "delete_runtime_candidate",
                ],
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
                "rollback_restore_documentation_only": True,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d98_restore_manifest_reference.json", {
            "ok": True,
            "restore_reference_mode": "DOCUMENTATION_ONLY",
            "restore_not_executed": True,
            "source_snapshot_sha256": "abc123",
        })

        write(root / "reports/d98_pre_execution_abort_plan.json", {
            "ok": True,
            "human_review_required": True,
            "must_remain_false": {
                "actual_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "runtime_code_mutated": False,
                "external_ai_called": False,
                "network_accessed": False,
                "git_commit_by_ai": False,
                "rollback_executed": False,
            },
        })

        write(root / "reports/d98_d99_final_guarded_execution_capsule_scope.json", {
            "ok": True,
            "pack_id": "d98-test",
            "reconfirmation_id": "d97-test",
            "regression_id": "d96-test",
            "allowed_next_gate": "D99_FINAL_GUARDED_EXECUTION_CAPSULE",
            "d99_allowed_to_create": [
                "final_guarded_execution_capsule",
                "final_no_apply_blocker_state",
                "post_capsule_manual_review_checklist",
            ],
            "d99_must_not_execute": [
                "actual_apply",
                "route_insert",
                "protected_core_mutation",
                "canonical_memory_overwrite",
                "external_ai_network_call",
                "git_commit_or_push_by_ai",
                "execute_rollback_now",
                "delete_runtime_candidate",
            ],
            "apply_allowed_after_d98": False,
            "route_insert_allowed_after_d98": False,
            "protected_core_mutation_allowed_after_d98": False,
            "required_phrase_for_later_gate": "APPROVE_D99_FINAL_GUARDED_EXECUTION_CAPSULE_ONLY",
        })

        return td, root

    def test_creates_final_guarded_capsule_only(self):
        td, root = self.root()
        try:
            r = create_final_guarded_execution_capsule(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "FINAL_GUARDED_EXECUTION_CAPSULE_READY")
            self.assertTrue(r["guardrails"]["final_guarded_capsule_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertFalse(r["final_guarded_execution_capsule"]["apply_allowed_now"])
            self.assertEqual(r["final_no_apply_blocker_state"]["next_required_gate"], "D100_CONTROLLED_HUMAN_EXECUTION_DECISION")
            self.assertTrue((root / "reports/d99_final_guarded_execution_capsule.json").exists())
            self.assertTrue((root / "reports/d99_final_no_apply_blocker_state.json").exists())
            self.assertTrue((root / "reports/d99_post_capsule_manual_review_checklist.json").exists())
            self.assertTrue((root / "reports/d99_d100_controlled_execution_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d98(self):
        td, root = self.root()
        try:
            (root / "reports/d98_rollback_restore_command_pack.json").unlink()
            r = create_final_guarded_execution_capsule(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "FINAL_GUARDED_EXECUTION_CAPSULE_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_d98_approves_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d98_rollback_restore_command_pack.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data))
            r = create_final_guarded_execution_capsule(root)
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

print("D99 FINAL GUARDED EXECUTION CAPSULE BOOT: repo =", ROOT)

Path("runtime_experimental/final_guarded_execution_capsule.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d99_final_guarded_execution_capsule.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/final_guarded_execution_capsule.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d99_final_guarded_execution_capsule", "-v"], check=True)

print("\n== run D99 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.final_guarded_execution_capsule import create_final_guarded_execution_capsule\n"
    "r=create_final_guarded_execution_capsule()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d99_final_guarded_execution_capsule.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/final_guarded_execution_capsule.py",
    "tests/test_d99_final_guarded_execution_capsule.py",
    "reports/d99_final_guarded_execution_capsule.json",
    "reports/d99_final_no_apply_blocker_state.json",
    "reports/d99_post_capsule_manual_review_checklist.json",
    "reports/d99_d100_controlled_execution_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D99_FINAL_GUARDED_EXECUTION_CAPSULE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D99 final guarded execution capsule"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D99 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD99 FINAL GUARDED EXECUTION CAPSULE BOOT DONE")
