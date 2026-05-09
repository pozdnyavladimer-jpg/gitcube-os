#!/usr/bin/env python3
# D112_DRY_RUN_APPLY_SCOPE_BOOT.py
#
# Creates D112 Dry-Run Apply Scope.
#
# D112 consumes D111 explicit approval artifacts and creates dry-run-only planning artifacts:
# - runtime_experimental/dry_run_apply_scope.py
# - tests/test_d112_dry_run_apply_scope.py
# - reports/d112_dry_run_apply_scope.json
# - reports/d112_dry_run_plan.json
# - reports/d112_dry_run_patch_preview.json
# - reports/d112_no_touch_verification.json
# - reports/d112_d113_final_apply_review_scope.json
#
# This is DRY-RUN ONLY.
# It does NOT approve real apply.
# It does NOT execute AI proposal commands.
# It does NOT apply patches.
# It does NOT mutate core/runtime/app/memory/routes.
# It does NOT commit/push by AI.

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

D111_REPORT = "reports/d111_explicit_approval_gate.json"
D111_APPROVAL_STATEMENT = "reports/d111_explicit_approval_statement.json"
D111_OPERATOR_DECISION = "reports/d111_operator_decision_record.json"
D111_D112_SCOPE = "reports/d111_d112_dry_run_apply_scope.json"
D110_REVIEW_SUMMARY = "reports/d110_proposal_review_summary.json"

OUT = "reports/d112_dry_run_apply_scope.json"
DRY_RUN_PLAN_OUT = "reports/d112_dry_run_plan.json"
PATCH_PREVIEW_OUT = "reports/d112_dry_run_patch_preview.json"
NO_TOUCH_OUT = "reports/d112_no_touch_verification.json"
D113_SCOPE_OUT = "reports/d112_d113_final_apply_review_scope.json"

REQ_D111_DECISION = "EXPLICIT_APPROVAL_GATE_READY"
REQ_D112_GATE = "D112_DRY_RUN_APPLY_SCOPE"
REQ_D113_GATE = "D113_FINAL_APPLY_REVIEW_SCOPE"
REQ_D111_SCOPE = "D112_DRY_RUN_APPLY_SCOPE_ONLY"
REQ_D111_OPERATOR_DECISION = "APPROVED_FOR_D112_DRY_RUN_SCOPE_ONLY"

BLOCKED_PREFIXES = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]

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


def starts(path, prefixes):
    return any(str(path).startswith(prefix) for prefix in prefixes)


def validate_d111(d111, approval_statement, operator_decision, d112_scope, review_summary):
    errors = []

    if not d111:
        errors.append("missing D111 explicit approval gate report")
        return errors

    if d111.get("ok") is not True:
        errors.append("D111 ok must be true")
    if d111.get("decision") != REQ_D111_DECISION:
        errors.append("D111 decision must be EXPLICIT_APPROVAL_GATE_READY")

    guard = d111.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D111 guardrails.{key} must be false")
    if guard.get("explicit_approval_gate_only") is not True:
        errors.append("D111 explicit_approval_gate_only must be true")
    if guard.get("approval_for_d112_dry_run_only") is not True:
        errors.append("D111 approval_for_d112_dry_run_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D111 approval_for_real_apply must be false")
    if guard.get("candidate_execution_allowed") is not False:
        errors.append("D111 candidate_execution_allowed must be false")

    summary = d111.get("summary", {})
    if summary.get("approval_scope") != REQ_D111_SCOPE:
        errors.append("D111 approval_scope must be D112 dry-run only")
    if summary.get("next_step") != REQ_D112_GATE:
        errors.append("D111 summary next_step must be D112")

    if not approval_statement:
        errors.append("missing D111 approval statement")
    else:
        if approval_statement.get("ok") is not True:
            errors.append("D111 approval statement ok must be true")
        if approval_statement.get("approval_scope") != REQ_D111_SCOPE:
            errors.append("D111 approval statement scope invalid")
        if approval_statement.get("approval_for_real_apply") is not False:
            errors.append("D111 approval statement approval_for_real_apply must be false")
        for key in ["actual_apply_executed", "candidate_executed"]:
            if approval_statement.get(key) is not False:
                errors.append(f"D111 approval statement {key} must be false")

    if not operator_decision:
        errors.append("missing D111 operator decision")
    else:
        if operator_decision.get("ok") is not True:
            errors.append("D111 operator decision ok must be true")
        if operator_decision.get("decision") != REQ_D111_OPERATOR_DECISION:
            errors.append("D111 operator decision invalid")
        if operator_decision.get("operator_phrase_matched") is not True:
            errors.append("D111 operator phrase must match")
        if operator_decision.get("approval_for_real_apply") is not False:
            errors.append("D111 operator decision approval_for_real_apply must be false")
        for key in [
            "actual_apply_executed",
            "candidate_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
        ]:
            if operator_decision.get(key) is not False:
                errors.append(f"D111 operator decision {key} must be false")

    if not d112_scope:
        errors.append("missing D111 D112 dry-run apply scope")
    else:
        if d112_scope.get("ok") is not True:
            errors.append("D111 D112 scope ok must be true")
        if d112_scope.get("allowed_next_gate") != REQ_D112_GATE:
            errors.append("D111 D112 scope allowed_next_gate must be D112")
        if d112_scope.get("dry_run_only") is not True:
            errors.append("D111 D112 scope dry_run_only must be true")
        if d112_scope.get("human_review_required") is not True:
            errors.append("D111 D112 scope human_review_required must be true")
        for key in [
            "actual_apply_allowed_after_d111",
            "route_insert_allowed_after_d111",
            "protected_core_mutation_allowed_after_d111",
            "sandbox_candidate_execution_allowed_after_d111",
        ]:
            if d112_scope.get(key) is not False:
                errors.append(f"D111 D112 scope {key} must be false")

    if review_summary:
        for path in review_summary.get("candidate_files", []):
            if starts(str(path), BLOCKED_PREFIXES):
                errors.append(f"D110 review summary contains blocked candidate path: {path}")

    return errors


