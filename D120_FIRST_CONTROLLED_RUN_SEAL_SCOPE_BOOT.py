#!/usr/bin/env python3
# D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE_BOOT.py
#
# Creates D120 First Controlled Run Seal Scope.
#
# D120 consumes D119 post-apply verification artifacts and creates first-cycle-seal-only artifacts:
# - runtime_experimental/first_controlled_run_seal_scope.py
# - tests/test_d120_first_controlled_run_seal_scope.py
# - reports/d120_first_controlled_run_seal_scope.json
# - reports/d120_guarded_autonomy_run_ledger.json
# - reports/d120_final_chain_integrity_summary.json
# - reports/d120_first_run_release_tag_plan.json
#
# This is FIRST CONTROLLED RUN SEAL SCOPE ONLY.
# It does NOT execute real apply by AI.
# It does NOT execute shell commands by AI.
# It does NOT create git tags by AI.
# It does NOT mutate core/runtime/app/memory/routes.
# It does NOT commit/push by AI.
#
# D120 seals the D106-D120 guarded autonomy cycle as documentation/ledger only.
# The next recommended track is AI provider propose-only connector / dashboard start command.

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

D119_REPORT = "reports/d119_post_apply_verification_gate_scope.json"
D119_TEST_RESULTS = "reports/d119_post_apply_test_results_summary.json"
D119_GIT_STATE = "reports/d119_post_apply_git_state_summary.json"
D119_D120_SCOPE = "reports/d119_d120_first_controlled_run_seal_scope.json"

OUT = "reports/d120_first_controlled_run_seal_scope.json"
LEDGER_OUT = "reports/d120_guarded_autonomy_run_ledger.json"
INTEGRITY_OUT = "reports/d120_final_chain_integrity_summary.json"
TAG_PLAN_OUT = "reports/d120_first_run_release_tag_plan.json"

REQ_D119_DECISION = "POST_APPLY_VERIFICATION_GATE_SCOPE_READY"
REQ_D120_GATE = "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE"
REQ_D119_APPROVAL_SCOPE = "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE_ONLY"

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


