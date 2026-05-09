
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D112_REPORT = "reports/d112_dry_run_apply_scope.json"
D112_PLAN = "reports/d112_dry_run_plan.json"
D112_PATCH_PREVIEW = "reports/d112_dry_run_patch_preview.json"
D112_NO_TOUCH = "reports/d112_no_touch_verification.json"
D112_D113_SCOPE = "reports/d112_d113_final_apply_review_scope.json"

OUT = "reports/d113_final_apply_review_scope.json"
EVIDENCE_PACKET_OUT = "reports/d113_final_apply_evidence_packet.json"
BLOCKER_MATRIX_OUT = "reports/d113_final_apply_blocker_matrix.json"
D114_SCOPE_OUT = "reports/d113_d114_final_human_apply_decision_scope.json"

REQ_D112_DECISION = "DRY_RUN_APPLY_SCOPE_READY"
REQ_D113_GATE = "D113_FINAL_APPLY_REVIEW_SCOPE"
REQ_D114_GATE = "D114_FINAL_HUMAN_APPLY_DECISION_SCOPE"

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


def starts(path, prefixes):
    return any(str(path).startswith(prefix) for prefix in prefixes)


def validate_d112(d112, plan, patch_preview, no_touch, d113_scope):
    errors = []

    if not d112:
        errors.append("missing D112 dry-run apply scope report")
        return errors

    if d112.get("ok") is not True:
        errors.append("D112 ok must be true")
    if d112.get("decision") != REQ_D112_DECISION:
        errors.append("D112 decision must be DRY_RUN_APPLY_SCOPE_READY")

    guard = d112.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D112 guardrails.{key} must be false")
    if guard.get("dry_run_only") is not True:
        errors.append("D112 guardrails.dry_run_only must be true")
    if guard.get("patch_generated") is not False:
        errors.append("D112 guardrails.patch_generated must be false")
    if guard.get("patch_applied") is not False:
        errors.append("D112 guardrails.patch_applied must be false")
    if guard.get("candidate_execution_allowed") is not False:
        errors.append("D112 guardrails.candidate_execution_allowed must be false")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D112 guardrails.approval_for_real_apply must be false")

    summary = d112.get("summary", {})
    if summary.get("dry_run_only") is not True:
        errors.append("D112 summary dry_run_only must be true")
    if summary.get("next_step") != REQ_D113_GATE:
        errors.append("D112 summary next_step must be D113")

    if not plan:
        errors.append("missing D112 dry-run plan")
    else:
        if plan.get("ok") is not True:
            errors.append("D112 dry-run plan ok must be true")
        if plan.get("dry_run_only") is not True:
            errors.append("D112 dry-run plan must be dry-run-only")
        for key in ["actual_apply_executed", "candidate_executed"]:
            if plan.get(key) is not False:
                errors.append(f"D112 dry-run plan {key} must be false")
        for path in plan.get("candidate_files", []):
            if starts(str(path), BLOCKED_PREFIXES):
                errors.append(f"D112 plan contains blocked candidate path: {path}")

    if not patch_preview:
        errors.append("missing D112 patch preview")
    else:
        if patch_preview.get("ok") is not True:
            errors.append("D112 patch preview ok must be true")
        if patch_preview.get("dry_run_only") is not True:
            errors.append("D112 patch preview must be dry-run-only")
        if patch_preview.get("patch_generated") is not False:
            errors.append("D112 patch preview patch_generated must be false")
        if patch_preview.get("patch_applied") is not False:
            errors.append("D112 patch preview patch_applied must be false")
        if patch_preview.get("files_mutated") not in ([], None):
            errors.append("D112 patch preview files_mutated must be empty")
        if patch_preview.get("blocked_path_hits"):
            errors.append("D112 patch preview blocked_path_hits must be empty")
        for key in ["actual_apply_executed", "candidate_executed"]:
            if patch_preview.get(key) is not False:
                errors.append(f"D112 patch preview {key} must be false")

    if not no_touch:
        errors.append("missing D112 no-touch verification")
    else:
        if no_touch.get("ok") is not True:
            errors.append("D112 no-touch verification ok must be true")
        if no_touch.get("safe_to_prepare_d113") is not True:
            errors.append("D112 no-touch safe_to_prepare_d113 must be true")
        if no_touch.get("blocked_path_hits"):
            errors.append("D112 no-touch blocked_path_hits must be empty")
        vf = no_touch.get("verified_false", {})
        for key in [
            "actual_apply_executed",
            "candidate_executed",
            "patch_applied",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "external_ai_called",
            "network_accessed",
            "git_commit_by_ai",
            "git_push_by_ai",
        ]:
            if vf.get(key) is not False:
                errors.append(f"D112 no-touch verified_false.{key} must be false")

    if not d113_scope:
        errors.append("missing D112 D113 final apply review scope")
    else:
        if d113_scope.get("ok") is not True:
            errors.append("D112 D113 scope ok must be true")
        if d113_scope.get("allowed_next_gate") != REQ_D113_GATE:
            errors.append("D112 D113 scope allowed_next_gate must be D113")
        if d113_scope.get("final_apply_review_only") is not True:
            errors.append("D112 D113 scope final_apply_review_only must be true")
        if d113_scope.get("human_review_required") is not True:
            errors.append("D112 D113 scope human_review_required must be true")
        for key in [
            "actual_apply_allowed_after_d112",
            "route_insert_allowed_after_d112",
            "protected_core_mutation_allowed_after_d112",
            "sandbox_candidate_execution_allowed_after_d112",
        ]:
            if d113_scope.get(key) is not False:
                errors.append(f"D112 D113 scope {key} must be false")

    return errors


