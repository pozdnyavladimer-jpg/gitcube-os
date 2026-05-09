
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D118_REPORT = "reports/d118_operator_local_execution_evidence_scope.json"
D118_LOG_TEMPLATE = "reports/d118_operator_local_execution_log_template.json"
D118_RESULT_CAPTURE = "reports/d118_operator_local_result_capture.json"
D118_D119_SCOPE = "reports/d118_d119_post_apply_verification_gate_scope.json"

OUT = "reports/d119_post_apply_verification_gate_scope.json"
TEST_RESULTS_OUT = "reports/d119_post_apply_test_results_summary.json"
GIT_STATE_OUT = "reports/d119_post_apply_git_state_summary.json"
D120_SCOPE_OUT = "reports/d119_d120_first_controlled_run_seal_scope.json"

REQ_D118_DECISION = "OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_READY"
REQ_D119_GATE = "D119_POST_APPLY_VERIFICATION_GATE_SCOPE"
REQ_D120_GATE = "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE"
REQ_D118_APPROVAL_SCOPE = "D119_POST_APPLY_VERIFICATION_GATE_SCOPE_ONLY"

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


def validate_d118(d118, log_template, result_capture, d119_scope):
    errors = []

    if not d118:
        errors.append("missing D118 operator local execution evidence scope report")
        return errors

    if d118.get("ok") is not True:
        errors.append("D118 ok must be true")
    if d118.get("decision") != REQ_D118_DECISION:
        errors.append("D118 decision must be OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_READY")

    guard = d118.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D118 guardrails.{key} must be false")
    if guard.get("operator_local_evidence_scope_only") is not True:
        errors.append("D118 operator_local_evidence_scope_only must be true")
    if guard.get("evidence_template_only") is not True:
        errors.append("D118 evidence_template_only must be true")
    if guard.get("approval_for_d119_verification_scope_only") is not True:
        errors.append("D118 approval_for_d119_verification_scope_only must be true")
    if guard.get("approval_for_real_apply_by_ai") is not False:
        errors.append("D118 approval_for_real_apply_by_ai must be false")
    if guard.get("candidate_execution_allowed_by_ai") is not False:
        errors.append("D118 candidate_execution_allowed_by_ai must be false")
    if guard.get("commands_executed_by_ai") is not False:
        errors.append("D118 commands_executed_by_ai must be false")

    summary = d118.get("summary", {})
    if summary.get("real_apply_by_ai_status") != "BLOCKED":
        errors.append("D118 real_apply_by_ai_status must be BLOCKED")
    if summary.get("approval_scope") != REQ_D118_APPROVAL_SCOPE:
        errors.append("D118 approval_scope must be D119 verification scope only")
    if summary.get("next_step") != REQ_D119_GATE:
        errors.append("D118 summary next_step must be D119")

    if not log_template:
        errors.append("missing D118 local execution log template")
    else:
        if log_template.get("ok") is not True:
            errors.append("D118 log template ok must be true")
        if log_template.get("template_mode") != "HUMAN_LOCAL_EVIDENCE_TEMPLATE_ONLY":
            errors.append("D118 log template must be template-only")
        for key in [
            "shell_executed_by_ai",
            "actual_apply_executed_by_ai",
            "candidate_executed_by_ai",
        ]:
            if log_template.get(key) is not False:
                errors.append(f"D118 log template {key} must be false")

    if not result_capture:
        errors.append("missing D118 operator local result capture")
    else:
        if result_capture.get("ok") is not True:
            errors.append("D118 result capture ok must be true")
        if result_capture.get("capture_status") != "AWAITING_OPERATOR_LOCAL_EVIDENCE":
            errors.append("D118 result capture must be awaiting operator evidence")
        for key in [
            "operator_local_execution_claimed",
            "operator_local_execution_evidence_present",
            "ai_executed_commands",
            "shell_executed_by_ai",
            "actual_apply_executed_by_ai",
            "candidate_executed_by_ai",
        ]:
            if result_capture.get(key) is not False:
                errors.append(f"D118 result capture {key} must be false")
        if result_capture.get("ready_for_d119_verification_scope") is not True:
            errors.append("D118 result capture must be ready for D119 verification scope")

    if not d119_scope:
        errors.append("missing D118 D119 post-apply verification gate scope")
    else:
        if d119_scope.get("ok") is not True:
            errors.append("D118 D119 scope ok must be true")
        if d119_scope.get("allowed_next_gate") != REQ_D119_GATE:
            errors.append("D118 D119 scope allowed_next_gate must be D119")
        if d119_scope.get("post_apply_verification_scope_only") is not True:
            errors.append("D118 D119 scope post_apply_verification_scope_only must be true")
        if d119_scope.get("human_review_required") is not True:
            errors.append("D118 D119 scope human_review_required must be true")
        for key in [
            "actual_apply_allowed_after_d118_by_ai",
            "route_insert_allowed_after_d118_by_ai",
            "protected_core_mutation_allowed_after_d118_by_ai",
            "sandbox_candidate_execution_allowed_after_d118_by_ai",
        ]:
            if d119_scope.get(key) is not False:
                errors.append(f"D118 D119 scope {key} must be false")

    return errors


