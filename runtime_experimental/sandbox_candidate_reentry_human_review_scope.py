
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

D159_REPORT = "reports/d159_proposal_to_sandbox_candidate_reentry_scope.json"
D159_MANIFEST = "reports/d159_sandbox_candidate_reentry_manifest.json"
D159_ASSERTIONS = "reports/d159_sandbox_candidate_reentry_no_touch_assertions.json"
D159_D160_SCOPE = "reports/d159_d160_sandbox_candidate_reentry_human_review_scope.json"

OUT = "reports/d160_sandbox_candidate_reentry_human_review_scope.json"
REVIEW_PACKET_OUT = "reports/d160_sandbox_candidate_reentry_review_packet.json"
NO_APPLY_ASSERTIONS_OUT = "reports/d160_sandbox_candidate_reentry_no_apply_assertions.json"
D161_SCOPE_OUT = "reports/d160_d161_sandbox_candidate_reentry_test_plan_scope.json"

REQ_D159_DECISION = "PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE_READY"
REQ_D160_GATE = "D160_SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE"
REQ_D161_GATE = "D161_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE"

STATUS_FALSE_D159 = [
    "real_apply_allowed_after_d159_by_ai",
    "route_insert_allowed_after_d159_by_ai",
    "protected_core_mutation_allowed_after_d159_by_ai",
    "network_allowed_after_d159_by_ai",
    "secret_read_allowed_after_d159_by_ai",
    "shell_allowed_after_d159_by_ai",
    "git_action_allowed_after_d159_by_ai",
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


def validate_d159(d159, manifest, assertions, d160_scope):
    errors = []

    if not d159:
        return ["missing D159 proposal to sandbox candidate reentry scope report"]

    if d159.get("ok") is not True:
        errors.append("D159 ok must be true")
    if d159.get("decision") != REQ_D159_DECISION:
        errors.append("D159 decision must be PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE_READY")

    summary = d159.get("summary", {})
    expected = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D159_PLUS",
        "candidate_reentry_status": "SANDBOX_CANDIDATE_REENTRY_DECLARED_PROVIDER_RESPONSE_REQUIRED_NOT_MATERIALIZED",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_NOT_CREATED_NO_PAYLOAD_WRITTEN",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D160_SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE_ONLY",
        "next_step": REQ_D160_GATE,
    }
    for k, v in expected.items():
        if summary.get(k) != v:
            errors.append(f"D159 summary.{k} must be {v}")

    guard = normalize_guard_flags(d159.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D159 guardrails"))
    for k in STATUS_FALSE_D159:
        if guard.get(k) is not False:
            errors.append(f"D159 guardrails.{k} must be false")
    for k in [
        "proposal_to_sandbox_candidate_reentry_scope_only",
        "sandbox_candidate_reentry_manifest_only",
        "sandbox_candidate_reentry_no_touch_assertions_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "provider_response_required_before_candidate",
        "approval_for_d160_sandbox_candidate_reentry_human_review_scope_only",
    ]:
        if guard.get(k) is not True:
            errors.append(f"D159 guardrails.{k} must be true")
    for k in [
        "provider_response_ingested",
        "proposal_materialized",
        "candidate_files_created",
        "candidate_payload_written",
        "candidate_summary_written",
        "candidate_manifest_written",
    ]:
        if guard.get(k) is not False:
            errors.append(f"D159 guardrails.{k} must be false")

    if not manifest:
        errors.append("missing D159 sandbox candidate reentry manifest")
    else:
        if manifest.get("ok") is not True:
            errors.append("D159 manifest ok must be true")
        if manifest.get("candidate_reentry_status") != "SANDBOX_CANDIDATE_REENTRY_DECLARED_PROVIDER_RESPONSE_REQUIRED_NOT_MATERIALIZED":
            errors.append("D159 manifest candidate reentry status mismatch")
        for k in ["canonical_guard_schema_applied", "fresh_intent_required", "provider_response_required_before_candidate", "human_review_required"]:
            if manifest.get(k) is not True:
                errors.append(f"D159 manifest {k} must be true")
        for k in [
            "provider_response_ingested",
            "proposal_materialized",
            "candidate_files_created",
            "candidate_payload_written",
            "candidate_summary_written",
            "candidate_manifest_written",
        ]:
            if manifest.get(k) is not False:
                errors.append(f"D159 manifest {k} must be false")
        errors.extend(validate_no_ai_execution(manifest, prefix="D159 manifest"))

    if not assertions:
        errors.append("missing D159 sandbox candidate reentry no touch assertions")
    else:
        if assertions.get("ok") is not True:
            errors.append("D159 assertions ok must be true")
        for k in [
            "canonical_guard_schema_applied",
            "no_candidate_files_written",
            "no_provider_response_ingested",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_apply",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
            "human_review_required",
        ]:
            if assertions.get(k) is not True:
                errors.append(f"D159 assertions {k} must be true")
        for k in [
            "provider_response_ingested",
            "proposal_materialized",
            "candidate_files_created",
            "candidate_payload_written",
            "candidate_summary_written",
            "candidate_manifest_written",
        ]:
            if assertions.get(k) is not False:
                errors.append(f"D159 assertions {k} must be false")
        errors.extend(validate_no_ai_execution(assertions, prefix="D159 assertions"))

    if not d160_scope:
        errors.append("missing D159 D160 sandbox candidate reentry human review scope")
    else:
        if d160_scope.get("ok") is not True:
            errors.append("D159 D160 scope ok must be true")
        if d160_scope.get("allowed_next_gate") != REQ_D160_GATE:
            errors.append("D159 D160 scope allowed_next_gate must be D160")
        if d160_scope.get("sandbox_candidate_reentry_human_review_scope_only") is not True:
            errors.append("D159 D160 scope must be human-review-only")
        if d160_scope.get("fresh_intent_required") is not True:
            errors.append("D159 D160 scope must require fresh intent")
        if d160_scope.get("provider_response_required_before_candidate") is not True:
            errors.append("D159 D160 scope must require provider response before candidate")
        if d160_scope.get("human_review_required") is not True:
            errors.append("D159 D160 scope must require human review")
        if d160_scope.get("canonical_guard_schema_required") is not True:
            errors.append("D159 D160 scope must require canonical guard schema")
        for k in STATUS_FALSE_D159:
            if d160_scope.get(k) is not False:
                errors.append(f"D159 D160 scope {k} must be false")

    return errors


def build_review_packet(review_id, d159):
    return normalize_guard_flags({
        "state": "D160_SANDBOX_CANDIDATE_REENTRY_REVIEW_PACKET",
        "ok": True,
        "review_id": review_id,
        "scope_id": d159.get("scope_id"),
        "intake_id": d159.get("intake_id"),
        "reentry_id": d159.get("reentry_id"),
        "next_cycle_id": d159.get("next_cycle_id"),
        "cycle_closure_id": d159.get("cycle_closure_id"),
        "previous_candidate_id": d159.get("previous_candidate_id"),
        "proposal_id": d159.get("proposal_id"),
        "created_at": now(),
        "review_packet_status": "REVIEW_PACKET_CREATED_NO_CANDIDATE_PAYLOAD_NO_EXECUTION",
        "canonical_guard_schema_applied": True,
        "human_review_required": True,
        "fresh_intent_required": True,
        "provider_response_required_before_candidate": True,
        "candidate_payload_available": False,
        "candidate_payload_written": False,
        "candidate_files_created": False,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "review_notes": [
            "D160 is a human-review gate only.",
            "Provider response is still required before any candidate payload may be materialized.",
            "No candidate payload files are written by D160.",
            "No apply, shell, network, secret read, route insert, protected core mutation, or git action by AI is allowed.",
        ],
    })


def build_no_apply_assertions(review_id, d159):
    return normalize_guard_flags({
        "state": "D160_SANDBOX_CANDIDATE_REENTRY_NO_APPLY_ASSERTIONS",
        "ok": True,
        "review_id": review_id,
        "scope_id": d159.get("scope_id"),
        "intake_id": d159.get("intake_id"),
        "reentry_id": d159.get("reentry_id"),
        "created_at": now(),
        "assertion_mode": "SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_NO_APPLY_ASSERTIONS",
        "canonical_guard_schema_applied": True,
        "no_candidate_payload_write": True,
        "no_candidate_execution": True,
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
        "apply_requested": False,
        "apply_executed": False,
        "human_review_required": True,
    })


def build_d161_scope(review_id, d159):
    return {
        "state": "D160_D161_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE",
        "ok": True,
        "review_id": review_id,
        "scope_id": d159.get("scope_id"),
        "intake_id": d159.get("intake_id"),
        "reentry_id": d159.get("reentry_id"),
        "next_cycle_id": d159.get("next_cycle_id"),
        "cycle_closure_id": d159.get("cycle_closure_id"),
        "previous_candidate_id": d159.get("previous_candidate_id"),
        "proposal_id": d159.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D161_GATE,
        "sandbox_candidate_reentry_test_plan_scope_only": True,
        "fresh_intent_required": True,
        "provider_response_required_before_candidate": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d161_allowed_to_create": [
            "sandbox_candidate_reentry_test_plan_scope",
            "sandbox_candidate_reentry_test_matrix",
            "sandbox_candidate_reentry_no_touch_assertions",
            "d162_sandbox_candidate_reentry_dry_test_runner_scope",
        ],
        "d161_must_not_execute": [
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
        "real_apply_allowed_after_d160_by_ai": False,
        "route_insert_allowed_after_d160_by_ai": False,
        "protected_core_mutation_allowed_after_d160_by_ai": False,
        "network_allowed_after_d160_by_ai": False,
        "secret_read_allowed_after_d160_by_ai": False,
        "shell_allowed_after_d160_by_ai": False,
        "git_action_allowed_after_d160_by_ai": False,
    }


def create_sandbox_candidate_reentry_human_review_scope(root="."):
    root = Path(root).resolve()

    d159 = read_json(root / D159_REPORT, {}) or {}
    manifest = read_json(root / D159_MANIFEST, {}) or {}
    assertions = read_json(root / D159_ASSERTIONS, {}) or {}
    d160_scope = read_json(root / D159_D160_SCOPE, {}) or {}

    errors = validate_d159(d159, manifest, assertions, d160_scope)

    review_id = "d160-" + digest({
        "scope_id": d159.get("scope_id"),
        "intake_id": d159.get("intake_id"),
        "reentry_id": d159.get("reentry_id"),
        "next_cycle_id": d159.get("next_cycle_id"),
        "proposal_id": d159.get("proposal_id"),
    })

    review_packet = build_review_packet(review_id, d159)
    no_apply_assertions = build_no_apply_assertions(review_id, d159)
    d161_scope = build_d161_scope(review_id, d159)

    for name, item in [("review_packet", review_packet), ("no_apply_assertions", no_apply_assertions)]:
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

    for k in [
        "real_apply_allowed_after_d160_by_ai",
        "route_insert_allowed_after_d160_by_ai",
        "protected_core_mutation_allowed_after_d160_by_ai",
        "network_allowed_after_d160_by_ai",
        "secret_read_allowed_after_d160_by_ai",
        "shell_allowed_after_d160_by_ai",
        "git_action_allowed_after_d160_by_ai",
    ]:
        if d161_scope.get(k) is not False:
            errors.append(f"d161_scope.{k} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE_BLOCKED"
    result = "D160_SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE_CREATED" if ok else "D160_SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE_BLOCKED"

    if ok:
        write_json(root / REVIEW_PACKET_OUT, review_packet)
        write_json(root / NO_APPLY_ASSERTIONS_OUT, no_apply_assertions)
        write_json(root / D161_SCOPE_OUT, d161_scope)

    report = {
        "state": "D160_SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "review_id": review_id,
        "scope_id": d159.get("scope_id"),
        "intake_id": d159.get("intake_id"),
        "reentry_id": d159.get("reentry_id"),
        "next_cycle_id": d159.get("next_cycle_id"),
        "cycle_closure_id": d159.get("cycle_closure_id"),
        "previous_candidate_id": d159.get("previous_candidate_id"),
        "proposal_id": d159.get("proposal_id"),
        "source_d159_report": D159_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "review_packet": review_packet if ok else {},
        "no_apply_assertions": no_apply_assertions if ok else {},
        "d161_scope": d161_scope if ok else {},
        "guardrails": build_no_touch_guardrails(
            sandbox_candidate_reentry_human_review_scope_only=True,
            sandbox_candidate_reentry_review_packet_only=True,
            sandbox_candidate_reentry_no_apply_assertions_only=True,
            canonical_guard_schema_applied=True,
            fresh_intent_required=True,
            provider_response_required_before_candidate=True,
            candidate_payload_available=False,
            candidate_payload_written=False,
            candidate_files_created=False,
            candidate_execution_requested=False,
            candidate_executed=False,
            apply_requested=False,
            apply_executed=False,
            approval_for_d161_sandbox_candidate_reentry_test_plan_scope_only=ok,
            real_apply_allowed_after_d160_by_ai=False,
            route_insert_allowed_after_d160_by_ai=False,
            protected_core_mutation_allowed_after_d160_by_ai=False,
            network_allowed_after_d160_by_ai=False,
            secret_read_allowed_after_d160_by_ai=False,
            shell_allowed_after_d160_by_ai=False,
            git_action_allowed_after_d160_by_ai=False,
        ),
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "review_id": review_id,
            "scope_id": d159.get("scope_id"),
            "intake_id": d159.get("intake_id"),
            "reentry_id": d159.get("reentry_id"),
            "next_cycle_id": d159.get("next_cycle_id"),
            "proposal_id": d159.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D160_PLUS" if ok else "BLOCKED",
            "review_status": "HUMAN_REVIEW_PACKET_CREATED_NO_CANDIDATE_PAYLOAD_NO_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_STILL_NOT_CREATED_NO_PAYLOAD_WRITTEN" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D161_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D161_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_human_review_scope_created": ok,
            "review_packet_created": ok,
            "no_apply_assertions_created": ok,
            "d161_scope_created": ok,
            "candidate_payload_written": False,
            "candidate_executed": False,
            "apply_executed": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D161 may create sandbox candidate reentry test plan scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_human_review_scope(), ensure_ascii=False, indent=2))