def build_evidence_packet(review_id, d112, plan, patch_preview, no_touch):
    return {
        "state": "D113_FINAL_APPLY_EVIDENCE_PACKET",
        "ok": True,
        "review_id": review_id,
        "dry_run_id": d112.get("dry_run_id"),
        "approval_id": d112.get("approval_id"),
        "proposal_id": d112.get("proposal_id"),
        "created_at": now(),
        "review_mode": "FINAL_APPLY_REVIEW_ONLY",
        "evidence_files": {
            "d112_report": D112_REPORT,
            "dry_run_plan": D112_PLAN,
            "patch_preview": D112_PATCH_PREVIEW,
            "no_touch_verification": D112_NO_TOUCH,
            "d112_d113_scope": D112_D113_SCOPE,
        },
        "dry_run_summary": {
            "dry_run_only": plan.get("dry_run_only") is True,
            "candidate_files": plan.get("candidate_files", []),
            "patch_generated": patch_preview.get("patch_generated") is True,
            "patch_applied": patch_preview.get("patch_applied") is True,
            "files_mutated": patch_preview.get("files_mutated", []),
            "safe_to_prepare_d113": no_touch.get("safe_to_prepare_d113") is True,
        },
        "review_items": [
            "Confirm D112 was dry-run-only",
            "Confirm no patch was generated or applied",
            "Confirm no files were mutated",
            "Confirm no protected paths were touched",
            "Confirm no candidate execution occurred",
            "Confirm no route insertion occurred",
            "Confirm no AI/network/API call occurred",
            "Prepare D114 final human apply decision scope only",
        ],
        "actual_apply_executed": False,
        "candidate_executed": False,
        "approval_for_real_apply": False,
    }


def build_blocker_matrix(review_id, evidence_packet):
    return {
        "state": "D113_FINAL_APPLY_BLOCKER_MATRIX",
        "ok": True,
        "review_id": review_id,
        "created_at": now(),
        "real_apply_current_status": "BLOCKED",
        "blocked_until": "D114_FINAL_HUMAN_APPLY_DECISION_SCOPE",
        "blockers": {
            "no_d114_final_human_apply_decision": True,
            "no_d115_final_apply_phrase": True,
            "no_real_apply_permission_matrix": True,
            "no_post_apply_rollback_plan": True,
            "no_final_operator_commit_boundary": True,
        },
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
        "not_approved": [
            "real_apply",
            "auto_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "sandbox_candidate_execution",
            "git_commit_or_push_by_ai",
        ],
    }


