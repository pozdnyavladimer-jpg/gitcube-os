#!/usr/bin/env python3
# D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_BOOT.py
#
# D146 consumes D145 final audit artifacts and creates a sandbox candidate archive scope.
#
# ARCHIVE SCOPE ONLY:
# no real/core apply, no route insert, no protected core mutation, no shell, no network,
# no secret read, no AI git action, no repeat candidate execution.
#
# D146 opens D147 Sandbox Candidate Promotion Decision Scope.

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

D145_REPORT = "reports/d145_sandbox_candidate_final_audit_scope.json"
D145_LEDGER = "reports/d145_sandbox_candidate_final_audit_ledger.json"
D145_REPLAY_INDEX = "reports/d145_sandbox_candidate_replay_index.json"
D145_D146_SCOPE = "reports/d145_d146_sandbox_candidate_archive_scope.json"

OUT = "reports/d146_sandbox_candidate_archive_scope.json"
ARCHIVE_MANIFEST_OUT = "reports/d146_sandbox_candidate_archive_manifest.json"
CHAIN_CLOSURE_OUT = "reports/d146_sandbox_candidate_chain_closure_receipt.json"
D147_SCOPE_OUT = "reports/d146_d147_sandbox_candidate_promotion_decision_scope.json"

REQ_D145_DECISION = "SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_READY"
REQ_D146_GATE = "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE"
REQ_D147_GATE = "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE"
REQ_D145_APPROVAL_SCOPE = "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_ONLY"
REQ_D147_APPROVAL_SCOPE = "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_ONLY"

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

BLOCKED_SUMMARY = {
    "real_apply_by_ai_status": "BLOCKED",
    "route_insert_status": "BLOCKED",
    "protected_core_status": "UNTOUCHED_BY_AI",
    "network_status": "NOT_ACCESSED",
    "secret_status": "NOT_READ",
    "shell_status": "NOT_EXECUTED",
    "real_provider_status": "NOT_CALLED",
}

