
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D121_REPORT = "reports/d121_ai_propose_only_provider_adapter_scope.json"
D121_CONTRACT = "reports/d121_provider_adapter_contract.json"
D121_MOCK_EXCHANGE = "reports/d121_mock_provider_request_response.json"
D121_D122_SCOPE = "reports/d121_d122_operator_dashboard_start_command_scope.json"

OUT = "reports/d122_operator_dashboard_start_command_scope.json"
FLOW_OUT = "reports/d122_single_entry_prompt_to_proposal_flow.json"
PREFLIGHT_OUT = "reports/d122_dashboard_preflight_checklist.json"
D123_SCOPE_OUT = "reports/d122_d123_provider_config_manual_enable_scope.json"

REQ_D121_DECISION = "AI_PROPOSE_ONLY_PROVIDER_ADAPTER_READY"
REQ_D122_GATE = "D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE"
REQ_D123_GATE = "D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE"
REQ_D121_APPROVAL_SCOPE = "D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE_ONLY"

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

FORBIDDEN_ACTIONS = [
    "real_apply_by_ai",
    "auto_apply",
    "route_insert_by_ai",
    "protected_core_mutation_by_ai",
    "canonical_memory_overwrite_by_ai",
    "external_ai_network_call_now",
    "shell_exec_from_ai",
    "git_commit_by_ai",
    "git_push_by_ai",
    "rollback_execute_by_ai",
    "restore_execute_by_ai",
    "execute_sandbox_candidate_by_ai",
    "commit_sandbox_candidate_by_ai",
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


def validate_d121(d121, contract, mock_exchange, d122_scope):
    errors = []

    if not d121:
        errors.append("missing D121 AI propose-only provider adapter report")
        return errors

    if d121.get("ok") is not True:
        errors.append("D121 ok must be true")
    if d121.get("decision") != REQ_D121_DECISION:
        errors.append("D121 decision must be AI_PROPOSE_ONLY_PROVIDER_ADAPTER_READY")

    guard = d121.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D121 guardrails.{key} must be false")
    if guard.get("provider_adapter_scope_only") is not True:
        errors.append("D121 provider_adapter_scope_only must be true")
    if guard.get("real_provider_enabled_now") is not False:
        errors.append("D121 real_provider_enabled_now must be false")
    if guard.get("mock_provider_only") is not True:
        errors.append("D121 mock_provider_only must be true")
    if guard.get("proposal_output_only") is not True:
        errors.append("D121 proposal_output_only must be true")
    if guard.get("approval_for_real_apply_by_ai") is not False:
        errors.append("D121 approval_for_real_apply_by_ai must be false")
    if guard.get("candidate_execution_allowed_by_ai") is not False:
        errors.append("D121 candidate_execution_allowed_by_ai must be false")
    if guard.get("commands_executed_by_ai") is not False:
        errors.append("D121 commands_executed_by_ai must be false")

    summary = d121.get("summary", {})
    if summary.get("provider_mode") != "MOCK_PROPOSE_ONLY":
        errors.append("D121 provider_mode must be MOCK_PROPOSE_ONLY")
    if summary.get("real_provider_status") != "DISABLED":
        errors.append("D121 real_provider_status must be DISABLED")
    if summary.get("network_status") != "BLOCKED":
        errors.append("D121 network_status must be BLOCKED")
    if summary.get("real_apply_by_ai_status") != "BLOCKED":
        errors.append("D121 real_apply_by_ai_status must be BLOCKED")
    if summary.get("approval_scope") != REQ_D121_APPROVAL_SCOPE:
        errors.append("D121 approval_scope must be D122 dashboard scope only")
    if summary.get("next_step") != REQ_D122_GATE:
        errors.append("D121 summary next_step must be D122")

    if not contract:
        errors.append("missing D121 provider adapter contract")
    else:
        if contract.get("ok") is not True:
            errors.append("D121 contract ok must be true")
        if contract.get("mode") != "AI_PROVIDER_PROPOSE_ONLY":
            errors.append("D121 contract mode must be propose-only")
        if contract.get("real_provider_enabled_now") is not False:
            errors.append("D121 contract real_provider_enabled_now must be false")
        if contract.get("mock_provider_only") is not True:
            errors.append("D121 contract mock_provider_only must be true")
        if contract.get("network_allowed_now") is not False:
            errors.append("D121 contract network_allowed_now must be false")
        if contract.get("secrets_allowed_now") is not False:
            errors.append("D121 contract secrets_allowed_now must be false")
        if contract.get("api_key_read_allowed_now") is not False:
            errors.append("D121 contract api_key_read_allowed_now must be false")
        output_contract = contract.get("output_contract", {})
        for field in [
            "proposal_id",
            "proposal_type",
            "intent",
            "target_scope",
            "candidate_files",
            "risk_flags",
            "guardrails",
            "validation_plan",
            "requires_human_review",
        ]:
            if field not in output_contract.get("required_fields", []):
                errors.append(f"D121 output contract missing required field: {field}")

    if not mock_exchange:
        errors.append("missing D121 mock provider request/response")
    else:
        if mock_exchange.get("ok") is not True:
            errors.append("D121 mock exchange ok must be true")
        if mock_exchange.get("mock_only") is not True:
            errors.append("D121 mock exchange must be mock_only")
        for key in ["real_provider_called", "network_accessed", "api_key_read", "secret_read"]:
            if mock_exchange.get(key) is not False:
                errors.append(f"D121 mock exchange {key} must be false")
        if mock_exchange.get("forbidden_hits") not in ([], None):
            errors.append("D121 mock exchange must have no forbidden hits")
        if mock_exchange.get("response_valid_shape") is not True:
            errors.append("D121 mock exchange response_valid_shape must be true")

    if not d122_scope:
        errors.append("missing D121 D122 operator dashboard scope")
    else:
        if d122_scope.get("ok") is not True:
            errors.append("D121 D122 scope ok must be true")
        if d122_scope.get("allowed_next_gate") != REQ_D122_GATE:
            errors.append("D121 D122 scope allowed_next_gate must be D122")
        if d122_scope.get("operator_dashboard_scope_only") is not True:
            errors.append("D121 D122 scope operator_dashboard_scope_only must be true")
        if d122_scope.get("human_review_required") is not True:
            errors.append("D121 D122 scope human_review_required must be true")
        if d122_scope.get("real_provider_enablement_allowed_now") is not False:
            errors.append("D121 D122 scope must not allow real provider enablement now")
        for key in [
            "real_apply_allowed_after_d121_by_ai",
            "route_insert_allowed_after_d121_by_ai",
            "protected_core_mutation_allowed_after_d121_by_ai",
            "sandbox_candidate_execution_allowed_after_d121_by_ai",
        ]:
            if d122_scope.get(key) is not False:
                errors.append(f"D121 D122 scope {key} must be false")
        must_not = d122_scope.get("d122_must_not_execute", [])
        for action in FORBIDDEN_ACTIONS:
            if action not in must_not:
                errors.append(f"D121 D122 scope missing forbidden action: {action}")

    return errors


def build_start_flow(dashboard_id, d121, contract):
    return {
        "state": "D122_SINGLE_ENTRY_PROMPT_TO_PROPOSAL_FLOW",
        "ok": True,
        "dashboard_id": dashboard_id,
        "adapter_id": d121.get("adapter_id"),
        "seal_id": d121.get("seal_id"),
        "proposal_id": d121.get("proposal_id"),
        "created_at": now(),
        "flow_mode": "MOCK_PROVIDER_PROPOSE_ONLY_NO_EXECUTION",
        "single_entry_command": "python -m runtime_experimental.operator_dashboard_start_command_scope --prompt '<human prompt>'",
        "flow_steps": [
            "accept human prompt",
            "wrap prompt in D121 input contract",
            "mock provider returns proposal-shaped JSON",
            "validate proposal shape against D121 output contract",
            "write proposal only to allowed sandbox/report scope",
            "stop before execution",
        ],
        "input_contract_reference": "reports/d121_provider_adapter_contract.json",
        "output_contract_required_fields": contract.get("output_contract", {}).get("required_fields", []),
        "allowed_output_paths": [
            "runtime_experimental/ai_sandbox_work/",
            "reports/",
            "tests/",
            "docs/",
        ],
        "blocked_output_paths": [
            "app/orchestration/",
            "core/",
            "runtime/",
            "bridges/",
            "memory/",
        ],
        "real_provider_called": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "actual_apply_executed": False,
        "candidate_executed": False,
    }


def build_dashboard_preflight(dashboard_id, d121):
    return {
        "state": "D122_DASHBOARD_PREFLIGHT_CHECKLIST",
        "ok": True,
        "dashboard_id": dashboard_id,
        "adapter_id": d121.get("adapter_id"),
        "created_at": now(),
        "dashboard_scope_only": True,
        "preflight_items": [
            "Confirm D120 chain is sealed",
            "Confirm D121 provider contract exists",
            "Confirm provider remains mock/propose-only",
            "Confirm no API key or secret is required",
            "Confirm no network call is allowed",
            "Confirm proposal output only",
            "Confirm no apply, route insert, core mutation, rollback, restore, git commit, or git push",
            "Prepare D123 manual provider config enable scope only",
        ],
        "must_remain_false": {
            "real_provider_enabled_now": False,
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
        },
    }


def build_d123_scope(dashboard_id, d121):
    return {
        "state": "D122_D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE",
        "ok": True,
        "dashboard_id": dashboard_id,
        "adapter_id": d121.get("adapter_id"),
        "seal_id": d121.get("seal_id"),
        "proposal_id": d121.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D123_GATE,
        "d123_allowed_to_create": [
            "provider_config_manual_enable_scope",
            "provider_secret_placeholder_policy",
            "network_allowlist_dry_plan",
            "d124_real_provider_dry_ping_scope",
        ],
        "d123_must_not_execute": [
            "read_real_api_key_now",
            "read_secret_now",
            "real_provider_call_now",
            "external_network_call_now",
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
        ],
        "provider_config_manual_enable_scope_only": True,
        "human_review_required": True,
        "real_provider_enabled_after_d122": False,
        "network_allowed_after_d122": False,
        "api_key_read_allowed_after_d122": False,
        "real_apply_allowed_after_d122_by_ai": False,
        "route_insert_allowed_after_d122_by_ai": False,
        "protected_core_mutation_allowed_after_d122_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_ONLY",
    }


def create_operator_dashboard_start_command_scope(root="."):
    root = Path(root).resolve()

    d121 = read_json(root / D121_REPORT, {}) or {}
    contract = read_json(root / D121_CONTRACT, {}) or {}
    mock_exchange = read_json(root / D121_MOCK_EXCHANGE, {}) or {}
    d122_scope = read_json(root / D121_D122_SCOPE, {}) or {}

    errors = validate_d121(d121, contract, mock_exchange, d122_scope)

    dashboard_id = "d122-" + digest({
        "adapter_id": d121.get("adapter_id"),
        "seal_id": d121.get("seal_id"),
        "proposal_id": d121.get("proposal_id"),
    })

    flow = build_start_flow(dashboard_id, d121, contract)
    preflight = build_dashboard_preflight(dashboard_id, d121)
    d123_scope = build_d123_scope(dashboard_id, d121)

    for key in [
        "real_provider_called",
        "network_accessed",
        "api_key_read",
        "secret_read",
        "shell_executed_by_ai",
        "actual_apply_executed",
        "candidate_executed",
    ]:
        if flow.get(key) is not False:
            errors.append(f"start flow {key} must be false")

    ok = not errors
    decision = "OPERATOR_DASHBOARD_START_COMMAND_SCOPE_READY" if ok else "OPERATOR_DASHBOARD_START_COMMAND_SCOPE_BLOCKED"
    result = "D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE_CREATED" if ok else "D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE_BLOCKED"

    if ok:
        write_json(root / FLOW_OUT, flow)
        write_json(root / PREFLIGHT_OUT, preflight)
        write_json(root / D123_SCOPE_OUT, d123_scope)

    report = {
        "state": "D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_OPERATOR_DASHBOARD_START_COMMAND_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "dashboard_id": dashboard_id,
        "adapter_id": d121.get("adapter_id"),
        "seal_id": d121.get("seal_id"),
        "proposal_id": d121.get("proposal_id"),
        "source_d121_report": D121_REPORT,
        "single_entry_prompt_to_proposal_flow": flow if ok else {},
        "dashboard_preflight_checklist": preflight if ok else {},
        "d123_scope": d123_scope if ok else {},
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
            "operator_dashboard_scope_only": True,
            "single_entry_prompt_flow_only": True,
            "real_provider_enabled_now": False,
            "mock_provider_only": True,
            "proposal_output_only": True,
            "approval_for_d123_config_scope_only": ok,
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
            "dashboard_id": dashboard_id,
            "adapter_id": d121.get("adapter_id"),
            "seal_id": d121.get("seal_id"),
            "proposal_id": d121.get("proposal_id"),
            "dashboard_mode": "MOCK_PROPOSE_ONLY_SINGLE_ENTRY",
            "real_provider_status": "DISABLED",
            "network_status": "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED",
            "approval_scope": "D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D123_GATE,
        },
        "success_condition": {
            "operator_dashboard_scope_created": ok,
            "single_entry_prompt_flow_created": ok,
            "dashboard_preflight_created": ok,
            "d123_scope_created": ok,
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "actual_apply_executed_by_ai": False,
            "candidate_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D123 may create provider config manual enable scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_operator_dashboard_start_command_scope(), ensure_ascii=False, indent=2))
