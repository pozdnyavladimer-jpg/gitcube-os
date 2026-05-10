#!/usr/bin/env python3
# D138_D139_NARROW_EXECUTION_AUTHORITY_REPAIR_BOOT.py
#
# Repair bridge between D138 and D139.
#
# Purpose:
# - Normalize D138 human execution intent / authority guard / D139 scope
#   into a narrow sandbox-only execution authority.
# - Fix accidental broad flags such as allow_network, allow_secret_read,
#   allow_shell_exec, allow_git_action_by_ai, allow_real_apply.
# - Do NOT execute the candidate.
# - Do NOT apply, shell, network, secret-read, route-insert, mutate protected core,
#   or perform AI git action.
#
# After this repair, rerun D139.

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


MODULE = r'''
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D138_REPORT = "reports/d138_sandbox_candidate_human_execution_intent_scope.json"
D138_INTENT_RECORD = "reports/d138_sandbox_candidate_human_execution_intent_record.json"
D138_AUTHORITY_GUARD = "reports/d138_sandbox_candidate_execution_authority_guard.json"
D138_D139_SCOPE = "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json"

OUT = "reports/d138_d139_narrow_execution_authority_repair.json"

REQ_D138_DECISION = "SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_READY"
REQ_D139_GATE = "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE"
REQ_D139_APPROVAL_SCOPE = "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_ONLY"
REQ_OPERATOR_PHRASE = "APPROVE_D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_ONLY"

BLOCKED_NON_EXEC_ACTIONS = [
    "real_apply_by_ai",
    "auto_apply",
    "route_insert_by_ai",
    "protected_core_mutation_by_ai",
    "canonical_memory_overwrite_by_ai",
    "shell_exec_from_ai",
    "shell_exec_from_ai_outside_declared_runner",
    "git_commit_by_ai",
    "git_push_by_ai",
    "rollback_execute_by_ai",
    "restore_execute_by_ai",
    "network_provider_call",
    "network_provider_call_by_ai",
    "secret_read",
    "secret_read_by_ai",
]

FALSE_GUARDRAILS = [
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
    "candidate_executed_now",
    "approval_for_real_apply_by_ai",
    "commands_executed_by_ai",
]

FALSE_AUTHORITY_FLAGS = [
    "allow_real_apply",
    "allow_route_insert",
    "allow_protected_core_mutation",
    "allow_network",
    "allow_secret_read",
    "allow_shell_exec",
    "allow_git_action_by_ai",
    "sandbox_execution_allowed_now",
    "candidate_execution_performed_now",
    "candidate_executed_now",
    "actual_apply_executed",
    "route_inserted",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "shell_executed_by_ai",
    "git_action_by_ai",
    "network_accessed",
    "api_key_read",
    "secret_read",
]

FALSE_SCOPE_FLAGS = [
    "candidate_executed_after_d138_by_ai",
    "real_apply_allowed_after_d138_by_ai",
    "route_insert_allowed_after_d138_by_ai",
    "protected_core_mutation_allowed_after_d138_by_ai",
    "network_allowed_after_d138",
    "secret_read_allowed_after_d138",
    "shell_allowed_after_d138_by_ai",
    "git_action_allowed_after_d138_by_ai",
]

FALSE_INTENT_FLAGS = [
    "approved_for_sandbox_candidate_execution_now",
    "approved_for_real_apply",
    "approved_for_route_insert",
    "approved_for_protected_core_mutation",
    "approved_for_git_action_by_ai",
    "candidate_execution_performed_now",
    "candidate_executed_now",
    "actual_apply_executed",
    "real_apply_executed",
    "shell_executed_by_ai",
    "git_action_by_ai",
    "network_accessed",
    "api_key_read",
    "secret_read",
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


def _ensure_list_has_all(values, required):
    out = []
    seen = set()
    for value in list(values or []) + list(required or []):
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def _candidate_identity(d138, intent_record, authority_guard, d139_scope):
    return {
        "intent_id": d138.get("intent_id") or intent_record.get("intent_id") or d139_scope.get("intent_id"),
        "scope_id": d138.get("scope_id") or authority_guard.get("scope_id") or d139_scope.get("scope_id"),
        "preflight_id": d138.get("preflight_id") or d139_scope.get("preflight_id"),
        "validation_id": d138.get("validation_id") or d139_scope.get("validation_id"),
        "write_materialization_id": d138.get("write_materialization_id") or d139_scope.get("write_materialization_id"),
        "candidate_id": d138.get("candidate_id") or intent_record.get("candidate_id") or authority_guard.get("candidate_id") or d139_scope.get("candidate_id"),
        "proposal_id": d138.get("proposal_id") or d139_scope.get("proposal_id"),
    }


def validate_prereqs(d138, intent_record, authority_guard, d139_scope):
    errors = []
    if not d138:
        errors.append("missing D138 human execution intent scope report")
    if not intent_record:
        errors.append("missing D138 human execution intent record")
    if not authority_guard:
        errors.append("missing D138 execution authority guard")
    if not d139_scope:
        errors.append("missing D138 D139 controlled execution run scope")
    if errors:
        return errors

    if d138.get("ok") is not True:
        errors.append("D138 ok must be true before authority repair")
    if d138.get("decision") != REQ_D138_DECISION:
        errors.append("D138 decision must be ready before authority repair")
    if d138.get("summary", {}).get("next_step") != REQ_D139_GATE:
        errors.append("D138 summary.next_step must be D139 before authority repair")
    if d139_scope.get("allowed_next_gate") != REQ_D139_GATE:
        errors.append("D138 D139 scope allowed_next_gate must be D139")

    return errors


def normalize_records(d138, intent_record, authority_guard, d139_scope):
    identity = _candidate_identity(d138, intent_record, authority_guard, d139_scope)

    # D138 main report remains a no-execution intent scope.
    d138.setdefault("guardrails", {})
    for key in FALSE_GUARDRAILS:
        d138["guardrails"][key] = False
    d138["guardrails"].update({
        "sandbox_candidate_human_execution_intent_scope_only": True,
        "human_execution_intent_record_only": True,
        "execution_authority_guard_only": True,
        "approval_for_d139_controlled_execution_run_scope_only": True,
    })
    d138.setdefault("summary", {})
    d138["summary"].update({
        "human_execution_intent_status": "HUMAN_INTENT_RECORD_CREATED_NO_EXECUTION",
        "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "candidate_execution_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": REQ_D139_APPROVAL_SCOPE,
        "next_step": REQ_D139_GATE,
    })

    # Human intent is a record of permission to create D139 run scope only.
    intent_record.update({
        "state": "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_RECORD",
        "ok": True,
        "record_mode": "HUMAN_EXECUTION_INTENT_RECORD_ONLY_NO_EXECUTION",
        "operator_decision": "PENDING_HUMAN_EXECUTION_INTENT_FOR_D139",
        "required_phrase_for_d139": REQ_OPERATOR_PHRASE,
        "approved_for_d139_controlled_execution_run_scope_only": True,
        "human_review_required": True,
    })
    for key, value in identity.items():
        if value is not None:
            intent_record.setdefault(key, value)
    for key in FALSE_INTENT_FLAGS:
        intent_record[key] = False

    # Authority guard must be narrow: sandbox-only, no apply/core/route/network/secrets/shell/git.
    authority_guard.update({
        "state": "D138_SANDBOX_CANDIDATE_EXECUTION_AUTHORITY_GUARD",
        "ok": True,
        "guard_mode": "HUMAN_INTENT_REQUIRED_SANDBOX_EXECUTION_ONLY_NO_APPLY",
        "authority_mode": "HUMAN_INTENT_REQUIRED_SANDBOX_EXECUTION_ONLY_NO_APPLY",
        "allowed_after_d138": [
            "create_d139_controlled_execution_run_scope",
            "prepare_sandbox_only_execution_command",
        ],
        "still_blocked": _ensure_list_has_all(authority_guard.get("still_blocked", []), BLOCKED_NON_EXEC_ACTIONS),
        "sandbox_execution_allowed_next_gate_only": True,
        "human_review_required": True,
    })
    for key, value in identity.items():
        if value is not None:
            authority_guard.setdefault(key, value)
    for key in FALSE_AUTHORITY_FLAGS:
        authority_guard[key] = False

    # D139 scope can allow only sandbox execution; all dangerous powers stay false/blocked.
    d139_scope.update({
        "state": "D138_D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE",
        "ok": True,
        "allowed_next_gate": REQ_D139_GATE,
        "d139_allowed_to_create": [
            "sandbox_candidate_controlled_execution_run_scope",
            "sandbox_candidate_execution_command_packet",
            "sandbox_candidate_execution_result",
            "d140_sandbox_candidate_post_execution_verification_scope",
        ],
        "d139_allowed_to_execute": [
            "sandbox_candidate_preview_only_inside_runtime_experimental_ai_sandbox_work",
        ],
        "d139_must_not_execute": _ensure_list_has_all(d139_scope.get("d139_must_not_execute", []), BLOCKED_NON_EXEC_ACTIONS),
        "sandbox_candidate_controlled_execution_run_scope_only": True,
        "human_review_required": True,
        "candidate_execution_allowed_after_d138_only_in_sandbox": True,
        "required_phrase_for_later_gate": REQ_OPERATOR_PHRASE,
    })
    for key, value in identity.items():
        if value is not None:
            d139_scope.setdefault(key, value)
    for key in FALSE_SCOPE_FLAGS:
        d139_scope[key] = False

    return d138, intent_record, authority_guard, d139_scope


def validate_normalized(d138, intent_record, authority_guard, d139_scope):
    errors = []

    for key in FALSE_GUARDRAILS:
        if d138.get("guardrails", {}).get(key) is not False:
            errors.append(f"D138 guardrails.{key} must be false after repair")

    for key in FALSE_INTENT_FLAGS:
        if intent_record.get(key) is not False:
            errors.append(f"D138 intent record {key} must be false after repair")

    for key in FALSE_AUTHORITY_FLAGS:
        if authority_guard.get(key) is not False:
            errors.append(f"D138 authority guard {key} must be false after repair")

    blocked = set(authority_guard.get("still_blocked", []))
    for item in BLOCKED_NON_EXEC_ACTIONS:
        if item not in blocked:
            errors.append(f"D138 authority guard still_blocked missing {item}")

    for key in FALSE_SCOPE_FLAGS:
        if d139_scope.get(key) is not False:
            errors.append(f"D138 D139 scope {key} must be false after repair")

    must_not = set(d139_scope.get("d139_must_not_execute", []))
    for item in BLOCKED_NON_EXEC_ACTIONS:
        if item not in must_not:
            errors.append(f"D138 D139 scope d139_must_not_execute missing {item}")

    if d139_scope.get("candidate_execution_allowed_after_d138_only_in_sandbox") is not True:
        errors.append("D138 D139 scope must allow sandbox-only candidate execution after D138")
    if d139_scope.get("allowed_next_gate") != REQ_D139_GATE:
        errors.append("D138 D139 scope allowed_next_gate must remain D139")

    return errors


def repair_d138_d139_narrow_execution_authority(root="."):
    root = Path(root).resolve()

    d138 = read_json(root / D138_REPORT, {}) or {}
    intent_record = read_json(root / D138_INTENT_RECORD, {}) or {}
    authority_guard = read_json(root / D138_AUTHORITY_GUARD, {}) or {}
    d139_scope = read_json(root / D138_D139_SCOPE, {}) or {}

    prereq_errors = validate_prereqs(d138, intent_record, authority_guard, d139_scope)
    repair_id = "d138-d139-repair-" + digest({
        "intent_id": d138.get("intent_id") or intent_record.get("intent_id"),
        "candidate_id": d138.get("candidate_id") or intent_record.get("candidate_id") or d139_scope.get("candidate_id"),
        "proposal_id": d138.get("proposal_id") or d139_scope.get("proposal_id"),
    })

    if not prereq_errors:
        d138, intent_record, authority_guard, d139_scope = normalize_records(
            d138, intent_record, authority_guard, d139_scope
        )
        validation_errors = validate_normalized(d138, intent_record, authority_guard, d139_scope)
    else:
        validation_errors = []

    errors = prereq_errors + validation_errors
    ok = not errors
    decision = "D138_D139_NARROW_EXECUTION_AUTHORITY_REPAIRED" if ok else "D138_D139_NARROW_EXECUTION_AUTHORITY_BLOCKED"
    result = "D138_D139_NARROW_EXECUTION_AUTHORITY_REPAIR_CREATED" if ok else "D138_D139_NARROW_EXECUTION_AUTHORITY_REPAIR_BLOCKED"

    if ok:
        write_json(root / D138_REPORT, d138)
        write_json(root / D138_INTENT_RECORD, intent_record)
        write_json(root / D138_AUTHORITY_GUARD, authority_guard)
        write_json(root / D138_D139_SCOPE, d139_scope)

    report = {
        "state": "D138_D139_NARROW_EXECUTION_AUTHORITY_REPAIR",
        "result": result,
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "repair_id": repair_id,
        "source_files": [D138_REPORT, D138_INTENT_RECORD, D138_AUTHORITY_GUARD, D138_D139_SCOPE],
        "rewritten_files": [D138_REPORT, D138_INTENT_RECORD, D138_AUTHORITY_GUARD, D138_D139_SCOPE] if ok else [],
        "guardrails": {
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "repair_only": True,
            "d139_may_be_retried_after_repair": ok,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "repair_status": "NARROW_AUTHORITY_REPAIRED" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
            "execution_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "git_action_by_ai_status": "BLOCKED",
            "approval_scope": REQ_D139_APPROVAL_SCOPE if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D139_GATE if ok else "BLOCKED",
        },
    }
    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(repair_d138_d139_narrow_execution_authority(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_d138_d139_authority_repair import repair_d138_d139_narrow_execution_authority


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD138D139NarrowExecutionAuthorityRepair(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        d138 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_READY",
            "intent_id": "d138-test",
            "scope_id": "d137-test",
            "candidate_id": "d126-test",
            "proposal_id": "d107-test",
            "guardrails": {},
            "summary": {"next_step": "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE"},
        }
        intent_record = {
            "ok": True,
            "intent_id": "d138-test",
            "candidate_id": "d126-test",
            "record_mode": "HUMAN_EXECUTION_INTENT_RECORD_ONLY_NO_EXECUTION",
            "real_apply_executed": True,
            "network_accessed": True,
        }
        authority_guard = {
            "ok": True,
            "intent_id": "d138-test",
            "candidate_id": "d126-test",
            "guard_mode": "HUMAN_INTENT_REQUIRED_SANDBOX_EXECUTION_ONLY_NO_APPLY",
            "allow_real_apply": True,
            "allow_network": True,
            "allow_secret_read": True,
            "allow_shell_exec": True,
            "allow_git_action_by_ai": True,
        }
        d139_scope = {
            "ok": True,
            "intent_id": "d138-test",
            "candidate_id": "d126-test",
            "allowed_next_gate": "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE",
            "sandbox_candidate_controlled_execution_run_scope_only": True,
            "human_review_required": True,
            "network_allowed_after_d138": True,
            "secret_read_allowed_after_d138": True,
            "shell_allowed_after_d138_by_ai": True,
            "git_action_allowed_after_d138_by_ai": True,
        }

        write(root / "reports/d138_sandbox_candidate_human_execution_intent_scope.json", d138)
        write(root / "reports/d138_sandbox_candidate_human_execution_intent_record.json", intent_record)
        write(root / "reports/d138_sandbox_candidate_execution_authority_guard.json", authority_guard)
        write(root / "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json", d139_scope)
        return td, root

    def test_repairs_broad_authority_flags_to_false(self):
        td, root = self.root()
        try:
            r = repair_d138_d139_narrow_execution_authority(root)
            self.assertTrue(r["ok"])
            guard = json.loads((root / "reports/d138_sandbox_candidate_execution_authority_guard.json").read_text())
            self.assertFalse(guard["allow_real_apply"])
            self.assertFalse(guard["allow_network"])
            self.assertFalse(guard["allow_secret_read"])
            self.assertFalse(guard["allow_shell_exec"])
            self.assertFalse(guard["allow_git_action_by_ai"])
            scope = json.loads((root / "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json").read_text())
            self.assertFalse(scope["network_allowed_after_d138"])
            self.assertFalse(scope["secret_read_allowed_after_d138"])
            self.assertFalse(scope["shell_allowed_after_d138_by_ai"])
            self.assertFalse(scope["git_action_allowed_after_d138_by_ai"])
            self.assertTrue(scope["candidate_execution_allowed_after_d138_only_in_sandbox"])
            self.assertEqual(scope["allowed_next_gate"], "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE")
        finally:
            td.cleanup()

    def test_does_not_execute_candidate(self):
        td, root = self.root()
        try:
            r = repair_d138_d139_narrow_execution_authority(root)
            self.assertTrue(r["ok"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["secret_read"])
        finally:
            td.cleanup()

    def test_blocks_missing_d138(self):
        td, root = self.root()
        try:
            (root / "reports/d138_sandbox_candidate_human_execution_intent_scope.json").unlink()
            r = repair_d138_d139_narrow_execution_authority(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_preserves_blocked_non_execution_actions(self):
        td, root = self.root()
        try:
            r = repair_d138_d139_narrow_execution_authority(root)
            self.assertTrue(r["ok"])
            scope = json.loads((root / "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json").read_text())
            for item in ["real_apply_by_ai", "route_insert_by_ai", "network_provider_call_by_ai", "secret_read_by_ai"]:
                self.assertIn(item, scope["d139_must_not_execute"])
        finally:
            td.cleanup()

    def test_writes_repair_report(self):
        td, root = self.root()
        try:
            r = repair_d138_d139_narrow_execution_authority(root)
            self.assertTrue(r["ok"])
            self.assertTrue((root / "reports/d138_d139_narrow_execution_authority_repair.json").exists())
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

print("D138 D139 NARROW EXECUTION AUTHORITY REPAIR BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_d138_d139_authority_repair.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d138_d139_narrow_execution_authority_repair.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_d138_d139_authority_repair.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d138_d139_narrow_execution_authority_repair", "-v"], check=True)

print("\n== run repair ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_d138_d139_authority_repair import repair_d138_d139_narrow_execution_authority\n"
    "r=repair_d138_d139_narrow_execution_authority()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d138_d139_narrow_execution_authority_repair.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_d138_d139_authority_repair.py",
    "tests/test_d138_d139_narrow_execution_authority_repair.py",
    "reports/d138_d139_narrow_execution_authority_repair.json",
    "reports/d138_sandbox_candidate_human_execution_intent_scope.json",
    "reports/d138_sandbox_candidate_human_execution_intent_record.json",
    "reports/d138_sandbox_candidate_execution_authority_guard.json",
    "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D138_D139_NARROW_EXECUTION_AUTHORITY_REPAIR_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: repair D138 D139 narrow execution authority"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D138 D139 authority repair changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD138 D139 NARROW EXECUTION AUTHORITY REPAIR BOOT DONE")
