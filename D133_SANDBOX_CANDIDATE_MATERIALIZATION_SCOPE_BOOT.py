#!/usr/bin/env python3
# D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_BOOT.py
#
# D133 consumes D132 static-validation artifacts and creates:
# - runtime_experimental/sandbox_candidate_materialization_scope.py
# - tests/test_d133_sandbox_candidate_materialization_scope.py
# - reports/d133_sandbox_candidate_materialization_scope.json
# - reports/d133_sandbox_candidate_materialization_manifest.json
# - reports/d133_sandbox_candidate_materialization_preflight.json
# - reports/d133_d134_sandbox_candidate_write_materialization_scope.json
#
# MATERIALIZATION SCOPE ONLY:
# no candidate write, no candidate execution, no apply, no shell, no network,
# no secret read, no protected core mutation, no route insert, no AI git action.
#
# D133 opens D134 Sandbox Candidate Write Materialization Scope.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE = r'''
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D132_REPORT = "reports/d132_sandbox_candidate_static_validation_scope.json"
D132_STATIC_VALIDATION_REPORT = "reports/d132_sandbox_candidate_static_validation_report.json"
D132_PATH_BOUNDARY_REPORT = "reports/d132_sandbox_candidate_path_boundary_report.json"
D132_D133_SCOPE = "reports/d132_d133_sandbox_candidate_materialization_scope.json"

OUT = "reports/d133_sandbox_candidate_materialization_scope.json"
MATERIALIZATION_MANIFEST_OUT = "reports/d133_sandbox_candidate_materialization_manifest.json"
MATERIALIZATION_PREFLIGHT_OUT = "reports/d133_sandbox_candidate_materialization_preflight.json"
D134_SCOPE_OUT = "reports/d133_d134_sandbox_candidate_write_materialization_scope.json"

REQ_D132_DECISION = "SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_READY"
REQ_D133_GATE = "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE"
REQ_D134_GATE = "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE"
REQ_D132_APPROVAL_SCOPE = "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_ONLY"

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

