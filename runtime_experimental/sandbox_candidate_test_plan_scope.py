
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D127_REPORT = "reports/d127_sandbox_candidate_human_review_scope.json"
D127_REVIEW_PACKET = "reports/d127_sandbox_candidate_review_packet.json"
D127_APPROVAL_RECORD = "reports/d127_sandbox_candidate_approval_or_rejection_record.json"
D127_D128_SCOPE = "reports/d127_d128_sandbox_candidate_test_plan_scope.json"

OUT = "reports/d128_sandbox_candidate_test_plan_scope.json"
TEST_MATRIX_OUT = "reports/d128_sandbox_candidate_test_matrix.json"
NO_TOUCH_OUT = "reports/d128_sandbox_candidate_no_touch_assertions.json"
D129_SCOPE_OUT = "reports/d128_d129_sandbox_candidate_dry_test_runner_scope.json"

REQ_D127_DECISION = "SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_READY"
REQ_D128_GATE = "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE"
REQ_D129_GATE = "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE"

FALSE_KEYS = [
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

NO_TOUCH_TARGETS = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(obj):
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
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


def validate_d127(d127, review_packet, approval_record, d128_scope):
    errors = []

    if not d127:
        return ["missing D127 sandbox candidate human review scope report"]

    if d127.get("ok") is not True:
        errors.append("D127 ok must be true")
    if d127.get("decision") != REQ_D127_DECISION:
        errors.append("D127 decision must be SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_READY")

    guard = d127.get("guardrails", {})
    for key in FALSE_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D127 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_human_review_scope_only",
        "review_packet_only",
        "approval_record_template_only",
        "approval_for_d128_test_plan_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D127 guardrails.{key} must be true")

    for key in [
        "candidate_files_written_now",
        "candidate_executed_now",
        "approval_for_candidate_execution",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D127 guardrails.{key} must be false")

    summary = d127.get("summary", {})
    if summary.get("review_status") != "PENDING_HUMAN_REVIEW_PACKET_CREATED":
        errors.append("D127 review_status must be PENDING_HUMAN_REVIEW_PACKET_CREATED")
    if summary.get("candidate_status") != "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED":
        errors.append("D127 candidate_status must be PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED")
    if summary.get("static_scan_status") != "PASS":
        errors.append("D127 static_scan_status must be PASS")
    if summary.get("approval_scope") != "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_ONLY":
        errors.append("D127 approval_scope must be D128 test plan scope only")
    if summary.get("next_step") != REQ_D128_GATE:
        errors.append("D127 next_step must be D128")

    if not review_packet:
        errors.append("missing D127 sandbox candidate review packet")
    else:
        if review_packet.get("ok") is not True:
            errors.append("D127 review packet ok must be true")
        if review_packet.get("packet_mode") != "HUMAN_REVIEW_PACKET_ONLY_NO_EXECUTION":
            errors.append("D127 review packet must be human-review packet only")
        if review_packet.get("static_scan_ok") is not True:
            errors.append("D127 review packet static_scan_ok must be true")
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
        ]:
            if review_packet.get(key) is not False:
                errors.append(f"D127 review packet {key} must be false")

    if not approval_record:
        errors.append("missing D127 approval/rejection record")
    else:
        if approval_record.get("ok") is not True:
            errors.append("D127 approval record ok must be true")
        if approval_record.get("operator_decision") != "PENDING_HUMAN_REVIEW":
            errors.append("D127 operator_decision must be pending human review")
        if approval_record.get("approved_for_d128_test_plan_scope_now") is not True:
            errors.append("D127 must approve D128 test plan scope only")
        for key in [
            "approved_for_candidate_execution",
            "approved_for_real_apply",
            "approved_for_route_insert",
            "approved_for_protected_core_mutation",
            "approved_for_git_action_by_ai",
        ]:
            if approval_record.get(key) is not False:
                errors.append(f"D127 approval record {key} must be false")

    if not d128_scope:
        errors.append("missing D127 D128 sandbox candidate test plan scope")
    else:
        if d128_scope.get("ok") is not True:
            errors.append("D127 D128 scope ok must be true")
        if d128_scope.get("allowed_next_gate") != REQ_D128_GATE:
            errors.append("D127 D128 scope allowed_next_gate must be D128")
        if d128_scope.get("sandbox_candidate_test_plan_scope_only") is not True:
            errors.append("D127 D128 scope must be test-plan-only")
        for key in [
            "candidate_written_after_d127",
            "candidate_executed_after_d127_by_ai",
            "real_apply_allowed_after_d127_by_ai",
            "route_insert_allowed_after_d127_by_ai",
            "protected_core_mutation_allowed_after_d127_by_ai",
        ]:
            if d128_scope.get(key) is not False:
                errors.append(f"D127 D128 scope {key} must be false")

    return errors


