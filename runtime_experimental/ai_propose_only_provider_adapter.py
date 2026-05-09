
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D120_REPORT = "reports/d120_first_controlled_run_seal_scope.json"
D120_LEDGER = "reports/d120_guarded_autonomy_run_ledger.json"
D120_INTEGRITY = "reports/d120_final_chain_integrity_summary.json"
D120_TAG_PLAN = "reports/d120_first_run_release_tag_plan.json"

OUT = "reports/d121_ai_propose_only_provider_adapter_scope.json"
CONTRACT_OUT = "reports/d121_provider_adapter_contract.json"
MOCK_EXCHANGE_OUT = "reports/d121_mock_provider_request_response.json"
D122_SCOPE_OUT = "reports/d121_d122_operator_dashboard_start_command_scope.json"

REQ_D120_DECISION = "FIRST_CONTROLLED_RUN_SEAL_SCOPE_READY"
REQ_D121_TRACK = "D121_AI_PROPOSE_ONLY_PROVIDER_ADAPTER"
REQ_D122_GATE = "D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE"

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


REQUIRED_CHAIN_ITEMS = [
    "D106 AI Provider Boundary",
    "D107 Proposal Schema Validator",
    "D108 Sandbox Proposal Writer",
    "D109 Regression Runner",
    "D110 Human Review Gate",
    "D111 Explicit Approval Gate",
    "D112 Dry-Run Apply Scope",
    "D113 Final Apply Review Scope",
    "D114 Final Human Apply Decision Scope",
    "D115 Final Apply Phrase Scope",
    "D116 Manual Apply Window Scope",
    "D117 Manual Apply Command Review Scope",
    "D118 Operator Local Execution Evidence Scope",
    "D119 Post-Apply Verification Gate Scope",
    "D120 First Controlled Run Seal Scope",
]


FORBIDDEN_FIELDS = [
    "api_key",
    "api_secret",
    "token",
    "password",
    "raw_shell_command",
    "shell_command",
    "subprocess",
    "exec",
    "eval",
    "auto_apply",
    "apply_now",
    "git_commit",
    "git_push",
    "route_insert",
    "protected_core_mutation",
    "canonical_memory_overwrite",
    "direct_core_edit",
]


