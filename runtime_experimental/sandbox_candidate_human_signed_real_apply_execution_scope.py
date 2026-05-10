
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D149_REPORT = "reports/d149_sandbox_candidate_guarded_real_apply_preflight_scope.json"
D149_PREFLIGHT_REPORT = "reports/d149_sandbox_candidate_real_apply_preflight_report.json"
D149_BLOCKERS = "reports/d149_sandbox_candidate_real_apply_blockers.json"
D149_D150_SCOPE = "reports/d149_d150_sandbox_candidate_human_signed_real_apply_execution_scope.json"

OUT = "reports/d150_sandbox_candidate_human_signed_real_apply_execution_scope.json"
SIGNATURE_RECORD_OUT = "reports/d150_sandbox_candidate_real_apply_signature_record.json"
AUTHORITY_GUARD_OUT = "reports/d150_sandbox_candidate_real_apply_execution_authority_guard.json"
D151_SCOPE_OUT = "reports/d150_d151_sandbox_candidate_guarded_real_apply_run_scope.json"

REQ_D149_DECISION = "SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_READY"
REQ_D150_GATE = "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE"
REQ_D151_GATE = "D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE"

FALSE_KEYS = [
    "external_ai_called", "network_accessed", "api_key_read", "secret_read",
    "shell_from_ai_executed", "shell_executed_by_ai",
    "runtime_code_mutated", "protected_core_mutated", "canonical_memory_mutated",
    "actual_apply_executed", "real_apply_executed", "route_inserted",
    "git_commit_by_ai", "git_push_by_ai", "git_action_by_ai",
    "rollback_executed", "restore_executed",
]

