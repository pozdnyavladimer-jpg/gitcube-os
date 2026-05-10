
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D150_REPORT = "reports/d150_sandbox_candidate_human_signed_real_apply_execution_scope.json"
D150_SIGNATURE_RECORD = "reports/d150_sandbox_candidate_real_apply_signature_record.json"
D150_AUTHORITY_GUARD = "reports/d150_sandbox_candidate_real_apply_execution_authority_guard.json"
D150_D151_SCOPE = "reports/d150_d151_sandbox_candidate_guarded_real_apply_run_scope.json"

OUT = "reports/d151_sandbox_candidate_guarded_real_apply_run_scope.json"
RUN_RESULT_OUT = "reports/d151_sandbox_candidate_real_apply_run_result.json"
SAFETY_RECEIPT_OUT = "reports/d151_sandbox_candidate_real_apply_run_safety_receipt.json"
D152_SCOPE_OUT = "reports/d151_d152_sandbox_candidate_post_real_apply_verification_scope.json"

REQ_D150_DECISION = "SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_READY"
REQ_D151_GATE = "D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE"
REQ_D152_GATE = "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE"

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

STATUS_FALSE_D150 = [
    "real_apply_allowed_after_d150_by_ai",
    "route_insert_allowed_after_d150_by_ai",
    "protected_core_mutation_allowed_after_d150_by_ai",
    "network_allowed_after_d150_by_ai",
    "secret_read_allowed_after_d150_by_ai",
    "shell_allowed_after_d150_by_ai",
    "git_action_allowed_after_d150_by_ai",
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


def validate_d150(d150, signature_record, authority_guard, d151_scope):
    errors = []

    if not d150:
        errors.append("missing D150 sandbox candidate human signed real apply execution scope report")
        return errors

    if d150.get("ok") is not True:
        errors.append("D150 ok must be true")
    if d150.get("decision") != REQ_D150_DECISION:
        errors.append("D150 decision must be SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_READY")

    summary = d150.get("summary", {})
    expected = {
        "human_signed_real_apply_status": "HUMAN_SIGNED_REAL_APPLY_SCOPE_RECORDED_NO_REAL_APPLY",
        "real_apply_execution_authority_status": "REAL_APPLY_EXECUTION_AUTHORITY_GUARD_CREATED_NO_REAL_APPLY",
        "candidate_status": "SANDBOX_CHAIN_READY_FOR_GUARDED_REAL_APPLY_RUN_SCOPE_NOT_CORE_APPLIED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_ONLY",
        "next_step": REQ_D151_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D150 summary.{key} must be {value}")

    guard = d150.get("guardrails", {})
    for key in FALSE_KEYS:
        if key in guard and guard.get(key) is not False:
            errors.append(f"D150 guardrails.{key} must be false")
    for key in STATUS_FALSE_D150:
        if guard.get(key) is not False:
            errors.append(f"D150 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_human_signed_real_apply_execution_scope_only",
        "human_signed_real_apply_signature_record_only",
        "real_apply_execution_authority_guard_only",
        "approval_for_d151_guarded_real_apply_run_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D150 guardrails.{key} must be true")

    if guard.get("approval_for_real_core_apply_now") is not False:
        errors.append("D150 approval_for_real_core_apply_now must be false")

    if not signature_record:
        errors.append("missing D150 real apply signature record")
    else:
        if signature_record.get("ok") is not True:
            errors.append("D150 real apply signature record ok must be true")
        if signature_record.get("signature_mode") != "HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_RECORD_ONLY_NO_REAL_APPLY":
            errors.append("D150 signature record mode must be no-real-apply")
        if signature_record.get("approved_for_d151_guarded_real_apply_run_scope_only") is not True:
            errors.append("D150 signature record must approve D151 run scope only")
        if signature_record.get("approved_for_real_core_apply_now") is not False:
            errors.append("D150 signature record approved_for_real_core_apply_now must be false")
        for key in FALSE_KEYS:
            if key in signature_record and signature_record.get(key) is not False:
                errors.append(f"D150 signature record {key} must be false")

    if not authority_guard:
        errors.append("missing D150 real apply execution authority guard")
    else:
        if authority_guard.get("ok") is not True:
            errors.append("D150 authority guard ok must be true")
        if authority_guard.get("authority_mode") != "HUMAN_SIGNED_REAL_APPLY_EXECUTION_AUTHORITY_GUARD_ONLY_NO_REAL_APPLY":
            errors.append("D150 authority guard mode must be HUMAN_SIGNED_REAL_APPLY_EXECUTION_AUTHORITY_GUARD_ONLY_NO_REAL_APPLY")
        if authority_guard.get("allow_d151_guarded_real_apply_run_scope") is not True:
            errors.append("D150 authority guard must allow D151 run scope")
        for key in [
            "allow_real_core_apply_now",
            "allow_route_insert",
            "allow_protected_core_mutation",
            "allow_network",
            "allow_secret_read",
            "allow_shell_exec",
            "allow_git_action_by_ai",
        ]:
            if authority_guard.get(key) is not False:
                errors.append(f"D150 authority guard {key} must be false")
        for key in STATUS_FALSE_D150:
            if authority_guard.get(key) is not False:
                errors.append(f"D150 authority guard {key} must be false")

    if not d151_scope:
        errors.append("missing D150 D151 guarded real apply run scope")
    else:
        if d151_scope.get("ok") is not True:
            errors.append("D150 D151 scope ok must be true")
        if d151_scope.get("allowed_next_gate") != REQ_D151_GATE:
            errors.append("D150 D151 scope allowed_next_gate must be D151")
        if d151_scope.get("sandbox_candidate_guarded_real_apply_run_scope_only") is not True:
            errors.append("D150 D151 scope must be guarded-real-apply-run-scope-only")
        if d151_scope.get("human_review_required") is not True:
            errors.append("D150 D151 scope must require human review")
        for key in STATUS_FALSE_D150:
            if d151_scope.get(key) is not False:
                errors.append(f"D150 D151 scope {key} must be false")

    return errors


def build_run_result(run_apply_id, d150):
    return {
        "state": "D151_SANDBOX_CANDIDATE_REAL_APPLY_RUN_RESULT",
        "ok": True,
        "run_apply_id": run_apply_id,
        "signature_id": d150.get("signature_id"),
        "preflight_id": d150.get("preflight_id"),
        "intent_id": d150.get("intent_id"),
        "decision_id": d150.get("decision_id"),
        "archive_id": d150.get("archive_id"),
        "candidate_id": d150.get("candidate_id"),
        "proposal_id": d150.get("proposal_id"),
        "created_at": now(),
        "run_mode": "GUARDED_REAL_APPLY_RUN_SCOPE_RECORDED_OPERATOR_ONLY_NO_AI_CORE_MUTATION",
        "real_apply_run_status": "GUARDED_REAL_APPLY_RUN_RECORDED_NO_AI_EXECUTION",
        "operator_authorized_run_scope": True,
        "operator_actual_core_apply_executed": False,
        "actual_apply_executed": False,
        "real_apply_executed": False,
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
        "shell_from_ai_executed": False,
        "git_action_by_ai": False,
        "git_commit_by_ai": False,
        "git_push_by_ai": False,
        "human_review_required": True,
    }


def build_safety_receipt(run_apply_id, d150):
    return {
        "state": "D151_SANDBOX_CANDIDATE_REAL_APPLY_RUN_SAFETY_RECEIPT",
        "ok": True,
        "run_apply_id": run_apply_id,
        "signature_id": d150.get("signature_id"),
        "candidate_id": d150.get("candidate_id"),
        "created_at": now(),
        "receipt_mode": "REAL_APPLY_RUN_SAFETY_RECEIPT_NO_AI_CORE_ACTION",
        "safety_status": "AI_DID_NOT_EXECUTE_REAL_CORE_APPLY",
        "no_ai_apply": True,
        "no_ai_route_insert": True,
        "no_ai_protected_core_mutation": True,
        "no_ai_network": True,
        "no_ai_secret_read": True,
        "no_ai_shell": True,
        "no_ai_git_action": True,
        "actual_apply_executed": False,
        "real_apply_executed": False,
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


def build_d152_scope(run_apply_id, d150):
    return {
        "state": "D151_D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE",
        "ok": True,
        "run_apply_id": run_apply_id,
        "signature_id": d150.get("signature_id"),
        "preflight_id": d150.get("preflight_id"),
        "intent_id": d150.get("intent_id"),
        "decision_id": d150.get("decision_id"),
        "archive_id": d150.get("archive_id"),
        "verification_id": d150.get("verification_id"),
        "apply_id": d150.get("apply_id"),
        "run_id": d150.get("run_id"),
        "candidate_id": d150.get("candidate_id"),
        "proposal_id": d150.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D152_GATE,
        "sandbox_candidate_post_real_apply_verification_scope_only": True,
        "human_review_required": True,
        "d152_allowed_to_create": [
            "post_real_apply_verification_scope",
            "real_apply_verification_report",
            "real_apply_integrity_receipt",
            "d153_final_real_apply_audit_scope",
        ],
        "d152_must_not_execute": [
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
        "real_apply_allowed_after_d151_by_ai": False,
        "route_insert_allowed_after_d151_by_ai": False,
        "protected_core_mutation_allowed_after_d151_by_ai": False,
        "network_allowed_after_d151_by_ai": False,
        "secret_read_allowed_after_d151_by_ai": False,
        "shell_allowed_after_d151_by_ai": False,
        "git_action_allowed_after_d151_by_ai": False,
    }


def create_sandbox_candidate_guarded_real_apply_run_scope(root="."):
    root = Path(root).resolve()

    d150 = read_json(root / D150_REPORT, {}) or {}
    signature_record = read_json(root / D150_SIGNATURE_RECORD, {}) or {}
    authority_guard = read_json(root / D150_AUTHORITY_GUARD, {}) or {}
    d151_scope = read_json(root / D150_D151_SCOPE, {}) or {}

    errors = validate_d150(d150, signature_record, authority_guard, d151_scope)

    run_apply_id = "d151-" + digest({
        "signature_id": d150.get("signature_id"),
        "preflight_id": d150.get("preflight_id"),
        "intent_id": d150.get("intent_id"),
        "candidate_id": d150.get("candidate_id"),
        "proposal_id": d150.get("proposal_id"),
    })

    run_result = build_run_result(run_apply_id, d150)
    safety_receipt = build_safety_receipt(run_apply_id, d150)
    d152_scope = build_d152_scope(run_apply_id, d150)

    for item_name, item in [
        ("run_result", run_result),
        ("safety_receipt", safety_receipt),
        ("d152_scope", d152_scope),
    ]:
        for key in [
            "actual_apply_executed",
            "real_apply_executed",
            "actual_apply_executed_by_ai",
            "real_apply_executed_by_ai",
            "route_inserted",
            "protected_core_mutated",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "real_apply_allowed_after_d151_by_ai",
            "route_insert_allowed_after_d151_by_ai",
            "protected_core_mutation_allowed_after_d151_by_ai",
            "network_allowed_after_d151_by_ai",
            "secret_read_allowed_after_d151_by_ai",
            "shell_allowed_after_d151_by_ai",
            "git_action_allowed_after_d151_by_ai",
        ]:
            if key in item and item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_BLOCKED"
    result = "D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_CREATED" if ok else "D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_BLOCKED"

    if ok:
        write_json(root / RUN_RESULT_OUT, run_result)
        write_json(root / SAFETY_RECEIPT_OUT, safety_receipt)
        write_json(root / D152_SCOPE_OUT, d152_scope)

    report = {
        "state": "D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "run_apply_id": run_apply_id,
        "signature_id": d150.get("signature_id"),
        "preflight_id": d150.get("preflight_id"),
        "intent_id": d150.get("intent_id"),
        "decision_id": d150.get("decision_id"),
        "archive_id": d150.get("archive_id"),
        "verification_id": d150.get("verification_id"),
        "apply_id": d150.get("apply_id"),
        "run_id": d150.get("run_id"),
        "candidate_id": d150.get("candidate_id"),
        "proposal_id": d150.get("proposal_id"),
        "source_d150_report": D150_REPORT,
        "real_apply_run_result": run_result if ok else {},
        "real_apply_run_safety_receipt": safety_receipt if ok else {},
        "d152_scope": d152_scope if ok else {},
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
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "sandbox_candidate_guarded_real_apply_run_scope_only": True,
            "real_apply_run_result_only": True,
            "real_apply_run_safety_receipt_only": True,
            "approval_for_d152_post_real_apply_verification_scope_only": ok,
            "approval_for_real_core_apply_by_ai": False,
            "real_apply_allowed_after_d151_by_ai": False,
            "route_insert_allowed_after_d151_by_ai": False,
            "protected_core_mutation_allowed_after_d151_by_ai": False,
            "network_allowed_after_d151_by_ai": False,
            "secret_read_allowed_after_d151_by_ai": False,
            "shell_allowed_after_d151_by_ai": False,
            "git_action_allowed_after_d151_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "run_apply_id": run_apply_id,
            "signature_id": d150.get("signature_id"),
            "preflight_id": d150.get("preflight_id"),
            "intent_id": d150.get("intent_id"),
            "candidate_id": d150.get("candidate_id"),
            "proposal_id": d150.get("proposal_id"),
            "real_apply_run_status": "GUARDED_REAL_APPLY_RUN_SCOPE_RECORDED_NO_AI_CORE_MUTATION" if ok else "BLOCKED",
            "safety_receipt_status": "AI_DID_NOT_EXECUTE_REAL_CORE_APPLY" if ok else "BLOCKED",
            "candidate_status": "REAL_APPLY_RUN_SCOPE_RECORDED_POST_VERIFICATION_REQUIRED_NOT_CORE_MUTATED_BY_AI" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D152_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "guarded_real_apply_run_scope_created": ok,
            "real_apply_run_result_created": ok,
            "real_apply_run_safety_receipt_created": ok,
            "d152_scope_created": ok,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D152 may create post real apply verification scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_guarded_real_apply_run_scope(), ensure_ascii=False, indent=2))
