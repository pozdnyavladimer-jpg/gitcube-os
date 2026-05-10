#!/usr/bin/env python3
# D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_BOOT.py
#
# D131 consumes D130 write-window artifacts and creates:
# - runtime_experimental/sandbox_candidate_write_once_scope.py
# - tests/test_d131_sandbox_candidate_write_once_scope.py
# - reports/d131_sandbox_candidate_write_once_scope.json
# - reports/d131_sandbox_candidate_write_once_manifest.json
# - reports/d131_sandbox_candidate_materialized_preview.json
# - reports/d131_d132_sandbox_candidate_static_validation_scope.json
#
# WRITE-ONCE SCOPE ONLY:
# no candidate execution, no apply, no shell, no network, no secret read,
# no route insert, no protected core mutation, no AI git action.
# This gate prepares a write-once manifest and materialized preview only;
# it does not execute or apply the candidate.
#
# D131 opens D132 Sandbox Candidate Static Validation Scope.

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

D130_REPORT = "reports/d130_sandbox_candidate_write_window_scope.json"
D130_WRITE_WINDOW_MANIFEST = "reports/d130_sandbox_candidate_write_window_manifest.json"
D130_WRITE_PREFLIGHT = "reports/d130_sandbox_candidate_write_preflight.json"
D130_D131_SCOPE = "reports/d130_d131_sandbox_candidate_write_once_scope.json"

OUT = "reports/d131_sandbox_candidate_write_once_scope.json"
WRITE_ONCE_MANIFEST_OUT = "reports/d131_sandbox_candidate_write_once_manifest.json"
MATERIALIZED_PREVIEW_OUT = "reports/d131_sandbox_candidate_materialized_preview.json"
D132_SCOPE_OUT = "reports/d131_d132_sandbox_candidate_static_validation_scope.json"

REQ_D130_DECISION = "SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_READY"
REQ_D131_GATE = "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE"
REQ_D132_GATE = "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE"
REQ_D130_APPROVAL_SCOPE = "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_ONLY"

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


def safe_candidate_root(root_value, candidate_id):
    default = f"runtime_experimental/ai_sandbox_work/{candidate_id or 'unknown-candidate'}/"
    if not isinstance(root_value, str) or not root_value:
        return default
    if not root_value.startswith("runtime_experimental/ai_sandbox_work/"):
        return default
    if ".." in root_value or root_value.startswith("/"):
        return default
    if not root_value.endswith("/"):
        return root_value + "/"
    return root_value


