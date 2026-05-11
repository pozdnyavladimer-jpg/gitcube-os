
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D155_REPORT = "reports/d155_sandbox_candidate_guarded_autonomy_cycle_closure_scope.json"
D155_CLOSURE_REPORT = "reports/d155_sandbox_candidate_guarded_autonomy_cycle_closure_report.json"
D155_REPLAY_INDEX = "reports/d155_sandbox_candidate_guarded_autonomy_cycle_replay_index.json"
D155_D156_SCOPE = "reports/d155_d156_controlled_autonomy_next_cycle_intake_scope.json"

OUT = "reports/d156_controlled_autonomy_next_cycle_intake_scope.json"
INTAKE_MANIFEST_OUT = "reports/d156_next_cycle_intake_manifest.json"
SAFETY_RESET_OUT = "reports/d156_next_cycle_safety_reset_report.json"
D157_SCOPE_OUT = "reports/d156_d157_provider_cycle_reentry_scope.json"

REQ_D155_DECISION = "SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE_READY"
REQ_D156_GATE = "D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE"
REQ_D157_GATE = "D157_PROVIDER_CYCLE_REENTRY_SCOPE"

FALSE_KEYS = [
    "network_accessed", "secret_read", "shell_executed_by_ai", "shell_from_ai_executed",
    "actual_apply_executed_by_ai", "real_apply_executed_by_ai", "route_inserted",
    "route_inserted_by_ai", "protected_core_mutated", "protected_core_mutated_by_ai",
    "canonical_memory_mutated", "git_action_by_ai", "git_commit_by_ai", "git_push_by_ai",
    "rollback_executed", "restore_executed",
]

D155_FALSE_FLAGS = [
    "real_apply_allowed_after_d155_by_ai",
    "route_insert_allowed_after_d155_by_ai",
    "protected_core_mutation_allowed_after_d155_by_ai",
    "network_allowed_after_d155_by_ai",
    "secret_read_allowed_after_d155_by_ai",
    "shell_allowed_after_d155_by_ai",
    "git_action_allowed_after_d155_by_ai",
]

