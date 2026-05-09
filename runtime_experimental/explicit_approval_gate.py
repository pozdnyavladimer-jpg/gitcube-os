
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D110_REPORT = "reports/d110_human_review_gate.json"
D110_PACKET = "reports/d110_human_review_packet.json"
D110_REVIEW_SUMMARY = "reports/d110_proposal_review_summary.json"
D110_APPROVAL_RECORD = "reports/d110_approval_or_rejection_record.json"
D110_D111_SCOPE = "reports/d110_d111_explicit_approval_gate_scope.json"

OUT = "reports/d111_explicit_approval_gate.json"
APPROVAL_STATEMENT_OUT = "reports/d111_explicit_approval_statement.json"
OPERATOR_DECISION_OUT = "reports/d111_operator_decision_record.json"
D112_SCOPE_OUT = "reports/d111_d112_dry_run_apply_scope.json"

REQ_D110_DECISION = "HUMAN_REVIEW_GATE_READY"
REQ_D111_GATE = "D111_EXPLICIT_APPROVAL_GATE"
REQ_D112_GATE = "D112_DRY_RUN_APPLY_SCOPE"
APPROVAL_PHRASE = "APPROVE_D111_EXPLICIT_APPROVAL_GATE_ONLY"

BLOCKED_PREFIXES = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]

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


def starts(path, prefixes):
    return any(str(path).startswith(prefix) for prefix in prefixes)


def validate_d110(d110, packet, review_summary, approval_record, d111_scope):
    errors = []

    if not d110:
        errors.append("missing D110 human review gate report")
        return errors

    if d110.get("ok") is not True:
        errors.append("D110 ok must be true")
    if d110.get("decision") != REQ_D110_DECISION:
        errors.append("D110 decision must be HUMAN_REVIEW_GATE_READY")

    guard = d110.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D110 guardrails.{key} must be false")
    if guard.get("human_review_packet_only") is not True:
        errors.append("D110 guardrails.human_review_packet_only must be true")
    if guard.get("approval_granted") is not False:
        errors.append("D110 guardrails.approval_granted must be false")
    if guard.get("candidate_execution_allowed") is not False:
        errors.append("D110 guardrails.candidate_execution_allowed must be false")

    summary = d110.get("summary", {})
    if summary.get("approval_state") != "PENDING_HUMAN_DECISION":
        errors.append("D110 approval_state must be pending human decision")
    if summary.get("next_step") != REQ_D111_GATE:
        errors.append("D110 summary next_step must be D111")

    if not packet:
        errors.append("missing D110 human review packet")
    else:
        if packet.get("ok") is not True:
            errors.append("D110 packet ok must be true")
        if packet.get("review_mode") != "HUMAN_DECISION_PACKET_ONLY":
            errors.append("D110 packet review_mode invalid")
        if packet.get("approval_granted") is not False:
            errors.append("D110 packet approval_granted must be false")
        for key in ["actual_apply_executed", "candidate_executed"]:
            if packet.get(key) is not False:
                errors.append(f"D110 packet {key} must be false")
        if "PREPARE_D111_EXPLICIT_APPROVAL_GATE_ONLY" not in packet.get("human_decision_options", []):
            errors.append("D110 packet missing D111 prepare option")

    if not review_summary:
        errors.append("missing D110 proposal review summary")
    else:
        if review_summary.get("ok") is not True:
            errors.append("D110 review summary ok must be true")
        if review_summary.get("requires_human_review") is not True:
            errors.append("D110 review summary requires_human_review must be true")
        if review_summary.get("approval_granted") is not False:
            errors.append("D110 review summary approval_granted must be false")
        for key in ["actual_apply_executed", "candidate_executed", "protected_core_mutated", "route_inserted"]:
            if review_summary.get(key) is not False:
                errors.append(f"D110 review summary {key} must be false")
        for path in review_summary.get("candidate_files", []):
            if starts(str(path), BLOCKED_PREFIXES):
                errors.append(f"D110 review summary contains blocked candidate path: {path}")

    if not approval_record:
        errors.append("missing D110 approval/rejection record")
    else:
        if approval_record.get("ok") is not True:
            errors.append("D110 approval record ok must be true")
        if approval_record.get("decision_state") != "PENDING_HUMAN_DECISION":
            errors.append("D110 approval record decision_state must be pending")
        if approval_record.get("approval_granted_now") is not False:
            errors.append("D110 approval record approval_granted_now must be false")
        if approval_record.get("rejection_recorded_now") is not False:
            errors.append("D110 approval record rejection_recorded_now must be false")
        if approval_record.get("human_phrase_required_for_later_gate") != APPROVAL_PHRASE:
            errors.append("D110 approval record required phrase mismatch")
        for key in ["actual_apply_executed", "candidate_executed"]:
            if approval_record.get(key) is not False:
                errors.append(f"D110 approval record {key} must be false")

    if not d111_scope:
        errors.append("missing D110 D111 explicit approval gate scope")
    else:
        if d111_scope.get("ok") is not True:
            errors.append("D110 D111 scope ok must be true")
        if d111_scope.get("allowed_next_gate") != REQ_D111_GATE:
            errors.append("D110 D111 scope allowed_next_gate must be D111")
        if d111_scope.get("human_review_required") is not True:
            errors.append("D110 D111 scope human_review_required must be true")
        if d111_scope.get("required_phrase_for_later_gate") != APPROVAL_PHRASE:
            errors.append("D110 D111 scope required phrase mismatch")
        for key in [
            "actual_apply_allowed_after_d110",
            "route_insert_allowed_after_d110",
            "protected_core_mutation_allowed_after_d110",
            "sandbox_candidate_execution_allowed_after_d110",
        ]:
            if d111_scope.get(key) is not False:
                errors.append(f"D110 D111 scope {key} must be false")

    return errors


