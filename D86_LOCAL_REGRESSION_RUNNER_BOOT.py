#!/usr/bin/env python3
# D86_LOCAL_REGRESSION_RUNNER_BOOT.py
#
# Adds D86 Local Regression Runner to GitCube OS.
#
# Run from repo root:
#     python D86_LOCAL_REGRESSION_RUNNER_BOOT.py
#
# Creates:
# - runtime_experimental/local_regression_runner.py
# - tests/test_d86_local_regression_runner.py
# - reports/d86_local_regression_runner.json
# - reports/d86_local_regression_results.json
#
# D86 does NOT call an external AI API.
# D86 does NOT use network access.
# D86 does NOT execute raw code from AI.
# D86 does NOT run shell commands from AI.
# D86 does NOT patch task_dispatcher.py.
# D86 does NOT mutate protected core.
# D86 does NOT overwrite canonical memory.
# D86 does NOT insert a real route.
# D86 does NOT apply changes.
#
# D86 only runs a fixed local allowlist of regression/probe commands.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_CODE = json.loads("\"from __future__ import annotations\\n\\nimport json\\nimport subprocess\\nimport sys\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nD85_REPORT = \\\"reports/d85_regression_rollback_evidence.json\\\"\\nD85_ROLLBACK = \\\"reports/d85_rollback_manifest.json\\\"\\nD85_CHECKLIST = \\\"reports/d85_regression_checklist.json\\\"\\nOUT = \\\"reports/d86_local_regression_runner.json\\\"\\nRESULTS_OUT = \\\"reports/d86_local_regression_results.json\\\"\\n\\n\\nALLOWED_COMMANDS = [\\n    [sys.executable, \\\"-m\\\", \\\"py_compile\\\", \\\"runtime_experimental/sandbox_writer_output_review.py\\\"],\\n    [sys.executable, \\\"-m\\\", \\\"unittest\\\", \\\"tests.test_d84_sandbox_writer_output_review\\\", \\\"-v\\\"],\\n    [sys.executable, \\\"-m\\\", \\\"py_compile\\\", \\\"runtime_experimental/regression_rollback_evidence.py\\\"],\\n    [sys.executable, \\\"-m\\\", \\\"unittest\\\", \\\"tests.test_d85_regression_rollback_evidence\\\", \\\"-v\\\"],\\n]\\n\\n\\nFORBIDDEN_TOKENS = [\\n    \\\"rm\\\",\\n    \\\"git commit\\\",\\n    \\\"git push\\\",\\n    \\\"git clean -f\\\",\\n    \\\"git checkout\\\",\\n    \\\"git reset\\\",\\n    \\\"curl\\\",\\n    \\\"wget\\\",\\n    \\\"ssh\\\",\\n    \\\"python -c\\\",\\n    \\\"subprocess\\\",\\n    \\\"eval\\\",\\n    \\\"exec\\\",\\n]\\n\\n\\ndef now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef command_to_text(cmd: List[str]) -> str:\\n    return \\\" \\\".join(str(x) for x in cmd)\\n\\n\\ndef is_safe_command_text(command_text: str) -> bool:\\n    lowered = command_text.lower()\\n    return not any(token in lowered for token in FORBIDDEN_TOKENS)\\n\\n\\ndef validate_d85(\\n    d85: Dict[str, Any],\\n    rollback: Dict[str, Any],\\n    checklist: Dict[str, Any],\\n    errors: List[str],\\n) -> None:\\n    if not d85:\\n        errors.append(\\\"D85 report missing or unreadable\\\")\\n        return\\n\\n    if d85.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D85 ok flag is not true\\\")\\n    if d85.get(\\\"decision\\\") != \\\"REGRESSION_ROLLBACK_EVIDENCE_READY\\\":\\n        errors.append(f\\\"D85 decision invalid: {d85.get('decision')}\\\")\\n\\n    guard = d85.get(\\\"guardrails\\\") if isinstance(d85.get(\\\"guardrails\\\"), dict) else {}\\n    for key in (\\n        \\\"external_ai_called\\\",\\n        \\\"network_accessed\\\",\\n        \\\"runtime_code_mutated\\\",\\n        \\\"protected_core_mutated\\\",\\n        \\\"canonical_memory_mutated\\\",\\n        \\\"actual_apply_executed\\\",\\n        \\\"route_inserted\\\",\\n        \\\"git_commit_by_ai\\\",\\n    ):\\n        if guard.get(key) is not False:\\n            errors.append(f\\\"D85 guardrail {key} is not false\\\")\\n\\n    if guard.get(\\\"rollback_evidence_only\\\") is not True:\\n        errors.append(\\\"D85 rollback_evidence_only is not true\\\")\\n    if guard.get(\\\"regression_evidence_only\\\") is not True:\\n        errors.append(\\\"D85 regression_evidence_only is not true\\\")\\n\\n    if not rollback:\\n        errors.append(\\\"D85 rollback manifest missing or unreadable\\\")\\n    else:\\n        if rollback.get(\\\"human_review_required\\\") is not True:\\n            errors.append(\\\"D85 rollback human_review_required is not true\\\")\\n        for key in (\\\"actual_rollback_executed\\\", \\\"actual_apply_executed\\\", \\\"route_inserted\\\", \\\"protected_core_touched\\\"):\\n            if rollback.get(key) is not False:\\n                errors.append(f\\\"D85 rollback {key} is not false\\\")\\n\\n    if not checklist:\\n        errors.append(\\\"D85 regression checklist missing or unreadable\\\")\\n    else:\\n        pass_condition = checklist.get(\\\"pass_condition\\\") if isinstance(checklist.get(\\\"pass_condition\\\"), dict) else {}\\n        for key in (\\n            \\\"all_tests_green\\\",\\n            \\\"rollback_manifest_present\\\",\\n            \\\"no_protected_core_mutation\\\",\\n            \\\"no_route_insert\\\",\\n            \\\"no_actual_apply\\\",\\n        ):\\n            if pass_condition.get(key) is not True:\\n                errors.append(f\\\"D85 checklist pass condition {key} is not true\\\")\\n\\n\\ndef run_local_command(cmd: List[str], cwd: Path, timeout: int = 60) -> Dict[str, Any]:\\n    command_text = command_to_text(cmd)\\n\\n    if not is_safe_command_text(command_text):\\n        return {\\n            \\\"command\\\": command_text,\\n            \\\"ok\\\": False,\\n            \\\"returncode\\\": None,\\n            \\\"stdout_tail\\\": \\\"\\\",\\n            \\\"stderr_tail\\\": \\\"blocked by D86 safety filter\\\",\\n            \\\"duration_timeout_seconds\\\": timeout,\\n        }\\n\\n    try:\\n        completed = subprocess.run(\\n            cmd,\\n            cwd=str(cwd),\\n            text=True,\\n            capture_output=True,\\n            timeout=timeout,\\n            check=False,\\n        )\\n        return {\\n            \\\"command\\\": command_text,\\n            \\\"ok\\\": completed.returncode == 0,\\n            \\\"returncode\\\": completed.returncode,\\n            \\\"stdout_tail\\\": completed.stdout[-4000:],\\n            \\\"stderr_tail\\\": completed.stderr[-4000:],\\n            \\\"duration_timeout_seconds\\\": timeout,\\n        }\\n    except subprocess.TimeoutExpired as exc:\\n        return {\\n            \\\"command\\\": command_text,\\n            \\\"ok\\\": False,\\n            \\\"returncode\\\": None,\\n            \\\"stdout_tail\\\": (exc.stdout or \\\"\\\")[-4000:] if isinstance(exc.stdout, str) else \\\"\\\",\\n            \\\"stderr_tail\\\": \\\"command timed out\\\",\\n            \\\"duration_timeout_seconds\\\": timeout,\\n        }\\n    except Exception as exc:\\n        return {\\n            \\\"command\\\": command_text,\\n            \\\"ok\\\": False,\\n            \\\"returncode\\\": None,\\n            \\\"stdout_tail\\\": \\\"\\\",\\n            \\\"stderr_tail\\\": repr(exc),\\n            \\\"duration_timeout_seconds\\\": timeout,\\n        }\\n\\n\\ndef create_local_regression_runner(\\n    root: str | Path = \\\".\\\",\\n    d85_report_path: str = D85_REPORT,\\n    d85_rollback_path: str = D85_ROLLBACK,\\n    d85_checklist_path: str = D85_CHECKLIST,\\n    output_path: str = OUT,\\n    results_output_path: str = RESULTS_OUT,\\n    execute_commands: bool = True,\\n) -> Dict[str, Any]:\\n    root = Path(root).resolve()\\n\\n    d85 = read_json(root / d85_report_path, {}) or {}\\n    rollback = read_json(root / d85_rollback_path, {}) or {}\\n    checklist = read_json(root / d85_checklist_path, {}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    validate_d85(d85, rollback, checklist, errors)\\n\\n    command_results: List[Dict[str, Any]] = []\\n    if not errors:\\n        for cmd in ALLOWED_COMMANDS:\\n            if execute_commands:\\n                command_results.append(run_local_command(cmd, cwd=root))\\n            else:\\n                command_results.append(\\n                    {\\n                        \\\"command\\\": command_to_text(cmd),\\n                        \\\"ok\\\": True,\\n                        \\\"returncode\\\": 0,\\n                        \\\"stdout_tail\\\": \\\"skipped execution in test mode\\\",\\n                        \\\"stderr_tail\\\": \\\"\\\",\\n                        \\\"duration_timeout_seconds\\\": 60,\\n                    }\\n                )\\n\\n    failing = [r for r in command_results if r.get(\\\"ok\\\") is not True]\\n    if failing:\\n        errors.append(f\\\"{len(failing)} local regression command(s) failed\\\")\\n\\n    ok = not errors\\n    decision = \\\"LOCAL_REGRESSION_PASSED\\\" if ok else \\\"LOCAL_REGRESSION_BLOCKED\\\"\\n    result = \\\"D86_LOCAL_REGRESSION_RESULTS_CREATED\\\" if ok else \\\"D86_LOCAL_REGRESSION_RESULTS_BLOCKED\\\"\\n\\n    package_id = str(d85.get(\\\"package_id\\\") or rollback.get(\\\"package_id\\\") or \\\"\\\")\\n    review_id = str((d85.get(\\\"evidence\\\") or {}).get(\\\"review_id\\\") or d85.get(\\\"review_id\\\") or \\\"\\\")\\n\\n    results = {\\n        \\\"state\\\": \\\"D86_LOCAL_REGRESSION_RESULTS\\\",\\n        \\\"ok\\\": ok,\\n        \\\"created_at\\\": now(),\\n        \\\"package_id\\\": package_id,\\n        \\\"review_id\\\": review_id,\\n        \\\"commands_allowed_count\\\": len(ALLOWED_COMMANDS),\\n        \\\"commands_run_count\\\": len(command_results),\\n        \\\"commands_passed_count\\\": len([r for r in command_results if r.get(\\\"ok\\\") is True]),\\n        \\\"commands_failed_count\\\": len(failing),\\n        \\\"command_results\\\": command_results,\\n        \\\"actual_apply_executed\\\": False,\\n        \\\"route_inserted\\\": False,\\n        \\\"protected_core_touched\\\": False,\\n        \\\"network_accessed\\\": False,\\n        \\\"external_ai_called\\\": False,\\n    }\\n\\n    if ok:\\n        write_json(root / results_output_path, results)\\n\\n    report = {\\n        \\\"state\\\": \\\"D86_LOCAL_REGRESSION_RUNNER\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_LOCAL_REGRESSION_RUNNER\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": now(),\\n        \\\"package_id\\\": package_id,\\n        \\\"review_id\\\": review_id,\\n        \\\"results_path\\\": str(root / results_output_path) if ok else \\\"\\\",\\n        \\\"input_reports\\\": {\\n            \\\"d85_report_path\\\": str(root / d85_report_path),\\n            \\\"d85_rollback_path\\\": str(root / d85_rollback_path),\\n            \\\"d85_checklist_path\\\": str(root / d85_checklist_path),\\n        },\\n        \\\"regression_results\\\": results,\\n        \\\"guardrails\\\": {\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n            \\\"local_regression_only\\\": True,\\n            \\\"allowlisted_commands_only\\\": True,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"package_id\\\": package_id,\\n            \\\"review_id\\\": review_id,\\n            \\\"commands_run_count\\\": len(command_results),\\n            \\\"commands_failed_count\\\": len(failing),\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"local_regression_results_created\\\": ok,\\n            \\\"all_local_regression_commands_passed\\\": ok,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D87 can assemble final pre-apply safety capsule; real apply remains blocked until explicit higher approval.\\\",\\n        },\\n    }\\n\\n    write_json(root / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(create_local_regression_runner(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.local_regression_runner import create_local_regression_runner\\n\\n\\nclass TestD86LocalRegressionRunner(unittest.TestCase):\\n    def make_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n\\n        (root / \\\"reports/d85_regression_rollback_evidence.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"REGRESSION_ROLLBACK_EVIDENCE_READY\\\",\\n                    \\\"package_id\\\": \\\"d85-test-package\\\",\\n                    \\\"evidence\\\": {\\\"review_id\\\": \\\"d84-test-review\\\"},\\n                    \\\"guardrails\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                        \\\"rollback_evidence_only\\\": True,\\n                        \\\"regression_evidence_only\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d85_rollback_manifest.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"package_id\\\": \\\"d85-test-package\\\",\\n                    \\\"human_review_required\\\": True,\\n                    \\\"actual_rollback_executed\\\": False,\\n                    \\\"actual_apply_executed\\\": False,\\n                    \\\"route_inserted\\\": False,\\n                    \\\"protected_core_touched\\\": False,\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d85_regression_checklist.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"package_id\\\": \\\"d85-test-package\\\",\\n                    \\\"pass_condition\\\": {\\n                        \\\"all_tests_green\\\": True,\\n                        \\\"rollback_manifest_present\\\": True,\\n                        \\\"no_protected_core_mutation\\\": True,\\n                        \\\"no_route_insert\\\": True,\\n                        \\\"no_actual_apply\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        return td, root\\n\\n    def test_creates_local_regression_results(self):\\n        td, root = self.make_root()\\n        try:\\n            report = create_local_regression_runner(root=root, execute_commands=False)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"LOCAL_REGRESSION_PASSED\\\")\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"allowlisted_commands_only\\\"])\\n            self.assertFalse(report[\\\"guardrails\\\"][\\\"actual_apply_executed\\\"])\\n            self.assertEqual(report[\\\"summary\\\"][\\\"commands_failed_count\\\"], 0)\\n            self.assertTrue((root / \\\"reports/d86_local_regression_runner.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d86_local_regression_results.json\\\").exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d85(self):\\n        td, root = self.make_root()\\n        try:\\n            (root / \\\"reports/d85_regression_rollback_evidence.json\\\").unlink()\\n            report = create_local_regression_runner(root=root, execute_commands=False)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"LOCAL_REGRESSION_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_d85_apply_flag(self):\\n        td, root = self.make_root()\\n        try:\\n            p = root / \\\"reports/d85_regression_rollback_evidence.json\\\"\\n            data = json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n            data[\\\"guardrails\\\"][\\\"actual_apply_executed\\\"] = True\\n            p.write_text(json.dumps(data), encoding=\\\"utf-8\\\")\\n\\n            report = create_local_regression_runner(root=root, execute_commands=False)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"LOCAL_REGRESSION_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


