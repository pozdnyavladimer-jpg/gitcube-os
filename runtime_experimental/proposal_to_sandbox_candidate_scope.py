
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D125_REPORT = "reports/d125_provider_response_to_proposal_intake_scope.json"
D125_SCHEMA_VALIDATOR = "reports/d125_provider_response_schema_validator.json"
D125_REJECTION_REPORT = "reports/d125_provider_intake_rejection_report.json"
D125_D126_SCOPE = "reports/d125_d126_proposal_to_sandbox_candidate_scope.json"

OUT = "reports/d126_proposal_to_sandbox_candidate_scope.json"
WRITE_PLAN_OUT = "reports/d126_sandbox_candidate_write_plan.json"
STATIC_SCAN_OUT = "reports/d126_sandbox_candidate_static_scan.json"
D127_SCOPE_OUT = "reports/d126_d127_sandbox_candidate_human_review_scope.json"

REQ_D125_DECISION = "PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_READY"
REQ_D126_GATE = "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE"
REQ_D127_GATE = "D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE"
REQ_D125_APPROVAL_SCOPE = "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_ONLY"

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

ALLOWED_SANDBOX_PREFIXES = [
    "runtime_experimental/ai_sandbox_work/",
    "reports/",
    "tests/",
    "docs/",
]

BLOCKED_PREFIXES = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]