CHAIN = [
    "D106 AI Provider Boundary",
    "D107 Proposal Schema Validator",
    "D108 Sandbox Proposal Writer",
    "D109 Regression Runner",
    "D110 Human Review Gate",
    "D111 Explicit Approval Gate",
    "D112 Dry-Run Apply Scope",
    "D113 Final Apply Review Scope",
    "D114 Final Human Apply Decision Scope",
    "D115 Final Apply Phrase Scope",
    "D116 Manual Apply Window Scope",
    "D117 Manual Apply Command Review Scope",
    "D118 Operator Local Execution Evidence Scope",
    "D119 Post-Apply Verification Gate Scope",
    "D120 First Controlled Run Seal Scope",
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


def validate_d119(d119, test_results, git_state, d120_scope):
    errors = []

    if not d119:
        errors.append("missing D119 post-apply verification gate scope report")
        return errors

    if d119.get("ok") is not True:
        errors.append("D119 ok must be true")
    if d119.get("decision") != REQ_D119_DECISION:
        errors.append("D119 decision must be POST_APPLY_VERIFICATION_GATE_SCOPE_READY")

    guard = d119.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D119 guardrails.{key} must be false")
    if guard.get("post_apply_verification_scope_only") is not True:
        errors.append("D119 post_apply_verification_scope_only must be true")
    if guard.get("verification_template_only") is not True:
        errors.append("D119 verification_template_only must be true")
    if guard.get("approval_for_d120_seal_scope_only") is not True:
        errors.append("D119 approval_for_d120_seal_scope_only must be true")
    if guard.get("approval_for_real_apply_by_ai") is not False:
        errors.append("D119 approval_for_real_apply_by_ai must be false")
    if guard.get("candidate_execution_allowed_by_ai") is not False:
        errors.append("D119 candidate_execution_allowed_by_ai must be false")
    if guard.get("commands_executed_by_ai") is not False:
        errors.append("D119 commands_executed_by_ai must be false")

    summary = d119.get("summary", {})
    if summary.get("real_apply_by_ai_status") != "BLOCKED":
        errors.append("D119 real_apply_by_ai_status must be BLOCKED")
    if summary.get("approval_scope") != REQ_D119_APPROVAL_SCOPE:
        errors.append("D119 approval_scope must be D120 seal scope only")
    if summary.get("next_step") != REQ_D120_GATE:
        errors.append("D119 summary next_step must be D120")

    if not test_results:
        errors.append("missing D119 post-apply test results summary")
    else:
        if test_results.get("ok") is not True:
            errors.append("D119 test summary ok must be true")
        if test_results.get("summary_mode") != "VERIFICATION_SCOPE_ONLY_NOT_EXECUTED":
            errors.append("D119 test summary must be verification-scope-only")
        for key in [
            "tests_executed_by_ai",
            "actual_apply_executed_by_ai",
            "candidate_executed_by_ai",
        ]:
            if test_results.get(key) is not False:
                errors.append(f"D119 test summary {key} must be false")

    if not git_state:
        errors.append("missing D119 post-apply git state summary")
    else:
        if git_state.get("ok") is not True:
            errors.append("D119 git state ok must be true")
        if git_state.get("summary_mode") != "GIT_STATE_SUMMARY_TEMPLATE_ONLY":
            errors.append("D119 git state must be template-only")
        for key in [
            "git_commands_executed_by_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "route_inserted_by_ai",
            "protected_core_mutated_by_ai",
        ]:
            if git_state.get(key) is not False:
                errors.append(f"D119 git state {key} must be false")

    if not d120_scope:
        errors.append("missing D119 D120 first controlled run seal scope")
    else:
        if d120_scope.get("ok") is not True:
            errors.append("D119 D120 scope ok must be true")
        if d120_scope.get("allowed_next_gate") != REQ_D120_GATE:
            errors.append("D119 D120 scope allowed_next_gate must be D120")
        if d120_scope.get("first_controlled_run_seal_scope_only") is not True:
            errors.append("D119 D120 scope first_controlled_run_seal_scope_only must be true")
        if d120_scope.get("human_review_required") is not True:
            errors.append("D119 D120 scope human_review_required must be true")
        for key in [
            "actual_apply_allowed_after_d119_by_ai",
            "route_insert_allowed_after_d119_by_ai",
            "protected_core_mutation_allowed_after_d119_by_ai",
            "sandbox_candidate_execution_allowed_after_d119_by_ai",
        ]:
            if d120_scope.get(key) is not False:
                errors.append(f"D119 D120 scope {key} must be false")

    return errors


def build_run_ledger(seal_id, d119, test_results, git_state):
    return {
        "state": "D120_GUARDED_AUTONOMY_RUN_LEDGER",
        "ok": True,
        "seal_id": seal_id,
        "verification_id": d119.get("verification_id"),
        "evidence_id": d119.get("evidence_id"),
        "review_id": d119.get("review_id"),
        "window_id": d119.get("window_id"),
        "phrase_id": d119.get("phrase_id"),
        "decision_id": d119.get("decision_id"),
        "dry_run_id": d119.get("dry_run_id"),
        "proposal_id": d119.get("proposal_id"),
        "created_at": now(),
        "chain": CHAIN,
        "chain_length": len(CHAIN),
        "core_rule": "AI proposes; system verifies; human approves; execution remains gated.",
        "run_status": "FIRST_CONTROLLED_RUN_SCOPE_SEALED",
        "real_apply_by_ai": False,
        "actual_apply_executed_by_ai": False,
        "commands_executed_by_ai": False,
        "operator_evidence_status": "awaiting/optional for future manual run",
        "test_summary_reference": test_results.get("state"),
        "git_state_reference": git_state.get("state"),
    }


def build_integrity_summary(seal_id, d119, test_results, git_state):
    return {
        "state": "D120_FINAL_CHAIN_INTEGRITY_SUMMARY",
        "ok": True,
        "seal_id": seal_id,
        "verification_id": d119.get("verification_id"),
        "proposal_id": d119.get("proposal_id"),
        "created_at": now(),
        "sealed_range": "D106-D120",
        "integrity_status": "SEALED_WITH_REAL_APPLY_BY_AI_BLOCKED",
        "checks": {
            "d119_ok": d119.get("ok") is True,
            "test_results_summary_ok": test_results.get("ok") is True,
            "git_state_summary_ok": git_state.get("ok") is True,
            "real_apply_by_ai_blocked": True,
            "ai_shell_execution_blocked": True,
            "ai_git_action_blocked": True,
            "protected_core_mutation_by_ai_blocked": True,
            "canonical_memory_overwrite_by_ai_blocked": True,
        },
        "must_remain_false": {
            "actual_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "canonical_memory_mutated_by_ai": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "rollback_executed_by_ai": False,
            "restore_executed_by_ai": False,
        },
        "final_principle": [
            "Autonomy may think.",
            "Autonomy may propose.",
            "Autonomy may verify.",
            "Autonomy may not silently execute.",
        ],
    }


def build_tag_plan(seal_id):
    tag_name = "guarded-autonomy-d106-d120-first-controlled-run"
    return {
        "state": "D120_FIRST_RUN_RELEASE_TAG_PLAN",
        "ok": True,
        "seal_id": seal_id,
        "created_at": now(),
        "tag_plan_only": True,
        "tag_created_by_ai": False,
        "tag_pushed_by_ai": False,
        "recommended_tag": tag_name,
        "manual_commands_for_human_only": [
            f"git tag {tag_name}",
            f"git push origin {tag_name}",
        ],
        "note": "This file documents a recommended manual tag only. D120 does not create or push tags.",
    }


def create_first_controlled_run_seal_scope(root="."):
    root = Path(root).resolve()

    d119 = read_json(root / D119_REPORT, {}) or {}
    test_results = read_json(root / D119_TEST_RESULTS, {}) or {}
    git_state = read_json(root / D119_GIT_STATE, {}) or {}
    d120_scope = read_json(root / D119_D120_SCOPE, {}) or {}

    errors = validate_d119(d119, test_results, git_state, d120_scope)

    seal_id = "d120-" + digest({
        "verification_id": d119.get("verification_id"),
        "evidence_id": d119.get("evidence_id"),
        "proposal_id": d119.get("proposal_id"),
    })

    ledger = build_run_ledger(seal_id, d119, test_results, git_state)
    integrity = build_integrity_summary(seal_id, d119, test_results, git_state)
    tag_plan = build_tag_plan(seal_id)

    if tag_plan.get("tag_created_by_ai") is not False:
        errors.append("tag plan tag_created_by_ai must be false")
    if tag_plan.get("tag_pushed_by_ai") is not False:
        errors.append("tag plan tag_pushed_by_ai must be false")
    if integrity.get("integrity_status") != "SEALED_WITH_REAL_APPLY_BY_AI_BLOCKED":
        errors.append("integrity status must keep real apply by AI blocked")

    ok = not errors
    decision = "FIRST_CONTROLLED_RUN_SEAL_SCOPE_READY" if ok else "FIRST_CONTROLLED_RUN_SEAL_SCOPE_BLOCKED"
    result = "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE_CREATED" if ok else "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE_BLOCKED"

    if ok:
        write_json(root / LEDGER_OUT, ledger)
        write_json(root / INTEGRITY_OUT, integrity)
        write_json(root / TAG_PLAN_OUT, tag_plan)

    report = {
        "state": "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_FIRST_CONTROLLED_RUN_SEAL_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "seal_id": seal_id,
        "verification_id": d119.get("verification_id"),
        "evidence_id": d119.get("evidence_id"),
        "review_id": d119.get("review_id"),
        "window_id": d119.get("window_id"),
        "phrase_id": d119.get("phrase_id"),
        "decision_id": d119.get("decision_id"),
        "dry_run_id": d119.get("dry_run_id"),
        "proposal_id": d119.get("proposal_id"),
        "source_d119_report": D119_REPORT,
        "guarded_autonomy_run_ledger": ledger if ok else {},
        "final_chain_integrity_summary": integrity if ok else {},
        "first_run_release_tag_plan": tag_plan if ok else {},
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
            "first_controlled_run_seal_scope_only": True,
            "ledger_only": True,
            "tag_plan_only": True,
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
            "seal_id": seal_id,
            "verification_id": d119.get("verification_id"),
            "proposal_id": d119.get("proposal_id"),
            "sealed_range": "D106-D120",
            "chain_length": len(CHAIN),
            "real_apply_by_ai_status": "BLOCKED",
            "first_controlled_run_status": "SEALED" if ok else "BLOCKED",
            "recommended_next_track": "D121_AI_PROPOSE_ONLY_PROVIDER_ADAPTER",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": "D121_AI_PROPOSE_ONLY_PROVIDER_ADAPTER",
        },
        "success_condition": {
            "first_controlled_run_seal_scope_created": ok,
            "guarded_autonomy_run_ledger_created": ok,
            "final_chain_integrity_summary_created": ok,
            "first_run_release_tag_plan_created": ok,
            "approval_for_real_apply_by_ai": False,
            "tag_created_by_ai": False,
            "real_ai_called": False,
            "actual_apply_executed_by_ai": False,
            "candidate_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D106-D120 guarded autonomy cycle is sealed. Next: propose-only AI provider adapter.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_first_controlled_run_seal_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.first_controlled_run_seal_scope import create_first_controlled_run_seal_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD120FirstControlledRunSealScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        verification_id = "d119-test"

        d119 = {
            "ok": True,
            "decision": "POST_APPLY_VERIFICATION_GATE_SCOPE_READY",
            "verification_id": verification_id,
            "evidence_id": "d118-test",
            "review_id": "d117-test",
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
                "post_apply_verification_scope_only": True,
                "verification_template_only": True,
                "approval_for_d120_seal_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "real_apply_by_ai_status": "BLOCKED",
                "approval_scope": "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE_ONLY",
                "next_step": "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE",
            },
        }

        test_results = {
            "ok": True,
            "verification_id": verification_id,
            "summary_mode": "VERIFICATION_SCOPE_ONLY_NOT_EXECUTED",
            "tests_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "candidate_executed_by_ai": False,
        }

        git_state = {
            "ok": True,
            "verification_id": verification_id,
            "summary_mode": "GIT_STATE_SUMMARY_TEMPLATE_ONLY",
            "git_commands_executed_by_ai": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
        }

        d120_scope = {
            "ok": True,
            "verification_id": verification_id,
            "allowed_next_gate": "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE",
            "first_controlled_run_seal_scope_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d119_by_ai": False,
            "route_insert_allowed_after_d119_by_ai": False,
            "protected_core_mutation_allowed_after_d119_by_ai": False,
            "sandbox_candidate_execution_allowed_after_d119_by_ai": False,
        }

        write(root / "reports/d119_post_apply_verification_gate_scope.json", d119)
        write(root / "reports/d119_post_apply_test_results_summary.json", test_results)
        write(root / "reports/d119_post_apply_git_state_summary.json", git_state)
        write(root / "reports/d119_d120_first_controlled_run_seal_scope.json", d120_scope)

        return td, root

    def test_creates_first_controlled_run_seal_outputs(self):
        td, root = self.root()
        try:
            r = create_first_controlled_run_seal_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "FIRST_CONTROLLED_RUN_SEAL_SCOPE_READY")
            self.assertEqual(r["summary"]["sealed_range"], "D106-D120")
            self.assertEqual(r["summary"]["first_controlled_run_status"], "SEALED")
            self.assertEqual(r["summary"]["recommended_next_track"], "D121_AI_PROPOSE_ONLY_PROVIDER_ADAPTER")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["git_push_by_ai"])
            self.assertTrue(r["final_chain_integrity_summary"]["ok"])
            self.assertFalse(r["first_run_release_tag_plan"]["tag_created_by_ai"])
            self.assertTrue((root / "reports/d120_first_controlled_run_seal_scope.json").exists())
            self.assertTrue((root / "reports/d120_guarded_autonomy_run_ledger.json").exists())
            self.assertTrue((root / "reports/d120_final_chain_integrity_summary.json").exists())
            self.assertTrue((root / "reports/d120_first_run_release_tag_plan.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d119(self):
        td, root = self.root()
        try:
            (root / "reports/d119_post_apply_verification_gate_scope.json").unlink()
            r = create_first_controlled_run_seal_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_git_state_claims_ai_commit(self):
        td, root = self.root()
        try:
            p = root / "reports/d119_post_apply_git_state_summary.json"
            data = json.loads(p.read_text())
            data["git_commit_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_first_controlled_run_seal_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d119_claims_apply_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d119_post_apply_verification_gate_scope.json"
            data = json.loads(p.read_text())
            data["guardrails"]["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_first_controlled_run_seal_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_scope_allows_apply_by_ai_after_d119(self):
        td, root = self.root()
        try:
            p = root / "reports/d119_d120_first_controlled_run_seal_scope.json"
            data = json.loads(p.read_text())
            data["actual_apply_allowed_after_d119_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_first_controlled_run_seal_scope(root)
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

print("D120 FIRST CONTROLLED RUN SEAL SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/first_controlled_run_seal_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d120_first_controlled_run_seal_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/first_controlled_run_seal_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d120_first_controlled_run_seal_scope", "-v"], check=True)

print("\n== run D120 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.first_controlled_run_seal_scope import create_first_controlled_run_seal_scope\n"
    "r=create_first_controlled_run_seal_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d120_first_controlled_run_seal_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/first_controlled_run_seal_scope.py",
    "tests/test_d120_first_controlled_run_seal_scope.py",
    "reports/d120_first_controlled_run_seal_scope.json",
    "reports/d120_guarded_autonomy_run_ledger.json",
    "reports/d120_final_chain_integrity_summary.json",
    "reports/d120_first_run_release_tag_plan.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D120 first controlled run seal scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D120 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD120 FIRST CONTROLLED RUN SEAL SCOPE BOOT DONE")
