
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from runtime_experimental.canonical_guard_schema import (
    canonical_schema_report,
    normalize_guard_flags,
    validate_no_ai_execution,
    build_no_touch_guardrails,
)

D161_REPORT = "reports/d161_sandbox_candidate_reentry_test_plan_scope.json"
D161_MATRIX = "reports/d161_sandbox_candidate_reentry_test_matrix.json"
D161_ASSERTIONS = "reports/d161_sandbox_candidate_reentry_no_touch_assertions.json"
D161_D162_SCOPE = "reports/d161_d162_sandbox_candidate_reentry_dry_test_runner_scope.json"

OUT = "reports/d162_sandbox_candidate_reentry_dry_test_runner_scope.json"
DRY_TEST_REPORT_OUT = "reports/d162_sandbox_candidate_reentry_dry_test_report.json"
SAFETY_RECEIPT_OUT = "reports/d162_sandbox_candidate_reentry_test_safety_receipt.json"
D163_SCOPE_OUT = "reports/d162_d163_provider_response_reentry_scope.json"

REQ_D161_DECISION = "SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE_READY"
REQ_D162_GATE = "D162_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE"
REQ_D163_GATE = "D163_PROVIDER_RESPONSE_REENTRY_SCOPE"

STATUS_FALSE_D161 = [
    "real_apply_allowed_after_d161_by_ai",
    "route_insert_allowed_after_d161_by_ai",
    "protected_core_mutation_allowed_after_d161_by_ai",
    "network_allowed_after_d161_by_ai",
    "secret_read_allowed_after_d161_by_ai",
    "shell_allowed_after_d161_by_ai",
    "git_action_allowed_after_d161_by_ai",
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


def validate_d161(d161, matrix, assertions, d162_scope):
    errors = []

    if not d161:
        return ["missing D161 sandbox candidate reentry test plan scope report"]

    if d161.get("ok") is not True:
        errors.append("D161 ok must be true")
    if d161.get("decision") != REQ_D161_DECISION:
        errors.append("D161 decision must be SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE_READY")

    summary = d161.get("summary", {})
    expected = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D161_PLUS",
        "test_plan_status": "TEST_PLAN_CREATED_DRY_MATRIX_ONLY_NO_TEST_EXECUTION",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_STILL_NOT_CREATED_NO_PAYLOAD_WRITTEN",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "test_execution_status": "NOT_EXECUTED",
        "candidate_execution_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D162_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE_ONLY",
        "next_step": REQ_D162_GATE,
    }
    for k, v in expected.items():
        if summary.get(k) != v:
            errors.append(f"D161 summary.{k} must be {v}")

    guard = normalize_guard_flags(d161.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D161 guardrails"))
    for k in STATUS_FALSE_D161:
        if guard.get(k) is not False:
            errors.append(f"D161 guardrails.{k} must be false")
    for k in [
        "sandbox_candidate_reentry_test_plan_scope_only",
        "sandbox_candidate_reentry_test_matrix_only",
        "sandbox_candidate_reentry_no_touch_assertions_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "provider_response_required_before_candidate",
        "dry_test_plan_only",
        "approval_for_d162_sandbox_candidate_reentry_dry_test_runner_scope_only",
    ]:
        if guard.get(k) is not True:
            errors.append(f"D161 guardrails.{k} must be true")
    for k in [
        "candidate_payload_available",
        "candidate_payload_written",
        "candidate_files_created",
        "candidate_execution_requested",
        "candidate_executed",
        "tests_executed",
        "apply_requested",
        "apply_executed",
    ]:
        if guard.get(k) is not False:
            errors.append(f"D161 guardrails.{k} must be false")

    if not matrix:
        errors.append("missing D161 sandbox candidate reentry test matrix")
    else:
        if matrix.get("ok") is not True:
            errors.append("D161 test matrix ok must be true")
        if matrix.get("test_matrix_status") != "TEST_MATRIX_CREATED_DRY_PLAN_ONLY_NO_CANDIDATE_EXECUTION":
            errors.append("D161 test matrix status mismatch")
        for k in ["canonical_guard_schema_applied", "fresh_intent_required", "provider_response_required_before_candidate", "human_review_required", "dry_test_plan_only"]:
            if matrix.get(k) is not True:
                errors.append(f"D161 test matrix {k} must be true")
        for k in [
            "candidate_payload_available",
            "candidate_payload_written",
            "candidate_files_created",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
        ]:
            if matrix.get(k) is not False:
                errors.append(f"D161 test matrix {k} must be false")
        items = matrix.get("test_items", [])
        if not isinstance(items, list) or len(items) < 5:
            errors.append("D161 test matrix must contain at least 5 test_items")
        errors.extend(validate_no_ai_execution(matrix, prefix="D161 matrix"))

    if not assertions:
        errors.append("missing D161 sandbox candidate reentry no touch assertions")
    else:
        if assertions.get("ok") is not True:
            errors.append("D161 assertions ok must be true")
        for k in [
            "canonical_guard_schema_applied",
            "no_candidate_payload_write",
            "no_candidate_execution",
            "no_test_execution",
            "no_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
            "human_review_required",
        ]:
            if assertions.get(k) is not True:
                errors.append(f"D161 assertions {k} must be true")
        for k in [
            "candidate_payload_written",
            "candidate_files_created",
            "candidate_execution_requested",
            "candidate_executed",
            "tests_executed",
            "apply_requested",
            "apply_executed",
        ]:
            if assertions.get(k) is not False:
                errors.append(f"D161 assertions {k} must be false")
        errors.extend(validate_no_ai_execution(assertions, prefix="D161 assertions"))

    if not d162_scope:
        errors.append("missing D161 D162 sandbox candidate reentry dry test runner scope")
    else:
        if d162_scope.get("ok") is not True:
            errors.append("D161 D162 scope ok must be true")
        if d162_scope.get("allowed_next_gate") != REQ_D162_GATE:
            errors.append("D161 D162 scope allowed_next_gate must be D162")
        if d162_scope.get("sandbox_candidate_reentry_dry_test_runner_scope_only") is not True:
            errors.append("D161 D162 scope must be dry-test-runner-only")
        if d162_scope.get("fresh_intent_required") is not True:
            errors.append("D161 D162 scope must require fresh intent")
        if d162_scope.get("provider_response_required_before_candidate") is not True:
            errors.append("D161 D162 scope must require provider response before candidate")
        if d162_scope.get("human_review_required") is not True:
            errors.append("D161 D162 scope must require human review")
        if d162_scope.get("canonical_guard_schema_required") is not True:
            errors.append("D161 D162 scope must require canonical guard schema")
        for k in STATUS_FALSE_D161:
            if d162_scope.get(k) is not False:
                errors.append(f"D161 D162 scope {k} must be false")

    return errors


def build_dry_test_report(runner_id, d161, matrix):
    test_items = matrix.get("test_items", []) if isinstance(matrix, dict) else []
    evaluated_items = []
    for item in test_items:
        evaluated_items.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "kind": item.get("kind"),
            "dry_evaluated": True,
            "candidate_executed": False,
            "shell_executed": False,
            "network_accessed": False,
            "secret_read": False,
            "apply_executed": False,
            "result": "DRY_PASS_METADATA_ONLY",
        })

    return normalize_guard_flags({
        "state": "D162_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_REPORT",
        "ok": True,
        "runner_id": runner_id,
        "plan_id": d161.get("plan_id"),
        "review_id": d161.get("review_id"),
        "scope_id": d161.get("scope_id"),
        "intake_id": d161.get("intake_id"),
        "reentry_id": d161.get("reentry_id"),
        "next_cycle_id": d161.get("next_cycle_id"),
        "cycle_closure_id": d161.get("cycle_closure_id"),
        "previous_candidate_id": d161.get("previous_candidate_id"),
        "proposal_id": d161.get("proposal_id"),
        "created_at": now(),
        "dry_test_report_status": "DRY_TEST_METADATA_EVALUATED_NO_CANDIDATE_EXECUTION",
        "canonical_guard_schema_applied": True,
        "dry_runner_scope_only": True,
        "dry_tests_evaluated": True,
        "tests_executed": False,
        "candidate_payload_available": False,
        "candidate_payload_written": False,
        "candidate_files_created": False,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "provider_response_required_before_candidate": True,
        "provider_response_ingested": False,
        "evaluated_count": len(evaluated_items),
        "evaluated_items": evaluated_items,
    })