def build_approval_statement(approval_id, d110, review_summary, operator_phrase):
    return {
        "state": "D111_EXPLICIT_APPROVAL_STATEMENT",
        "ok": True,
        "approval_id": approval_id,
        "gate_id": d110.get("gate_id"),
        "proposal_id": review_summary.get("proposal_id") or d110.get("proposal_id"),
        "created_at": now(),
        "operator_phrase": operator_phrase,
        "approval_scope": "D112_DRY_RUN_APPLY_SCOPE_ONLY",
        "human_statement": (
            "I approve only the creation of the D112 dry-run apply scope. "
            "This does not approve real apply, route insertion, protected-core mutation, "
            "canonical memory overwrite, external AI/network calls, candidate execution, "
            "or AI git actions."
        ),
        "explicitly_not_approved": [
            "real_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "sandbox_candidate_execution",
            "git_commit_or_push_by_ai",
        ],
        "actual_apply_executed": False,
        "candidate_executed": False,
        "approval_for_real_apply": False,
    }


def build_operator_decision(approval_id, approval_statement):
    return {
        "state": "D111_OPERATOR_DECISION_RECORD",
        "ok": True,
        "approval_id": approval_id,
        "created_at": now(),
        "decision": "APPROVED_FOR_D112_DRY_RUN_SCOPE_ONLY",
        "operator_phrase_matched": approval_statement.get("operator_phrase") == APPROVAL_PHRASE,
        "approval_scope": approval_statement.get("approval_scope"),
        "not_approved": approval_statement.get("explicitly_not_approved", []),
        "actual_apply_executed": False,
        "candidate_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "approval_for_real_apply": False,
    }


