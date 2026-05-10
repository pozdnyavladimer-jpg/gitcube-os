#!/usr/bin/env python3
# D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_BOOT.py
#
# D132 consumes D131 write-once / materialized-preview artifacts and creates:
# - runtime_experimental/sandbox_candidate_static_validation_scope.py
# - tests/test_d132_sandbox_candidate_static_validation_scope.py
# - reports/d132_sandbox_candidate_static_validation_scope.json
# - reports/d132_sandbox_candidate_static_validation_report.json
# - reports/d132_sandbox_candidate_path_boundary_report.json
# - reports/d132_d133_sandbox_candidate_materialization_scope.json
#
# STATIC VALIDATION SCOPE ONLY:
# no candidate write, no candidate execution, no apply, no shell, no network,
# no secret read, no protected core mutation, no route insert, no AI git action.
#
# D132 opens D133 Sandbox Candidate Materialization Scope.

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

D131_REPORT = "reports/d131_sandbox_candidate_write_once_scope.json"
D131_WRITE_ONCE_MANIFEST = "reports/d131_sandbox_candidate_write_once_manifest.json"
D131_MATERIALIZED_PREVIEW = "reports/d131_sandbox_candidate_materialized_preview.json"
D131_D132_SCOPE = "reports/d131_d132_sandbox_candidate_static_validation_scope.json"

OUT = "reports/d132_sandbox_candidate_static_validation_scope.json"
STATIC_VALIDATION_REPORT_OUT = "reports/d132_sandbox_candidate_static_validation_report.json"
PATH_BOUNDARY_REPORT_OUT = "reports/d132_sandbox_candidate_path_boundary_report.json"
D133_SCOPE_OUT = "reports/d132_d133_sandbox_candidate_materialization_scope.json"

REQ_D131_DECISION = "SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_READY"
REQ_D132_GATE = "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE"
REQ_D133_GATE = "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE"
REQ_D131_APPROVAL_SCOPE = "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_ONLY"

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