def build_test_matrix(plan_id, d127, review_packet):
    return {
        "state": "D128_SANDBOX_CANDIDATE_TEST_MATRIX",
        "ok": True,
        "plan_id": plan_id,
        "review_id": d127.get("review_id"),
        "candidate_id": d127.get("candidate_id"),
        "proposal_id": d127.get("proposal_id"),
        "created_at": now(),
        "matrix_mode": "TEST_PLAN_ONLY_NO_EXECUTION",
        "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
        "test_groups": [
            {
                "name": "schema_and_manifest_checks",
                "purpose": "Confirm candidate manifest and summary shape before any candidate write.",
                "dry_only": True,
            },
            {
                "name": "path_boundary_checks",
                "purpose": "Confirm planned files stay inside allowed sandbox/report/test/doc paths.",
                "dry_only": True,
            },
            {
                "name": "no_touch_assertions",
                "purpose": "Confirm protected targets remain untouched.",
                "dry_only": True,
            },
            {
                "name": "no_execution_assertions",
                "purpose": "Confirm no provider/network/shell/apply/git/candidate execution occurs.",
                "dry_only": True,
            },
        ],
        "planned_files_reference": review_packet.get("planned_files", []),
        "candidate_files_written_now": False,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_no_touch_assertions(plan_id, d127):
    return {
        "state": "D128_SANDBOX_CANDIDATE_NO_TOUCH_ASSERTIONS",
        "ok": True,
        "plan_id": plan_id,
        "review_id": d127.get("review_id"),
        "candidate_id": d127.get("candidate_id"),
        "created_at": now(),
        "assertion_mode": "NO_TOUCH_ASSERTIONS_ONLY_NO_EXECUTION",
        "no_touch_targets": NO_TOUCH_TARGETS,
        "must_remain_false": {
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
        },
        "human_review_required": True,
    }


def build_d129_scope(plan_id, d127):
    return {
        "state": "D128_D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE",
        "ok": True,
        "plan_id": plan_id,
        "review_id": d127.get("review_id"),
        "candidate_id": d127.get("candidate_id"),
        "intake_id": d127.get("intake_id"),
        "ping_id": d127.get("ping_id"),
        "config_id": d127.get("config_id"),
        "dashboard_id": d127.get("dashboard_id"),
        "adapter_id": d127.get("adapter_id"),
        "seal_id": d127.get("seal_id"),
        "proposal_id": d127.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D129_GATE,
        "d129_allowed_to_create": [
            "sandbox_candidate_dry_test_runner_scope",
            "sandbox_candidate_dry_test_results",
            "sandbox_candidate_integrity_diff_summary",
            "d130_sandbox_candidate_write_window_scope",
        ],
        "d129_must_not_execute": [
            "execute_sandbox_candidate_by_ai",
            "commit_sandbox_candidate_by_ai",
            "real_apply_by_ai",
            "auto_apply",
            "route_insert_by_ai",
            "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai",
            "shell_exec_from_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute_by_ai",
            "restore_execute_by_ai",
        ],
        "sandbox_candidate_dry_test_runner_scope_only": True,
        "human_review_required": True,
        "candidate_written_after_d128": False,
        "candidate_executed_after_d128_by_ai": False,
        "real_apply_allowed_after_d128_by_ai": False,
        "route_insert_allowed_after_d128_by_ai": False,
        "protected_core_mutation_allowed_after_d128_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_ONLY",
    }


def create_sandbox_candidate_test_plan_scope(root="."):
    root = Path(root).resolve()

    d127 = read_json(root / D127_REPORT, {}) or {}
    review_packet = read_json(root / D127_REVIEW_PACKET, {}) or {}
    approval_record = read_json(root / D127_APPROVAL_RECORD, {}) or {}
    d128_scope = read_json(root / D127_D128_SCOPE, {}) or {}

    errors = validate_d127(d127, review_packet, approval_record, d128_scope)

    plan_id = "d128-" + digest({
        "review_id": d127.get("review_id"),
        "candidate_id": d127.get("candidate_id"),
        "adapter_id": d127.get("adapter_id"),
        "proposal_id": d127.get("proposal_id"),
    })

    test_matrix = build_test_matrix(plan_id, d127, review_packet)
    no_touch_assertions = build_no_touch_assertions(plan_id, d127)
    d129_scope = build_d129_scope(plan_id, d127)

    for item_name, item in [("test_matrix", test_matrix)]:
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
        ]:
            if item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    for key, value in no_touch_assertions.get("must_remain_false", {}).items():
        if value is not False:
            errors.append(f"no_touch_assertions {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_BLOCKED"
    result = "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_CREATED" if ok else "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_BLOCKED"

    if ok:
        write_json(root / TEST_MATRIX_OUT, test_matrix)
        write_json(root / NO_TOUCH_OUT, no_touch_assertions)
        write_json(root / D129_SCOPE_OUT, d129_scope)

    report = {
        "state": "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "plan_id": plan_id,
        "review_id": d127.get("review_id"),
        "candidate_id": d127.get("candidate_id"),
        "intake_id": d127.get("intake_id"),
        "ping_id": d127.get("ping_id"),
        "config_id": d127.get("config_id"),
        "dashboard_id": d127.get("dashboard_id"),
        "adapter_id": d127.get("adapter_id"),
        "seal_id": d127.get("seal_id"),
        "proposal_id": d127.get("proposal_id"),
        "source_d127_report": D127_REPORT,
        "sandbox_candidate_test_matrix": test_matrix if ok else {},
        "sandbox_candidate_no_touch_assertions": no_touch_assertions if ok else {},
        "d129_scope": d129_scope if ok else {},
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
            "sandbox_candidate_test_plan_scope_only": True,
            "test_matrix_only": True,
            "no_touch_assertions_only": True,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "approval_for_d129_dry_test_runner_scope_only": ok,
            "approval_for_candidate_execution": False,
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
            "plan_id": plan_id,
            "review_id": d127.get("review_id"),
            "candidate_id": d127.get("candidate_id"),
            "adapter_id": d127.get("adapter_id"),
            "seal_id": d127.get("seal_id"),
            "proposal_id": d127.get("proposal_id"),
            "test_plan_status": "PLAN_CREATED_NOT_RUN",
            "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
            "no_touch_status": "ASSERTIONS_CREATED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "approval_scope": "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D129_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_test_plan_scope_created": ok,
            "sandbox_candidate_test_matrix_created": ok,
            "sandbox_candidate_no_touch_assertions_created": ok,
            "d129_scope_created": ok,
            "candidate_files_written": False,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D129 may create sandbox candidate dry test runner scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_test_plan_scope(), ensure_ascii=False, indent=2))