FORBIDDEN_ACTIONS = [
    "real_apply",
    "auto_apply",
    "route_insert",
    "protected_core_mutation",
    "canonical_memory_overwrite",
    "external_ai_network_call_now",
    "shell_exec",
    "subprocess_exec",
    "git_commit_by_ai",
    "git_push_by_ai",
    "rollback_execute",
    "restore_execute",
    "delete_runtime_candidate",
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


def contains_forbidden(obj, forbidden_fields, forbidden_actions):
    hits = []

    def walk(value, path=""):
        if isinstance(value, dict):
            for k, v in value.items():
                key = str(k)
                low_key = key.lower()
                if low_key in forbidden_fields or any(term in low_key for term in forbidden_actions):
                    hits.append(f"forbidden key/content detected: {path}.{key}".strip("."))
                walk(v, f"{path}.{key}".strip("."))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                walk(item, f"{path}[{i}]")
        elif isinstance(value, str):
            low_value = value.lower()
            for term in forbidden_fields + forbidden_actions:
                if term in low_value:
                    hits.append(f"forbidden text/content detected: {path}")
                    break

    walk(obj)
    return hits


def validate_d120(d120, ledger, integrity, tag_plan):
    errors = []

    if not d120:
        errors.append("missing D120 first controlled run seal scope report")
        return errors

    if d120.get("ok") is not True:
        errors.append("D120 ok must be true")
    if d120.get("decision") != REQ_D120_DECISION:
        errors.append("D120 decision must be FIRST_CONTROLLED_RUN_SEAL_SCOPE_READY")

    guard = d120.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D120 guardrails.{key} must be false")
    if guard.get("first_controlled_run_seal_scope_only") is not True:
        errors.append("D120 first_controlled_run_seal_scope_only must be true")
    if guard.get("ledger_only") is not True:
        errors.append("D120 ledger_only must be true")
    if guard.get("tag_plan_only") is not True:
        errors.append("D120 tag_plan_only must be true")
    if guard.get("approval_for_real_apply_by_ai") is not False:
        errors.append("D120 approval_for_real_apply_by_ai must be false")
    if guard.get("candidate_execution_allowed_by_ai") is not False:
        errors.append("D120 candidate_execution_allowed_by_ai must be false")
    if guard.get("commands_executed_by_ai") is not False:
        errors.append("D120 commands_executed_by_ai must be false")

    summary = d120.get("summary", {})
    if summary.get("sealed_range") != "D106-D120":
        errors.append("D120 sealed_range must be D106-D120")
    if summary.get("first_controlled_run_status") != "SEALED":
        errors.append("D120 first_controlled_run_status must be SEALED")
    if summary.get("real_apply_by_ai_status") != "BLOCKED":
        errors.append("D120 real_apply_by_ai_status must be BLOCKED")
    if summary.get("recommended_next_track") != REQ_D121_TRACK:
        errors.append("D120 recommended_next_track must be D121")

    if not ledger:
        errors.append("missing D120 guarded autonomy run ledger")
    else:
        if ledger.get("ok") is not True:
            errors.append("D120 ledger ok must be true")
        if ledger.get("chain_length") != 15:
            errors.append("D120 ledger chain_length must be 15")
        chain = ledger.get("chain", [])
        for item in REQUIRED_CHAIN_ITEMS:
            if item not in chain:
                errors.append(f"D120 ledger missing chain item: {item}")
        if ledger.get("run_status") != "FIRST_CONTROLLED_RUN_SCOPE_SEALED":
            errors.append("D120 ledger run_status must be sealed")
        for key in [
            "real_apply_by_ai",
            "actual_apply_executed_by_ai",
            "commands_executed_by_ai",
        ]:
            if ledger.get(key) is not False:
                errors.append(f"D120 ledger {key} must be false")

    if not integrity:
        errors.append("missing D120 final chain integrity summary")
    else:
        if integrity.get("ok") is not True:
            errors.append("D120 integrity ok must be true")
        if integrity.get("sealed_range") != "D106-D120":
            errors.append("D120 integrity sealed_range must be D106-D120")
        if integrity.get("integrity_status") != "SEALED_WITH_REAL_APPLY_BY_AI_BLOCKED":
            errors.append("D120 integrity status must keep real apply by AI blocked")
        checks = integrity.get("checks", {})
        for key in [
            "d119_ok",
            "test_results_summary_ok",
            "git_state_summary_ok",
            "real_apply_by_ai_blocked",
            "ai_shell_execution_blocked",
            "ai_git_action_blocked",
            "protected_core_mutation_by_ai_blocked",
            "canonical_memory_overwrite_by_ai_blocked",
        ]:
            if checks.get(key) is not True:
                errors.append(f"D120 integrity checks.{key} must be true")

    if not tag_plan:
        errors.append("missing D120 first run release tag plan")
    else:
        if tag_plan.get("ok") is not True:
            errors.append("D120 tag plan ok must be true")
        if tag_plan.get("tag_plan_only") is not True:
            errors.append("D120 tag plan must be tag-plan-only")
        if tag_plan.get("tag_created_by_ai") is not False:
            errors.append("D120 tag_created_by_ai must be false")
        if tag_plan.get("tag_pushed_by_ai") is not False:
            errors.append("D120 tag_pushed_by_ai must be false")

    return errors


def build_provider_contract(adapter_id, d120):
    return {
        "state": "D121_PROVIDER_ADAPTER_CONTRACT",
        "ok": True,
        "adapter_id": adapter_id,
        "seal_id": d120.get("seal_id"),
        "proposal_id": d120.get("proposal_id"),
        "created_at": now(),
        "mode": "AI_PROVIDER_PROPOSE_ONLY",
        "real_provider_enabled_now": False,
        "mock_provider_only": True,
        "network_allowed_now": False,
        "secrets_allowed_now": False,
        "api_key_read_allowed_now": False,
        "input_contract": {
            "required_fields": [
                "request_id",
                "human_prompt",
                "target_scope",
                "allowed_paths",
                "blocked_paths",
                "expected_output_contract",
            ],
            "blocked_fields": FORBIDDEN_FIELDS,
            "max_prompt_chars": 12000,
        },
        "output_contract": {
            "format": "json",
            "required_fields": [
                "proposal_id",
                "proposal_type",
                "intent",
                "target_scope",
                "candidate_files",
                "risk_flags",
                "guardrails",
                "validation_plan",
                "requires_human_review",
            ],
            "allowed_proposal_types": [
                "documentation_proposal",
                "test_proposal",
                "sandbox_patch_proposal",
                "analysis_proposal",
                "schema_proposal",
            ],
            "forbidden_fields": FORBIDDEN_FIELDS,
            "forbidden_actions": FORBIDDEN_ACTIONS,
        },
        "allowed_paths_for_proposals_only": [
            "runtime_experimental/ai_sandbox_work/",
            "reports/",
            "tests/",
            "docs/",
        ],
        "blocked_paths": [
            "app/orchestration/",
            "core/",
            "runtime/",
            "bridges/",
            "memory/",
        ],
        "provider_must_not": [
            "read secrets",
            "call network from this module",
            "execute shell",
            "create subprocess",
            "apply patches",
            "mutate protected core",
            "commit or push git",
            "route insert",
        ],
    }


def build_mock_provider_exchange(adapter_id, contract):
    request = {
        "request_id": "mock-d121-request",
        "human_prompt": "Create a harmless documentation proposal for the guarded autonomy chain.",
        "target_scope": "docs/",
        "allowed_paths": contract.get("allowed_paths_for_proposals_only", []),
        "blocked_paths": contract.get("blocked_paths", []),
        "expected_output_contract": contract.get("output_contract", {}),
    }
    response = {
        "proposal_id": "d121-mock-proposal",
        "proposal_type": "documentation_proposal",
        "intent": "Document the sealed D106-D120 guarded autonomy cycle.",
        "target_scope": "docs/",
        "candidate_files": [
            {
                "path": "docs/guarded_autonomy_first_controlled_run.md",
                "operation": "create",
                "content_summary": "Human-readable summary of the sealed propose-only guarded autonomy cycle.",
            }
        ],
        "risk_flags": [],
        "guardrails": {
            "propose_only": True,
            "requires_human_review": True,
            "no_shell": True,
            "no_network": True,
            "no_secrets": True,
            "no_apply": True,
            "no_git_actions": True,
            "routing_changes_blocked": True,
            "protected_area_changes_blocked": True,
        },
        "validation_plan": [
            "validate schema",
            "write only to sandbox/docs/report path",
            "run tests before any later human review",
        ],
        "requires_human_review": True,
    }
    return {
        "state": "D121_MOCK_PROVIDER_REQUEST_RESPONSE",
        "ok": True,
        "adapter_id": adapter_id,
        "created_at": now(),
        "mock_only": True,
        "real_provider_called": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "request": request,
        "response": response,
        "forbidden_hits": contains_forbidden(response, FORBIDDEN_FIELDS, FORBIDDEN_ACTIONS),
        "response_valid_shape": True,
    }


def build_d122_scope(adapter_id, d120):
    return {
        "state": "D121_D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE",
        "ok": True,
        "adapter_id": adapter_id,
        "seal_id": d120.get("seal_id"),
        "proposal_id": d120.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D122_GATE,
        "d122_allowed_to_create": [
            "operator_dashboard_start_command",
            "single_entry_prompt_to_proposal_flow",
            "dashboard_preflight_checklist",
            "d123_provider_config_manual_enable_scope",
        ],
        "d122_must_not_execute": [
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
        ],
        "operator_dashboard_scope_only": True,
        "human_review_required": True,
        "real_provider_enablement_allowed_now": False,
        "real_apply_allowed_after_d121_by_ai": False,
        "route_insert_allowed_after_d121_by_ai": False,
        "protected_core_mutation_allowed_after_d121_by_ai": False,
        "sandbox_candidate_execution_allowed_after_d121_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE_ONLY",
    }


def create_ai_propose_only_provider_adapter_scope(root="."):
    root = Path(root).resolve()

    d120 = read_json(root / D120_REPORT, {}) or {}
    ledger = read_json(root / D120_LEDGER, {}) or {}
    integrity = read_json(root / D120_INTEGRITY, {}) or {}
    tag_plan = read_json(root / D120_TAG_PLAN, {}) or {}

    errors = validate_d120(d120, ledger, integrity, tag_plan)

    adapter_id = "d121-" + digest({
        "seal_id": d120.get("seal_id"),
        "proposal_id": d120.get("proposal_id"),
        "sealed_range": d120.get("summary", {}).get("sealed_range"),
    })

    contract = build_provider_contract(adapter_id, d120)
    mock_exchange = build_mock_provider_exchange(adapter_id, contract)
    d122_scope = build_d122_scope(adapter_id, d120)

    if contract.get("real_provider_enabled_now") is not False:
        errors.append("provider contract real_provider_enabled_now must be false")
    if contract.get("network_allowed_now") is not False:
        errors.append("provider contract network_allowed_now must be false")
    if contract.get("api_key_read_allowed_now") is not False:
        errors.append("provider contract api_key_read_allowed_now must be false")
    if mock_exchange.get("forbidden_hits"):
        errors.append("mock provider response contains forbidden content: " + "; ".join(mock_exchange["forbidden_hits"]))
    if mock_exchange.get("real_provider_called") is not False:
        errors.append("mock provider exchange real_provider_called must be false")

    ok = not errors
    decision = "AI_PROPOSE_ONLY_PROVIDER_ADAPTER_READY" if ok else "AI_PROPOSE_ONLY_PROVIDER_ADAPTER_BLOCKED"
    result = "D121_AI_PROPOSE_ONLY_PROVIDER_ADAPTER_CREATED" if ok else "D121_AI_PROPOSE_ONLY_PROVIDER_ADAPTER_BLOCKED"

    if ok:
        write_json(root / CONTRACT_OUT, contract)
        write_json(root / MOCK_EXCHANGE_OUT, mock_exchange)
        write_json(root / D122_SCOPE_OUT, d122_scope)

    report = {
        "state": "D121_AI_PROPOSE_ONLY_PROVIDER_ADAPTER_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_AI_PROPOSE_ONLY_PROVIDER_ADAPTER",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "adapter_id": adapter_id,
        "seal_id": d120.get("seal_id"),
        "proposal_id": d120.get("proposal_id"),
        "source_d120_report": D120_REPORT,
        "provider_adapter_contract": contract if ok else {},
        "mock_provider_request_response": mock_exchange if ok else {},
        "d122_scope": d122_scope if ok else {},
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
            "provider_adapter_scope_only": True,
            "real_provider_enabled_now": False,
            "mock_provider_only": True,
            "proposal_output_only": True,
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
            "adapter_id": adapter_id,
            "seal_id": d120.get("seal_id"),
            "proposal_id": d120.get("proposal_id"),
            "provider_mode": "MOCK_PROPOSE_ONLY",
            "real_provider_status": "DISABLED",
            "network_status": "BLOCKED",
            "real_apply_by_ai_status": "BLOCKED",
            "approval_scope": "D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D122_GATE,
        },
        "success_condition": {
            "provider_adapter_scope_created": ok,
            "provider_contract_created": ok,
            "mock_exchange_created": ok,
            "d122_scope_created": ok,
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "actual_apply_executed_by_ai": False,
            "candidate_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D122 may create operator dashboard/start command scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_ai_propose_only_provider_adapter_scope(), ensure_ascii=False, indent=2))