def sh(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, text=True, capture_output=False, check=check)


def find_repo_root() -> Path:
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p
    return here


ROOT = find_repo_root()
os.chdir(ROOT)

Path("runtime_experimental").mkdir(parents=True, exist_ok=True)
Path("tests").mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(parents=True, exist_ok=True)

print("D86 LOCAL REGRESSION RUNNER BOOT: repo =", ROOT)

Path("runtime_experimental/local_regression_runner.py").write_text(MODULE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/local_regression_runner.py")

Path("tests/test_d86_local_regression_runner.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d86_local_regression_runner.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/local_regression_runner.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d86_local_regression_runner", "-v"], check=True)

print("\n== run D86 local regression runner ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.local_regression_runner import create_local_regression_runner\n"
        "r=create_local_regression_runner()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d86_local_regression_runner.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== results preview ==")
res = Path("reports/d86_local_regression_results.json")
if res.exists():
    data = json.loads(res.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("COMMANDS_RUN:", data.get("commands_run_count"))
    print("COMMANDS_PASSED:", data.get("commands_passed_count"))
    print("COMMANDS_FAILED:", data.get("commands_failed_count"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/local_regression_runner.py",
    "tests/test_d86_local_regression_runner.py",
    "reports/d86_local_regression_runner.json",
    "reports/d86_local_regression_results.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D86_LOCAL_REGRESSION_RUNNER_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D86 local regression runner"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D86 local regression runner changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD86 LOCAL REGRESSION RUNNER BOOT DONE")
