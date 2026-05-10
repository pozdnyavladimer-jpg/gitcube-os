
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D144_REPORT = "reports/d144_sandbox_candidate_post_apply_verification_scope.json"
D144_POST_APPLY_REPORT = "reports/d144_sandbox_candidate_post_apply_verification_report.json"
D144_APPLY_INTEGRITY_RECEIPT = "reports/d144_sandbox_candidate_apply_integrity_receipt.json"
D144_D145_SCOPE = "reports/d144_d145_sandbox_candidate_final_audit_scope.json"

OUT = "reports/d145_sandbox_candidate_final_audit_scope.json"
FINAL_AUDIT_LEDGER_OUT = "reports/d145_sandbox_candidate_final_audit_ledger.json"
REPLAY_INDEX_OUT = "reports/d145_sandbox_candidate_replay_index.json"
D146_SCOPE_OUT = "reports/d145_d146_sandbox_candidate_archive_scope.json"

REQ_D144_DECISION = "SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_READY"
REQ_D145_GATE = "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE"
REQ_D146_GATE = "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE"
REQ_D144_APPROVAL_SCOPE = "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_ONLY"

FALSE_GUARD_KEYS = [
    "external_ai_called", "network_accessed", "api_key_read", "secret_read",
    "shell_from_ai_executed", "runtime_code_mutated", "protected_core_mutated",
    "canonical_memory_mutated", "actual_apply_executed", "route_inserted",
    "git_commit_by_ai", "git_push_by_ai", "rollback_executed", "restore_executed",
]

UNSAFE_BOOLEAN_KEYS = [
    "actual_apply_executed", "real_apply_executed", "real_core_apply_executed",
    "route_inserted", "protected_core_mutated", "canonical_memory_mutated",
    "runtime_code_mutated", "external_ai_called", "network_accessed", "api_key_read",
    "secret_read", "shell_from_ai_executed", "shell_executed_by_ai",
    "git_commit_by_ai", "git_push_by_ai", "git_action_by_ai", "rollback_executed",
    "restore_executed", "candidate_executed_now", "candidate_executed_by_ai",
    "candidate_reexecuted_now", "auto_apply_allowed", "real_apply_allowed_by_ai",
    "approved_for_real_apply_by_ai", "route_insert_allowed_by_ai",
    "protected_core_mutation_allowed_by_ai",
]

UNSAFE_STATUS_EXPECTED = {
    "real_provider_status": "NOT_CALLED",
    "network_status": "NOT_ACCESSED",
    "secret_status": "NOT_READ",
    "shell_status": "NOT_EXECUTED",
    "real_apply_by_ai_status": "BLOCKED",
    "route_insert_status": "BLOCKED",
    "protected_core_status": "UNTOUCHED_BY_AI",
}

BLOCKED_ACTIONS = [
    "real_apply_by_ai", "auto_apply_by_ai", "route_insert_by_ai",
    "protected_core_mutation_by_ai", "canonical_memory_overwrite_by_ai",
    "shell_exec_from_ai", "external_network_call_by_ai", "secret_read_by_ai",
    "git_commit_by_ai", "git_push_by_ai", "rollback_execute_by_ai",
    "restore_execute_by_ai", "candidate_reexecution_by_ai",
]

AUDIT_CHAIN_ARTIFACTS = [
    "reports/d126_sandbox_candidate_scope.json",
    "reports/d127_sandbox_candidate_human_review_scope.json",
    "reports/d128_sandbox_candidate_test_plan_scope.json",
    "reports/d129_sandbox_candidate_dry_test_runner_scope.json",
    "reports/d130_sandbox_candidate_write_window_scope.json",
    "reports/d131_sandbox_candidate_write_once_scope.json",
    "reports/d132_sandbox_candidate_static_validation_scope.json",
    "reports/d133_sandbox_candidate_materialization_scope.json",
    "reports/d134_sandbox_candidate_write_materialization_scope.json",
    "reports/d135_sandbox_candidate_post_write_validation_scope.json",
    "reports/d136_sandbox_candidate_execution_preflight_scope.json",
    "reports/d137_sandbox_candidate_controlled_execution_scope.json",
    "reports/d138_sandbox_candidate_human_execution_intent_scope.json",
    "reports/d139_sandbox_candidate_controlled_execution_run_scope.json",
    "reports/d140_sandbox_candidate_post_execution_verification_scope.json",
    "reports/d141_sandbox_candidate_apply_preflight_scope.json",
    "reports/d142_sandbox_candidate_human_apply_intent_scope.json",
    "reports/d143_sandbox_candidate_guarded_apply_scope.json",
    "reports/d144_sandbox_candidate_post_apply_verification_scope.json",
]

