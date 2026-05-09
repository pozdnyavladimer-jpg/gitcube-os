
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

D108_REPORT = "reports/d108_sandbox_proposal_writer.json"
D108_MANIFEST = "reports/d108_sandbox_proposal_manifest.json"
D108_RECEIPT = "reports/d108_writer_receipt.json"
D108_D109_SCOPE = "reports/d108_d109_regression_runner_scope.json"
D108_SANDBOX_PROPOSAL = "runtime_experimental/ai_sandbox_work/d108_accepted_proposal.json"

OUT = "reports/d109_regression_runner.json"
STATIC_CHECKS_OUT = "reports/d109_sandbox_static_checks.json"
REGRESSION_RESULTS_OUT = "reports/d109_sandbox_regression_results.json"
DIFF_SUMMARY_OUT = "reports/d109_sandbox_diff_summary.json"
D110_SCOPE_OUT = "reports/d109_d110_human_review_gate_scope.json"

REQ_D108_DECISION = "SANDBOX_PROPOSAL_WRITER_READY"
REQ_D109_GATE = "D109_REGRESSION_RUNNER"
REQ_D110_GATE = "D110_HUMAN_REVIEW_GATE"

BLOCKED_PREFIXES = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]

SAFE_COMMANDS = [
    [sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_proposal_writer.py"],
    [sys.executable, "-m", "py_compile", "runtime_experimental/proposal_schema_validator.py"],
    [sys.executable, "-m", "py_compile", "runtime_experimental/ai_propose_only_provider_boundary.py"],
    [sys.executable, "-m", "unittest", "tests.test_d108_sandbox_proposal_writer", "-v"],
    [sys.executable, "-m", "unittest", "tests.test_d107_proposal_schema_validator", "-v"],
    [sys.executable, "-m", "unittest", "tests.test_d106_ai_propose_only_provider_boundary", "-v"],
]

OPTIONAL_GIT_COMMANDS = [
    ["git", "diff", "--stat"],
    ["git", "status", "--short"],
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


def starts(path, prefixes):
    return any(str(path).startswith(prefix) for prefix in prefixes)


def run_command(cmd, timeout=90):
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {
            "command": " ".join(cmd),
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout_tail": p.stdout[-3000:],
            "stderr_tail": p.stderr[-3000:],
            "duration_timeout_seconds": timeout,
        }
    except Exception as exc:
        return {
            "command": " ".join(cmd),
            "ok": False,
            "returncode": -1,
            "stdout_tail": "",
            "stderr_tail": repr(exc),
            "duration_timeout_seconds": timeout,
        }


def validate_d108(d108, manifest, receipt, scope, sandbox_proposal):
    errors = []

    if not d108:
        errors.append("missing D108 report")
        return errors

    if d108.get("ok") is not True:
        errors.append("D108 ok must be true")
    if d108.get("decision") != REQ_D108_DECISION:
        errors.append("D108 decision must be SANDBOX_PROPOSAL_WRITER_READY")

    guard = d108.get("guardrails", {})
    for key in [
        "external_ai_called",
        "network_accessed",
        "api_key_read",
        "secret_read",
        "shell_executed",
        "runtime_code_mutated",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "actual_apply_executed",
        "route_inserted",
        "git_commit_by_ai",
        "rollback_executed",
        "restore_executed",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D108 guardrails.{key} must be false")
    for key in ["sandbox_write_only", "proposal_json_copy_only"]:
        if guard.get(key) is not True:
            errors.append(f"D108 guardrails.{key} must be true")
    if guard.get("candidate_execution_allowed") is not False:
        errors.append("D108 candidate_execution_allowed must be false")

    if not manifest:
        errors.append("missing D108 manifest")
    else:
        if manifest.get("ok") is not True:
            errors.append("D108 manifest ok must be true")
        for key in [
            "actual_apply_executed",
            "candidate_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
        ]:
            if manifest.get(key) is not False:
                errors.append(f"D108 manifest {key} must be false")
        for f in manifest.get("sandbox_files", []):
            if starts(f, BLOCKED_PREFIXES):
                errors.append(f"D108 manifest contains blocked path: {f}")

    if not receipt:
        errors.append("missing D108 writer receipt")
    else:
        if receipt.get("ok") is not True:
            errors.append("D108 receipt ok must be true")
        for key in [
            "external_ai_called",
            "network_accessed",
            "shell_executed",
            "actual_apply_executed",
            "candidate_executed",
            "git_commit_by_ai",
        ]:
            if receipt.get(key) is not False:
                errors.append(f"D108 receipt {key} must be false")

    if not scope:
        errors.append("missing D108 D109 scope")
    else:
        if scope.get("ok") is not True:
            errors.append("D108 D109 scope ok must be true")
        if scope.get("allowed_next_gate") != REQ_D109_GATE:
            errors.append("D108 D109 scope allowed_next_gate must be D109")
        for key in [
            "actual_apply_allowed_after_d108",
            "route_insert_allowed_after_d108",
            "protected_core_mutation_allowed_after_d108",
            "sandbox_candidate_execution_allowed_after_d108",
        ]:
            if scope.get(key) is not False:
                errors.append(f"D108 scope {key} must be false")

    if not sandbox_proposal:
        errors.append("missing D108 sandbox proposal copy")
    else:
        if sandbox_proposal.get("ok") is not True:
            errors.append("D108 sandbox proposal copy ok must be true")
        if sandbox_proposal.get("sandbox_copy_only") is not True:
            errors.append("D108 sandbox proposal must be copy only")
        if sandbox_proposal.get("actual_apply_executed") is not False:
            errors.append("D108 sandbox proposal actual_apply_executed must be false")
        if sandbox_proposal.get("candidate_executed") is not False:
            errors.append("D108 sandbox proposal candidate_executed must be false")

    return errors


def build_static_checks(root, runner_id, d108, manifest, receipt, sandbox_proposal):
    sandbox_files = list(manifest.get("sandbox_files", [])) if isinstance(manifest, dict) else []
    files_to_check = sorted(set(sandbox_files + [D108_SANDBOX_PROPOSAL]))
    existing = []
    missing = []
    blocked = []

    for item in files_to_check:
        if starts(item, BLOCKED_PREFIXES):
            blocked.append(item)
        if (Path(root) / item).exists():
            existing.append(item)
        else:
            missing.append(item)

    return {
        "state": "D109_SANDBOX_STATIC_CHECKS",
        "ok": not missing and not blocked,
        "runner_id": runner_id,
        "created_at": now(),
        "sandbox_files_declared": sandbox_files,
        "existing_files": existing,
        "missing_files": missing,
        "blocked_paths_detected": blocked,
        "json_integrity": {
            "d108_report_loaded": bool(d108),
            "manifest_loaded": bool(manifest),
            "receipt_loaded": bool(receipt),
            "sandbox_proposal_loaded": bool(sandbox_proposal),
        },
        "actual_apply_executed": False,
        "candidate_executed": False,
        "protected_core_mutated": False,
        "route_inserted": False,
    }


def build_diff_summary(runner_id, command_results):
    diff = next((x for x in command_results if x.get("command") == "git diff --stat"), None)
    status = next((x for x in command_results if x.get("command") == "git status --short"), None)
    return {
        "state": "D109_SANDBOX_DIFF_SUMMARY",
        "ok": True,
        "runner_id": runner_id,
        "created_at": now(),
        "git_diff_stat": diff or {},
        "git_status_short": status or {},
        "documentation_only": True,
        "actual_apply_executed": False,
        "candidate_executed": False,
    }


def build_d110_scope(runner_id, regression_ok, static_ok):
    return {
        "state": "D109_D110_HUMAN_REVIEW_GATE_SCOPE",
        "ok": regression_ok and static_ok,
        "runner_id": runner_id,
        "created_at": now(),
        "allowed_next_gate": REQ_D110_GATE,
        "d110_allowed_to_create": [
            "human_review_gate",
            "human_review_packet",
            "proposal_review_summary",
            "approval_or_rejection_record",
        ],
        "d110_must_not_execute": [
            "real_apply",
            "auto_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "shell_exec_from_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute",
            "restore_execute",
            "apply_sandbox_candidate",
            "execute_sandbox_candidate",
            "commit_sandbox_candidate",
        ],
        "human_review_required": True,
        "actual_apply_allowed_after_d109": False,
        "route_insert_allowed_after_d109": False,
        "protected_core_mutation_allowed_after_d109": False,
        "sandbox_candidate_execution_allowed_after_d109": False,
        "required_phrase_for_later_gate": "APPROVE_D110_HUMAN_REVIEW_GATE_ONLY",
    }


def create_regression_runner(root=".", execute_commands=True):
    root = Path(root).resolve()

    d108 = read_json(root / D108_REPORT, {}) or {}
    manifest = read_json(root / D108_MANIFEST, {}) or {}
    receipt = read_json(root / D108_RECEIPT, {}) or {}
    scope = read_json(root / D108_D109_SCOPE, {}) or {}
    sandbox_proposal = read_json(root / D108_SANDBOX_PROPOSAL, {}) or {}

    errors = validate_d108(d108, manifest, receipt, scope, sandbox_proposal)
    runner_id = "d109-" + digest({
        "writer_id": d108.get("writer_id"),
        "validator_id": d108.get("validator_id"),
        "proposal_id": d108.get("proposal_id"),
    })

    command_results = []
    if execute_commands and not errors:
        for cmd in SAFE_COMMANDS:
            command_results.append(run_command(cmd))
        for cmd in OPTIONAL_GIT_COMMANDS:
            command_results.append(run_command(cmd))
    else:
        command_results.append({
            "command": "commands_skipped",
            "ok": not errors,
            "returncode": 0 if not errors else 1,
            "stdout_tail": "execute_commands disabled or input validation failed",
            "stderr_tail": "",
        })

    regression_ok = all(x.get("ok") is True for x in command_results)
    static_checks = build_static_checks(root, runner_id, d108, manifest, receipt, sandbox_proposal)
    static_ok = static_checks.get("ok") is True

    if not regression_ok:
        errors.append("one or more safe regression commands failed")
    if not static_ok:
        errors.append("sandbox static checks failed")

    ok = not errors
    decision = "REGRESSION_RUNNER_READY" if ok else "REGRESSION_RUNNER_BLOCKED"
    result = "D109_REGRESSION_RUNNER_CREATED" if ok else "D109_REGRESSION_RUNNER_BLOCKED"

    regression_results = {
        "state": "D109_SANDBOX_REGRESSION_RESULTS",
        "ok": regression_ok,
        "runner_id": runner_id,
        "created_at": now(),
        "commands": command_results,
        "commands_count": len(command_results),
        "passed_count": sum(1 for x in command_results if x.get("ok") is True),
        "failed_count": sum(1 for x in command_results if x.get("ok") is not True),
        "actual_apply_executed": False,
        "candidate_executed": False,
        "shell_from_ai_executed": False,
    }

    diff_summary = build_diff_summary(runner_id, command_results)
    d110_scope = build_d110_scope(runner_id, regression_ok, static_ok)

    if ok:
        write_json(root / STATIC_CHECKS_OUT, static_checks)
        write_json(root / REGRESSION_RESULTS_OUT, regression_results)
        write_json(root / DIFF_SUMMARY_OUT, diff_summary)
        write_json(root / D110_SCOPE_OUT, d110_scope)

    report = {
        "state": "D109_REGRESSION_RUNNER",
        "result": result,
        "route": "FIELD_INTENT_REGRESSION_RUNNER",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "runner_id": runner_id,
        "writer_id": d108.get("writer_id"),
        "validator_id": d108.get("validator_id"),
        "proposal_id": d108.get("proposal_id"),
        "source_d108_report": D108_REPORT,
        "static_checks": static_checks,
        "regression_results": regression_results,
        "diff_summary": diff_summary,
        "d110_scope": d110_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "safe_local_commands_executed": execute_commands and not bool(errors),
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
            "sandbox_regression_only": True,
            "candidate_execution_allowed": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": [],
        },
        "summary": {
            "decision": decision,
            "runner_id": runner_id,
            "writer_id": d108.get("writer_id"),
            "proposal_id": d108.get("proposal_id"),
            "regression_ok": regression_ok,
            "static_ok": static_ok,
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D110_GATE,
        },
        "success_condition": {
            "regression_runner_created": ok,
            "static_checks_created": ok,
            "regression_results_created": ok,
            "diff_summary_created": ok,
            "d110_scope_created": ok,
            "real_ai_called": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "protected_core_untouched": True,
            "next_step": "D110 may create human review packet only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_regression_runner(), ensure_ascii=False, indent=2))
