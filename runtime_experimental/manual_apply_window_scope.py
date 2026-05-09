
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D115_REPORT = "reports/d115_final_apply_phrase_scope.json"
D115_PHRASE_STATEMENT = "reports/d115_final_apply_phrase_statement.json"
D115_PRE_APPLY_LOCK = "reports/d115_final_pre_apply_lock_report.json"
D115_D116_SCOPE = "reports/d115_d116_manual_apply_window_scope.json"

OUT = "reports/d116_manual_apply_window_scope.json"
PREFLIGHT_OUT = "reports/d116_manual_apply_preflight_checklist.json"
COMMAND_PACKET_OUT = "reports/d116_operator_local_command_packet.json"
D117_SCOPE_OUT = "reports/d116_d117_manual_apply_command_review_scope.json"

REQ_D115_DECISION = "FINAL_APPLY_PHRASE_SCOPE_READY"
REQ_D116_GATE = "D116_MANUAL_APPLY_WINDOW_SCOPE"
REQ_D117_GATE = "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE"
REQ_D115_APPROVAL_SCOPE = "D116_MANUAL_APPLY_WINDOW_SCOPE_ONLY"
D116_REQUIRED_PHRASE = "APPROVE_D116_MANUAL_APPLY_WINDOW_SCOPE_ONLY"

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


def validate_d115(d115, phrase_statement, pre_apply_lock, d116_scope):
    errors = []

    if not d115:
        errors.append("missing D115 final apply phrase scope report")
        return errors

    if d115.get("ok") is not True:
        errors.append("D115 ok must be true")
    if d115.get("decision") != REQ_D115_DECISION:
        errors.append("D115 decision must be FINAL_APPLY_PHRASE_SCOPE_READY")

    guard = d115.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D115 guardrails.{key} must be false")
    if guard.get("final_phrase_scope_only") is not True:
        errors.append("D115 final_phrase_scope_only must be true")
    if guard.get("approval_for_d116_manual_window_only") is not True:
        errors.append("D115 approval_for_d116_manual_window_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D115 approval_for_real_apply must be false")
    if guard.get("candidate_execution_allowed") is not False:
        errors.append("D115 candidate_execution_allowed must be false")

    summary = d115.get("summary", {})
    if summary.get("real_apply_current_status") != "BLOCKED":
        errors.append("D115 real_apply_current_status must be BLOCKED")
    if summary.get("approval_scope") != REQ_D115_APPROVAL_SCOPE:
        errors.append("D115 approval_scope must be D116 manual window only")
    if summary.get("next_step") != REQ_D116_GATE:
        errors.append("D115 summary next_step must be D116")

    if not phrase_statement:
        errors.append("missing D115 final apply phrase statement")
    else:
        if phrase_statement.get("ok") is not True:
            errors.append("D115 phrase statement ok must be true")
        if phrase_statement.get("phrase_scope") != REQ_D115_APPROVAL_SCOPE:
            errors.append("D115 phrase statement scope must be D116 manual window only")
        if phrase_statement.get("required_phrase") != D116_REQUIRED_PHRASE:
            errors.append("D115 phrase statement required phrase mismatch")
        if phrase_statement.get("real_apply_approved_now") is not False:
            errors.append("D115 phrase statement real_apply_approved_now must be false")
        for key in ["actual_apply_executed", "candidate_executed"]:
            if phrase_statement.get(key) is not False:
                errors.append(f"D115 phrase statement {key} must be false")

    if not pre_apply_lock:
        errors.append("missing D115 final pre-apply lock report")
    else:
        if pre_apply_lock.get("ok") is not True:
            errors.append("D115 pre-apply lock ok must be true")
        if pre_apply_lock.get("lock_state") != "REAL_APPLY_STILL_LOCKED":
            errors.append("D115 pre-apply lock state must be REAL_APPLY_STILL_LOCKED")
        if pre_apply_lock.get("real_apply_permission") != "NOT_GRANTED":
            errors.append("D115 pre-apply lock real_apply_permission must be NOT_GRANTED")
        if pre_apply_lock.get("real_apply_approved_now") is not False:
            errors.append("D115 pre-apply lock real_apply_approved_now must be false")
        mf = pre_apply_lock.get("must_remain_false", {})
        for key in [
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "external_ai_called",
            "network_accessed",
            "candidate_executed",
            "git_commit_by_ai",
            "git_push_by_ai",
        ]:
            if mf.get(key) is not False:
                errors.append(f"D115 pre-apply lock must_remain_false.{key} must be false")

    if not d116_scope:
        errors.append("missing D115 D116 manual apply window scope")
    else:
        if d116_scope.get("ok") is not True:
            errors.append("D115 D116 scope ok must be true")
        if d116_scope.get("allowed_next_gate") != REQ_D116_GATE:
            errors.append("D115 D116 scope allowed_next_gate must be D116")
        if d116_scope.get("manual_apply_window_scope_only") is not True:
            errors.append("D115 D116 scope manual_apply_window_scope_only must be true")
        if d116_scope.get("human_review_required") is not True:
            errors.append("D115 D116 scope human_review_required must be true")
        if d116_scope.get("required_phrase_for_later_gate") != D116_REQUIRED_PHRASE:
            errors.append("D115 D116 scope required phrase mismatch")
        for key in [
            "actual_apply_allowed_after_d115",
            "route_insert_allowed_after_d115",
            "protected_core_mutation_allowed_after_d115",
            "sandbox_candidate_execution_allowed_after_d115",
        ]:
            if d116_scope.get(key) is not False:
                errors.append(f"D115 D116 scope {key} must be false")

    return errors


