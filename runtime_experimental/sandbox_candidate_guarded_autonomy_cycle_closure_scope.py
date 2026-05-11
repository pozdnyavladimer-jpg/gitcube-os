
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D154_REPORT = "reports/d154_sandbox_candidate_real_apply_chain_archive_scope.json"
D154_ARCHIVE_MANIFEST = "reports/d154_sandbox_candidate_real_apply_chain_archive_manifest.json"
D154_CLOSURE_RECEIPT = "reports/d154_sandbox_candidate_real_apply_chain_closure_receipt.json"
D154_D155_SCOPE = "reports/d154_d155_sandbox_candidate_guarded_autonomy_cycle_closure_scope.json"

OUT = "reports/d155_sandbox_candidate_guarded_autonomy_cycle_closure_scope.json"
CLOSURE_REPORT_OUT = "reports/d155_sandbox_candidate_guarded_autonomy_cycle_closure_report.json"
REPLAY_INDEX_OUT = "reports/d155_sandbox_candidate_guarded_autonomy_cycle_replay_index.json"
D156_SCOPE_OUT = "reports/d155_d156_controlled_autonomy_next_cycle_intake_scope.json"

REQ_D154_DECISION = "SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE_READY"
REQ_D155_GATE = "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE"
REQ_D156_GATE = "D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE"

FALSE_KEYS = [
    "external_ai_called", "network_accessed", "api_key_read", "secret_read",
    "shell_from_ai_executed", "shell_executed_by_ai",
    "runtime_code_mutated", "protected_core_mutated", "protected_core_mutated_by_ai",
    "canonical_memory_mutated", "actual_apply_executed_by_ai", "real_apply_executed_by_ai",
    "route_inserted", "route_inserted_by_ai",
    "git_commit_by_ai", "git_push_by_ai", "git_action_by_ai",
    "rollback_executed", "restore_executed",
]