def build_test_results_summary(verification_id, d118, result_capture):
    return {
        "state": "D119_POST_APPLY_TEST_RESULTS_SUMMARY",
        "ok": True,
        "verification_id": verification_id,
        "evidence_id": d118.get("evidence_id"),
        "review_id": d118.get("review_id"),
        "proposal_id": d118.get("proposal_id"),
        "created_at": now(),
        "summary_mode": "VERIFICATION_SCOPE_ONLY_NOT_EXECUTED",
        "tests_executed_by_ai": False,
        "operator_test_evidence_present": False,
        "operator_reported_tests_summary": result_capture.get("tests_summary", "not captured yet"),
        "required_before_d120": [
            "operator local execution evidence reviewed",
            "test command outputs captured",
            "exit codes captured",
            "no secrets included in evidence",
            "git state reviewed",
        ],
        "verification_status": "AWAITING_OPERATOR_EVIDENCE_OR_NO_APPLY_TO_VERIFY",
        "actual_apply_executed_by_ai": False,
        "candidate_executed_by_ai": False,
    }


def build_git_state_summary(verification_id, d118, result_capture):
    return {
        "state": "D119_POST_APPLY_GIT_STATE_SUMMARY",
        "ok": True,
        "verification_id": verification_id,
        "evidence_id": d118.get("evidence_id"),
        "proposal_id": d118.get("proposal_id"),
        "created_at": now(),
        "summary_mode": "GIT_STATE_SUMMARY_TEMPLATE_ONLY",
        "git_commands_executed_by_ai": False,
        "operator_git_evidence_present": False,
        "working_tree_before": result_capture.get("working_tree_before", "not captured yet"),
        "working_tree_after": result_capture.get("working_tree_after", "not captured yet"),
        "commands_run": result_capture.get("commands_run", []),
        "exit_codes": result_capture.get("exit_codes", {}),
        "git_state_status": "AWAITING_OPERATOR_EVIDENCE_OR_NO_APPLY_TO_VERIFY",
        "git_commit_by_ai": False,
        "git_push_by_ai": False,
        "route_inserted_by_ai": False,
        "protected_core_mutated_by_ai": False,
    }


def build_d120_scope(verification_id, d118):
    return {
        "state": "D119_D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE",
        "ok": True,
        "verification_id": verification_id,
        "evidence_id": d118.get("evidence_id"),
        "review_id": d118.get("review_id"),
        "window_id": d118.get("window_id"),
        "phrase_id": d118.get("phrase_id"),
        "decision_id": d118.get("decision_id"),
        "dry_run_id": d118.get("dry_run_id"),
        "proposal_id": d118.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D120_GATE,
        "d120_allowed_to_create": [
            "first_controlled_run_seal",
            "guarded_autonomy_run_ledger",
            "final_chain_integrity_summary",
            "first_run_release_tag_plan",
        ],
        "d120_must_not_execute": [
            "real_apply_by_ai",
            "auto_apply",
            "route_insert_by_ai",
            "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai",
            "external_ai_network_call",
            "shell_exec_from_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute_by_ai",
            "restore_execute_by_ai",
            "execute_sandbox_candidate_by_ai",
            "commit_sandbox_candidate_by_ai",
        ],
        "first_controlled_run_seal_scope_only": True,
        "human_review_required": True,
        "actual_apply_allowed_after_d119_by_ai": False,
        "route_insert_allowed_after_d119_by_ai": False,
        "protected_core_mutation_allowed_after_d119_by_ai": False,
        "sandbox_candidate_execution_allowed_after_d119_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE_ONLY",
    }