ARCHIVE_ITEMS = [
    "reports/d139_sandbox_candidate_controlled_execution_run_scope.json",
    "reports/d139_sandbox_candidate_execution_run_result.json",
    "reports/d139_sandbox_candidate_execution_safety_receipt.json",
    "reports/d140_sandbox_candidate_post_execution_verification_scope.json",
    "reports/d140_sandbox_candidate_post_execution_verification_report.json",
    "reports/d140_sandbox_candidate_execution_integrity_receipt.json",
    "reports/d141_sandbox_candidate_apply_preflight_scope.json",
    "reports/d141_sandbox_candidate_apply_preflight_report.json",
    "reports/d141_sandbox_candidate_apply_blockers.json",
    "reports/d142_sandbox_candidate_human_apply_intent_scope.json",
    "reports/d142_sandbox_candidate_human_apply_intent_record.json",
    "reports/d142_sandbox_candidate_apply_authority_guard.json",
    "reports/d143_sandbox_candidate_guarded_apply_scope.json",
    "reports/d143_sandbox_candidate_guarded_apply_plan.json",
    "reports/d143_sandbox_candidate_guarded_apply_receipt.json",
    "reports/d144_sandbox_candidate_post_apply_verification_scope.json",
    "reports/d144_sandbox_candidate_post_apply_verification_report.json",
    "reports/d144_sandbox_candidate_apply_integrity_receipt.json",
    "reports/d145_sandbox_candidate_final_audit_scope.json",
    "reports/d145_sandbox_candidate_final_audit_ledger.json",
    "reports/d145_sandbox_candidate_replay_index.json",
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


def false_guard_ok(obj, prefix, errors, keys=FALSE_KEYS):
    if not isinstance(obj, dict):
        return
    for key in keys:
        if key in obj and obj.get(key) is not False:
            errors.append(f"{prefix} {key} must be false")


def validate_d145(d145, ledger, replay_index, d146_scope):
    errors = []

    if not d145:
        errors.append("missing D145 sandbox candidate final audit scope report")
        return errors

    if d145.get("ok") is not True:
        errors.append("D145 ok must be true")
    if d145.get("decision") != REQ_D145_DECISION:
        errors.append("D145 decision must be SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_READY")

    false_guard_ok(d145.get("guardrails", {}), "D145 guardrails", errors)

    summary = d145.get("summary", {})
    if summary.get("approval_scope") != REQ_D145_APPROVAL_SCOPE:
        errors.append("D145 approval_scope must be D146 archive scope only")
    if summary.get("next_step") != REQ_D146_GATE:
        errors.append("D145 next_step must be D146")

    if "final_audit_status" in summary and "FINAL_AUDIT" not in str(summary.get("final_audit_status")):
        errors.append("D145 final_audit_status must indicate final audit")
    if "replay_index_status" in summary and "INDEX" not in str(summary.get("replay_index_status")):
        errors.append("D145 replay_index_status must indicate index created")
    if "candidate_status" in summary and "NOT_CORE_APPLIED" not in str(summary.get("candidate_status")):
        errors.append("D145 candidate_status must remain not core applied")

    for key, expected in BLOCKED_SUMMARY.items():
        if key in summary and summary.get(key) != expected:
            errors.append(f"D145 summary.{key} must be {expected}")

    if not ledger:
        errors.append("missing D145 final audit ledger")
    else:
        if ledger.get("ok") is not True:
            errors.append("D145 final audit ledger ok must be true")
        false_guard_ok(ledger, "D145 final audit ledger", errors)
        if "ledger_status" in ledger and "CREATED" not in str(ledger.get("ledger_status")):
            errors.append("D145 final audit ledger_status must indicate created")

    if not replay_index:
        errors.append("missing D145 replay index")
    else:
        if replay_index.get("ok") is not True:
            errors.append("D145 replay index ok must be true")
        false_guard_ok(replay_index, "D145 replay index", errors)
        if "replay_executed" in replay_index and replay_index.get("replay_executed") is not False:
            errors.append("D145 replay index replay_executed must be false")

    if not d146_scope:
        errors.append("missing D145 D146 archive scope")
    else:
        if d146_scope.get("ok") is not True:
            errors.append("D145 D146 archive scope ok must be true")
        if d146_scope.get("allowed_next_gate") != REQ_D146_GATE:
            errors.append("D145 D146 scope allowed_next_gate must be D146")
        if d146_scope.get("sandbox_candidate_archive_scope_only") is not True:
            errors.append("D145 D146 scope must be archive-scope-only")
        if d146_scope.get("human_review_required") is not True:
            errors.append("D145 D146 scope must require human review")
        false_guard_ok(d146_scope, "D145 D146 scope", errors)
        for key in [
            "real_apply_allowed_after_d145_by_ai",
            "route_insert_allowed_after_d145_by_ai",
            "protected_core_mutation_allowed_after_d145_by_ai",
            "network_allowed_after_d145_by_ai",
            "secret_read_allowed_after_d145_by_ai",
            "shell_allowed_after_d145_by_ai",
            "git_action_allowed_after_d145_by_ai",
            "candidate_execution_allowed_after_d145_by_ai",
        ]:
            if key in d146_scope and d146_scope.get(key) is not False:
                errors.append(f"D145 D146 scope {key} must be false")

    return errors


def archive_item_status(root, item):
    p = root / item
    return {
        "path": item,
        "present": p.exists(),
        "size_bytes": p.stat().st_size if p.exists() else 0,
    }


def build_archive_manifest(root, archive_id, d145, ledger, replay_index):
    items = [archive_item_status(root, item) for item in ARCHIVE_ITEMS]
    return {
        "state": "D146_SANDBOX_CANDIDATE_ARCHIVE_MANIFEST",
        "ok": True,
        "archive_id": archive_id,
        "audit_id": d145.get("audit_id"),
        "verification_id": d145.get("verification_id"),
        "apply_id": d145.get("apply_id"),
        "run_id": d145.get("run_id"),
        "candidate_id": d145.get("candidate_id"),
        "proposal_id": d145.get("proposal_id"),
        "created_at": now(),
        "archive_mode": "SANDBOX_CANDIDATE_ARCHIVE_MANIFEST_ONLY_NO_CORE_APPLY",
        "archive_status": "ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
        "archive_items": items,
        "archive_items_total": len(items),
        "archive_items_present": sum(1 for i in items if i["present"]),
        "source_ledger_state": ledger.get("state"),
        "source_replay_index_state": replay_index.get("state"),
        "candidate_executed_again_now": False,
        "sandbox_apply_replayed_now": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_chain_closure_receipt(archive_id, d145):
    return {
        "state": "D146_SANDBOX_CANDIDATE_CHAIN_CLOSURE_RECEIPT",
        "ok": True,
        "archive_id": archive_id,
        "audit_id": d145.get("audit_id"),
        "verification_id": d145.get("verification_id"),
        "apply_id": d145.get("apply_id"),
        "run_id": d145.get("run_id"),
        "candidate_id": d145.get("candidate_id"),
        "created_at": now(),
        "closure_mode": "SANDBOX_CHAIN_CLOSURE_RECEIPT_ONLY_NO_PROMOTION",
        "closure_status": "SANDBOX_CHAIN_ARCHIVED_READY_FOR_PROMOTION_DECISION",
        "chain_summary": [
            "D139 sandbox execution completed",
            "D140 post execution verified",
            "D141 apply preflight created",
            "D142 human apply intent recorded",
            "D143 sandbox guarded apply evidence created",
            "D144 post apply verified",
            "D145 final audit ledger created",
            "D146 archive manifest created",
        ],
        "candidate_executed_again_now": False,
        "real_core_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_d147_scope(archive_id, d145):
    return {
        "state": "D146_D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE",
        "ok": True,
        "archive_id": archive_id,
        "audit_id": d145.get("audit_id"),
        "verification_id": d145.get("verification_id"),
        "apply_id": d145.get("apply_id"),
        "run_id": d145.get("run_id"),
        "candidate_id": d145.get("candidate_id"),
        "proposal_id": d145.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D147_GATE,
        "d147_allowed_to_create": [
            "sandbox_candidate_promotion_decision_scope",
            "sandbox_candidate_promotion_decision_record",
            "sandbox_candidate_core_apply_request_or_close_record",
            "d148_sandbox_candidate_core_apply_request_scope",
        ],
        "d147_must_not_execute": [
            "real_core_apply_by_ai",
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
            "candidate_execution_again_by_ai",
        ],
        "sandbox_candidate_promotion_decision_scope_only": True,
        "human_review_required": True,
        "candidate_executed_after_d146_by_ai": False,
        "real_apply_allowed_after_d146_by_ai": False,
        "route_insert_allowed_after_d146_by_ai": False,
        "protected_core_mutation_allowed_after_d146_by_ai": False,
        "network_allowed_after_d146_by_ai": False,
        "secret_read_allowed_after_d146_by_ai": False,
        "shell_allowed_after_d146_by_ai": False,
        "git_action_allowed_after_d146_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_ONLY",
    }


def create_sandbox_candidate_archive_scope(root="."):
    root = Path(root).resolve()

    d145 = read_json(root / D145_REPORT, {}) or {}
    ledger = read_json(root / D145_LEDGER, {}) or {}
    replay_index = read_json(root / D145_REPLAY_INDEX, {}) or {}
    d146_scope = read_json(root / D145_D146_SCOPE, {}) or {}

    errors = validate_d145(d145, ledger, replay_index, d146_scope)

    archive_id = "d146-" + digest({
        "audit_id": d145.get("audit_id"),
        "verification_id": d145.get("verification_id"),
        "apply_id": d145.get("apply_id"),
        "run_id": d145.get("run_id"),
        "candidate_id": d145.get("candidate_id"),
        "proposal_id": d145.get("proposal_id"),
    })

    archive_manifest = build_archive_manifest(root, archive_id, d145, ledger, replay_index)
    chain_closure = build_chain_closure_receipt(archive_id, d145)
    d147_scope = build_d147_scope(archive_id, d145)

    for item_name, item in [
        ("archive_manifest", archive_manifest),
        ("chain_closure", chain_closure),
        ("d147_scope", d147_scope),
    ]:
        false_guard_ok(item, item_name, errors)

    if archive_manifest.get("archive_items_present", 0) <= 0:
        errors.append("archive manifest must include present archive items")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_ARCHIVE_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_ARCHIVE_SCOPE_BLOCKED"
    result = "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_CREATED" if ok else "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_BLOCKED"

    if ok:
        write_json(root / ARCHIVE_MANIFEST_OUT, archive_manifest)
        write_json(root / CHAIN_CLOSURE_OUT, chain_closure)
        write_json(root / D147_SCOPE_OUT, d147_scope)

    report = {
        "state": "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_ARCHIVE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "archive_id": archive_id,
        "audit_id": d145.get("audit_id"),
        "verification_id": d145.get("verification_id"),
        "apply_id": d145.get("apply_id"),
        "run_id": d145.get("run_id"),
        "candidate_id": d145.get("candidate_id"),
        "proposal_id": d145.get("proposal_id"),
        "source_d145_report": D145_REPORT,
        "sandbox_candidate_archive_manifest": archive_manifest if ok else {},
        "sandbox_candidate_chain_closure_receipt": chain_closure if ok else {},
        "d147_scope": d147_scope if ok else {},
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
            "rollback_executed": False,
            "restore_executed": False,
            "sandbox_candidate_archive_scope_only": True,
            "archive_manifest_only": True,
            "chain_closure_receipt_only": True,
            "candidate_executed_again_now": False,
            "sandbox_apply_replayed_now": False,
            "approval_for_d147_promotion_decision_scope_only": ok,
            "approval_for_real_core_apply_by_ai": False,
            "approval_for_route_insert_by_ai": False,
            "approval_for_protected_core_mutation_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "archive_id": archive_id,
            "audit_id": d145.get("audit_id"),
            "verification_id": d145.get("verification_id"),
            "apply_id": d145.get("apply_id"),
            "run_id": d145.get("run_id"),
            "candidate_id": d145.get("candidate_id"),
            "proposal_id": d145.get("proposal_id"),
            "archive_status": "ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED" if ok else "BLOCKED",
            "chain_closure_status": "SANDBOX_CHAIN_ARCHIVED_READY_FOR_PROMOTION_DECISION" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_ARCHIVED_NOT_CORE_APPLIED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": REQ_D147_APPROVAL_SCOPE if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D147_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_archive_scope_created": ok,
            "sandbox_candidate_archive_manifest_created": ok,
            "sandbox_candidate_chain_closure_receipt_created": ok,
            "d147_scope_created": ok,
            "real_core_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "candidate_executed_again": False,
            "next_step": "D147 may create sandbox candidate promotion decision scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_archive_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_archive_scope import create_sandbox_candidate_archive_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD146SandboxCandidateArchiveScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        audit_id = "d145-test"
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
            "real_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
        }

        d145 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_READY",
            "audit_id": audit_id,
            "verification_id": verification_id,
            "apply_id": apply_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_final_audit_scope_only": True,
                "final_audit_ledger_only": True,
                "replay_index_only": True,
                "approval_for_d146_archive_scope_only": True,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "final_audit_status": "FINAL_AUDIT_LEDGER_CREATED",
                "replay_index_status": "INDEX_CREATED_NOT_REPLAYED",
                "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_FINAL_AUDIT_READY_NOT_CORE_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_ONLY",
                "next_step": "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE",
            },
        }

        ledger = dict(false_guard, **{
            "state": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_LEDGER",
            "ok": True,
            "audit_id": audit_id,
            "candidate_id": candidate_id,
            "ledger_status": "FINAL_AUDIT_LEDGER_CREATED",
        })

        replay_index = dict(false_guard, **{
            "state": "D145_SANDBOX_CANDIDATE_REPLAY_INDEX",
            "ok": True,
            "audit_id": audit_id,
            "candidate_id": candidate_id,
            "index_status": "INDEX_CREATED_NOT_REPLAYED",
            "replay_executed": False,
        })

        d146_scope = dict(false_guard, **{
            "state": "D145_D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE",
            "ok": True,
            "audit_id": audit_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE",
            "sandbox_candidate_archive_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d145_by_ai": False,
            "route_insert_allowed_after_d145_by_ai": False,
            "protected_core_mutation_allowed_after_d145_by_ai": False,
            "network_allowed_after_d145_by_ai": False,
            "secret_read_allowed_after_d145_by_ai": False,
            "shell_allowed_after_d145_by_ai": False,
            "git_action_allowed_after_d145_by_ai": False,
            "candidate_execution_allowed_after_d145_by_ai": False,
        })

        write(root / "reports/d145_sandbox_candidate_final_audit_scope.json", d145)
        write(root / "reports/d145_sandbox_candidate_final_audit_ledger.json", ledger)
        write(root / "reports/d145_sandbox_candidate_replay_index.json", replay_index)
        write(root / "reports/d145_d146_sandbox_candidate_archive_scope.json", d146_scope)
        write(root / "reports/d139_sandbox_candidate_controlled_execution_run_scope.json", {"ok": True})
        return td, root

    def test_creates_archive_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_archive_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_ARCHIVE_SCOPE_READY")
            self.assertEqual(r["summary"]["archive_status"], "ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED")
            self.assertEqual(r["summary"]["approval_scope"], "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_ONLY")
            self.assertEqual(r["d147_scope"]["allowed_next_gate"], "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted"])
            self.assertTrue((root / "reports/d146_sandbox_candidate_archive_scope.json").exists())
            self.assertTrue((root / "reports/d146_sandbox_candidate_archive_manifest.json").exists())
            self.assertTrue((root / "reports/d146_sandbox_candidate_chain_closure_receipt.json").exists())
            self.assertTrue((root / "reports/d146_d147_sandbox_candidate_promotion_decision_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d145(self):
        td, root = self.root()
        try:
            (root / "reports/d145_sandbox_candidate_final_audit_scope.json").unlink()
            r = create_sandbox_candidate_archive_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d145_real_apply_not_blocked(self):
        td, root = self.root()
        try:
            p = root / "reports/d145_sandbox_candidate_final_audit_scope.json"
            d = json.loads(p.read_text())
            d["summary"]["real_apply_by_ai_status"] = "ALLOWED"
            p.write_text(json.dumps(d), encoding="utf-8")
            r = create_sandbox_candidate_archive_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_ledger_says_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d145_sandbox_candidate_final_audit_ledger.json"
            d = json.loads(p.read_text())
            d["actual_apply_executed"] = True
            p.write_text(json.dumps(d), encoding="utf-8")
            r = create_sandbox_candidate_archive_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d146_scope_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d145_d146_sandbox_candidate_archive_scope.json"
            d = json.loads(p.read_text())
            d["route_insert_allowed_after_d145_by_ai"] = True
            p.write_text(json.dumps(d), encoding="utf-8")
            r = create_sandbox_candidate_archive_scope(root)
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

print("D146 SANDBOX CANDIDATE ARCHIVE SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_archive_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d146_sandbox_candidate_archive_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_archive_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d146_sandbox_candidate_archive_scope", "-v"], check=True)

print("\n== run D146 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_archive_scope import create_sandbox_candidate_archive_scope\n"
    "r=create_sandbox_candidate_archive_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d146_sandbox_candidate_archive_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_archive_scope.py",
    "tests/test_d146_sandbox_candidate_archive_scope.py",
    "reports/d146_sandbox_candidate_archive_scope.json",
    "reports/d146_sandbox_candidate_archive_manifest.json",
    "reports/d146_sandbox_candidate_chain_closure_receipt.json",
    "reports/d146_d147_sandbox_candidate_promotion_decision_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D146 sandbox candidate archive scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D146 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD146 SANDBOX CANDIDATE ARCHIVE SCOPE BOOT DONE")
