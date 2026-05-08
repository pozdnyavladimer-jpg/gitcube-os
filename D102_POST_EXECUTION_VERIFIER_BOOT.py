#!/usr/bin/env python3
# D102_POST_EXECUTION_VERIFIER_BOOT.py
#
# Creates D102 Post-Execution Verifier.
#
# D102 validates D101 one-shot manual execution capsule and creates:
# - post-execution verifier
# - post-execution evidence report
# - changed files manifest
# - execution integrity summary
# - D103 rollback evidence builder scope
#
# D102 does NOT execute apply, does NOT insert routes, does NOT mutate protected
# core, does NOT call network/AI, does NOT execute rollback, does NOT delete
# candidates, does NOT run post-fix mutation, and does NOT permit AI git actions.
#
# Because the chain is still guarded, D102 records verification readiness and
# no-execution evidence. Real apply remains blocked.

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

D101_REPORT = "reports/d101_one_shot_manual_execution_capsule.json"
D101_COMMAND_PREVIEW = "reports/d101_manual_command_preview.json"
D101_POST_CHECKS = "reports/d101_post_execution_required_checks.json"
D101_ABORT_POLICY = "reports/d101_abort_on_mismatch_policy.json"
D101_D102_SCOPE = "reports/d101_d102_post_execution_verifier_scope.json"

OUT = "reports/d102_post_execution_verifier.json"
EVIDENCE_OUT = "reports/d102_post_execution_evidence_report.json"
CHANGED_FILES_OUT = "reports/d102_changed_files_manifest.json"
INTEGRITY_OUT = "reports/d102_execution_integrity_summary.json"
D103_SCOPE_OUT = "reports/d102_d103_rollback_evidence_builder_scope.json"

REQ_D101_DECISION = "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_READY"
REQ_D102_GATE = "D102_POST_EXECUTION_VERIFIER"
REQ_D102_PHRASE = "APPROVE_D102_POST_EXECUTION_VERIFIER_ONLY"

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
    "run_manual_apply_now",
    "execute_post_fix_mutation",
]

