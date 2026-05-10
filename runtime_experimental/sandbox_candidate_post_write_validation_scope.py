
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D134_REPORT = "reports/d134_sandbox_candidate_write_materialization_scope.json"
D134_WRITE_RECEIPT = "reports/d134_sandbox_candidate_write_materialization_receipt.json"
D134_WRITE_POSTCHECK = "reports/d134_sandbox_candidate_write_materialization_postcheck.json"
D134_D135_SCOPE = "reports/d134_d135_sandbox_candidate_post_write_validation_scope.json"

OUT = "reports/d135_sandbox_candidate_post_write_validation_scope.json"
VALIDATION_OUT = "reports/d135_sandbox_candidate_post_write_validation_report.json"
INVENTORY_OUT = "reports/d135_sandbox_candidate_materialized_file_inventory.json"
D136_SCOPE_OUT = "reports/d135_d136_sandbox_candidate_execution_preflight_scope.json"

REQ_D134_DECISION = "SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_READY"
REQ_D135_GATE = "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE"
REQ_D136_GATE = "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE"
REQ_D134_APPROVAL_SCOPE = "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_ONLY"

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

EXPECTED_CANDIDATE_FILENAMES = [
    "candidate_manifest.json",
    "candidate_summary.md",
    "candidate_payload.json",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def text_digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def read_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_text(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return default


def write_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_safe_candidate_root(root_value):
    return (
        isinstance(root_value, str)
        and root_value.startswith("runtime_experimental/ai_sandbox_work/")
        and root_value.endswith("/")
        and ".." not in root_value
        and not root_value.startswith("/")
    )


def is_safe_candidate_path(path_value, root_value):
    return (
        isinstance(path_value, str)
        and isinstance(root_value, str)
        and path_value.startswith(root_value)
        and ".." not in path_value
        and not path_value.startswith("/")
        and not path_value.endswith("/")
    )


def expected_candidate_paths(root_value):
    return [f"{root_value}{name}" for name in EXPECTED_CANDIDATE_FILENAMES]


def validate_d134(d134, write_receipt, write_postcheck, d135_scope):
    errors = []

    if not d134:
        errors.append("missing D134 sandbox candidate write materialization scope report")
        return errors

    if d134.get("ok") is not True:
        errors.append("D134 ok must be true")
    if d134.get("decision") != REQ_D134_DECISION:
        errors.append("D134 decision must be SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_READY")

    guard = d134.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D134 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_write_materialization_scope_only",
        "write_materialization_receipt_only",
        "write_materialization_postcheck_only",
        "candidate_files_materialized",
        "approval_for_d135_post_write_validation_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D134 guardrails.{key} must be true")

    for key in [
        "candidate_executed_now",
        "approval_for_candidate_execution",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D134 guardrails.{key} must be false")

    summary = d134.get("summary", {})
    expected = {
        "candidate_status": "MATERIALIZED_NOT_EXECUTED_NOT_APPLIED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": REQ_D134_APPROVAL_SCOPE,
        "next_step": REQ_D135_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D134 summary.{key} must be {value}")
    if summary.get("write_materialization_status") not in [
        "CANDIDATE_FILES_MATERIALIZED",
        "CANDIDATE_FILES_ALREADY_MATERIALIZED_VERIFIED",
    ]:
        errors.append("D134 write_materialization_status must confirm candidate files materialized")

    if not write_receipt:
        errors.append("missing D134 sandbox candidate write materialization receipt")
    else:
        if write_receipt.get("ok") is not True:
            errors.append("D134 write receipt ok must be true")
        if write_receipt.get("receipt_mode") != "SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_RECEIPT_ONLY":
            errors.append("D134 write receipt mode must be receipt-only")
        root_value = write_receipt.get("allowed_candidate_write_root")
        if not is_safe_candidate_root(root_value):
            errors.append("D134 write receipt candidate root must be safe")
        expected_paths = expected_candidate_paths(root_value) if is_safe_candidate_root(root_value) else []
        if sorted(write_receipt.get("candidate_files_expected", [])) != sorted(expected_paths):
            errors.append("D134 write receipt must contain exactly expected candidate files")
        if write_receipt.get("candidate_files_materialized") is not True:
            errors.append("D134 write receipt must confirm candidate files materialized")
        if write_receipt.get("candidate_files_blocked_existing_paths", []):
            errors.append("D134 write receipt must not contain blocked existing paths")
        for key in [
            "candidate_executed_now",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "network_accessed",
            "api_key_read",
            "secret_read",
        ]:
            if write_receipt.get(key) is not False:
                errors.append(f"D134 write receipt {key} must be false")

    if not write_postcheck:
        errors.append("missing D134 sandbox candidate write materialization postcheck")
    else:
        if write_postcheck.get("ok") is not True:
            errors.append("D134 write postcheck ok must be true")
        if write_postcheck.get("postcheck_mode") != "SANDBOX_CANDIDATE_WRITE_POSTCHECK_NO_EXECUTION_NO_APPLY":
            errors.append("D134 write postcheck mode must be no-execution-no-apply")
        root_value = write_postcheck.get("allowed_candidate_write_root")
        if not is_safe_candidate_root(root_value):
            errors.append("D134 write postcheck candidate root must be safe")
        expected_paths = expected_candidate_paths(root_value) if is_safe_candidate_root(root_value) else []
        if sorted(write_postcheck.get("candidate_files_existing", [])) != sorted(expected_paths):
            errors.append("D134 write postcheck must list exactly expected candidate files")
        if write_postcheck.get("candidate_files_missing", []):
            errors.append("D134 write postcheck must not have missing candidate files")
        for path, ok in write_postcheck.get("candidate_file_digest_matches", {}).items():
            if ok is not True:
                errors.append(f"D134 write postcheck digest mismatch: {path}")
        if write_postcheck.get("candidate_files_materialized") is not True:
            errors.append("D134 write postcheck must confirm candidate files materialized")
        for key in [
            "candidate_executed_now",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "network_accessed",
            "api_key_read",
            "secret_read",
        ]:
            if write_postcheck.get(key) is not False:
                errors.append(f"D134 write postcheck {key} must be false")

    if not d135_scope:
        errors.append("missing D134 D135 sandbox candidate post-write validation scope")
    else:
        if d135_scope.get("ok") is not True:
            errors.append("D134 D135 scope ok must be true")
        if d135_scope.get("allowed_next_gate") != REQ_D135_GATE:
            errors.append("D134 D135 scope allowed_next_gate must be D135")
        if d135_scope.get("sandbox_candidate_post_write_validation_scope_only") is not True:
            errors.append("D134 D135 scope must be post-write validation scope only")
        if d135_scope.get("human_review_required") is not True:
            errors.append("D134 D135 scope must require human review")
        for key in [
            "candidate_executed_after_d134_by_ai",
            "real_apply_allowed_after_d134_by_ai",
            "route_insert_allowed_after_d134_by_ai",
            "protected_core_mutation_allowed_after_d134_by_ai",
        ]:
            if d135_scope.get(key) is not False:
                errors.append(f"D134 D135 scope {key} must be false")

    return errors


def build_inventory(root, validation_id, d134, write_receipt):
    root_value = write_receipt.get("allowed_candidate_write_root")
    expected_paths = expected_candidate_paths(root_value) if is_safe_candidate_root(root_value) else []
    files = []
    missing = []
    for rel_path in expected_paths:
        p = root / rel_path
        if not p.exists():
            missing.append(rel_path)
            continue
        text = p.read_text(encoding="utf-8")
        parsed_json = None
        json_ok = None
        if rel_path.endswith(".json"):
            try:
                parsed_json = json.loads(text)
                json_ok = True
            except Exception:
                json_ok = False
        files.append({
            "path": rel_path,
            "size_bytes": len(text.encode("utf-8")),
            "sha256_16": text_digest(text),
            "json_ok": json_ok,
            "state": parsed_json.get("state") if isinstance(parsed_json, dict) else None,
            "ok": parsed_json.get("ok") if isinstance(parsed_json, dict) else None,
        })

    return {
        "state": "D135_SANDBOX_CANDIDATE_MATERIALIZED_FILE_INVENTORY",
        "ok": not missing and len(files) == len(expected_paths),
        "validation_id": validation_id,
        "write_materialization_id": d134.get("write_materialization_id"),
        "candidate_id": d134.get("candidate_id"),
        "proposal_id": d134.get("proposal_id"),
        "created_at": now(),
        "inventory_mode": "READ_ONLY_MATERIALIZED_FILE_INVENTORY_NO_EXECUTION",
        "allowed_candidate_write_root": root_value,
        "expected_files": expected_paths,
        "files": files,
        "missing_files": missing,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "human_review_required": True,
    }


def build_validation_report(root, validation_id, d134, write_receipt, write_postcheck, inventory):
    root_value = write_receipt.get("allowed_candidate_write_root")
    manifest_path = root / f"{root_value}candidate_manifest.json"
    payload_path = root / f"{root_value}candidate_payload.json"
    summary_path = root / f"{root_value}candidate_summary.md"

    manifest = read_json(manifest_path, {}) or {}
    payload = read_json(payload_path, {}) or {}
    summary_text = read_text(summary_path, "") or ""

    expected_paths = expected_candidate_paths(root_value) if is_safe_candidate_root(root_value) else []
    all_paths_safe = all(is_safe_candidate_path(path, root_value) for path in expected_paths)
    receipt_paths = sorted(write_receipt.get("candidate_files_expected", [])) == sorted(expected_paths)
    postcheck_paths = sorted(write_postcheck.get("candidate_files_existing", [])) == sorted(expected_paths)
    digest_matches = all(write_postcheck.get("candidate_file_digest_matches", {}).values())

    manifest_guard = manifest.get("guardrails", {}) if isinstance(manifest, dict) else {}
    manifest_guard_ok = True
    for key in [
        "candidate_executed",
        "actual_apply_executed",
        "route_inserted",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "shell_executed_by_ai",
        "git_action_by_ai",
        "network_accessed",
        "api_key_read",
        "secret_read",
    ]:
        if manifest_guard.get(key) is not False:
            manifest_guard_ok = False

    checks = {
        "candidate_root_safe": is_safe_candidate_root(root_value),
        "expected_files_present": inventory.get("ok") is True,
        "all_paths_under_candidate_root": all_paths_safe,
        "receipt_paths_match_expected": receipt_paths,
        "postcheck_paths_match_expected": postcheck_paths,
        "postcheck_digest_matches": digest_matches,
        "manifest_json_ok": manifest.get("ok") is True,
        "manifest_status_ok": manifest.get("candidate_status") == "MATERIALIZED_NOT_EXECUTED_NOT_APPLIED",
        "manifest_guardrails_hold": manifest_guard_ok,
        "payload_json_ok": payload.get("ok") is True,
        "payload_mode_safe": payload.get("payload_mode") == "SAFE_SANDBOX_CANDIDATE_PLACEHOLDER_NO_EXECUTION",
        "payload_execution_not_executed": payload.get("execution_mode") == "NOT_EXECUTED",
        "payload_apply_not_applied": payload.get("apply_mode") == "NOT_APPLIED",
        "payload_route_insert_blocked": payload.get("route_insert_mode") == "BLOCKED",
        "payload_protected_core_untouched": payload.get("protected_core_mode") == "UNTOUCHED_BY_AI",
        "summary_file_present": bool(summary_text.strip()),
        "summary_declares_no_execution": "no candidate execution" in summary_text,
        "summary_declares_no_apply": "no real apply" in summary_text,
        "next_gate_confirmed": payload.get("next_required_gate") == REQ_D135_GATE,
    }

    ok = all(checks.values())
    return {
        "state": "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_REPORT",
        "ok": ok,
        "validation_id": validation_id,
        "write_materialization_id": d134.get("write_materialization_id"),
        "materialization_id": d134.get("materialization_id"),
        "static_validation_id": d134.get("static_validation_id"),
        "write_once_id": d134.get("write_once_id"),
        "window_id": d134.get("window_id"),
        "runner_id": d134.get("runner_id"),
        "plan_id": d134.get("plan_id"),
        "review_id": d134.get("review_id"),
        "candidate_id": d134.get("candidate_id"),
        "proposal_id": d134.get("proposal_id"),
        "created_at": now(),
        "validation_mode": "POST_WRITE_VALIDATION_ONLY_NO_EXECUTION_NO_APPLY",
        "allowed_candidate_write_root": root_value,
        "checks": checks,
        "candidate_status": "MATERIALIZED_NOT_EXECUTED_NOT_APPLIED" if ok else "POST_WRITE_VALIDATION_BLOCKED",
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "human_review_required": True,
    }


def build_d136_scope(validation_id, d134):
    return {
        "state": "D135_D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE",
        "ok": True,
        "validation_id": validation_id,
        "write_materialization_id": d134.get("write_materialization_id"),
        "materialization_id": d134.get("materialization_id"),
        "static_validation_id": d134.get("static_validation_id"),
        "write_once_id": d134.get("write_once_id"),
        "window_id": d134.get("window_id"),
        "runner_id": d134.get("runner_id"),
        "plan_id": d134.get("plan_id"),
        "review_id": d134.get("review_id"),
        "candidate_id": d134.get("candidate_id"),
        "intake_id": d134.get("intake_id"),
        "ping_id": d134.get("ping_id"),
        "config_id": d134.get("config_id"),
        "dashboard_id": d134.get("dashboard_id"),
        "adapter_id": d134.get("adapter_id"),
        "seal_id": d134.get("seal_id"),
        "proposal_id": d134.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D136_GATE,
        "d136_allowed_to_create": [
            "sandbox_candidate_execution_preflight_scope",
            "sandbox_candidate_execution_preflight_report",
            "sandbox_candidate_execution_command_packet",
            "d137_sandbox_candidate_controlled_execution_scope",
        ],
        "d136_must_not_execute": [
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
        "sandbox_candidate_execution_preflight_scope_only": True,
        "human_review_required": True,
        "candidate_executed_after_d135_by_ai": False,
        "real_apply_allowed_after_d135_by_ai": False,
        "route_insert_allowed_after_d135_by_ai": False,
        "protected_core_mutation_allowed_after_d135_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_ONLY",
    }


def create_sandbox_candidate_post_write_validation_scope(root="."):
    root = Path(root).resolve()

    d134 = read_json(root / D134_REPORT, {}) or {}
    write_receipt = read_json(root / D134_WRITE_RECEIPT, {}) or {}
    write_postcheck = read_json(root / D134_WRITE_POSTCHECK, {}) or {}
    d135_scope_in = read_json(root / D134_D135_SCOPE, {}) or {}

    errors = validate_d134(d134, write_receipt, write_postcheck, d135_scope_in)

    validation_id = "d135-" + digest({
        "write_materialization_id": d134.get("write_materialization_id"),
        "materialization_id": d134.get("materialization_id"),
        "static_validation_id": d134.get("static_validation_id"),
        "write_once_id": d134.get("write_once_id"),
        "candidate_id": d134.get("candidate_id"),
        "proposal_id": d134.get("proposal_id"),
    })

    inventory = build_inventory(root, validation_id, d134, write_receipt)
    validation_report = build_validation_report(root, validation_id, d134, write_receipt, write_postcheck, inventory)
    d136_scope = build_d136_scope(validation_id, d134)

    if inventory.get("ok") is not True:
        errors.append("materialized file inventory must be ok")
    if validation_report.get("ok") is not True:
        errors.append("post-write validation report must be ok")

    for item_name, item in [("inventory", inventory), ("validation_report", validation_report)]:
        for key in [
            "candidate_executed_now",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "network_accessed",
            "api_key_read",
            "secret_read",
        ]:
            if item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_BLOCKED"
    result = "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_CREATED" if ok else "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_BLOCKED"

    if ok:
        write_json(root / VALIDATION_OUT, validation_report)
        write_json(root / INVENTORY_OUT, inventory)
        write_json(root / D136_SCOPE_OUT, d136_scope)

    report = {
        "state": "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "validation_id": validation_id,
        "write_materialization_id": d134.get("write_materialization_id"),
        "materialization_id": d134.get("materialization_id"),
        "static_validation_id": d134.get("static_validation_id"),
        "write_once_id": d134.get("write_once_id"),
        "window_id": d134.get("window_id"),
        "runner_id": d134.get("runner_id"),
        "plan_id": d134.get("plan_id"),
        "review_id": d134.get("review_id"),
        "candidate_id": d134.get("candidate_id"),
        "intake_id": d134.get("intake_id"),
        "ping_id": d134.get("ping_id"),
        "config_id": d134.get("config_id"),
        "dashboard_id": d134.get("dashboard_id"),
        "adapter_id": d134.get("adapter_id"),
        "seal_id": d134.get("seal_id"),
        "proposal_id": d134.get("proposal_id"),
        "source_d134_report": D134_REPORT,
        "sandbox_candidate_post_write_validation_report": validation_report if ok else {},
        "sandbox_candidate_materialized_file_inventory": inventory if ok else {},
        "d136_scope": d136_scope if ok else {},
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
            "sandbox_candidate_post_write_validation_scope_only": True,
            "post_write_validation_report_only": True,
            "materialized_file_inventory_only": True,
            "candidate_files_materialized": ok,
            "candidate_files_validated": ok,
            "candidate_executed_now": False,
            "approval_for_d136_execution_preflight_scope_only": ok,
            "approval_for_candidate_execution": False,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "validation_id": validation_id,
            "write_materialization_id": d134.get("write_materialization_id"),
            "materialization_id": d134.get("materialization_id"),
            "static_validation_id": d134.get("static_validation_id"),
            "write_once_id": d134.get("write_once_id"),
            "window_id": d134.get("window_id"),
            "runner_id": d134.get("runner_id"),
            "plan_id": d134.get("plan_id"),
            "review_id": d134.get("review_id"),
            "candidate_id": d134.get("candidate_id"),
            "adapter_id": d134.get("adapter_id"),
            "seal_id": d134.get("seal_id"),
            "proposal_id": d134.get("proposal_id"),
            "post_write_validation_status": "POST_WRITE_VALIDATION_PASS_NO_EXECUTION" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D136_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_post_write_validation_scope_created": ok,
            "sandbox_candidate_post_write_validation_report_created": ok,
            "sandbox_candidate_materialized_file_inventory_created": ok,
            "d136_scope_created": ok,
            "candidate_files_validated": ok,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D136 may create sandbox candidate execution preflight scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_post_write_validation_scope(), ensure_ascii=False, indent=2))