PROTECTED_TARGETS = [
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


def validate_d132(d132, static_validation_report, path_boundary_report, d133_scope):
    errors = []

    if not d132:
        errors.append("missing D132 sandbox candidate static validation scope report")
        return errors

    if d132.get("ok") is not True:
        errors.append("D132 ok must be true")
    if d132.get("decision") != REQ_D132_DECISION:
        errors.append("D132 decision must be SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_READY")

    guard = d132.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D132 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_static_validation_scope_only",
        "static_validation_report_only",
        "path_boundary_report_only",
        "approval_for_d133_materialization_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D132 guardrails.{key} must be true")

    for key in [
        "candidate_files_written_now",
        "candidate_executed_now",
        "approval_for_candidate_execution",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D132 guardrails.{key} must be false")

    summary = d132.get("summary", {})
    expected = {
        "static_validation_status": "STATIC_VALIDATION_PASS_NO_WRITE",
        "path_boundary_status": "STATIC_PATH_BOUNDARY_PASS_NO_SCAN",
        "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": REQ_D132_APPROVAL_SCOPE,
        "next_step": REQ_D133_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D132 summary.{key} must be {value}")

    if not static_validation_report:
        errors.append("missing D132 sandbox candidate static validation report")
    else:
        if static_validation_report.get("ok") is not True:
            errors.append("D132 static validation report ok must be true")
        if static_validation_report.get("validation_mode") != "STATIC_VALIDATION_ONLY_NO_CANDIDATE_WRITE_EXECUTION":
            errors.append("D132 static validation mode must be no-write/no-execution")
        if static_validation_report.get("static_validation_status") != "PASS_STATIC_ONLY":
            errors.append("D132 static validation status must be PASS_STATIC_ONLY")
        root = static_validation_report.get("allowed_candidate_write_root")
        if not is_safe_candidate_root(root):
            errors.append("D132 static validation root must be safe")
        planned = static_validation_report.get("planned_candidate_files", [])
        if len(planned) < 3:
            errors.append("D132 static validation must include at least 3 planned candidate files")
        for path in planned:
            if not is_safe_candidate_path(path, root):
                errors.append("D132 planned candidate file must stay inside allowed candidate write root")
        checks = static_validation_report.get("checks", {})
        required_checks = [
            "write_once_manifest_present",
            "materialized_preview_present",
            "candidate_root_safe",
            "planned_paths_under_candidate_root",
            "preview_paths_under_candidate_root",
            "preview_matches_planned_count",
            "candidate_not_written",
            "candidate_not_executed",
            "real_apply_blocked",
            "route_insert_blocked",
            "protected_core_untouched",
            "no_shell",
            "no_network",
            "no_secret_read",
        ]
        for key in required_checks:
            if checks.get(key) is not True:
                errors.append(f"D132 static validation check {key} must be true")
        for key in [
            "candidate_files_written_now",
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
            if static_validation_report.get(key) is not False:
                errors.append(f"D132 static validation report {key} must be false")

    if not path_boundary_report:
        errors.append("missing D132 sandbox candidate path boundary report")
    else:
        if path_boundary_report.get("ok") is not True:
            errors.append("D132 path boundary report ok must be true")
        if path_boundary_report.get("boundary_mode") != "PATH_BOUNDARY_STATIC_ONLY_NO_FILESYSTEM_SCAN":
            errors.append("D132 path boundary mode must be static-only/no-scan")
        if path_boundary_report.get("boundary_status") != "STATIC_PATH_BOUNDARY_PASS":
            errors.append("D132 path boundary status must be STATIC_PATH_BOUNDARY_PASS")
        root = path_boundary_report.get("allowed_candidate_write_root")
        if not is_safe_candidate_root(root):
            errors.append("D132 path boundary root must be safe")
        if path_boundary_report.get("blocked_paths", []) != []:
            errors.append("D132 path boundary blocked_paths must be empty")
        for target in PROTECTED_TARGETS:
            if target not in path_boundary_report.get("protected_targets", []):
                errors.append(f"D132 path boundary protected target missing: {target}")
        if path_boundary_report.get("filesystem_scan_executed") is not False:
            errors.append("D132 path boundary filesystem scan must be false")
        if path_boundary_report.get("git_diff_executed") is not False:
            errors.append("D132 path boundary git diff must be false")
        for path in path_boundary_report.get("static_paths_checked", []):
            if not is_safe_candidate_path(path, root):
                errors.append("D132 static path checked must stay inside candidate root")
        for key in [
            "candidate_files_written_now",
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
            if path_boundary_report.get(key) is not False:
                errors.append(f"D132 path boundary report {key} must be false")

    if not d133_scope:
        errors.append("missing D132 D133 sandbox candidate materialization scope")
    else:
        if d133_scope.get("ok") is not True:
            errors.append("D132 D133 scope ok must be true")
        if d133_scope.get("allowed_next_gate") != REQ_D133_GATE:
            errors.append("D132 D133 scope allowed_next_gate must be D133")
        if d133_scope.get("sandbox_candidate_materialization_scope_only") is not True:
            errors.append("D132 D133 scope must be materialization scope only")
        if d133_scope.get("human_review_required") is not True:
            errors.append("D132 D133 scope must require human review")
        for key in [
            "candidate_written_after_d132",
            "candidate_executed_after_d132_by_ai",
            "real_apply_allowed_after_d132_by_ai",
            "route_insert_allowed_after_d132_by_ai",
            "protected_core_mutation_allowed_after_d132_by_ai",
        ]:
            if d133_scope.get(key) is not False:
                errors.append(f"D132 D133 scope {key} must be false")

    return errors


def build_materialization_manifest(materialization_id, d132, static_validation_report, path_boundary_report):
    root = static_validation_report.get("allowed_candidate_write_root")
    planned = static_validation_report.get("planned_candidate_files", [])
    return {
        "state": "D133_SANDBOX_CANDIDATE_MATERIALIZATION_MANIFEST",
        "ok": True,
        "materialization_id": materialization_id,
        "static_validation_id": d132.get("static_validation_id"),
        "write_once_id": d132.get("write_once_id"),
        "window_id": d132.get("window_id"),
        "runner_id": d132.get("runner_id"),
        "plan_id": d132.get("plan_id"),
        "review_id": d132.get("review_id"),
        "candidate_id": d132.get("candidate_id"),
        "proposal_id": d132.get("proposal_id"),
        "created_at": now(),
        "manifest_mode": "MATERIALIZATION_MANIFEST_ONLY_NO_CANDIDATE_WRITE",
        "materialization_status": "MATERIALIZATION_SCOPE_DECLARED_NOT_WRITTEN",
        "allowed_candidate_write_root": root,
        "planned_materialization_files": planned,
        "planned_materialization_file_count": len(planned),
        "source_preview_digest": static_validation_report.get("preview_digest"),
        "path_boundary_status": path_boundary_report.get("boundary_status"),
        "materialization_policy": {
            "static_validation_required": True,
            "path_boundary_required": True,
            "candidate_root_only": True,
            "write_materialization_next_gate_only": True,
            "single_materialization_attempt": True,
            "no_overwrite_existing_candidate_files": True,
            "no_execution_after_materialization": True,
            "no_apply_after_materialization": True,
            "no_route_insert_after_materialization": True,
            "human_review_required": True,
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


def build_materialization_preflight(materialization_id, d132, static_validation_report, path_boundary_report):
    root = static_validation_report.get("allowed_candidate_write_root")
    planned = static_validation_report.get("planned_candidate_files", [])
    blocked = path_boundary_report.get("blocked_paths", [])
    checks = {
        "d132_static_validation_scope_ready": d132.get("decision") == REQ_D132_DECISION,
        "static_validation_report_passed": static_validation_report.get("ok") is True,
        "path_boundary_report_passed": path_boundary_report.get("ok") is True,
        "candidate_root_safe": is_safe_candidate_root(root),
        "planned_files_present": len(planned) >= 3,
        "planned_paths_under_candidate_root": all(is_safe_candidate_path(path, root) for path in planned),
        "no_blocked_paths": blocked == [],
        "candidate_not_written": True,
        "candidate_not_executed": True,
        "real_apply_blocked": True,
        "route_insert_blocked": True,
        "protected_core_untouched": True,
        "no_shell": True,
        "no_network": True,
        "no_secret_read": True,
    }
    return {
        "state": "D133_SANDBOX_CANDIDATE_MATERIALIZATION_PREFLIGHT",
        "ok": all(checks.values()),
        "materialization_id": materialization_id,
        "static_validation_id": d132.get("static_validation_id"),
        "write_once_id": d132.get("write_once_id"),
        "window_id": d132.get("window_id"),
        "runner_id": d132.get("runner_id"),
        "plan_id": d132.get("plan_id"),
        "review_id": d132.get("review_id"),
        "candidate_id": d132.get("candidate_id"),
        "proposal_id": d132.get("proposal_id"),
        "created_at": now(),
        "preflight_mode": "MATERIALIZATION_PREFLIGHT_ONLY_NO_FILESYSTEM_WRITE",
        "preflight_status": "MATERIALIZATION_PREFLIGHT_PASS_NO_WRITE" if all(checks.values()) else "MATERIALIZATION_PREFLIGHT_BLOCKED",
        "allowed_candidate_write_root": root,
        "planned_materialization_files": planned,
        "checks": checks,
        "filesystem_write_executed": False,
        "filesystem_scan_executed": False,
        "git_diff_executed": False,
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


def build_d134_scope(materialization_id, d132):
    return {
        "state": "D133_D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE",
        "ok": True,
        "materialization_id": materialization_id,
        "static_validation_id": d132.get("static_validation_id"),
        "write_once_id": d132.get("write_once_id"),
        "window_id": d132.get("window_id"),
        "runner_id": d132.get("runner_id"),
        "plan_id": d132.get("plan_id"),
        "review_id": d132.get("review_id"),
        "candidate_id": d132.get("candidate_id"),
        "intake_id": d132.get("intake_id"),
        "ping_id": d132.get("ping_id"),
        "config_id": d132.get("config_id"),
        "dashboard_id": d132.get("dashboard_id"),
        "adapter_id": d132.get("adapter_id"),
        "seal_id": d132.get("seal_id"),
        "proposal_id": d132.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D134_GATE,
        "d134_allowed_to_create": [
            "sandbox_candidate_write_materialization_scope",
            "sandbox_candidate_write_materialization_receipt",
            "sandbox_candidate_write_materialization_postcheck",
            "d135_sandbox_candidate_post_write_validation_scope",
        ],
        "d134_must_not_execute": [
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
        "sandbox_candidate_write_materialization_scope_only": True,
        "human_review_required": True,
        "candidate_written_after_d133": False,
        "candidate_executed_after_d133_by_ai": False,
        "real_apply_allowed_after_d133_by_ai": False,
        "route_insert_allowed_after_d133_by_ai": False,
        "protected_core_mutation_allowed_after_d133_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_ONLY",
    }


def create_sandbox_candidate_materialization_scope(root="."):
    root = Path(root).resolve()

    d132 = read_json(root / D132_REPORT, {}) or {}
    static_validation_report = read_json(root / D132_STATIC_VALIDATION_REPORT, {}) or {}
    path_boundary_report = read_json(root / D132_PATH_BOUNDARY_REPORT, {}) or {}
    d133_scope = read_json(root / D132_D133_SCOPE, {}) or {}

    errors = validate_d132(d132, static_validation_report, path_boundary_report, d133_scope)

    materialization_id = "d133-" + digest({
        "static_validation_id": d132.get("static_validation_id"),
        "write_once_id": d132.get("write_once_id"),
        "window_id": d132.get("window_id"),
        "runner_id": d132.get("runner_id"),
        "plan_id": d132.get("plan_id"),
        "review_id": d132.get("review_id"),
        "candidate_id": d132.get("candidate_id"),
        "proposal_id": d132.get("proposal_id"),
    })

    materialization_manifest = build_materialization_manifest(materialization_id, d132, static_validation_report, path_boundary_report)
    materialization_preflight = build_materialization_preflight(materialization_id, d132, static_validation_report, path_boundary_report)
    d134_scope = build_d134_scope(materialization_id, d132)

    if materialization_preflight.get("ok") is not True:
        errors.append("materialization_preflight must pass all preflight checks")

    policy = materialization_manifest.get("materialization_policy", {})
    for key in [
        "static_validation_required",
        "path_boundary_required",
        "candidate_root_only",
        "write_materialization_next_gate_only",
        "single_materialization_attempt",
        "no_overwrite_existing_candidate_files",
        "no_execution_after_materialization",
        "no_apply_after_materialization",
        "no_route_insert_after_materialization",
        "human_review_required",
    ]:
        if policy.get(key) is not True:
            errors.append(f"materialization_manifest policy {key} must be true")

    for item_name, item in [
        ("materialization_manifest", materialization_manifest),
        ("materialization_preflight", materialization_preflight),
    ]:
        for key in [
            "candidate_files_written_now",
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

    for key in ["filesystem_write_executed", "filesystem_scan_executed", "git_diff_executed"]:
        if materialization_preflight.get(key) is not False:
            errors.append(f"materialization_preflight {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_BLOCKED"
    result = "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_CREATED" if ok else "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_BLOCKED"

    if ok:
        write_json(root / MATERIALIZATION_MANIFEST_OUT, materialization_manifest)
        write_json(root / MATERIALIZATION_PREFLIGHT_OUT, materialization_preflight)
        write_json(root / D134_SCOPE_OUT, d134_scope)

    report = {
        "state": "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "materialization_id": materialization_id,
        "static_validation_id": d132.get("static_validation_id"),
        "write_once_id": d132.get("write_once_id"),
        "window_id": d132.get("window_id"),
        "runner_id": d132.get("runner_id"),
        "plan_id": d132.get("plan_id"),
        "review_id": d132.get("review_id"),
        "candidate_id": d132.get("candidate_id"),
        "intake_id": d132.get("intake_id"),
        "ping_id": d132.get("ping_id"),
        "config_id": d132.get("config_id"),
        "dashboard_id": d132.get("dashboard_id"),
        "adapter_id": d132.get("adapter_id"),
        "seal_id": d132.get("seal_id"),
        "proposal_id": d132.get("proposal_id"),
        "source_d132_report": D132_REPORT,
        "sandbox_candidate_materialization_manifest": materialization_manifest if ok else {},
        "sandbox_candidate_materialization_preflight": materialization_preflight if ok else {},
        "d134_scope": d134_scope if ok else {},
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
            "sandbox_candidate_materialization_scope_only": True,
            "materialization_manifest_only": True,
            "materialization_preflight_only": True,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "approval_for_d134_write_materialization_scope_only": ok,
            "approval_for_candidate_execution": False,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "materialization_id": materialization_id,
            "static_validation_id": d132.get("static_validation_id"),
            "write_once_id": d132.get("write_once_id"),
            "window_id": d132.get("window_id"),
            "runner_id": d132.get("runner_id"),
            "plan_id": d132.get("plan_id"),
            "review_id": d132.get("review_id"),
            "candidate_id": d132.get("candidate_id"),
            "adapter_id": d132.get("adapter_id"),
            "seal_id": d132.get("seal_id"),
            "proposal_id": d132.get("proposal_id"),
            "materialization_status": "MATERIALIZATION_SCOPE_DECLARED_NOT_WRITTEN" if ok else "BLOCKED",
            "materialization_preflight_status": "MATERIALIZATION_PREFLIGHT_PASS_NO_WRITE" if ok else "BLOCKED",
            "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D134_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_materialization_scope_created": ok,
            "sandbox_candidate_materialization_manifest_created": ok,
            "sandbox_candidate_materialization_preflight_created": ok,
            "d134_scope_created": ok,
            "candidate_files_written": False,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D134 may create sandbox candidate write materialization scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_materialization_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_materialization_scope import create_sandbox_candidate_materialization_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD133SandboxCandidateMaterializationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        static_validation_id = "d132-test"
        write_once_id = "d131-test"
        window_id = "d130-test"
        runner_id = "d129-test"
        plan_id = "d128-test"
        review_id = "d127-test"
        candidate_id = "d126-test"
        intake_id = "d125-test"
        ping_id = "d124-test"
        config_id = "d123-test"
        dashboard_id = "d122-test"
        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"
        candidate_root = f"runtime_experimental/ai_sandbox_work/{candidate_id}/"
        planned_files = [
            f"{candidate_root}candidate_manifest.json",
            f"{candidate_root}candidate_summary.md",
            f"{candidate_root}candidate_payload.json",
        ]

        false_guard = {
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
        }

        d132 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_READY",
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "intake_id": intake_id,
            "ping_id": ping_id,
            "config_id": config_id,
            "dashboard_id": dashboard_id,
            "adapter_id": adapter_id,
            "seal_id": seal_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_static_validation_scope_only": True,
                "static_validation_report_only": True,
                "path_boundary_report_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d133_materialization_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "static_validation_status": "STATIC_VALIDATION_PASS_NO_WRITE",
                "path_boundary_status": "STATIC_PATH_BOUNDARY_PASS_NO_SCAN",
                "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_ONLY",
                "next_step": "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE",
            },
        }

        static_validation_report = {
            "ok": True,
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "validation_mode": "STATIC_VALIDATION_ONLY_NO_CANDIDATE_WRITE_EXECUTION",
            "static_validation_status": "PASS_STATIC_ONLY",
            "allowed_candidate_write_root": candidate_root,
            "planned_candidate_files": planned_files,
            "preview_files_count": 3,
            "preview_digest": "preview-digest-test",
            "checks": {
                "write_once_manifest_present": True,
                "materialized_preview_present": True,
                "candidate_root_safe": True,
                "planned_paths_under_candidate_root": True,
                "preview_paths_under_candidate_root": True,
                "preview_matches_planned_count": True,
                "candidate_not_written": True,
                "candidate_not_executed": True,
                "real_apply_blocked": True,
                "route_insert_blocked": True,
                "protected_core_untouched": True,
                "no_shell": True,
                "no_network": True,
                "no_secret_read": True,
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

        path_boundary_report = {
            "ok": True,
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "boundary_mode": "PATH_BOUNDARY_STATIC_ONLY_NO_FILESYSTEM_SCAN",
            "boundary_status": "STATIC_PATH_BOUNDARY_PASS",
            "allowed_candidate_write_root": candidate_root,
            "static_paths_checked": planned_files,
            "blocked_paths": [],
            "protected_targets": ["app/orchestration/", "core/", "runtime/", "bridges/", "memory/"],
            "protected_targets_status": {
                "app/orchestration/": "OUT_OF_CANDIDATE_WRITE_SCOPE",
                "core/": "OUT_OF_CANDIDATE_WRITE_SCOPE",
                "runtime/": "OUT_OF_CANDIDATE_WRITE_SCOPE",
                "bridges/": "OUT_OF_CANDIDATE_WRITE_SCOPE",
                "memory/": "OUT_OF_CANDIDATE_WRITE_SCOPE",
            },
            "filesystem_scan_executed": False,
            "git_diff_executed": False,
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

        d133_scope = {
            "ok": True,
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE",
            "sandbox_candidate_materialization_scope_only": True,
            "human_review_required": True,
            "candidate_written_after_d132": False,
            "candidate_executed_after_d132_by_ai": False,
            "real_apply_allowed_after_d132_by_ai": False,
            "route_insert_allowed_after_d132_by_ai": False,
            "protected_core_mutation_allowed_after_d132_by_ai": False,
        }

        write(root / "reports/d132_sandbox_candidate_static_validation_scope.json", d132)
        write(root / "reports/d132_sandbox_candidate_static_validation_report.json", static_validation_report)
        write(root / "reports/d132_sandbox_candidate_path_boundary_report.json", path_boundary_report)
        write(root / "reports/d132_d133_sandbox_candidate_materialization_scope.json", d133_scope)
        return td, root

    def test_creates_materialization_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_materialization_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_READY")
            self.assertEqual(r["summary"]["materialization_status"], "MATERIALIZATION_SCOPE_DECLARED_NOT_WRITTEN")
            self.assertEqual(r["summary"]["approval_scope"], "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d134_scope"]["allowed_next_gate"], "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE")
            self.assertTrue((root / "reports/d133_sandbox_candidate_materialization_scope.json").exists())
            self.assertTrue((root / "reports/d133_sandbox_candidate_materialization_manifest.json").exists())
            self.assertTrue((root / "reports/d133_sandbox_candidate_materialization_preflight.json").exists())
            self.assertTrue((root / "reports/d133_d134_sandbox_candidate_write_materialization_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d132(self):
        td, root = self.root()
        try:
            (root / "reports/d132_sandbox_candidate_static_validation_scope.json").unlink()
            r = create_sandbox_candidate_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_static_validation_check_fails(self):
        td, root = self.root()
        try:
            p = root / "reports/d132_sandbox_candidate_static_validation_report.json"
            data = json.loads(p.read_text())
            data["checks"]["no_network"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_path_boundary_has_blocked_path(self):
        td, root = self.root()
        try:
            p = root / "reports/d132_sandbox_candidate_path_boundary_report.json"
            data = json.loads(p.read_text())
            data["blocked_paths"] = ["core/unsafe.py"]
            data["ok"] = False
            data["boundary_status"] = "STATIC_PATH_BOUNDARY_BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d133_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d132_d133_sandbox_candidate_materialization_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d132_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
'''


def sh(cmd, check=False):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, text=True, capture_output=False, check=check)


def repo_root():
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p
    return here


ROOT = repo_root()
os.chdir(ROOT)
Path("runtime_experimental").mkdir(exist_ok=True)
Path("tests").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)

print("D133 SANDBOX CANDIDATE MATERIALIZATION SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_materialization_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d133_sandbox_candidate_materialization_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_materialization_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d133_sandbox_candidate_materialization_scope", "-v"], check=True)

print("\n== run D133 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_materialization_scope import create_sandbox_candidate_materialization_scope\n"
    "r=create_sandbox_candidate_materialization_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d133_sandbox_candidate_materialization_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_materialization_scope.py",
    "tests/test_d133_sandbox_candidate_materialization_scope.py",
    "reports/d133_sandbox_candidate_materialization_scope.json",
    "reports/d133_sandbox_candidate_materialization_manifest.json",
    "reports/d133_sandbox_candidate_materialization_preflight.json",
    "reports/d133_d134_sandbox_candidate_write_materialization_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D133 sandbox candidate materialization scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D133 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD133 SANDBOX CANDIDATE MATERIALIZATION SCOPE BOOT DONE")