def build_dry_run_plan(dry_run_id, d111, approval_statement, operator_decision, d112_scope, review_summary):
    candidate_files = []
    target_scope = ""
    proposal_id = d111.get("proposal_id")
    if isinstance(review_summary, dict):
        candidate_files = list(review_summary.get("candidate_files", []))
        target_scope = review_summary.get("target_scope") or ""
        proposal_id = review_summary.get("proposal_id") or proposal_id

    return {
        "state": "D112_DRY_RUN_PLAN",
        "ok": True,
        "dry_run_id": dry_run_id,
        "approval_id": d111.get("approval_id"),
        "proposal_id": proposal_id,
        "created_at": now(),
        "mode": "DRY_RUN_ONLY_NO_FILE_MUTATION",
        "source_approval_scope": approval_statement.get("approval_scope"),
        "operator_decision": operator_decision.get("decision"),
        "target_scope": target_scope,
        "candidate_files": candidate_files,
        "planned_steps": [
            "Load proposal and approval evidence",
            "Prepare dry-run plan only",
            "Prepare patch preview metadata only",
            "Verify no protected files are touched",
            "Verify no real apply is executed",
            "Prepare D113 final apply review scope",
        ],
        "not_planned": [
            "real_apply",
            "auto_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "shell_exec_from_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "sandbox_candidate_execution",
        ],
        "actual_apply_executed": False,
        "candidate_executed": False,
        "dry_run_only": True,
    }


def build_patch_preview(dry_run_id, plan):
    blocked_hits = [p for p in plan.get("candidate_files", []) if starts(str(p), BLOCKED_PREFIXES)]
    return {
        "state": "D112_DRY_RUN_PATCH_PREVIEW",
        "ok": not blocked_hits,
        "dry_run_id": dry_run_id,
        "created_at": now(),
        "preview_type": "METADATA_ONLY_NO_PATCH_APPLICATION",
        "candidate_files_preview": plan.get("candidate_files", []),
        "blocked_path_hits": blocked_hits,
        "patch_generated": False,
        "patch_applied": False,
        "files_mutated": [],
        "actual_apply_executed": False,
        "candidate_executed": False,
        "dry_run_only": True,
    }


def build_no_touch_verification(dry_run_id, plan, patch_preview):
    return {
        "state": "D112_NO_TOUCH_VERIFICATION",
        "ok": patch_preview.get("ok") is True,
        "dry_run_id": dry_run_id,
        "created_at": now(),
        "verified_false": {
            "actual_apply_executed": False,
            "candidate_executed": False,
            "patch_applied": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
        },
        "blocked_path_hits": patch_preview.get("blocked_path_hits", []),
        "safe_to_prepare_d113": patch_preview.get("ok") is True,
    }


