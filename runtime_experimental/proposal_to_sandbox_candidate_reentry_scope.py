
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

D158_SCHEMA = "reports/d158_canonical_guard_schema.json"
D158_REPORT = "reports/d158_proposal_cycle_reentry_intake_scope.json"
D158_MANIFEST = "reports/d158_proposal_reentry_intake_manifest.json"
D158_ASSERTIONS = "reports/d158_proposal_reentry_no_execution_assertions.json"
D158_D159_SCOPE = "reports/d158_d159_proposal_to_sandbox_candidate_reentry_scope.json"

OUT = "reports/d159_proposal_to_sandbox_candidate_reentry_scope.json"
CANDIDATE_REENTRY_MANIFEST_OUT = "reports/d159_sandbox_candidate_reentry_manifest.json"
NO_TOUCH_ASSERTIONS_OUT = "reports/d159_sandbox_candidate_reentry_no_touch_assertions.json"
D160_SCOPE_OUT = "reports/d159_d160_sandbox_candidate_reentry_human_review_scope.json"

REQ_D158_DECISION = "PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_READY"
REQ_D159_GATE = "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE"
REQ_D160_GATE = "D160_SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE"

STATUS_FALSE_D158 = [
    "real_apply_allowed_after_d158_by_ai",
    "route_insert_allowed_after_d158_by_ai",
    "protected_core_mutation_allowed_after_d158_by_ai",
    "network_allowed_after_d158_by_ai",
    "secret_read_allowed_after_d158_by_ai",
    "shell_allowed_after_d158_by_ai",
    "git_action_allowed_after_d158_by_ai",
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


def validate_d158(schema, d158, manifest, assertions, d159_scope):
    errors = []

    if not schema:
        errors.append("missing D158 canonical guard schema report")
    else:
        if schema.get("ok") is not True:
            errors.append("D158 canonical schema ok must be true")
        if schema.get("schema_status") != "CANONICAL_GUARD_SCHEMA_CREATED_FOR_D158_PLUS":
            errors.append("D158 canonical schema status must be created for D158 plus")
        if schema.get("normalization_rule") != "MISSING_SAFE_ALIASES_NORMALIZE_TO_FALSE_DANGEROUS_TRUE_FLAGS_BLOCK":
            errors.append("D158 canonical schema normalization rule mismatch")

    if not d158:
        return ["missing D158 proposal cycle reentry intake scope report"]

    if d158.get("ok") is not True:
        errors.append("D158 ok must be true")
    if d158.get("decision") != REQ_D158_DECISION:
        errors.append("D158 decision must be PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_READY")

    summary = d158.get("summary", {})
    expected = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_CREATED_FOR_D158_PLUS",
        "proposal_reentry_status": "PROPOSAL_REENTRY_INTAKE_CREATED_NO_PROVIDER_RESPONSE_NO_EXECUTION",
        "candidate_status": "PROPOSAL_REENTRY_READY_FOR_SANDBOX_CANDIDATE_REENTRY_NOT_CREATED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE_ONLY",
        "next_step": REQ_D159_GATE,
    }
    for k, v in expected.items():
        if summary.get(k) != v:
            errors.append(f"D158 summary.{k} must be {v}")

    guard = normalize_guard_flags(d158.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D158 guardrails"))
    for k in STATUS_FALSE_D158:
        if guard.get(k) is not False:
            errors.append(f"D158 guardrails.{k} must be false")
    for k in [
        "proposal_cycle_reentry_intake_scope_only",
        "proposal_reentry_intake_manifest_only",
        "proposal_reentry_no_execution_assertions_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "approval_for_d159_proposal_to_sandbox_candidate_reentry_scope_only",
    ]:
        if guard.get(k) is not True:
            errors.append(f"D158 guardrails.{k} must be true")
    for k in ["provider_response_ingested", "proposal_materialized", "candidate_created"]:
        if guard.get(k) is not False:
            errors.append(f"D158 guardrails.{k} must be false")

    if not manifest:
        errors.append("missing D158 proposal reentry intake manifest")
    else:
        if manifest.get("ok") is not True:
            errors.append("D158 manifest ok must be true")
        if manifest.get("proposal_reentry_status") != "PROPOSAL_REENTRY_INTAKE_CREATED_NO_PROVIDER_RESPONSE_NO_EXECUTION":
            errors.append("D158 manifest proposal reentry status mismatch")
        for k in ["fresh_intent_required", "provider_response_required_before_candidate", "human_review_required"]:
            if manifest.get(k) is not True:
                errors.append(f"D158 manifest {k} must be true")
        for k in ["real_provider_call_performed", "provider_response_ingested", "proposal_materialized", "candidate_created"]:
            if manifest.get(k) is not False:
                errors.append(f"D158 manifest {k} must be false")
        errors.extend(validate_no_ai_execution(manifest, prefix="D158 manifest"))

    if not assertions:
        errors.append("missing D158 proposal reentry no execution assertions")
    else:
        if assertions.get("ok") is not True:
            errors.append("D158 assertions ok must be true")
        for k in ["no_network", "no_secret_read", "no_shell", "no_apply", "no_route_insert", "no_core_mutation_by_ai", "no_git_action_by_ai", "human_review_required"]:
            if assertions.get(k) is not True:
                errors.append(f"D158 assertions {k} must be true")
        for k in ["real_provider_call_performed", "provider_response_ingested", "proposal_materialized", "candidate_created"]:
            if assertions.get(k) is not False:
                errors.append(f"D158 assertions {k} must be false")
        errors.extend(validate_no_ai_execution(assertions, prefix="D158 assertions"))

    if not d159_scope:
        errors.append("missing D158 D159 proposal to sandbox candidate reentry scope")
    else:
        if d159_scope.get("ok") is not True:
            errors.append("D158 D159 scope ok must be true")
        if d159_scope.get("allowed_next_gate") != REQ_D159_GATE:
            errors.append("D158 D159 scope allowed_next_gate must be D159")
        if d159_scope.get("proposal_to_sandbox_candidate_reentry_scope_only") is not True:
            errors.append("D158 D159 scope must be proposal-to-sandbox-candidate-reentry-only")
        if d159_scope.get("fresh_intent_required") is not True:
            errors.append("D158 D159 scope must require fresh intent")
        if d159_scope.get("provider_response_required_before_candidate") is not True:
            errors.append("D158 D159 scope must require provider response before candidate")
        if d159_scope.get("human_review_required") is not True:
            errors.append("D158 D159 scope must require human review")
        if d159_scope.get("canonical_guard_schema_required") is not True:
            errors.append("D158 D159 scope must require canonical guard schema")
        for k in STATUS_FALSE_D158:
            if d159_scope.get(k) is not False:
                errors.append(f"D158 D159 scope {k} must be false")

    return errors


def build_candidate_reentry_manifest(scope_id, d158):
    return normalize_guard_flags({
        "state": "D159_SANDBOX_CANDIDATE_REENTRY_MANIFEST",
        "ok": True,
        "scope_id": scope_id,
        "intake_id": d158.get("intake_id"),
        "reentry_id": d158.get("reentry_id"),
        "next_cycle_id": d158.get("next_cycle_id"),
        "cycle_closure_id": d158.get("cycle_closure_id"),
        "previous_candidate_id": d158.get("candidate_id"),
        "proposal_id": d158.get("proposal_id"),
        "created_at": now(),
        "manifest_mode": "SANDBOX_CANDIDATE_REENTRY_MANIFEST_ONLY_NO_CANDIDATE_FILES",
        "candidate_reentry_status": "SANDBOX_CANDIDATE_REENTRY_DECLARED_PROVIDER_RESPONSE_REQUIRED_NOT_MATERIALIZED",
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "provider_response_required_before_candidate": True,
        "provider_response_ingested": False,
        "proposal_materialized": False,
        "candidate_files_created": False,
        "candidate_payload_written": False,
        "candidate_summary_written": False,
        "candidate_manifest_written": False,
        "human_review_required": True,
    })


def build_no_touch_assertions(scope_id, d158):
    return normalize_guard_flags({
        "state": "D159_SANDBOX_CANDIDATE_REENTRY_NO_TOUCH_ASSERTIONS",
        "ok": True,
        "scope_id": scope_id,
        "intake_id": d158.get("intake_id"),
        "reentry_id": d158.get("reentry_id"),
        "next_cycle_id": d158.get("next_cycle_id"),
        "created_at": now(),
        "assertion_mode": "SANDBOX_CANDIDATE_REENTRY_NO_TOUCH_ASSERTIONS",
        "canonical_guard_schema_applied": True,
        "no_candidate_files_written": True,
        "no_provider_response_ingested": True,
        "no_network": True,
        "no_secret_read": True,
        "no_shell": True,
        "no_apply": True,
        "no_route_insert": True,
        "no_core_mutation_by_ai": True,
        "no_git_action_by_ai": True,
        "provider_response_ingested": False,
        "proposal_materialized": False,
        "candidate_files_created": False,
        "candidate_payload_written": False,
        "candidate_summary_written": False,
        "candidate_manifest_written": False,
        "human_review_required": True,
    })


def build_d160_scope(scope_id, d158):
    return {
        "state": "D159_D160_SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE",
        "ok": True,
        "scope_id": scope_id,
        "intake_id": d158.get("intake_id"),
        "reentry_id": d158.get("reentry_id"),
        "next_cycle_id": d158.get("next_cycle_id"),
        "cycle_closure_id": d158.get("cycle_closure_id"),
        "previous_candidate_id": d158.get("candidate_id"),
        "proposal_id": d158.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D160_GATE,
        "sandbox_candidate_reentry_human_review_scope_only": True,
        "fresh_intent_required": True,
        "provider_response_required_before_candidate": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "d160_allowed_to_create": [
            "sandbox_candidate_reentry_human_review_scope",
            "sandbox_candidate_reentry_review_packet",
            "sandbox_candidate_reentry_no_apply_assertions",
            "d161_sandbox_candidate_reentry_test_plan_scope",
        ],
        "d160_must_not_execute": [
            "real_provider_call",
            "candidate_payload_write",
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
        "real_apply_allowed_after_d159_by_ai": False,
        "route_insert_allowed_after_d159_by_ai": False,
        "protected_core_mutation_allowed_after_d159_by_ai": False,
        "network_allowed_after_d159_by_ai": False,
        "secret_read_allowed_after_d159_by_ai": False,
        "shell_allowed_after_d159_by_ai": False,
        "git_action_allowed_after_d159_by_ai": False,
    }


def create_proposal_to_sandbox_candidate_reentry_scope(root="."):
    root = Path(root).resolve()

    schema = read_json(root / D158_SCHEMA, {}) or {}
    d158 = read_json(root / D158_REPORT, {}) or {}
    manifest = read_json(root / D158_MANIFEST, {}) or {}
    assertions = read_json(root / D158_ASSERTIONS, {}) or {}
    d159_scope = read_json(root / D158_D159_SCOPE, {}) or {}

    errors = validate_d158(schema, d158, manifest, assertions, d159_scope)

    scope_id = "d159-" + digest({
        "intake_id": d158.get("intake_id"),
        "reentry_id": d158.get("reentry_id"),
        "next_cycle_id": d158.get("next_cycle_id"),
        "candidate_id": d158.get("candidate_id"),
        "proposal_id": d158.get("proposal_id"),
    })

    candidate_manifest = build_candidate_reentry_manifest(scope_id, d158)
    no_touch_assertions = build_no_touch_assertions(scope_id, d158)
    d160_scope = build_d160_scope(scope_id, d158)

    for name, item in [("candidate_manifest", candidate_manifest), ("no_touch_assertions", no_touch_assertions)]:
        errors.extend(validate_no_ai_execution(item, prefix=name))
        for k in ["provider_response_ingested", "proposal_materialized", "candidate_files_created", "candidate_payload_written", "candidate_summary_written", "candidate_manifest_written"]:
            if item.get(k) is not False:
                errors.append(f"{name}.{k} must be false")

    for k in [
        "real_apply_allowed_after_d159_by_ai",
        "route_insert_allowed_after_d159_by_ai",
        "protected_core_mutation_allowed_after_d159_by_ai",
        "network_allowed_after_d159_by_ai",
        "secret_read_allowed_after_d159_by_ai",
        "shell_allowed_after_d159_by_ai",
        "git_action_allowed_after_d159_by_ai",
    ]:
        if d160_scope.get(k) is not False:
            errors.append(f"d160_scope.{k} must be false")

    ok = not errors
    decision = "PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE_READY" if ok else "PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE_BLOCKED"
    result = "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE_CREATED" if ok else "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE_BLOCKED"

    if ok:
        write_json(root / CANDIDATE_REENTRY_MANIFEST_OUT, candidate_manifest)
        write_json(root / NO_TOUCH_ASSERTIONS_OUT, no_touch_assertions)
        write_json(root / D160_SCOPE_OUT, d160_scope)

    report = {
        "state": "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "scope_id": scope_id,
        "intake_id": d158.get("intake_id"),
        "reentry_id": d158.get("reentry_id"),
        "next_cycle_id": d158.get("next_cycle_id"),
        "cycle_closure_id": d158.get("cycle_closure_id"),
        "previous_candidate_id": d158.get("candidate_id"),
        "proposal_id": d158.get("proposal_id"),
        "source_d158_report": D158_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "sandbox_candidate_reentry_manifest": candidate_manifest if ok else {},
        "sandbox_candidate_reentry_no_touch_assertions": no_touch_assertions if ok else {},
        "d160_scope": d160_scope if ok else {},
        "guardrails": build_no_touch_guardrails(
            proposal_to_sandbox_candidate_reentry_scope_only=True,
            sandbox_candidate_reentry_manifest_only=True,
            sandbox_candidate_reentry_no_touch_assertions_only=True,
            canonical_guard_schema_applied=True,
            fresh_intent_required=True,
            provider_response_required_before_candidate=True,
            provider_response_ingested=False,
            proposal_materialized=False,
            candidate_files_created=False,
            candidate_payload_written=False,
            candidate_summary_written=False,
            candidate_manifest_written=False,
            approval_for_d160_sandbox_candidate_reentry_human_review_scope_only=ok,
            real_apply_allowed_after_d159_by_ai=False,
            route_insert_allowed_after_d159_by_ai=False,
            protected_core_mutation_allowed_after_d159_by_ai=False,
            network_allowed_after_d159_by_ai=False,
            secret_read_allowed_after_d159_by_ai=False,
            shell_allowed_after_d159_by_ai=False,
            git_action_allowed_after_d159_by_ai=False,
        ),
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "scope_id": scope_id,
            "intake_id": d158.get("intake_id"),
            "reentry_id": d158.get("reentry_id"),
            "next_cycle_id": d158.get("next_cycle_id"),
            "proposal_id": d158.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D159_PLUS" if ok else "BLOCKED",
            "candidate_reentry_status": "SANDBOX_CANDIDATE_REENTRY_DECLARED_PROVIDER_RESPONSE_REQUIRED_NOT_MATERIALIZED" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_NOT_CREATED_NO_PAYLOAD_WRITTEN" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D160_SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D160_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "proposal_to_sandbox_candidate_reentry_scope_created": ok,
            "sandbox_candidate_reentry_manifest_created": ok,
            "sandbox_candidate_reentry_no_touch_assertions_created": ok,
            "d160_scope_created": ok,
            "provider_response_ingested": False,
            "candidate_payload_written": False,
            "candidate_files_created": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D160 may create sandbox candidate reentry human review scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_proposal_to_sandbox_candidate_reentry_scope(), ensure_ascii=False, indent=2))
