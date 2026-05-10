
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D129_REPORT = "reports/d129_sandbox_candidate_dry_test_runner_scope.json"
D129_DRY_RESULTS = "reports/d129_sandbox_candidate_dry_test_results.json"
D129_INTEGRITY_DIFF = "reports/d129_sandbox_candidate_integrity_diff_summary.json"
D129_D130_SCOPE = "reports/d129_d130_sandbox_candidate_write_window_scope.json"

OUT = "reports/d130_sandbox_candidate_write_window_scope.json"
WRITE_WINDOW_MANIFEST_OUT = "reports/d130_sandbox_candidate_write_window_manifest.json"
WRITE_PREFLIGHT_OUT = "reports/d130_sandbox_candidate_write_preflight.json"
D131_SCOPE_OUT = "reports/d130_d131_sandbox_candidate_write_once_scope.json"

REQ_D129_DECISION = "SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_READY"
REQ_D130_GATE = "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE"
REQ_D131_GATE = "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE"
REQ_D129_APPROVAL_SCOPE = "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_ONLY"

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

NO_TOUCH_TARGETS = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
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


def validate_d129(d129, dry_results, integrity_diff, d130_scope):
    errors = []

    if not d129:
        errors.append("missing D129 sandbox candidate dry test runner scope report")
        return errors

    if d129.get("ok") is not True:
        errors.append("D129 ok must be true")
    if d129.get("decision") != REQ_D129_DECISION:
        errors.append("D129 decision must be SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_READY")

    guard = d129.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D129 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_dry_test_runner_scope_only",
        "dry_test_results_only",
        "integrity_diff_summary_only",
        "approval_for_d130_write_window_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D129 guardrails.{key} must be true")

    for key in [
        "candidate_files_written_now",
        "candidate_executed_now",
        "approval_for_candidate_execution",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D129 guardrails.{key} must be false")

    summary = d129.get("summary", {})
    expected = {
        "dry_test_status": "DRY_RESULTS_CREATED_NOT_EXECUTED",
        "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
        "integrity_status": "NO_TOUCH_ASSERTIONS_HELD_BY_SCOPE",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "real_apply_by_ai_status": "BLOCKED",
        "approval_scope": REQ_D129_APPROVAL_SCOPE,
        "next_step": REQ_D130_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D129 summary.{key} must be {value}")

    if not dry_results:
        errors.append("missing D129 sandbox candidate dry test results")
    else:
        if dry_results.get("ok") is not True:
            errors.append("D129 dry results ok must be true")
        if dry_results.get("results_mode") != "DRY_TEST_RESULTS_ONLY_NO_CANDIDATE_EXECUTION":
            errors.append("D129 dry results mode must be no-candidate-execution")
        if dry_results.get("human_review_required") is not True:
            errors.append("D129 dry results must require human review")
        if dry_results.get("test_groups_total", 0) < 4:
            errors.append("D129 dry results must include at least 4 dry test groups")
        if dry_results.get("test_groups_dry_passed") != dry_results.get("test_groups_total"):
            errors.append("D129 dry results dry_passed must equal total")
        for check in dry_results.get("checks", []):
            if check.get("dry_only") is not True:
                errors.append("D129 dry result check must be dry_only")
            if check.get("candidate_executed") is not False:
                errors.append("D129 dry result check candidate_executed must be false")
            if check.get("actual_apply_executed") is not False:
                errors.append("D129 dry result check actual_apply_executed must be false")
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "network_accessed",
            "api_key_read",
            "secret_read",
        ]:
            if dry_results.get(key) is not False:
                errors.append(f"D129 dry results {key} must be false")

    if not integrity_diff:
        errors.append("missing D129 sandbox candidate integrity diff summary")
    else:
        if integrity_diff.get("ok") is not True:
            errors.append("D129 integrity diff ok must be true")
        if integrity_diff.get("summary_mode") != "DECLARED_NO_TOUCH_DIFF_SUMMARY_NO_GIT_DIFF_EXECUTION":
            errors.append("D129 integrity diff summary mode must be declared no-touch without git diff execution")
        if integrity_diff.get("human_review_required") is not True:
            errors.append("D129 integrity diff must require human review")
        for key in [
            "git_diff_executed",
            "filesystem_scan_executed",
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
        ]:
            if integrity_diff.get(key) is not False:
                errors.append(f"D129 integrity diff {key} must be false")
        for target in NO_TOUCH_TARGETS:
            if target not in integrity_diff.get("protected_targets", []):
                errors.append(f"D129 integrity diff protected target missing: {target}")

    if not d130_scope:
        errors.append("missing D129 D130 sandbox candidate write window scope")
    else:
        if d130_scope.get("ok") is not True:
            errors.append("D129 D130 scope ok must be true")
        if d130_scope.get("allowed_next_gate") != REQ_D130_GATE:
            errors.append("D129 D130 scope allowed_next_gate must be D130")
        if d130_scope.get("sandbox_candidate_write_window_scope_only") is not True:
            errors.append("D129 D130 scope must be write window scope only")
        if d130_scope.get("human_review_required") is not True:
            errors.append("D129 D130 scope must require human review")
        for key in [
            "candidate_written_after_d129",
            "candidate_executed_after_d129_by_ai",
            "real_apply_allowed_after_d129_by_ai",
            "route_insert_allowed_after_d129_by_ai",
            "protected_core_mutation_allowed_after_d129_by_ai",
        ]:
            if d130_scope.get(key) is not False:
                errors.append(f"D129 D130 scope {key} must be false")

    return errors


def build_write_window_manifest(window_id, d129):
    candidate_id = d129.get("candidate_id") or "unknown-candidate"
    candidate_root = f"runtime_experimental/ai_sandbox_work/{candidate_id}/"

    return {
        "state": "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_MANIFEST",
        "ok": True,
        "window_id": window_id,
        "runner_id": d129.get("runner_id"),
        "plan_id": d129.get("plan_id"),
        "review_id": d129.get("review_id"),
        "candidate_id": d129.get("candidate_id"),
        "proposal_id": d129.get("proposal_id"),
        "created_at": now(),
        "manifest_mode": "WRITE_WINDOW_MANIFEST_ONLY_NO_CANDIDATE_WRITE",
        "write_window_status": "OPENED_FOR_D131_SCOPE_ONLY_NOT_USED",
        "allowed_candidate_write_root": candidate_root,
        "planned_candidate_files_for_later_gate": [
            f"{candidate_root}candidate_manifest.json",
            f"{candidate_root}candidate_summary.md",
            f"{candidate_root}candidate_payload.json",
        ],
        "allowed_report_outputs_for_later_gate": [
            "reports/d131_sandbox_candidate_write_once_scope.json",
            "reports/d131_sandbox_candidate_write_once_manifest.json",
            "reports/d131_sandbox_candidate_materialized_preview.json",
            "reports/d131_d132_sandbox_candidate_static_validation_scope.json",
        ],
        "write_policy": {
            "write_once_only_after_d131_gate": True,
            "candidate_root_only": True,
            "no_overwrite_without_later_gate": True,
            "no_execution_after_write": True,
            "no_apply_after_write": True,
            "human_review_required": True,
        },
        "candidate_files_written_now": False,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "human_review_required": True,
    }


def build_write_preflight(window_id, d129, dry_results, integrity_diff):
    return {
        "state": "D130_SANDBOX_CANDIDATE_WRITE_PREFLIGHT",
        "ok": True,
        "window_id": window_id,
        "runner_id": d129.get("runner_id"),
        "plan_id": d129.get("plan_id"),
        "review_id": d129.get("review_id"),
        "candidate_id": d129.get("candidate_id"),
        "created_at": now(),
        "preflight_mode": "WRITE_WINDOW_PREFLIGHT_ONLY_NO_CANDIDATE_WRITE",
        "preflight_status": "PASS_SCOPE_ONLY",
        "input_checks": {
            "d129_report_ready": d129.get("ok") is True,
            "dry_results_ready": dry_results.get("ok") is True,
            "integrity_diff_ready": integrity_diff.get("ok") is True,
            "dry_results_no_execution": dry_results.get("candidate_executed_now") is False,
            "integrity_no_git_diff_execution": integrity_diff.get("git_diff_executed") is False,
            "integrity_no_filesystem_scan_execution": integrity_diff.get("filesystem_scan_executed") is False,
        },
        "candidate_files_written_now": False,
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


def build_d131_scope(window_id, d129):
    return {
        "state": "D130_D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE",
        "ok": True,
        "window_id": window_id,
        "runner_id": d129.get("runner_id"),
        "plan_id": d129.get("plan_id"),
        "review_id": d129.get("review_id"),
        "candidate_id": d129.get("candidate_id"),
        "intake_id": d129.get("intake_id"),
        "ping_id": d129.get("ping_id"),
        "config_id": d129.get("config_id"),
        "dashboard_id": d129.get("dashboard_id"),
        "adapter_id": d129.get("adapter_id"),
        "seal_id": d129.get("seal_id"),
        "proposal_id": d129.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D131_GATE,
        "d131_allowed_to_create": [
            "sandbox_candidate_write_once_scope",
            "sandbox_candidate_write_once_manifest",
            "sandbox_candidate_materialized_preview",
            "d132_sandbox_candidate_static_validation_scope",
        ],
        "d131_must_not_execute": [
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
        "sandbox_candidate_write_once_scope_only": True,
        "human_review_required": True,
        "candidate_written_after_d130": False,
        "candidate_executed_after_d130_by_ai": False,
        "real_apply_allowed_after_d130_by_ai": False,
        "route_insert_allowed_after_d130_by_ai": False,
        "protected_core_mutation_allowed_after_d130_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_ONLY",
    }


def create_sandbox_candidate_write_window_scope(root="."):
    root = Path(root).resolve()

    d129 = read_json(root / D129_REPORT, {}) or {}
    dry_results = read_json(root / D129_DRY_RESULTS, {}) or {}
    integrity_diff = read_json(root / D129_INTEGRITY_DIFF, {}) or {}
    d130_scope = read_json(root / D129_D130_SCOPE, {}) or {}

    errors = validate_d129(d129, dry_results, integrity_diff, d130_scope)

    window_id = "d130-" + digest({
        "runner_id": d129.get("runner_id"),
        "plan_id": d129.get("plan_id"),
        "review_id": d129.get("review_id"),
        "candidate_id": d129.get("candidate_id"),
        "proposal_id": d129.get("proposal_id"),
    })

    write_window_manifest = build_write_window_manifest(window_id, d129)
    write_preflight = build_write_preflight(window_id, d129, dry_results, integrity_diff)
    d131_scope = build_d131_scope(window_id, d129)

    for item_name, item in [
        ("write_window_manifest", write_window_manifest),
        ("write_preflight", write_preflight),
    ]:
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "network_accessed",
            "api_key_read",
            "secret_read",
        ]:
            if item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    for key in [
        "route_inserted",
        "protected_core_mutated",
        "canonical_memory_mutated",
    ]:
        if write_preflight.get(key) is not False:
            errors.append(f"write_preflight {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_BLOCKED"
    result = "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_CREATED" if ok else "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_BLOCKED"

    if ok:
        write_json(root / WRITE_WINDOW_MANIFEST_OUT, write_window_manifest)
        write_json(root / WRITE_PREFLIGHT_OUT, write_preflight)
        write_json(root / D131_SCOPE_OUT, d131_scope)

    report = {
        "state": "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "window_id": window_id,
        "runner_id": d129.get("runner_id"),
        "plan_id": d129.get("plan_id"),
        "review_id": d129.get("review_id"),
        "candidate_id": d129.get("candidate_id"),
        "intake_id": d129.get("intake_id"),
        "ping_id": d129.get("ping_id"),
        "config_id": d129.get("config_id"),
        "dashboard_id": d129.get("dashboard_id"),
        "adapter_id": d129.get("adapter_id"),
        "seal_id": d129.get("seal_id"),
        "proposal_id": d129.get("proposal_id"),
        "source_d129_report": D129_REPORT,
        "sandbox_candidate_write_window_manifest": write_window_manifest if ok else {},
        "sandbox_candidate_write_preflight": write_preflight if ok else {},
        "d131_scope": d131_scope if ok else {},
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
            "sandbox_candidate_write_window_scope_only": True,
            "write_window_manifest_only": True,
            "write_preflight_only": True,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "approval_for_d131_write_once_scope_only": ok,
            "approval_for_candidate_execution": False,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "window_id": window_id,
            "runner_id": d129.get("runner_id"),
            "plan_id": d129.get("plan_id"),
            "review_id": d129.get("review_id"),
            "candidate_id": d129.get("candidate_id"),
            "adapter_id": d129.get("adapter_id"),
            "seal_id": d129.get("seal_id"),
            "proposal_id": d129.get("proposal_id"),
            "write_window_status": "WRITE_WINDOW_SCOPE_OPENED_NOT_USED" if ok else "BLOCKED",
            "write_preflight_status": "WRITE_PREFLIGHT_CREATED_NO_WRITE" if ok else "BLOCKED",
            "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D131_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_write_window_scope_created": ok,
            "sandbox_candidate_write_window_manifest_created": ok,
            "sandbox_candidate_write_preflight_created": ok,
            "d131_scope_created": ok,
            "candidate_files_written": False,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D131 may create sandbox candidate write-once scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_write_window_scope(), ensure_ascii=False, indent=2))