def build_d112_scope(approval_id, review_summary):
    return {
        "state": "D111_D112_DRY_RUN_APPLY_SCOPE",
        "ok": True,
        "approval_id": approval_id,
        "proposal_id": review_summary.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D112_GATE,
        "d112_allowed_to_create": [
            "dry_run_apply_scope",
            "dry_run_plan",
            "dry_run_patch_preview",
            "dry_run_no_touch_verification",
            "d113_final_apply_review_scope",
        ],
        "d112_must_not_execute": [
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
        "dry_run_only": True,
        "human_review_required": True,
        "actual_apply_allowed_after_d111": False,
        "route_insert_allowed_after_d111": False,
        "protected_core_mutation_allowed_after_d111": False,
        "sandbox_candidate_execution_allowed_after_d111": False,
        "required_phrase_for_later_gate": "APPROVE_D112_DRY_RUN_APPLY_SCOPE_ONLY",
    }


def create_explicit_approval_gate(root=".", operator_phrase=APPROVAL_PHRASE):
    root = Path(root).resolve()

    d110 = read_json(root / D110_REPORT, {}) or {}
    packet = read_json(root / D110_PACKET, {}) or {}
    review_summary = read_json(root / D110_REVIEW_SUMMARY, {}) or {}
    approval_record = read_json(root / D110_APPROVAL_RECORD, {}) or {}
    d111_scope = read_json(root / D110_D111_SCOPE, {}) or {}

    errors = validate_d110(d110, packet, review_summary, approval_record, d111_scope)

    if operator_phrase != APPROVAL_PHRASE:
        errors.append("operator phrase does not match D111 explicit approval phrase")

    approval_id = "d111-" + digest({
        "gate_id": d110.get("gate_id"),
        "runner_id": d110.get("runner_id"),
        "proposal_id": review_summary.get("proposal_id") or d110.get("proposal_id"),
        "operator_phrase": operator_phrase,
    })

    ok = not errors
    decision = "EXPLICIT_APPROVAL_GATE_READY" if ok else "EXPLICIT_APPROVAL_GATE_BLOCKED"
    result = "D111_EXPLICIT_APPROVAL_GATE_CREATED" if ok else "D111_EXPLICIT_APPROVAL_GATE_BLOCKED"

    approval_statement = build_approval_statement(approval_id, d110, review_summary, operator_phrase)
    operator_decision = build_operator_decision(approval_id, approval_statement)
    d112_scope = build_d112_scope(approval_id, review_summary)

    if ok:
        write_json(root / APPROVAL_STATEMENT_OUT, approval_statement)
        write_json(root / OPERATOR_DECISION_OUT, operator_decision)
        write_json(root / D112_SCOPE_OUT, d112_scope)

    report = {
        "state": "D111_EXPLICIT_APPROVAL_GATE",
        "result": result,
        "route": "FIELD_INTENT_EXPLICIT_APPROVAL_GATE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "approval_id": approval_id,
        "gate_id": d110.get("gate_id"),
        "runner_id": d110.get("runner_id"),
        "proposal_id": review_summary.get("proposal_id") or d110.get("proposal_id"),
        "source_d110_report": D110_REPORT,
        "approval_statement": approval_statement if ok else {},
        "operator_decision_record": operator_decision if ok else {},
        "d112_scope": d112_scope if ok else {},
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
            "rollback_executed": False,
            "restore_executed": False,
            "explicit_approval_gate_only": True,
            "approval_for_d112_dry_run_only": ok,
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
            "approval_id": approval_id,
            "gate_id": d110.get("gate_id"),
            "proposal_id": review_summary.get("proposal_id") or d110.get("proposal_id"),
            "approval_scope": "D112_DRY_RUN_APPLY_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D112_GATE,
        },
        "success_condition": {
            "explicit_approval_gate_created": ok,
            "approval_statement_created": ok,
            "operator_decision_record_created": ok,
            "d112_scope_created": ok,
            "approval_for_d112_dry_run_only": ok,
            "approval_for_real_apply": False,
            "real_ai_called": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "protected_core_untouched": True,
            "next_step": "D112 may create dry-run apply scope only. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_explicit_approval_gate(), ensure_ascii=False, indent=2))
