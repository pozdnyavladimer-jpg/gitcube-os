
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D156_REPORT = "reports/d156_controlled_autonomy_next_cycle_intake_scope.json"
D156_INTAKE_MANIFEST = "reports/d156_next_cycle_intake_manifest.json"
D156_SAFETY_RESET = "reports/d156_next_cycle_safety_reset_report.json"
D156_D157_SCOPE = "reports/d156_d157_provider_cycle_reentry_scope.json"

OUT = "reports/d157_provider_cycle_reentry_scope.json"
CONFIG_OUT = "reports/d157_provider_reentry_config_manifest.json"
DRY_PING_OUT = "reports/d157_provider_reentry_dry_ping_scope.json"
D158_SCOPE_OUT = "reports/d157_d158_proposal_cycle_reentry_intake_scope.json"

REQ_D156_DECISION = "CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE_READY"
REQ_D157_GATE = "D157_PROVIDER_CYCLE_REENTRY_SCOPE"
REQ_D158_GATE = "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE"

FALSE_KEYS = [
    "network_accessed", "secret_read", "shell_executed_by_ai",
    "actual_apply_executed_by_ai", "real_apply_executed_by_ai",
    "route_inserted", "route_inserted_by_ai",
    "protected_core_mutated", "protected_core_mutated_by_ai",
    "git_action_by_ai",
]