REQUIRED_CANDIDATE_FILES = [
    "candidate_manifest.json",
    "candidate_payload.json",
    "candidate_summary.md",
    "sandbox_execution_result.json",
    "sandbox_apply_result.json",
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


def candidate_dir(root, candidate_id):
    if not candidate_id:
        return None
    return root / "runtime_experimental" / "ai_sandbox_work" / candidate_id


def check_false_map(name, obj, errors):
    if not isinstance(obj, dict):
        return
    for key in UNSAFE_BOOLEAN_KEYS:
        if key in obj and obj.get(key) is not False:
            errors.append(f"{name} {key} must be false")


def check_statuses(name, obj, errors):
    if not isinstance(obj, dict):
        return
    for key, value in UNSAFE_STATUS_EXPECTED.items():
        if key in obj and obj.get(key) != value:
            errors.append(f"{name} {key} must be {value}")


def file_digest(path):
    p = Path(path)
    if not p.exists():
        return None
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except Exception:
        return None


def validate_candidate_files(root, candidate_id, errors):
    cdir = candidate_dir(root, candidate_id)
    if cdir is None:
        errors.append("missing candidate_id")
        return None
    if not cdir.exists():
        errors.append(f"missing sandbox candidate directory: {cdir}")
        return cdir
    for name in REQUIRED_CANDIDATE_FILES:
        if not (cdir / name).exists():
            errors.append(f"missing sandbox candidate file: {name}")
    return cdir


def validate_d144(root, d144, post_apply_report, integrity_receipt, d145_scope):
    errors = []
    if not d144:
        return ["missing D144 sandbox candidate post apply verification scope report"]

    if d144.get("ok") is not True:
        errors.append("D144 ok must be true")
    if d144.get("decision") != REQ_D144_DECISION:
        errors.append("D144 decision must be SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_READY")

    summary = d144.get("summary", {})
    expected = {
        "post_apply_verification_status": "SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION",
        "sandbox_apply_integrity_status": "SANDBOX_APPLY_EVIDENCE_PRESENT_AND_VALIDATED",
        "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_NOT_CORE_APPLIED",
        "approval_scope": REQ_D144_APPROVAL_SCOPE,
        "next_step": REQ_D145_GATE,
    }
    expected.update(UNSAFE_STATUS_EXPECTED)
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D144 summary.{key} must be {value}")

    guard = d144.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D144 guardrails.{key} must be false")
    for key in [
        "sandbox_candidate_post_apply_verification_scope_only",
        "post_apply_verification_report_only",
        "apply_integrity_receipt_only",
        "approval_for_d145_final_audit_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D144 guardrails.{key} must be true")
    for key in [
        "candidate_executed_now", "approval_for_real_apply_by_ai",
        "approval_for_route_insert_by_ai", "approval_for_protected_core_mutation_by_ai",
        "candidate_execution_allowed_by_ai", "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D144 guardrails.{key} must be false")

    candidate_id = d144.get("candidate_id") or summary.get("candidate_id")
    cdir = validate_candidate_files(root, candidate_id, errors)

    if not post_apply_report:
        errors.append("missing D144 sandbox candidate post apply verification report")
    else:
        if post_apply_report.get("ok") is not True:
            errors.append("D144 post apply report ok must be true")
        if post_apply_report.get("report_mode") != "POST_SANDBOX_APPLY_VERIFICATION_ONLY_NO_CORE_MUTATION":
            errors.append("D144 post apply report mode must be post verification only/no core mutation")
        if post_apply_report.get("post_apply_verification_status") != "SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION":
            errors.append("D144 post apply verification status must be SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION")
        if post_apply_report.get("candidate_status") != "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_NOT_CORE_APPLIED":
            errors.append("D144 post apply report candidate_status must be verified not core applied")
        if post_apply_report.get("human_review_required") is not True:
            errors.append("D144 post apply report must require human review")
        check_false_map("D144 post apply report", post_apply_report, errors)

    if not integrity_receipt:
        errors.append("missing D144 sandbox candidate apply integrity receipt")
    else:
        if integrity_receipt.get("ok") is not True:
            errors.append("D144 apply integrity receipt ok must be true")
        if integrity_receipt.get("receipt_mode") != "SANDBOX_APPLY_INTEGRITY_RECEIPT_NO_CORE_MUTATION":
            errors.append("D144 apply integrity receipt mode must be no core mutation")
        if integrity_receipt.get("sandbox_apply_integrity_status") != "SANDBOX_APPLY_EVIDENCE_PRESENT_AND_VALIDATED":
            errors.append("D144 apply integrity status must be evidence present and validated")
        if integrity_receipt.get("protected_core_status") != "UNTOUCHED_BY_AI":
            errors.append("D144 apply integrity protected_core_status must be UNTOUCHED_BY_AI")
        if integrity_receipt.get("route_insert_status") != "BLOCKED":
            errors.append("D144 apply integrity route_insert_status must be BLOCKED")
        if integrity_receipt.get("candidate_files_all_present") is not True:
            errors.append("D144 apply integrity candidate_files_all_present must be true")
        if integrity_receipt.get("human_review_required") is not True:
            errors.append("D144 apply integrity receipt must require human review")
        check_false_map("D144 apply integrity receipt", integrity_receipt, errors)

    if not d145_scope:
        errors.append("missing D144 D145 final audit scope")
    else:
        if d145_scope.get("ok") is not True:
            errors.append("D144 D145 scope ok must be true")
        if d145_scope.get("allowed_next_gate") != REQ_D145_GATE:
            errors.append("D144 D145 scope allowed_next_gate must be D145")
        if d145_scope.get("sandbox_candidate_final_audit_scope_only") is not True:
            errors.append("D144 D145 scope must be final audit scope only")
        if d145_scope.get("sandbox_apply_verified_after_d144") is not True:
            errors.append("D144 D145 scope sandbox_apply_verified_after_d144 must be true")
        if d145_scope.get("human_review_required") is not True:
            errors.append("D144 D145 scope must require human review")
        for key in [
            "candidate_executed_after_d144_by_ai", "real_apply_allowed_after_d144_by_ai",
            "auto_apply_allowed_after_d144_by_ai", "route_insert_allowed_after_d144_by_ai",
            "protected_core_mutation_allowed_after_d144_by_ai", "network_allowed_after_d144_by_ai",
            "secret_read_allowed_after_d144_by_ai", "shell_allowed_after_d144_by_ai",
            "git_action_allowed_after_d144_by_ai",
        ]:
            if d145_scope.get(key) is not False:
                errors.append(f"D144 D145 scope {key} must be false")

    return errors


def build_final_audit_ledger(root, audit_id, d144, post_apply_report, integrity_receipt):
    summary = d144.get("summary", {})
    candidate_id = d144.get("candidate_id") or summary.get("candidate_id")
    artifact_entries = []
    for item in AUDIT_CHAIN_ARTIFACTS:
        p = root / item
        artifact_entries.append({
            "path": item,
            "present": p.exists(),
            "digest16": file_digest(p),
        })
    return {
        "state": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_LEDGER",
        "ok": True,
        "audit_id": audit_id,
        "verification_id": d144.get("verification_id") or summary.get("verification_id"),
        "apply_id": d144.get("apply_id") or summary.get("apply_id"),
        "run_id": d144.get("run_id") or summary.get("run_id"),
        "candidate_id": candidate_id,
        "proposal_id": d144.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "ledger_mode": "FINAL_AUDIT_LEDGER_ONLY_NO_EXECUTION_NO_CORE_MUTATION",
        "audited_range": "D126_D145_SANDBOX_CANDIDATE_CHAIN",
        "artifact_entries": artifact_entries,
        "artifacts_present_count": sum(1 for x in artifact_entries if x["present"]),
        "artifacts_total": len(artifact_entries),
        "post_apply_verification_status": post_apply_report.get("post_apply_verification_status"),
        "sandbox_apply_integrity_status": integrity_receipt.get("sandbox_apply_integrity_status"),
        "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_FINAL_AUDIT_READY_NOT_CORE_APPLIED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "shell_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "actual_apply_executed": False,
        "real_apply_executed": False,
        "real_core_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "shell_from_ai_executed": False,
        "shell_executed_by_ai": False,
        "git_commit_by_ai": False,
        "git_push_by_ai": False,
        "git_action_by_ai": False,
        "candidate_executed_now": False,
        "candidate_executed_by_ai": False,
        "human_review_required": True,
    }


def build_replay_index(root, audit_id, d144):
    summary = d144.get("summary", {})
    candidate_id = d144.get("candidate_id") or summary.get("candidate_id")
    cdir = candidate_dir(root, candidate_id)
    replay_files = []
    for name in REQUIRED_CANDIDATE_FILES:
        p = cdir / name if cdir else None
        replay_files.append({
            "path": str(Path("runtime_experimental/ai_sandbox_work") / candidate_id / name) if candidate_id else name,
            "present": p.exists() if p else False,
            "digest16": file_digest(p) if p else None,
        })
    return {
        "state": "D145_SANDBOX_CANDIDATE_REPLAY_INDEX",
        "ok": True,
        "audit_id": audit_id,
        "verification_id": d144.get("verification_id") or summary.get("verification_id"),
        "apply_id": d144.get("apply_id") or summary.get("apply_id"),
        "run_id": d144.get("run_id") or summary.get("run_id"),
        "candidate_id": candidate_id,
        "proposal_id": d144.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "replay_mode": "REPLAY_INDEX_ONLY_NO_EXECUTION",
        "replay_order": [
            "candidate_manifest.json",
            "candidate_payload.json",
            "sandbox_execution_result.json",
            "sandbox_apply_result.json",
            "d139_execution_scope_report",
            "d140_post_execution_verification_report",
            "d143_guarded_apply_report",
            "d144_post_apply_verification_report",
        ],
        "candidate_replay_files": replay_files,
        "candidate_replay_files_all_present": bool(replay_files) and all(x["present"] for x in replay_files),
        "replay_status": "INDEX_CREATED_NOT_REPLAYED",
        "actual_replay_executed": False,
        "actual_apply_executed": False,
        "real_core_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "network_accessed": False,
        "secret_read": False,
        "shell_from_ai_executed": False,
        "shell_executed_by_ai": False,
        "git_commit_by_ai": False,
        "git_push_by_ai": False,
        "git_action_by_ai": False,
        "candidate_executed_now": False,
        "candidate_executed_by_ai": False,
        "human_review_required": True,
    }


def build_d146_scope(audit_id, d144):
    summary = d144.get("summary", {})
    return {
        "state": "D145_D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE",
        "ok": True,
        "audit_id": audit_id,
        "verification_id": d144.get("verification_id") or summary.get("verification_id"),
        "apply_id": d144.get("apply_id") or summary.get("apply_id"),
        "run_id": d144.get("run_id") or summary.get("run_id"),
        "candidate_id": d144.get("candidate_id") or summary.get("candidate_id"),
        "proposal_id": d144.get("proposal_id") or summary.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D146_GATE,
        "d146_allowed_to_create": [
            "sandbox_candidate_archive_scope",
            "sandbox_candidate_archive_manifest",
            "sandbox_candidate_archive_receipt",
            "d147_sandbox_candidate_chain_closeout_scope",
        ],
        "d146_must_not_execute": BLOCKED_ACTIONS,
        "sandbox_candidate_archive_scope_only": True,
        "human_review_required": True,
        "final_audit_created_after_d145": True,
        "candidate_executed_after_d145_by_ai": False,
        "real_apply_allowed_after_d145_by_ai": False,
        "auto_apply_allowed_after_d145_by_ai": False,
        "route_insert_allowed_after_d145_by_ai": False,
        "protected_core_mutation_allowed_after_d145_by_ai": False,
        "network_allowed_after_d145_by_ai": False,
        "secret_read_allowed_after_d145_by_ai": False,
        "shell_allowed_after_d145_by_ai": False,
        "git_action_allowed_after_d145_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_ONLY",
    }


def create_sandbox_candidate_final_audit_scope(root="."):
    root = Path(root).resolve()
    d144 = read_json(root / D144_REPORT, {}) or {}
    post_apply_report = read_json(root / D144_POST_APPLY_REPORT, {}) or {}
    integrity_receipt = read_json(root / D144_APPLY_INTEGRITY_RECEIPT, {}) or {}
    d145_scope_in = read_json(root / D144_D145_SCOPE, {}) or {}

    errors = validate_d144(root, d144, post_apply_report, integrity_receipt, d145_scope_in)
    summary = d144.get("summary", {})
    candidate_id = d144.get("candidate_id") or summary.get("candidate_id")

    audit_id = "d145-" + digest({
        "verification_id": d144.get("verification_id") or summary.get("verification_id"),
        "apply_id": d144.get("apply_id") or summary.get("apply_id"),
        "candidate_id": candidate_id,
        "proposal_id": d144.get("proposal_id") or summary.get("proposal_id"),
    })

    final_audit_ledger = build_final_audit_ledger(root, audit_id, d144, post_apply_report, integrity_receipt)
    replay_index = build_replay_index(root, audit_id, d144)
    d146_scope = build_d146_scope(audit_id, d144)

    for item_name, item in [("final_audit_ledger", final_audit_ledger), ("replay_index", replay_index)]:
        check_false_map(item_name, item, errors)
        check_statuses(item_name, item, errors)
    if replay_index.get("candidate_replay_files_all_present") is not True:
        errors.append("replay_index candidate_replay_files_all_present must be true")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_BLOCKED"
    result = "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_CREATED" if ok else "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_BLOCKED"

    if ok:
        write_json(root / FINAL_AUDIT_LEDGER_OUT, final_audit_ledger)
        write_json(root / REPLAY_INDEX_OUT, replay_index)
        write_json(root / D146_SCOPE_OUT, d146_scope)

    report = {
        "state": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "audit_id": audit_id,
        "verification_id": d144.get("verification_id") or summary.get("verification_id"),
        "apply_id": d144.get("apply_id") or summary.get("apply_id"),
        "run_id": d144.get("run_id") or summary.get("run_id"),
        "candidate_id": candidate_id,
        "proposal_id": d144.get("proposal_id") or summary.get("proposal_id"),
        "source_d144_report": D144_REPORT,
        "sandbox_candidate_final_audit_ledger": final_audit_ledger if ok else {},
        "sandbox_candidate_replay_index": replay_index if ok else {},
        "d146_scope": d146_scope if ok else {},
        "guardrails": {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False, "secret_read": False,
            "shell_from_ai_executed": False, "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False, "route_inserted": False,
            "git_commit_by_ai": False, "git_push_by_ai": False, "rollback_executed": False, "restore_executed": False,
            "sandbox_candidate_final_audit_scope_only": True,
            "final_audit_ledger_only": True,
            "replay_index_only": True,
            "candidate_executed_now": False,
            "approval_for_d146_archive_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "approval_for_route_insert_by_ai": False,
            "approval_for_protected_core_mutation_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "audit_id": audit_id,
            "verification_id": d144.get("verification_id") or summary.get("verification_id"),
            "apply_id": d144.get("apply_id") or summary.get("apply_id"),
            "run_id": d144.get("run_id") or summary.get("run_id"),
            "candidate_id": candidate_id,
            "proposal_id": d144.get("proposal_id") or summary.get("proposal_id"),
            "final_audit_status": "FINAL_AUDIT_LEDGER_CREATED" if ok else "BLOCKED",
            "replay_index_status": "INDEX_CREATED_NOT_REPLAYED" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_FINAL_AUDIT_READY_NOT_CORE_APPLIED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D146_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_final_audit_scope_created": ok,
            "sandbox_candidate_final_audit_ledger_created": ok,
            "sandbox_candidate_replay_index_created": ok,
            "d146_scope_created": ok,
            "final_audit_ready": ok,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "real_core_apply_executed": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D146 may create archive scope only.",
        },
    }
    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_final_audit_scope(), ensure_ascii=False, indent=2))
