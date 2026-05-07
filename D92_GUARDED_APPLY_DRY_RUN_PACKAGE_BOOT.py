#!/usr/bin/env python3
# D92_GUARDED_APPLY_DRY_RUN_PACKAGE_BOOT.py
#
# Creates D92 guarded apply dry-run package.
# It does NOT apply changes, insert routes, mutate protected core, call network/AI, or run git actions by AI.

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import tempfile
import unittest


MODULE = r"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D91_REPORT = "reports/d91_explicit_apply_scope_approval.json"
D91_SCOPE = "reports/d91_apply_scope_request.json"
D91_BLOCKED = "reports/d91_apply_still_blocked.json"

OUT = "reports/d92_guarded_apply_dry_run_package.json"
DIFF = "reports/d92_apply_scope_diff_preview.json"
RECHECK = "reports/d92_pre_apply_recheck_commands.json"
ABORTS = "reports/d92_abort_conditions.json"

REQ_DECISION = "EXPLICIT_APPLY_SCOPE_APPROVAL_READY"
REQ_GATE = "D92_GUARDED_APPLY_DRY_RUN_PACKAGE"
REQ_PHRASE = "APPROVE_D91_SCOPE_FOR_D92_GUARDED_APPLY_DRY_RUN_ONLY"

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

D92_SCOPE = [
    "generate_guarded_apply_dry_run_package",
    "generate_apply_scope_diff_preview",
    "generate_pre_apply_recheck_commands",
    "generate_abort_conditions",
]