def build_d114_scope(review_id, evidence_packet):
    return {
        "state": "D113_D114_FINAL_HUMAN_APPLY_DECISION_SCOPE",
        "ok": True,
        "review_id": review_id,
        "dry_run_id": evidence_packet.get("dry_run_id"),
        "proposal_id": evidence_packet.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D114_GATE,
        "d114_allowed_to_create": [
            "final_human_apply_decision_scope",
            "final_apply_permission_matrix",
            "final_operator_decision_statement",
            "d115_final_apply_phrase_scope",
        ],
        "d114_must_not_execute": [
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
        "final_human_decision_only": True,
        "human_review_required": True,
        "actual_apply_allowed_after_d113": False,
        "route_insert_allowed_after_d113": False,
        "protected_core_mutation_allowed_after_d113": False,
        "sandbox_candidate_execution_allowed_after_d113": False,
        "required_phrase_for_later_gate": "APPROVE_D114_FINAL_HUMAN_APPLY_DECISION_SCOPE_ONLY",
    }


def create_final_apply_review_scope(root="."):
    root = Path(root).resolve()

    d112 = read_json(root / D112_REPORT, {}) or {}
    plan = read_json(root / D112_PLAN, {}) or {}
    patch_preview = read_json(root / D112_PATCH_PREVIEW, {}) or {}
    no_touch = read_json(root / D112_NO_TOUCH, {}) or {}
    d113_scope = read_json(root / D112_D113_SCOPE, {}) or {}

    errors = validate_d112(d112, plan, patch_preview, no_touch, d113_scope)

    review_id = "d113-" + digest({
        "dry_run_id": d112.get("dry_run_id"),
        "approval_id": d112.get("approval_id"),
        "proposal_id": d112.get("proposal_id"),
    })

    evidence_packet = build_evidence_packet(review_id, d112, plan, patch_preview, no_touch)
    blocker_matrix = build_blocker_matrix(review_id, evidence_packet)
    d114_scope = build_d114_scope(review_id, evidence_packet)

    ok = not errors
    decision = "FINAL_APPLY_REVIEW_SCOPE_READY" if ok else "FINAL_APPLY_REVIEW_SCOPE_BLOCKED"
    result = "D113_FINAL_APPLY_REVIEW_SCOPE_CREATED" if ok else "D113_FINAL_APPLY_REVIEW_SCOPE_BLOCKED"

    if ok:
        write_json(root / EVIDENCE_PACKET_OUT, evidence_packet)
        write_json(root / BLOCKER_MATRIX_OUT, blocker_matrix)
        write_json(root / D114_SCOPE_OUT, d114_scope)

    report = {
        "state": "D113_FINAL_APPLY_REVIEW_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_FINAL_APPLY_REVIEW_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "review_id": review_id,
        "dry_run_id": d112.get("dry_run_id"),
        "approval_id": d112.get("approval_id"),
        "proposal_id": d112.get("proposal_id"),
        "source_d112_report": D112_REPORT,
        "evidence_packet": evidence_packet if ok else {},
        "blocker_matrix": blocker_matrix if ok else {},
        "d114_scope": d114_scope if ok else {},
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
            "final_apply_review_only": True,
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
            "review_id": review_id,
            "dry_run_id": d112.get("dry_run_id"),
            "proposal_id": d112.get("proposal_id"),
            "real_apply_current_status": "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D114_GATE,
        },
        "success_condition": {
            "final_apply_review_scope_created": ok,
            "evidence_packet_created": ok,
            "blocker_matrix_created": ok,
            "d114_scope_created": ok,
            "real_ai_called": False,
            "actual_apply_executed": False,
            "patch_applied": False,
            "candidate_executed": False,
            "protected_core_untouched": True,
            "next_step": "D114 may create final human apply decision scope only. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_final_apply_review_scope(), ensure_ascii=False, indent=2))
