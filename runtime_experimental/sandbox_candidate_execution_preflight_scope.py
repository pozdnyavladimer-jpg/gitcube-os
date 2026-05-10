
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D135_REPORT = "reports/d135_sandbox_candidate_post_write_validation_scope.json"
D135_VALIDATION_REPORT = "reports/d135_sandbox_candidate_post_write_validation_report.json"
D135_INVENTORY = "reports/d135_sandbox_candidate_materialized_file_inventory.json"
D135_D136_SCOPE = "reports/d135_d136_sandbox_candidate_execution_preflight_scope.json"

OUT = "reports/d136_sandbox_candidate_execution_preflight_scope.json"
PREFLIGHT_REPORT_OUT = "reports/d136_sandbox_candidate_execution_preflight_report.json"
EXECUTION_BLOCKERS_OUT = "reports/d136_sandbox_candidate_execution_blockers.json"
D137_SCOPE_OUT = "reports/d136_d137_sandbox_candidate_controlled_execution_scope.json"

REQ_D135_DECISION = "SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_READY"
REQ_D136_GATE = "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE"
REQ_D137_GATE = "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE"
REQ_D135_APPROVAL_SCOPE = "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_ONLY"

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

PROTECTED_TARGETS = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]

EXPECTED_SANDBOX_PREFIX = "runtime_experimental/ai_sandbox_work/"


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


def _contains_candidate_execution_flag(obj):
    if not isinstance(obj, dict):
        return False
    risky_keys = [
        "candidate_executed_now",
        "actual_apply_executed",
        "shell_executed_by_ai",
        "git_action_by_ai",
        "network_accessed",
        "api_key_read",
        "secret_read",
    ]
    return any(obj.get(key) is True for key in risky_keys)


def _inventory_paths(inventory):
    paths = []
    if not isinstance(inventory, dict):
        return paths

    for key in ["files", "materialized_files", "candidate_files", "inventory"]:
        value = inventory.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    paths.append(item)
                elif isinstance(item, dict):
                    p = item.get("path") or item.get("file") or item.get("name")
                    if p:
                        paths.append(str(p))

    for key in ["candidate_manifest", "candidate_summary", "candidate_payload"]:
        value = inventory.get(key)
        if isinstance(value, str):
            paths.append(value)
        elif isinstance(value, dict):
            p = value.get("path")
            if p:
                paths.append(str(p))

    return paths


