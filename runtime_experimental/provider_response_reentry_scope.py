
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

D162_REPORT = "reports/d162_sandbox_candidate_reentry_dry_test_runner_scope.json"
D162_DRY_REPORT = "reports/d162_sandbox_candidate_reentry_dry_test_report.json"
D162_SAFETY_RECEIPT = "reports/d162_sandbox_candidate_reentry_test_safety_receipt.json"
D162_D163_SCOPE = "reports/d162_d163_provider_response_reentry_scope.json"

OUT = "reports/d163_provider_response_reentry_scope.json"
MANIFEST_OUT = "reports/d163_provider_response_reentry_manifest.json"
DRY_CAPTURE_RECEIPT_OUT = "reports/d163_provider_response_reentry_dry_capture_receipt.json"
D164_SCOPE_OUT = "reports/d163_d164_sandbox_candidate_reentry_materialization_scope.json"

REQ_D162_DECISION = "SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE_READY"
REQ_D163_GATE = "D163_PROVIDER_RESPONSE_REENTRY_SCOPE"
REQ_D164_GATE = "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE"

STATUS_FALSE_D162 = [
    "real_apply_allowed_after_d162_by_ai",
    "route_insert_allowed_after_d162_by_ai",
    "protected_core_mutation_allowed_after_d162_by_ai",
    "network_allowed_after_d162_by_ai",
    "secret_read_allowed_after_d162_by_ai",
    "shell_allowed_after_d162_by_ai",
    "git_action_allowed_after_d162_by_ai",
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


def validate_d162(d162, dry_report, safety_receipt, d163_scope):
    errors = []

    if not d162:
        return ["missing D162 sandbox candidate reentry dry test runner scope report"]

    if d162.get("ok") is not True:
        errors.append("D162 ok must be true")
    if d162.get("decision") != REQ_D162_DECISION:
        errors.append("D162 decision must be SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE_READY")

    summary = d162.get("summary", {})
    expected = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D162_PLUS",
        "dry_test_status": "DRY_TEST_METADATA_EVALUATED_NO_CANDIDATE_EXECUTION",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_STILL_NOT_CREATED_NO_PAYLOAD_WRITTEN",
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
        "approval_scope": "D163_PROVIDER_RESPONSE_REENTRY_SCOPE_ONLY",
        "next_step": REQ_D163_GATE,
    }
    for k, v in expected.items():
        if summary.get(k) != v:
            errors.append(f"D162 summary.{k} must be {v}")

    guard = normalize_guard_flags(d162.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D162 guardrails"))
    for k in STATUS_FALSE_D162:
        if guard.get(k) is not False:
            errors.append(f"D162 guardrails.{k} must be false")
    for k in [
        "sandbox_candidate_reentry_dry_test_runner_scope_only",
        "sandbox_candidate_reentry_dry_test_report_only",
        "sandbox_candidate_reentry_test_safety_receipt_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "provider_response_required_before_candidate",
        "dry_tests_evaluated",
        "approval_for_d163_provider_response_reentry_scope_only",
    ]:
        if guard.get(k) is not True:
            errors.append(f"D162 guardrails.{k} must be true")
    for k in [
        "tests_executed",
        "candidate_payload_available",
        "candidate_payload_written",
        "candidate_files_created",
        "candidate_execution_requested",
        "candidate_executed",
        "provider_response_ingested",
        "apply_requested",
        "apply_executed",
    ]:
        if guard.get(k) is not False:
            errors.append(f"D162 guardrails.{k} must be false")

    if not dry_report:
        errors.append("missing D162 dry test report")
    else:
        if dry_report.get("ok") is not True:
            errors.append("D162 dry report ok must be true")
        if dry_report.get("dry_test_report_status") != "DRY_TEST_METADATA_EVALUATED_NO_CANDIDATE_EXECUTION":
            errors.append("D162 dry report status mismatch")
        for k in ["canonical_guard_schema_applied", "dry_runner_scope_only", "dry_tests_evaluated", "provider_response_required_before_candidate"]:
            if dry_report.get(k) is not True:
                errors.append(f"D162 dry report {k} must be true")
        for k in [
            "tests_executed",
            "candidate_payload_available",
            "candidate_payload_written",
            "candidate_files_created",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "provider_response_ingested",
        ]:
            if dry_report.get(k) is not False:
                errors.append(f"D162 dry report {k} must be false")
        if dry_report.get("evaluated_count", 0) < 5:
            errors.append("D162 dry report evaluated_count must be at least 5")
        errors.extend(validate_no_ai_execution(dry_report, prefix="D162 dry_report"))

    if not safety_receipt:
        errors.append("missing D162 safety receipt")
    else:
        if safety_receipt.get("ok") is not True:
            errors.append("D162 safety receipt ok must be true")
        if safety_receipt.get("safety_receipt_status") != "DRY_TEST_RUNNER_RECORDED_NO_TOUCH_NO_CANDIDATE_EXECUTION":
            errors.append("D162 safety receipt status mismatch")
        for k in [
            "canonical_guard_schema_applied",
            "dry_tests_evaluated",
            "no_candidate_payload_write",
            "no_candidate_execution",
            "no_real_test_execution",
            "no_apply",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
            "human_review_required",
        ]:
            if safety_receipt.get(k) is not True:
                errors.append(f"D162 safety receipt {k} must be true")
        for k in [
            "tests_executed",
            "candidate_payload_written",
            "candidate_files_created",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
        ]:
            if safety_receipt.get(k) is not False:
                errors.append(f"D162 safety receipt {k} must be false")
        errors.extend(validate_no_ai_execution(safety_receipt, prefix="D162 safety_receipt"))

    if not d163_scope:
        errors.append("missing D162 D163 provider response reentry scope")
    else:
        if d163_scope.get("ok") is not True:
            errors.append("D162 D163 scope ok must be true")
        if d163_scope.get("allowed_next_gate") != REQ_D163_GATE:
            errors.append("D162 D163 scope allowed_next_gate must be D163")
        if d163_scope.get("provider_response_reentry_scope_only") is not True:
            errors.append("D162 D163 scope must be provider-response-reentry-only")
        if d163_scope.get("fresh_intent_required") is not True:
            errors.append("D162 D163 scope must require fresh intent")
        if d163_scope.get("provider_response_required_before_candidate") is not True:
            errors.append("D162 D163 scope must require provider response before candidate")
        if d163_scope.get("human_review_required") is not True:
            errors.append("D162 D163 scope must require human review")
        if d163_scope.get("canonical_guard_schema_required") is not True:
            errors.append("D162 D163 scope must require canonical guard schema")
        for k in STATUS_FALSE_D162:
            if d163_scope.get(k) is not False:
                errors.append(f"D162 D163 scope {k} must be false")

    return errors


def build_manifest(response_id, d162):
    return normalize_guard_flags({
        "state": "D163_PROVIDER_RESPONSE_REENTRY_MANIFEST",
        "ok": True,
        "response_id": response_id,
        "runner_id": d162.get("runner_id"),
        "plan_id": d162.get("plan_id"),
        "review_id": d162.get("review_id"),
        "scope_id": d162.get("scope_id"),
        "intake_id": d162.get("intake_id"),
        "reentry_id": d162.get("reentry_id"),
        "next_cycle_id": d162.get("next_cycle_id"),
        "cycle_closure_id": d162.get("cycle_closure_id"),
        "previous_candidate_id": d162.get("previous_candidate_id"),
        "proposal_id": d162.get("proposal_id"),
        "created_at": now(),
        "manifest_status": "PROVIDER_RESPONSE_REENTRY_DECLARED_DRY_CAPTURE_ONLY_NO_PROVIDER_CALL",
        "canonical_guard_schema_applied": True,
        "provider_response_reentry_scope_only": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "provider_response_capture_mode": "DRY_CAPTURE_PLACEHOLDER_ONLY",
        "provider_response_required_before_candidate": True,
        "candidate_materialization_allowed_next": True,
        "candidate_payload_written": False,
        "candidate_files_created": False,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
    })


def build_dry_capture_receipt(response_id, d162):
    return normalize_guard_flags({
        "state": "D163_PROVIDER_RESPONSE_REENTRY_DRY_CAPTURE_RECEIPT",
        "ok": True,
        "response_id": response_id,
        "runner_id": d162.get("runner_id"),
        "plan_id": d162.get("plan_id"),
        "review_id": d162.get("review_id"),
        "scope_id": d162.get("scope_id"),
        "intake_id": d162.get("intake_id"),
        "reentry_id": d162.get("reentry_id"),
        "created_at": now(),
        "receipt_status": "DRY_PROVIDER_RESPONSE_CAPTURE_RECORDED_NO_NETWORK_NO_SECRET_NO_PROVIDER_CALL",
        "canonical_guard_schema_applied": True,
        "dry_capture_only": True,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "candidate_payload_written": False,
        "candidate_files_created": False,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "no_provider_call": True,
        "no_network": True,
        "no_secret_read": True,
        "no_shell": True,
        "no_candidate_payload_write": True,
        "no_candidate_execution": True,
        "no_apply": True,
        "no_route_insert": True,
        "no_core_mutation_by_ai": True,
        "no_git_action_by_ai": True,
        "human_review_required": True,
    })


def build_d164_scope(response_id, d162):
    return {
        "state": "D163_D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE",
        "ok": True,
        "response_id": response_id,
        "runner_id": d162.get("runner_id"),
        "plan_id": d162.get("plan_id"),
        "review_id": d162.get("review_id"),
        "scope_id": d162.get("scope_id"),
        "intake_id": d162.get("intake_id"),
        "reentry_id": d162.get("reentry_id"),
        "next_cycle_id": d162.get("next_cycle_id"),
        "cycle_closure_id": d162.get("cycle_closure_id"),
        "previous_candidate_id": d162.get("previous_candidate_id"),
        "proposal_id": d162.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D164_GATE,
        "sandbox_candidate_reentry_materialization_scope_only": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "provider_response_required_before_candidate": True,
        "provider_response_capture_required_or_dry_placeholder_allowed": True,
        "d164_allowed_to_create": [
            "sandbox_candidate_reentry_materialization_scope",
            "sandbox_candidate_reentry_materialization_manifest",
            "sandbox_candidate_reentry_materialization_preflight",
            "d165_sandbox_candidate_reentry_static_validation_scope",
        ],
        "d164_must_not_execute": [
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
        "real_apply_allowed_after_d163_by_ai": False,
        "route_insert_allowed_after_d163_by_ai": False,
        "protected_core_mutation_allowed_after_d163_by_ai": False,
        "network_allowed_after_d163_by_ai": False,
        "secret_read_allowed_after_d163_by_ai": False,
        "shell_allowed_after_d163_by_ai": False,
        "git_action_allowed_after_d163_by_ai": False,
    }


def create_provider_response_reentry_scope(root="."):
    root = Path(root).resolve()

    d162 = read_json(root / D162_REPORT, {}) or {}
    dry_report = read_json(root / D162_DRY_REPORT, {}) or {}
    safety_receipt = read_json(root / D162_SAFETY_RECEIPT, {}) or {}
    d163_scope = read_json(root / D162_D163_SCOPE, {}) or {}

    errors = validate_d162(d162, dry_report, safety_receipt, d163_scope)

    response_id = "d163-" + digest({
        "runner_id": d162.get("runner_id"),
        "plan_id": d162.get("plan_id"),
        "review_id": d162.get("review_id"),
        "scope_id": d162.get("scope_id"),
        "intake_id": d162.get("intake_id"),
        "reentry_id": d162.get("reentry_id"),
        "next_cycle_id": d162.get("next_cycle_id"),
        "proposal_id": d162.get("proposal_id"),
    })

    manifest = build_manifest(response_id, d162)
    dry_capture_receipt = build_dry_capture_receipt(response_id, d162)
    d164_scope = build_d164_scope(response_id, d162)

    for name, item in [("manifest", manifest), ("dry_capture_receipt", dry_capture_receipt)]:
        errors.extend(validate_no_ai_execution(item, prefix=name))
        for k in [
            "real_provider_call_performed",
            "provider_response_ingested",
            "provider_response_captured",
            "candidate_payload_written",
            "candidate_files_created",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
        ]:
            if item.get(k) is not False:
                errors.append(f"{name}.{k} must be false")
    if manifest.get("candidate_materialization_allowed_next") is not True:
        errors.append("manifest.candidate_materialization_allowed_next must be true")
    if dry_capture_receipt.get("dry_capture_only") is not True:
        errors.append("dry_capture_receipt.dry_capture_only must be true")

    for k in [
        "real_apply_allowed_after_d163_by_ai",
        "route_insert_allowed_after_d163_by_ai",
        "protected_core_mutation_allowed_after_d163_by_ai",
        "network_allowed_after_d163_by_ai",
        "secret_read_allowed_after_d163_by_ai",
        "shell_allowed_after_d163_by_ai",
        "git_action_allowed_after_d163_by_ai",
    ]:
        if d164_scope.get(k) is not False:
            errors.append(f"d164_scope.{k} must be false")

    ok = not errors
    decision = "PROVIDER_RESPONSE_REENTRY_SCOPE_READY" if ok else "PROVIDER_RESPONSE_REENTRY_SCOPE_BLOCKED"
    result = "D163_PROVIDER_RESPONSE_REENTRY_SCOPE_CREATED" if ok else "D163_PROVIDER_RESPONSE_REENTRY_SCOPE_BLOCKED"

    if ok:
        write_json(root / MANIFEST_OUT, manifest)
        write_json(root / DRY_CAPTURE_RECEIPT_OUT, dry_capture_receipt)
        write_json(root / D164_SCOPE_OUT, d164_scope)

    report = {
        "state": "D163_PROVIDER_RESPONSE_REENTRY_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_PROVIDER_RESPONSE_REENTRY_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "response_id": response_id,
        "runner_id": d162.get("runner_id"),
        "plan_id": d162.get("plan_id"),
        "review_id": d162.get("review_id"),
        "scope_id": d162.get("scope_id"),
        "intake_id": d162.get("intake_id"),
        "reentry_id": d162.get("reentry_id"),
        "next_cycle_id": d162.get("next_cycle_id"),
        "cycle_closure_id": d162.get("cycle_closure_id"),
        "previous_candidate_id": d162.get("previous_candidate_id"),
        "proposal_id": d162.get("proposal_id"),
        "source_d162_report": D162_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "provider_response_reentry_manifest": manifest if ok else {},
        "provider_response_reentry_dry_capture_receipt": dry_capture_receipt if ok else {},
        "d164_scope": d164_scope if ok else {},
        "guardrails": build_no_touch_guardrails(
            provider_response_reentry_scope_only=True,
            provider_response_reentry_manifest_only=True,
            provider_response_reentry_dry_capture_receipt_only=True,
            canonical_guard_schema_applied=True,
            fresh_intent_required=True,
            human_review_required=True,
            real_provider_call_performed=False,
            provider_response_ingested=False,
            provider_response_captured=False,
            dry_capture_only=True,
            candidate_materialization_allowed_next=ok,
            candidate_payload_written=False,
            candidate_files_created=False,
            candidate_execution_requested=False,
            candidate_executed=False,
            apply_requested=False,
            apply_executed=False,
            approval_for_d164_sandbox_candidate_reentry_materialization_scope_only=ok,
            real_apply_allowed_after_d163_by_ai=False,
            route_insert_allowed_after_d163_by_ai=False,
            protected_core_mutation_allowed_after_d163_by_ai=False,
            network_allowed_after_d163_by_ai=False,
            secret_read_allowed_after_d163_by_ai=False,
            shell_allowed_after_d163_by_ai=False,
            git_action_allowed_after_d163_by_ai=False,
        ),
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "response_id": response_id,
            "runner_id": d162.get("runner_id"),
            "plan_id": d162.get("plan_id"),
            "review_id": d162.get("review_id"),
            "scope_id": d162.get("scope_id"),
            "intake_id": d162.get("intake_id"),
            "reentry_id": d162.get("reentry_id"),
            "next_cycle_id": d162.get("next_cycle_id"),
            "proposal_id": d162.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D163_PLUS" if ok else "BLOCKED",
            "provider_response_status": "DRY_CAPTURE_DECLARED_NO_PROVIDER_CALL_NO_NETWORK" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_MATERIALIZATION_SCOPE_NOT_WRITTEN" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D164_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "provider_response_reentry_scope_created": ok,
            "provider_response_reentry_manifest_created": ok,
            "dry_capture_receipt_created": ok,
            "d164_scope_created": ok,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "candidate_payload_written": False,
            "candidate_executed": False,
            "apply_executed": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D164 may create sandbox candidate reentry materialization scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_provider_response_reentry_scope(), ensure_ascii=False, indent=2))
