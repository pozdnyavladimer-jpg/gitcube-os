from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


D85_REPORT = "reports/d85_regression_rollback_evidence.json"
D85_ROLLBACK = "reports/d85_rollback_manifest.json"
D85_CHECKLIST = "reports/d85_regression_checklist.json"
OUT = "reports/d86_local_regression_runner.json"
RESULTS_OUT = "reports/d86_local_regression_results.json"


ALLOWED_COMMANDS = [
    [sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_writer_output_review.py"],
    [sys.executable, "-m", "unittest", "tests.test_d84_sandbox_writer_output_review", "-v"],
    [sys.executable, "-m", "py_compile", "runtime_experimental/regression_rollback_evidence.py"],
    [sys.executable, "-m", "unittest", "tests.test_d85_regression_rollback_evidence", "-v"],
]


FORBIDDEN_TOKENS = [
    "rm",
    "git commit",
    "git push",
    "git clean -f",
    "git checkout",
    "git reset",
    "curl",
    "wget",
    "ssh",
    "python -c",
    "subprocess",
    "eval",
    "exec",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def command_to_text(cmd: List[str]) -> str:
    return " ".join(str(x) for x in cmd)


def is_safe_command_text(command_text: str) -> bool:
    lowered = command_text.lower()
    return not any(token in lowered for token in FORBIDDEN_TOKENS)


def validate_d85(
    d85: Dict[str, Any],
    rollback: Dict[str, Any],
    checklist: Dict[str, Any],
    errors: List[str],
) -> None:
    if not d85:
        errors.append("D85 report missing or unreadable")
        return

    if d85.get("ok") is not True:
        errors.append("D85 ok flag is not true")
    if d85.get("decision") != "REGRESSION_ROLLBACK_EVIDENCE_READY":
        errors.append(f"D85 decision invalid: {d85.get('decision')}")

    guard = d85.get("guardrails") if isinstance(d85.get("guardrails"), dict) else {}
    for key in (
        "external_ai_called",
        "network_accessed",
        "runtime_code_mutated",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "actual_apply_executed",
        "route_inserted",
        "git_commit_by_ai",
    ):
        if guard.get(key) is not False:
            errors.append(f"D85 guardrail {key} is not false")

    if guard.get("rollback_evidence_only") is not True:
        errors.append("D85 rollback_evidence_only is not true")
    if guard.get("regression_evidence_only") is not True:
        errors.append("D85 regression_evidence_only is not true")

    if not rollback:
        errors.append("D85 rollback manifest missing or unreadable")
    else:
        if rollback.get("human_review_required") is not True:
            errors.append("D85 rollback human_review_required is not true")
        for key in ("actual_rollback_executed", "actual_apply_executed", "route_inserted", "protected_core_touched"):
            if rollback.get(key) is not False:
                errors.append(f"D85 rollback {key} is not false")

    if not checklist:
        errors.append("D85 regression checklist missing or unreadable")
    else:
        pass_condition = checklist.get("pass_condition") if isinstance(checklist.get("pass_condition"), dict) else {}
        for key in (
            "all_tests_green",
            "rollback_manifest_present",
            "no_protected_core_mutation",
            "no_route_insert",
            "no_actual_apply",
        ):
            if pass_condition.get(key) is not True:
                errors.append(f"D85 checklist pass condition {key} is not true")


def run_local_command(cmd: List[str], cwd: Path, timeout: int = 60) -> Dict[str, Any]:
    command_text = command_to_text(cmd)

    if not is_safe_command_text(command_text):
        return {
            "command": command_text,
            "ok": False,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": "blocked by D86 safety filter",
            "duration_timeout_seconds": timeout,
        }

    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command_text,
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
            "duration_timeout_seconds": timeout,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command_text,
            "ok": False,
            "returncode": None,
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": "command timed out",
            "duration_timeout_seconds": timeout,
        }
    except Exception as exc:
        return {
            "command": command_text,
            "ok": False,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": repr(exc),
            "duration_timeout_seconds": timeout,
        }


def create_local_regression_runner(
    root: str | Path = ".",
    d85_report_path: str = D85_REPORT,
    d85_rollback_path: str = D85_ROLLBACK,
    d85_checklist_path: str = D85_CHECKLIST,
    output_path: str = OUT,
    results_output_path: str = RESULTS_OUT,
    execute_commands: bool = True,
) -> Dict[str, Any]:
    root = Path(root).resolve()

    d85 = read_json(root / d85_report_path, {}) or {}
    rollback = read_json(root / d85_rollback_path, {}) or {}
    checklist = read_json(root / d85_checklist_path, {}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    validate_d85(d85, rollback, checklist, errors)

    command_results: List[Dict[str, Any]] = []
    if not errors:
        for cmd in ALLOWED_COMMANDS:
            if execute_commands:
                command_results.append(run_local_command(cmd, cwd=root))
            else:
                command_results.append(
                    {
                        "command": command_to_text(cmd),
                        "ok": True,
                        "returncode": 0,
                        "stdout_tail": "skipped execution in test mode",
                        "stderr_tail": "",
                        "duration_timeout_seconds": 60,
                    }
                )

    failing = [r for r in command_results if r.get("ok") is not True]
    if failing:
        errors.append(f"{len(failing)} local regression command(s) failed")

    ok = not errors
    decision = "LOCAL_REGRESSION_PASSED" if ok else "LOCAL_REGRESSION_BLOCKED"
    result = "D86_LOCAL_REGRESSION_RESULTS_CREATED" if ok else "D86_LOCAL_REGRESSION_RESULTS_BLOCKED"

    package_id = str(d85.get("package_id") or rollback.get("package_id") or "")
    review_id = str((d85.get("evidence") or {}).get("review_id") or d85.get("review_id") or "")

    results = {
        "state": "D86_LOCAL_REGRESSION_RESULTS",
        "ok": ok,
        "created_at": now(),
        "package_id": package_id,
        "review_id": review_id,
        "commands_allowed_count": len(ALLOWED_COMMANDS),
        "commands_run_count": len(command_results),
        "commands_passed_count": len([r for r in command_results if r.get("ok") is True]),
        "commands_failed_count": len(failing),
        "command_results": command_results,
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_touched": False,
        "network_accessed": False,
        "external_ai_called": False,
    }

    if ok:
        write_json(root / results_output_path, results)

    report = {
        "state": "D86_LOCAL_REGRESSION_RUNNER",
        "result": result,
        "route": "FIELD_INTENT_LOCAL_REGRESSION_RUNNER",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "package_id": package_id,
        "review_id": review_id,
        "results_path": str(root / results_output_path) if ok else "",
        "input_reports": {
            "d85_report_path": str(root / d85_report_path),
            "d85_rollback_path": str(root / d85_rollback_path),
            "d85_checklist_path": str(root / d85_checklist_path),
        },
        "regression_results": results,
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "local_regression_only": True,
            "allowlisted_commands_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "package_id": package_id,
            "review_id": review_id,
            "commands_run_count": len(command_results),
            "commands_failed_count": len(failing),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "local_regression_results_created": ok,
            "all_local_regression_commands_passed": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D87 can assemble final pre-apply safety capsule; real apply remains blocked until explicit higher approval.",
        },
    }

    write_json(root / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_local_regression_runner(), ensure_ascii=False, indent=2))