def build_safety_receipt(runner_id, d161):
    return normalize_guard_flags({
        "state": "D162_SANDBOX_CANDIDATE_REENTRY_TEST_SAFETY_RECEIPT",
        "ok": True,
        "runner_id": runner_id,
        "plan_id": d161.get("plan_id"),
        "review_id": d161.get("review_id"),
        "scope_id": d161.get("scope_id"),
        "intake_id": d161.get("intake_id"),
        "reentry_id": d161.get("reentry_id"),
        "created_at": now(),
        "safety_receipt_status": "DRY_TEST_RUNNER_RECORDED_NO_TOUCH_NO_CANDIDATE_EXECUTION",
        "canonical_guard_schema_applied": True,
        "dry_tests_evaluated": True,
        "tests_executed": False,
        "candidate_payload_written": False,
        "candidate_files_created": False,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "no_candidate_payload_write": True,
        "no_candidate_execution": True,
        "no_real_test_execution": True,
        "no_apply": True,
        "no_network": True,
        "no_secret_read": True,
        "no_shell": True,
        "no_route_insert": True,
        "no_core_mutation_by_ai": True,
        "no_git_action_by_ai": True,
        "human_review_required": True,
    })


def build_d163_scope(runner_id, d161):
    return {
        "state": "D162_D163_PROVIDER_RESPONSE_REENTRY_SCOPE",
        "ok": True,
        "runner_id": runner_id,
        "plan_id": d161.get("plan_id"),
        "review_id": d161.get("review_id"),
        "scope_id": d161.get("scope_id"),
        "intake_id": d161.get("intake_id"),
        "reentry_id": d161.get("reentry_id"),
        "next_cycle_id": d161.get("next_cycle_id"),
        "cycle_closure_id": d161.get("cycle_closure_id"),
        "previous_candidate_id": d161.get("previous_candidate_id"),
        "proposal_id": d161.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D163_GATE,
        "provider_response_reentry_scope_only": True,
        "fresh_intent_required": True,
        "provider_response_required_before_candidate": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d163_allowed_to_create": [
            "provider_response_reentry_scope",
            "provider_response_reentry_manifest",
            "provider_response_reentry_dry_capture_receipt",
            "d164_sandbox_candidate_reentry_materialization_scope",
        ],
        "d163_must_not_execute": [
            "unreviewed_provider_call",
            "candidate_execution",
            "real_core_apply",
            "route_insert_by_ai",
            "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai",
            "shell_exec_from_ai",
            "network_call_by_ai_without_human_intent",
            "secret_read_by_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute_by_ai",
            "restore_execute_by_ai",
        ],
        "real_apply_allowed_after_d162_by_ai": False,
        "route_insert_allowed_after_d162_by_ai": False,
        "protected_core_mutation_allowed_after_d162_by_ai": False,
        "network_allowed_after_d162_by_ai": False,
        "secret_read_allowed_after_d162_by_ai": False,
        "shell_allowed_after_d162_by_ai": False,
        "git_action_allowed_after_d162_by_ai": False,
    }