D102_ALLOWED_TO_CREATE = [
    "post_execution_verifier",
    "post_execution_evidence_report",
    "changed_files_manifest",
    "execution_integrity_summary",
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


def validate_d101(d101, command_preview, post_checks, abort_policy, scope):
    errors = []
    warnings = []

    if not d101:
        errors.append("missing D101 one-shot manual execution capsule report")
        return errors, warnings

    if d101.get("ok") is not True:
        errors.append("D101 ok must be true")
    if d101.get("decision") != REQ_D101_DECISION:
        errors.append(f"D101 decision invalid: {d101.get('decision')}")

    guard = d101.get("guardrails") if isinstance(d101.get("guardrails"), dict) else {}
    check_false_flags("D101.guardrails", guard, errors)

    if guard.get("rollback_executed") is not False:
        errors.append("D101 rollback_executed must be false")
    if guard.get("restore_executed") is not False:
        errors.append("D101 restore_executed must be false")
    if guard.get("manual_capsule_preview_only") is not True:
        errors.append("D101 manual_capsule_preview_only must be true")
    if guard.get("human_manual_only") is not True:
        errors.append("D101 human_manual_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D101 approval_for_real_apply must be false")

    capsule = d101.get("one_shot_manual_execution_capsule") if isinstance(d101.get("one_shot_manual_execution_capsule"), dict) else {}
    if not capsule:
        errors.append("D101 embedded one_shot_manual_execution_capsule missing")
    else:
        if capsule.get("ok") is not True:
            errors.append("D101 capsule ok must be true")
        if capsule.get("mode") != "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_PREVIEW_ONLY":
            errors.append("D101 capsule mode must be preview-only")
        if capsule.get("manual_only") is not True:
            errors.append("D101 capsule manual_only must be true")
        if capsule.get("ai_execution_allowed") is not False:
            errors.append("D101 capsule ai_execution_allowed must be false")
        for key in [
            "real_apply_allowed_now",
            "route_insert_allowed_now",
            "protected_core_mutation_allowed_now",
        ]:
            if capsule.get(key) is not False:
                errors.append(f"D101 capsule {key} must be false")
        if capsule.get("next_required_gate") != REQ_D102_GATE:
            errors.append("D101 capsule next_required_gate must be D102")

    if not command_preview:
        errors.append("missing D101 manual command preview")
    else:
        if command_preview.get("ok") is not True:
            errors.append("D101 command preview ok must be true")
        if command_preview.get("commands_are_preview_only") is not True:
            errors.append("D101 commands_are_preview_only must be true")
        if command_preview.get("commands_must_be_run_by_human_only") is not True:
            errors.append("D101 commands_must_be_run_by_human_only must be true")
        if command_preview.get("ai_must_not_execute") is not True:
            errors.append("D101 ai_must_not_execute must be true")

    if not post_checks:
        errors.append("missing D101 post-execution required checks")
    else:
        if post_checks.get("ok") is not True:
            errors.append("D101 post checks ok must be true")
        must = post_checks.get("must_remain_false_until_later_gate") if isinstance(post_checks.get("must_remain_false_until_later_gate"), dict) else {}
        for key in [
            "ai_executed_apply",
            "ai_inserted_route",
            "ai_committed_or_pushed",
            "external_ai_called_for_execution",
        ]:
            if must.get(key) is not False:
                errors.append(f"D101 post checks {key} must be false")

    if not abort_policy:
        errors.append("missing D101 abort-on-mismatch policy")
    else:
        if abort_policy.get("ok") is not True:
            errors.append("D101 abort policy ok must be true")
        if abort_policy.get("abort_action") != "STOP_AND_REQUEST_HUMAN_REVIEW":
            errors.append("D101 abort action invalid")
        if abort_policy.get("rollback_not_executed_here") is not True:
            errors.append("D101 rollback_not_executed_here must be true")

    if not scope:
        errors.append("missing D101 D102 post-execution verifier scope")
    else:
        if scope.get("ok") is not True:
            errors.append("D101 D102 scope ok must be true")
        if scope.get("allowed_next_gate") != REQ_D102_GATE:
            errors.append("D101 D102 scope allowed_next_gate must be D102")
        for item in D102_ALLOWED_TO_CREATE:
            if item not in scope.get("d102_allowed_to_create", []):
                errors.append(f"D101 D102 scope missing allowed item: {item}")
        for item in FORBIDDEN_AUTONOMOUS_ACTIONS:
            if item not in scope.get("d102_must_not_execute", []):
                errors.append(f"D101 D102 scope missing must-not-execute item: {item}")
        if scope.get("apply_allowed_after_d101") is not False:
            errors.append("D101 scope apply_allowed_after_d101 must be false")
        if scope.get("route_insert_allowed_after_d101") is not False:
            errors.append("D101 scope route_insert_allowed_after_d101 must be false")
        if scope.get("protected_core_mutation_allowed_after_d101") is not False:
            errors.append("D101 scope protected_core_mutation_allowed_after_d101 must be false")
        if scope.get("required_phrase_for_later_gate") != REQ_D102_PHRASE:
            errors.append("D101 scope required phrase invalid")

    return errors, warnings


def existing_report_paths(root: Path, prefix: str):
    reports_dir = root / "reports"
    if not reports_dir.exists():
        return []
    return sorted(
        p.relative_to(root).as_posix()
        for p in reports_dir.glob(prefix + "*")
        if p.is_file()
    )


def build_evidence_report(verifier_id, capsule_id, decision_id, root):
    return {
        "state": "D102_POST_EXECUTION_EVIDENCE_REPORT",
        "ok": True,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "created_at": now(),
        "evidence_mode": "NO_EXECUTION_OBSERVED_VERIFICATION_READINESS",
        "real_apply_observed": False,
        "route_insert_observed": False,
        "protected_core_mutation_observed": False,
        "external_ai_execution_observed": False,
        "rollback_execution_observed": False,
        "source_artifacts_seen": {
            "d101": existing_report_paths(root, "d101_"),
            "d100": existing_report_paths(root, "d100_"),
            "d99": existing_report_paths(root, "d99_"),
        },
        "human_review_required": True,
    }


def build_changed_files_manifest(verifier_id, capsule_id):
    return {
        "state": "D102_CHANGED_FILES_MANIFEST",
        "ok": True,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "created_at": now(),
        "manifest_mode": "DECLARATIVE_NO_EXECUTION_MANIFEST",
        "changed_files_collection_method": "not_collected_by_shell_in_runtime_module",
        "changed_files_from_manual_execution": [],
        "manual_execution_performed": False,
        "expected_future_collection_commands_for_human": [
            "git status --short",
            "git diff --name-only",
            "git diff --stat",
        ],
        "must_not_include_without_later_explicit_gate": [
            "app/orchestration/",
            "core/",
            "runtime/",
            "bridges/",
            "memory/",
        ],
    }


def build_integrity_summary(verifier_id, capsule_id):
    return {
        "state": "D102_EXECUTION_INTEGRITY_SUMMARY",
        "ok": True,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "created_at": now(),
        "integrity_decision": "POST_EXECUTION_VERIFIER_READY_NO_EXECUTION_RECORDED",
        "manual_execution_performed": False,
        "ai_execution_performed": False,
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "network_accessed": False,
        "external_ai_called": False,
        "git_commit_by_ai": False,
        "rollback_executed": False,
        "ready_for_d103": True,
        "reason": "D102 creates verifier evidence and no-execution integrity summary only. It does not execute apply.",
    }


def build_verifier(verifier_id, capsule_id, decision_id, d101):
    return {
        "state": "D102_POST_EXECUTION_VERIFIER_ARTIFACT",
        "ok": True,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "created_at": now(),
        "mode": "POST_EXECUTION_VERIFIER_NO_EXECUTION_RECORDED",
        "source_d101_decision": d101.get("decision"),
        "verifies": [
            "D101 manual capsule exists",
            "D101 command preview is human-only",
            "D101 post-execution required checks exist",
            "D101 abort-on-mismatch policy exists",
            "no AI execution occurred",
            "no real apply occurred",
            "no route insertion occurred",
            "no protected-core mutation occurred",
        ],
        "not_approved": FORBIDDEN_AUTONOMOUS_ACTIONS,
        "next_required_gate": "D103_ROLLBACK_EVIDENCE_BUILDER",
    }


def build_d103_scope(verifier_id, capsule_id):
    return {
        "state": "D102_D103_ROLLBACK_EVIDENCE_BUILDER_SCOPE",
        "ok": True,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "created_at": now(),
        "allowed_next_gate": "D103_ROLLBACK_EVIDENCE_BUILDER",
        "d103_allowed_to_create": [
            "rollback_evidence_builder",
            "rollback_evidence_bundle",
            "restore_point_reference",
            "rollback_readiness_summary",
        ],
        "d103_must_not_execute": FORBIDDEN_AUTONOMOUS_ACTIONS + [
            "execute_rollback_now",
            "restore_files_now",
            "delete_generated_candidate",
        ],
        "apply_allowed_after_d102": False,
        "route_insert_allowed_after_d102": False,
        "protected_core_mutation_allowed_after_d102": False,
        "required_phrase_for_later_gate": "APPROVE_D103_ROLLBACK_EVIDENCE_BUILDER_ONLY",
    }


def create_post_execution_verifier(root="."):
    root = Path(root).resolve()

    d101 = read_json(root / D101_REPORT, {}) or {}
    command_preview = read_json(root / D101_COMMAND_PREVIEW, {}) or {}
    post_checks = read_json(root / D101_POST_CHECKS, {}) or {}
    abort_policy = read_json(root / D101_ABORT_POLICY, {}) or {}
    scope = read_json(root / D101_D102_SCOPE, {}) or {}

    errors, warnings = validate_d101(d101, command_preview, post_checks, abort_policy, scope)

    capsule_id = str(d101.get("capsule_id") or command_preview.get("capsule_id") or post_checks.get("capsule_id") or scope.get("capsule_id") or "")
    decision_id = str(d101.get("decision_id") or command_preview.get("decision_id") or scope.get("decision_id") or "")
    source_capsule_id = str(d101.get("source_capsule_id") or "")
    pack_id = str(d101.get("pack_id") or "")
    regression_id = str(d101.get("regression_id") or "")

    verifier_id = "d102-" + digest({
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "source_capsule_id": source_capsule_id,
        "pack_id": pack_id,
        "regression_id": regression_id,
        "d101_decision": d101.get("decision"),
    })

    ok = not errors
    decision = "POST_EXECUTION_VERIFIER_READY" if ok else "POST_EXECUTION_VERIFIER_BLOCKED"
    result = "D102_POST_EXECUTION_VERIFIER_CREATED" if ok else "D102_POST_EXECUTION_VERIFIER_BLOCKED"

    verifier = build_verifier(verifier_id, capsule_id, decision_id, d101)
    evidence = build_evidence_report(verifier_id, capsule_id, decision_id, root)
    changed_files = build_changed_files_manifest(verifier_id, capsule_id)
    integrity = build_integrity_summary(verifier_id, capsule_id)
    d103_scope = build_d103_scope(verifier_id, capsule_id)

    if ok:
        write_json(root / EVIDENCE_OUT, evidence)
        write_json(root / CHANGED_FILES_OUT, changed_files)
        write_json(root / INTEGRITY_OUT, integrity)
        write_json(root / D103_SCOPE_OUT, d103_scope)

    report = {
        "state": "D102_POST_EXECUTION_VERIFIER",
        "result": result,
        "route": "FIELD_INTENT_POST_EXECUTION_VERIFIER",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "source_capsule_id": source_capsule_id,
        "pack_id": pack_id,
        "regression_id": regression_id,
        "evidence_report_path": str(root / EVIDENCE_OUT) if ok else "",
        "changed_files_manifest_path": str(root / CHANGED_FILES_OUT) if ok else "",
        "execution_integrity_summary_path": str(root / INTEGRITY_OUT) if ok else "",
        "d103_scope_path": str(root / D103_SCOPE_OUT) if ok else "",
        "input_reports": {
            "d101_report_path": str(root / D101_REPORT),
            "d101_command_preview_path": str(root / D101_COMMAND_PREVIEW),
            "d101_post_checks_path": str(root / D101_POST_CHECKS),
            "d101_abort_policy_path": str(root / D101_ABORT_POLICY),
            "d101_d102_scope_path": str(root / D101_D102_SCOPE),
        },
        "post_execution_verifier": verifier if ok else {},
        "post_execution_evidence_report": evidence if ok else {},
        "changed_files_manifest": changed_files if ok else {},
        "execution_integrity_summary": integrity if ok else {},
        "d103_scope": d103_scope if ok else {},
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
            "post_execution_verifier_only": True,
            "manual_execution_performed": False,
            "approval_for_real_apply": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "verifier_id": verifier_id,
            "capsule_id": capsule_id,
            "decision_id": decision_id,
            "source_capsule_id": source_capsule_id,
            "pack_id": pack_id,
            "regression_id": regression_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "post_execution_verifier_created": ok,
            "evidence_report_created": ok,
            "changed_files_manifest_created": ok,
            "integrity_summary_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D103 may create rollback evidence bundle. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_post_execution_verifier(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.post_execution_verifier import create_post_execution_verifier


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD102PostExecutionVerifier(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d101_one_shot_manual_execution_capsule.json", {
            "ok": True,
            "decision": "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_READY",
            "capsule_id": "d101-test",
            "decision_id": "d100-test",
            "source_capsule_id": "d99-test",
            "pack_id": "d98-test",
            "regression_id": "d96-test",
            "one_shot_manual_execution_capsule": {
                "ok": True,
                "mode": "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_PREVIEW_ONLY",
                "manual_only": True,
                "ai_execution_allowed": False,
                "real_apply_allowed_now": False,
                "route_insert_allowed_now": False,
                "protected_core_mutation_allowed_now": False,
                "next_required_gate": "D102_POST_EXECUTION_VERIFIER",
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
                "manual_capsule_preview_only": True,
                "human_manual_only": True,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d101_manual_command_preview.json", {
            "ok": True,
            "capsule_id": "d101-test",
            "decision_id": "d100-test",
            "commands_are_preview_only": True,
            "commands_must_be_run_by_human_only": True,
            "ai_must_not_execute": True,
        })

        write(root / "reports/d101_post_execution_required_checks.json", {
            "ok": True,
            "capsule_id": "d101-test",
            "must_remain_false_until_later_gate": {
                "ai_executed_apply": False,
                "ai_inserted_route": False,
                "ai_committed_or_pushed": False,
                "external_ai_called_for_execution": False,
            },
        })

        write(root / "reports/d101_abort_on_mismatch_policy.json", {
            "ok": True,
            "capsule_id": "d101-test",
            "abort_action": "STOP_AND_REQUEST_HUMAN_REVIEW",
            "rollback_not_executed_here": True,
        })

        write(root / "reports/d101_d102_post_execution_verifier_scope.json", {
            "ok": True,
            "capsule_id": "d101-test",
            "decision_id": "d100-test",
            "allowed_next_gate": "D102_POST_EXECUTION_VERIFIER",
            "d102_allowed_to_create": [
                "post_execution_verifier",
                "post_execution_evidence_report",
                "changed_files_manifest",
                "execution_integrity_summary",
            ],
            "d102_must_not_execute": [
                "actual_apply_by_ai",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "external_ai_network_execution",
                "git_commit_or_push_by_ai",
                "execute_rollback_by_ai",
                "delete_runtime_candidate_by_ai",
                "run_manual_apply_now",
                "execute_post_fix_mutation",
            ],
            "apply_allowed_after_d101": False,
            "route_insert_allowed_after_d101": False,
            "protected_core_mutation_allowed_after_d101": False,
            "required_phrase_for_later_gate": "APPROVE_D102_POST_EXECUTION_VERIFIER_ONLY",
        })

        return td, root

    def test_creates_post_execution_verifier_only(self):
        td, root = self.root()
        try:
            r = create_post_execution_verifier(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "POST_EXECUTION_VERIFIER_READY")
            self.assertTrue(r["guardrails"]["post_execution_verifier_only"])
            self.assertFalse(r["guardrails"]["manual_execution_performed"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["post_execution_verifier"]["next_required_gate"], "D103_ROLLBACK_EVIDENCE_BUILDER")
            self.assertTrue(r["execution_integrity_summary"]["ready_for_d103"])
            self.assertTrue((root / "reports/d102_post_execution_verifier.json").exists())
            self.assertTrue((root / "reports/d102_post_execution_evidence_report.json").exists())
            self.assertTrue((root / "reports/d102_changed_files_manifest.json").exists())
            self.assertTrue((root / "reports/d102_execution_integrity_summary.json").exists())
            self.assertTrue((root / "reports/d102_d103_rollback_evidence_builder_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d101(self):
        td, root = self.root()
        try:
            (root / "reports/d101_one_shot_manual_execution_capsule.json").unlink()
            r = create_post_execution_verifier(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "POST_EXECUTION_VERIFIER_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d101_one_shot_manual_execution_capsule.json"
            data = json.loads(p.read_text())
            data["guardrails"]["actual_apply_executed"] = True
            p.write_text(json.dumps(data))
            r = create_post_execution_verifier(root)
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

print("D102 POST-EXECUTION VERIFIER BOOT: repo =", ROOT)

Path("runtime_experimental/post_execution_verifier.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d102_post_execution_verifier.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/post_execution_verifier.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d102_post_execution_verifier", "-v"], check=True)

print("\n== run D102 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.post_execution_verifier import create_post_execution_verifier\n"
    "r=create_post_execution_verifier()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d102_post_execution_verifier.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/post_execution_verifier.py",
    "tests/test_d102_post_execution_verifier.py",
    "reports/d102_post_execution_verifier.json",
    "reports/d102_post_execution_evidence_report.json",
    "reports/d102_changed_files_manifest.json",
    "reports/d102_execution_integrity_summary.json",
    "reports/d102_d103_rollback_evidence_builder_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D102_POST_EXECUTION_VERIFIER_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D102 post-execution verifier"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D102 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD102 POST-EXECUTION VERIFIER BOOT DONE")
