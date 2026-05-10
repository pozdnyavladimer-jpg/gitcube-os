#!/usr/bin/env python3
# D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_BOOT.py
#
# D148 consumes D147 sandbox candidate promotion decision artifacts and creates:
# - runtime_experimental/sandbox_candidate_human_real_apply_intent_scope.py
# - tests/test_d148_sandbox_candidate_human_real_apply_intent_scope.py
# - reports/d148_sandbox_candidate_human_real_apply_intent_scope.json
# - reports/d148_sandbox_candidate_human_real_apply_intent_record.json
# - reports/d148_sandbox_candidate_real_apply_authority_guard.json
# - reports/d148_d149_sandbox_candidate_guarded_real_apply_preflight_scope.json
#
# HUMAN REAL APPLY INTENT SCOPE ONLY:
# no real/core apply, no route insert, no protected core mutation, no shell,
# no network, no secret read, no git action by AI, no candidate re-execution.
#
# D148 opens D149 Guarded Real Apply Preflight Scope only.

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

D147_REPORT = "reports/d147_sandbox_candidate_promotion_decision_scope.json"
D147_DECISION_RECORD = "reports/d147_sandbox_candidate_promotion_decision_record.json"
D147_READINESS_REVIEW = "reports/d147_sandbox_candidate_real_apply_readiness_review.json"
D147_D148_SCOPE = "reports/d147_d148_sandbox_candidate_human_real_apply_intent_scope.json"

OUT = "reports/d148_sandbox_candidate_human_real_apply_intent_scope.json"
INTENT_RECORD_OUT = "reports/d148_sandbox_candidate_human_real_apply_intent_record.json"
AUTHORITY_GUARD_OUT = "reports/d148_sandbox_candidate_real_apply_authority_guard.json"
D149_SCOPE_OUT = "reports/d148_d149_sandbox_candidate_guarded_real_apply_preflight_scope.json"

REQ_D147_DECISION = "SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_READY"
REQ_D148_GATE = "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE"
REQ_D149_GATE = "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE"

FALSE_KEYS = [
    "external_ai_called",
    "network_accessed",
    "api_key_read",
    "secret_read",
    "shell_from_ai_executed",
    "shell_executed_by_ai",
    "runtime_code_mutated",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "actual_apply_executed",
    "real_apply_executed",
    "route_inserted",
    "git_commit_by_ai",
    "git_push_by_ai",
    "git_action_by_ai",
    "rollback_executed",
    "restore_executed",
]