D156_FALSE_FLAGS = [
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


def require_false(container, keys, errors, prefix):
    for key in keys:
        if key in container and container.get(key) is not False:
            errors.append(f"{prefix}.{key} must be false")


def validate_d155(d155, closure_report, replay_index, d156_scope):
    errors = []
    if not d155:
        return ["missing D155 guarded autonomy cycle closure scope report"]
    if d155.get("ok") is not True:
        errors.append("D155 ok must be true")
    if d155.get("decision") != REQ_D155_DECISION:
        errors.append("D155 decision must be guarded autonomy cycle closure ready")

    summary = d155.get("summary", {})
    required_summary = {
        "cycle_closure_status": "GUARDED_AUTONOMY_CYCLE_CLOSED_READY_FOR_CONTROLLED_NEXT_CYCLE_INTAKE",
        "replay_index_status": "GUARDED_AUTONOMY_CYCLE_REPLAY_INDEX_CREATED_NO_EXECUTION",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE_ONLY",
        "next_step": REQ_D156_GATE,
    }
    for key, expected in required_summary.items():
        if summary.get(key) != expected:
            errors.append(f"D155 summary.{key} must be {expected}")
    if "FRESH_INTENT" not in str(summary.get("candidate_status", "")):
        errors.append("D155 candidate_status must require fresh intent")

    guard = d155.get("guardrails", {})
    require_false(guard, FALSE_KEYS + D155_FALSE_FLAGS, errors, "D155 guardrails")
    for key in [
        "sandbox_candidate_guarded_autonomy_cycle_closure_scope_only",
        "guarded_autonomy_cycle_closure_report_only",
        "guarded_autonomy_cycle_replay_index_only",
        "approval_for_d156_controlled_autonomy_next_cycle_intake_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D155 guardrails.{key} must be true")

    if not closure_report:
        errors.append("missing D155 guarded autonomy cycle closure report")
    else:
        if closure_report.get("ok") is not True:
            errors.append("D155 closure report ok must be true")
        for key in ["real_apply_chain_closed", "next_cycle_requires_fresh_intent", "no_ai_core_mutation", "no_ai_route_insert", "no_ai_network", "no_ai_secret_read", "no_ai_shell", "no_ai_git_action"]:
            if closure_report.get(key) is not True:
                errors.append(f"D155 closure report {key} must be true")
        require_false(closure_report, FALSE_KEYS, errors, "D155 closure report")

    if not replay_index:
        errors.append("missing D155 guarded autonomy cycle replay index")
    else:
        if replay_index.get("ok") is not True:
            errors.append("D155 replay index ok must be true")
        if replay_index.get("replay_executes_anything") is not False:
            errors.append("D155 replay_executes_anything must be false")
        if replay_index.get("next_cycle_starts_from_new_intent_only") is not True:
            errors.append("D155 replay index must require new intent")
        require_false(replay_index, FALSE_KEYS, errors, "D155 replay index")

    if not d156_scope:
        errors.append("missing D155 D156 controlled autonomy next cycle intake scope")
    else:
        if d156_scope.get("ok") is not True:
            errors.append("D155 D156 scope ok must be true")
        if d156_scope.get("allowed_next_gate") != REQ_D156_GATE:
            errors.append("D155 D156 scope allowed_next_gate must be D156")
        if d156_scope.get("controlled_autonomy_next_cycle_intake_scope_only") is not True:
            errors.append("D155 D156 scope must be controlled-autonomy-next-cycle-intake-only")
        if d156_scope.get("fresh_intent_required") is not True:
            errors.append("D155 D156 scope must require fresh intent")
        require_false(d156_scope, D155_FALSE_FLAGS, errors, "D155 D156 scope")
    return errors


def build_intake_manifest(next_cycle_id, d155):
    return {
        "state": "D156_NEXT_CYCLE_INTAKE_MANIFEST",
        "ok": True,
        "next_cycle_id": next_cycle_id,
        "cycle_closure_id": d155.get("cycle_closure_id"),
        "archive2_id": d155.get("archive2_id"),
        "audit_id": d155.get("audit_id"),
        "candidate_id": d155.get("candidate_id"),
        "proposal_id": d155.get("proposal_id"),
        "created_at": now(),
        "intake_mode": "CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_MANIFEST_ONLY",
        "intake_status": "NEXT_CYCLE_INTAKE_CREATED_FRESH_INTENT_REQUIRED_NO_INHERITED_AUTHORITY",
        "fresh_intent_required": True,
        "inherited_execution_authority": False,
        "old_candidate_reuse_allowed": False,
        "old_apply_authority_reuse_allowed": False,
        "operator_review_required": True,
        "provider_reentry_scope_only": True,
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "route_inserted_by_ai": False,
        "protected_core_mutated": False,
        "protected_core_mutated_by_ai": False,
        "canonical_memory_mutated": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_safety_reset_report(next_cycle_id, d155):
    data = {
        "state": "D156_NEXT_CYCLE_SAFETY_RESET_REPORT",
        "ok": True,
        "next_cycle_id": next_cycle_id,
        "cycle_closure_id": d155.get("cycle_closure_id"),
        "created_at": now(),
        "reset_mode": "NEXT_CYCLE_SAFETY_RESET_ONLY_NO_ACTION",
        "reset_status": "SAFETY_FLAGS_RESET_FOR_NEXT_CONTROLLED_CYCLE",
        "previous_cycle_closed": True,
        "fresh_intent_required": True,
        "provider_must_reenter_dry_scope": True,
        "candidate_must_be_rebuilt": True,
        "review_must_be_repeated": True,
        "apply_authority_must_be_reissued": True,
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }
    for key in D156_FALSE_FLAGS:
        data[key] = False
    return data


def build_d157_scope(next_cycle_id, d155):
    data = {
        "state": "D156_D157_PROVIDER_CYCLE_REENTRY_SCOPE",
        "ok": True,
        "next_cycle_id": next_cycle_id,
        "cycle_closure_id": d155.get("cycle_closure_id"),
        "archive2_id": d155.get("archive2_id"),
        "audit_id": d155.get("audit_id"),
        "candidate_id": d155.get("candidate_id"),
        "proposal_id": d155.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D157_GATE,
        "provider_cycle_reentry_scope_only": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "d157_allowed_to_create": [
            "provider_cycle_reentry_scope",
            "provider_reentry_config_manifest",
            "provider_reentry_dry_ping_scope",
            "d158_proposal_cycle_reentry_intake_scope",
        ],
        "d157_must_not_execute": [
            "real_provider_call",
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
    }
    for key in D156_FALSE_FLAGS:
        data[key] = False
    return data


def create_controlled_autonomy_next_cycle_intake_scope(root="."):
    root = Path(root).resolve()
    d155 = read_json(root / D155_REPORT, {}) or {}
    closure_report = read_json(root / D155_CLOSURE_REPORT, {}) or {}
    replay_index = read_json(root / D155_REPLAY_INDEX, {}) or {}
    d156_scope = read_json(root / D155_D156_SCOPE, {}) or {}

    errors = validate_d155(d155, closure_report, replay_index, d156_scope)
    next_cycle_id = "d156-" + digest({
        "cycle_closure_id": d155.get("cycle_closure_id"),
        "archive2_id": d155.get("archive2_id"),
        "audit_id": d155.get("audit_id"),
        "candidate_id": d155.get("candidate_id"),
        "proposal_id": d155.get("proposal_id"),
    })

    intake_manifest = build_intake_manifest(next_cycle_id, d155)
    safety_reset_report = build_safety_reset_report(next_cycle_id, d155)
    d157_scope = build_d157_scope(next_cycle_id, d155)

    for item_name, item in [("intake_manifest", intake_manifest), ("safety_reset_report", safety_reset_report), ("d157_scope", d157_scope)]:
        require_false(item, FALSE_KEYS + D156_FALSE_FLAGS, errors, item_name)

    ok = not errors
    decision = "CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE_READY" if ok else "CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE_BLOCKED"
    result = "D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE_CREATED" if ok else "D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE_BLOCKED"

    if ok:
        write_json(root / INTAKE_MANIFEST_OUT, intake_manifest)
        write_json(root / SAFETY_RESET_OUT, safety_reset_report)
        write_json(root / D157_SCOPE_OUT, d157_scope)

    guardrails = {
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "shell_from_ai_executed": False,
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "route_inserted_by_ai": False,
        "protected_core_mutated": False,
        "protected_core_mutated_by_ai": False,
        "canonical_memory_mutated": False,
        "git_commit_by_ai": False,
        "git_push_by_ai": False,
        "git_action_by_ai": False,
        "controlled_autonomy_next_cycle_intake_scope_only": True,
        "next_cycle_intake_manifest_only": True,
        "next_cycle_safety_reset_report_only": True,
        "fresh_intent_required": True,
        "inherited_execution_authority": False,
        "approval_for_d157_provider_cycle_reentry_scope_only": ok,
    }
    for key in D156_FALSE_FLAGS:
        guardrails[key] = False

    report = {
        "state": "D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "next_cycle_id": next_cycle_id,
        "cycle_closure_id": d155.get("cycle_closure_id"),
        "archive2_id": d155.get("archive2_id"),
        "audit_id": d155.get("audit_id"),
        "candidate_id": d155.get("candidate_id"),
        "proposal_id": d155.get("proposal_id"),
        "source_d155_report": D155_REPORT,
        "next_cycle_intake_manifest": intake_manifest if ok else {},
        "next_cycle_safety_reset_report": safety_reset_report if ok else {},
        "d157_scope": d157_scope if ok else {},
        "guardrails": guardrails,
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "next_cycle_id": next_cycle_id,
            "cycle_closure_id": d155.get("cycle_closure_id"),
            "candidate_id": d155.get("candidate_id"),
            "proposal_id": d155.get("proposal_id"),
            "next_cycle_intake_status": "NEXT_CYCLE_INTAKE_CREATED_FRESH_INTENT_REQUIRED_NO_INHERITED_AUTHORITY" if ok else "BLOCKED",
            "safety_reset_status": "SAFETY_FLAGS_RESET_FOR_NEXT_CONTROLLED_CYCLE" if ok else "BLOCKED",
            "candidate_status": "PREVIOUS_CANDIDATE_CLOSED_NEXT_CYCLE_REQUIRES_FRESH_INTENT" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D157_PROVIDER_CYCLE_REENTRY_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D157_GATE if ok else "BLOCKED",
        },
    }
    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_controlled_autonomy_next_cycle_intake_scope(), ensure_ascii=False, indent=2))