FORBIDDEN_CANDIDATE_MARKERS = [
    "subprocess.",
    "os.system",
    "eval(",
    "exec(",
    "open('/",
    "open(\"/",
    "git push",
    "git commit",
    "curl ",
    "wget ",
    "rm -rf",
    "api_key",
    "api_secret",
    "password",
    "token",
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


def validate_d125(d125, schema_validator, rejection_report, d126_scope):
    errors = []

    if not d125:
        errors.append("missing D125 provider response intake scope report")
        return errors

    if d125.get("ok") is not True:
        errors.append("D125 ok must be true")
    if d125.get("decision") != REQ_D125_DECISION:
        errors.append("D125 decision must be PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_READY")

    guard = d125.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D125 guardrails.{key} must be false")
    for key in [
        "provider_response_intake_scope_only",
        "schema_validation_only",
        "rejection_report_only",
        "approval_for_d126_sandbox_candidate_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D125 guardrails.{key} must be true")
    for key in [
        "real_provider_called_now",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D125 guardrails.{key} must be false")

    summary = d125.get("summary", {})
    if summary.get("intake_status") != "PROPOSAL_SHAPE_ACCEPTED":
        errors.append("D125 intake_status must be PROPOSAL_SHAPE_ACCEPTED")
    if summary.get("schema_validator_status") != "PASS":
        errors.append("D125 schema_validator_status must be PASS")
    if summary.get("real_provider_status") != "NOT_CALLED":
        errors.append("D125 real_provider_status must be NOT_CALLED")
    if summary.get("network_status") != "NOT_ACCESSED":
        errors.append("D125 network_status must be NOT_ACCESSED")
    if summary.get("secret_status") != "NOT_READ":
        errors.append("D125 secret_status must be NOT_READ")
    if summary.get("real_apply_by_ai_status") != "BLOCKED":
        errors.append("D125 real_apply_by_ai_status must be BLOCKED")
    if summary.get("approval_scope") != REQ_D125_APPROVAL_SCOPE:
        errors.append("D125 approval_scope must be D126 sandbox candidate scope only")
    if summary.get("next_step") != REQ_D126_GATE:
        errors.append("D125 next_step must be D126")

    if not schema_validator:
        errors.append("missing D125 provider response schema validator")
    else:
        if schema_validator.get("ok") is not True:
            errors.append("D125 schema validator ok must be true")
        if schema_validator.get("validator_mode") != "PROPOSAL_SHAPE_ONLY_NO_EXECUTION":
            errors.append("D125 schema validator must be proposal-shape-only")
        if schema_validator.get("response_shape_valid") is not True:
            errors.append("D125 response_shape_valid must be true")
        if schema_validator.get("response_shape_errors") not in ([], None):
            errors.append("D125 schema validator response_shape_errors must be empty")
        for key in [
            "real_provider_called",
            "network_accessed",
            "api_key_read",
            "secret_read",
            "actual_apply_executed",
            "candidate_executed",
        ]:
            if schema_validator.get(key) is not False:
                errors.append(f"D125 schema validator {key} must be false")

    if not rejection_report:
        errors.append("missing D125 provider intake rejection report")
    else:
        if rejection_report.get("ok") is not True:
            errors.append("D125 rejection report ok must be true")
        if rejection_report.get("provider_response_rejected") is not False:
            errors.append("D125 provider_response_rejected must be false")
        if rejection_report.get("accepted_for_d126_sandbox_candidate_scope") is not True:
            errors.append("D125 accepted_for_d126_sandbox_candidate_scope must be true")
        if rejection_report.get("human_review_required") is not True:
            errors.append("D125 rejection report must require human review")
        for key in [
            "real_provider_called",
            "network_accessed",
            "api_key_read",
            "secret_read",
            "actual_apply_executed",
            "candidate_executed",
        ]:
            if rejection_report.get(key) is not False:
                errors.append(f"D125 rejection report {key} must be false")

    if not d126_scope:
        errors.append("missing D125 D126 proposal to sandbox candidate scope")
    else:
        if d126_scope.get("ok") is not True:
            errors.append("D125 D126 scope ok must be true")
        if d126_scope.get("allowed_next_gate") != REQ_D126_GATE:
            errors.append("D125 D126 scope allowed_next_gate must be D126")
        if d126_scope.get("proposal_to_sandbox_candidate_scope_only") is not True:
            errors.append("D125 D126 proposal_to_sandbox_candidate_scope_only must be true")
        if d126_scope.get("human_review_required") is not True:
            errors.append("D125 D126 scope must require human review")
        if d126_scope.get("schema_validator_ok") is not True:
            errors.append("D125 D126 scope schema_validator_ok must be true")
        if d126_scope.get("intake_rejected") is not False:
            errors.append("D125 D126 scope intake_rejected must be false")
        for key in [
            "real_provider_call_executed_after_d125",
            "network_call_executed_after_d125",
            "api_key_read_after_d125",
            "real_apply_allowed_after_d125_by_ai",
            "route_insert_allowed_after_d125_by_ai",
            "protected_core_mutation_allowed_after_d125_by_ai",
        ]:
            if d126_scope.get(key) is not False:
                errors.append(f"D125 D126 scope {key} must be false")

    return errors


def build_write_plan(candidate_id, d125, schema_validator):
    proposal_id = d125.get("proposal_id") or schema_validator.get("proposal_id")
    candidate_root = f"runtime_experimental/ai_sandbox_work/{candidate_id}/"
    candidate_manifest = candidate_root + "candidate_manifest.json"
    candidate_summary = candidate_root + "candidate_summary.md"

    return {
        "state": "D126_SANDBOX_CANDIDATE_WRITE_PLAN",
        "ok": True,
        "candidate_id": candidate_id,
        "intake_id": d125.get("intake_id"),
        "ping_id": d125.get("ping_id"),
        "adapter_id": d125.get("adapter_id"),
        "seal_id": d125.get("seal_id"),
        "proposal_id": proposal_id,
        "created_at": now(),
        "plan_mode": "SANDBOX_CANDIDATE_PLAN_ONLY_NO_EXECUTION",
        "candidate_root": candidate_root,
        "planned_files": [
            {
                "path": candidate_manifest,
                "operation": "create",
                "purpose": "proposal intake manifest for later human review",
            },
            {
                "path": candidate_summary,
                "operation": "create",
                "purpose": "human-readable sandbox candidate summary",
            },
        ],
        "allowed_prefixes": ALLOWED_SANDBOX_PREFIXES,
        "blocked_prefixes": BLOCKED_PREFIXES,
        "candidate_files_written_now": False,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_static_scan(candidate_id, write_plan):
    planned_files = write_plan.get("planned_files", [])
    errors = []

    for item in planned_files:
        path = item.get("path", "")
        if not any(path.startswith(prefix) for prefix in ALLOWED_SANDBOX_PREFIXES):
            errors.append(f"planned path outside allowed prefixes: {path}")
        if any(path.startswith(prefix) for prefix in BLOCKED_PREFIXES):
            errors.append(f"planned path targets blocked prefix: {path}")

    text_blob = json.dumps(write_plan, ensure_ascii=False).lower()
    marker_hits = []
    for marker in FORBIDDEN_CANDIDATE_MARKERS:
        if marker.lower() in text_blob:
            marker_hits.append(marker)

    if marker_hits:
        errors.append("forbidden candidate markers present: " + ", ".join(marker_hits))

    return {
        "state": "D126_SANDBOX_CANDIDATE_STATIC_SCAN",
        "ok": not errors,
        "candidate_id": candidate_id,
        "created_at": now(),
        "scan_mode": "STATIC_PLAN_SCAN_ONLY_NO_EXECUTION",
        "planned_files_count": len(planned_files),
        "allowed_prefixes_ok": not any("outside allowed" in e for e in errors),
        "blocked_prefix_hits": [e for e in errors if "blocked prefix" in e],
        "forbidden_marker_hits": marker_hits,
        "errors": errors,
        "candidate_files_written_now": False,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_d127_scope(candidate_id, d125, static_scan):
    ready = static_scan.get("ok") is True
    return {
        "state": "D126_D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE",
        "ok": ready,
        "candidate_id": candidate_id,
        "intake_id": d125.get("intake_id"),
        "ping_id": d125.get("ping_id"),
        "config_id": d125.get("config_id"),
        "dashboard_id": d125.get("dashboard_id"),
        "adapter_id": d125.get("adapter_id"),
        "seal_id": d125.get("seal_id"),
        "proposal_id": d125.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D127_GATE if ready else "BLOCKED",
        "d127_allowed_to_create": [
            "sandbox_candidate_human_review_scope",
            "sandbox_candidate_review_packet",
            "sandbox_candidate_approval_or_rejection_record",
            "d128_sandbox_candidate_test_plan_scope",
        ] if ready else [],
        "d127_must_not_execute": [
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
        "sandbox_candidate_human_review_scope_only": ready,
        "human_review_required": True,
        "static_scan_ok": ready,
        "candidate_written_after_d126": False,
        "candidate_executed_after_d126_by_ai": False,
        "real_apply_allowed_after_d126_by_ai": False,
        "route_insert_allowed_after_d126_by_ai": False,
        "protected_core_mutation_allowed_after_d126_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_ONLY",
    }


def create_proposal_to_sandbox_candidate_scope(root="."):
    root = Path(root).resolve()

    d125 = read_json(root / D125_REPORT, {}) or {}
    schema_validator = read_json(root / D125_SCHEMA_VALIDATOR, {}) or {}
    rejection_report = read_json(root / D125_REJECTION_REPORT, {}) or {}
    d126_scope = read_json(root / D125_D126_SCOPE, {}) or {}

    errors = validate_d125(d125, schema_validator, rejection_report, d126_scope)

    candidate_id = "d126-" + digest({
        "intake_id": d125.get("intake_id"),
        "ping_id": d125.get("ping_id"),
        "adapter_id": d125.get("adapter_id"),
        "proposal_id": d125.get("proposal_id"),
    })

    write_plan = build_write_plan(candidate_id, d125, schema_validator)
    static_scan = build_static_scan(candidate_id, write_plan)
    d127_scope = build_d127_scope(candidate_id, d125, static_scan)

    if static_scan.get("ok") is not True:
        errors.extend(static_scan.get("errors", []))

    for item_name, item in [("write_plan", write_plan), ("static_scan", static_scan)]:
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
        ]:
            if item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_READY" if ok else "PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_BLOCKED"
    result = "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_CREATED" if ok else "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_BLOCKED"

    if ok:
        write_json(root / WRITE_PLAN_OUT, write_plan)
        write_json(root / STATIC_SCAN_OUT, static_scan)
        write_json(root / D127_SCOPE_OUT, d127_scope)

    report = {
        "state": "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "candidate_id": candidate_id,
        "intake_id": d125.get("intake_id"),
        "ping_id": d125.get("ping_id"),
        "config_id": d125.get("config_id"),
        "dashboard_id": d125.get("dashboard_id"),
        "adapter_id": d125.get("adapter_id"),
        "seal_id": d125.get("seal_id"),
        "proposal_id": d125.get("proposal_id"),
        "source_d125_report": D125_REPORT,
        "sandbox_candidate_write_plan": write_plan if ok else {},
        "sandbox_candidate_static_scan": static_scan if ok else {},
        "d127_scope": d127_scope if ok else {},
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
            "proposal_to_sandbox_candidate_scope_only": True,
            "sandbox_write_plan_only": True,
            "static_scan_only": True,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "approval_for_d127_human_review_scope_only": ok,
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
            "candidate_id": candidate_id,
            "intake_id": d125.get("intake_id"),
            "ping_id": d125.get("ping_id"),
            "adapter_id": d125.get("adapter_id"),
            "seal_id": d125.get("seal_id"),
            "proposal_id": d125.get("proposal_id"),
            "sandbox_candidate_status": "PLAN_CREATED_NOT_WRITTEN_NOT_EXECUTED" if ok else "BLOCKED",
            "static_scan_status": "PASS" if static_scan.get("ok") is True else "FAIL",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "approval_scope": "D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D127_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "proposal_to_sandbox_candidate_scope_created": ok,
            "sandbox_candidate_write_plan_created": ok,
            "sandbox_candidate_static_scan_created": ok,
            "d127_scope_created": ok,
            "candidate_files_written": False,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D127 may create sandbox candidate human review scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_proposal_to_sandbox_candidate_scope(), ensure_ascii=False, indent=2))
