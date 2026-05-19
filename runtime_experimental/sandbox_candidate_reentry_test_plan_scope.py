
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

D160_REPORT = "reports/d160_sandbox_candidate_reentry_human_review_scope.json"
D160_REVIEW_PACKET = "reports/d160_sandbox_candidate_reentry_review_packet.json"
D160_ASSERTIONS = "reports/d160_sandbox_candidate_reentry_no_apply_assertions.json"
D160_D161_SCOPE = "reports/d160_d161_sandbox_candidate_reentry_test_plan_scope.json"

OUT = "reports/d161_sandbox_candidate_reentry_test_plan_scope.json"
TEST_MATRIX_OUT = "reports/d161_sandbox_candidate_reentry_test_matrix.json"
NO_TOUCH_ASSERTIONS_OUT = "reports/d161_sandbox_candidate_reentry_no_touch_assertions.json"
D162_SCOPE_OUT = "reports/d161_d162_sandbox_candidate_reentry_dry_test_runner_scope.json"

REQ_D160_DECISION = "SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE_READY"
REQ_D161_GATE = "D161_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE"
REQ_D162_GATE = "D162_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE"

STATUS_FALSE_D160 = [
    "real_apply_allowed_after_d160_by_ai",
    "route_insert_allowed_after_d160_by_ai",
    "protected_core_mutation_allowed_after_d160_by_ai",
    "network_allowed_after_d160_by_ai",
    "secret_read_allowed_after_d160_by_ai",
    "shell_allowed_after_d160_by_ai",
    "git_action_allowed_after_d160_by_ai",
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


def validate_d160(d160, review_packet, assertions, d161_scope):
    errors = []

    if not d160:
        return ["missing D160 sandbox candidate reentry human review scope report"]

    if d160.get("ok") is not True:
        errors.append("D160 ok must be true")
    if d160.get("decision") != REQ_D160_DECISION:
        errors.append("D160 decision must be SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE_READY")

    summary = d160.get("summary", {})
    expected = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D160_PLUS",
        "review_status": "HUMAN_REVIEW_PACKET_CREATED_NO_CANDIDATE_PAYLOAD_NO_EXECUTION",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_STILL_NOT_CREATED_NO_PAYLOAD_WRITTEN",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D161_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE_ONLY",
        "next_step": REQ_D161_GATE,
    }
    for k, v in expected.items():
        if summary.get(k) != v:
            errors.append(f"D160 summary.{k} must be {v}")

    guard = normalize_guard_flags(d160.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D160 guardrails"))
    for k in STATUS_FALSE_D160:
        if guard.get(k) is not False:
            errors.append(f"D160 guardrails.{k} must be false")
    for k in [
        "sandbox_candidate_reentry_human_review_scope_only",
        "sandbox_candidate_reentry_review_packet_only",
        "sandbox_candidate_reentry_no_apply_assertions_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "provider_response_required_before_candidate",
        "approval_for_d161_sandbox_candidate_reentry_test_plan_scope_only",
    ]:
        if guard.get(k) is not True:
            errors.append(f"D160 guardrails.{k} must be true")
    for k in [
        "candidate_payload_available",
        "candidate_payload_written",
        "candidate_files_created",
        "candidate_execution_requested",
        "candidate_executed",
        "apply_requested",
        "apply_executed",
    ]:
        if guard.get(k) is not False:
            errors.append(f"D160 guardrails.{k} must be false")

    if not review_packet:
        errors.append("missing D160 sandbox candidate reentry review packet")
    else:
        if review_packet.get("ok") is not True:
            errors.append("D160 review packet ok must be true")
        if review_packet.get("review_packet_status") != "REVIEW_PACKET_CREATED_NO_CANDIDATE_PAYLOAD_NO_EXECUTION":
            errors.append("D160 review packet status mismatch")
        for k in ["canonical_guard_schema_applied", "human_review_required", "fresh_intent_required", "provider_response_required_before_candidate"]:
            if review_packet.get(k) is not True:
                errors.append(f"D160 review packet {k} must be true")
        for k in [
            "candidate_payload_available",
            "candidate_payload_written",
            "candidate_files_created",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
        ]:
            if review_packet.get(k) is not False:
                errors.append(f"D160 review packet {k} must be false")
        errors.extend(validate_no_ai_execution(review_packet, prefix="D160 review_packet"))

    if not assertions:
        errors.append("missing D160 sandbox candidate reentry no apply assertions")
    else:
        if assertions.get("ok") is not True:
            errors.append("D160 assertions ok must be true")
        for k in [
            "canonical_guard_schema_applied",
            "no_candidate_payload_write",
            "no_candidate_execution",
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
                errors.append(f"D160 assertions {k} must be true")
        for k in [
            "candidate_payload_written",
            "candidate_files_created",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
        ]:
            if assertions.get(k) is not False:
                errors.append(f"D160 assertions {k} must be false")
        errors.extend(validate_no_ai_execution(assertions, prefix="D160 assertions"))

    if not d161_scope:
        errors.append("missing D160 D161 sandbox candidate reentry test plan scope")
    else:
        if d161_scope.get("ok") is not True:
            errors.append("D160 D161 scope ok must be true")
        if d161_scope.get("allowed_next_gate") != REQ_D161_GATE:
            errors.append("D160 D161 scope allowed_next_gate must be D161")
        if d161_scope.get("sandbox_candidate_reentry_test_plan_scope_only") is not True:
            errors.append("D160 D161 scope must be test-plan-only")
        if d161_scope.get("fresh_intent_required") is not True:
            errors.append("D160 D161 scope must require fresh intent")
        if d161_scope.get("provider_response_required_before_candidate") is not True:
            errors.append("D160 D161 scope must require provider response before candidate")
        if d161_scope.get("human_review_required") is not True:
            errors.append("D160 D161 scope must require human review")
        if d161_scope.get("canonical_guard_schema_required") is not True:
            errors.append("D160 D161 scope must require canonical guard schema")
        for k in STATUS_FALSE_D160:
            if d161_scope.get(k) is not False:
                errors.append(f"D160 D161 scope {k} must be false")

    return errors


def build_test_matrix(plan_id, d160):
    return normalize_guard_flags({
        "state": "D161_SANDBOX_CANDIDATE_REENTRY_TEST_MATRIX",
        "ok": True,
        "plan_id": plan_id,
        "review_id": d160.get("review_id"),
        "scope_id": d160.get("scope_id"),
        "intake_id": d160.get("intake_id"),
        "reentry_id": d160.get("reentry_id"),
        "next_cycle_id": d160.get("next_cycle_id"),
        "cycle_closure_id": d160.get("cycle_closure_id"),
        "previous_candidate_id": d160.get("previous_candidate_id"),
        "proposal_id": d160.get("proposal_id"),
        "created_at": now(),
        "test_matrix_status": "TEST_MATRIX_CREATED_DRY_PLAN_ONLY_NO_CANDIDATE_EXECUTION",
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "provider_response_required_before_candidate": True,
        "human_review_required": True,
        "candidate_payload_available": False,
        "candidate_payload_written": False,
        "candidate_files_created": False,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "dry_test_plan_only": True,
        "test_items": [
            {
                "id": "D161-T1",
                "name": "validate canonical guard schema presence",
                "kind": "schema",
                "must_not_execute_candidate": True,
            },
            {
                "id": "D161-T2",
                "name": "assert provider response is still not ingested",
                "kind": "status",
                "must_not_call_provider": True,
            },
            {
                "id": "D161-T3",
                "name": "assert candidate payload is still not written",
                "kind": "safety",
                "must_not_write_candidate_payload": True,
            },
            {
                "id": "D161-T4",
                "name": "assert no apply route exists",
                "kind": "guard",
                "must_not_apply": True,
            },
            {
                "id": "D161-T5",
                "name": "assert no shell/network/secret/git action by AI",
                "kind": "no_touch",
                "must_not_touch_external_surfaces": True,
            },
        ],
    })


def build_no_touch_assertions(plan_id, d160):
    return normalize_guard_flags({
        "state": "D161_SANDBOX_CANDIDATE_REENTRY_NO_TOUCH_ASSERTIONS",
        "ok": True,
        "plan_id": plan_id,
        "review_id": d160.get("review_id"),
        "scope_id": d160.get("scope_id"),
        "intake_id": d160.get("intake_id"),
        "reentry_id": d160.get("reentry_id"),
        "created_at": now(),
        "assertion_mode": "SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_NO_TOUCH_ASSERTIONS",
        "canonical_guard_schema_applied": True,
        "no_candidate_payload_write": True,
        "no_candidate_execution": True,
        "no_test_execution": True,
        "no_apply": True,
        "no_network": True,
        "no_secret_read": True,
        "no_shell": True,
        "no_route_insert": True,
        "no_core_mutation_by_ai": True,
        "no_git_action_by_ai": True,
        "candidate_payload_written": False,
        "candidate_files_created": False,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "tests_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "human_review_required": True,
    })


def build_d162_scope(plan_id, d160):
    return {
        "state": "D161_D162_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE",
        "ok": True,
        "plan_id": plan_id,
        "review_id": d160.get("review_id"),
        "scope_id": d160.get("scope_id"),
        "intake_id": d160.get("intake_id"),
        "reentry_id": d160.get("reentry_id"),
        "next_cycle_id": d160.get("next_cycle_id"),
        "cycle_closure_id": d160.get("cycle_closure_id"),
        "previous_candidate_id": d160.get("previous_candidate_id"),
        "proposal_id": d160.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D162_GATE,
        "sandbox_candidate_reentry_dry_test_runner_scope_only": True,
        "fresh_intent_required": True,
        "provider_response_required_before_candidate": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d162_allowed_to_create": [
            "sandbox_candidate_reentry_dry_test_runner_scope",
            "sandbox_candidate_reentry_dry_test_report",
            "sandbox_candidate_reentry_test_safety_receipt",
            "d163_provider_response_reentry_scope",
        ],
        "d162_must_not_execute": [
            "real_provider_call",
            "candidate_payload_write",
            "candidate_execution",
            "real_core_apply",
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
        "real_apply_allowed_after_d161_by_ai": False,
        "route_insert_allowed_after_d161_by_ai": False,
        "protected_core_mutation_allowed_after_d161_by_ai": False,
        "network_allowed_after_d161_by_ai": False,
        "secret_read_allowed_after_d161_by_ai": False,
        "shell_allowed_after_d161_by_ai": False,
        "git_action_allowed_after_d161_by_ai": False,
    }


def create_sandbox_candidate_reentry_test_plan_scope(root="."):
    root = Path(root).resolve()

    d160 = read_json(root / D160_REPORT, {}) or {}
    review_packet = read_json(root / D160_REVIEW_PACKET, {}) or {}
    assertions = read_json(root / D160_ASSERTIONS, {}) or {}
    d161_scope = read_json(root / D160_D161_SCOPE, {}) or {}

    errors = validate_d160(d160, review_packet, assertions, d161_scope)

    plan_id = "d161-" + digest({
        "review_id": d160.get("review_id"),
        "scope_id": d160.get("scope_id"),
        "intake_id": d160.get("intake_id"),
        "reentry_id": d160.get("reentry_id"),
        "next_cycle_id": d160.get("next_cycle_id"),
        "proposal_id": d160.get("proposal_id"),
    })

    test_matrix = build_test_matrix(plan_id, d160)
    no_touch_assertions = build_no_touch_assertions(plan_id, d160)
    d162_scope = build_d162_scope(plan_id, d160)

    for name, item in [("test_matrix", test_matrix), ("no_touch_assertions", no_touch_assertions)]:
        errors.extend(validate_no_ai_execution(item, prefix=name))
        for k in [
            "candidate_payload_written",
            "candidate_files_created",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
        ]:
            if item.get(k) is not False:
                errors.append(f"{name}.{k} must be false")
    if no_touch_assertions.get("tests_executed") is not False:
        errors.append("no_touch_assertions.tests_executed must be false")

    for k in [
        "real_apply_allowed_after_d161_by_ai",
        "route_insert_allowed_after_d161_by_ai",
        "protected_core_mutation_allowed_after_d161_by_ai",
        "network_allowed_after_d161_by_ai",
        "secret_read_allowed_after_d161_by_ai",
        "shell_allowed_after_d161_by_ai",
        "git_action_allowed_after_d161_by_ai",
    ]:
        if d162_scope.get(k) is not False:
            errors.append(f"d162_scope.{k} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE_BLOCKED"
    result = "D161_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE_CREATED" if ok else "D161_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE_BLOCKED"

    if ok:
        write_json(root / TEST_MATRIX_OUT, test_matrix)
        write_json(root / NO_TOUCH_ASSERTIONS_OUT, no_touch_assertions)
        write_json(root / D162_SCOPE_OUT, d162_scope)

    report = {
        "state": "D161_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "plan_id": plan_id,
        "review_id": d160.get("review_id"),
        "scope_id": d160.get("scope_id"),
        "intake_id": d160.get("intake_id"),
        "reentry_id": d160.get("reentry_id"),
        "next_cycle_id": d160.get("next_cycle_id"),
        "cycle_closure_id": d160.get("cycle_closure_id"),
        "previous_candidate_id": d160.get("previous_candidate_id"),
        "proposal_id": d160.get("proposal_id"),
        "source_d160_report": D160_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "test_matrix": test_matrix if ok else {},
        "no_touch_assertions": no_touch_assertions if ok else {},
        "d162_scope": d162_scope if ok else {},
        "guardrails": build_no_touch_guardrails(
            sandbox_candidate_reentry_test_plan_scope_only=True,
            sandbox_candidate_reentry_test_matrix_only=True,
            sandbox_candidate_reentry_no_touch_assertions_only=True,
            canonical_guard_schema_applied=True,
            fresh_intent_required=True,
            provider_response_required_before_candidate=True,
            dry_test_plan_only=True,
            candidate_payload_available=False,
            candidate_payload_written=False,
            candidate_files_created=False,
            candidate_execution_requested=False,
            candidate_executed=False,
            tests_executed=False,
            apply_requested=False,
            apply_executed=False,
            approval_for_d162_sandbox_candidate_reentry_dry_test_runner_scope_only=ok,
            real_apply_allowed_after_d161_by_ai=False,
            route_insert_allowed_after_d161_by_ai=False,
            protected_core_mutation_allowed_after_d161_by_ai=False,
            network_allowed_after_d161_by_ai=False,
            secret_read_allowed_after_d161_by_ai=False,
            shell_allowed_after_d161_by_ai=False,
            git_action_allowed_after_d161_by_ai=False,
        ),
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "plan_id": plan_id,
            "review_id": d160.get("review_id"),
            "scope_id": d160.get("scope_id"),
            "intake_id": d160.get("intake_id"),
            "reentry_id": d160.get("reentry_id"),
            "next_cycle_id": d160.get("next_cycle_id"),
            "proposal_id": d160.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D161_PLUS" if ok else "BLOCKED",
            "test_plan_status": "TEST_PLAN_CREATED_DRY_MATRIX_ONLY_NO_TEST_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_STILL_NOT_CREATED_NO_PAYLOAD_WRITTEN" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "test_execution_status": "NOT_EXECUTED",
            "candidate_execution_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D162_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D162_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_test_plan_scope_created": ok,
            "test_matrix_created": ok,
            "no_touch_assertions_created": ok,
            "d162_scope_created": ok,
            "candidate_payload_written": False,
            "candidate_executed": False,
            "tests_executed": False,
            "apply_executed": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D162 may create dry test runner scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_test_plan_scope(), ensure_ascii=False, indent=2))