STATUS_FALSE_KEYS = [
    "real_apply_allowed_after_d147_by_ai",
    "route_insert_allowed_after_d147_by_ai",
    "protected_core_mutation_allowed_after_d147_by_ai",
    "network_allowed_after_d147_by_ai",
    "secret_read_allowed_after_d147_by_ai",
    "shell_allowed_after_d147_by_ai",
    "git_action_allowed_after_d147_by_ai",
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


def validate_d147(d147, decision_record, readiness_review, d148_scope):
    errors = []

    if not d147:
        errors.append("missing D147 sandbox candidate promotion decision scope report")
        return errors

    if d147.get("ok") is not True:
        errors.append("D147 ok must be true")
    if d147.get("decision") != REQ_D147_DECISION:
        errors.append("D147 decision must be SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_READY")

    summary = d147.get("summary", {})
    if summary.get("promotion_decision") not in ("PROMOTE_TO_REAL_APPLY_PATH", "PROMOTION_PATH_SELECTED"):
        errors.append("D147 promotion decision must select real-apply path")
    if summary.get("real_provider_status") not in (None, "NOT_CALLED"):
        errors.append("D147 real_provider_status must be NOT_CALLED")
    if summary.get("network_status") not in (None, "NOT_ACCESSED"):
        errors.append("D147 network_status must be NOT_ACCESSED")
    if summary.get("secret_status") not in (None, "NOT_READ"):
        errors.append("D147 secret_status must be NOT_READ")
    if summary.get("shell_status") not in (None, "NOT_EXECUTED"):
        errors.append("D147 shell_status must be NOT_EXECUTED")
    if summary.get("real_apply_by_ai_status") not in (None, "BLOCKED"):
        errors.append("D147 real_apply_by_ai_status must be BLOCKED")
    if summary.get("route_insert_status") not in (None, "BLOCKED"):
        errors.append("D147 route_insert_status must be BLOCKED")
    if summary.get("protected_core_status") not in (None, "UNTOUCHED_BY_AI"):
        errors.append("D147 protected_core_status must be UNTOUCHED_BY_AI")
    if summary.get("next_step") not in (None, REQ_D148_GATE):
        errors.append("D147 next_step must be D148 human real apply intent scope")

    guard = d147.get("guardrails", {})
    for key in FALSE_KEYS:
        if key in guard and guard.get(key) is not False:
            errors.append(f"D147 guardrails.{key} must be false")

    if not decision_record:
        errors.append("missing D147 sandbox candidate promotion decision record")
    else:
        if decision_record.get("ok") is not True:
            errors.append("D147 promotion decision record ok must be true")
        if decision_record.get("promotion_decision") not in ("PROMOTE_TO_REAL_APPLY_PATH", "PROMOTION_PATH_SELECTED"):
            errors.append("D147 promotion decision record must select promotion path")
        for key in FALSE_KEYS + STATUS_FALSE_KEYS:
            if key in decision_record and decision_record.get(key) is not False:
                errors.append(f"D147 promotion decision record {key} must be false")

    if not readiness_review:
        errors.append("missing D147 real apply readiness review")
    else:
        if readiness_review.get("ok") is not True:
            errors.append("D147 real apply readiness review ok must be true")
        for key in FALSE_KEYS + STATUS_FALSE_KEYS:
            if key in readiness_review and readiness_review.get(key) is not False:
                errors.append(f"D147 readiness review {key} must be false")

    if not d148_scope:
        errors.append("missing D147 D148 human real apply intent scope")
    else:
        if d148_scope.get("ok") is not True:
            errors.append("D147 D148 scope ok must be true")
        if d148_scope.get("allowed_next_gate") != REQ_D148_GATE:
            errors.append("D147 D148 scope allowed_next_gate must be D148")
        if d148_scope.get("sandbox_candidate_human_real_apply_intent_scope_only") is not True:
            errors.append("D147 D148 scope must be human-real-apply-intent-only")
        if d148_scope.get("human_review_required") is not True:
            errors.append("D147 D148 scope must require human review")
        for key in STATUS_FALSE_KEYS:
            if d148_scope.get(key) is not False:
                errors.append(f"D147 D148 scope {key} must be false")

    return errors


def build_intent_record(intent_id, d147):
    return {
        "state": "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_RECORD",
        "ok": True,
        "intent_id": intent_id,
        "decision_id": d147.get("decision_id"),
        "archive_id": d147.get("archive_id"),
        "candidate_id": d147.get("candidate_id"),
        "proposal_id": d147.get("proposal_id"),
        "created_at": now(),
        "intent_mode": "HUMAN_REAL_APPLY_INTENT_RECORD_ONLY_NO_REAL_APPLY",
        "operator_intent_status": "HUMAN_REAL_APPLY_INTENT_RECORDED_NO_EXECUTION",
        "approved_for_d149_guarded_real_apply_preflight_scope_only": True,
        "approved_for_real_core_apply_now": False,
        "actual_apply_executed": False,
        "real_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
        "required_phrase_for_next_gate": "APPROVE_D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_ONLY",
    }


def build_authority_guard(intent_id, d147):
    return {
        "state": "D148_SANDBOX_CANDIDATE_REAL_APPLY_AUTHORITY_GUARD",
        "ok": True,
        "intent_id": intent_id,
        "decision_id": d147.get("decision_id"),
        "candidate_id": d147.get("candidate_id"),
        "created_at": now(),
        "authority_mode": "REAL_APPLY_AUTHORITY_GUARD_ONLY_NO_REAL_APPLY",
        "allow_d149_guarded_real_apply_preflight": True,
        "allow_real_core_apply_now": False,
        "allow_route_insert": False,
        "allow_protected_core_mutation": False,
        "allow_network": False,
        "allow_secret_read": False,
        "allow_shell_exec": False,
        "allow_git_action_by_ai": False,
        "real_apply_allowed_after_d148_by_ai": False,
        "route_insert_allowed_after_d148_by_ai": False,
        "protected_core_mutation_allowed_after_d148_by_ai": False,
        "network_allowed_after_d148_by_ai": False,
        "secret_read_allowed_after_d148_by_ai": False,
        "shell_allowed_after_d148_by_ai": False,
        "git_action_allowed_after_d148_by_ai": False,
        "human_review_required": True,
    }


def build_d149_scope(intent_id, d147):
    return {
        "state": "D148_D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE",
        "ok": True,
        "intent_id": intent_id,
        "decision_id": d147.get("decision_id"),
        "archive_id": d147.get("archive_id"),
        "verification_id": d147.get("verification_id"),
        "apply_id": d147.get("apply_id"),
        "run_id": d147.get("run_id"),
        "candidate_id": d147.get("candidate_id"),
        "proposal_id": d147.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D149_GATE,
        "sandbox_candidate_guarded_real_apply_preflight_scope_only": True,
        "human_review_required": True,
        "d149_allowed_to_create": [
            "guarded_real_apply_preflight_scope",
            "real_apply_preflight_report",
            "real_apply_blockers",
            "d150_human_signed_real_apply_execution_scope",
        ],
        "d149_must_not_execute": [
            "real_core_apply_now",
            "route_insert_by_ai",
            "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai",
            "shell_exec_from_ai",
            "network_call_by_ai",
            "secret_read_by_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute_by_ai",
            "restore_execute_by_ai",
        ],
        "real_apply_allowed_after_d148_by_ai": False,
        "route_insert_allowed_after_d148_by_ai": False,
        "protected_core_mutation_allowed_after_d148_by_ai": False,
        "network_allowed_after_d148_by_ai": False,
        "secret_read_allowed_after_d148_by_ai": False,
        "shell_allowed_after_d148_by_ai": False,
        "git_action_allowed_after_d148_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_ONLY",
    }


def create_sandbox_candidate_human_real_apply_intent_scope(root="."):
    root = Path(root).resolve()

    d147 = read_json(root / D147_REPORT, {}) or {}
    decision_record = read_json(root / D147_DECISION_RECORD, {}) or {}
    readiness_review = read_json(root / D147_READINESS_REVIEW, {}) or {}
    d148_scope = read_json(root / D147_D148_SCOPE, {}) or {}

    errors = validate_d147(d147, decision_record, readiness_review, d148_scope)

    intent_id = "d148-" + digest({
        "decision_id": d147.get("decision_id"),
        "archive_id": d147.get("archive_id"),
        "candidate_id": d147.get("candidate_id"),
        "proposal_id": d147.get("proposal_id"),
    })

    intent_record = build_intent_record(intent_id, d147)
    authority_guard = build_authority_guard(intent_id, d147)
    d149_scope = build_d149_scope(intent_id, d147)

    for item_name, item in [
        ("intent_record", intent_record),
        ("authority_guard", authority_guard),
        ("d149_scope", d149_scope),
    ]:
        for key in [
            "actual_apply_executed",
            "real_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "real_apply_allowed_after_d148_by_ai",
            "route_insert_allowed_after_d148_by_ai",
            "protected_core_mutation_allowed_after_d148_by_ai",
            "network_allowed_after_d148_by_ai",
            "secret_read_allowed_after_d148_by_ai",
            "shell_allowed_after_d148_by_ai",
            "git_action_allowed_after_d148_by_ai",
        ]:
            if key in item and item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_BLOCKED"
    result = "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_CREATED" if ok else "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_BLOCKED"

    if ok:
        write_json(root / INTENT_RECORD_OUT, intent_record)
        write_json(root / AUTHORITY_GUARD_OUT, authority_guard)
        write_json(root / D149_SCOPE_OUT, d149_scope)

    report = {
        "state": "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "intent_id": intent_id,
        "decision_id": d147.get("decision_id"),
        "archive_id": d147.get("archive_id"),
        "verification_id": d147.get("verification_id"),
        "apply_id": d147.get("apply_id"),
        "run_id": d147.get("run_id"),
        "candidate_id": d147.get("candidate_id"),
        "proposal_id": d147.get("proposal_id"),
        "source_d147_report": D147_REPORT,
        "human_real_apply_intent_record": intent_record if ok else {},
        "real_apply_authority_guard": authority_guard if ok else {},
        "d149_scope": d149_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "shell_executed_by_ai": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "sandbox_candidate_human_real_apply_intent_scope_only": True,
            "human_real_apply_intent_record_only": True,
            "real_apply_authority_guard_only": True,
            "approval_for_d149_guarded_real_apply_preflight_scope_only": ok,
            "approval_for_real_core_apply_now": False,
            "real_apply_allowed_after_d148_by_ai": False,
            "route_insert_allowed_after_d148_by_ai": False,
            "protected_core_mutation_allowed_after_d148_by_ai": False,
            "network_allowed_after_d148_by_ai": False,
            "secret_read_allowed_after_d148_by_ai": False,
            "shell_allowed_after_d148_by_ai": False,
            "git_action_allowed_after_d148_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "intent_id": intent_id,
            "decision_id": d147.get("decision_id"),
            "archive_id": d147.get("archive_id"),
            "candidate_id": d147.get("candidate_id"),
            "proposal_id": d147.get("proposal_id"),
            "human_real_apply_intent_status": "HUMAN_REAL_APPLY_INTENT_RECORDED_NO_REAL_APPLY" if ok else "BLOCKED",
            "real_apply_authority_status": "REAL_APPLY_AUTHORITY_GUARD_CREATED_NO_REAL_APPLY" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CHAIN_PROMOTED_TO_REAL_APPLY_PREFLIGHT_PATH_NOT_CORE_APPLIED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D149_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "human_real_apply_intent_scope_created": ok,
            "human_real_apply_intent_record_created": ok,
            "real_apply_authority_guard_created": ok,
            "d149_scope_created": ok,
            "real_core_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "next_step": "D149 may create guarded real apply preflight scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_human_real_apply_intent_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_human_real_apply_intent_scope import create_sandbox_candidate_human_real_apply_intent_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD148SandboxCandidateHumanRealApplyIntentScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        decision_id = "d147-test"
        archive_id = "d146-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d147 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_READY",
            "decision_id": decision_id,
            "archive_id": archive_id,
            "verification_id": "d144-test",
            "apply_id": "d143-test",
            "run_id": "d139-test",
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": {
                "network_accessed": False,
                "secret_read": False,
                "shell_executed_by_ai": False,
                "actual_apply_executed": False,
                "real_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "git_action_by_ai": False,
            },
            "summary": {
                "promotion_decision": "PROMOTE_TO_REAL_APPLY_PATH",
                "candidate_status": "SANDBOX_CHAIN_AUDITED_ARCHIVED_PROMOTION_PATH_SELECTED_NOT_CORE_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_ONLY",
                "next_step": "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE",
            },
        }

        decision_record = {
            "ok": True,
            "decision_id": decision_id,
            "promotion_decision": "PROMOTE_TO_REAL_APPLY_PATH",
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        readiness_review = {
            "ok": True,
            "decision_id": decision_id,
            "candidate_id": candidate_id,
            "candidate_status": "SANDBOX_CHAIN_AUDITED_ARCHIVED_PROMOTION_PATH_SELECTED_NOT_CORE_APPLIED",
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        d148_scope = {
            "ok": True,
            "decision_id": decision_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE",
            "sandbox_candidate_human_real_apply_intent_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d147_by_ai": False,
            "route_insert_allowed_after_d147_by_ai": False,
            "protected_core_mutation_allowed_after_d147_by_ai": False,
            "network_allowed_after_d147_by_ai": False,
            "secret_read_allowed_after_d147_by_ai": False,
            "shell_allowed_after_d147_by_ai": False,
            "git_action_allowed_after_d147_by_ai": False,
        }

        write(root / "reports/d147_sandbox_candidate_promotion_decision_scope.json", d147)
        write(root / "reports/d147_sandbox_candidate_promotion_decision_record.json", decision_record)
        write(root / "reports/d147_sandbox_candidate_real_apply_readiness_review.json", readiness_review)
        write(root / "reports/d147_d148_sandbox_candidate_human_real_apply_intent_scope.json", d148_scope)

        return td, root

    def test_creates_human_real_apply_intent_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_human_real_apply_intent_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertEqual(r["d149_scope"]["allowed_next_gate"], "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE")
            self.assertTrue((root / "reports/d148_sandbox_candidate_human_real_apply_intent_scope.json").exists())
            self.assertTrue((root / "reports/d148_sandbox_candidate_human_real_apply_intent_record.json").exists())
            self.assertTrue((root / "reports/d148_sandbox_candidate_real_apply_authority_guard.json").exists())
            self.assertTrue((root / "reports/d148_d149_sandbox_candidate_guarded_real_apply_preflight_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d147(self):
        td, root = self.root()
        try:
            (root / "reports/d147_sandbox_candidate_promotion_decision_scope.json").unlink()
            r = create_sandbox_candidate_human_real_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d147_summary_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d147_sandbox_candidate_promotion_decision_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["network_status"] = "ACCESSED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_real_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_readiness_review_says_core_mutated(self):
        td, root = self.root()
        try:
            p = root / "reports/d147_sandbox_candidate_real_apply_readiness_review.json"
            data = json.loads(p.read_text())
            data["protected_core_mutated"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_real_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d148_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d147_d148_sandbox_candidate_human_real_apply_intent_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d147_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_real_apply_intent_scope(root)
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

print("D148 SANDBOX CANDIDATE HUMAN REAL APPLY INTENT SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_human_real_apply_intent_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d148_sandbox_candidate_human_real_apply_intent_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_human_real_apply_intent_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d148_sandbox_candidate_human_real_apply_intent_scope", "-v"], check=True)

print("\n== run D148 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_human_real_apply_intent_scope import create_sandbox_candidate_human_real_apply_intent_scope\n"
    "r=create_sandbox_candidate_human_real_apply_intent_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d148_sandbox_candidate_human_real_apply_intent_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_human_real_apply_intent_scope.py",
    "tests/test_d148_sandbox_candidate_human_real_apply_intent_scope.py",
    "reports/d148_sandbox_candidate_human_real_apply_intent_scope.json",
    "reports/d148_sandbox_candidate_human_real_apply_intent_record.json",
    "reports/d148_sandbox_candidate_real_apply_authority_guard.json",
    "reports/d148_d149_sandbox_candidate_guarded_real_apply_preflight_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D148 sandbox candidate human real apply intent scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D148 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD148 SANDBOX CANDIDATE HUMAN REAL APPLY INTENT SCOPE BOOT DONE")