def create_post_apply_verification_gate_scope(root="."):
    root = Path(root).resolve()

    d118 = read_json(root / D118_REPORT, {}) or {}
    log_template = read_json(root / D118_LOG_TEMPLATE, {}) or {}
    result_capture = read_json(root / D118_RESULT_CAPTURE, {}) or {}
    d119_scope = read_json(root / D118_D119_SCOPE, {}) or {}

    errors = validate_d118(d118, log_template, result_capture, d119_scope)

    verification_id = "d119-" + digest({
        "evidence_id": d118.get("evidence_id"),
        "review_id": d118.get("review_id"),
        "proposal_id": d118.get("proposal_id"),
    })

    test_summary = build_test_results_summary(verification_id, d118, result_capture)
    git_state = build_git_state_summary(verification_id, d118, result_capture)
    d120_scope = build_d120_scope(verification_id, d118)

    if test_summary.get("tests_executed_by_ai") is not False:
        errors.append("test summary tests_executed_by_ai must be false")
    if git_state.get("git_commands_executed_by_ai") is not False:
        errors.append("git state summary git_commands_executed_by_ai must be false")
    if git_state.get("git_commit_by_ai") is not False:
        errors.append("git state summary git_commit_by_ai must be false")

    ok = not errors
    decision = "POST_APPLY_VERIFICATION_GATE_SCOPE_READY" if ok else "POST_APPLY_VERIFICATION_GATE_SCOPE_BLOCKED"
    result = "D119_POST_APPLY_VERIFICATION_GATE_SCOPE_CREATED" if ok else "D119_POST_APPLY_VERIFICATION_GATE_SCOPE_BLOCKED"

    if ok:
        write_json(root / TEST_RESULTS_OUT, test_summary)
        write_json(root / GIT_STATE_OUT, git_state)
        write_json(root / D120_SCOPE_OUT, d120_scope)

    report = {
        "state": "D119_POST_APPLY_VERIFICATION_GATE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_POST_APPLY_VERIFICATION_GATE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "verification_id": verification_id,
        "evidence_id": d118.get("evidence_id"),
        "review_id": d118.get("review_id"),
        "window_id": d118.get("window_id"),
        "phrase_id": d118.get("phrase_id"),
        "decision_id": d118.get("decision_id"),
        "dry_run_id": d118.get("dry_run_id"),
        "proposal_id": d118.get("proposal_id"),
        "source_d118_report": D118_REPORT,
        "post_apply_test_results_summary": test_summary if ok else {},
        "post_apply_git_state_summary": git_state if ok else {},
        "d120_scope": d120_scope if ok else {},
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
            "post_apply_verification_scope_only": True,
            "verification_template_only": True,
            "approval_for_d120_seal_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": [],
        },
        "summary": {
            "decision": decision,
            "verification_id": verification_id,
            "evidence_id": d118.get("evidence_id"),
            "proposal_id": d118.get("proposal_id"),
            "real_apply_by_ai_status": "BLOCKED",
            "verification_status": "SCOPE_CREATED_AWAITING_OPERATOR_EVIDENCE_OR_NO_APPLY_TO_VERIFY" if ok else "BLOCKED",
            "approval_scope": "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D120_GATE,
        },
        "success_condition": {
            "post_apply_verification_gate_scope_created": ok,
            "test_results_summary_created": ok,
            "git_state_summary_created": ok,
            "d120_scope_created": ok,
            "approval_for_d120_seal_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "real_ai_called": False,
            "actual_apply_executed_by_ai": False,
            "candidate_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D120 may create first controlled run seal scope only. Real apply by AI remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_post_apply_verification_gate_scope(), ensure_ascii=False, indent=2))