STATUS_FALSE_D149 = [
    "real_apply_allowed_after_d149_by_ai",
    "route_insert_allowed_after_d149_by_ai",
    "protected_core_mutation_allowed_after_d149_by_ai",
    "network_allowed_after_d149_by_ai",
    "secret_read_allowed_after_d149_by_ai",
    "shell_allowed_after_d149_by_ai",
    "git_action_allowed_after_d149_by_ai",
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


def validate_d149(d149, preflight_report, blockers, d150_scope):
    errors = []

    if not d149:
        errors.append("missing D149 sandbox candidate guarded real apply preflight scope report")
        return errors

    if d149.get("ok") is not True:
        errors.append("D149 ok must be true")
    if d149.get("decision") != REQ_D149_DECISION:
        errors.append("D149 decision must be SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_READY")

    summary = d149.get("summary", {})
    expected = {
        "real_apply_preflight_status": "REAL_APPLY_PREFLIGHT_CREATED_NO_EXECUTION",
        "real_apply_blocker_status": "AI_REAL_APPLY_BLOCKERS_DECLARED",
        "candidate_status": "SANDBOX_CHAIN_READY_FOR_HUMAN_SIGNED_REAL_APPLY_EXECUTION_NOT_CORE_APPLIED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_ONLY",
        "next_step": REQ_D150_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D149 summary.{key} must be {value}")

    guard = d149.get("guardrails", {})
    for key in FALSE_KEYS:
        if key in guard and guard.get(key) is not False:
            errors.append(f"D149 guardrails.{key} must be false")
    for key in STATUS_FALSE_D149:
        if guard.get(key) is not False:
            errors.append(f"D149 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_guarded_real_apply_preflight_scope_only",
        "real_apply_preflight_report_only",
        "real_apply_blockers_only",
        "approval_for_d150_human_signed_real_apply_execution_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D149 guardrails.{key} must be true")

    if guard.get("approval_for_real_core_apply_now") is not False:
        errors.append("D149 approval_for_real_core_apply_now must be false")

    if not preflight_report:
        errors.append("missing D149 real apply preflight report")
    else:
        if preflight_report.get("ok") is not True:
            errors.append("D149 real apply preflight report ok must be true")
        if preflight_report.get("preflight_mode") != "REAL_APPLY_PREFLIGHT_ONLY_NO_REAL_APPLY":
            errors.append("D149 preflight report mode must be REAL_APPLY_PREFLIGHT_ONLY_NO_REAL_APPLY")
        if preflight_report.get("preflight_status") != "REAL_APPLY_PREFLIGHT_CREATED_NO_EXECUTION":
            errors.append("D149 preflight status must be no-execution")
        for key in FALSE_KEYS:
            if key in preflight_report and preflight_report.get(key) is not False:
                errors.append(f"D149 preflight report {key} must be false")

    if not blockers:
        errors.append("missing D149 real apply blockers")
    else:
        if blockers.get("ok") is not True:
            errors.append("D149 real apply blockers ok must be true")
        if blockers.get("blocker_mode") != "REAL_APPLY_BLOCKERS_DECLARED_NO_EXECUTION":
            errors.append("D149 blockers mode must be REAL_APPLY_BLOCKERS_DECLARED_NO_EXECUTION")
        for b in [
            "real_core_apply_by_ai", "route_insert_by_ai", "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai", "shell_exec_from_ai", "network_call_by_ai",
            "secret_read_by_ai", "git_commit_by_ai", "git_push_by_ai",
        ]:
            if b not in blockers.get("hard_blockers_for_ai", []):
                errors.append(f"D149 blockers missing {b}")
        for key in FALSE_KEYS:
            if key in blockers and blockers.get(key) is not False:
                errors.append(f"D149 blockers {key} must be false")

    if not d150_scope:
        errors.append("missing D149 D150 human signed real apply execution scope")
    else:
        if d150_scope.get("ok") is not True:
            errors.append("D149 D150 scope ok must be true")
        if d150_scope.get("allowed_next_gate") != REQ_D150_GATE:
            errors.append("D149 D150 scope allowed_next_gate must be D150")
        if d150_scope.get("sandbox_candidate_human_signed_real_apply_execution_scope_only") is not True:
            errors.append("D149 D150 scope must be human-signed-real-apply-execution-scope-only")
        if d150_scope.get("human_review_required") is not True:
            errors.append("D149 D150 scope must require human review")
        for key in STATUS_FALSE_D149:
            if d150_scope.get(key) is not False:
                errors.append(f"D149 D150 scope {key} must be false")

    return errors


def build_signature_record(signature_id, d149):
    return {
        "state": "D150_SANDBOX_CANDIDATE_REAL_APPLY_SIGNATURE_RECORD",
        "ok": True,
        "signature_id": signature_id,
        "preflight_id": d149.get("preflight_id"),
        "intent_id": d149.get("intent_id"),
        "decision_id": d149.get("decision_id"),
        "archive_id": d149.get("archive_id"),
        "candidate_id": d149.get("candidate_id"),
        "proposal_id": d149.get("proposal_id"),
        "created_at": now(),
        "signature_mode": "HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_RECORD_ONLY_NO_REAL_APPLY",
        "operator_signature_status": "HUMAN_SIGNED_EXECUTION_SCOPE_RECORDED_NO_EXECUTION",
        "approved_for_d151_guarded_real_apply_run_scope_only": True,
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
        "required_phrase_for_next_gate": "APPROVE_D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_ONLY",
    }


def build_authority_guard(signature_id, d149):
    return {
        "state": "D150_SANDBOX_CANDIDATE_REAL_APPLY_EXECUTION_AUTHORITY_GUARD",
        "ok": True,
        "signature_id": signature_id,
        "preflight_id": d149.get("preflight_id"),
        "intent_id": d149.get("intent_id"),
        "candidate_id": d149.get("candidate_id"),
        "created_at": now(),
        "authority_mode": "HUMAN_SIGNED_REAL_APPLY_EXECUTION_AUTHORITY_GUARD_ONLY_NO_REAL_APPLY",
        "allow_d151_guarded_real_apply_run_scope": True,
        "allow_real_core_apply_now": False,
        "allow_route_insert": False,
        "allow_protected_core_mutation": False,
        "allow_network": False,
        "allow_secret_read": False,
        "allow_shell_exec": False,
        "allow_git_action_by_ai": False,
        "real_apply_allowed_after_d150_by_ai": False,
        "route_insert_allowed_after_d150_by_ai": False,
        "protected_core_mutation_allowed_after_d150_by_ai": False,
        "network_allowed_after_d150_by_ai": False,
        "secret_read_allowed_after_d150_by_ai": False,
        "shell_allowed_after_d150_by_ai": False,
        "git_action_allowed_after_d150_by_ai": False,
        "human_review_required": True,
    }


def build_d151_scope(signature_id, d149):
    return {
        "state": "D150_D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE",
        "ok": True,
        "signature_id": signature_id,
        "preflight_id": d149.get("preflight_id"),
        "intent_id": d149.get("intent_id"),
        "decision_id": d149.get("decision_id"),
        "archive_id": d149.get("archive_id"),
        "verification_id": d149.get("verification_id"),
        "apply_id": d149.get("apply_id"),
        "run_id": d149.get("run_id"),
        "candidate_id": d149.get("candidate_id"),
        "proposal_id": d149.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D151_GATE,
        "sandbox_candidate_guarded_real_apply_run_scope_only": True,
        "human_review_required": True,
        "d151_allowed_to_create": [
            "guarded_real_apply_run_scope",
            "real_apply_run_result",
            "real_apply_run_safety_receipt",
            "d152_post_real_apply_verification_scope",
        ],
        "d151_must_not_execute_by_ai": [
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
        ],
        "real_apply_allowed_after_d150_by_ai": False,
        "route_insert_allowed_after_d150_by_ai": False,
        "protected_core_mutation_allowed_after_d150_by_ai": False,
        "network_allowed_after_d150_by_ai": False,
        "secret_read_allowed_after_d150_by_ai": False,
        "shell_allowed_after_d150_by_ai": False,
        "git_action_allowed_after_d150_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_ONLY",
    }


def create_sandbox_candidate_human_signed_real_apply_execution_scope(root="."):
    root = Path(root).resolve()

    d149 = read_json(root / D149_REPORT, {}) or {}
    preflight_report = read_json(root / D149_PREFLIGHT_REPORT, {}) or {}
    blockers = read_json(root / D149_BLOCKERS, {}) or {}
    d150_scope = read_json(root / D149_D150_SCOPE, {}) or {}

    errors = validate_d149(d149, preflight_report, blockers, d150_scope)

    signature_id = "d150-" + digest({
        "preflight_id": d149.get("preflight_id"),
        "intent_id": d149.get("intent_id"),
        "decision_id": d149.get("decision_id"),
        "archive_id": d149.get("archive_id"),
        "candidate_id": d149.get("candidate_id"),
        "proposal_id": d149.get("proposal_id"),
    })

    signature_record = build_signature_record(signature_id, d149)
    authority_guard = build_authority_guard(signature_id, d149)
    d151_scope = build_d151_scope(signature_id, d149)

    for item_name, item in [
        ("signature_record", signature_record),
        ("authority_guard", authority_guard),
        ("d151_scope", d151_scope),
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
            "real_apply_allowed_after_d150_by_ai",
            "route_insert_allowed_after_d150_by_ai",
            "protected_core_mutation_allowed_after_d150_by_ai",
            "network_allowed_after_d150_by_ai",
            "secret_read_allowed_after_d150_by_ai",
            "shell_allowed_after_d150_by_ai",
            "git_action_allowed_after_d150_by_ai",
        ]:
            if key in item and item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_BLOCKED"
    result = "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_CREATED" if ok else "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_BLOCKED"

    if ok:
        write_json(root / SIGNATURE_RECORD_OUT, signature_record)
        write_json(root / AUTHORITY_GUARD_OUT, authority_guard)
        write_json(root / D151_SCOPE_OUT, d151_scope)

    report = {
        "state": "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "signature_id": signature_id,
        "preflight_id": d149.get("preflight_id"),
        "intent_id": d149.get("intent_id"),
        "decision_id": d149.get("decision_id"),
        "archive_id": d149.get("archive_id"),
        "verification_id": d149.get("verification_id"),
        "apply_id": d149.get("apply_id"),
        "run_id": d149.get("run_id"),
        "candidate_id": d149.get("candidate_id"),
        "proposal_id": d149.get("proposal_id"),
        "source_d149_report": D149_REPORT,
        "real_apply_signature_record": signature_record if ok else {},
        "real_apply_execution_authority_guard": authority_guard if ok else {},
        "d151_scope": d151_scope if ok else {},
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
            "sandbox_candidate_human_signed_real_apply_execution_scope_only": True,
            "human_signed_real_apply_signature_record_only": True,
            "real_apply_execution_authority_guard_only": True,
            "approval_for_d151_guarded_real_apply_run_scope_only": ok,
            "approval_for_real_core_apply_now": False,
            "real_apply_allowed_after_d150_by_ai": False,
            "route_insert_allowed_after_d150_by_ai": False,
            "protected_core_mutation_allowed_after_d150_by_ai": False,
            "network_allowed_after_d150_by_ai": False,
            "secret_read_allowed_after_d150_by_ai": False,
            "shell_allowed_after_d150_by_ai": False,
            "git_action_allowed_after_d150_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "signature_id": signature_id,
            "preflight_id": d149.get("preflight_id"),
            "intent_id": d149.get("intent_id"),
            "decision_id": d149.get("decision_id"),
            "archive_id": d149.get("archive_id"),
            "candidate_id": d149.get("candidate_id"),
            "proposal_id": d149.get("proposal_id"),
            "human_signed_real_apply_status": "HUMAN_SIGNED_REAL_APPLY_SCOPE_RECORDED_NO_REAL_APPLY" if ok else "BLOCKED",
            "real_apply_execution_authority_status": "REAL_APPLY_EXECUTION_AUTHORITY_GUARD_CREATED_NO_REAL_APPLY" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CHAIN_READY_FOR_GUARDED_REAL_APPLY_RUN_SCOPE_NOT_CORE_APPLIED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D151_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "human_signed_real_apply_execution_scope_created": ok,
            "real_apply_signature_record_created": ok,
            "real_apply_execution_authority_guard_created": ok,
            "d151_scope_created": ok,
            "real_core_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "next_step": "D151 may create guarded real apply run scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_human_signed_real_apply_execution_scope(), ensure_ascii=False, indent=2))
