#!/usr/bin/env python3
# D110_HUMAN_REVIEW_GATE_BOOT.py
# Creates D110 Human Review Gate.
# D110 consumes D109 evidence and creates a human review packet only.
# No real apply. No route insert. No core/runtime/app/memory mutation. No AI git action.

from __future__ import annotations

import json
import hashlib
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

D109_REPORT = "reports/d109_regression_runner.json"
D109_STATIC_CHECKS = "reports/d109_sandbox_static_checks.json"
D109_REGRESSION_RESULTS = "reports/d109_sandbox_regression_results.json"
D109_DIFF_SUMMARY = "reports/d109_sandbox_diff_summary.json"
D109_D110_SCOPE = "reports/d109_d110_human_review_gate_scope.json"
D108_SANDBOX_PROPOSAL = "runtime_experimental/ai_sandbox_work/d108_accepted_proposal.json"

OUT = "reports/d110_human_review_gate.json"
HUMAN_PACKET_OUT = "reports/d110_human_review_packet.json"
PROPOSAL_REVIEW_SUMMARY_OUT = "reports/d110_proposal_review_summary.json"
APPROVAL_RECORD_OUT = "reports/d110_approval_or_rejection_record.json"
D111_SCOPE_OUT = "reports/d110_d111_explicit_approval_gate_scope.json"

REQ_D109_DECISION = "REGRESSION_RUNNER_READY"
REQ_D110_GATE = "D110_HUMAN_REVIEW_GATE"
REQ_D111_GATE = "D111_EXPLICIT_APPROVAL_GATE"

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


def validate_d109(d109, static_checks, regression_results, diff_summary, d110_scope, sandbox_proposal):
    errors = []

    if not d109:
        errors.append("missing D109 regression runner report")
        return errors

    if d109.get("ok") is not True:
        errors.append("D109 ok must be true")
    if d109.get("decision") != REQ_D109_DECISION:
        errors.append("D109 decision must be REGRESSION_RUNNER_READY")

    guard = d109.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D109 guardrails.{key} must be false")
    if guard.get("sandbox_regression_only") is not True:
        errors.append("D109 guardrails.sandbox_regression_only must be true")
    if guard.get("candidate_execution_allowed") is not False:
        errors.append("D109 guardrails.candidate_execution_allowed must be false")

    summary = d109.get("summary", {})
    if summary.get("regression_ok") is not True:
        errors.append("D109 summary.regression_ok must be true")
    if summary.get("static_ok") is not True:
        errors.append("D109 summary.static_ok must be true")
    if summary.get("next_step") != REQ_D110_GATE:
        errors.append("D109 summary.next_step must be D110_HUMAN_REVIEW_GATE")

    if not static_checks:
        errors.append("missing D109 static checks")
    else:
        if static_checks.get("ok") is not True:
            errors.append("D109 static checks ok must be true")
        if static_checks.get("blocked_paths_detected"):
            errors.append("D109 static checks detected blocked paths")
        for key in ["actual_apply_executed", "candidate_executed", "protected_core_mutated", "route_inserted"]:
            if static_checks.get(key) is not False:
                errors.append(f"D109 static checks {key} must be false")

    if not regression_results:
        errors.append("missing D109 regression results")
    else:
        if regression_results.get("ok") is not True:
            errors.append("D109 regression results ok must be true")
        if regression_results.get("failed_count") not in (0, None):
            errors.append("D109 regression failed_count must be zero")
        for key in ["actual_apply_executed", "candidate_executed", "shell_from_ai_executed"]:
            if regression_results.get(key) is not False:
                errors.append(f"D109 regression results {key} must be false")

    if not diff_summary:
        errors.append("missing D109 diff summary")
    else:
        if diff_summary.get("ok") is not True:
            errors.append("D109 diff summary ok must be true")
        if diff_summary.get("documentation_only") is not True:
            errors.append("D109 diff summary documentation_only must be true")
        for key in ["actual_apply_executed", "candidate_executed"]:
            if diff_summary.get(key) is not False:
                errors.append(f"D109 diff summary {key} must be false")

    if not d110_scope:
        errors.append("missing D109 D110 scope")
    else:
        if d110_scope.get("ok") is not True:
            errors.append("D109 D110 scope ok must be true")
        if d110_scope.get("allowed_next_gate") != REQ_D110_GATE:
            errors.append("D109 D110 scope allowed_next_gate must be D110")
        if d110_scope.get("human_review_required") is not True:
            errors.append("D109 D110 scope human_review_required must be true")
        for key in [
            "actual_apply_allowed_after_d109",
            "route_insert_allowed_after_d109",
            "protected_core_mutation_allowed_after_d109",
            "sandbox_candidate_execution_allowed_after_d109",
        ]:
            if d110_scope.get(key) is not False:
                errors.append(f"D109 D110 scope {key} must be false")

    if not sandbox_proposal:
        errors.append("missing D108 sandbox proposal copy")
    else:
        if sandbox_proposal.get("ok") is not True:
            errors.append("D108 sandbox proposal ok must be true")
        if sandbox_proposal.get("sandbox_copy_only") is not True:
            errors.append("D108 sandbox proposal must be copy only")
        if sandbox_proposal.get("actual_apply_executed") is not False:
            errors.append("D108 sandbox proposal actual_apply_executed must be false")
        if sandbox_proposal.get("candidate_executed") is not False:
            errors.append("D108 sandbox proposal candidate_executed must be false")
        proposal = sandbox_proposal.get("proposal", {})
        for path in proposal.get("candidate_files", []):
            if starts(str(path), BLOCKED_PREFIXES):
                errors.append(f"sandbox proposal contains blocked candidate path: {path}")

    return errors


