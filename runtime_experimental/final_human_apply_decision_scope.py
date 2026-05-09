
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D113_REPORT = "reports/d113_final_apply_review_scope.json"
D113_EVIDENCE = "reports/d113_final_apply_evidence_packet.json"
D113_BLOCKER_MATRIX = "reports/d113_final_apply_blocker_matrix.json"
D113_D114_SCOPE = "reports/d113_d114_final_human_apply_decision_scope.json"

OUT = "reports/d114_final_human_apply_decision_scope.json"
PERMISSION_MATRIX_OUT = "reports/d114_final_apply_permission_matrix.json"
OPERATOR_STATEMENT_OUT = "reports/d114_final_operator_decision_statement.json"
D115_SCOPE_OUT = "reports/d114_d115_final_apply_phrase_scope.json"

REQ_D113_DECISION = "FINAL_APPLY_REVIEW_SCOPE_READY"
REQ_D114_GATE = "D114_FINAL_HUMAN_APPLY_DECISION_SCOPE"
REQ_D115_GATE = "D115_FINAL_APPLY_PHRASE_SCOPE"

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

BLOCKED_PREFIXES = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
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


def validate_d113(d113, evidence, blocker_matrix, d114_scope):
    errors = []

    if not d113:
        errors.append("missing D113 final apply review scope report")
        return errors

    if d113.get("ok") is not True:
        errors.append("D113 ok must be true")
    if d113.get("decision") != REQ_D113_DECISION:
        errors.append("D113 decision must be FINAL_APPLY_REVIEW_SCOPE_READY")

    guard = d113.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D113 guardrails.{key} must be false")
    if guard.get("final_apply_review_only") is not True:
        errors.append("D113 final_apply_review_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D113 approval_for_real_apply must be false")
    if guard.get("candidate_execution_allowed") is not False:
        errors.append("D113 candidate_execution_allowed must be false")

    summary = d113.get("summary", {})
    if summary.get("real_apply_current_status") != "BLOCKED":
        errors.append("D113 real_apply_current_status must be BLOCKED")
    if summary.get("next_step") != REQ_D114_GATE:
        errors.append("D113 summary next_step must be D114")

    if not evidence:
        errors.append("missing D113 evidence packet")
    else:
        if evidence.get("ok") is not True:
            errors.append("D113 evidence packet ok must be true")
        if evidence.get("review_mode") != "FINAL_APPLY_REVIEW_ONLY":
            errors.append("D113 evidence review_mode must be final-review-only")
        for key in ["actual_apply_executed", "candidate_executed", "approval_for_real_apply"]:
            if evidence.get(key) is not False:
                errors.append(f"D113 evidence {key} must be false")
        dry = evidence.get("dry_run_summary", {})
        if dry.get("patch_applied") is not False:
            errors.append("D113 evidence dry_run_summary.patch_applied must be false")
        if dry.get("files_mutated") not in ([], None):
            errors.append("D113 evidence dry_run_summary.files_mutated must be empty")
        for path in dry.get("candidate_files", []):
            if starts(str(path), BLOCKED_PREFIXES):
                errors.append(f"D113 evidence contains blocked candidate path: {path}")

    if not blocker_matrix:
        errors.append("missing D113 blocker matrix")
    else:
        if blocker_matrix.get("ok") is not True:
            errors.append("D113 blocker matrix ok must be true")
        if blocker_matrix.get("real_apply_current_status") != "BLOCKED":
            errors.append("D113 blocker matrix real apply status must be BLOCKED")
        if blocker_matrix.get("blocked_until") != REQ_D114_GATE:
            errors.append("D113 blocker matrix blocked_until must be D114")
        mf = blocker_matrix.get("must_remain_false", {})
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
                errors.append(f"D113 blocker matrix must_remain_false.{key} must be false")

    if not d114_scope:
        errors.append("missing D113 D114 final human apply decision scope")
    else:
        if d114_scope.get("ok") is not True:
            errors.append("D113 D114 scope ok must be true")
        if d114_scope.get("allowed_next_gate") != REQ_D114_GATE:
            errors.append("D113 D114 scope allowed_next_gate must be D114")
        if d114_scope.get("final_human_decision_only") is not True:
            errors.append("D113 D114 scope final_human_decision_only must be true")
        if d114_scope.get("human_review_required") is not True:
            errors.append("D113 D114 scope human_review_required must be true")
        for key in [
            "actual_apply_allowed_after_d113",
            "route_insert_allowed_after_d113",
            "protected_core_mutation_allowed_after_d113",
            "sandbox_candidate_execution_allowed_after_d113",
        ]:
            if d114_scope.get(key) is not False:
                errors.append(f"D113 D114 scope {key} must be false")

    return errors


def build_permission_matrix(decision_id, d113, evidence, blocker_matrix):
    return {
        "state": "D114_FINAL_APPLY_PERMISSION_MATRIX",
        "ok": True,
        "decision_id": decision_id,
        "review_id": d113.get("review_id"),
        "dry_run_id": d113.get("dry_run_id"),
        "proposal_id": d113.get("proposal_id"),
        "created_at": now(),
        "real_apply_permission": "NOT_GRANTED",
        "d115_phrase_scope_permission": "GRANTED_FOR_PHRASE_SCOPE_ONLY",
        "permissions": {
            "create_d115_final_apply_phrase_scope": True,
            "prepare_final_apply_phrase_text": True,
            "prepare_operator_final_decision_statement": True,
            "real_apply_now": False,
            "auto_apply_now": False,
            "route_insert_now": False,
            "protected_core_mutation_now": False,
            "canonical_memory_overwrite_now": False,
            "external_ai_or_network_call_now": False,
            "sandbox_candidate_execution_now": False,
            "ai_git_commit_or_push_now": False,
        },
        "still_blocked": [
            "real_apply",
            "auto_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "sandbox_candidate_execution",
            "git_commit_or_push_by_ai",
        ],
        "evidence_files": evidence.get("evidence_files", {}),
        "blockers_carried_forward": blocker_matrix.get("blockers", {}),
    }


