
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

D153_REPORT = "reports/d153_sandbox_candidate_final_real_apply_audit_scope.json"
D153_AUDIT_LEDGER = "reports/d153_sandbox_candidate_real_apply_audit_ledger.json"
D153_REPLAY_INDEX = "reports/d153_sandbox_candidate_real_apply_replay_index.json"
D153_D154_SCOPE = "reports/d153_d154_sandbox_candidate_real_apply_chain_archive_scope.json"

OUT = "reports/d154_sandbox_candidate_real_apply_chain_archive_scope.json"
ARCHIVE_MANIFEST_OUT = "reports/d154_sandbox_candidate_real_apply_chain_archive_manifest.json"
CLOSURE_RECEIPT_OUT = "reports/d154_sandbox_candidate_real_apply_chain_closure_receipt.json"
D155_SCOPE_OUT = "reports/d154_d155_sandbox_candidate_guarded_autonomy_cycle_closure_scope.json"

REQ_D153_DECISION = "SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_READY"
REQ_D154_GATE = "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE"
REQ_D155_GATE = "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE"

FALSE_KEYS = [
    "network_accessed", "secret_read", "shell_executed_by_ai", "shell_from_ai_executed",
    "actual_apply_executed_by_ai", "real_apply_executed_by_ai", "route_inserted",
    "route_inserted_by_ai", "protected_core_mutated", "protected_core_mutated_by_ai",
    "canonical_memory_mutated", "git_action_by_ai", "git_commit_by_ai", "git_push_by_ai",
]

STATUS_FALSE_D153 = [
    "real_apply_allowed_after_d153_by_ai", "route_insert_allowed_after_d153_by_ai",
    "protected_core_mutation_allowed_after_d153_by_ai", "network_allowed_after_d153_by_ai",
    "secret_read_allowed_after_d153_by_ai", "shell_allowed_after_d153_by_ai",
    "git_action_allowed_after_d153_by_ai",
]

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]

def read_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def write_json(path, data):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def validate_d153(d153, audit_ledger, replay_index, d154_scope):
    errors = []
    if not d153:
        return ["missing D153 sandbox candidate final real apply audit scope report"]
    if d153.get("ok") is not True:
        errors.append("D153 ok must be true")
    if d153.get("decision") != REQ_D153_DECISION:
        errors.append("D153 decision must be SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_READY")

    s = d153.get("summary", {})
    expected = {
        "final_real_apply_audit_status": "FINAL_REAL_APPLY_AUDIT_LEDGER_CREATED_NO_AI_CORE_MUTATION",
        "replay_index_status": "REAL_APPLY_CHAIN_REPLAY_INDEX_CREATED_NO_EXECUTION",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE_ONLY",
        "next_step": REQ_D154_GATE,
    }
    for k, v in expected.items():
        if s.get(k) != v:
            errors.append(f"D153 summary.{k} must be {v}")

    for src_name, src in [("D153 guardrails", d153.get("guardrails", {})), ("D153 audit ledger", audit_ledger or {}), ("D153 replay index", replay_index or {})]:
        for k in FALSE_KEYS:
            if k in src and src.get(k) is not False:
                errors.append(f"{src_name} {k} must be false")

    for k in STATUS_FALSE_D153:
        if d153.get("guardrails", {}).get(k) is not False:
            errors.append(f"D153 guardrails.{k} must be false")

    if not audit_ledger:
        errors.append("missing D153 real apply audit ledger")
    else:
        if audit_ledger.get("ok") is not True:
            errors.append("D153 audit ledger ok must be true")
        if audit_ledger.get("ledger_mode") != "FINAL_REAL_APPLY_AUDIT_LEDGER_ONLY_NO_ACTION":
            errors.append("D153 audit ledger mode must be FINAL_REAL_APPLY_AUDIT_LEDGER_ONLY_NO_ACTION")
        if audit_ledger.get("audit_status") != "FINAL_REAL_APPLY_AUDIT_LEDGER_CREATED_NO_AI_CORE_MUTATION":
            errors.append("D153 audit status must show no AI core mutation")

    if not replay_index:
        errors.append("missing D153 real apply replay index")
    else:
        if replay_index.get("ok") is not True:
            errors.append("D153 replay index ok must be true")
        if replay_index.get("replay_index_mode") != "REAL_APPLY_REPLAY_INDEX_ONLY_NO_EXECUTION":
            errors.append("D153 replay index mode must be no-execution")
        if replay_index.get("replay_status") != "REAL_APPLY_CHAIN_REPLAY_INDEX_CREATED_NO_EXECUTION":
            errors.append("D153 replay status must be no-execution")
        if replay_index.get("replay_executes_anything") is not False:
            errors.append("D153 replay index replay_executes_anything must be false")

    if not d154_scope:
        errors.append("missing D153 D154 real apply chain archive scope")
    else:
        if d154_scope.get("ok") is not True:
            errors.append("D153 D154 scope ok must be true")
        if d154_scope.get("allowed_next_gate") != REQ_D154_GATE:
            errors.append("D153 D154 scope allowed_next_gate must be D154")
        if d154_scope.get("sandbox_candidate_real_apply_chain_archive_scope_only") is not True:
            errors.append("D153 D154 scope must be real-apply-chain-archive-only")
        for k in STATUS_FALSE_D153:
            if d154_scope.get(k) is not False:
                errors.append(f"D153 D154 scope {k} must be false")
    return errors

