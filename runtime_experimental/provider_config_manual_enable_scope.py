
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D122_REPORT = "reports/d122_operator_dashboard_start_command_scope.json"
D122_FLOW = "reports/d122_single_entry_prompt_to_proposal_flow.json"
D122_PREFLIGHT = "reports/d122_dashboard_preflight_checklist.json"
D122_D123_SCOPE = "reports/d122_d123_provider_config_manual_enable_scope.json"

OUT = "reports/d123_provider_config_manual_enable_scope.json"
SECRET_POLICY_OUT = "reports/d123_provider_secret_placeholder_policy.json"
NETWORK_PLAN_OUT = "reports/d123_network_allowlist_dry_plan.json"
D124_SCOPE_OUT = "reports/d123_d124_real_provider_dry_ping_scope.json"

REQ_D122_DECISION = "OPERATOR_DASHBOARD_START_COMMAND_SCOPE_READY"
REQ_D123_GATE = "D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE"
REQ_D124_GATE = "D124_REAL_PROVIDER_DRY_PING_SCOPE"
REQ_D122_APPROVAL_SCOPE = "D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_ONLY"

FALSE_GUARD_KEYS = [
    "external_ai_called", "network_accessed", "api_key_read", "secret_read",
    "shell_from_ai_executed", "runtime_code_mutated", "protected_core_mutated",
    "canonical_memory_mutated", "actual_apply_executed", "route_inserted",
    "git_commit_by_ai", "git_push_by_ai", "rollback_executed", "restore_executed",
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


def validate_d122(d122, flow, preflight, d123_scope):
    errors = []
    if not d122:
        return ["missing D122 operator dashboard start command scope report"]

    if d122.get("ok") is not True:
        errors.append("D122 ok must be true")
    if d122.get("decision") != REQ_D122_DECISION:
        errors.append("D122 decision must be OPERATOR_DASHBOARD_START_COMMAND_SCOPE_READY")

    guard = d122.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D122 guardrails.{key} must be false")

    for key in [
        "operator_dashboard_scope_only",
        "single_entry_prompt_flow_only",
        "mock_provider_only",
        "proposal_output_only",
        "approval_for_d123_config_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D122 guardrails.{key} must be true")

    for key in [
        "real_provider_enabled_now",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D122 guardrails.{key} must be false")

    summary = d122.get("summary", {})
    expected = {
        "dashboard_mode": "MOCK_PROPOSE_ONLY_SINGLE_ENTRY",
        "real_provider_status": "DISABLED",
        "network_status": "BLOCKED",
        "real_apply_by_ai_status": "BLOCKED",
        "approval_scope": REQ_D122_APPROVAL_SCOPE,
        "next_step": REQ_D123_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D122 summary.{key} must be {value}")

    if not flow:
        errors.append("missing D122 single entry prompt-to-proposal flow")
    else:
        if flow.get("ok") is not True:
            errors.append("D122 flow ok must be true")
        if flow.get("flow_mode") != "MOCK_PROVIDER_PROPOSE_ONLY_NO_EXECUTION":
            errors.append("D122 flow mode must be mock propose-only no-execution")
        for key in [
            "real_provider_called", "network_accessed", "api_key_read", "secret_read",
            "shell_executed_by_ai", "actual_apply_executed", "candidate_executed",
        ]:
            if flow.get(key) is not False:
                errors.append(f"D122 flow {key} must be false")

    if not preflight:
        errors.append("missing D122 dashboard preflight checklist")
    else:
        if preflight.get("ok") is not True:
            errors.append("D122 preflight ok must be true")
        if preflight.get("dashboard_scope_only") is not True:
            errors.append("D122 preflight dashboard_scope_only must be true")
        mf = preflight.get("must_remain_false", {})
        for key in [
            "real_provider_enabled_now", "external_ai_called", "network_accessed",
            "api_key_read", "secret_read", "shell_from_ai_executed",
            "actual_apply_executed", "route_inserted", "protected_core_mutated",
            "canonical_memory_mutated", "git_commit_by_ai", "git_push_by_ai",
        ]:
            if mf.get(key) is not False:
                errors.append(f"D122 preflight must_remain_false.{key} must be false")

    if not d123_scope:
        errors.append("missing D122 D123 provider config manual enable scope")
    else:
        if d123_scope.get("ok") is not True:
            errors.append("D122 D123 scope ok must be true")
        if d123_scope.get("allowed_next_gate") != REQ_D123_GATE:
            errors.append("D122 D123 scope allowed_next_gate must be D123")
        if d123_scope.get("provider_config_manual_enable_scope_only") is not True:
            errors.append("D122 D123 scope provider_config_manual_enable_scope_only must be true")
        if d123_scope.get("human_review_required") is not True:
            errors.append("D122 D123 scope human_review_required must be true")
        for key in [
            "real_provider_enabled_after_d122", "network_allowed_after_d122",
            "api_key_read_allowed_after_d122", "real_apply_allowed_after_d122_by_ai",
            "route_insert_allowed_after_d122_by_ai",
            "protected_core_mutation_allowed_after_d122_by_ai",
        ]:
            if d123_scope.get(key) is not False:
                errors.append(f"D122 D123 scope {key} must be false")

    return errors


def build_secret_placeholder_policy(config_id, d122):
    return {
        "state": "D123_PROVIDER_SECRET_PLACEHOLDER_POLICY",
        "ok": True,
        "config_id": config_id,
        "dashboard_id": d122.get("dashboard_id"),
        "adapter_id": d122.get("adapter_id"),
        "seal_id": d122.get("seal_id"),
        "proposal_id": d122.get("proposal_id"),
        "created_at": now(),
        "policy_mode": "PLACEHOLDER_ONLY_NO_SECRET_READ",
        "secret_read_now": False,
        "api_key_read_now": False,
        "real_provider_enabled_now": False,
        "allowed_placeholder_names": [
            "PROVIDER_NAME_PLACEHOLDER",
            "PROVIDER_MODEL_PLACEHOLDER",
            "PROVIDER_ENDPOINT_PLACEHOLDER",
            "PROVIDER_API_KEY_ENV_NAME_PLACEHOLDER",
        ],
        "forbidden_values": [
            "raw api key value",
            "raw token value",
            "password",
            "private key",
            "secret environment dump",
        ],
        "manual_operator_steps_for_later": [
            "Choose provider name manually",
            "Choose model name manually",
            "Store real secret only in local environment outside repository",
            "Never commit real secrets",
            "Only D124 may perform a dry ping scope after explicit human review",
        ],
    }


def build_network_allowlist_dry_plan(config_id, d122):
    return {
        "state": "D123_NETWORK_ALLOWLIST_DRY_PLAN",
        "ok": True,
        "config_id": config_id,
        "dashboard_id": d122.get("dashboard_id"),
        "adapter_id": d122.get("adapter_id"),
        "created_at": now(),
        "plan_mode": "DRY_PLAN_ONLY_NO_NETWORK",
        "network_accessed_now": False,
        "real_provider_call_now": False,
        "allowlist_enabled_now": False,
        "candidate_allowlist_entries": [
            {
                "name": "provider_api_endpoint_placeholder",
                "value": "https://provider.example.invalid/v1",
                "status": "placeholder_not_enabled",
            }
        ],
        "dry_checks_for_d124": [
            "confirm provider endpoint placeholder",
            "confirm secret env name placeholder",
            "confirm no raw secret in repository",
            "confirm D124 dry ping scope before any real request",
            "confirm provider response must be proposal-shaped only",
        ],
    }


def build_d124_scope(config_id, d122):
    return {
        "state": "D123_D124_REAL_PROVIDER_DRY_PING_SCOPE",
        "ok": True,
        "config_id": config_id,
        "dashboard_id": d122.get("dashboard_id"),
        "adapter_id": d122.get("adapter_id"),
        "seal_id": d122.get("seal_id"),
        "proposal_id": d122.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D124_GATE,
        "d124_allowed_to_create": [
            "real_provider_dry_ping_scope",
            "provider_request_shape_probe",
            "provider_response_shape_probe",
            "d125_provider_response_to_proposal_intake_scope",
        ],
        "d124_must_not_execute": [
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
            "execute_sandbox_candidate_by_ai",
            "commit_sandbox_candidate_by_ai",
        ],
        "d124_must_remain_dry": [
            "no apply",
            "no route insertion",
            "no protected core mutation",
            "no git action by AI",
            "provider output must be proposal-shaped JSON only",
        ],
        "real_provider_dry_ping_scope_only": True,
        "human_review_required": True,
        "real_provider_enabled_after_d123": False,
        "network_call_executed_after_d123": False,
        "api_key_read_after_d123": False,
        "real_apply_allowed_after_d123_by_ai": False,
        "route_insert_allowed_after_d123_by_ai": False,
        "protected_core_mutation_allowed_after_d123_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D124_REAL_PROVIDER_DRY_PING_SCOPE_ONLY",
    }


def create_provider_config_manual_enable_scope(root="."):
    root = Path(root).resolve()
    d122 = read_json(root / D122_REPORT, {}) or {}
    flow = read_json(root / D122_FLOW, {}) or {}
    preflight = read_json(root / D122_PREFLIGHT, {}) or {}
    d123_scope = read_json(root / D122_D123_SCOPE, {}) or {}

    errors = validate_d122(d122, flow, preflight, d123_scope)

    config_id = "d123-" + digest({
        "dashboard_id": d122.get("dashboard_id"),
        "adapter_id": d122.get("adapter_id"),
        "seal_id": d122.get("seal_id"),
        "proposal_id": d122.get("proposal_id"),
    })

    secret_policy = build_secret_placeholder_policy(config_id, d122)
    network_plan = build_network_allowlist_dry_plan(config_id, d122)
    d124_scope = build_d124_scope(config_id, d122)

    for key in ["secret_read_now", "api_key_read_now", "real_provider_enabled_now"]:
        if secret_policy.get(key) is not False:
            errors.append(f"secret policy {key} must be false")
    for key in ["network_accessed_now", "real_provider_call_now", "allowlist_enabled_now"]:
        if network_plan.get(key) is not False:
            errors.append(f"network dry plan {key} must be false")
    for key in [
        "real_provider_enabled_after_d123",
        "network_call_executed_after_d123",
        "api_key_read_after_d123",
        "real_apply_allowed_after_d123_by_ai",
    ]:
        if d124_scope.get(key) is not False:
            errors.append(f"D124 scope {key} must be false")

    ok = not errors
    decision = "PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_READY" if ok else "PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_BLOCKED"
    result = "D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_CREATED" if ok else "D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_BLOCKED"

    if ok:
        write_json(root / SECRET_POLICY_OUT, secret_policy)
        write_json(root / NETWORK_PLAN_OUT, network_plan)
        write_json(root / D124_SCOPE_OUT, d124_scope)

    report = {
        "state": "D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "config_id": config_id,
        "dashboard_id": d122.get("dashboard_id"),
        "adapter_id": d122.get("adapter_id"),
        "seal_id": d122.get("seal_id"),
        "proposal_id": d122.get("proposal_id"),
        "source_d122_report": D122_REPORT,
        "provider_secret_placeholder_policy": secret_policy if ok else {},
        "network_allowlist_dry_plan": network_plan if ok else {},
        "d124_scope": d124_scope if ok else {},
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
            "provider_config_manual_enable_scope_only": True,
            "placeholder_policy_only": True,
            "network_allowlist_dry_plan_only": True,
            "real_provider_enabled_now": False,
            "real_provider_called_now": False,
            "approval_for_d124_dry_ping_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "config_id": config_id,
            "dashboard_id": d122.get("dashboard_id"),
            "adapter_id": d122.get("adapter_id"),
            "seal_id": d122.get("seal_id"),
            "proposal_id": d122.get("proposal_id"),
            "provider_config_status": "PLACEHOLDER_ONLY",
            "real_provider_status": "DISABLED",
            "network_status": "DRY_PLAN_ONLY",
            "secret_status": "PLACEHOLDER_ONLY_NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "approval_scope": "D124_REAL_PROVIDER_DRY_PING_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D124_GATE,
        },
        "success_condition": {
            "provider_config_scope_created": ok,
            "secret_placeholder_policy_created": ok,
            "network_allowlist_dry_plan_created": ok,
            "d124_scope_created": ok,
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "actual_apply_executed_by_ai": False,
            "candidate_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D124 may create real provider dry ping scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_provider_config_manual_enable_scope(), ensure_ascii=False, indent=2))