def create_sandbox_candidate_reentry_dry_test_runner_scope(root="."):
    root = Path(root).resolve()

    d161 = read_json(root / D161_REPORT, {}) or {}
    matrix = read_json(root / D161_MATRIX, {}) or {}
    assertions = read_json(root / D161_ASSERTIONS, {}) or {}
    d162_scope = read_json(root / D161_D162_SCOPE, {}) or {}

    errors = validate_d161(d161, matrix, assertions, d162_scope)

    runner_id = "d162-" + digest({
        "plan_id": d161.get("plan_id"),
        "review_id": d161.get("review_id"),
        "scope_id": d161.get("scope_id"),
        "intake_id": d161.get("intake_id"),
        "reentry_id": d161.get("reentry_id"),
        "next_cycle_id": d161.get("next_cycle_id"),
        "proposal_id": d161.get("proposal_id"),
    })

    dry_test_report = build_dry_test_report(runner_id, d161, matrix)
    safety_receipt = build_safety_receipt(runner_id, d161)
    d163_scope = build_d163_scope(runner_id, d161)

    for name, item in [("dry_test_report", dry_test_report), ("safety_receipt", safety_receipt)]:
        errors.extend(validate_no_ai_execution(item, prefix=name))
        for k in [
            "tests_executed",
            "candidate_payload_written",
            "candidate_files_created",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "provider_response_ingested",
        ]:
            if item.get(k) is not False:
                errors.append(f"{name}.{k} must be false")
    if dry_test_report.get("dry_tests_evaluated") is not True:
        errors.append("dry_test_report.dry_tests_evaluated must be true")
    if safety_receipt.get("dry_tests_evaluated") is not True:
        errors.append("safety_receipt.dry_tests_evaluated must be true")

    for k in [
        "real_apply_allowed_after_d162_by_ai",
        "route_insert_allowed_after_d162_by_ai",
        "protected_core_mutation_allowed_after_d162_by_ai",
        "network_allowed_after_d162_by_ai",
        "secret_read_allowed_after_d162_by_ai",
        "shell_allowed_after_d162_by_ai",
        "git_action_allowed_after_d162_by_ai",
    ]:
        if d163_scope.get(k) is not False:
            errors.append(f"d163_scope.{k} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE_BLOCKED"
    result = "D162_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE_CREATED" if ok else "D162_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE_BLOCKED"

    if ok:
        write_json(root / DRY_TEST_REPORT_OUT, dry_test_report)
        write_json(root / SAFETY_RECEIPT_OUT, safety_receipt)
        write_json(root / D163_SCOPE_OUT, d163_scope)

    report = {
        "state": "D162_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "runner_id": runner_id,
        "plan_id": d161.get("plan_id"),
        "review_id": d161.get("review_id"),
        "scope_id": d161.get("scope_id"),
        "intake_id": d161.get("intake_id"),
        "reentry_id": d161.get("reentry_id"),
        "next_cycle_id": d161.get("next_cycle_id"),
        "cycle_closure_id": d161.get("cycle_closure_id"),
        "previous_candidate_id": d161.get("previous_candidate_id"),
        "proposal_id": d161.get("proposal_id"),
        "source_d161_report": D161_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "dry_test_report": dry_test_report if ok else {},
        "safety_receipt": safety_receipt if ok else {},
        "d163_scope": d163_scope if ok else {},
        "guardrails": build_no_touch_guardrails(
            sandbox_candidate_reentry_dry_test_runner_scope_only=True,
            sandbox_candidate_reentry_dry_test_report_only=True,
            sandbox_candidate_reentry_test_safety_receipt_only=True,
            canonical_guard_schema_applied=True,
            fresh_intent_required=True,
            provider_response_required_before_candidate=True,
            dry_tests_evaluated=ok,
            tests_executed=False,
            candidate_payload_available=False,
            candidate_payload_written=False,
            candidate_files_created=False,
            candidate_execution_requested=False,
            candidate_executed=False,
            provider_response_ingested=False,
            apply_requested=False,
            apply_executed=False,
            approval_for_d163_provider_response_reentry_scope_only=ok,
            real_apply_allowed_after_d162_by_ai=False,
            route_insert_allowed_after_d162_by_ai=False,
            protected_core_mutation_allowed_after_d162_by_ai=False,
            network_allowed_after_d162_by_ai=False,
            secret_read_allowed_after_d162_by_ai=False,
            shell_allowed_after_d162_by_ai=False,
            git_action_allowed_after_d162_by_ai=False,
        ),
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "runner_id": runner_id,
            "plan_id": d161.get("plan_id"),
            "review_id": d161.get("review_id"),
            "scope_id": d161.get("scope_id"),
            "intake_id": d161.get("intake_id"),
            "reentry_id": d161.get("reentry_id"),
            "next_cycle_id": d161.get("next_cycle_id"),
            "proposal_id": d161.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D162_PLUS" if ok else "BLOCKED",
            "dry_test_status": "DRY_TEST_METADATA_EVALUATED_NO_CANDIDATE_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_STILL_NOT_CREATED_NO_PAYLOAD_WRITTEN" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "test_execution_status": "DRY_METADATA_ONLY_NOT_EXECUTED",
            "candidate_execution_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D163_PROVIDER_RESPONSE_REENTRY_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D163_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_dry_test_runner_scope_created": ok,
            "dry_test_report_created": ok,
            "safety_receipt_created": ok,
            "d163_scope_created": ok,
            "dry_tests_evaluated": ok,
            "tests_executed": False,
            "candidate_payload_written": False,
            "candidate_executed": False,
            "apply_executed": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D163 may create provider response reentry scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_dry_test_runner_scope(), ensure_ascii=False, indent=2))