def build_archive_manifest(archive2_id, d153):
    return {
        "state": "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_MANIFEST",
        "ok": True,
        "archive2_id": archive2_id,
        "audit_id": d153.get("audit_id"),
        "verification_id": d153.get("verification_id"),
        "run_apply_id": d153.get("run_apply_id"),
        "candidate_id": d153.get("candidate_id"),
        "proposal_id": d153.get("proposal_id"),
        "created_at": now(),
        "archive_mode": "real-apply-chain-archive-manifest-only",
        "archive_status": "REAL_APPLY_CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
        "archived_without_real_apply_again": True,
        "archive_upload_performed": False,
        "archive_compression_performed": False,
        "archive_contains": [
            "D147 promotion decision", "D148 human real apply intent",
            "D149 guarded real apply preflight", "D150 human signed execution scope",
            "D151 guarded real apply run scope", "D152 post real apply verification",
            "D153 final real apply audit",
        ],
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "route_inserted_by_ai": False,
        "protected_core_mutated": False,
        "protected_core_mutated_by_ai": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }

def build_closure_receipt(archive2_id, d153):
    return {
        "state": "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_CLOSURE_RECEIPT",
        "ok": True,
        "archive2_id": archive2_id,
        "audit_id": d153.get("audit_id"),
        "verification_id": d153.get("verification_id"),
        "run_apply_id": d153.get("run_apply_id"),
        "candidate_id": d153.get("candidate_id"),
        "proposal_id": d153.get("proposal_id"),
        "created_at": now(),
        "closure_mode": "REAL_APPLY_CHAIN_CLOSURE_RECEIPT_ONLY_NO_ACTION",
        "closure_status": "REAL_APPLY_CHAIN_ARCHIVED_READY_FOR_GUARDED_AUTONOMY_CYCLE_CLOSURE",
        "chain_closed_for_ai_execution": True,
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
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }

def build_d155_scope(archive2_id, d153):
    return {
        "state": "D154_D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE",
        "ok": True,
        "archive2_id": archive2_id,
        "audit_id": d153.get("audit_id"),
        "verification_id": d153.get("verification_id"),
        "run_apply_id": d153.get("run_apply_id"),
        "candidate_id": d153.get("candidate_id"),
        "proposal_id": d153.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D155_GATE,
        "sandbox_candidate_guarded_autonomy_cycle_closure_scope_only": True,
        "human_review_required": True,
        "d155_allowed_to_create": [
            "guarded_autonomy_cycle_closure_scope",
            "guarded_autonomy_cycle_closure_report",
            "guarded_autonomy_cycle_replay_index",
            "d156_controlled_autonomy_next_cycle_intake_scope",
        ],
        "real_apply_allowed_after_d154_by_ai": False,
        "route_insert_allowed_after_d154_by_ai": False,
        "protected_core_mutation_allowed_after_d154_by_ai": False,
        "network_allowed_after_d154_by_ai": False,
        "secret_read_allowed_after_d154_by_ai": False,
        "shell_allowed_after_d154_by_ai": False,
        "git_action_allowed_after_d154_by_ai": False,
    }

