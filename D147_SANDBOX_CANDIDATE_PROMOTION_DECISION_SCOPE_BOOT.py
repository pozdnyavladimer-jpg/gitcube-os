#!/usr/bin/env python3
# D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_BOOT.py
#
# D147 consumes D146 archive artifacts and creates a sandbox-candidate promotion
# decision scope. It does NOT perform real/core apply. It does NOT mutate
# protected core, insert routes, call network/provider, read secrets, execute shell
# from AI, or perform AI git actions.
#
# D147 opens D148 Sandbox Candidate Human Real Apply Intent Scope only.

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

D146_REPORT = "reports/d146_sandbox_candidate_archive_scope.json"
D146_ARCHIVE_MANIFEST = "reports/d146_sandbox_candidate_archive_manifest.json"
D146_CHAIN_CLOSURE = "reports/d146_sandbox_candidate_chain_closure_receipt.json"
D146_D147_SCOPE = "reports/d146_d147_sandbox_candidate_promotion_decision_scope.json"

OUT = "reports/d147_sandbox_candidate_promotion_decision_scope.json"
DECISION_RECORD_OUT = "reports/d147_sandbox_candidate_promotion_decision_record.json"
REAL_APPLY_READINESS_OUT = "reports/d147_sandbox_candidate_real_apply_readiness_review.json"
D148_SCOPE_OUT = "reports/d147_d148_sandbox_candidate_human_real_apply_intent_scope.json"

REQ_D146_DECISION = "SANDBOX_CANDIDATE_ARCHIVE_SCOPE_READY"
REQ_D147_GATE = "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE"
REQ_D148_GATE = "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE"
REQ_D146_APPROVAL_SCOPE = "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_ONLY"

