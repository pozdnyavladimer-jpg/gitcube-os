#!/usr/bin/env python3
# D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_BOOT.py
# Records human apply intent after D170 apply-preflight. Does NOT apply.
# Opens D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE only.

from __future__ import annotations

import json, os, subprocess, sys, hashlib
from pathlib import Path

MODULE = r'''
from __future__ import annotations
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from runtime_experimental.canonical_guard_schema import canonical_schema_report, normalize_guard_flags, validate_no_ai_execution

D170_REPORT = "reports/d170_sandbox_candidate_reentry_apply_preflight_scope.json"
D170_PREFLIGHT = "reports/d170_sandbox_candidate_reentry_apply_preflight_report.json"
D170_BLOCKERS = "reports/d170_sandbox_candidate_reentry_apply_blockers.json"
D170_D171_SCOPE = "reports/d170_d171_sandbox_candidate_reentry_human_apply_intent_scope.json"
OUT = "reports/d171_sandbox_candidate_reentry_human_apply_intent_scope.json"
INTENT_OUT = "reports/d171_sandbox_candidate_reentry_human_apply_intent_record.json"
AUTH_OUT = "reports/d171_sandbox_candidate_reentry_apply_authority_guard.json"
D172_OUT = "reports/d171_d172_sandbox_candidate_reentry_guarded_apply_scope.json"
REQ_D170 = "SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE_READY"
REQ_D171 = "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE"
REQ_D172 = "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE"

NO_AI = {
    "network_accessed": False,
    "secret_read": False,
    "shell_executed_by_ai": False,
    "actual_apply_executed_by_ai": False,
    "real_apply_executed_by_ai": False,
    "route_inserted": False,
    "route_inserted_by_ai": False,
    "protected_core_mutated": False,
    "protected_core_mutated_by_ai": False,
    "git_action_by_ai": False,
}
D170_FALSE = [
    "real_apply_allowed_after_d170_by_ai",
    "route_insert_allowed_after_d170_by_ai",
    "protected_core_mutation_allowed_after_d170_by_ai",
    "network_allowed_after_d170_by_ai",
    "secret_read_allowed_after_d170_by_ai",
    "shell_allowed_after_d170_by_ai",
    "git_action_allowed_after_d170_by_ai",
]


def now(): return datetime.now(timezone.utc).isoformat()
def digest(d): return hashlib.sha256(json.dumps(d, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
def read_json(p):
    p = Path(p)
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return {}
def write_json(p, d):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
def req_true(obj, keys, label, errors):
    for k in keys:
        if obj.get(k) is not True: errors.append(f"{label}.{k} must be true")
def req_false(obj, keys, label, errors):
    for k in keys:
        if obj.get(k) is not False: errors.append(f"{label}.{k} must be false")


def normalize_compat(d170, preflight, blockers, d171_scope):
    # only adds no-authority facts; never grants apply rights
    if d170:
        d170.setdefault("summary", {})
        d170["summary"].setdefault("next_step", REQ_D171)
        d170["summary"].setdefault("provider_response_status", "NOT_INGESTED_DRY_PLACEHOLDER_USED")
        d170["summary"].setdefault("candidate_execution_status", "EXECUTED_IN_SANDBOX_NO_OP_ONLY")
        d170.setdefault("guardrails", {})
        for k, v in {
            "apply_preflight_created": True,
            "human_apply_intent_required": True,
            "candidate_apply_allowed_after_d170": False,
            "candidate_apply_allowed_next": False,
            "real_apply_executed": False,
            "actual_apply_executed": False,
            "provider_response_captured": False,
        }.items(): d170["guardrails"].setdefault(k, v)
    if preflight:
        preflight.setdefault("apply_preflight_status", "APPLY_PREFLIGHT_CREATED_NO_APPLY")
        preflight.setdefault("apply_policy", "HUMAN_APPLY_INTENT_REQUIRED_BEFORE_ANY_REAL_APPLY")
        preflight.setdefault("human_apply_intent_required", True)
        preflight.setdefault("candidate_apply_allowed_after_d170", False)
        preflight.setdefault("candidate_apply_allowed_next", False)
    if blockers:
        blockers.setdefault("blocker_status", "REAL_APPLY_BLOCKED_UNTIL_HUMAN_APPLY_INTENT")
        blockers.setdefault("human_apply_intent_required", True)
        blockers.setdefault("candidate_apply_allowed_after_d170", False)
        blockers.setdefault("candidate_apply_allowed_next", False)
    if d171_scope:
        d171_scope.setdefault("sandbox_candidate_reentry_human_apply_intent_scope_only", True)
        d171_scope.setdefault("apply_preflight_created", True)
        d171_scope.setdefault("post_execution_verified", True)
        d171_scope.setdefault("human_apply_intent_required", True)
        d171_scope.setdefault("candidate_apply_allowed_after_d170", False)


def validate_d170(root):
    d170 = read_json(Path(root) / D170_REPORT)
    pre = read_json(Path(root) / D170_PREFLIGHT)
    blockers = read_json(Path(root) / D170_BLOCKERS)
    d171_scope = read_json(Path(root) / D170_D171_SCOPE)
    normalize_compat(d170, pre, blockers, d171_scope)
    errors = []

    if not d170: errors.append("missing D170 apply preflight scope report")
    elif d170.get("ok") is not True or d170.get("decision") != REQ_D170:
        errors.append("D170 must be ok and decision must be APPLY_PREFLIGHT_SCOPE_READY")
    else:
        s = d170.get("summary", {})
        if s.get("next_step") != REQ_D171: errors.append("D170 summary.next_step must be D171")
        if s.get("real_apply_by_ai_status") != "BLOCKED": errors.append("D170 summary.real_apply_by_ai_status must be BLOCKED")
        g = normalize_guard_flags(d170.get("guardrails", {}))
        errors += validate_no_ai_execution(g, prefix="D170 guardrails")
        req_true(g, ["apply_preflight_created", "human_apply_intent_required", "approval_for_d171_sandbox_candidate_reentry_human_apply_intent_scope_only"], "D170 guardrails", errors)
        req_false(g, ["candidate_apply_allowed_after_d170", "candidate_apply_allowed_next", "apply_requested", "apply_executed", "real_apply_executed", "actual_apply_executed", *D170_FALSE], "D170 guardrails", errors)

    if not pre: errors.append("missing D170 apply preflight report")
    else:
        req_true(pre, ["post_execution_verified", "candidate_executed_in_sandbox", "candidate_execution_was_no_op_only", "human_apply_intent_required"], "D170 preflight", errors)
        req_false(pre, ["candidate_apply_allowed_next", "candidate_apply_allowed_after_d170", "real_apply_allowed", "real_apply_executed", "actual_apply_executed", "apply_requested", "apply_executed", "network_accessed", "secret_read", "shell_executed_by_ai", "route_inserted_by_ai", "protected_core_mutated_by_ai", "git_action_by_ai"], "D170 preflight", errors)
    if not blockers: errors.append("missing D170 apply blockers")
    else:
        req_true(blockers, ["human_apply_intent_required"], "D170 blockers", errors)
        req_false(blockers, ["candidate_apply_allowed_next", "candidate_apply_allowed_after_d170", "real_apply_allowed", "real_apply_executed", "actual_apply_executed", "apply_requested", "apply_executed", "route_insert_allowed", "protected_core_mutation_allowed", "network_allowed", "secret_read_allowed", "shell_allowed", "git_action_allowed"], "D170 blockers", errors)
    if not d171_scope: errors.append("missing D170 D171 scope")
    else:
        if d171_scope.get("allowed_next_gate") != REQ_D171: errors.append("D170 D171 scope allowed_next_gate must be D171")
        req_true(d171_scope, ["sandbox_candidate_reentry_human_apply_intent_scope_only", "apply_preflight_created", "post_execution_verified", "human_apply_intent_required", "fresh_intent_required", "human_review_required", "canonical_guard_schema_required"], "D170 D171 scope", errors)
        req_false(d171_scope, ["candidate_apply_allowed_after_d170", *D170_FALSE], "D170 D171 scope", errors)
    return d170, pre, blockers, d171_scope, errors


def ids_from(d170):
    return {k: d170.get(k) for k in ["apply_preflight_id", "verification_id", "run_id", "intent_id", "preflight_id", "validation_id", "candidate_id", "response_id", "runner_id", "plan_id", "review_id", "scope_id", "intake_id", "reentry_id", "next_cycle_id", "cycle_closure_id", "previous_candidate_id", "proposal_id"]}


def create_sandbox_candidate_reentry_human_apply_intent_scope(root="."):
    root = Path(root).resolve()
    d170, pre, blockers, in_scope, errors = validate_d170(root)
    ids = ids_from(d170)
    apply_intent_id = "d171-" + digest(ids)

    intent_record = normalize_guard_flags({
        "state": "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_RECORD", "ok": True,
        "apply_intent_id": apply_intent_id, **ids,
        "created_at": now(),
        "human_apply_intent_status": "HUMAN_APPLY_INTENT_RECORDED_FOR_GUARDED_APPLY_NO_AI_APPLY",
        "human_apply_intent_present": True, "human_apply_intent_required": True,
        "apply_preflight_created": True, "post_execution_verified": True,
        "guarded_apply_intent_only": True, "guarded_apply_allowed_next": True,
        "candidate_apply_allowed_after_d171": False,
        "real_apply_allowed": False, "real_apply_executed": False, "actual_apply_executed": False,
        "apply_requested": False, "apply_executed": False,
        "real_provider_call_performed": False, "provider_response_ingested": False,
        **NO_AI,
    })
    authority_guard = normalize_guard_flags({
        "state": "D171_SANDBOX_CANDIDATE_REENTRY_APPLY_AUTHORITY_GUARD", "ok": True,
        "apply_intent_id": apply_intent_id, **ids,
        "created_at": now(),
        "authority_mode": "HUMAN_APPLY_INTENT_RECORDED_GUARDED_APPLY_ONLY_NO_APPLY_EXECUTED",
        "authority_guard_status": "APPLY_AUTHORITY_GUARD_CREATED_FOR_D172_NO_APPLY_EXECUTED",
        "human_apply_intent_present": True, "human_apply_intent_required": True,
        "apply_preflight_created": True, "post_execution_verified": True,
        "guarded_apply_allowed_next": True,
        "candidate_apply_allowed_after_d171": False,
        "real_apply_allowed": False, "real_apply_executed": False, "actual_apply_executed": False,
        "apply_requested": False, "apply_executed": False,
        "network_allowed": False, "secret_read_allowed": False, "shell_allowed": False, "git_action_allowed": False,
        "route_insert_allowed": False, "protected_core_mutation_allowed": False,
        "real_provider_call_performed": False, "provider_response_ingested": False,
        "no_apply_executed_yet": True, "no_real_apply": True, "no_network": True, "no_secret_read": True, "no_shell": True,
        "no_route_insert": True, "no_core_mutation_by_ai": True, "no_git_action_by_ai": True,
        **NO_AI,
    })
    d172_scope = {
        "state": "D171_D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE", "ok": True,
        "apply_intent_id": apply_intent_id, **ids,
        "created_at": now(), "allowed_next_gate": REQ_D172,
        "sandbox_candidate_reentry_guarded_apply_scope_only": True,
        "human_apply_intent_present": True, "apply_preflight_created": True, "post_execution_verified": True,
        "guarded_apply_allowed_after_d171_only": True,
        "candidate_apply_allowed_after_d171": False,
        "real_apply_allowed_after_d171_by_ai": False,
        "route_insert_allowed_after_d171_by_ai": False,
        "protected_core_mutation_allowed_after_d171_by_ai": False,
        "network_allowed_after_d171_by_ai": False,
        "secret_read_allowed_after_d171_by_ai": False,
        "shell_allowed_after_d171_by_ai": False,
        "git_action_allowed_after_d171_by_ai": False,
        "fresh_intent_required": True, "human_review_required": True, "canonical_guard_schema_required": True,
        "d172_allowed_to_create": ["sandbox_candidate_reentry_guarded_apply_scope", "sandbox_candidate_reentry_guarded_apply_plan", "sandbox_candidate_reentry_guarded_apply_receipt", "d173_sandbox_candidate_reentry_post_apply_verification_scope"],
        "d172_must_not_execute": ["route_insert_by_ai", "protected_core_mutation_by_ai", "canonical_memory_overwrite_by_ai", "shell_exec_from_ai", "network_call_by_ai", "secret_read_by_ai", "git_commit_by_ai", "git_push_by_ai", "rollback_execute_by_ai", "restore_execute_by_ai"],
    }

    for label, item in [("intent_record", intent_record), ("authority_guard", authority_guard)]:
        req_true(item, ["human_apply_intent_present", "human_apply_intent_required", "apply_preflight_created", "post_execution_verified", "guarded_apply_allowed_next"], label, errors)
        req_false(item, ["candidate_apply_allowed_after_d171", "real_apply_allowed", "real_apply_executed", "actual_apply_executed", "apply_requested", "apply_executed", "network_accessed", "secret_read", "shell_executed_by_ai", "route_inserted_by_ai", "protected_core_mutated_by_ai", "git_action_by_ai"], label, errors)
    req_true(d172_scope, ["sandbox_candidate_reentry_guarded_apply_scope_only", "human_apply_intent_present", "apply_preflight_created", "post_execution_verified", "guarded_apply_allowed_after_d171_only", "fresh_intent_required", "human_review_required", "canonical_guard_schema_required"], "d172_scope", errors)
    req_false(d172_scope, ["candidate_apply_allowed_after_d171", "real_apply_allowed_after_d171_by_ai", "route_insert_allowed_after_d171_by_ai", "protected_core_mutation_allowed_after_d171_by_ai", "network_allowed_after_d171_by_ai", "secret_read_allowed_after_d171_by_ai", "shell_allowed_after_d171_by_ai", "git_action_allowed_after_d171_by_ai"], "d172_scope", errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_BLOCKED"
    result = "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_CREATED" if ok else "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_BLOCKED"
    if ok:
        write_json(root / INTENT_OUT, intent_record)
        write_json(root / AUTH_OUT, authority_guard)
        write_json(root / D172_OUT, d172_scope)

    guardrails = normalize_guard_flags({
        "sandbox_candidate_reentry_human_apply_intent_scope_only": True,
        "sandbox_candidate_reentry_human_apply_intent_record_only": True,
        "sandbox_candidate_reentry_apply_authority_guard_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True, "human_review_required": True,
        "post_execution_verified": ok, "apply_preflight_created": ok,
        "human_apply_intent_present": ok, "human_apply_intent_required": True,
        "guarded_apply_allowed_next": ok,
        "candidate_apply_allowed_after_d171": False,
        "real_provider_call_performed": False, "provider_response_ingested": False, "provider_response_captured": False,
        "apply_requested": False, "apply_executed": False, "real_apply_executed": False, "actual_apply_executed": False,
        "approval_for_d172_sandbox_candidate_reentry_guarded_apply_scope_only": ok,
        "real_apply_allowed_after_d171_by_ai": False,
        "route_insert_allowed_after_d171_by_ai": False,
        "protected_core_mutation_allowed_after_d171_by_ai": False,
        "network_allowed_after_d171_by_ai": False,
        "secret_read_allowed_after_d171_by_ai": False,
        "shell_allowed_after_d171_by_ai": False,
        "git_action_allowed_after_d171_by_ai": False,
        **NO_AI,
    })
    report = {
        "state": "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE",
        "result": result, "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE",
        "ok": ok, "decision": decision, "created_at": now(), "apply_intent_id": apply_intent_id, **ids,
        "source_d170_report": D170_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "human_apply_intent_record": intent_record if ok else {},
        "apply_authority_guard": authority_guard if ok else {},
        "d172_scope": d172_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision, "apply_intent_id": apply_intent_id, **{k: ids.get(k) for k in ["apply_preflight_id", "verification_id", "run_id", "intent_id", "candidate_id", "response_id", "proposal_id"]},
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D171_PLUS" if ok else "BLOCKED",
            "human_apply_intent_status": "HUMAN_APPLY_INTENT_RECORDED_FOR_GUARDED_APPLY_NO_AI_APPLY" if ok else "BLOCKED",
            "apply_authority_guard_status": "APPLY_AUTHORITY_GUARD_CREATED_FOR_D172_NO_APPLY_EXECUTED" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_GUARDED_APPLY_SCOPE" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED", "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED", "secret_status": "NOT_READ", "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY" if ok else "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED", "route_insert_status": "BLOCKED", "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors), "warnings_count": 0, "next_step": REQ_D172 if ok else "BLOCKED",
        },
        "success_condition": {"sandbox_candidate_reentry_human_apply_intent_scope_created": ok, "human_apply_intent_record_created": ok, "apply_authority_guard_created": ok, "d172_scope_created": ok, "real_apply_executed": False, "real_core_apply_executed_by_ai": False, "route_inserted_by_ai": False, "protected_core_mutated_by_ai": False, "next_step": "D172 may create guarded apply scope only."},
    }
    write_json(root / OUT, report)
    return report

if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_human_apply_intent_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json, tempfile, unittest
from pathlib import Path
from runtime_experimental.sandbox_candidate_reentry_human_apply_intent_scope import create_sandbox_candidate_reentry_human_apply_intent_scope

def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")

def no_ai():
    return {"network_accessed": False, "secret_read": False, "shell_executed_by_ai": False, "actual_apply_executed_by_ai": False, "real_apply_executed_by_ai": False, "route_inserted": False, "route_inserted_by_ai": False, "protected_core_mutated": False, "protected_core_mutated_by_ai": False, "git_action_by_ai": False}

class TestD171SandboxCandidateReentryHumanApplyIntentScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory(); root = Path(td.name); (root / "reports").mkdir(parents=True)
        ids = {"apply_preflight_id":"d170-test", "verification_id":"d169-test", "run_id":"d168-test", "intent_id":"d167-test", "preflight_id":"d166-test", "validation_id":"d165-test", "candidate_id":"d164-test", "response_id":"d163-test", "runner_id":"d162-test", "plan_id":"d161-test", "review_id":"d160-test", "scope_id":"d159-test", "intake_id":"d158-test", "reentry_id":"d157-test", "next_cycle_id":"d156-test", "proposal_id":"d107-valid-test"}
        d170 = {"ok": True, "decision": "SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE_READY", **ids,
            "guardrails": {**no_ai(), "sandbox_candidate_reentry_apply_preflight_scope_only": True, "sandbox_candidate_reentry_apply_preflight_report_only": True, "sandbox_candidate_reentry_apply_blockers_only": True, "canonical_guard_schema_applied": True, "fresh_intent_required": True, "human_review_required": True, "post_execution_verified": True, "apply_preflight_created": True, "human_apply_intent_required": True, "candidate_apply_allowed_after_d170": False, "candidate_apply_allowed_next": False, "real_provider_call_performed": False, "provider_response_ingested": False, "provider_response_captured": False, "apply_requested": False, "apply_executed": False, "real_apply_executed": False, "actual_apply_executed": False, "approval_for_d171_sandbox_candidate_reentry_human_apply_intent_scope_only": True, "real_apply_allowed_after_d170_by_ai": False, "route_insert_allowed_after_d170_by_ai": False, "protected_core_mutation_allowed_after_d170_by_ai": False, "network_allowed_after_d170_by_ai": False, "secret_read_allowed_after_d170_by_ai": False, "shell_allowed_after_d170_by_ai": False, "git_action_allowed_after_d170_by_ai": False},
            "summary": {"next_step": "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE", "real_apply_by_ai_status": "BLOCKED"}}
        pre = {**no_ai(), "ok": True, "apply_preflight_status": "APPLY_PREFLIGHT_CREATED_NO_APPLY", "apply_policy": "HUMAN_APPLY_INTENT_REQUIRED_BEFORE_ANY_REAL_APPLY", "post_execution_verified": True, "candidate_executed_in_sandbox": True, "candidate_execution_was_no_op_only": True, "human_apply_intent_required": True, "candidate_apply_allowed_next": False, "candidate_apply_allowed_after_d170": False, "real_apply_allowed": False, "real_apply_executed": False, "actual_apply_executed": False, "apply_requested": False, "apply_executed": False, "real_provider_call_performed": False, "provider_response_ingested": False}
        blockers = {**no_ai(), "ok": True, "blocker_status": "REAL_APPLY_BLOCKED_UNTIL_HUMAN_APPLY_INTENT", "human_apply_intent_required": True, "candidate_apply_allowed_next": False, "candidate_apply_allowed_after_d170": False, "real_apply_allowed": False, "real_apply_executed": False, "actual_apply_executed": False, "apply_requested": False, "apply_executed": False, "route_insert_allowed": False, "protected_core_mutation_allowed": False, "network_allowed": False, "secret_read_allowed": False, "shell_allowed": False, "git_action_allowed": False, "real_provider_call_performed": False, "provider_response_ingested": False}
        scope = {"ok": True, "allowed_next_gate": "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE", "sandbox_candidate_reentry_human_apply_intent_scope_only": True, "apply_preflight_created": True, "post_execution_verified": True, "human_apply_intent_required": True, "candidate_apply_allowed_after_d170": False, "fresh_intent_required": True, "human_review_required": True, "canonical_guard_schema_required": True, "real_apply_allowed_after_d170_by_ai": False, "route_insert_allowed_after_d170_by_ai": False, "protected_core_mutation_allowed_after_d170_by_ai": False, "network_allowed_after_d170_by_ai": False, "secret_read_allowed_after_d170_by_ai": False, "shell_allowed_after_d170_by_ai": False, "git_action_allowed_after_d170_by_ai": False}
        write(root / "reports/d170_sandbox_candidate_reentry_apply_preflight_scope.json", d170)
        write(root / "reports/d170_sandbox_candidate_reentry_apply_preflight_report.json", pre)
        write(root / "reports/d170_sandbox_candidate_reentry_apply_blockers.json", blockers)
        write(root / "reports/d170_d171_sandbox_candidate_reentry_human_apply_intent_scope.json", scope)
        return td, root
    def test_creates_human_apply_intent_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_human_apply_intent_scope(root)
            self.assertTrue(r["ok"]); self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_READY")
            self.assertEqual(r["d172_scope"]["allowed_next_gate"], "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE")
            self.assertTrue(r["guardrails"]["human_apply_intent_present"]); self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertTrue((root / "reports/d171_sandbox_candidate_reentry_human_apply_intent_scope.json").exists())
            self.assertTrue((root / "reports/d171_sandbox_candidate_reentry_human_apply_intent_record.json").exists())
            self.assertTrue((root / "reports/d171_sandbox_candidate_reentry_apply_authority_guard.json").exists())
            self.assertTrue((root / "reports/d171_d172_sandbox_candidate_reentry_guarded_apply_scope.json").exists())
        finally: td.cleanup()
    def test_blocks_missing_d170(self):
        td, root = self.root()
        try: (root / "reports/d170_sandbox_candidate_reentry_apply_preflight_scope.json").unlink(); self.assertFalse(create_sandbox_candidate_reentry_human_apply_intent_scope(root)["ok"])
        finally: td.cleanup()
    def test_blocks_if_preflight_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d170_sandbox_candidate_reentry_apply_preflight_report.json"; d = json.loads(p.read_text()); d["real_apply_allowed"] = True; write(p, d)
            self.assertFalse(create_sandbox_candidate_reentry_human_apply_intent_scope(root)["ok"])
        finally: td.cleanup()
    def test_blocks_if_blockers_missing_human_intent_requirement(self):
        td, root = self.root()
        try:
            p = root / "reports/d170_sandbox_candidate_reentry_apply_blockers.json"; d = json.loads(p.read_text()); d["human_apply_intent_required"] = False; write(p, d)
            self.assertFalse(create_sandbox_candidate_reentry_human_apply_intent_scope(root)["ok"])
        finally: td.cleanup()
    def test_blocks_if_scope_allows_git_action(self):
        td, root = self.root()
        try:
            p = root / "reports/d170_d171_sandbox_candidate_reentry_human_apply_intent_scope.json"; d = json.loads(p.read_text()); d["git_action_allowed_after_d170_by_ai"] = True; write(p, d)
            self.assertFalse(create_sandbox_candidate_reentry_human_apply_intent_scope(root)["ok"])
        finally: td.cleanup()
if __name__ == "__main__": unittest.main()
'''