def build_operator_statement(decision_id, permission_matrix):
    return {
        "state": "D114_FINAL_OPERATOR_DECISION_STATEMENT",
        "ok": True,
        "decision_id": decision_id,
        "created_at": now(),
        "human_decision_scope": "D115_FINAL_APPLY_PHRASE_SCOPE_ONLY",
        "operator_statement": (
            "I approve only the creation of the D115 final apply phrase scope. "
            "This does not execute real apply and does not authorize route insertion, "
            "protected-core mutation, canonical memory overwrite, external AI/network calls, "
            "sandbox candidate execution, rollback/restore, or AI git actions."
        ),
        "real_apply_approved_now": False,
        "d115_phrase_scope_approved": True,
        "actual_apply_executed": False,
        "candidate_executed": False,
    }


def build_d115_scope(decision_id, d113):
    return {
        "state": "D114_D115_FINAL_APPLY_PHRASE_SCOPE",
        "ok": True,
        "decision_id": decision_id,
        "review_id": d113.get("review_id"),
        "dry_run_id": d113.get("dry_run_id"),
        "proposal_id": d113.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D115_GATE,
        "d115_allowed_to_create": [
            "final_apply_phrase_scope",
            "final_apply_phrase_statement",
            "final_pre_apply_lock_report",
            "d116_manual_apply_window_scope",
        ],
        "d115_must_not_execute": [
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
        "final_phrase_scope_only": True,
        "human_review_required": True,
        "actual_apply_allowed_after_d114": False,
        "route_insert_allowed_after_d114": False,
        "protected_core_mutation_allowed_after_d114": False,
        "sandbox_candidate_execution_allowed_after_d114": False,
        "required_phrase_for_later_gate": "APPROVE_D115_FINAL_APPLY_PHRASE_SCOPE_ONLY",
    }


def create_final_human_apply_decision_scope(root="."):
    root = Path(root).resolve()

    d113 = read_json(root / D113_REPORT, {}) or {}
    evidence = read_json(root / D113_EVIDENCE, {}) or {}
    blocker_matrix = read_json(root / D113_BLOCKER_MATRIX, {}) or {}
    d114_scope = read_json(root / D113_D114_SCOPE, {}) or {}

    errors = validate_d113(d113, evidence, blocker_matrix, d114_scope)

    decision_id = "d114-" + digest({
        "review_id": d113.get("review_id"),
        "dry_run_id": d113.get("dry_run_id"),
        "proposal_id": d113.get("proposal_id"),
    })

    permission_matrix = build_permission_matrix(decision_id, d113, evidence, blocker_matrix)
    operator_statement = build_operator_statement(decision_id, permission_matrix)
    d115_scope = build_d115_scope(decision_id, d113)

    ok = not errors
    decision = "FINAL_HUMAN_APPLY_DECISION_SCOPE_READY" if ok else "FINAL_HUMAN_APPLY_DECISION_SCOPE_BLOCKED"
    result = "D114_FINAL_HUMAN_APPLY_DECISION_SCOPE_CREATED" if ok else "D114_FINAL_HUMAN_APPLY_DECISION_SCOPE_BLOCKED"

    if ok:
        write_json(root / PERMISSION_MATRIX_OUT, permission_matrix)
        write_json(root / OPERATOR_STATEMENT_OUT, operator_statement)
        write_json(root / D115_SCOPE_OUT, d115_scope)

    report = {
        "state": "D114_FINAL_HUMAN_APPLY_DECISION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_FINAL_HUMAN_APPLY_DECISION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "decision_id": decision_id,
        "review_id": d113.get("review_id"),
        "dry_run_id": d113.get("dry_run_id"),
        "proposal_id": d113.get("proposal_id"),
        "source_d113_report": D113_REPORT,
        "permission_matrix": permission_matrix if ok else {},
        "operator_decision_statement": operator_statement if ok else {},
        "d115_scope": d115_scope if ok else {},
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
            "final_human_decision_only": True,
            "approval_for_d115_phrase_scope_only": ok,
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
            "decision_id": decision_id,
            "review_id": d113.get("review_id"),
            "proposal_id": d113.get("proposal_id"),
            "real_apply_current_status": "BLOCKED",
            "approval_scope": "D115_FINAL_APPLY_PHRASE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D115_GATE,
        },
        "success_condition": {
            "final_human_apply_decision_scope_created": ok,
            "permission_matrix_created": ok,
            "operator_decision_statement_created": ok,
            "d115_scope_created": ok,
            "approval_for_d115_phrase_scope_only": ok,
            "approval_for_real_apply": False,
            "real_ai_called": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "protected_core_untouched": True,
            "next_step": "D115 may create final apply phrase scope only. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_final_human_apply_decision_scope(), ensure_ascii=False, indent=2))