def build_preflight_checklist(window_id, d115, phrase_statement, pre_apply_lock):
    return {
        "state": "D116_MANUAL_APPLY_PREFLIGHT_CHECKLIST",
        "ok": True,
        "window_id": window_id,
        "phrase_id": d115.get("phrase_id"),
        "decision_id": d115.get("decision_id"),
        "proposal_id": d115.get("proposal_id"),
        "created_at": now(),
        "manual_window_mode": "LOCAL_OPERATOR_REVIEW_ONLY",
        "required_phrase_from_d115": phrase_statement.get("required_phrase"),
        "lock_state": pre_apply_lock.get("lock_state"),
        "preflight_items": [
            "Confirm D115 final phrase scope exists",
            "Confirm real apply is still locked",
            "Confirm command packet is documentation-only",
            "Confirm operator must run commands manually, not AI",
            "Confirm no shell command is executed by this module",
            "Confirm no route insertion is performed",
            "Confirm no protected-core mutation is performed",
            "Confirm rollback/restore is not executed automatically",
            "Prepare D117 manual apply command review scope only",
        ],
        "must_remain_false": {
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "candidate_executed": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
        },
        "actual_apply_executed": False,
        "candidate_executed": False,
    }


def build_operator_command_packet(window_id, d115):
    return {
        "state": "D116_OPERATOR_LOCAL_COMMAND_PACKET",
        "ok": True,
        "window_id": window_id,
        "phrase_id": d115.get("phrase_id"),
        "decision_id": d115.get("decision_id"),
        "proposal_id": d115.get("proposal_id"),
        "created_at": now(),
        "packet_mode": "DOCUMENTATION_ONLY_NOT_EXECUTED",
        "commands_are_not_executed_by_ai": True,
        "human_may_run_manually_after_d117": True,
        "commands": [
            "git status --short",
            "python -m unittest discover -s tests -v",
            "python -m py_compile runtime_experimental/*.py",
            "cat reports/d115_final_pre_apply_lock_report.json",
            "cat reports/d116_manual_apply_preflight_checklist.json",
            "git diff --stat",
        ],
        "blocked_commands": [
            "git apply",
            "git commit",
            "git push",
            "route insert",
            "direct protected-core edit",
            "execute sandbox candidate",
            "rollback execute",
            "restore execute",
            "external AI/network call",
        ],
        "real_apply_command_included": False,
        "shell_executed_by_ai": False,
        "actual_apply_executed": False,
        "candidate_executed": False,
    }