FALSE_GUARD_KEYS = [
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
    "route_inserted",
    "git_commit_by_ai",
    "git_push_by_ai",
    "git_action_by_ai",
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


def validate_d146(d146, archive_manifest, chain_closure, d147_scope):
    errors = []

    if not d146:
        errors.append("missing D146 sandbox candidate archive scope report")
        return errors

    if d146.get("ok") is not True:
        errors.append("D146 ok must be true")
    if d146.get("decision") != REQ_D146_DECISION:
        errors.append("D146 decision must be SANDBOX_CANDIDATE_ARCHIVE_SCOPE_READY")

    guard = d146.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if key in guard and guard.get(key) is not False:
            errors.append(f"D146 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_archive_scope_only",
        "archive_manifest_only",
        "chain_closure_receipt_only",
        "approval_for_d147_promotion_decision_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D146 guardrails.{key} must be true")

    for key in [
        "candidate_reexecuted_now",
        "real_apply_executed_now",
        "approval_for_real_apply_by_ai",
        "route_insert_allowed_by_ai",
        "protected_core_mutation_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if key in guard and guard.get(key) is not False:
            errors.append(f"D146 guardrails.{key} must be false")

    summary = d146.get("summary", {})
    expected = {
        "archive_status": "ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
        "chain_closure_status": "SANDBOX_CHAIN_ARCHIVED_READY_FOR_PROMOTION_DECISION",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": REQ_D146_APPROVAL_SCOPE,
        "next_step": REQ_D147_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D146 summary.{key} must be {value}")

    candidate_status = summary.get("candidate_status", "")
    if "ARCHIVED" not in candidate_status:
        errors.append("D146 summary.candidate_status must indicate archived sandbox candidate")
    if "NOT_CORE_APPLIED" not in candidate_status:
        errors.append("D146 summary.candidate_status must indicate not core applied")

    if not archive_manifest:
        errors.append("missing D146 sandbox candidate archive manifest")
    else:
        if archive_manifest.get("ok") is not True:
            errors.append("D146 archive manifest ok must be true")
        if archive_manifest.get("archive_mode") not in [
            "ARCHIVE_MANIFEST_ONLY_NOT_COMPRESSED_NOT_UPLOADED",
            "SANDBOX_CHAIN_ARCHIVE_MANIFEST_ONLY",
        ]:
            errors.append("D146 archive manifest mode must be archive-manifest-only")
        for key in ["real_apply_executed", "route_inserted", "protected_core_mutated"]:
            if archive_manifest.get(key) is not False:
                errors.append(f"D146 archive manifest {key} must be false")

    if not chain_closure:
        errors.append("missing D146 chain closure receipt")
    else:
        if chain_closure.get("ok") is not True:
            errors.append("D146 chain closure receipt ok must be true")
        if chain_closure.get("closure_status") not in [
            "SANDBOX_CHAIN_ARCHIVED_READY_FOR_PROMOTION_DECISION",
            "SANDBOX_CHAIN_CLOSED_READY_FOR_PROMOTION_DECISION",
        ]:
            errors.append("D146 chain closure receipt must be ready for promotion decision")
        for key in ["real_apply_executed", "route_inserted", "protected_core_mutated"]:
            if chain_closure.get(key) is not False:
                errors.append(f"D146 chain closure receipt {key} must be false")

    if not d147_scope:
        errors.append("missing D146 D147 promotion decision scope")
    else:
        if d147_scope.get("ok") is not True:
            errors.append("D146 D147 scope ok must be true")
        if d147_scope.get("allowed_next_gate") != REQ_D147_GATE:
            errors.append("D146 D147 scope allowed_next_gate must be D147")
        if d147_scope.get("sandbox_candidate_promotion_decision_scope_only") is not True:
            errors.append("D146 D147 scope must be promotion-decision-only")
        if d147_scope.get("human_review_required") is not True:
            errors.append("D146 D147 scope must require human review")
        for key in [
            "real_apply_allowed_after_d146_by_ai",
            "route_insert_allowed_after_d146_by_ai",
            "protected_core_mutation_allowed_after_d146_by_ai",
            "network_allowed_after_d146_by_ai",
            "secret_read_allowed_after_d146_by_ai",
            "shell_allowed_after_d146_by_ai",
            "git_action_allowed_after_d146_by_ai",
        ]:
            if d147_scope.get(key) is not False:
                errors.append(f"D146 D147 scope {key} must be false")

    return errors


def build_decision_record(decision_id, d146):
    return {
        "state": "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_RECORD",
        "ok": True,
        "decision_id": decision_id,
        "archive_id": d146.get("archive_id"),
        "verification_id": d146.get("verification_id"),
        "apply_id": d146.get("apply_id"),
        "run_id": d146.get("run_id"),
        "candidate_id": d146.get("candidate_id"),
        "proposal_id": d146.get("proposal_id"),
        "created_at": now(),
        "decision_mode": "PROMOTION_DECISION_RECORD_ONLY_NO_REAL_APPLY",
        "promotion_decision": "PROMOTE_TO_REAL_APPLY_PATH",
        "promotion_meaning": "Open D148 human real apply intent scope only; do not perform real/core apply now.",
        "candidate_status": "SANDBOX_CHAIN_AUDITED_ARCHIVED_PROMOTION_PATH_SELECTED_NOT_CORE_APPLIED",
        "real_apply_executed_now": False,
        "route_inserted_now": False,
        "protected_core_mutated_now": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_real_apply_readiness(decision_id, d146):
    return {
        "state": "D147_SANDBOX_CANDIDATE_REAL_APPLY_READINESS_REVIEW",
        "ok": True,
        "decision_id": decision_id,
        "archive_id": d146.get("archive_id"),
        "candidate_id": d146.get("candidate_id"),
        "created_at": now(),
        "review_mode": "READINESS_REVIEW_ONLY_NO_REAL_APPLY",
        "readiness_status": "READY_FOR_HUMAN_REAL_APPLY_INTENT_GATE",
        "required_prior_chain": [
            "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_READY",
            "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_READY",
            "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_READY",
            "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_READY",
            "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_READY",
            "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_READY",
        ],
        "must_remain_false": {
            "real_apply_executed_now": False,
            "route_inserted_now": False,
            "protected_core_mutated_now": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        },
        "human_review_required": True,
    }


def build_d148_scope(decision_id, d146):
    return {
        "state": "D147_D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE",
        "ok": True,
        "decision_id": decision_id,
        "archive_id": d146.get("archive_id"),
        "verification_id": d146.get("verification_id"),
        "apply_id": d146.get("apply_id"),
        "run_id": d146.get("run_id"),
        "candidate_id": d146.get("candidate_id"),
        "proposal_id": d146.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D148_GATE,
        "d148_allowed_to_create": [
            "sandbox_candidate_human_real_apply_intent_scope",
            "sandbox_candidate_human_real_apply_intent_record",
            "sandbox_candidate_real_apply_authority_guard",
            "d149_sandbox_candidate_guarded_real_apply_preflight_scope",
        ],
        "d148_must_not_execute": [
            "real_core_apply_by_ai",
            "auto_apply",
            "route_insert_by_ai",
            "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai",
            "shell_exec_from_ai",
            "network_or_provider_call_by_ai",
            "secret_read_by_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute_by_ai",
            "restore_execute_by_ai",
        ],
        "sandbox_candidate_human_real_apply_intent_scope_only": True,
        "human_review_required": True,
        "real_apply_allowed_after_d147_by_ai": False,
        "route_insert_allowed_after_d147_by_ai": False,
        "protected_core_mutation_allowed_after_d147_by_ai": False,
        "network_allowed_after_d147_by_ai": False,
        "secret_read_allowed_after_d147_by_ai": False,
        "shell_allowed_after_d147_by_ai": False,
        "git_action_allowed_after_d147_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_ONLY",
    }


def create_sandbox_candidate_promotion_decision_scope(root="."):
    root = Path(root).resolve()

    d146 = read_json(root / D146_REPORT, {}) or {}
    archive_manifest = read_json(root / D146_ARCHIVE_MANIFEST, {}) or {}
    chain_closure = read_json(root / D146_CHAIN_CLOSURE, {}) or {}
    d147_scope = read_json(root / D146_D147_SCOPE, {}) or {}

    errors = validate_d146(d146, archive_manifest, chain_closure, d147_scope)

    decision_id = "d147-" + digest({
        "archive_id": d146.get("archive_id"),
        "candidate_id": d146.get("candidate_id"),
        "proposal_id": d146.get("proposal_id"),
    })

    decision_record = build_decision_record(decision_id, d146)
    readiness_review = build_real_apply_readiness(decision_id, d146)
    d148_scope = build_d148_scope(decision_id, d146)

    for item_name, item in [("decision_record", decision_record), ("readiness_review", readiness_review)]:
        for key in ["real_apply_executed_now", "route_inserted_now", "protected_core_mutated_now"]:
            if item.get(key) is not False and item.get("must_remain_false", {}).get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_BLOCKED"
    result = "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_CREATED" if ok else "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_BLOCKED"

    if ok:
        write_json(root / DECISION_RECORD_OUT, decision_record)
        write_json(root / REAL_APPLY_READINESS_OUT, readiness_review)
        write_json(root / D148_SCOPE_OUT, d148_scope)

    report = {
        "state": "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "decision_id": decision_id,
        "archive_id": d146.get("archive_id"),
        "verification_id": d146.get("verification_id"),
        "apply_id": d146.get("apply_id"),
        "run_id": d146.get("run_id"),
        "candidate_id": d146.get("candidate_id"),
        "proposal_id": d146.get("proposal_id"),
        "source_d146_report": D146_REPORT,
        "promotion_decision_record": decision_record if ok else {},
        "real_apply_readiness_review": readiness_review if ok else {},
        "d148_scope": d148_scope if ok else {},
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
            "route_inserted": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
            "sandbox_candidate_promotion_decision_scope_only": True,
            "promotion_decision_record_only": True,
            "real_apply_readiness_review_only": True,
            "approval_for_d148_human_real_apply_intent_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "real_apply_allowed_now": False,
            "route_insert_allowed_now": False,
            "protected_core_mutation_allowed_now": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "decision_id": decision_id,
            "archive_id": d146.get("archive_id"),
            "candidate_id": d146.get("candidate_id"),
            "proposal_id": d146.get("proposal_id"),
            "promotion_decision": "PROMOTE_TO_REAL_APPLY_PATH" if ok else "BLOCKED",
            "promotion_status": "PROMOTION_PATH_SELECTED_HUMAN_REAL_APPLY_INTENT_REQUIRED" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CHAIN_AUDITED_ARCHIVED_PROMOTION_PATH_SELECTED_NOT_CORE_APPLIED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D148_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_promotion_decision_scope_created": ok,
            "promotion_decision_record_created": ok,
            "real_apply_readiness_review_created": ok,
            "d148_scope_created": ok,
            "real_core_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "next_step": "D148 may create human real apply intent scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_promotion_decision_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_promotion_decision_scope import create_sandbox_candidate_promotion_decision_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD147SandboxCandidatePromotionDecisionScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        archive_id = "d146-test"
        verification_id = "d144-test"
        apply_id = "d143-test"
        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        false_guard = {
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
            "route_inserted": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
        }

        d146 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_ARCHIVE_SCOPE_READY",
            "archive_id": archive_id,
            "verification_id": verification_id,
            "apply_id": apply_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_archive_scope_only": True,
                "archive_manifest_only": True,
                "chain_closure_receipt_only": True,
                "approval_for_d147_promotion_decision_scope_only": True,
                "candidate_reexecuted_now": False,
                "real_apply_executed_now": False,
                "approval_for_real_apply_by_ai": False,
                "route_insert_allowed_by_ai": False,
                "protected_core_mutation_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "archive_status": "ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
                "chain_closure_status": "SANDBOX_CHAIN_ARCHIVED_READY_FOR_PROMOTION_DECISION",
                "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_ARCHIVED_NOT_CORE_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_ONLY",
                "next_step": "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE",
            },
        }

        archive_manifest = {
            "ok": True,
            "archive_id": archive_id,
            "candidate_id": candidate_id,
            "archive_mode": "ARCHIVE_MANIFEST_ONLY_NOT_COMPRESSED_NOT_UPLOADED",
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
        }
        chain_closure = {
            "ok": True,
            "archive_id": archive_id,
            "candidate_id": candidate_id,
            "closure_status": "SANDBOX_CHAIN_ARCHIVED_READY_FOR_PROMOTION_DECISION",
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
        }
        d147_scope = {
            "ok": True,
            "archive_id": archive_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE",
            "sandbox_candidate_promotion_decision_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d146_by_ai": False,
            "route_insert_allowed_after_d146_by_ai": False,
            "protected_core_mutation_allowed_after_d146_by_ai": False,
            "network_allowed_after_d146_by_ai": False,
            "secret_read_allowed_after_d146_by_ai": False,
            "shell_allowed_after_d146_by_ai": False,
            "git_action_allowed_after_d146_by_ai": False,
        }

        write(root / "reports/d146_sandbox_candidate_archive_scope.json", d146)
        write(root / "reports/d146_sandbox_candidate_archive_manifest.json", archive_manifest)
        write(root / "reports/d146_sandbox_candidate_chain_closure_receipt.json", chain_closure)
        write(root / "reports/d146_d147_sandbox_candidate_promotion_decision_scope.json", d147_scope)
        return td, root

    def test_creates_promotion_decision_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_promotion_decision_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_READY")
            self.assertEqual(r["summary"]["promotion_decision"], "PROMOTE_TO_REAL_APPLY_PATH")
            self.assertEqual(r["summary"]["approval_scope"], "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["real_apply_allowed_now"])
            self.assertFalse(r["guardrails"]["route_insert_allowed_now"])
            self.assertFalse(r["guardrails"]["protected_core_mutation_allowed_now"])
            self.assertEqual(r["d148_scope"]["allowed_next_gate"], "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE")
            self.assertTrue((root / "reports/d147_sandbox_candidate_promotion_decision_scope.json").exists())
            self.assertTrue((root / "reports/d147_sandbox_candidate_promotion_decision_record.json").exists())
            self.assertTrue((root / "reports/d147_sandbox_candidate_real_apply_readiness_review.json").exists())
            self.assertTrue((root / "reports/d147_d148_sandbox_candidate_human_real_apply_intent_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d146(self):
        td, root = self.root()
        try:
            (root / "reports/d146_sandbox_candidate_archive_scope.json").unlink()
            r = create_sandbox_candidate_promotion_decision_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d146_summary_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d146_sandbox_candidate_archive_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["real_apply_by_ai_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_promotion_decision_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_archive_manifest_says_core_mutated(self):
        td, root = self.root()
        try:
            p = root / "reports/d146_sandbox_candidate_archive_manifest.json"
            data = json.loads(p.read_text())
            data["protected_core_mutated"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_promotion_decision_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d147_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d146_d147_sandbox_candidate_promotion_decision_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d146_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_promotion_decision_scope(root)
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

print("D147 SANDBOX CANDIDATE PROMOTION DECISION SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_promotion_decision_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d147_sandbox_candidate_promotion_decision_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_promotion_decision_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d147_sandbox_candidate_promotion_decision_scope", "-v"], check=True)

print("\n== run D147 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_promotion_decision_scope import create_sandbox_candidate_promotion_decision_scope\n"
    "r=create_sandbox_candidate_promotion_decision_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d147_sandbox_candidate_promotion_decision_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_promotion_decision_scope.py",
    "tests/test_d147_sandbox_candidate_promotion_decision_scope.py",
    "reports/d147_sandbox_candidate_promotion_decision_scope.json",
    "reports/d147_sandbox_candidate_promotion_decision_record.json",
    "reports/d147_sandbox_candidate_real_apply_readiness_review.json",
    "reports/d147_d148_sandbox_candidate_human_real_apply_intent_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D147 sandbox candidate promotion decision scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D147 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD147 SANDBOX CANDIDATE PROMOTION DECISION SCOPE BOOT DONE")