STATUS_FALSE_D156 = [
    "real_apply_allowed_after_d156_by_ai",
    "route_insert_allowed_after_d156_by_ai",
    "protected_core_mutation_allowed_after_d156_by_ai",
    "network_allowed_after_d156_by_ai",
    "secret_read_allowed_after_d156_by_ai",
    "shell_allowed_after_d156_by_ai",
    "git_action_allowed_after_d156_by_ai",
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


def validate_d156(d156, intake_manifest, safety_reset, d157_scope):
    errors = []
    if not d156:
        return ["missing D156 controlled autonomy next cycle intake scope report"]

    if d156.get("ok") is not True:
        errors.append("D156 ok must be true")
    if d156.get("decision") != REQ_D156_DECISION:
        errors.append("D156 decision must be CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE_READY")

    summary = d156.get("summary", {})
    expected = {
        "next_cycle_intake_status": "NEXT_CYCLE_INTAKE_CREATED_FRESH_INTENT_REQUIRED_NO_INHERITED_AUTHORITY",
        "safety_reset_status": "SAFETY_FLAGS_RESET_FOR_NEXT_CONTROLLED_CYCLE",
        "candidate_status": "PREVIOUS_CANDIDATE_CLOSED_NEXT_CYCLE_REQUIRES_FRESH_INTENT",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D157_PROVIDER_CYCLE_REENTRY_SCOPE_ONLY",
        "next_step": REQ_D157_GATE,
    }
    for k, v in expected.items():
        if summary.get(k) != v:
            errors.append(f"D156 summary.{k} must be {v}")

    guard = d156.get("guardrails", {})
    for k in FALSE_KEYS + STATUS_FALSE_D156:
        if guard.get(k) is not False:
            errors.append(f"D156 guardrails.{k} must be false")
    for k in [
        "controlled_autonomy_next_cycle_intake_scope_only",
        "next_cycle_intake_manifest_only",
        "next_cycle_safety_reset_report_only",
        "fresh_intent_required",
        "approval_for_d157_provider_cycle_reentry_scope_only",
    ]:
        if guard.get(k) is not True:
            errors.append(f"D156 guardrails.{k} must be true")
    if guard.get("inherited_execution_authority") is not False:
        errors.append("D156 inherited_execution_authority must be false")

    if not intake_manifest:
        errors.append("missing D156 next cycle intake manifest")
    else:
        if intake_manifest.get("ok") is not True:
            errors.append("D156 intake manifest ok must be true")
        if intake_manifest.get("intake_status") != "NEXT_CYCLE_INTAKE_CREATED_FRESH_INTENT_REQUIRED_NO_INHERITED_AUTHORITY":
            errors.append("D156 intake manifest status must require fresh intent/no inherited authority")
        for k in ["fresh_intent_required", "operator_review_required", "provider_reentry_scope_only"]:
            if intake_manifest.get(k) is not True:
                errors.append(f"D156 intake manifest {k} must be true")
        for k in ["inherited_execution_authority", "old_candidate_reuse_allowed", "old_apply_authority_reuse_allowed"]:
            if intake_manifest.get(k) is not False:
                errors.append(f"D156 intake manifest {k} must be false")
        for k in FALSE_KEYS:
            if k in intake_manifest and intake_manifest.get(k) is not False:
                errors.append(f"D156 intake manifest {k} must be false")

    if not safety_reset:
        errors.append("missing D156 next cycle safety reset report")
    else:
        if safety_reset.get("ok") is not True:
            errors.append("D156 safety reset ok must be true")
        if safety_reset.get("reset_status") != "SAFETY_FLAGS_RESET_FOR_NEXT_CONTROLLED_CYCLE":
            errors.append("D156 safety reset status must be reset-for-next-controlled-cycle")
        for k in [
            "previous_cycle_closed", "fresh_intent_required", "provider_must_reenter_dry_scope",
            "candidate_must_be_rebuilt", "review_must_be_repeated", "apply_authority_must_be_reissued",
        ]:
            if safety_reset.get(k) is not True:
                errors.append(f"D156 safety reset {k} must be true")
        for k in FALSE_KEYS + STATUS_FALSE_D156:
            # Compatibility: older D156 safety reset reports did not emit every *_by_ai alias.
            # If the field exists it must be false; missing aliases are accepted.
            if k in safety_reset and safety_reset.get(k) is not False:
                errors.append(f"D156 safety reset {k} must be false")

    if not d157_scope:
        errors.append("missing D156 D157 provider cycle reentry scope")
    else:
        if d157_scope.get("ok") is not True:
            errors.append("D156 D157 scope ok must be true")
        if d157_scope.get("allowed_next_gate") != REQ_D157_GATE:
            errors.append("D156 D157 scope allowed_next_gate must be D157")
        if d157_scope.get("provider_cycle_reentry_scope_only") is not True:
            errors.append("D156 D157 scope must be provider-cycle-reentry-only")
        if d157_scope.get("fresh_intent_required") is not True:
            errors.append("D156 D157 scope must require fresh intent")
        if d157_scope.get("human_review_required") is not True:
            errors.append("D156 D157 scope must require human review")
        for k in STATUS_FALSE_D156:
            if d157_scope.get(k) is not False:
                errors.append(f"D156 D157 scope {k} must be false")

    return errors


def build_config(reentry_id, d156):
    return {
        "state": "D157_PROVIDER_REENTRY_CONFIG_MANIFEST",
        "ok": True,
        "reentry_id": reentry_id,
        "next_cycle_id": d156.get("next_cycle_id"),
        "cycle_closure_id": d156.get("cycle_closure_id"),
        "candidate_id": d156.get("candidate_id"),
        "proposal_id": d156.get("proposal_id"),
        "created_at": now(),
        "config_mode": "PROVIDER_REENTRY_CONFIG_MANIFEST_ONLY_NO_PROVIDER_CALL",
        "provider_reentry_status": "PROVIDER_REENTRY_CONFIG_CREATED_NO_NETWORK_NO_SECRET",
        "fresh_intent_required": True,
        "manual_provider_enable_required": True,
        "dry_ping_scope_required": True,
        "real_provider_call_performed": False,
        "provider_network_call_performed": False,
        "provider_secret_read_performed": False,
        "provider_response_ingested": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "route_inserted_by_ai": False,
        "protected_core_mutated": False,
        "protected_core_mutated_by_ai": False,
        "human_review_required": True,
    }


def build_dry_ping(reentry_id, d156):
    return {
        "state": "D157_PROVIDER_REENTRY_DRY_PING_SCOPE",
        "ok": True,
        "reentry_id": reentry_id,
        "next_cycle_id": d156.get("next_cycle_id"),
        "candidate_id": d156.get("candidate_id"),
        "proposal_id": d156.get("proposal_id"),
        "created_at": now(),
        "dry_ping_mode": "PROVIDER_REENTRY_DRY_PING_SCOPE_ONLY_NO_NETWORK",
        "dry_ping_status": "DRY_PING_SCOPE_CREATED_PROVIDER_NOT_CALLED",
        "dry_ping_executes_provider": False,
        "real_provider_call_performed": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "human_review_required": True,
    }


def build_d158_scope(reentry_id, d156):
    return {
        "state": "D157_D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE",
        "ok": True,
        "reentry_id": reentry_id,
        "next_cycle_id": d156.get("next_cycle_id"),
        "cycle_closure_id": d156.get("cycle_closure_id"),
        "candidate_id": d156.get("candidate_id"),
        "proposal_id": d156.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D158_GATE,
        "proposal_cycle_reentry_intake_scope_only": True,
        "fresh_intent_required": True,
        "provider_response_must_be_dry_or_manual": True,
        "human_review_required": True,
        "d158_allowed_to_create": [
            "proposal_cycle_reentry_intake_scope",
            "proposal_reentry_intake_manifest",
            "proposal_reentry_no_execution_assertions",
            "d159_proposal_to_sandbox_candidate_reentry_scope",
        ],
        "d158_must_not_execute": [
            "real_provider_call", "real_core_apply", "route_insert_by_ai",
            "protected_core_mutation_by_ai", "canonical_memory_overwrite_by_ai",
            "shell_exec_from_ai", "network_call_by_ai", "secret_read_by_ai",
            "git_commit_by_ai", "git_push_by_ai", "rollback_execute_by_ai", "restore_execute_by_ai",
        ],
        "real_apply_allowed_after_d157_by_ai": False,
        "route_insert_allowed_after_d157_by_ai": False,
        "protected_core_mutation_allowed_after_d157_by_ai": False,
        "network_allowed_after_d157_by_ai": False,
        "secret_read_allowed_after_d157_by_ai": False,
        "shell_allowed_after_d157_by_ai": False,
        "git_action_allowed_after_d157_by_ai": False,
    }


def create_provider_cycle_reentry_scope(root="."):
    root = Path(root).resolve()

    d156 = read_json(root / D156_REPORT, {}) or {}
    intake_manifest = read_json(root / D156_INTAKE_MANIFEST, {}) or {}
    safety_reset = read_json(root / D156_SAFETY_RESET, {}) or {}
    d157_scope = read_json(root / D156_D157_SCOPE, {}) or {}

    errors = validate_d156(d156, intake_manifest, safety_reset, d157_scope)

    reentry_id = "d157-" + digest({
        "next_cycle_id": d156.get("next_cycle_id"),
        "cycle_closure_id": d156.get("cycle_closure_id"),
        "candidate_id": d156.get("candidate_id"),
        "proposal_id": d156.get("proposal_id"),
    })

    config = build_config(reentry_id, d156)
    dry_ping = build_dry_ping(reentry_id, d156)
    d158_scope = build_d158_scope(reentry_id, d156)

    for name, item in [("config", config), ("dry_ping", dry_ping), ("d158_scope", d158_scope)]:
        for k in [
            "real_provider_call_performed", "provider_network_call_performed",
            "provider_secret_read_performed", "provider_response_ingested",
            "network_accessed", "secret_read", "shell_executed_by_ai", "git_action_by_ai",
            "actual_apply_executed_by_ai", "real_apply_executed_by_ai",
            "route_inserted", "route_inserted_by_ai",
            "protected_core_mutated", "protected_core_mutated_by_ai",
            "real_apply_allowed_after_d157_by_ai",
            "route_insert_allowed_after_d157_by_ai",
            "protected_core_mutation_allowed_after_d157_by_ai",
            "network_allowed_after_d157_by_ai",
            "secret_read_allowed_after_d157_by_ai",
            "shell_allowed_after_d157_by_ai",
            "git_action_allowed_after_d157_by_ai",
        ]:
            if k in item and item.get(k) is not False:
                errors.append(f"{name} {k} must be false")

    ok = not errors
    decision = "PROVIDER_CYCLE_REENTRY_SCOPE_READY" if ok else "PROVIDER_CYCLE_REENTRY_SCOPE_BLOCKED"
    result = "D157_PROVIDER_CYCLE_REENTRY_SCOPE_CREATED" if ok else "D157_PROVIDER_CYCLE_REENTRY_SCOPE_BLOCKED"

    if ok:
        write_json(root / CONFIG_OUT, config)
        write_json(root / DRY_PING_OUT, dry_ping)
        write_json(root / D158_SCOPE_OUT, d158_scope)

    report = {
        "state": "D157_PROVIDER_CYCLE_REENTRY_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_PROVIDER_CYCLE_REENTRY_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "reentry_id": reentry_id,
        "next_cycle_id": d156.get("next_cycle_id"),
        "cycle_closure_id": d156.get("cycle_closure_id"),
        "candidate_id": d156.get("candidate_id"),
        "proposal_id": d156.get("proposal_id"),
        "source_d156_report": D156_REPORT,
        "provider_reentry_config_manifest": config if ok else {},
        "provider_reentry_dry_ping_scope": dry_ping if ok else {},
        "d158_scope": d158_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "shell_executed_by_ai": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "route_inserted_by_ai": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "real_provider_call_performed": False,
            "provider_network_call_performed": False,
            "provider_secret_read_performed": False,
            "provider_response_ingested": False,
            "provider_cycle_reentry_scope_only": True,
            "provider_reentry_config_manifest_only": True,
            "provider_reentry_dry_ping_scope_only": True,
            "fresh_intent_required": True,
            "approval_for_d158_proposal_cycle_reentry_intake_scope_only": ok,
            "real_apply_allowed_after_d157_by_ai": False,
            "route_insert_allowed_after_d157_by_ai": False,
            "protected_core_mutation_allowed_after_d157_by_ai": False,
            "network_allowed_after_d157_by_ai": False,
            "secret_read_allowed_after_d157_by_ai": False,
            "shell_allowed_after_d157_by_ai": False,
            "git_action_allowed_after_d157_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "reentry_id": reentry_id,
            "next_cycle_id": d156.get("next_cycle_id"),
            "candidate_id": d156.get("candidate_id"),
            "proposal_id": d156.get("proposal_id"),
            "provider_reentry_status": "PROVIDER_REENTRY_CONFIG_CREATED_NO_NETWORK_NO_SECRET" if ok else "BLOCKED",
            "dry_ping_status": "DRY_PING_SCOPE_CREATED_PROVIDER_NOT_CALLED" if ok else "BLOCKED",
            "candidate_status": "NEXT_CYCLE_PROVIDER_REENTRY_READY_NO_PROVIDER_CALL" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D158_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "provider_cycle_reentry_scope_created": ok,
            "provider_reentry_config_manifest_created": ok,
            "provider_reentry_dry_ping_scope_created": ok,
            "d158_scope_created": ok,
            "real_provider_call_performed": False,
            "network_accessed": False,
            "secret_read": False,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D158 may create proposal cycle reentry intake scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_provider_cycle_reentry_scope(), ensure_ascii=False, indent=2))