def validate_d131(d131, write_once_manifest, materialized_preview, d132_scope):
    errors = []

    if not d131:
        errors.append("missing D131 sandbox candidate write once scope report")
        return errors

    if d131.get("ok") is not True:
        errors.append("D131 ok must be true")
    if d131.get("decision") != REQ_D131_DECISION:
        errors.append("D131 decision must be SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_READY")

    guard = d131.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D131 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_write_once_scope_only",
        "write_once_manifest_only",
        "materialized_preview_only",
        "approval_for_d132_static_validation_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D131 guardrails.{key} must be true")

    for key in [
        "candidate_files_written_now",
        "candidate_executed_now",
        "approval_for_candidate_execution",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D131 guardrails.{key} must be false")

    summary = d131.get("summary", {})
    expected = {
        "write_once_status": "WRITE_ONCE_SCOPE_ARMED_NOT_USED",
        "materialized_preview_status": "PREVIEW_CREATED_NO_CANDIDATE_WRITE",
        "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": REQ_D131_APPROVAL_SCOPE,
        "next_step": REQ_D132_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D131 summary.{key} must be {value}")

    if not write_once_manifest:
        errors.append("missing D131 sandbox candidate write once manifest")
    else:
        if write_once_manifest.get("ok") is not True:
            errors.append("D131 write once manifest ok must be true")
        if write_once_manifest.get("manifest_mode") != "WRITE_ONCE_MANIFEST_ONLY_NO_CANDIDATE_WRITE":
            errors.append("D131 write once manifest mode must be no-candidate-write")
        if write_once_manifest.get("write_once_status") != "WRITE_ONCE_SCOPE_ARMED_NOT_USED":
            errors.append("D131 write once status must be armed not used")
        root = write_once_manifest.get("allowed_candidate_write_root")
        if not is_safe_candidate_root(root):
            errors.append("D131 allowed candidate write root must be safe runtime_experimental/ai_sandbox_work root")
        planned = write_once_manifest.get("planned_candidate_files_for_later_gate", [])
        if len(planned) < 3:
            errors.append("D131 write once manifest must include at least 3 planned candidate files")
        for item in planned:
            if not is_safe_candidate_path(item, root):
                errors.append("D131 planned candidate file must stay inside allowed candidate write root")
        policy = write_once_manifest.get("write_once_policy", {})
        for key in [
            "candidate_root_only",
            "single_materialization_window",
            "no_overwrite_existing_candidate_files",
            "hash_preview_before_write",
            "no_execution_after_write",
            "no_apply_after_write",
            "no_route_insert_after_write",
            "human_review_required",
        ]:
            if policy.get(key) is not True:
                errors.append(f"D131 write once policy {key} must be true")
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
            if write_once_manifest.get(key) is not False:
                errors.append(f"D131 write once manifest {key} must be false")

    if not materialized_preview:
        errors.append("missing D131 sandbox candidate materialized preview")
    else:
        if materialized_preview.get("ok") is not True:
            errors.append("D131 materialized preview ok must be true")
        if materialized_preview.get("preview_mode") != "MATERIALIZED_PREVIEW_ONLY_NO_CANDIDATE_WRITE":
            errors.append("D131 materialized preview mode must be no-candidate-write")
        root = materialized_preview.get("allowed_candidate_write_root")
        if not is_safe_candidate_root(root):
            errors.append("D131 materialized preview root must be safe")
        preview_files = materialized_preview.get("preview_files", [])
        if len(preview_files) < 3:
            errors.append("D131 materialized preview must include at least 3 preview files")
        for entry in preview_files:
            path = entry.get("path") if isinstance(entry, dict) else None
            if not is_safe_candidate_path(path, root):
                errors.append("D131 materialized preview path must stay inside allowed candidate write root")
            if isinstance(entry, dict) and entry.get("written_now") is not False:
                errors.append("D131 materialized preview written_now must be false")
            if isinstance(entry, dict) and entry.get("planned_for_later_write_gate") is not True:
                errors.append("D131 materialized preview must be planned for later write gate")
            if isinstance(entry, dict) and not isinstance(entry.get("preview_digest"), str):
                errors.append("D131 materialized preview file must have preview_digest")
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
            if materialized_preview.get(key) is not False:
                errors.append(f"D131 materialized preview {key} must be false")

    if not d132_scope:
        errors.append("missing D131 D132 sandbox candidate static validation scope")
    else:
        if d132_scope.get("ok") is not True:
            errors.append("D131 D132 scope ok must be true")
        if d132_scope.get("allowed_next_gate") != REQ_D132_GATE:
            errors.append("D131 D132 scope allowed_next_gate must be D132")
        if d132_scope.get("sandbox_candidate_static_validation_scope_only") is not True:
            errors.append("D131 D132 scope must be static validation scope only")
        if d132_scope.get("human_review_required") is not True:
            errors.append("D131 D132 scope must require human review")
        for key in [
            "candidate_written_after_d131",
            "candidate_executed_after_d131_by_ai",
            "real_apply_allowed_after_d131_by_ai",
            "route_insert_allowed_after_d131_by_ai",
            "protected_core_mutation_allowed_after_d131_by_ai",
        ]:
            if d132_scope.get(key) is not False:
                errors.append(f"D131 D132 scope {key} must be false")

    return errors


def build_static_validation_report(static_validation_id, d131, write_once_manifest, materialized_preview):
    root = write_once_manifest.get("allowed_candidate_write_root")
    planned = write_once_manifest.get("planned_candidate_files_for_later_gate", [])
    preview_files = materialized_preview.get("preview_files", [])
    preview_paths = [entry.get("path") for entry in preview_files if isinstance(entry, dict)]

    checks = {
        "write_once_manifest_present": True,
        "materialized_preview_present": True,
        "candidate_root_safe": is_safe_candidate_root(root),
        "planned_paths_under_candidate_root": all(is_safe_candidate_path(p, root) for p in planned),
        "preview_paths_under_candidate_root": all(is_safe_candidate_path(p, root) for p in preview_paths),
        "preview_matches_planned_count": len(preview_paths) == len(planned),
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
        "state": "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_REPORT",
        "ok": all(checks.values()),
        "static_validation_id": static_validation_id,
        "write_once_id": d131.get("write_once_id"),
        "window_id": d131.get("window_id"),
        "runner_id": d131.get("runner_id"),
        "plan_id": d131.get("plan_id"),
        "review_id": d131.get("review_id"),
        "candidate_id": d131.get("candidate_id"),
        "proposal_id": d131.get("proposal_id"),
        "created_at": now(),
        "validation_mode": "STATIC_VALIDATION_ONLY_NO_CANDIDATE_WRITE_EXECUTION",
        "static_validation_status": "PASS_STATIC_ONLY" if all(checks.values()) else "FAIL_STATIC_ONLY",
        "allowed_candidate_write_root": root,
        "planned_candidate_files": planned,
        "preview_files_count": len(preview_files),
        "preview_digest": materialized_preview.get("preview_digest"),
        "checks": checks,
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


def build_path_boundary_report(static_validation_id, d131, write_once_manifest, materialized_preview):
    root = write_once_manifest.get("allowed_candidate_write_root")
    planned = write_once_manifest.get("planned_candidate_files_for_later_gate", [])
    preview_files = materialized_preview.get("preview_files", [])
    preview_paths = [entry.get("path") for entry in preview_files if isinstance(entry, dict)]
    all_paths = []
    for path in [*planned, *preview_paths]:
        if path not in all_paths:
            all_paths.append(path)

    blocked_paths = [path for path in all_paths if not is_safe_candidate_path(path, root)]

    return {
        "state": "D132_SANDBOX_CANDIDATE_PATH_BOUNDARY_REPORT",
        "ok": len(blocked_paths) == 0 and is_safe_candidate_root(root),
        "static_validation_id": static_validation_id,
        "write_once_id": d131.get("write_once_id"),
        "candidate_id": d131.get("candidate_id"),
        "proposal_id": d131.get("proposal_id"),
        "created_at": now(),
        "boundary_mode": "PATH_BOUNDARY_STATIC_ONLY_NO_FILESYSTEM_SCAN",
        "boundary_status": "STATIC_PATH_BOUNDARY_PASS" if len(blocked_paths) == 0 and is_safe_candidate_root(root) else "STATIC_PATH_BOUNDARY_BLOCKED",
        "allowed_candidate_write_root": root,
        "static_paths_checked": all_paths,
        "blocked_paths": blocked_paths,
        "protected_targets": PROTECTED_TARGETS,
        "protected_targets_status": {target: "OUT_OF_CANDIDATE_WRITE_SCOPE" for target in PROTECTED_TARGETS},
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


def build_d133_scope(static_validation_id, d131):
    return {
        "state": "D132_D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE",
        "ok": True,
        "static_validation_id": static_validation_id,
        "write_once_id": d131.get("write_once_id"),
        "window_id": d131.get("window_id"),
        "runner_id": d131.get("runner_id"),
        "plan_id": d131.get("plan_id"),
        "review_id": d131.get("review_id"),
        "candidate_id": d131.get("candidate_id"),
        "intake_id": d131.get("intake_id"),
        "ping_id": d131.get("ping_id"),
        "config_id": d131.get("config_id"),
        "dashboard_id": d131.get("dashboard_id"),
        "adapter_id": d131.get("adapter_id"),
        "seal_id": d131.get("seal_id"),
        "proposal_id": d131.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D133_GATE,
        "d133_allowed_to_create": [
            "sandbox_candidate_materialization_scope",
            "sandbox_candidate_materialization_manifest",
            "sandbox_candidate_materialization_preflight",
            "d134_sandbox_candidate_write_materialization_scope",
        ],
        "d133_must_not_execute": [
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
        "sandbox_candidate_materialization_scope_only": True,
        "human_review_required": True,
        "candidate_written_after_d132": False,
        "candidate_executed_after_d132_by_ai": False,
        "real_apply_allowed_after_d132_by_ai": False,
        "route_insert_allowed_after_d132_by_ai": False,
        "protected_core_mutation_allowed_after_d132_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_ONLY",
    }


def create_sandbox_candidate_static_validation_scope(root="."):
    root = Path(root).resolve()

    d131 = read_json(root / D131_REPORT, {}) or {}
    write_once_manifest = read_json(root / D131_WRITE_ONCE_MANIFEST, {}) or {}
    materialized_preview = read_json(root / D131_MATERIALIZED_PREVIEW, {}) or {}
    d132_scope = read_json(root / D131_D132_SCOPE, {}) or {}

    errors = validate_d131(d131, write_once_manifest, materialized_preview, d132_scope)

    static_validation_id = "d132-" + digest({
        "write_once_id": d131.get("write_once_id"),
        "window_id": d131.get("window_id"),
        "runner_id": d131.get("runner_id"),
        "plan_id": d131.get("plan_id"),
        "review_id": d131.get("review_id"),
        "candidate_id": d131.get("candidate_id"),
        "proposal_id": d131.get("proposal_id"),
    })

    static_validation_report = build_static_validation_report(static_validation_id, d131, write_once_manifest, materialized_preview)
    path_boundary_report = build_path_boundary_report(static_validation_id, d131, write_once_manifest, materialized_preview)
    d133_scope = build_d133_scope(static_validation_id, d131)

    if static_validation_report.get("ok") is not True:
        errors.append("static_validation_report must pass all static checks")
    if path_boundary_report.get("ok") is not True:
        errors.append("path_boundary_report must pass all boundary checks")

    for item_name, item in [
        ("static_validation_report", static_validation_report),
        ("path_boundary_report", path_boundary_report),
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

    if path_boundary_report.get("filesystem_scan_executed") is not False:
        errors.append("path_boundary_report filesystem_scan_executed must be false")
    if path_boundary_report.get("git_diff_executed") is not False:
        errors.append("path_boundary_report git_diff_executed must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_BLOCKED"
    result = "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_CREATED" if ok else "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_BLOCKED"

    if ok:
        write_json(root / STATIC_VALIDATION_REPORT_OUT, static_validation_report)
        write_json(root / PATH_BOUNDARY_REPORT_OUT, path_boundary_report)
        write_json(root / D133_SCOPE_OUT, d133_scope)

    report = {
        "state": "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "static_validation_id": static_validation_id,
        "write_once_id": d131.get("write_once_id"),
        "window_id": d131.get("window_id"),
        "runner_id": d131.get("runner_id"),
        "plan_id": d131.get("plan_id"),
        "review_id": d131.get("review_id"),
        "candidate_id": d131.get("candidate_id"),
        "intake_id": d131.get("intake_id"),
        "ping_id": d131.get("ping_id"),
        "config_id": d131.get("config_id"),
        "dashboard_id": d131.get("dashboard_id"),
        "adapter_id": d131.get("adapter_id"),
        "seal_id": d131.get("seal_id"),
        "proposal_id": d131.get("proposal_id"),
        "source_d131_report": D131_REPORT,
        "sandbox_candidate_static_validation_report": static_validation_report if ok else {},
        "sandbox_candidate_path_boundary_report": path_boundary_report if ok else {},
        "d133_scope": d133_scope if ok else {},
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
            "sandbox_candidate_static_validation_scope_only": True,
            "static_validation_report_only": True,
            "path_boundary_report_only": True,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "approval_for_d133_materialization_scope_only": ok,
            "approval_for_candidate_execution": False,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "static_validation_id": static_validation_id,
            "write_once_id": d131.get("write_once_id"),
            "window_id": d131.get("window_id"),
            "runner_id": d131.get("runner_id"),
            "plan_id": d131.get("plan_id"),
            "review_id": d131.get("review_id"),
            "candidate_id": d131.get("candidate_id"),
            "adapter_id": d131.get("adapter_id"),
            "seal_id": d131.get("seal_id"),
            "proposal_id": d131.get("proposal_id"),
            "static_validation_status": "STATIC_VALIDATION_PASS_NO_WRITE" if ok else "BLOCKED",
            "path_boundary_status": "STATIC_PATH_BOUNDARY_PASS_NO_SCAN" if ok else "BLOCKED",
            "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D133_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_static_validation_scope_created": ok,
            "sandbox_candidate_static_validation_report_created": ok,
            "sandbox_candidate_path_boundary_report_created": ok,
            "d133_scope_created": ok,
            "candidate_files_written": False,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D133 may create sandbox candidate materialization scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_static_validation_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_static_validation_scope import create_sandbox_candidate_static_validation_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD132SandboxCandidateStaticValidationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

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

        d131 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_READY",
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
                "sandbox_candidate_write_once_scope_only": True,
                "write_once_manifest_only": True,
                "materialized_preview_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d132_static_validation_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "write_once_status": "WRITE_ONCE_SCOPE_ARMED_NOT_USED",
                "materialized_preview_status": "PREVIEW_CREATED_NO_CANDIDATE_WRITE",
                "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_ONLY",
                "next_step": "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE",
            },
        }

        write_once_manifest = {
            "ok": True,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "manifest_mode": "WRITE_ONCE_MANIFEST_ONLY_NO_CANDIDATE_WRITE",
            "write_once_status": "WRITE_ONCE_SCOPE_ARMED_NOT_USED",
            "allowed_candidate_write_root": candidate_root,
            "planned_candidate_files_for_later_gate": planned_files,
            "write_once_policy": {
                "candidate_root_only": True,
                "single_materialization_window": True,
                "no_overwrite_existing_candidate_files": True,
                "hash_preview_before_write": True,
                "no_execution_after_write": True,
                "no_apply_after_write": True,
                "no_route_insert_after_write": True,
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

        materialized_preview = {
            "ok": True,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "preview_mode": "MATERIALIZED_PREVIEW_ONLY_NO_CANDIDATE_WRITE",
            "allowed_candidate_write_root": candidate_root,
            "preview_files": [
                {"path": planned_files[0], "role": "candidate_manifest.json", "planned_for_later_write_gate": True, "written_now": False, "preview_digest": "aaaabbbbcccc1111"},
                {"path": planned_files[1], "role": "candidate_summary.md", "planned_for_later_write_gate": True, "written_now": False, "preview_digest": "dddd111122223333"},
                {"path": planned_files[2], "role": "candidate_payload.json", "planned_for_later_write_gate": True, "written_now": False, "preview_digest": "eeee444455556666"},
            ],
            "preview_digest": "preview-digest-test",
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

        d132_scope = {
            "ok": True,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE",
            "sandbox_candidate_static_validation_scope_only": True,
            "human_review_required": True,
            "candidate_written_after_d131": False,
            "candidate_executed_after_d131_by_ai": False,
            "real_apply_allowed_after_d131_by_ai": False,
            "route_insert_allowed_after_d131_by_ai": False,
            "protected_core_mutation_allowed_after_d131_by_ai": False,
        }

        write(root / "reports/d131_sandbox_candidate_write_once_scope.json", d131)
        write(root / "reports/d131_sandbox_candidate_write_once_manifest.json", write_once_manifest)
        write(root / "reports/d131_sandbox_candidate_materialized_preview.json", materialized_preview)
        write(root / "reports/d131_d132_sandbox_candidate_static_validation_scope.json", d132_scope)
        return td, root

    def test_creates_static_validation_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_static_validation_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_READY")
            self.assertEqual(r["summary"]["static_validation_status"], "STATIC_VALIDATION_PASS_NO_WRITE")
            self.assertEqual(r["summary"]["approval_scope"], "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d133_scope"]["allowed_next_gate"], "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE")
            self.assertTrue((root / "reports/d132_sandbox_candidate_static_validation_scope.json").exists())
            self.assertTrue((root / "reports/d132_sandbox_candidate_static_validation_report.json").exists())
            self.assertTrue((root / "reports/d132_sandbox_candidate_path_boundary_report.json").exists())
            self.assertTrue((root / "reports/d132_d133_sandbox_candidate_materialization_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d131(self):
        td, root = self.root()
        try:
            (root / "reports/d131_sandbox_candidate_write_once_scope.json").unlink()
            r = create_sandbox_candidate_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_materialized_preview_says_candidate_written(self):
        td, root = self.root()
        try:
            p = root / "reports/d131_sandbox_candidate_materialized_preview.json"
            data = json.loads(p.read_text())
            data["candidate_files_written_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_preview_path_leaves_candidate_root(self):
        td, root = self.root()
        try:
            p = root / "reports/d131_sandbox_candidate_materialized_preview.json"
            data = json.loads(p.read_text())
            data["preview_files"][0]["path"] = "core/unsafe.py"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d132_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d131_d132_sandbox_candidate_static_validation_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d131_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_static_validation_scope(root)
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

print("D132 SANDBOX CANDIDATE STATIC VALIDATION SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_static_validation_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d132_sandbox_candidate_static_validation_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_static_validation_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d132_sandbox_candidate_static_validation_scope", "-v"], check=True)

print("\n== run D132 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_static_validation_scope import create_sandbox_candidate_static_validation_scope\n"
    "r=create_sandbox_candidate_static_validation_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d132_sandbox_candidate_static_validation_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_static_validation_scope.py",
    "tests/test_d132_sandbox_candidate_static_validation_scope.py",
    "reports/d132_sandbox_candidate_static_validation_scope.json",
    "reports/d132_sandbox_candidate_static_validation_report.json",
    "reports/d132_sandbox_candidate_path_boundary_report.json",
    "reports/d132_d133_sandbox_candidate_materialization_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D132 sandbox candidate static validation scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D132 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD132 SANDBOX CANDIDATE STATIC VALIDATION SCOPE BOOT DONE")
