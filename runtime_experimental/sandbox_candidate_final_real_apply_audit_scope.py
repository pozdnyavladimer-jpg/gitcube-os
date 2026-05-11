
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D152_REPORT = "reports/d152_sandbox_candidate_post_real_apply_verification_scope.json"
D152_VERIFICATION_REPORT = "reports/d152_sandbox_candidate_real_apply_verification_report.json"
D152_INTEGRITY_RECEIPT = "reports/d152_sandbox_candidate_real_apply_integrity_receipt.json"
D152_D153_SCOPE = "reports/d152_d153_sandbox_candidate_final_real_apply_audit_scope.json"

OUT = "reports/d153_sandbox_candidate_final_real_apply_audit_scope.json"
AUDIT_LEDGER_OUT = "reports/d153_sandbox_candidate_real_apply_audit_ledger.json"
REPLAY_INDEX_OUT = "reports/d153_sandbox_candidate_real_apply_replay_index.json"
D154_SCOPE_OUT = "reports/d153_d154_sandbox_candidate_real_apply_chain_archive_scope.json"

REQ_D152_DECISION = "SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_READY"
REQ_D153_GATE = "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE"
REQ_D154_GATE = "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE"

DANGEROUS_FALSE_KEYS = [
    "network_accessed", "secret_read", "shell_executed_by_ai", "shell_from_ai_executed",
    "git_action_by_ai", "git_commit_by_ai", "git_push_by_ai",
    "route_inserted", "route_inserted_by_ai",
    "protected_core_mutated", "protected_core_mutated_by_ai",
    "actual_apply_executed_by_ai", "real_apply_executed_by_ai",
    "canonical_memory_mutated", "rollback_executed", "restore_executed",
]