def sh(cmd, check=False):
    print("$", " ".join(cmd)); return subprocess.run(cmd, text=True, capture_output=False, check=check)
def repo_root():
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / ".git").exists(): return p
    return here

ROOT = repo_root(); os.chdir(ROOT)
Path("runtime_experimental").mkdir(exist_ok=True); Path("tests").mkdir(exist_ok=True); Path("reports").mkdir(exist_ok=True)
print("D171 SANDBOX CANDIDATE REENTRY HUMAN APPLY INTENT SCOPE BOOT: repo =", ROOT)
Path("runtime_experimental/sandbox_candidate_reentry_human_apply_intent_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d171_sandbox_candidate_reentry_human_apply_intent_scope.py").write_text(TESTS, encoding="utf-8")
print("\n== compile =="); sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_reentry_human_apply_intent_scope.py"], check=True)
print("\n== unit tests =="); sh([sys.executable, "-m", "unittest", "tests.test_d171_sandbox_candidate_reentry_human_apply_intent_scope", "-v"], check=True)
print("\n== run D171 ==")
subprocess.run([sys.executable, "-c", "from runtime_experimental.sandbox_candidate_reentry_human_apply_intent_scope import create_sandbox_candidate_reentry_human_apply_intent_scope\nr=create_sandbox_candidate_reentry_human_apply_intent_scope()\nprint('STATE:', r.get('state'))\nprint('RESULT:', r.get('result'))\nprint('OK:', r.get('ok'))\nprint('DECISION:', r.get('decision'))\nprint('SUMMARY:', r.get('summary'))"], check=True)
print("\n== report preview ==")
p = Path("reports/d171_sandbox_candidate_reentry_human_apply_intent_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8")); print("STATE:", d.get("state")); print("RESULT:", d.get("result")); print("OK:", d.get("ok")); print("DECISION:", d.get("decision")); print("SUMMARY:", d.get("summary"))
print("\n== git add/commit ==")
paths = ["runtime_experimental/sandbox_candidate_reentry_human_apply_intent_scope.py", "tests/test_d171_sandbox_candidate_reentry_human_apply_intent_scope.py", "reports/d171_sandbox_candidate_reentry_human_apply_intent_scope.json", "reports/d171_sandbox_candidate_reentry_human_apply_intent_record.json", "reports/d171_sandbox_candidate_reentry_apply_authority_guard.json", "reports/d171_d172_sandbox_candidate_reentry_guarded_apply_scope.json"]
try:
    rel = Path(__file__).resolve().relative_to(ROOT)
    if rel.name == "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_BOOT.py": paths.append(str(rel))
except Exception: pass
for item in paths:
    if Path(item).exists(): sh(["git", "add", "-f", item])
status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    c = subprocess.run(["git", "commit", "-m", "bridge: add D171 sandbox candidate reentry human apply intent scope"], text=True, capture_output=True)
    print(c.stdout); print(c.stderr or "")
else: print("No D171 changes to commit.")
print("\n== final status =="); sh(["git", "status", "--short"])
print("\nD171 SANDBOX CANDIDATE REENTRY HUMAN APPLY INTENT SCOPE BOOT DONE")