FORBIDDEN = [
    "actual_apply",
    "route_insert",
    "protected_core_mutation",
    "canonical_memory_overwrite",
    "external_ai_network_call",
    "git_commit_or_push_by_ai",
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


def validate_d91(d91, scope, blocked):
    errors = []

    if not d91:
        errors.append("missing D91 report")
        return errors

    if d91.get("ok") is not True:
        errors.append("D91 ok must be true")
    if d91.get("decision") != REQ_DECISION:
        errors.append(f"D91 decision invalid: {d91.get('decision')}")

    guard = d91.get("guardrails") if isinstance(d91.get("guardrails"), dict) else {}
    check_false_flags("D91.guardrails", guard, errors)
    if guard.get("scope_approval_only") is not True:
        errors.append("D91 scope_approval_only must be true")
    if guard.get("d92_dry_run_only") is not True:
        errors.append("D91 d92_dry_run_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D91 approval_for_real_apply must be false")

    if not scope:
        errors.append("missing D91 scope request")
    else:
        if scope.get("ok") is not True:
            errors.append("D91 scope ok must be true")
        if scope.get("approval_phrase") != REQ_PHRASE:
            errors.append("D91 approval phrase invalid")
        if scope.get("approved_next_gate") != REQ_GATE:
            errors.append("D91 approved_next_gate invalid")
        allowed = scope.get("allowed_scope_for_d92", [])
        for item in D92_SCOPE:
            if item not in allowed:
                errors.append(f"D91 allowed_scope_for_d92 missing {item}")
        forbidden = scope.get("forbidden_real_actions", [])
        for item in FORBIDDEN:
            if item not in forbidden:
                errors.append(f"D91 forbidden_real_actions missing {item}")

    if not blocked:
        errors.append("missing D91 apply_still_blocked")
    else:
        for key in [
            "apply_allowed_now",
            "route_insert_allowed_now",
            "protected_core_mutation_allowed_now",
            "canonical_memory_mutation_allowed_now",
            "external_ai_call_allowed_now",
            "git_action_by_ai_allowed_now",
        ]:
            if blocked.get(key) is not False:
                errors.append(f"D91 blocked.{key} must be false")
        if blocked.get("next_required_gate") != REQ_GATE:
            errors.append("D91 next_required_gate invalid")

    return errors


def create_guarded_apply_dry_run_package(root="."):
    root = Path(root).resolve()
    d91 = read_json(root / D91_REPORT, {}) or {}
    scope = read_json(root / D91_SCOPE, {}) or {}
    blocked = read_json(root / D91_BLOCKED, {}) or {}

    errors = validate_d91(d91, scope, blocked)
    approval_id = str(d91.get("approval_id") or scope.get("approval_id") or "")
    evidence = d91.get("evidence") if isinstance(d91.get("evidence"), dict) else {}
    plan_id = str(evidence.get("plan_id") or scope.get("source_plan_id") or "")
    source_package_id = str(evidence.get("package_id") or scope.get("source_package_id") or "")
    package_id = "d92-" + digest({"approval_id": approval_id, "plan_id": plan_id, "source_package_id": source_package_id})

    ok = not errors
    decision = "GUARDED_APPLY_DRY_RUN_PACKAGE_READY" if ok else "GUARDED_APPLY_DRY_RUN_PACKAGE_BLOCKED"
    result = "D92_GUARDED_APPLY_DRY_RUN_PACKAGE_CREATED" if ok else "D92_GUARDED_APPLY_DRY_RUN_PACKAGE_BLOCKED"

    diff = {
        "state": "D92_APPLY_SCOPE_DIFF_PREVIEW",
        "ok": True,
        "package_id": package_id,
        "created_at": now(),
        "dry_run_only": True,
        "documentation_only": True,
        "source_approval_id": approval_id,
        "source_plan_id": plan_id,
        "source_package_id": source_package_id,
        "planned_files_to_touch": [],
        "protected_files_to_touch": [],
        "route_insertions": [],
        "runtime_mutations": [],
        "canonical_memory_changes": [],
        "external_calls": [],
        "diff_status": "NO_REAL_DIFF_PREPARED_D92_IS_DRY_RUN_PACKAGE_ONLY",
        "allowed_next_gate": "D93_DRY_RUN_RECHECK_GATE",
    }

    recheck = {
        "state": "D92_PRE_APPLY_RECHECK_COMMANDS",
        "ok": True,
        "package_id": package_id,
        "created_at": now(),
        "commands_are_documentation_only": True,
        "commands_must_not_be_executed_by_ai": True,
        "human_may_run_manually": True,
        "commands": [
            "python -m unittest discover -s tests -v",
            "python -m py_compile runtime_experimental/*.py",
            "python -m unittest tests.test_d90_controlled_apply_plan -v",
            "python -m unittest tests.test_d91_explicit_apply_scope_approval -v",
            "python -m unittest tests.test_d92_guarded_apply_dry_run_package -v",
            "git diff --stat",
            "git status --short",
        ],
        "blocked_commands": ["git apply", "git commit", "git push", "route insert", "direct protected-core edit"],
    }

    aborts = {
        "state": "D92_ABORT_CONDITIONS",
        "ok": True,
        "package_id": package_id,
        "created_at": now(),
        "abort_if": [
            "any unit test fails",
            "D66 recheck is missing or failed",
            "D85 rollback manifest is missing",
            "D86 local regression results are missing or failed",
            "planned diff touches protected core",
            "planned diff mutates canonical memory",
            "planned diff inserts route without later explicit gate",
            "external AI/network call is required",
            "AI attempts git commit or push",
        ],
        "must_remain_false": {
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
            "runtime_code_mutated": False,
        },
    }

    dry_run_package = {
        "state": "D92_GUARDED_APPLY_DRY_RUN_PACKAGE_PREVIEW",
        "ok": True,
        "package_id": package_id,
        "created_at": now(),
        "mode": "GUARDED_DRY_RUN_PACKAGE_ONLY",
        "source_approval_id": approval_id,
        "source_plan_id": plan_id,
        "source_package_id": source_package_id,
        "approved_scope_from_d91": scope.get("allowed_scope_for_d92", []),
        "dry_run_contract": {
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
            "dry_run_package_only": True,
        },
        "generated_artifacts": {
            "diff_preview_state": diff["state"],
            "recheck_commands_state": recheck["state"],
            "abort_conditions_state": aborts["state"],
        },
        "required_next_gate": "D93_DRY_RUN_RECHECK_GATE",
    }

    if ok:
        write_json(root / DIFF, diff)
        write_json(root / RECHECK, recheck)
        write_json(root / ABORTS, aborts)

    report = {
        "state": "D92_GUARDED_APPLY_DRY_RUN_PACKAGE",
        "result": result,
        "route": "FIELD_INTENT_GUARDED_APPLY_DRY_RUN_PACKAGE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "package_id": package_id,
        "diff_preview_path": str(root / DIFF) if ok else "",
        "recheck_commands_path": str(root / RECHECK) if ok else "",
        "abort_conditions_path": str(root / ABORTS) if ok else "",
        "input_reports": {
            "d91_report_path": str(root / D91_REPORT),
            "d91_scope_path": str(root / D91_SCOPE),
            "d91_blocked_path": str(root / D91_BLOCKED),
        },
        "dry_run_package": dry_run_package if ok else {},
        "diff_preview": diff if ok else {},
        "pre_apply_recheck_commands": recheck if ok else {},
        "abort_conditions": aborts if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "guarded_dry_run_package_only": True,
            "apply_allowed_now": False,
            "approval_for_real_apply": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "package_id": package_id,
            "approval_id": approval_id,
            "plan_id": plan_id,
            "source_package_id": source_package_id,
            "errors_count": len(errors),
            "warnings_count": 0,
        },
        "success_condition": {
            "guarded_apply_dry_run_package_created": ok,
            "diff_preview_created": ok,
            "recheck_commands_created": ok,
            "abort_conditions_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D93 should verify D92 dry-run package. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_guarded_apply_dry_run_package(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.guarded_apply_dry_run_package import create_guarded_apply_dry_run_package


def write(path, data):
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD92GuardedApplyDryRunPackage(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()
        write(root / "reports/d91_explicit_apply_scope_approval.json", {
            "ok": True,
            "decision": "EXPLICIT_APPLY_SCOPE_APPROVAL_READY",
            "approval_id": "d91-test",
            "evidence": {"plan_id": "d90-test", "package_id": "d85-test"},
            "guardrails": {
                "external_ai_called": False,
                "network_accessed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
                "scope_approval_only": True,
                "d92_dry_run_only": True,
                "approval_for_real_apply": False,
            },
        })
        write(root / "reports/d91_apply_scope_request.json", {
            "ok": True,
            "approval_id": "d91-test",
            "approval_phrase": "APPROVE_D91_SCOPE_FOR_D92_GUARDED_APPLY_DRY_RUN_ONLY",
            "approved_next_gate": "D92_GUARDED_APPLY_DRY_RUN_PACKAGE",
            "source_plan_id": "d90-test",
            "source_package_id": "d85-test",
            "allowed_scope_for_d92": [
                "generate_guarded_apply_dry_run_package",
                "generate_apply_scope_diff_preview",
                "generate_pre_apply_recheck_commands",
                "generate_abort_conditions",
            ],
            "forbidden_real_actions": [
                "actual_apply",
                "route_insert",
                "protected_core_mutation",
                "canonical_memory_overwrite",
                "external_ai_network_call",
                "git_commit_or_push_by_ai",
            ],
        })
        write(root / "reports/d91_apply_still_blocked.json", {
            "ok": True,
            "apply_allowed_now": False,
            "route_insert_allowed_now": False,
            "protected_core_mutation_allowed_now": False,
            "canonical_memory_mutation_allowed_now": False,
            "external_ai_call_allowed_now": False,
            "git_action_by_ai_allowed_now": False,
            "next_required_gate": "D92_GUARDED_APPLY_DRY_RUN_PACKAGE",
        })
        return td, root

    def test_creates_dry_run_package_only(self):
        td, root = self.root()
        try:
            r = create_guarded_apply_dry_run_package(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "GUARDED_APPLY_DRY_RUN_PACKAGE_READY")
            self.assertTrue(r["guardrails"]["guarded_dry_run_package_only"])
            self.assertFalse(r["guardrails"]["apply_allowed_now"])
            self.assertEqual(r["dry_run_package"]["required_next_gate"], "D93_DRY_RUN_RECHECK_GATE")
            self.assertTrue((root / "reports/d92_guarded_apply_dry_run_package.json").exists())
            self.assertTrue((root / "reports/d92_apply_scope_diff_preview.json").exists())
            self.assertTrue((root / "reports/d92_pre_apply_recheck_commands.json").exists())
            self.assertTrue((root / "reports/d92_abort_conditions.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d91(self):
        td, root = self.root()
        try:
            (root / "reports/d91_explicit_apply_scope_approval.json").unlink()
            r = create_guarded_apply_dry_run_package(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "GUARDED_APPLY_DRY_RUN_PACKAGE_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_real_apply_approval(self):
        td, root = self.root()
        try:
            p = root / "reports/d91_explicit_apply_scope_approval.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data))
            r = create_guarded_apply_dry_run_package(root)
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

print("D92 GUARDED APPLY DRY-RUN PACKAGE BOOT: repo =", ROOT)

Path("runtime_experimental/guarded_apply_dry_run_package.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d92_guarded_apply_dry_run_package.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/guarded_apply_dry_run_package.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d92_guarded_apply_dry_run_package", "-v"], check=True)

print("\n== run D92 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.guarded_apply_dry_run_package import create_guarded_apply_dry_run_package\n"
    "r=create_guarded_apply_dry_run_package()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d92_guarded_apply_dry_run_package.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/guarded_apply_dry_run_package.py",
    "tests/test_d92_guarded_apply_dry_run_package.py",
    "reports/d92_guarded_apply_dry_run_package.json",
    "reports/d92_apply_scope_diff_preview.json",
    "reports/d92_pre_apply_recheck_commands.json",
    "reports/d92_abort_conditions.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D92_GUARDED_APPLY_DRY_RUN_PACKAGE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D92 guarded apply dry-run package"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D92 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD92 GUARDED APPLY DRY-RUN PACKAGE BOOT DONE")