def build_review_summary(gate_id, d109, static_checks, regression_results, sandbox_proposal):
    proposal = sandbox_proposal.get("proposal", {}) if isinstance(sandbox_proposal, dict) else {}
    return {
        "state": "D110_PROPOSAL_REVIEW_SUMMARY",
        "ok": True,
        "gate_id": gate_id,
        "created_at": now(),
        "proposal_id": proposal.get("proposal_id") or d109.get("proposal_id"),
        "proposal_type": proposal.get("proposal_type"),
        "intent": proposal.get("intent"),
        "target_scope": proposal.get("target_scope"),
        "candidate_files": proposal.get("candidate_files", []),
        "risk_flags": proposal.get("risk_flags", []),
        "requires_human_review": True,
        "regression_ok": regression_results.get("ok") is True,
        "static_checks_ok": static_checks.get("ok") is True,
        "approval_granted": False,
        "actual_apply_executed": False,
        "candidate_executed": False,
        "protected_core_mutated": False,
        "route_inserted": False,
    }


def build_human_packet(gate_id, d109, static_checks, regression_results, diff_summary, review_summary):
    return {
        "state": "D110_HUMAN_REVIEW_PACKET",
        "ok": True,
        "gate_id": gate_id,
        "created_at": now(),
        "review_mode": "HUMAN_DECISION_PACKET_ONLY",
        "proposal_id": review_summary.get("proposal_id"),
        "review_items": [
            "Read D108 sandbox accepted proposal copy",
            "Read D109 static checks",
            "Read D109 regression results",
            "Read D109 diff summary",
            "Confirm no real apply was executed",
            "Confirm no candidate code was executed",
            "Confirm no core/runtime/app/memory/route mutation occurred",
            "Choose reject, request more evidence, or prepare D111 explicit approval gate",
        ],
        "human_decision_options": [
            "REJECT_SANDBOX_PROPOSAL",
            "REQUEST_MORE_SANDBOX_EVIDENCE",
            "PREPARE_D111_EXPLICIT_APPROVAL_GATE_ONLY",
        ],
        "evidence": {
            "d109_report": D109_REPORT,
            "static_checks": D109_STATIC_CHECKS,
            "regression_results": D109_REGRESSION_RESULTS,
            "diff_summary": D109_DIFF_SUMMARY,
            "review_summary": PROPOSAL_REVIEW_SUMMARY_OUT,
        },
        "regression_summary": d109.get("summary", {}),
        "static_summary": {
            "ok": static_checks.get("ok"),
            "existing_files_count": len(static_checks.get("existing_files", [])),
            "missing_files_count": len(static_checks.get("missing_files", [])),
            "blocked_paths_count": len(static_checks.get("blocked_paths_detected", [])),
        },
        "approval_granted": False,
        "actual_apply_executed": False,
        "candidate_executed": False,
    }


def build_approval_record(gate_id, review_summary):
    return {
        "state": "D110_APPROVAL_OR_REJECTION_RECORD",
        "ok": True,
        "gate_id": gate_id,
        "created_at": now(),
        "proposal_id": review_summary.get("proposal_id"),
        "decision_state": "PENDING_HUMAN_DECISION",
        "approval_granted_now": False,
        "rejection_recorded_now": False,
        "allowed_human_decisions": [
            "REJECT_SANDBOX_PROPOSAL",
            "REQUEST_MORE_SANDBOX_EVIDENCE",
            "PREPARE_D111_EXPLICIT_APPROVAL_GATE_ONLY",
        ],
        "not_approved": [
            "real_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "git_commit_or_push_by_ai",
            "sandbox_candidate_execution",
        ],
        "human_phrase_required_for_later_gate": "APPROVE_D111_EXPLICIT_APPROVAL_GATE_ONLY",
        "actual_apply_executed": False,
        "candidate_executed": False,
    }


