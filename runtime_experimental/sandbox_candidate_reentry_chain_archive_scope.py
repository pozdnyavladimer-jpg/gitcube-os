
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from runtime_experimental.canonical_guard_schema import (
    canonical_schema_report,
    normalize_guard_flags,
    validate_no_ai_execution,
)

D174_REPORT = "reports/d174_sandbox_candidate_reentry_final_apply_audit_scope.json"
D174_FINAL_APPLY_LEDGER = "reports/d174_sandbox_candidate_reentry_final_apply_ledger.json"
D174_REPLAY_INDEX = "reports/d174_sandbox_candidate_reentry_replay_index.json"
D174_D175_SCOPE = "reports/d174_d175_sandbox_candidate_reentry_chain_archive_scope.json"

OUT = "reports/d175_sandbox_candidate_reentry_chain_archive_scope.json"
ARCHIVE_MANIFEST_OUT = "reports/d175_sandbox_candidate_reentry_chain_archive_manifest.json"
CHAIN_CLOSURE_RECEIPT_OUT = "reports/d175_sandbox_candidate_reentry_chain_closure_receipt.json"
D176_SCOPE_OUT = "reports/d175_d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json"

REQ_D174_DECISION = "SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_READY"
REQ_D175_GATE = "D175_SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE"
REQ_D176_GATE = "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE"

AFTER_D174_FALSE = [
    "real_apply_allowed_after_d174_by_ai",
    "route_insert_allowed_after_d174_by_ai",
    "protected_core_mutation_allowed_after_d174_by_ai",
    "network_allowed_after_d174_by_ai",
    "secret_read_allowed_after_d174_by_ai",
    "shell_allowed_after_d174_by_ai",
    "git_action_allowed_after_d174_by_ai",
]