def build_d117_scope(window_id, d115):
    return {
        "state": "D116_D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE",
        "ok": True,
        "window_id": window_id,
        "phrase_id": d115.get("phrase_id"),
        "decision_id": d115.get("decision_id"),
        "review_id": d115.get("review_id"),
        "dry_run_id": d115.get("dry_run_id"),
        "proposal_id": d115.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D117_GATE,
        "d117_allowed_to_create": [
            "manual_apply_command_review_scope",
            "reviewed_operator_command_packet",
            "manual_apply_ready_or_blocked_record",
            "d118_operator_local_execution_evidence_scope",
        ],
        "d117_must_not_execute": [
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
        "manual_command_review_only": True,
        "human_review_required": True,
        "actual_apply_allowed_after_d116": False,
        "route_insert_allowed_after_d116": False,
        "protected_core_mutation_allowed_after_d116": False,
        "sandbox_candidate_execution_allowed_after_d116": False,
        "required_phrase_for_later_gate": "APPROVE_D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE_ONLY",
    }


def create_manual_apply_window_scope(root="."):
    root = Path(root).resolve()

    d115 = read_json(root / D115_REPORT, {}) or {}
    phrase_statement = read_json(root / D115_PHRASE_STATEMENT, {}) or {}
    pre_apply_lock = read_json(root / D115_PRE_APPLY_LOCK, {}) or {}
    d116_scope = read_json(root / D115_D116_SCOPE, {}) or {}

    errors = validate_d115(d115, phrase_statement, pre_apply_lock, d116_scope)

    window_id = "d116-" + digest({
        "phrase_id": d115.get("phrase_id"),
        "decision_id": d115.get("decision_id"),
        "proposal_id": d115.get("proposal_id"),
    })

    preflight = build_preflight_checklist(window_id, d115, phrase_statement, pre_apply_lock)
    command_packet = build_operator_command_packet(window_id, d115)
    d117_scope = build_d117_scope(window_id, d115)

    if command_packet.get("real_apply_command_included") is not False:
        errors.append("operator command packet must not include real apply command")
    if command_packet.get("shell_executed_by_ai") is not False:
        errors.append("operator command packet shell_executed_by_ai must be false")
    if command_packet.get("actual_apply_executed") is not False:
        errors.append("operator command packet actual_apply_executed must be false")

    ok = not errors
    decision = "MANUAL_APPLY_WINDOW_SCOPE_READY" if ok else "MANUAL_APPLY_WINDOW_SCOPE_BLOCKED"
    result = "D116_MANUAL_APPLY_WINDOW_SCOPE_CREATED" if ok else "D116_MANUAL_APPLY_WINDOW_SCOPE_BLOCKED"

    if ok:
        write_json(root / PREFLIGHT_OUT, preflight)
        write_json(root / COMMAND_PACKET_OUT, command_packet)
        write_json(root / D117_SCOPE_OUT, d117_scope)

    report = {
        "state": "D116_MANUAL_APPLY_WINDOW_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_MANUAL_APPLY_WINDOW_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "window_id": window_id,
        "phrase_id": d115.get("phrase_id"),
        "decision_id": d115.get("decision_id"),
        "review_id": d115.get("review_id"),
        "dry_run_id": d115.get("dry_run_id"),
        "proposal_id": d115.get("proposal_id"),
        "source_d115_report": D115_REPORT,
        "manual_apply_preflight_checklist": preflight if ok else {},
        "operator_local_command_packet": command_packet if ok else {},
        "d117_scope": d117_scope if ok else {},
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
            "manual_apply_window_scope_only": True,
            "operator_command_packet_documentation_only": True,
            "approval_for_d117_command_review_only": ok,
            "approval_for_real_apply": False,
            "candidate_execution_allowed": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": [],
        },
        "summary": {
            "decision": decision,
            "window_id": window_id,
            "phrase_id": d115.get("phrase_id"),
            "proposal_id": d115.get("proposal_id"),
            "real_apply_current_status": "BLOCKED",
            "approval_scope": "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D117_GATE,
        },
        "success_condition": {
            "manual_apply_window_scope_created": ok,
            "preflight_checklist_created": ok,
            "operator_command_packet_created": ok,
            "d117_scope_created": ok,
            "approval_for_d117_command_review_only": ok,
            "approval_for_real_apply": False,
            "real_ai_called": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "protected_core_untouched": True,
            "next_step": "D117 may review manual operator command packet only. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_manual_apply_window_scope(), ensure_ascii=False, indent=2))