STATUS_FALSE_D152 = [
    "real_apply_allowed_after_d152_by_ai",
    "route_insert_allowed_after_d152_by_ai",
    "protected_core_mutation_allowed_after_d152_by_ai",
    "network_allowed_after_d152_by_ai",
    "secret_read_allowed_after_d152_by_ai",
    "shell_allowed_after_d152_by_ai",
    "git_action_allowed_after_d152_by_ai",
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


def _check_false_fields(errors, label, obj, keys):
    for key in keys:
        if key in obj and obj.get(key) is not False:
            errors.append(f"{label} {key} must be false")


def validate_d152(d152, verification_report, integrity_receipt, d153_scope):
    errors = []
    if not d152:
        return ["missing D152 sandbox candidate post real apply verification scope report"]

    if d152.get("ok") is not True:
        errors.append("D152 ok must be true")
    if d152.get("decision") != REQ_D152_DECISION:
        errors.append("D152 decision must be SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_READY")

    summary = d152.get("summary", {})
    expected_summary = {
        "verification_status": "REAL_APPLY_RUN_SCOPE_VERIFIED_NO_AI_CORE_MUTATION",
        "integrity_status": "NO_AI_CORE_MUTATION_VERIFIED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_ONLY",
        "next_step": REQ_D153_GATE,
    }
    for key, value in expected_summary.items():
        if summary.get(key) != value:
            errors.append(f"D152 summary {key} must be {value}")

    guard = d152.get("guardrails", {})
    _check_false_fields(errors, "D152 guardrails", guard, DANGEROUS_FALSE_KEYS + STATUS_FALSE_D152)
    for key in [
        "sandbox_candidate_post_real_apply_verification_scope_only",
        "real_apply_verification_report_only",
        "real_apply_integrity_receipt_only",
        "approval_for_d153_final_real_apply_audit_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D152 guardrails {key} must be true")

    if not verification_report:
        errors.append("missing D152 real apply verification report")
    else:
        if verification_report.get("ok") is not True:
            errors.append("D152 verification report ok must be true")
        if verification_report.get("verification_status") != "REAL_APPLY_RUN_SCOPE_VERIFIED_NO_AI_CORE_MUTATION":
            errors.append("D152 verification report status must verify no AI core mutation")
        _check_false_fields(errors, "D152 verification report", verification_report, DANGEROUS_FALSE_KEYS)

    if not integrity_receipt:
        errors.append("missing D152 real apply integrity receipt")
    else:
        if integrity_receipt.get("ok") is not True:
            errors.append("D152 integrity receipt ok must be true")
        if integrity_receipt.get("integrity_status") != "NO_AI_CORE_MUTATION_VERIFIED":
            errors.append("D152 integrity receipt must verify no AI core mutation")
        _check_false_fields(errors, "D152 integrity receipt", integrity_receipt, DANGEROUS_FALSE_KEYS)

    if not d153_scope:
        errors.append("missing D152 D153 final real apply audit scope")
    else:
        if d153_scope.get("ok") is not True:
            errors.append("D152 D153 scope ok must be true")
        if d153_scope.get("allowed_next_gate") != REQ_D153_GATE:
            errors.append("D152 D153 scope allowed_next_gate must be D153")
        if d153_scope.get("sandbox_candidate_final_real_apply_audit_scope_only") is not True:
            errors.append("D152 D153 scope must be final-real-apply-audit-only")
        if d153_scope.get("human_review_required") is not True:
            errors.append("D152 D153 scope must require human review")
        _check_false_fields(errors, "D152 D153 scope", d153_scope, STATUS_FALSE_D152)

    return errors


def build_audit_ledger(audit_id, d152):
    return {
        "state": "D153_SANDBOX_CANDIDATE_REAL_APPLY_AUDIT_LEDGER",
        "ok": True,
        "audit_id": audit_id,
        "verification_id": d152.get("verification_id"),
        "run_apply_id": d152.get("run_apply_id"),
        "signature_id": d152.get("signature_id"),
        "preflight_id": d152.get("preflight_id"),
        "intent_id": d152.get("intent_id"),
        "decision_id": d152.get("decision_id"),
        "archive_id": d152.get("archive_id"),
        "candidate_id": d152.get("candidate_id"),
        "proposal_id": d152.get("proposal_id"),
        "created_at": now(),
        "ledger_mode": "FINAL_REAL_APPLY_AUDIT_LEDGER_ONLY_NO_ACTION",
        "audit_status": "FINAL_REAL_APPLY_AUDIT_LEDGER_CREATED_NO_AI_CORE_MUTATION",
        "audit_entries": [
            "D147 promotion decision ready",
            "D148 human real apply intent recorded",
            "D149 guarded real apply preflight recorded",
            "D150 human signed execution scope recorded",
            "D151 guarded real apply run scope recorded",
            "D152 post real apply verification passed",
        ],
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "route_inserted_by_ai": False,
        "protected_core_mutated": False,
        "protected_core_mutated_by_ai": False,
        "canonical_memory_mutated": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_replay_index(audit_id, d152):
    return {
        "state": "D153_SANDBOX_CANDIDATE_REAL_APPLY_REPLAY_INDEX",
        "ok": True,
        "audit_id": audit_id,
        "verification_id": d152.get("verification_id"),
        "run_apply_id": d152.get("run_apply_id"),
        "candidate_id": d152.get("candidate_id"),
        "proposal_id": d152.get("proposal_id"),
        "created_at": now(),
        "replay_index_mode": "REAL_APPLY_REPLAY_INDEX_ONLY_NO_EXECUTION",
        "replay_status": "REAL_APPLY_CHAIN_REPLAY_INDEX_CREATED_NO_EXECUTION",
        "replay_sources": [
            "reports/d147_sandbox_candidate_promotion_decision_scope.json",
            "reports/d148_sandbox_candidate_human_real_apply_intent_scope.json",
            "reports/d149_sandbox_candidate_guarded_real_apply_preflight_scope.json",
            "reports/d150_sandbox_candidate_human_signed_real_apply_execution_scope.json",
            "reports/d151_sandbox_candidate_guarded_real_apply_run_scope.json",
            "reports/d152_sandbox_candidate_post_real_apply_verification_scope.json",
        ],
        "replay_executes_anything": False,
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_d154_scope(audit_id, d152):
    return {
        "state": "D153_D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE",
        "ok": True,
        "audit_id": audit_id,
        "verification_id": d152.get("verification_id"),
        "run_apply_id": d152.get("run_apply_id"),
        "signature_id": d152.get("signature_id"),
        "preflight_id": d152.get("preflight_id"),
        "intent_id": d152.get("intent_id"),
        "decision_id": d152.get("decision_id"),
        "archive_id": d152.get("archive_id"),
        "candidate_id": d152.get("candidate_id"),
        "proposal_id": d152.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D154_GATE,
        "sandbox_candidate_real_apply_chain_archive_scope_only": True,
        "human_review_required": True,
        "d154_allowed_to_create": [
            "real_apply_chain_archive_scope",
            "real_apply_chain_archive_manifest",
            "real_apply_chain_closure_receipt",
            "d155_guarded_autonomy_cycle_closure_scope",
        ],
        "d154_must_not_execute": [
            "real_core_apply_again",
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
        "real_apply_allowed_after_d153_by_ai": False,
        "route_insert_allowed_after_d153_by_ai": False,
        "protected_core_mutation_allowed_after_d153_by_ai": False,
        "network_allowed_after_d153_by_ai": False,
        "secret_read_allowed_after_d153_by_ai": False,
        "shell_allowed_after_d153_by_ai": False,
        "git_action_allowed_after_d153_by_ai": False,
    }


def create_sandbox_candidate_final_real_apply_audit_scope(root="."):
    root = Path(root).resolve()

    d152 = read_json(root / D152_REPORT, {}) or {}
    verification_report = read_json(root / D152_VERIFICATION_REPORT, {}) or {}
    integrity_receipt = read_json(root / D152_INTEGRITY_RECEIPT, {}) or {}
    d153_scope = read_json(root / D152_D153_SCOPE, {}) or {}

    errors = validate_d152(d152, verification_report, integrity_receipt, d153_scope)

    audit_id = "d153-" + digest({
        "verification_id": d152.get("verification_id"),
        "run_apply_id": d152.get("run_apply_id"),
        "signature_id": d152.get("signature_id"),
        "candidate_id": d152.get("candidate_id"),
        "proposal_id": d152.get("proposal_id"),
    })

    audit_ledger = build_audit_ledger(audit_id, d152)
    replay_index = build_replay_index(audit_id, d152)
    d154_scope = build_d154_scope(audit_id, d152)

    for label, obj in [("audit_ledger", audit_ledger), ("replay_index", replay_index), ("d154_scope", d154_scope)]:
        _check_false_fields(errors, label, obj, DANGEROUS_FALSE_KEYS + [
            "real_apply_allowed_after_d153_by_ai",
            "route_insert_allowed_after_d153_by_ai",
            "protected_core_mutation_allowed_after_d153_by_ai",
            "network_allowed_after_d153_by_ai",
            "secret_read_allowed_after_d153_by_ai",
            "shell_allowed_after_d153_by_ai",
            "git_action_allowed_after_d153_by_ai",
        ])

    ok = not errors
    decision = "SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_BLOCKED"
    result = "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_CREATED" if ok else "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_BLOCKED"

    if ok:
        write_json(root / AUDIT_LEDGER_OUT, audit_ledger)
        write_json(root / REPLAY_INDEX_OUT, replay_index)
        write_json(root / D154_SCOPE_OUT, d154_scope)

    report = {
        "state": "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "audit_id": audit_id,
        "verification_id": d152.get("verification_id"),
        "run_apply_id": d152.get("run_apply_id"),
        "signature_id": d152.get("signature_id"),
        "preflight_id": d152.get("preflight_id"),
        "intent_id": d152.get("intent_id"),
        "decision_id": d152.get("decision_id"),
        "archive_id": d152.get("archive_id"),
        "candidate_id": d152.get("candidate_id"),
        "proposal_id": d152.get("proposal_id"),
        "source_d152_report": D152_REPORT,
        "real_apply_audit_ledger": audit_ledger if ok else {},
        "real_apply_replay_index": replay_index if ok else {},
        "d154_scope": d154_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "shell_executed_by_ai": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "route_inserted_by_ai": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "sandbox_candidate_final_real_apply_audit_scope_only": True,
            "real_apply_audit_ledger_only": True,
            "real_apply_replay_index_only": True,
            "approval_for_d154_real_apply_chain_archive_scope_only": ok,
            "real_apply_allowed_after_d153_by_ai": False,
            "route_insert_allowed_after_d153_by_ai": False,
            "protected_core_mutation_allowed_after_d153_by_ai": False,
            "network_allowed_after_d153_by_ai": False,
            "secret_read_allowed_after_d153_by_ai": False,
            "shell_allowed_after_d153_by_ai": False,
            "git_action_allowed_after_d153_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "audit_id": audit_id,
            "verification_id": d152.get("verification_id"),
            "run_apply_id": d152.get("run_apply_id"),
            "candidate_id": d152.get("candidate_id"),
            "proposal_id": d152.get("proposal_id"),
            "final_real_apply_audit_status": "FINAL_REAL_APPLY_AUDIT_LEDGER_CREATED_NO_AI_CORE_MUTATION" if ok else "BLOCKED",
            "replay_index_status": "REAL_APPLY_CHAIN_REPLAY_INDEX_CREATED_NO_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "FINAL_REAL_APPLY_AUDIT_READY_FOR_CHAIN_ARCHIVE_NOT_CORE_MUTATED_BY_AI" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D154_GATE if ok else "BLOCKED",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_final_real_apply_audit_scope(), ensure_ascii=False, indent=2))