STATUS_FALSE_D154 = [
    "real_apply_allowed_after_d154_by_ai",
    "route_insert_allowed_after_d154_by_ai",
    "protected_core_mutation_allowed_after_d154_by_ai",
    "network_allowed_after_d154_by_ai",
    "secret_read_allowed_after_d154_by_ai",
    "shell_allowed_after_d154_by_ai",
    "git_action_allowed_after_d154_by_ai",
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


def validate_d154(d154, archive_manifest, closure_receipt, d155_scope):
    errors = []
    if not d154:
        errors.append("missing D154 sandbox candidate real apply chain archive scope report")
        return errors

    if d154.get("ok") is not True:
        errors.append("D154 ok must be true")
    if d154.get("decision") != REQ_D154_DECISION:
        errors.append("D154 decision must be SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE_READY")

    summary = d154.get("summary", {})
    expected = {
        "real_apply_chain_archive_status": "REAL_APPLY_CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
        "chain_closure_status": "REAL_APPLY_CHAIN_ARCHIVED_READY_FOR_GUARDED_AUTONOMY_CYCLE_CLOSURE",
        "candidate_status": "REAL_APPLY_CHAIN_ARCHIVED_READY_FOR_GUARDED_AUTONOMY_CYCLE_CLOSURE_NOT_CORE_MUTATED_BY_AI",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE_ONLY",
        "next_step": REQ_D155_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D154 summary.{key} must be {value}")

    guard = d154.get("guardrails", {})
    for key in FALSE_KEYS:
        if key in guard and guard.get(key) is not False:
            errors.append(f"D154 guardrails.{key} must be false")
    for key in STATUS_FALSE_D154:
        if guard.get(key) is not False:
            errors.append(f"D154 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_real_apply_chain_archive_scope_only",
        "real_apply_chain_archive_manifest_only",
        "real_apply_chain_closure_receipt_only",
        "approval_for_d155_guarded_autonomy_cycle_closure_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D154 guardrails.{key} must be true")

    for key in ["archive_upload_performed", "archive_compression_performed"]:
        if guard.get(key) is not False:
            errors.append(f"D154 guardrails.{key} must be false")

    if not archive_manifest:
        errors.append("missing D154 real apply chain archive manifest")
    else:
        if archive_manifest.get("ok") is not True:
            errors.append("D154 archive manifest ok must be true")
        if archive_manifest.get("archive_mode") != "real-apply-chain-archive-manifest-only":
            errors.append("D154 archive manifest mode must be real-apply-chain-archive-manifest-only")
        if archive_manifest.get("archive_status") != "REAL_APPLY_CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED":
            errors.append("D154 archive status must be manifest-created-not-compressed-not-uploaded")
        if archive_manifest.get("archived_without_real_apply_again") is not True:
            errors.append("D154 archive manifest archived_without_real_apply_again must be true")
        for key in ["archive_upload_performed", "archive_compression_performed"]:
            if archive_manifest.get(key) is not False:
                errors.append(f"D154 archive manifest {key} must be false")
        for key in FALSE_KEYS:
            if key in archive_manifest and archive_manifest.get(key) is not False:
                errors.append(f"D154 archive manifest {key} must be false")

    if not closure_receipt:
        errors.append("missing D154 real apply chain closure receipt")
    else:
        if closure_receipt.get("ok") is not True:
            errors.append("D154 closure receipt ok must be true")
        if closure_receipt.get("closure_status") != "REAL_APPLY_CHAIN_ARCHIVED_READY_FOR_GUARDED_AUTONOMY_CYCLE_CLOSURE":
            errors.append("D154 closure receipt status must be ready for guarded autonomy cycle closure")
        for key in [
            "chain_closed_for_ai_execution", "no_second_apply", "no_ai_core_mutation",
            "no_ai_route_insert", "no_ai_network", "no_ai_secret_read", "no_ai_shell", "no_ai_git_action",
        ]:
            if closure_receipt.get(key) is not True:
                errors.append(f"D154 closure receipt {key} must be true")
        for key in FALSE_KEYS:
            if key in closure_receipt and closure_receipt.get(key) is not False:
                errors.append(f"D154 closure receipt {key} must be false")

    if not d155_scope:
        errors.append("missing D154 D155 guarded autonomy cycle closure scope")
    else:
        if d155_scope.get("ok") is not True:
            errors.append("D154 D155 scope ok must be true")
        if d155_scope.get("allowed_next_gate") != REQ_D155_GATE:
            errors.append("D154 D155 scope allowed_next_gate must be D155")
        if d155_scope.get("sandbox_candidate_guarded_autonomy_cycle_closure_scope_only") is not True:
            errors.append("D154 D155 scope must be guarded-autonomy-cycle-closure-only")
        if d155_scope.get("human_review_required") is not True:
            errors.append("D154 D155 scope must require human review")
        for key in STATUS_FALSE_D154:
            if d155_scope.get(key) is not False:
                errors.append(f"D154 D155 scope {key} must be false")

    return errors


def build_closure_report(cycle_closure_id, d154):
    return {
        "state": "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_REPORT",
        "ok": True,
        "cycle_closure_id": cycle_closure_id,
        "archive2_id": d154.get("archive2_id"),
        "audit_id": d154.get("audit_id"),
        "verification_id": d154.get("verification_id"),
        "run_apply_id": d154.get("run_apply_id"),
        "signature_id": d154.get("signature_id"),
        "preflight_id": d154.get("preflight_id"),
        "intent_id": d154.get("intent_id"),
        "decision_id": d154.get("decision_id"),
        "archive_id": d154.get("archive_id"),
        "candidate_id": d154.get("candidate_id"),
        "proposal_id": d154.get("proposal_id"),
        "created_at": now(),
        "closure_mode": "GUARDED_AUTONOMY_CYCLE_CLOSURE_REPORT_ONLY_NO_ACTION",
        "cycle_closure_status": "GUARDED_AUTONOMY_CYCLE_CLOSED_READY_FOR_CONTROLLED_NEXT_CYCLE_INTAKE",
        "real_apply_chain_closed": True,
        "operator_cycle_review_required": True,
        "next_cycle_requires_fresh_intent": True,
        "no_second_apply": True,
        "no_ai_core_mutation": True,
        "no_ai_route_insert": True,
        "no_ai_network": True,
        "no_ai_secret_read": True,
        "no_ai_shell": True,
        "no_ai_git_action": True,
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


def build_replay_index(cycle_closure_id, d154):
    return {
        "state": "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_REPLAY_INDEX",
        "ok": True,
        "cycle_closure_id": cycle_closure_id,
        "archive2_id": d154.get("archive2_id"),
        "audit_id": d154.get("audit_id"),
        "candidate_id": d154.get("candidate_id"),
        "proposal_id": d154.get("proposal_id"),
        "created_at": now(),
        "replay_index_mode": "GUARDED_AUTONOMY_CYCLE_REPLAY_INDEX_ONLY_NO_EXECUTION",
        "replay_status": "GUARDED_AUTONOMY_CYCLE_REPLAY_INDEX_CREATED_NO_EXECUTION",
        "cycle_replay_sources": [
            "reports/d121_ai_propose_only_provider_adapter_scope.json",
            "reports/d126_proposal_to_sandbox_candidate_scope.json",
            "reports/d139_sandbox_candidate_controlled_execution_run_scope.json",
            "reports/d147_sandbox_candidate_promotion_decision_scope.json",
            "reports/d151_sandbox_candidate_guarded_real_apply_run_scope.json",
            "reports/d154_sandbox_candidate_real_apply_chain_archive_scope.json",
        ],
        "replay_executes_anything": False,
        "next_cycle_starts_from_new_intent_only": True,
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


def build_d156_scope(cycle_closure_id, d154):
    return {
        "state": "D155_D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE",
        "ok": True,
        "cycle_closure_id": cycle_closure_id,
        "archive2_id": d154.get("archive2_id"),
        "audit_id": d154.get("audit_id"),
        "verification_id": d154.get("verification_id"),
        "run_apply_id": d154.get("run_apply_id"),
        "signature_id": d154.get("signature_id"),
        "preflight_id": d154.get("preflight_id"),
        "intent_id": d154.get("intent_id"),
        "decision_id": d154.get("decision_id"),
        "archive_id": d154.get("archive_id"),
        "candidate_id": d154.get("candidate_id"),
        "proposal_id": d154.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D156_GATE,
        "controlled_autonomy_next_cycle_intake_scope_only": True,
        "fresh_intent_required": True,
        "human_review_required": True,
        "d156_allowed_to_create": [
            "controlled_autonomy_next_cycle_intake_scope",
            "next_cycle_intake_manifest",
            "next_cycle_safety_reset_report",
            "d157_provider_cycle_reentry_scope",
        ],
        "d156_must_not_execute": [
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
        "real_apply_allowed_after_d155_by_ai": False,
        "route_insert_allowed_after_d155_by_ai": False,
        "protected_core_mutation_allowed_after_d155_by_ai": False,
        "network_allowed_after_d155_by_ai": False,
        "secret_read_allowed_after_d155_by_ai": False,
        "shell_allowed_after_d155_by_ai": False,
        "git_action_allowed_after_d155_by_ai": False,
    }


def create_sandbox_candidate_guarded_autonomy_cycle_closure_scope(root="."):
    root = Path(root).resolve()

    d154 = read_json(root / D154_REPORT, {}) or {}
    archive_manifest = read_json(root / D154_ARCHIVE_MANIFEST, {}) or {}
    closure_receipt = read_json(root / D154_CLOSURE_RECEIPT, {}) or {}
    d155_scope = read_json(root / D154_D155_SCOPE, {}) or {}

    errors = validate_d154(d154, archive_manifest, closure_receipt, d155_scope)

    cycle_closure_id = "d155-" + digest({
        "archive2_id": d154.get("archive2_id"),
        "audit_id": d154.get("audit_id"),
        "verification_id": d154.get("verification_id"),
        "run_apply_id": d154.get("run_apply_id"),
        "candidate_id": d154.get("candidate_id"),
        "proposal_id": d154.get("proposal_id"),
    })

    closure_report = build_closure_report(cycle_closure_id, d154)
    replay_index = build_replay_index(cycle_closure_id, d154)
    d156_scope = build_d156_scope(cycle_closure_id, d154)

    for item_name, item in [
        ("closure_report", closure_report),
        ("replay_index", replay_index),
        ("d156_scope", d156_scope),
    ]:
        for key in [
            "actual_apply_executed_by_ai", "real_apply_executed_by_ai",
            "route_inserted", "route_inserted_by_ai",
            "protected_core_mutated", "protected_core_mutated_by_ai",
            "network_accessed", "secret_read", "shell_executed_by_ai", "git_action_by_ai",
            "real_apply_allowed_after_d155_by_ai",
            "route_insert_allowed_after_d155_by_ai",
            "protected_core_mutation_allowed_after_d155_by_ai",
            "network_allowed_after_d155_by_ai",
            "secret_read_allowed_after_d155_by_ai",
            "shell_allowed_after_d155_by_ai",
            "git_action_allowed_after_d155_by_ai",
        ]:
            if key in item and item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE_BLOCKED"
    result = "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE_CREATED" if ok else "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE_BLOCKED"

    if ok:
        write_json(root / CLOSURE_REPORT_OUT, closure_report)
        write_json(root / REPLAY_INDEX_OUT, replay_index)
        write_json(root / D156_SCOPE_OUT, d156_scope)

    report = {
        "state": "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "cycle_closure_id": cycle_closure_id,
        "archive2_id": d154.get("archive2_id"),
        "audit_id": d154.get("audit_id"),
        "verification_id": d154.get("verification_id"),
        "run_apply_id": d154.get("run_apply_id"),
        "signature_id": d154.get("signature_id"),
        "preflight_id": d154.get("preflight_id"),
        "intent_id": d154.get("intent_id"),
        "decision_id": d154.get("decision_id"),
        "archive_id": d154.get("archive_id"),
        "candidate_id": d154.get("candidate_id"),
        "proposal_id": d154.get("proposal_id"),
        "source_d154_report": D154_REPORT,
        "guarded_autonomy_cycle_closure_report": closure_report if ok else {},
        "guarded_autonomy_cycle_replay_index": replay_index if ok else {},
        "d156_scope": d156_scope if ok else {},
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
            "archive_upload_performed": False,
            "archive_compression_performed": False,
            "sandbox_candidate_guarded_autonomy_cycle_closure_scope_only": True,
            "guarded_autonomy_cycle_closure_report_only": True,
            "guarded_autonomy_cycle_replay_index_only": True,
            "approval_for_d156_controlled_autonomy_next_cycle_intake_scope_only": ok,
            "real_apply_allowed_after_d155_by_ai": False,
            "route_insert_allowed_after_d155_by_ai": False,
            "protected_core_mutation_allowed_after_d155_by_ai": False,
            "network_allowed_after_d155_by_ai": False,
            "secret_read_allowed_after_d155_by_ai": False,
            "shell_allowed_after_d155_by_ai": False,
            "git_action_allowed_after_d155_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "cycle_closure_id": cycle_closure_id,
            "archive2_id": d154.get("archive2_id"),
            "audit_id": d154.get("audit_id"),
            "candidate_id": d154.get("candidate_id"),
            "proposal_id": d154.get("proposal_id"),
            "cycle_closure_status": "GUARDED_AUTONOMY_CYCLE_CLOSED_READY_FOR_CONTROLLED_NEXT_CYCLE_INTAKE" if ok else "BLOCKED",
            "replay_index_status": "GUARDED_AUTONOMY_CYCLE_REPLAY_INDEX_CREATED_NO_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "GUARDED_AUTONOMY_CYCLE_CLOSED_NEXT_CYCLE_REQUIRES_FRESH_INTENT_NOT_CORE_MUTATED_BY_AI" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D156_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "guarded_autonomy_cycle_closure_scope_created": ok,
            "guarded_autonomy_cycle_closure_report_created": ok,
            "guarded_autonomy_cycle_replay_index_created": ok,
            "d156_scope_created": ok,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D156 may create controlled autonomy next cycle intake scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_guarded_autonomy_cycle_closure_scope(), ensure_ascii=False, indent=2))
