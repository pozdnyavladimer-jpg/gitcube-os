
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from runtime_experimental.canonical_guard_schema import (
    canonical_schema_report,
    normalize_guard_flags,
    validate_no_ai_execution,
)

D163_REPORT = "reports/d163_provider_response_reentry_scope.json"
D163_MANIFEST = "reports/d163_provider_response_reentry_manifest.json"
D163_DRY_CAPTURE_RECEIPT = "reports/d163_provider_response_reentry_dry_capture_receipt.json"
D163_D164_SCOPE = "reports/d163_d164_sandbox_candidate_reentry_materialization_scope.json"

OUT = "reports/d164_sandbox_candidate_reentry_materialization_scope.json"
MATERIALIZATION_MANIFEST_OUT = "reports/d164_sandbox_candidate_reentry_materialization_manifest.json"
PREFLIGHT_OUT = "reports/d164_sandbox_candidate_reentry_materialization_preflight.json"
D165_SCOPE_OUT = "reports/d164_d165_sandbox_candidate_reentry_static_validation_scope.json"

REQ_D163_DECISION = "PROVIDER_RESPONSE_REENTRY_SCOPE_READY"
REQ_D164_GATE = "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE"
REQ_D165_GATE = "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE"

DANGEROUS_AFTER_D163_FALSE = [
    "real_apply_allowed_after_d163_by_ai",
    "route_insert_allowed_after_d163_by_ai",
    "protected_core_mutation_allowed_after_d163_by_ai",
    "network_allowed_after_d163_by_ai",
    "secret_read_allowed_after_d163_by_ai",
    "shell_allowed_after_d163_by_ai",
    "git_action_allowed_after_d163_by_ai",
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


def require_false(obj, keys, label, errors):
    for k in keys:
        if obj.get(k) is not False:
            errors.append(f"{label}.{k} must be false")


def require_true(obj, keys, label, errors):
    for k in keys:
        if obj.get(k) is not True:
            errors.append(f"{label}.{k} must be true")


def validate_d163(d163, manifest, receipt, d164_scope):
    errors = []

    if not d163:
        return ["missing D163 provider response reentry scope report"]
    if d163.get("ok") is not True:
        errors.append("D163 ok must be true")
    if d163.get("decision") != REQ_D163_DECISION:
        errors.append("D163 decision must be PROVIDER_RESPONSE_REENTRY_SCOPE_READY")

    summary = d163.get("summary", {})
    expected_summary = {
        "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D163_PLUS",
        "provider_response_status": "DRY_CAPTURE_DECLARED_NO_PROVIDER_CALL_NO_NETWORK",
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_MATERIALIZATION_SCOPE_NOT_WRITTEN",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "candidate_execution_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_ONLY",
        "next_step": REQ_D164_GATE,
    }
    for k, v in expected_summary.items():
        if summary.get(k) != v:
            errors.append(f"D163 summary.{k} must be {v}")

    guard = normalize_guard_flags(d163.get("guardrails", {}))
    errors.extend(validate_no_ai_execution(guard, prefix="D163 guardrails"))
    require_true(guard, [
        "provider_response_reentry_scope_only",
        "provider_response_reentry_manifest_only",
        "provider_response_reentry_dry_capture_receipt_only",
        "canonical_guard_schema_applied",
        "fresh_intent_required",
        "human_review_required",
        "dry_capture_only",
        "candidate_materialization_allowed_next",
        "approval_for_d164_sandbox_candidate_reentry_materialization_scope_only",
    ], "D163 guardrails", errors)
    require_false(guard, [
        "real_provider_call_performed",
        "provider_response_ingested",
        "provider_response_captured",
        "candidate_payload_written",
        "candidate_files_created",
        "candidate_execution_requested",
        "candidate_executed",
        "apply_requested",
        "apply_executed",
        *DANGEROUS_AFTER_D163_FALSE,
    ], "D163 guardrails", errors)

    if not manifest:
        errors.append("missing D163 provider response reentry manifest")
    else:
        if manifest.get("ok") is not True:
            errors.append("D163 manifest ok must be true")
        if manifest.get("manifest_status") != "PROVIDER_RESPONSE_REENTRY_DECLARED_DRY_CAPTURE_ONLY_NO_PROVIDER_CALL":
            errors.append("D163 manifest status mismatch")
        require_true(manifest, [
            "canonical_guard_schema_applied",
            "provider_response_reentry_scope_only",
            "fresh_intent_required",
            "human_review_required",
            "provider_response_required_before_candidate",
            "candidate_materialization_allowed_next",
        ], "D163 manifest", errors)
        require_false(manifest, [
            "real_provider_call_performed",
            "provider_response_ingested",
            "provider_response_captured",
            "candidate_payload_written",
            "candidate_files_created",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
        ], "D163 manifest", errors)
        errors.extend(validate_no_ai_execution(manifest, prefix="D163 manifest"))

    if not receipt:
        errors.append("missing D163 dry capture receipt")
    else:
        if receipt.get("ok") is not True:
            errors.append("D163 dry capture receipt ok must be true")
        if receipt.get("receipt_status") != "DRY_PROVIDER_RESPONSE_CAPTURE_RECORDED_NO_NETWORK_NO_SECRET_NO_PROVIDER_CALL":
            errors.append("D163 dry capture receipt status mismatch")
        require_true(receipt, [
            "canonical_guard_schema_applied",
            "dry_capture_only",
            "no_provider_call",
            "no_network",
            "no_secret_read",
            "no_shell",
            "no_candidate_payload_write",
            "no_candidate_execution",
            "no_apply",
            "no_route_insert",
            "no_core_mutation_by_ai",
            "no_git_action_by_ai",
            "human_review_required",
        ], "D163 dry capture receipt", errors)
        require_false(receipt, [
            "real_provider_call_performed",
            "provider_response_ingested",
            "provider_response_captured",
            "network_accessed",
            "secret_read",
            "shell_executed_by_ai",
            "candidate_payload_written",
            "candidate_files_created",
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
        ], "D163 dry capture receipt", errors)
        errors.extend(validate_no_ai_execution(receipt, prefix="D163 dry capture receipt"))

    if not d164_scope:
        errors.append("missing D163 D164 materialization scope")
    else:
        if d164_scope.get("ok") is not True:
            errors.append("D163 D164 scope ok must be true")
        if d164_scope.get("allowed_next_gate") != REQ_D164_GATE:
            errors.append("D163 D164 scope allowed_next_gate must be D164")
        require_true(d164_scope, [
            "sandbox_candidate_reentry_materialization_scope_only",
            "fresh_intent_required",
            "human_review_required",
            "canonical_guard_schema_required",
            "provider_response_required_before_candidate",
            "provider_response_capture_required_or_dry_placeholder_allowed",
        ], "D163 D164 scope", errors)
        require_false(d164_scope, DANGEROUS_AFTER_D163_FALSE, "D163 D164 scope", errors)

    return errors


def base_no_ai_flags():
    return {
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "route_inserted_by_ai": False,
        "protected_core_mutated": False,
        "protected_core_mutated_by_ai": False,
        "git_action_by_ai": False,
    }


def build_candidate_payload(candidate_id, d163):
    data = {
        "state": "D164_SANDBOX_CANDIDATE_REENTRY_PAYLOAD",
        "ok": True,
        "candidate_id": candidate_id,
        "response_id": d163.get("response_id"),
        "runner_id": d163.get("runner_id"),
        "plan_id": d163.get("plan_id"),
        "review_id": d163.get("review_id"),
        "scope_id": d163.get("scope_id"),
        "intake_id": d163.get("intake_id"),
        "reentry_id": d163.get("reentry_id"),
        "next_cycle_id": d163.get("next_cycle_id"),
        "proposal_id": d163.get("proposal_id"),
        "created_at": now(),
        "payload_kind": "NO_OP_REENTRY_PLACEHOLDER_FOR_STATIC_VALIDATION",
        "payload_status": "MATERIALIZED_IN_SANDBOX_ONLY_NO_EXECUTION",
        "source_response_mode": "DRY_CAPTURE_PLACEHOLDER_ONLY",
        "intent": "Create a sandbox-only placeholder candidate for static validation of the reentry pipeline.",
        "operations": [
            {
                "op": "NO_OP",
                "reason": "Provider response was not called or ingested; placeholder exists only to test validation gates.",
                "writes_core": False,
                "executes_code": False,
                "requires_network": False,
                "requires_secrets": False,
                "requires_shell": False,
            }
        ],
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_candidate_manifest(candidate_id, d163, work_dir):
    data = {
        "state": "D164_SANDBOX_CANDIDATE_REENTRY_CANDIDATE_MANIFEST",
        "ok": True,
        "candidate_id": candidate_id,
        "response_id": d163.get("response_id"),
        "runner_id": d163.get("runner_id"),
        "plan_id": d163.get("plan_id"),
        "review_id": d163.get("review_id"),
        "scope_id": d163.get("scope_id"),
        "intake_id": d163.get("intake_id"),
        "reentry_id": d163.get("reentry_id"),
        "next_cycle_id": d163.get("next_cycle_id"),
        "proposal_id": d163.get("proposal_id"),
        "created_at": now(),
        "candidate_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION",
        "candidate_work_dir": str(work_dir),
        "candidate_manifest_path": str(work_dir / "candidate_manifest.json"),
        "candidate_payload_path": str(work_dir / "candidate_payload.json"),
        "candidate_summary_path": str(work_dir / "candidate_summary.md"),
        "source_response_mode": "DRY_CAPTURE_PLACEHOLDER_ONLY",
        "candidate_files_created": True,
        "candidate_payload_written": True,
        "candidate_manifest_written": True,
        "candidate_summary_written": True,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_summary_md(candidate_id, d163):
    lines = [
        "# D164 Sandbox Candidate Reentry Materialization",
        "",
        f"- candidate_id: `{candidate_id}`",
        f"- response_id: `{d163.get('response_id')}`",
        f"- proposal_id: `{d163.get('proposal_id')}`",
        "- source_response_mode: `DRY_CAPTURE_PLACEHOLDER_ONLY`",
        "- status: `SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION`",
        "",
        "This is a sandbox-only no-op placeholder candidate for static validation of the reentry pipeline.",
        "",
        "No provider call was performed.",
        "No network was accessed.",
        "No secret was read.",
        "No shell was executed by AI.",
        "No candidate was executed.",
        "No apply was executed.",
        "No route insert occurred.",
        "No protected core mutation occurred.",
        "No git action by AI occurred.",
        "",
    ]
    return "\n".join(lines)


def build_materialization_manifest(candidate_id, d163, work_dir):
    data = {
        "state": "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_MANIFEST",
        "ok": True,
        "candidate_id": candidate_id,
        "response_id": d163.get("response_id"),
        "runner_id": d163.get("runner_id"),
        "plan_id": d163.get("plan_id"),
        "review_id": d163.get("review_id"),
        "scope_id": d163.get("scope_id"),
        "intake_id": d163.get("intake_id"),
        "reentry_id": d163.get("reentry_id"),
        "next_cycle_id": d163.get("next_cycle_id"),
        "cycle_closure_id": d163.get("cycle_closure_id"),
        "previous_candidate_id": d163.get("previous_candidate_id"),
        "proposal_id": d163.get("proposal_id"),
        "created_at": now(),
        "materialization_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION",
        "candidate_work_dir": str(work_dir),
        "candidate_manifest_path": str(work_dir / "candidate_manifest.json"),
        "candidate_payload_path": str(work_dir / "candidate_payload.json"),
        "candidate_summary_path": str(work_dir / "candidate_summary.md"),
        "source_response_mode": "DRY_CAPTURE_PLACEHOLDER_ONLY",
        "canonical_guard_schema_applied": True,
        "sandbox_candidate_reentry_materialization_scope_only": True,
        "candidate_files_created": True,
        "candidate_payload_written": True,
        "candidate_manifest_written": True,
        "candidate_summary_written": True,
        "candidate_ready_for_static_validation": True,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_preflight(candidate_id, d163, work_dir):
    data = {
        "state": "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_PREFLIGHT",
        "ok": True,
        "candidate_id": candidate_id,
        "response_id": d163.get("response_id"),
        "created_at": now(),
        "preflight_status": "MATERIALIZATION_PREFLIGHT_READY_FOR_STATIC_VALIDATION_NO_EXECUTION",
        "candidate_work_dir": str(work_dir),
        "candidate_manifest_exists": (work_dir / "candidate_manifest.json").exists(),
        "candidate_payload_exists": (work_dir / "candidate_payload.json").exists(),
        "candidate_summary_exists": (work_dir / "candidate_summary.md").exists(),
        "candidate_files_created": True,
        "candidate_payload_written": True,
        "candidate_manifest_written": True,
        "candidate_summary_written": True,
        "candidate_ready_for_static_validation": True,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "apply_requested": False,
        "apply_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
    }
    data.update(base_no_ai_flags())
    return normalize_guard_flags(data)


def build_d165_scope(candidate_id, d163, work_dir):
    return {
        "state": "D164_D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE",
        "ok": True,
        "candidate_id": candidate_id,
        "response_id": d163.get("response_id"),
        "runner_id": d163.get("runner_id"),
        "plan_id": d163.get("plan_id"),
        "review_id": d163.get("review_id"),
        "scope_id": d163.get("scope_id"),
        "intake_id": d163.get("intake_id"),
        "reentry_id": d163.get("reentry_id"),
        "next_cycle_id": d163.get("next_cycle_id"),
        "cycle_closure_id": d163.get("cycle_closure_id"),
        "previous_candidate_id": d163.get("previous_candidate_id"),
        "proposal_id": d163.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D165_GATE,
        "sandbox_candidate_reentry_static_validation_scope_only": True,
        "candidate_files_required": True,
        "candidate_work_dir": str(work_dir),
        "candidate_payload_path": str(work_dir / "candidate_payload.json"),
        "candidate_manifest_path": str(work_dir / "candidate_manifest.json"),
        "fresh_intent_required": True,
        "human_review_required": True,
        "canonical_guard_schema_required": True,
        "candidate_execution_allowed": False,
        "d165_allowed_to_create": [
            "sandbox_candidate_reentry_static_validation_scope",
            "sandbox_candidate_reentry_static_validation_report",
            "sandbox_candidate_reentry_static_validation_receipt",
            "d166_sandbox_candidate_reentry_controlled_execution_preflight_scope",
        ],
        "d165_must_not_execute": [
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
        "real_apply_allowed_after_d164_by_ai": False,
        "route_insert_allowed_after_d164_by_ai": False,
        "protected_core_mutation_allowed_after_d164_by_ai": False,
        "network_allowed_after_d164_by_ai": False,
        "secret_read_allowed_after_d164_by_ai": False,
        "shell_allowed_after_d164_by_ai": False,
        "git_action_allowed_after_d164_by_ai": False,
    }


def create_sandbox_candidate_reentry_materialization_scope(root="."):
    root = Path(root).resolve()

    d163 = read_json(root / D163_REPORT, {}) or {}
    manifest = read_json(root / D163_MANIFEST, {}) or {}
    receipt = read_json(root / D163_DRY_CAPTURE_RECEIPT, {}) or {}
    d164_scope = read_json(root / D163_D164_SCOPE, {}) or {}

    errors = validate_d163(d163, manifest, receipt, d164_scope)

    candidate_id = "d164-" + digest({
        "response_id": d163.get("response_id"),
        "runner_id": d163.get("runner_id"),
        "plan_id": d163.get("plan_id"),
        "review_id": d163.get("review_id"),
        "scope_id": d163.get("scope_id"),
        "intake_id": d163.get("intake_id"),
        "reentry_id": d163.get("reentry_id"),
        "next_cycle_id": d163.get("next_cycle_id"),
        "proposal_id": d163.get("proposal_id"),
    })
    work_dir = Path("runtime_experimental/ai_sandbox_work") / candidate_id

    candidate_payload = build_candidate_payload(candidate_id, d163)
    candidate_manifest = build_candidate_manifest(candidate_id, d163, work_dir)
    materialization_manifest = build_materialization_manifest(candidate_id, d163, work_dir)
    d165_scope = build_d165_scope(candidate_id, d163, work_dir)

    for label, item in [
        ("candidate_payload", candidate_payload),
        ("candidate_manifest", candidate_manifest),
        ("materialization_manifest", materialization_manifest),
    ]:
        errors.extend(validate_no_ai_execution(item, prefix=label))
        require_false(item, [
            "candidate_execution_requested",
            "candidate_executed",
            "apply_requested",
            "apply_executed",
            "real_provider_call_performed",
            "provider_response_ingested",
        ], label, errors)

    require_false(d165_scope, [
        "candidate_execution_allowed",
        "real_apply_allowed_after_d164_by_ai",
        "route_insert_allowed_after_d164_by_ai",
        "protected_core_mutation_allowed_after_d164_by_ai",
        "network_allowed_after_d164_by_ai",
        "secret_read_allowed_after_d164_by_ai",
        "shell_allowed_after_d164_by_ai",
        "git_action_allowed_after_d164_by_ai",
    ], "d165_scope", errors)

    ok = not errors
    preflight = {}

    if ok:
        abs_work_dir = root / work_dir
        abs_work_dir.mkdir(parents=True, exist_ok=True)
        write_json(root / work_dir / "candidate_payload.json", candidate_payload)
        write_json(root / work_dir / "candidate_manifest.json", candidate_manifest)
        (root / work_dir / "candidate_summary.md").write_text(build_summary_md(candidate_id, d163), encoding="utf-8")

        preflight = build_preflight(candidate_id, d163, root / work_dir)
        errors.extend(validate_no_ai_execution(preflight, prefix="preflight"))
        require_true(preflight, [
            "candidate_manifest_exists",
            "candidate_payload_exists",
            "candidate_summary_exists",
            "candidate_ready_for_static_validation",
        ], "preflight", errors)

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_BLOCKED"
    result = "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_CREATED" if ok else "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_BLOCKED"

    if ok:
        write_json(root / MATERIALIZATION_MANIFEST_OUT, materialization_manifest)
        write_json(root / PREFLIGHT_OUT, preflight)
        write_json(root / D165_SCOPE_OUT, d165_scope)

    guardrails = normalize_guard_flags({
        "sandbox_candidate_reentry_materialization_scope_only": True,
        "sandbox_candidate_reentry_materialization_manifest_only": True,
        "sandbox_candidate_reentry_materialization_preflight_only": True,
        "canonical_guard_schema_applied": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "source_response_mode": "DRY_CAPTURE_PLACEHOLDER_ONLY",
        "candidate_files_created": ok,
        "candidate_payload_written": ok,
        "candidate_manifest_written": ok,
        "candidate_summary_written": ok,
        "candidate_ready_for_static_validation": ok,
        "candidate_execution_requested": False,
        "candidate_executed": False,
        "real_provider_call_performed": False,
        "provider_response_ingested": False,
        "provider_response_captured": False,
        "apply_requested": False,
        "apply_executed": False,
        "approval_for_d165_sandbox_candidate_reentry_static_validation_scope_only": ok,
        "real_apply_allowed_after_d164_by_ai": False,
        "route_insert_allowed_after_d164_by_ai": False,
        "protected_core_mutation_allowed_after_d164_by_ai": False,
        "network_allowed_after_d164_by_ai": False,
        "secret_read_allowed_after_d164_by_ai": False,
        "shell_allowed_after_d164_by_ai": False,
        "git_action_allowed_after_d164_by_ai": False,
        **base_no_ai_flags(),
    })

    report = {
        "state": "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "candidate_id": candidate_id,
        "response_id": d163.get("response_id"),
        "runner_id": d163.get("runner_id"),
        "plan_id": d163.get("plan_id"),
        "review_id": d163.get("review_id"),
        "scope_id": d163.get("scope_id"),
        "intake_id": d163.get("intake_id"),
        "reentry_id": d163.get("reentry_id"),
        "next_cycle_id": d163.get("next_cycle_id"),
        "cycle_closure_id": d163.get("cycle_closure_id"),
        "previous_candidate_id": d163.get("previous_candidate_id"),
        "proposal_id": d163.get("proposal_id"),
        "source_d163_report": D163_REPORT,
        "canonical_guard_schema": canonical_schema_report(),
        "candidate_work_dir": str(work_dir) if ok else None,
        "materialization_manifest": materialization_manifest if ok else {},
        "materialization_preflight": preflight if ok else {},
        "d165_scope": d165_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "candidate_id": candidate_id,
            "response_id": d163.get("response_id"),
            "runner_id": d163.get("runner_id"),
            "plan_id": d163.get("plan_id"),
            "review_id": d163.get("review_id"),
            "scope_id": d163.get("scope_id"),
            "intake_id": d163.get("intake_id"),
            "reentry_id": d163.get("reentry_id"),
            "next_cycle_id": d163.get("next_cycle_id"),
            "proposal_id": d163.get("proposal_id"),
            "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D164_PLUS" if ok else "BLOCKED",
            "materialization_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_READY_FOR_STATIC_VALIDATION" if ok else "BLOCKED",
            "source_response_mode": "DRY_CAPTURE_PLACEHOLDER_ONLY" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "candidate_execution_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D165_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_reentry_materialization_scope_created": ok,
            "candidate_payload_written": ok,
            "candidate_manifest_written": ok,
            "candidate_summary_written": ok,
            "materialization_manifest_created": ok,
            "materialization_preflight_created": ok,
            "d165_scope_created": ok,
            "candidate_executed": False,
            "apply_executed": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D165 may create sandbox candidate reentry static validation scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_reentry_materialization_scope(), ensure_ascii=False, indent=2))