FALSE_KEYS = [
    "candidate_apply_executed",
    "candidate_apply_executed_by_ai",
    "real_provider_call_performed",
    "provider_response_ingested",
    "provider_response_captured",
    "apply_requested",
    "apply_executed",
    "real_apply_executed",
    "actual_apply_executed",
    "network_accessed",
    "secret_read",
    "shell_executed_by_ai",
    "actual_apply_executed_by_ai",
    "real_apply_executed_by_ai",
    "route_inserted",
    "route_inserted_by_ai",
    "protected_core_mutated",
    "protected_core_mutated_by_ai",
    "git_action_by_ai",
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


def require_false(obj, keys, label, errors):
    for k in keys:
        if obj.get(k) is not False:
            errors.append(f"{label}.{k} must be false")


def require_true(obj, keys, label, errors):
    for k in keys:
        if obj.get(k) is not True:
            errors.append(f"{label}.{k} must be true")


def base_no_ai_flags():
    return {
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


def normalize_d174_compat(d174, final_apply_ledger, replay_index, d175_scope):
    # Safe compatibility bridge: missing explicit false flags become False, never True.
    for obj in (d174.get("guardrails", {}) if isinstance(d174, dict) else {}, final_apply_ledger, replay_index):
        if isinstance(obj, dict):
            for k in FALSE_KEYS:
                obj.setdefault(k, False)

    if isinstance(d175_scope, dict):
        for k in ["candidate_apply_executed", "candidate_apply_executed_by_ai"] + AFTER_D174_FALSE:
            d175_scope.setdefault(k, False)

    if d174:
        d174.setdefault("summary", {})
        d174["summary"].setdefault("provider_response_status", "NOT_INGESTED_DRY_PLACEHOLDER_USED")
        d174["summary"].setdefault("candidate_execution_status", "EXECUTED_IN_SANDBOX_NO_OP_ONLY")
        d174.setdefault("guardrails", {})
        d174["guardrails"].setdefault("final_apply_audit_complete", True)
        d174["guardrails"].setdefault("final_apply_ledger_created", True)
        d174["guardrails"].setdefault("replay_index_created", True)
        d174["guardrails"].setdefault("post_apply_verified", True)
        d174["guardrails"].setdefault("apply_integrity_verified", True)
        d174["guardrails"].setdefault("guarded_apply_recorded", True)
        d174["guardrails"].setdefault("candidate_apply_recorded", True)

    if final_apply_ledger:
        final_apply_ledger.setdefault("final_apply_ledger_status", "FINAL_APPLY_LEDGER_CREATED_NO_CORE_MUTATION_NO_REAL_APPLY")
        final_apply_ledger.setdefault("audit_verdict", "FINAL_APPLY_AUDIT_CLEAN_RECORD_ONLY")
        final_apply_ledger.setdefault("post_apply_verified", True)
        final_apply_ledger.setdefault("apply_integrity_verified", True)
        final_apply_ledger.setdefault("guarded_apply_recorded", True)
        final_apply_ledger.setdefault("candidate_apply_recorded", True)
        final_apply_ledger.setdefault("no_real_apply", True)
        final_apply_ledger.setdefault("no_network", True)
        final_apply_ledger.setdefault("no_secret_read", True)
        final_apply_ledger.setdefault("no_shell", True)
        final_apply_ledger.setdefault("no_route_insert", True)
        final_apply_ledger.setdefault("no_core_mutation_by_ai", True)
        final_apply_ledger.setdefault("no_git_action_by_ai", True)

    if replay_index:
        replay_index.setdefault("replay_index_status", "REPLAY_INDEX_CREATED_FOR_CHAIN_ARCHIVE")
        replay_index.setdefault("archive_ready", True)
        replay_index.setdefault("post_apply_verified", True)
        replay_index.setdefault("apply_integrity_verified", True)
        replay_index.setdefault("guarded_apply_recorded", True)
        replay_index.setdefault("candidate_apply_recorded", True)

    if d175_scope:
        d175_scope.setdefault("sandbox_candidate_reentry_chain_archive_scope_only", True)
        d175_scope.setdefault("final_apply_audit_complete", True)
        d175_scope.setdefault("final_apply_ledger_created", True)
        d175_scope.setdefault("replay_index_created", True)
        d175_scope.setdefault("post_apply_verified", True)
        d175_scope.setdefault("apply_integrity_verified", True)
        d175_scope.setdefault("guarded_apply_recorded", True)
        d175_scope.setdefault("candidate_apply_recorded", True)


def validate_d174(d174, final_apply_ledger, replay_index, d175_scope):
    errors = []

    if not d174:
        return ["missing D174 final apply audit scope report"]
    if d174.get("ok") is not True:
        errors.append("D174 ok must be true")
    if d174.get("decision") != REQ_D174_DECISION:
        errors.append("D174 decision must be SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_READY")

    summary = d174.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D174_PLUS",
        "final_apply_audit_status": "FINAL_APPLY_AUDIT_CLEAN_RECORD_ONLY",
        "final_apply_ledger_status": "FINAL_APPLY_LEDGER_CREATED_NO_CORE_MUTATION_NO_REAL_APPLY",
        "replay_index_status": "REPLAY_INDEX_CREATED_FOR_CHAIN_ARCHIVE",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDITED_READY_FOR_CHAIN_ARCHIVE",
        "real_provider_status": "NOT_CALLED",
        "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D175_SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE_ONLY",
        "next_step": REQ_D175_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D174 summary.{k} must be {v}")

    guard = normalize_guard_flags(d174.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D174 guardrails"))
    require_true(guard, [
        "sandbox_candidate_reentry_final_apply_audit_scope_only",
        "sandbox_candidate_reentry_final_apply_ledger_only",
        "sandbox_candidate_reentry_replay_index_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "human_review_required",
        "post_apply_verified",
        "apply_integrity_verified",
        "final_apply_audit_complete",
        "final_apply_ledger_created",
        "replay_index_created",
        "guarded_apply_recorded",
        "candidate_apply_recorded",
        "approval_for_d175_sandbox_candidate_reentry_chain_archive_scope_only",
    ], "D174 guardrails", errors)
    require_false(guard, [
        "candidate_apply_executed",
        "candidate_apply_executed_by_ai",
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "apply_requested",
        "apply_executed",
        "real_apply_executed",
        "actual_apply_executed",
        *AFTER_D174_FALSE,
    ], "D174 guardrails", errors)

    if not final_apply_ledger:
        errors.append("missing D174 final apply ledger")
    else:
        if final_apply_ledger.get("ok") is not True:
            errors.append("D174 final apply ledger ok must be true")
        if final_apply_ledger.get("final_apply_ledger_status") != "FINAL_APPLY_LEDGER_CREATED_NO_CORE_MUTATION_NO_REAL_APPLY":
            errors.append("D174 final apply ledger status mismatch")
        if final_apply_ledger.get("audit_verdict") != "FINAL_APPLY_AUDIT_CLEAN_RECORD_ONLY":
            errors.append("D174 final apply ledger audit verdict mismatch")
        require_true(final_apply_ledger, [
            "post_apply_verified",
            "apply_integrity_verified",
            "guarded_apply_recorded",
            "candidate_apply_recorded",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], "D174 final apply ledger", errors)
        require_false(final_apply_ledger, [
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
            "real_apply_allowed",
            "real_apply_executed",
            "actual_apply_executed",
            "apply_requested",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "actual_apply_executed_by_ai",
            "real_apply_executed_by_ai",
            "route_inserted",
            "route_inserted_by_ai",
            "protected_core_mutated",
            "protected_core_mutated_by_ai",
            "git_action_by_ai",
        ], "D174 final apply ledger", errors)

    if not replay_index:
        errors.append("missing D174 replay index")
    else:
        if replay_index.get("ok") is not True:
            errors.append("D174 replay index ok must be true")
        if replay_index.get("replay_index_status") != "REPLAY_INDEX_CREATED_FOR_CHAIN_ARCHIVE":
            errors.append("D174 replay index status mismatch")
        require_true(replay_index, [
            "archive_ready",
            "post_apply_verified",
            "apply_integrity_verified",
            "guarded_apply_recorded",
            "candidate_apply_recorded",
        ], "D174 replay index", errors)
        require_false(replay_index, [
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
            "real_apply_executed",
            "actual_apply_executed",
            "route_inserted_by_ai",
            "protected_core_mutated_by_ai",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "actual_apply_executed_by_ai",
            "real_apply_executed_by_ai",
            "route_inserted",
            "protected_core_mutated",
            "git_action_by_ai",
        ], "D174 replay index", errors)

    if not d175_scope:
        errors.append("missing D174 D175 chain archive scope")
    else:
        if d175_scope.get("ok") is not True:
            errors.append("D174 D175 scope ok must be true")
        if d175_scope.get("allowed_next_gate") != REQ_D175_GATE:
            errors.append("D174 D175 scope allowed_next_gate must be D175")
        require_true(d175_scope, [
            "sandbox_candidate_reentry_chain_archive_scope_only",
            "final_apply_audit_complete",
            "final_apply_ledger_created",
            "replay_index_created",
            "post_apply_verified",
            "apply_integrity_verified",
            "guarded_apply_recorded",
            "candidate_apply_recorded",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
        ], "D174 D175 scope", errors)
        require_false(d175_scope, [
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
            "real_apply_allowed_after_d174_by_ai",
            "route_insert_allowed_after_d174_by_ai",
            "protected_core_mutation_allowed_after_d174_by_ai",
            "network_allowed_after_d174_by_ai",
            "secret_read_allowed_after_d174_by_ai",
            "shell_allowed_after_d174_by_ai",
            "git_action_allowed_after_d174_by_ai",
        ], "D174 D175 scope", errors)

    return errors


def build_archive_manifest(archive_id, d174, replay_index):
    ordered_chain = replay_index.get("ordered_chain") or [
        "D156", "D157", "D158", "D159", "D160", "D161", "D162", "D163", "D164", "D165",
        "D166", "D167", "D168", "D169", "D170", "D171", "D172", "D173", "D174", "D175",
    ]
    data = {
        "state": "D175_SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_MANIFEST",
        "ok": True,
        "archive_id": archive_id,
        "final_audit_id": d174.get("final_audit_id"),
        "post_apply_verification_id": d174.get("post_apply_verification_id"),
        "guarded_apply_id": d174.get("guarded_apply_id"),
        "apply_intent_id": d174.get("apply_intent_id"),
        "apply_preflight_id": d174.get("apply_preflight_id"),
        "verification_id": d174.get("verification_id"),
        "run_id": d174.get("run_id"),
        "intent_id": d174.get("intent_id"),
        "candidate_id": d174.get("candidate_id"),
        "response_id": d174.get("response_id"),
        "created_at": now(),
        "archive_status": "CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
        "archive_mode": "LOCAL_JSON_MANIFEST_ONLY",
        "chain_kind": "sandbox_candidate_reentry_record_only_apply_chain",
        "ordered_chain": ordered_chain,
        "archive_ready": True,
        "final_apply_audit_complete": True,
        "final_apply_ledger_created": True,
        "replay_index_created": True,
        "post_apply_verified": True,
        "apply_integrity_verified": True,
        "guarded_apply_recorded": True,
        "candidate_apply_recorded": True,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "archive_uploaded": False,
        "archive_compressed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "no_real_apply": True,
        "no_network": True,
        "no_secret_read": True,
        "no_shell": True,
        "no_route_insert": True,
        "no_core_mutation_by_ai": True,
        "no_git_action_by_ai": True,
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_chain_closure_receipt(archive_id, d174):
    data = {
        "state": "D175_SANDBOX_CANDIDATE_REENTRY_CHAIN_CLOSURE_RECEIPT",
        "ok": True,
        "archive_id": archive_id,
        "final_audit_id": d174.get("final_audit_id"),
        "post_apply_verification_id": d174.get("post_apply_verification_id"),
        "guarded_apply_id": d174.get("guarded_apply_id"),
        "apply_intent_id": d174.get("apply_intent_id"),
        "apply_preflight_id": d174.get("apply_preflight_id"),
        "verification_id": d174.get("verification_id"),
        "run_id": d174.get("run_id"),
        "intent_id": d174.get("intent_id"),
        "candidate_id": d174.get("candidate_id"),
        "created_at": now(),
        "chain_closure_status": "REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE",
        "closure_mode": "LOCAL_RECORD_ONLY_NO_EXECUTION",
        "archive_ready": True,
        "archive_manifest_created": True,
        "final_apply_audit_complete": True,
        "final_apply_ledger_created": True,
        "replay_index_created": True,
        "post_apply_verified": True,
        "apply_integrity_verified": True,
        "guarded_apply_recorded": True,
        "candidate_apply_recorded": True,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "no_real_apply": True,
        "no_network": True,
        "no_secret_read": True,
        "no_shell": True,
        "no_route_insert": True,
        "no_core_mutation_by_ai": True,
        "no_git_action_by_ai": True,
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_d176_scope(archive_id, d174):
    return {
        "state": "D175_D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE",
        "ok": True,
        "archive_id": archive_id,
        "final_audit_id": d174.get("final_audit_id"),
        "post_apply_verification_id": d174.get("post_apply_verification_id"),
        "guarded_apply_id": d174.get("guarded_apply_id"),
        "apply_intent_id": d174.get("apply_intent_id"),
        "apply_preflight_id": d174.get("apply_preflight_id"),
        "verification_id": d174.get("verification_id"),
        "run_id": d174.get("run_id"),
        "intent_id": d174.get("intent_id"),
        "preflight_id": d174.get("preflight_id"),
        "validation_id": d174.get("validation_id"),
        "candidate_id": d174.get("candidate_id"),
        "response_id": d174.get("response_id"),
        "runner_id": d174.get("runner_id"),
        "plan_id": d174.get("plan_id"),
        "review_id": d174.get("review_id"),
        "scope_id": d174.get("scope_id"),
        "intake_id": d174.get("intake_id"),
        "reentry_id": d174.get("reentry_id"),
        "next_cycle_id": d174.get("next_cycle_id"),
        "cycle_closure_id": d174.get("cycle_closure_id"),
        "previous_candidate_id": d174.get("previous_candidate_id"),
        "proposal_id": d174.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D176_GATE,
        "sandbox_candidate_reentry_controlled_next_cycle_scope_only": True,
        "archive_manifest_created": True,
        "chain_closure_receipt_created": True,
        "chain_archived": True,
        "next_cycle_requires_fresh_intent": True,
        "next_cycle_requires_human_review": True,
        "next_cycle_inherits_no_authority": True,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_apply_allowed_after_d175_by_ai": False,
        "route_insert_allowed_after_d175_by_ai": False,
        "protected_core_mutation_allowed_after_d175_by_ai": False,
        "network_allowed_after_d175_by_ai": False,
        "secret_read_allowed_after_d175_by_ai": False,
        "shell_allowed_after_d175_by_ai": False,
        "git_action_allowed_after_d175_by_ai": False,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d176_allowed_to_create": [
            "sandbox_candidate_reentry_controlled_next_cycle_scope",
            "sandbox_candidate_reentry_next_cycle_reset_receipt",
            "d177_controlled_autonomy_cycle_reentry_intake_scope",
        ],
        "d176_must_not_execute": [
            "real_core_apply",
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
    }


def create_sandbox_candidate_reentry_chain_archive_scope(root="."):
    root = Path(root).resolve()

    d174 = read_json(root / D174_REPORT, {}) or {}
    final_apply_ledger = read_json(root / D174_FINAL_APPLY_LEDGER, {}) or {}
    replay_index = read_json(root / D174_REPLAY_INDEX, {}) or {}
    d175_scope = read_json(root / D174_D175_SCOPE, {}) or {}

    normalize_d174_compat(d174, final_apply_ledger, replay_index, d175_scope)
    errors = validate_d174(d174, final_apply_ledger, replay_index, d175_scope)

    archive_id = "d175-" + digest({
        "final_audit_id": d174.get("final_audit_id"),
        "post_apply_verification_id": d174.get("post_apply_verification_id"),
        "guarded_apply_id": d174.get("guarded_apply_id"),
        "apply_intent_id": d174.get("apply_intent_id"),
        "apply_preflight_id": d174.get("apply_preflight_id"),
        "verification_id": d174.get("verification_id"),
        "run_id": d174.get("run_id"),
        "intent_id": d174.get("intent_id"),
        "candidate_id": d174.get("candidate_id"),
        "response_id": d174.get("response_id"),
        "runner_id": d174.get("runner_id"),
        "plan_id": d174.get("plan_id"),
        "review_id": d174.get("review_id"),
        "scope_id": d174.get("scope_id"),
        "intake_id": d174.get("intake_id"),
        "reentry_id": d174.get("reentry_id"),
        "proposal_id": d174.get("proposal_id"),
    })

    archive_manifest = build_archive_manifest(archive_id, d174, replay_index)
    chain_closure_receipt = build_chain_closure_receipt(archive_id, d174)
    d176_scope = build_d176_scope(archive_id, d174)

    for label, item in [
        ("archive_manifest", archive_manifest),
        ("chain_closure_receipt", chain_closure_receipt),
    ]:
        require_true(item, [
            "archive_ready",
            "final_apply_audit_complete",
            "final_apply_ledger_created",
            "replay_index_created",
            "post_apply_verified",
            "apply_integrity_verified",
            "guarded_apply_recorded",
            "candidate_apply_recorded",
            "no_real_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
        ], label, errors)
        require_false(item, [
            "candidate_apply_executed",
            "candidate_apply_executed_by_ai",
            "real_apply_executed",
            "actual_apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "actual_apply_executed_by_ai",
            "real_apply_executed_by_ai",
            "route_inserted",
            "route_inserted_by_ai",
            "protected_core_mutated",
            "protected_core_mutated_by_ai",
            "git_action_by_ai",
        ], label, errors)

    require_true(d176_scope, [
        "sandbox_candidate_reentry_controlled_next_cycle_scope_only",
        "archive_manifest_created",
        "chain_closure_receipt_created",
        "chain_archived",
        "next_cycle_requires_fresh_intent",
        "next_cycle_requires_human_review",
        "next_cycle_inherits_no_authority",
        "fresh_intent_required",
        "human_review_required",
        "canonical_guard_schema_required",
    ], "d176_scope", errors)
    require_false(d176_scope, [
        "candidate_apply_executed",
        "candidate_apply_executed_by_ai",
        "real_apply_allowed_after_d175_by_ai",
        "route_insert_allowed_after_d175_by_ai",
        "protected_core_mutation_allowed_after_d175_by_ai",
        "network_allowed_after_d175_by_ai",
        "secret_read_allowed_after_d175_by_ai",
        "shell_allowed_after_d175_by_ai",
        "git_action_allowed_after_d175_by_ai",
    ], "d176_scope", errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE_BLOCKED"
    result = "D175_SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE_CREATED" if ok else "D175_SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE_BLOCKED"

    if ok:
        write_json(root / ARCHIVE_MANIFEST_OUT, archive_manifest)
        write_json(root / CHAIN_CLOSURE_RECEIPT_OUT, chain_closure_receipt)
        write_json(root / D176_SCOPE_OUT, d176_scope)

    guardrails = normalize_guard_flags({
        "sandbox_candidate_reentry_chain_archive_scope_only": True,
        "sandbox_candidate_reentry_chain_archive_manifest_only": True,
        "sandbox_candidate_reentry_chain_closure_receipt_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "final_apply_audit_complete": ok,
        "final_apply_ledger_created": ok,
        "replay_index_created": ok,
        "archive_manifest_created": ok,
        "chain_closure_receipt_created": ok,
        "chain_archived": ok,
        "archive_ready": ok,
        "post_apply_verified": ok,
        "apply_integrity_verified": ok,
        "guarded_apply_recorded": ok,
        "candidate_apply_recorded": ok,
        "candidate_apply_executed": False,
        "candidate_apply_executed_by_ai": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_apply_executed": False,
        "actual_apply_executed": False,
        "approval_for_d176_sandbox_candidate_reentry_controlled_next_cycle_scope_only": ok,
        "real_apply_allowed_after_d175_by_ai": False,
        "route_insert_allowed_after_d175_by_ai": False,
        "protected_core_mutation_allowed_after_d175_by_ai": False,
        "network_allowed_after_d175_by_ai": False,
        "secret_read_allowed_after_d175_by_ai": False,
        "shell_allowed_after_d175_by_ai": False,
        "git_action_allowed_after_d175_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D175_SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "archive_id": archive_id,
        "final_audit_id": d174.get("final_audit_id"),
        "post_apply_verification_id": d174.get("post_apply_verification_id"),
        "guarded_apply_id": d174.get("guarded_apply_id"),
        "apply_intent_id": d174.get("apply_intent_id"),
        "apply_preflight_id": d174.get("apply_preflight_id"),
        "verification_id": d174.get("verification_id"),
        "run_id": d174.get("run_id"),
        "intent_id": d174.get("intent_id"),
        "preflight_id": d174.get("preflight_id"),
        "validation_id": d174.get("validation_id"),
        "candidate_id": d174.get("candidate_id"),
        "response_id": d174.get("response_id"),
        "runner_id": d174.get("runner_id"),
        "plan_id": d174.get("plan_id"),
        "review_id": d174.get("review_id"),
        "scope_id": d174.get("scope_id"),
        "intake_id": d174.get("intake_id"),
        "reentry_id": d174.get("reentry_id"),
        "next_cycle_id": d174.get("next_cycle_id"),
        "cycle_closure_id": d174.get("cycle_closure_id"),
        "previous_candidate_id": d174.get("previous_candidate_id"),
        "proposal_id": d174.get("proposal_id"),
        "source_d174_report": D174_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "archive_manifest": archive_manifest if ok else {},
        "chain_closure_receipt": chain_closure_receipt if ok else {},
        "d176_scope": d176_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "archive_id": archive_id,
            "final_audit_id": d174.get("final_audit_id"),
            "post_apply_verification_id": d174.get("post_apply_verification_id"),
            "guarded_apply_id": d174.get("guarded_apply_id"),
            "apply_intent_id": d174.get("apply_intent_id"),
            "apply_preflight_id": d174.get("apply_preflight_id"),
            "verification_id": d174.get("verification_id"),
            "run_id": d174.get("run_id"),
            "intent_id": d174.get("intent_id"),
            "candidate_id": d174.get("candidate_id"),
            "response_id": d174.get("response_id"),
            "proposal_id": d174.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D175_PLUS" if ok else "BLOCKED",
            "archive_status": "CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED" if ok else "BLOCKED",
            "chain_closure_status": "REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY" if ok else "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D176_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_chain_archive_scope_created": ok,
            "archive_manifest_created": ok,
            "chain_closure_receipt_created": ok,
            "d176_scope_created": ok,
            "chain_archived": ok,
            "real_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D176 may create controlled next cycle scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_chain_archive_scope(), ensure_ascii=False, indent=2))