def build_d113_scope(dry_run_id, plan, no_touch):
    return {
        "state": "D112_D113_FINAL_APPLY_REVIEW_SCOPE",
        "ok": no_touch.get("ok") is True,
        "dry_run_id": dry_run_id,
        "proposal_id": plan.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D113_GATE,
        "d113_allowed_to_create": [
            "final_apply_review_scope",
            "final_apply_evidence_packet",
            "final_apply_blocker_matrix",
            "d114_final_human_apply_decision_scope",
        ],
        "d113_must_not_execute": [
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
        "final_apply_review_only": True,
        "human_review_required": True,
        "actual_apply_allowed_after_d112": False,
        "route_insert_allowed_after_d112": False,
        "protected_core_mutation_allowed_after_d112": False,
        "sandbox_candidate_execution_allowed_after_d112": False,
        "required_phrase_for_later_gate": "APPROVE_D113_FINAL_APPLY_REVIEW_SCOPE_ONLY",
    }


def create_dry_run_apply_scope(root="."):
    root = Path(root).resolve()

    d111 = read_json(root / D111_REPORT, {}) or {}
    approval_statement = read_json(root / D111_APPROVAL_STATEMENT, {}) or {}
    operator_decision = read_json(root / D111_OPERATOR_DECISION, {}) or {}
    d112_scope = read_json(root / D111_D112_SCOPE, {}) or {}
    review_summary = read_json(root / D110_REVIEW_SUMMARY, {}) or {}

    errors = validate_d111(d111, approval_statement, operator_decision, d112_scope, review_summary)

    dry_run_id = "d112-" + digest({
        "approval_id": d111.get("approval_id"),
        "gate_id": d111.get("gate_id"),
        "proposal_id": d111.get("proposal_id"),
    })

    plan = build_dry_run_plan(dry_run_id, d111, approval_statement, operator_decision, d112_scope, review_summary)
    patch_preview = build_patch_preview(dry_run_id, plan)
    no_touch = build_no_touch_verification(dry_run_id, plan, patch_preview)
    d113_scope = build_d113_scope(dry_run_id, plan, no_touch)

    if patch_preview.get("ok") is not True:
        errors.append("dry-run patch preview detected blocked path")
    if no_touch.get("ok") is not True:
        errors.append("no-touch verification failed")

    ok = not errors
    decision = "DRY_RUN_APPLY_SCOPE_READY" if ok else "DRY_RUN_APPLY_SCOPE_BLOCKED"
    result = "D112_DRY_RUN_APPLY_SCOPE_CREATED" if ok else "D112_DRY_RUN_APPLY_SCOPE_BLOCKED"

    if ok:
        write_json(root / DRY_RUN_PLAN_OUT, plan)
        write_json(root / PATCH_PREVIEW_OUT, patch_preview)
        write_json(root / NO_TOUCH_OUT, no_touch)
        write_json(root / D113_SCOPE_OUT, d113_scope)

    report = {
        "state": "D112_DRY_RUN_APPLY_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_DRY_RUN_APPLY_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "dry_run_id": dry_run_id,
        "approval_id": d111.get("approval_id"),
        "gate_id": d111.get("gate_id"),
        "proposal_id": plan.get("proposal_id"),
        "source_d111_report": D111_REPORT,
        "dry_run_plan": plan if ok else {},
        "dry_run_patch_preview": patch_preview if ok else {},
        "no_touch_verification": no_touch if ok else {},
        "d113_scope": d113_scope if ok else {},
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
            "dry_run_only": True,
            "patch_generated": False,
            "patch_applied": False,
            "candidate_execution_allowed": False,
            "approval_for_real_apply": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": [],
        },
        "summary": {
            "decision": decision,
            "dry_run_id": dry_run_id,
            "approval_id": d111.get("approval_id"),
            "proposal_id": plan.get("proposal_id"),
            "dry_run_only": True,
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D113_GATE,
        },
        "success_condition": {
            "dry_run_scope_created": ok,
            "dry_run_plan_created": ok,
            "patch_preview_created": ok,
            "no_touch_verification_created": ok,
            "d113_scope_created": ok,
            "real_ai_called": False,
            "actual_apply_executed": False,
            "patch_applied": False,
            "candidate_executed": False,
            "protected_core_untouched": True,
            "next_step": "D113 may create final apply review scope only. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_dry_run_apply_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.dry_run_apply_scope import create_dry_run_apply_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD112DryRunApplyScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        approval_id = "d111-test"

        d111 = {
            "ok": True,
            "decision": "EXPLICIT_APPROVAL_GATE_READY",
            "approval_id": approval_id,
            "gate_id": "d110-test",
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
                "rollback_executed": False,
                "restore_executed": False,
                "explicit_approval_gate_only": True,
                "approval_for_d112_dry_run_only": True,
                "approval_for_real_apply": False,
                "candidate_execution_allowed": False,
            },
            "summary": {
                "approval_scope": "D112_DRY_RUN_APPLY_SCOPE_ONLY",
                "next_step": "D112_DRY_RUN_APPLY_SCOPE",
            },
        }

        approval_statement = {
            "ok": True,
            "approval_id": approval_id,
            "approval_scope": "D112_DRY_RUN_APPLY_SCOPE_ONLY",
            "approval_for_real_apply": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        operator_decision = {
            "ok": True,
            "approval_id": approval_id,
            "decision": "APPROVED_FOR_D112_DRY_RUN_SCOPE_ONLY",
            "operator_phrase_matched": True,
            "approval_for_real_apply": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
        }

        d112_scope = {
            "ok": True,
            "approval_id": approval_id,
            "allowed_next_gate": "D112_DRY_RUN_APPLY_SCOPE",
            "dry_run_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d111": False,
            "route_insert_allowed_after_d111": False,
            "protected_core_mutation_allowed_after_d111": False,
            "sandbox_candidate_execution_allowed_after_d111": False,
        }

        review_summary = {
            "ok": True,
            "proposal_id": proposal_id,
            "target_scope": "runtime_experimental/ai_sandbox_work/",
            "candidate_files": ["runtime_experimental/ai_sandbox_work/proposal_manifest.json"],
        }

        write(root / "reports/d111_explicit_approval_gate.json", d111)
        write(root / "reports/d111_explicit_approval_statement.json", approval_statement)
        write(root / "reports/d111_operator_decision_record.json", operator_decision)
        write(root / "reports/d111_d112_dry_run_apply_scope.json", d112_scope)
        write(root / "reports/d110_proposal_review_summary.json", review_summary)

        return td, root

    def test_creates_dry_run_outputs(self):
        td, root = self.root()
        try:
            r = create_dry_run_apply_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "DRY_RUN_APPLY_SCOPE_READY")
            self.assertTrue(r["summary"]["dry_run_only"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["patch_applied"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["d113_scope"]["allowed_next_gate"], "D113_FINAL_APPLY_REVIEW_SCOPE")
            self.assertTrue((root / "reports/d112_dry_run_apply_scope.json").exists())
            self.assertTrue((root / "reports/d112_dry_run_plan.json").exists())
            self.assertTrue((root / "reports/d112_dry_run_patch_preview.json").exists())
            self.assertTrue((root / "reports/d112_no_touch_verification.json").exists())
            self.assertTrue((root / "reports/d112_d113_final_apply_review_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d111(self):
        td, root = self.root()
        try:
            (root / "reports/d111_explicit_approval_gate.json").unlink()
            r = create_dry_run_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d111_claims_real_apply_approval(self):
        td, root = self.root()
        try:
            p = root / "reports/d111_explicit_approval_gate.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_dry_run_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_operator_phrase_not_matched(self):
        td, root = self.root()
        try:
            p = root / "reports/d111_operator_decision_record.json"
            data = json.loads(p.read_text())
            data["operator_phrase_matched"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_dry_run_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_blocked_candidate_path(self):
        td, root = self.root()
        try:
            p = root / "reports/d110_proposal_review_summary.json"
            data = json.loads(p.read_text())
            data["candidate_files"] = ["core/unsafe.py"]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_dry_run_apply_scope(root)
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

print("D112 DRY RUN APPLY SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/dry_run_apply_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d112_dry_run_apply_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/dry_run_apply_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d112_dry_run_apply_scope", "-v"], check=True)

print("\n== run D112 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.dry_run_apply_scope import create_dry_run_apply_scope\n"
    "r=create_dry_run_apply_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d112_dry_run_apply_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/dry_run_apply_scope.py",
    "tests/test_d112_dry_run_apply_scope.py",
    "reports/d112_dry_run_apply_scope.json",
    "reports/d112_dry_run_plan.json",
    "reports/d112_dry_run_patch_preview.json",
    "reports/d112_no_touch_verification.json",
    "reports/d112_d113_final_apply_review_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D112_DRY_RUN_APPLY_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D112 dry-run apply scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D112 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD112 DRY RUN APPLY SCOPE BOOT DONE")