def validate_d130(d130, write_window_manifest, write_preflight, d131_scope):
    errors = []

    if not d130:
        errors.append("missing D130 sandbox candidate write window scope report")
        return errors

    if d130.get("ok") is not True:
        errors.append("D130 ok must be true")
    if d130.get("decision") != REQ_D130_DECISION:
        errors.append("D130 decision must be SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_READY")

    guard = d130.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D130 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_write_window_scope_only",
        "write_window_manifest_only",
        "write_preflight_only",
        "approval_for_d131_write_once_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D130 guardrails.{key} must be true")

    for key in [
        "candidate_files_written_now",
        "candidate_executed_now",
        "approval_for_candidate_execution",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D130 guardrails.{key} must be false")

    summary = d130.get("summary", {})
    expected = {
        "write_window_status": "WRITE_WINDOW_SCOPE_OPENED_NOT_USED",
        "write_preflight_status": "WRITE_PREFLIGHT_CREATED_NO_WRITE",
        "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": REQ_D130_APPROVAL_SCOPE,
        "next_step": REQ_D131_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D130 summary.{key} must be {value}")

    if not write_window_manifest:
        errors.append("missing D130 sandbox candidate write window manifest")
    else:
        if write_window_manifest.get("ok") is not True:
            errors.append("D130 write window manifest ok must be true")
        if write_window_manifest.get("manifest_mode") != "WRITE_WINDOW_MANIFEST_ONLY_NO_CANDIDATE_WRITE":
            errors.append("D130 write window manifest mode must be no-candidate-write")
        if write_window_manifest.get("write_window_status") != "OPENED_FOR_D131_SCOPE_ONLY_NOT_USED":
            errors.append("D130 write window status must be opened for D131 only and not used")
        root = write_window_manifest.get("allowed_candidate_write_root")
        if not isinstance(root, str) or not root.startswith("runtime_experimental/ai_sandbox_work/") or ".." in root or root.startswith("/"):
            errors.append("D130 allowed candidate write root must stay inside runtime_experimental/ai_sandbox_work")
        planned = write_window_manifest.get("planned_candidate_files_for_later_gate", [])
        if len(planned) < 3:
            errors.append("D130 write window manifest must include at least 3 planned candidate files")
        for item in planned:
            if not isinstance(item, str) or not isinstance(root, str) or not item.startswith(root):
                errors.append("D130 planned candidate file must stay inside allowed candidate write root")
        policy = write_window_manifest.get("write_policy", {})
        for key in [
            "write_once_only_after_d131_gate",
            "candidate_root_only",
            "no_overwrite_without_later_gate",
            "no_execution_after_write",
            "no_apply_after_write",
            "human_review_required",
        ]:
            if policy.get(key) is not True:
                errors.append(f"D130 write policy {key} must be true")
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
            if write_window_manifest.get(key) is not False:
                errors.append(f"D130 write window manifest {key} must be false")

    if not write_preflight:
        errors.append("missing D130 sandbox candidate write preflight")
    else:
        if write_preflight.get("ok") is not True:
            errors.append("D130 write preflight ok must be true")
        if write_preflight.get("preflight_mode") != "WRITE_WINDOW_PREFLIGHT_ONLY_NO_CANDIDATE_WRITE":
            errors.append("D130 write preflight mode must be no-candidate-write")
        if write_preflight.get("preflight_status") != "PASS_SCOPE_ONLY":
            errors.append("D130 write preflight status must be PASS_SCOPE_ONLY")
        for key, value in write_preflight.get("input_checks", {}).items():
            if value is not True:
                errors.append(f"D130 write preflight input check {key} must be true")
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
            if write_preflight.get(key) is not False:
                errors.append(f"D130 write preflight {key} must be false")

    if not d131_scope:
        errors.append("missing D130 D131 sandbox candidate write once scope")
    else:
        if d131_scope.get("ok") is not True:
            errors.append("D130 D131 scope ok must be true")
        if d131_scope.get("allowed_next_gate") != REQ_D131_GATE:
            errors.append("D130 D131 scope allowed_next_gate must be D131")
        if d131_scope.get("sandbox_candidate_write_once_scope_only") is not True:
            errors.append("D130 D131 scope must be write-once scope only")
        if d131_scope.get("human_review_required") is not True:
            errors.append("D130 D131 scope must require human review")
        for key in [
            "candidate_written_after_d130",
            "candidate_executed_after_d130_by_ai",
            "real_apply_allowed_after_d130_by_ai",
            "route_insert_allowed_after_d130_by_ai",
            "protected_core_mutation_allowed_after_d130_by_ai",
        ]:
            if d131_scope.get(key) is not False:
                errors.append(f"D130 D131 scope {key} must be false")

    return errors


def build_write_once_manifest(write_once_id, d130, write_window_manifest):
    candidate_id = d130.get("candidate_id")
    root = safe_candidate_root(write_window_manifest.get("allowed_candidate_write_root"), candidate_id)
    planned = write_window_manifest.get("planned_candidate_files_for_later_gate") or [
        f"{root}candidate_manifest.json",
        f"{root}candidate_summary.md",
        f"{root}candidate_payload.json",
    ]

    planned = [p for p in planned if isinstance(p, str) and p.startswith(root) and ".." not in p and not p.startswith("/")]

    return {
        "state": "D131_SANDBOX_CANDIDATE_WRITE_ONCE_MANIFEST",
        "ok": True,
        "write_once_id": write_once_id,
        "window_id": d130.get("window_id"),
        "runner_id": d130.get("runner_id"),
        "plan_id": d130.get("plan_id"),
        "review_id": d130.get("review_id"),
        "candidate_id": candidate_id,
        "proposal_id": d130.get("proposal_id"),
        "created_at": now(),
        "manifest_mode": "WRITE_ONCE_MANIFEST_ONLY_NO_CANDIDATE_WRITE",
        "write_once_status": "WRITE_ONCE_SCOPE_ARMED_NOT_USED",
        "allowed_candidate_write_root": root,
        "planned_candidate_files_for_later_gate": planned,
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


def build_materialized_preview(write_once_id, d130, write_once_manifest):
    root = write_once_manifest.get("allowed_candidate_write_root")
    planned = write_once_manifest.get("planned_candidate_files_for_later_gate", [])

    preview_files = []
    for path in planned:
        role = Path(path).name
        preview_payload = {
            "candidate_id": d130.get("candidate_id"),
            "proposal_id": d130.get("proposal_id"),
            "path": path,
            "role": role,
            "mode": "preview_only_not_written",
        }
        preview_files.append({
            "path": path,
            "role": role,
            "planned_for_later_write_gate": True,
            "written_now": False,
            "preview_digest": digest(preview_payload),
        })

    return {
        "state": "D131_SANDBOX_CANDIDATE_MATERIALIZED_PREVIEW",
        "ok": True,
        "write_once_id": write_once_id,
        "window_id": d130.get("window_id"),
        "runner_id": d130.get("runner_id"),
        "plan_id": d130.get("plan_id"),
        "review_id": d130.get("review_id"),
        "candidate_id": d130.get("candidate_id"),
        "proposal_id": d130.get("proposal_id"),
        "created_at": now(),
        "preview_mode": "MATERIALIZED_PREVIEW_ONLY_NO_CANDIDATE_WRITE",
        "allowed_candidate_write_root": root,
        "preview_files": preview_files,
        "preview_digest": digest(preview_files),
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


def build_d132_scope(write_once_id, d130):
    return {
        "state": "D131_D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE",
        "ok": True,
        "write_once_id": write_once_id,
        "window_id": d130.get("window_id"),
        "runner_id": d130.get("runner_id"),
        "plan_id": d130.get("plan_id"),
        "review_id": d130.get("review_id"),
        "candidate_id": d130.get("candidate_id"),
        "intake_id": d130.get("intake_id"),
        "ping_id": d130.get("ping_id"),
        "config_id": d130.get("config_id"),
        "dashboard_id": d130.get("dashboard_id"),
        "adapter_id": d130.get("adapter_id"),
        "seal_id": d130.get("seal_id"),
        "proposal_id": d130.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D132_GATE,
        "d132_allowed_to_create": [
            "sandbox_candidate_static_validation_scope",
            "sandbox_candidate_static_validation_report",
            "sandbox_candidate_path_boundary_report",
            "d133_sandbox_candidate_materialization_scope",
        ],
        "d132_must_not_execute": [
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
        "sandbox_candidate_static_validation_scope_only": True,
        "human_review_required": True,
        "candidate_written_after_d131": False,
        "candidate_executed_after_d131_by_ai": False,
        "real_apply_allowed_after_d131_by_ai": False,
        "route_insert_allowed_after_d131_by_ai": False,
        "protected_core_mutation_allowed_after_d131_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_ONLY",
    }


def create_sandbox_candidate_write_once_scope(root="."):
    root = Path(root).resolve()

    d130 = read_json(root / D130_REPORT, {}) or {}
    write_window_manifest = read_json(root / D130_WRITE_WINDOW_MANIFEST, {}) or {}
    write_preflight = read_json(root / D130_WRITE_PREFLIGHT, {}) or {}
    d131_scope = read_json(root / D130_D131_SCOPE, {}) or {}

    errors = validate_d130(d130, write_window_manifest, write_preflight, d131_scope)

    write_once_id = "d131-" + digest({
        "window_id": d130.get("window_id"),
        "runner_id": d130.get("runner_id"),
        "plan_id": d130.get("plan_id"),
        "review_id": d130.get("review_id"),
        "candidate_id": d130.get("candidate_id"),
        "proposal_id": d130.get("proposal_id"),
    })

    write_once_manifest = build_write_once_manifest(write_once_id, d130, write_window_manifest)
    materialized_preview = build_materialized_preview(write_once_id, d130, write_once_manifest)
    d132_scope = build_d132_scope(write_once_id, d130)

    for item_name, item in [
        ("write_once_manifest", write_once_manifest),
        ("materialized_preview", materialized_preview),
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

    allowed_root = write_once_manifest.get("allowed_candidate_write_root", "")
    for entry in materialized_preview.get("preview_files", []):
        path = entry.get("path")
        if not isinstance(path, str) or not path.startswith(allowed_root) or ".." in path or path.startswith("/"):
            errors.append("materialized_preview path must stay inside allowed candidate write root")
        if entry.get("written_now") is not False:
            errors.append("materialized_preview files must not be written now")
        if entry.get("planned_for_later_write_gate") is not True:
            errors.append("materialized_preview files must be planned for later write gate")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_BLOCKED"
    result = "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_CREATED" if ok else "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_BLOCKED"

    if ok:
        write_json(root / WRITE_ONCE_MANIFEST_OUT, write_once_manifest)
        write_json(root / MATERIALIZED_PREVIEW_OUT, materialized_preview)
        write_json(root / D132_SCOPE_OUT, d132_scope)

    report = {
        "state": "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "write_once_id": write_once_id,
        "window_id": d130.get("window_id"),
        "runner_id": d130.get("runner_id"),
        "plan_id": d130.get("plan_id"),
        "review_id": d130.get("review_id"),
        "candidate_id": d130.get("candidate_id"),
        "intake_id": d130.get("intake_id"),
        "ping_id": d130.get("ping_id"),
        "config_id": d130.get("config_id"),
        "dashboard_id": d130.get("dashboard_id"),
        "adapter_id": d130.get("adapter_id"),
        "seal_id": d130.get("seal_id"),
        "proposal_id": d130.get("proposal_id"),
        "source_d130_report": D130_REPORT,
        "sandbox_candidate_write_once_manifest": write_once_manifest if ok else {},
        "sandbox_candidate_materialized_preview": materialized_preview if ok else {},
        "d132_scope": d132_scope if ok else {},
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
            "sandbox_candidate_write_once_scope_only": True,
            "write_once_manifest_only": True,
            "materialized_preview_only": True,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "approval_for_d132_static_validation_scope_only": ok,
            "approval_for_candidate_execution": False,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "write_once_id": write_once_id,
            "window_id": d130.get("window_id"),
            "runner_id": d130.get("runner_id"),
            "plan_id": d130.get("plan_id"),
            "review_id": d130.get("review_id"),
            "candidate_id": d130.get("candidate_id"),
            "adapter_id": d130.get("adapter_id"),
            "seal_id": d130.get("seal_id"),
            "proposal_id": d130.get("proposal_id"),
            "write_once_status": "WRITE_ONCE_SCOPE_ARMED_NOT_USED" if ok else "BLOCKED",
            "materialized_preview_status": "PREVIEW_CREATED_NO_CANDIDATE_WRITE" if ok else "BLOCKED",
            "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D132_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_write_once_scope_created": ok,
            "sandbox_candidate_write_once_manifest_created": ok,
            "sandbox_candidate_materialized_preview_created": ok,
            "d132_scope_created": ok,
            "candidate_files_written": False,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D132 may create sandbox candidate static validation scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_write_once_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_write_once_scope import create_sandbox_candidate_write_once_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD131SandboxCandidateWriteOnceScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

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

        d130 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_READY",
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
                "sandbox_candidate_write_window_scope_only": True,
                "write_window_manifest_only": True,
                "write_preflight_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d131_write_once_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "write_window_status": "WRITE_WINDOW_SCOPE_OPENED_NOT_USED",
                "write_preflight_status": "WRITE_PREFLIGHT_CREATED_NO_WRITE",
                "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_ONLY",
                "next_step": "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE",
            },
        }

        write_window_manifest = {
            "ok": True,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "manifest_mode": "WRITE_WINDOW_MANIFEST_ONLY_NO_CANDIDATE_WRITE",
            "write_window_status": "OPENED_FOR_D131_SCOPE_ONLY_NOT_USED",
            "allowed_candidate_write_root": candidate_root,
            "planned_candidate_files_for_later_gate": [
                f"{candidate_root}candidate_manifest.json",
                f"{candidate_root}candidate_summary.md",
                f"{candidate_root}candidate_payload.json",
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

        write_preflight = {
            "ok": True,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "preflight_mode": "WRITE_WINDOW_PREFLIGHT_ONLY_NO_CANDIDATE_WRITE",
            "preflight_status": "PASS_SCOPE_ONLY",
            "input_checks": {
                "d129_report_ready": True,
                "dry_results_ready": True,
                "integrity_diff_ready": True,
                "dry_results_no_execution": True,
                "integrity_no_git_diff_execution": True,
                "integrity_no_filesystem_scan_execution": True,
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

        d131_scope = {
            "ok": True,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE",
            "sandbox_candidate_write_once_scope_only": True,
            "human_review_required": True,
            "candidate_written_after_d130": False,
            "candidate_executed_after_d130_by_ai": False,
            "real_apply_allowed_after_d130_by_ai": False,
            "route_insert_allowed_after_d130_by_ai": False,
            "protected_core_mutation_allowed_after_d130_by_ai": False,
        }

        write(root / "reports/d130_sandbox_candidate_write_window_scope.json", d130)
        write(root / "reports/d130_sandbox_candidate_write_window_manifest.json", write_window_manifest)
        write(root / "reports/d130_sandbox_candidate_write_preflight.json", write_preflight)
        write(root / "reports/d130_d131_sandbox_candidate_write_once_scope.json", d131_scope)
        return td, root

    def test_creates_write_once_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_write_once_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_READY")
            self.assertEqual(r["summary"]["write_once_status"], "WRITE_ONCE_SCOPE_ARMED_NOT_USED")
            self.assertEqual(r["summary"]["approval_scope"], "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d132_scope"]["allowed_next_gate"], "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE")
            self.assertTrue((root / "reports/d131_sandbox_candidate_write_once_scope.json").exists())
            self.assertTrue((root / "reports/d131_sandbox_candidate_write_once_manifest.json").exists())
            self.assertTrue((root / "reports/d131_sandbox_candidate_materialized_preview.json").exists())
            self.assertTrue((root / "reports/d131_d132_sandbox_candidate_static_validation_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d130(self):
        td, root = self.root()
        try:
            (root / "reports/d130_sandbox_candidate_write_window_scope.json").unlink()
            r = create_sandbox_candidate_write_once_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_write_window_manifest_says_candidate_written(self):
        td, root = self.root()
        try:
            p = root / "reports/d130_sandbox_candidate_write_window_manifest.json"
            data = json.loads(p.read_text())
            data["candidate_files_written_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_write_once_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_write_preflight_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d130_sandbox_candidate_write_preflight.json"
            data = json.loads(p.read_text())
            data["route_inserted"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_write_once_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d131_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d130_d131_sandbox_candidate_write_once_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d130_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_write_once_scope(root)
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

print("D131 SANDBOX CANDIDATE WRITE ONCE SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_candidate_write_once_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d131_sandbox_candidate_write_once_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_candidate_write_once_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d131_sandbox_candidate_write_once_scope", "-v"], check=True)

print("\n== run D131 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.sandbox_candidate_write_once_scope import create_sandbox_candidate_write_once_scope\n"
    "r=create_sandbox_candidate_write_once_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d131_sandbox_candidate_write_once_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_candidate_write_once_scope.py",
    "tests/test_d131_sandbox_candidate_write_once_scope.py",
    "reports/d131_sandbox_candidate_write_once_scope.json",
    "reports/d131_sandbox_candidate_write_once_manifest.json",
    "reports/d131_sandbox_candidate_materialized_preview.json",
    "reports/d131_d132_sandbox_candidate_static_validation_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D131 sandbox candidate write once scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D131 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD131 SANDBOX CANDIDATE WRITE ONCE SCOPE BOOT DONE")