def validate_d135(d135, validation_report, inventory, d136_scope):
    errors = []

    if not d135:
        errors.append("missing D135 sandbox candidate post-write validation scope report")
        return errors

    if d135.get("ok") is not True:
        errors.append("D135 ok must be true")
    if d135.get("decision") != REQ_D135_DECISION:
        errors.append("D135 decision must be SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_READY")

    guard = d135.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D135 guardrails.{key} must be false")

    for key in [
        "candidate_executed_now",
        "approval_for_candidate_execution",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D135 guardrails.{key} must be false")

    summary = d135.get("summary", {})
    expected = {
        "post_write_validation_status": "POST_WRITE_VALIDATION_PASS_NO_EXECUTION",
        "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": REQ_D135_APPROVAL_SCOPE,
        "next_step": REQ_D136_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D135 summary.{key} must be {value}")

    if not validation_report:
        errors.append("missing D135 post-write validation report")
    else:
        if validation_report.get("ok") is not True:
            errors.append("D135 validation report ok must be true")
        if _contains_candidate_execution_flag(validation_report):
            errors.append("D135 validation report must not indicate execution/apply/shell/network/secret use")
        status = validation_report.get("validation_status") or validation_report.get("post_write_validation_status")
        if status and status not in [
            "PASS_NO_EXECUTION",
            "POST_WRITE_VALIDATION_PASS_NO_EXECUTION",
            "MATERIALIZED_FILES_VALIDATED_NO_EXECUTION",
        ]:
            errors.append("D135 validation report status must be pass/no-execution")

    if not inventory:
        errors.append("missing D135 materialized file inventory")
    else:
        if inventory.get("ok") is not True:
            errors.append("D135 materialized file inventory ok must be true")
        if _contains_candidate_execution_flag(inventory):
            errors.append("D135 inventory must not indicate execution/apply/shell/network/secret use")
        paths = _inventory_paths(inventory)
        if not paths:
            errors.append("D135 inventory must include materialized candidate file paths")
        for p in paths:
            if not p.startswith(EXPECTED_SANDBOX_PREFIX):
                errors.append(f"D135 inventory path must stay inside sandbox: {p}")
        required_suffixes = ["candidate_manifest.json", "candidate_summary.md", "candidate_payload.json"]
        for suffix in required_suffixes:
            if not any(p.endswith(suffix) for p in paths):
                errors.append(f"D135 inventory missing {suffix}")

    if not d136_scope:
        errors.append("missing D135 D136 execution preflight scope")
    else:
        if d136_scope.get("ok") is not True:
            errors.append("D135 D136 scope ok must be true")
        if d136_scope.get("allowed_next_gate") != REQ_D136_GATE:
            errors.append("D135 D136 scope allowed_next_gate must be D136")
        if d136_scope.get("sandbox_candidate_execution_preflight_scope_only") is not True:
            errors.append("D135 D136 scope must be execution preflight scope only")
        if d136_scope.get("human_review_required") is not True:
            errors.append("D135 D136 scope must require human review")
        for key in [
            "candidate_executed_after_d135_by_ai",
            "real_apply_allowed_after_d135_by_ai",
            "route_insert_allowed_after_d135_by_ai",
            "protected_core_mutation_allowed_after_d135_by_ai",
        ]:
            if d136_scope.get(key) is not False:
                errors.append(f"D135 D136 scope {key} must be false")

    return errors


def build_preflight_report(preflight_id, d135, validation_report, inventory):
    paths = _inventory_paths(inventory)
    required = ["candidate_manifest.json", "candidate_summary.md", "candidate_payload.json"]
    required_checks = []
    for suffix in required:
        required_checks.append({
            "name": f"required_file_{suffix}",
            "status": "PREFLIGHT_PASS" if any(p.endswith(suffix) for p in paths) else "PREFLIGHT_FAIL",
            "execution_performed": False,
        })

    return {
        "state": "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_REPORT",
        "ok": True,
        "preflight_id": preflight_id,
        "validation_id": d135.get("validation_id"),
        "write_materialization_id": d135.get("write_materialization_id"),
        "candidate_id": d135.get("candidate_id"),
        "proposal_id": d135.get("proposal_id"),
        "created_at": now(),
        "preflight_mode": "EXECUTION_PREFLIGHT_ONLY_NO_CANDIDATE_EXECUTION",
        "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
        "materialized_paths": paths,
        "required_checks": required_checks,
        "post_write_validation_status": validation_report.get("validation_status") or validation_report.get("post_write_validation_status"),
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "human_review_required": True,
    }


def build_execution_blockers(preflight_id, d135):
    return {
        "state": "D136_SANDBOX_CANDIDATE_EXECUTION_BLOCKERS",
        "ok": True,
        "preflight_id": preflight_id,
        "validation_id": d135.get("validation_id"),
        "candidate_id": d135.get("candidate_id"),
        "created_at": now(),
        "blocker_mode": "DECLARE_EXECUTION_BOUNDARIES_NO_EXECUTION",
        "still_blocked": [
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
            "network_provider_call_by_ai",
            "secret_read_by_ai",
        ],
        "candidate_execution_performed": False,
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "human_review_required": True,
    }


def build_d137_scope(preflight_id, d135):
    return {
        "state": "D136_D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE",
        "ok": True,
        "preflight_id": preflight_id,
        "validation_id": d135.get("validation_id"),
        "write_materialization_id": d135.get("write_materialization_id"),
        "materialization_id": d135.get("materialization_id"),
        "static_validation_id": d135.get("static_validation_id"),
        "write_once_id": d135.get("write_once_id"),
        "window_id": d135.get("window_id"),
        "runner_id": d135.get("runner_id"),
        "plan_id": d135.get("plan_id"),
        "review_id": d135.get("review_id"),
        "candidate_id": d135.get("candidate_id"),
        "intake_id": d135.get("intake_id"),
        "ping_id": d135.get("ping_id"),
        "config_id": d135.get("config_id"),
        "dashboard_id": d135.get("dashboard_id"),
        "adapter_id": d135.get("adapter_id"),
        "seal_id": d135.get("seal_id"),
        "proposal_id": d135.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D137_GATE,
        "d137_allowed_to_create": [
            "sandbox_candidate_controlled_execution_scope",
            "sandbox_candidate_controlled_execution_receipt",
            "sandbox_candidate_no_apply_post_execution_guard",
            "d138_sandbox_candidate_post_execution_validation_scope",
        ],
        "d137_must_not_execute": [
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
            "network_provider_call_by_ai",
            "secret_read_by_ai",
        ],
        "sandbox_candidate_controlled_execution_scope_only": True,
        "human_review_required": True,
        "candidate_executed_after_d136_by_ai": False,
        "real_apply_allowed_after_d136_by_ai": False,
        "route_insert_allowed_after_d136_by_ai": False,
        "protected_core_mutation_allowed_after_d136_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_ONLY",
    }


def create_sandbox_candidate_execution_preflight_scope(root="."):
    root = Path(root).resolve()

    d135 = read_json(root / D135_REPORT, {}) or {}
    validation_report = read_json(root / D135_VALIDATION_REPORT, {}) or {}
    inventory = read_json(root / D135_INVENTORY, {}) or {}
    d136_scope = read_json(root / D135_D136_SCOPE, {}) or {}

    errors = validate_d135(d135, validation_report, inventory, d136_scope)

    preflight_id = "d136-" + digest({
        "validation_id": d135.get("validation_id"),
        "write_materialization_id": d135.get("write_materialization_id"),
        "candidate_id": d135.get("candidate_id"),
        "proposal_id": d135.get("proposal_id"),
    })

    preflight_report = build_preflight_report(preflight_id, d135, validation_report, inventory)
    execution_blockers = build_execution_blockers(preflight_id, d135)
    d137_scope = build_d137_scope(preflight_id, d135)

    for item_name, item in [("preflight_report", preflight_report), ("execution_blockers", execution_blockers)]:
        for key in ["candidate_executed_now", "actual_apply_executed", "shell_executed_by_ai", "git_action_by_ai", "network_accessed", "api_key_read", "secret_read"]:
            if item.get(key) is True:
                errors.append(f"{item_name} {key} must not be true")

    for check in preflight_report.get("required_checks", []):
        if check.get("status") != "PREFLIGHT_PASS":
            errors.append(f"preflight check failed: {check.get('name')}")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_BLOCKED"
    result = "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_CREATED" if ok else "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_BLOCKED"

    if ok:
        write_json(root / PREFLIGHT_REPORT_OUT, preflight_report)
        write_json(root / EXECUTION_BLOCKERS_OUT, execution_blockers)
        write_json(root / D137_SCOPE_OUT, d137_scope)

    report = {
        "state": "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "preflight_id": preflight_id,
        "validation_id": d135.get("validation_id"),
        "write_materialization_id": d135.get("write_materialization_id"),
        "materialization_id": d135.get("materialization_id"),
        "static_validation_id": d135.get("static_validation_id"),
        "write_once_id": d135.get("write_once_id"),
        "window_id": d135.get("window_id"),
        "runner_id": d135.get("runner_id"),
        "plan_id": d135.get("plan_id"),
        "review_id": d135.get("review_id"),
        "candidate_id": d135.get("candidate_id"),
        "intake_id": d135.get("intake_id"),
        "ping_id": d135.get("ping_id"),
        "config_id": d135.get("config_id"),
        "dashboard_id": d135.get("dashboard_id"),
        "adapter_id": d135.get("adapter_id"),
        "seal_id": d135.get("seal_id"),
        "proposal_id": d135.get("proposal_id"),
        "source_d135_report": D135_REPORT,
        "sandbox_candidate_execution_preflight_report": preflight_report if ok else {},
        "sandbox_candidate_execution_blockers": execution_blockers if ok else {},
        "d137_scope": d137_scope if ok else {},
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
            "sandbox_candidate_execution_preflight_scope_only": True,
            "execution_preflight_report_only": True,
            "execution_blockers_only": True,
            "candidate_executed_now": False,
            "approval_for_d137_controlled_execution_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "approval_for_route_insert_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "preflight_id": preflight_id,
            "validation_id": d135.get("validation_id"),
            "write_materialization_id": d135.get("write_materialization_id"),
            "candidate_id": d135.get("candidate_id"),
            "adapter_id": d135.get("adapter_id"),
            "seal_id": d135.get("seal_id"),
            "proposal_id": d135.get("proposal_id"),
            "execution_preflight_status": "PREFLIGHT_PASS_NO_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "candidate_execution_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D137_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_execution_preflight_scope_created": ok,
            "sandbox_candidate_execution_preflight_report_created": ok,
            "sandbox_candidate_execution_blockers_created": ok,
            "d137_scope_created": ok,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D137 may create sandbox candidate controlled execution scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_execution_preflight_scope(), ensure_ascii=False, indent=2))