def create_sandbox_candidate_real_apply_chain_archive_scope(root="."):
    root = Path(root).resolve()
    d153 = read_json(root / D153_REPORT, {}) or {}
    audit_ledger = read_json(root / D153_AUDIT_LEDGER, {}) or {}
    replay_index = read_json(root / D153_REPLAY_INDEX, {}) or {}
    d154_scope = read_json(root / D153_D154_SCOPE, {}) or {}

    errors = validate_d153(d153, audit_ledger, replay_index, d154_scope)
    archive2_id = "d154-" + digest({
        "audit_id": d153.get("audit_id"),
        "verification_id": d153.get("verification_id"),
        "run_apply_id": d153.get("run_apply_id"),
        "candidate_id": d153.get("candidate_id"),
        "proposal_id": d153.get("proposal_id"),
    })

    archive_manifest = build_archive_manifest(archive2_id, d153)
    closure_receipt = build_closure_receipt(archive2_id, d153)
    d155_scope = build_d155_scope(archive2_id, d153)

    for item_name, item in [("archive_manifest", archive_manifest), ("closure_receipt", closure_receipt), ("d155_scope", d155_scope)]:
        for k in [
            "actual_apply_executed_by_ai", "real_apply_executed_by_ai", "route_inserted",
            "route_inserted_by_ai", "protected_core_mutated", "protected_core_mutated_by_ai",
            "network_accessed", "secret_read", "shell_executed_by_ai", "git_action_by_ai",
            "real_apply_allowed_after_d154_by_ai", "route_insert_allowed_after_d154_by_ai",
            "protected_core_mutation_allowed_after_d154_by_ai", "network_allowed_after_d154_by_ai",
            "secret_read_allowed_after_d154_by_ai", "shell_allowed_after_d154_by_ai",
            "git_action_allowed_after_d154_by_ai",
        ]:
            if k in item and item.get(k) is not False:
                errors.append(f"{item_name} {k} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE_BLOCKED"
    result = "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE_CREATED" if ok else "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE_BLOCKED"

    if ok:
        write_json(root / ARCHIVE_MANIFEST_OUT, archive_manifest)
        write_json(root / CLOSURE_RECEIPT_OUT, closure_receipt)
        write_json(root / D155_SCOPE_OUT, d155_scope)

    report = {
        "state": "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "archive2_id": archive2_id,
        "audit_id": d153.get("audit_id"),
        "verification_id": d153.get("verification_id"),
        "run_apply_id": d153.get("run_apply_id"),
        "candidate_id": d153.get("candidate_id"),
        "proposal_id": d153.get("proposal_id"),
        "source_d153_report": D153_REPORT,
        "real_apply_chain_archive_manifest": archive_manifest if ok else {},
        "real_apply_chain_closure_receipt": closure_receipt if ok else {},
        "d155_scope": d155_scope if ok else {},
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
            "sandbox_candidate_real_apply_chain_archive_scope_only": True,
            "real_apply_chain_archive_manifest_only": True,
            "real_apply_chain_closure_receipt_only": True,
            "approval_for_d155_guarded_autonomy_cycle_closure_scope_only": ok,
            "real_apply_allowed_after_d154_by_ai": False,
            "route_insert_allowed_after_d154_by_ai": False,
            "protected_core_mutation_allowed_after_d154_by_ai": False,
            "network_allowed_after_d154_by_ai": False,
            "secret_read_allowed_after_d154_by_ai": False,
            "shell_allowed_after_d154_by_ai": False,
            "git_action_allowed_after_d154_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "archive2_id": archive2_id,
            "audit_id": d153.get("audit_id"),
            "verification_id": d153.get("verification_id"),
            "run_apply_id": d153.get("run_apply_id"),
            "candidate_id": d153.get("candidate_id"),
            "proposal_id": d153.get("proposal_id"),
            "real_apply_chain_archive_status": "REAL_APPLY_CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED" if ok else "BLOCKED",
            "chain_closure_status": "REAL_APPLY_CHAIN_ARCHIVED_READY_FOR_GUARDED_AUTONOMY_CYCLE_CLOSURE" if ok else "BLOCKED",
            "candidate_status": "REAL_APPLY_CHAIN_ARCHIVED_READY_FOR_GUARDED_AUTONOMY_CYCLE_CLOSURE_NOT_CORE_MUTATED_BY_AI" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D155_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "real_apply_chain_archive_scope_created": ok,
            "real_apply_chain_archive_manifest_created": ok,
            "real_apply_chain_closure_receipt_created": ok,
            "d155_scope_created": ok,
            "real_core_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
            "next_step": "D155 may create guarded autonomy cycle closure scope only.",
        },
    }
    write_json(root / OUT, report)
    return report

if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_real_apply_chain_archive_scope(), ensure_ascii=False, indent=2))