def build_d111_scope(gate_id, review_summary):
    return {
        "state": "D110_D111_EXPLICIT_APPROVAL_GATE_SCOPE",
        "ok": True,
        "gate_id": gate_id,
        "proposal_id": review_summary.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D111_GATE,
        "d111_allowed_to_create": [
            "explicit_approval_gate",
            "explicit_approval_statement",
            "operator_decision_record",
            "d112_dry_run_apply_scope",
        ],
        "d111_must_not_execute": [
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
        "human_review_required": True,
        "actual_apply_allowed_after_d110": False,
        "route_insert_allowed_after_d110": False,
        "protected_core_mutation_allowed_after_d110": False,
        "sandbox_candidate_execution_allowed_after_d110": False,
        "required_phrase_for_later_gate": "APPROVE_D111_EXPLICIT_APPROVAL_GATE_ONLY",
    }


def create_human_review_gate(root="."):
    root = Path(root).resolve()

    d109 = read_json(root / D109_REPORT, {}) or {}
    static_checks = read_json(root / D109_STATIC_CHECKS, {}) or {}
    regression_results = read_json(root / D109_REGRESSION_RESULTS, {}) or {}
    diff_summary = read_json(root / D109_DIFF_SUMMARY, {}) or {}
    d110_scope = read_json(root / D109_D110_SCOPE, {}) or {}
    sandbox_proposal = read_json(root / D108_SANDBOX_PROPOSAL, {}) or {}

    errors = validate_d109(d109, static_checks, regression_results, diff_summary, d110_scope, sandbox_proposal)

    gate_id = "d110-" + digest({
        "runner_id": d109.get("runner_id"),
        "writer_id": d109.get("writer_id"),
        "proposal_id": d109.get("proposal_id"),
    })

    ok = not errors
    decision = "HUMAN_REVIEW_GATE_READY" if ok else "HUMAN_REVIEW_GATE_BLOCKED"
    result = "D110_HUMAN_REVIEW_GATE_CREATED" if ok else "D110_HUMAN_REVIEW_GATE_BLOCKED"

    review_summary = build_review_summary(gate_id, d109, static_checks, regression_results, sandbox_proposal)
    human_packet = build_human_packet(gate_id, d109, static_checks, regression_results, diff_summary, review_summary)
    approval_record = build_approval_record(gate_id, review_summary)
    d111_scope = build_d111_scope(gate_id, review_summary)

    if ok:
        write_json(root / PROPOSAL_REVIEW_SUMMARY_OUT, review_summary)
        write_json(root / HUMAN_PACKET_OUT, human_packet)
        write_json(root / APPROVAL_RECORD_OUT, approval_record)
        write_json(root / D111_SCOPE_OUT, d111_scope)

    report = {
        "state": "D110_HUMAN_REVIEW_GATE",
        "result": result,
        "route": "FIELD_INTENT_HUMAN_REVIEW_GATE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "gate_id": gate_id,
        "runner_id": d109.get("runner_id"),
        "writer_id": d109.get("writer_id"),
        "proposal_id": review_summary.get("proposal_id"),
        "source_d109_report": D109_REPORT,
        "human_review_packet": human_packet if ok else {},
        "proposal_review_summary": review_summary if ok else {},
        "approval_or_rejection_record": approval_record if ok else {},
        "d111_scope": d111_scope if ok else {},
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
            "human_review_packet_only": True,
            "approval_granted": False,
            "candidate_execution_allowed": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": [],
        },
        "summary": {
            "decision": decision,
            "gate_id": gate_id,
            "runner_id": d109.get("runner_id"),
            "proposal_id": review_summary.get("proposal_id"),
            "approval_state": "PENDING_HUMAN_DECISION" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D111_GATE,
        },
        "success_condition": {
            "human_review_gate_created": ok,
            "human_review_packet_created": ok,
            "proposal_review_summary_created": ok,
            "approval_record_created": ok,
            "d111_scope_created": ok,
            "approval_granted": False,
            "real_ai_called": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "protected_core_untouched": True,
            "next_step": "D111 may create an explicit human approval gate only. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_human_review_gate(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.human_review_gate import create_human_review_gate


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD110HumanReviewGate(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        (root / "runtime_experimental/ai_sandbox_work").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"

        d109 = {
            "ok": True,
            "decision": "REGRESSION_RUNNER_READY",
            "runner_id": "d109-test",
            "writer_id": "d108-test",
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
                "sandbox_regression_only": True,
                "candidate_execution_allowed": False,
            },
            "summary": {
                "regression_ok": True,
                "static_ok": True,
                "next_step": "D110_HUMAN_REVIEW_GATE",
            },
        }

        static_checks = {
            "ok": True,
            "existing_files": ["runtime_experimental/ai_sandbox_work/d108_accepted_proposal.json"],
            "missing_files": [],
            "blocked_paths_detected": [],
            "actual_apply_executed": False,
            "candidate_executed": False,
            "protected_core_mutated": False,
            "route_inserted": False,
        }

        regression_results = {
            "ok": True,
            "failed_count": 0,
            "passed_count": 4,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "shell_from_ai_executed": False,
        }

        diff_summary = {
            "ok": True,
            "documentation_only": True,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        d110_scope = {
            "ok": True,
            "allowed_next_gate": "D110_HUMAN_REVIEW_GATE",
            "human_review_required": True,
            "actual_apply_allowed_after_d109": False,
            "route_insert_allowed_after_d109": False,
            "protected_core_mutation_allowed_after_d109": False,
            "sandbox_candidate_execution_allowed_after_d109": False,
        }

        sandbox_proposal = {
            "ok": True,
            "sandbox_copy_only": True,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "proposal": {
                "proposal_id": proposal_id,
                "proposal_type": "analysis_proposal",
                "intent": "review sandbox proposal",
                "target_scope": "runtime_experimental/ai_sandbox_work/",
                "candidate_files": ["runtime_experimental/ai_sandbox_work/proposal_manifest.json"],
                "risk_flags": ["proposal_only"],
                "requires_human_review": True,
            },
        }

        write(root / "reports/d109_regression_runner.json", d109)
        write(root / "reports/d109_sandbox_static_checks.json", static_checks)
        write(root / "reports/d109_sandbox_regression_results.json", regression_results)
        write(root / "reports/d109_sandbox_diff_summary.json", diff_summary)
        write(root / "reports/d109_d110_human_review_gate_scope.json", d110_scope)
        write(root / "runtime_experimental/ai_sandbox_work/d108_accepted_proposal.json", sandbox_proposal)

        return td, root

    def test_creates_human_review_outputs(self):
        td, root = self.root()
        try:
            r = create_human_review_gate(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "HUMAN_REVIEW_GATE_READY")
            self.assertEqual(r["summary"]["approval_state"], "PENDING_HUMAN_DECISION")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["approval_granted"])
            self.assertEqual(r["d111_scope"]["allowed_next_gate"], "D111_EXPLICIT_APPROVAL_GATE")
            self.assertTrue((root / "reports/d110_human_review_gate.json").exists())
            self.assertTrue((root / "reports/d110_human_review_packet.json").exists())
            self.assertTrue((root / "reports/d110_proposal_review_summary.json").exists())
            self.assertTrue((root / "reports/d110_approval_or_rejection_record.json").exists())
            self.assertTrue((root / "reports/d110_d111_explicit_approval_gate_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d109(self):
        td, root = self.root()
        try:
            (root / "reports/d109_regression_runner.json").unlink()
            r = create_human_review_gate(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_regression_failed(self):
        td, root = self.root()
        try:
            p = root / "reports/d109_sandbox_regression_results.json"
            data = json.loads(p.read_text())
            data["ok"] = False
            data["failed_count"] = 1
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_human_review_gate(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d109_claims_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d109_regression_runner.json"
            data = json.loads(p.read_text())
            data["guardrails"]["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_human_review_gate(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_blocked_candidate_path(self):
        td, root = self.root()
        try:
            p = root / "runtime_experimental/ai_sandbox_work/d108_accepted_proposal.json"
            data = json.loads(p.read_text())
            data["proposal"]["candidate_files"] = ["core/unsafe.py"]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_human_review_gate(root)
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

print("D110 HUMAN REVIEW GATE BOOT: repo =", ROOT)

Path("runtime_experimental/human_review_gate.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d110_human_review_gate.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/human_review_gate.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d110_human_review_gate", "-v"], check=True)

print("\n== run D110 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.human_review_gate import create_human_review_gate\n"
    "r=create_human_review_gate()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d110_human_review_gate.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/human_review_gate.py",
    "tests/test_d110_human_review_gate.py",
    "reports/d110_human_review_gate.json",
    "reports/d110_human_review_packet.json",
    "reports/d110_proposal_review_summary.json",
    "reports/d110_approval_or_rejection_record.json",
    "reports/d110_d111_explicit_approval_gate_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D110_HUMAN_REVIEW_GATE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D110 human review gate"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D110 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD110 HUMAN REVIEW GATE BOOT DONE")
