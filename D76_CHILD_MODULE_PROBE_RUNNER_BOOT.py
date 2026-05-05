#!/usr/bin/env python3
# D76_CHILD_MODULE_PROBE_RUNNER_BOOT.py
# Safe rebuild: avoids nested triple-quote syntax issue.
# Run from repo root:
#   python D76_CHILD_MODULE_PROBE_RUNNER_BOOT.py

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

RUNNER_CODE = r'''
from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_D75_REPORT = "reports/d75_differentiation_scaffold_package.json"
DEFAULT_OUTPUT = "reports/d76_child_module_probe_report.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_relative_path(path_value: str) -> str:
    raw = str(path_value or "").strip().replace("\\", "/").lstrip("/")
    parts: List[str] = []
    for part in raw.split("/"):
        if not part or part == "." or part == "..":
            continue
        parts.append(part)
    return "/".join(parts)


def _load_module_from_path(path: Path):
    spec = importlib.util.spec_from_file_location("d76_child_probe_target", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_probe_result(result: Dict[str, Any], errors: List[str]) -> None:
    if not isinstance(result, dict):
        errors.append("child probe result is not a dict")
        return
    if result.get("ok") is not True:
        errors.append("child probe ok flag is not true")

    guardrails = result.get("guardrails") if isinstance(result.get("guardrails"), dict) else {}
    for key in (
        "protected_core_mutated",
        "canonical_memory_mutated",
        "external_ai_called",
        "actual_apply_executed",
    ):
        if guardrails.get(key) is not False:
            errors.append(f"child probe guardrail {key} is not false")

    if guardrails.get("sandbox_only") is not True:
        errors.append("child probe sandbox_only is not true")


def _validate_contract(contract: Dict[str, Any], errors: List[str]) -> None:
    if not isinstance(contract, dict):
        errors.append("child route contract is not a dict")
        return
    if contract.get("ok") is not True:
        errors.append("child route contract ok flag is not true")
    if contract.get("allowed_mode") != "SANDBOX_PROBE_ONLY":
        errors.append(f"child route contract allowed_mode is not SANDBOX_PROBE_ONLY: {contract.get('allowed_mode')}")

    forbidden = contract.get("forbidden_actions")
    if not isinstance(forbidden, list):
        errors.append("child route contract forbidden_actions is not a list")
    else:
        for action in ("direct_core_edit", "overwrite_canonical_memory", "auto_apply_runtime_mutation"):
            if action not in forbidden:
                errors.append(f"child route contract missing forbidden action: {action}")

    required = contract.get("required_before_integration")
    if not isinstance(required, list):
        errors.append("child route contract required_before_integration is not a list")
    else:
        for gate in ("D66_RECHECK", "UNIT_TESTS", "REGRESSION_TESTS", "ROLLBACK_MANIFEST"):
            if gate not in required:
                errors.append(f"child route contract missing required gate: {gate}")


def run_child_module_probe(
    root: str | Path = ".",
    d75_report_path: str = DEFAULT_D75_REPORT,
    output_path: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()
    d75 = _read_json(root_path / d75_report_path, default={}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    if not d75:
        errors.append("D75 scaffold package report missing or unreadable")
    else:
        if d75.get("ok") is not True:
            errors.append("D75 ok flag is not true")
        if d75.get("decision") != "DIFFERENTIATION_SCAFFOLD_READY":
            errors.append(f"D75 decision is not DIFFERENTIATION_SCAFFOLD_READY: {d75.get('decision')}")
        guardrails = d75.get("guardrails") if isinstance(d75.get("guardrails"), dict) else {}
        if guardrails.get("actual_apply_executed") is not False:
            errors.append("D75 actual_apply_executed is not false")
        if guardrails.get("scaffold_only") is not True:
            errors.append("D75 scaffold_only is not true")

    pkg = d75.get("scaffold_package") if isinstance(d75.get("scaffold_package"), dict) else {}
    child_path = _safe_relative_path(str(pkg.get("child_module_path", "")))
    test_path = _safe_relative_path(str(pkg.get("test_module_path", "")))

    if not child_path:
        errors.append("D75 child_module_path is missing")
    if child_path and not child_path.startswith("runtime_experimental/differentiated_modules/"):
        errors.append(f"D76 rejected child path outside differentiated_modules: {child_path}")

    child_abs = root_path / child_path if child_path else root_path / "__missing_child__.py"
    if child_path and not child_abs.exists():
        errors.append(f"D75 child module does not exist on disk: {child_path}")

    module_description: Dict[str, Any] = {}
    probe_result: Dict[str, Any] = {}
    route_contract: Dict[str, Any] = {}

    if not errors:
        try:
            module = _load_module_from_path(child_abs)

            describe = getattr(module, "describe_module", None)
            if callable(describe):
                value = describe()
                module_description = value if isinstance(value, dict) else {}
            else:
                warnings.append("child module has no describe_module function")

            probe = getattr(module, "run_sandbox_probe", None)
            if not callable(probe):
                errors.append("child module has no callable run_sandbox_probe")
            else:
                value = probe({"kind": "D76_CHILD_MODULE_PROBE", "source": "D76"})
                probe_result = value if isinstance(value, dict) else {}
                _validate_probe_result(probe_result, errors)

            contract_fn = getattr(module, "propose_route_contract", None)
            if not callable(contract_fn):
                errors.append("child module has no callable propose_route_contract")
            else:
                value = contract_fn({"kind": "D76_ROUTE_CONTRACT_PROBE", "source": "D76"})
                route_contract = value if isinstance(value, dict) else {}
                _validate_contract(route_contract, errors)
        except Exception as exc:
            errors.append(f"child module probe crashed: {exc}")

    ok = len(errors) == 0
    decision = "CHILD_MODULE_PROBE_PASSED" if ok else "CHILD_MODULE_PROBE_BLOCKED"
    result = "D76_CHILD_MODULE_PROBE_COMPLETED" if ok else "D76_CHILD_MODULE_PROBE_BLOCKED"

    report = {
        "state": "D76_CHILD_MODULE_PROBE_RUNNER",
        "result": result,
        "route": "FIELD_INTENT_CHILD_MODULE_PROBE",
        "ok": ok,
        "decision": decision,
        "created_at": _now(),
        "input_reports": {"d75_report_path": str(root_path / d75_report_path)},
        "probe_target": {"child_module_path": child_path, "test_module_path": test_path},
        "module_description": module_description,
        "probe_result": probe_result,
        "route_contract": route_contract,
        "guardrails": {
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "probe_only": True,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": warnings},
        "summary": {
            "decision": decision,
            "child_module_path": child_path,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
            "probe_ok": probe_result.get("ok") if isinstance(probe_result, dict) else None,
            "contract_ok": route_contract.get("ok") if isinstance(route_contract, dict) else None,
        },
        "success_condition": {
            "child_probe_passed": ok,
            "actual_apply_executed": False,
            "protected_core_untouched": True,
            "next_step": "D77 can prepare a narrow adapter contract proposal, still without core mutation.",
        },
    }

    _write_json(root_path / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(run_child_module_probe(), ensure_ascii=False, indent=2))
'''.lstrip()

TEST_CODE = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.child_module_probe_runner import run_child_module_probe


CHILD_CODE = """
from __future__ import annotations

def describe_module():
    return {"state": "D75_DIFFERENTIATED_CHILD_MODULE", "sandbox_only": True}

def run_sandbox_probe(event=None):
    return {
        "ok": True,
        "state": "D75_DIFFERENTIATED_CHILD_MODULE",
        "payload_preserved": dict(event or {}),
        "guardrails": {
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "sandbox_only": True,
        },
    }

def propose_route_contract(event=None):
    return {
        "ok": True,
        "contract": "D75_CHILD_MODULE_ROUTE_CONTRACT",
        "allowed_mode": "SANDBOX_PROBE_ONLY",
        "forbidden_actions": [
            "direct_core_edit",
            "overwrite_canonical_memory",
            "external_ai_call",
            "auto_apply_runtime_mutation",
        ],
        "required_before_integration": [
            "D66_RECHECK",
            "UNIT_TESTS",
            "REGRESSION_TESTS",
            "ROLLBACK_MANIFEST",
            "HUMAN_OR_HIGHER_POLICY_APPROVAL",
        ],
    }
"""


class TestD76ChildModuleProbeRunner(unittest.TestCase):
    def make_valid_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        child_dir = root / "runtime_experimental/differentiated_modules"
        child_dir.mkdir(parents=True)
        (root / "reports").mkdir(parents=True)
        (root / "tests").mkdir(parents=True)

        child_rel = "runtime_experimental/differentiated_modules/01_test_route_policy_child.py"
        test_rel = "tests/test_d75_01_test_route_policy_child.py"

        (root / child_rel).write_text(CHILD_CODE, encoding="utf-8")
        (root / test_rel).write_text("# placeholder generated D75 test\\n", encoding="utf-8")

        (root / "reports/d75_differentiation_scaffold_package.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "DIFFERENTIATION_SCAFFOLD_READY",
                    "guardrails": {"actual_apply_executed": False, "scaffold_only": True},
                    "scaffold_package": {
                        "child_module_path": child_rel,
                        "test_module_path": test_rel,
                    },
                }
            ),
            encoding="utf-8",
        )
        return td, root, child_rel

    def test_child_probe_passes(self):
        td, root, child_rel = self.make_valid_root()
        try:
            report = run_child_module_probe(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "CHILD_MODULE_PROBE_PASSED")
            self.assertEqual(report["probe_target"]["child_module_path"], child_rel)
            self.assertTrue(report["probe_result"]["ok"])
            self.assertTrue(report["route_contract"]["ok"])
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertTrue((root / "reports/d76_child_module_probe_report.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_child_module(self):
        td, root, child_rel = self.make_valid_root()
        try:
            (root / child_rel).unlink()
            report = run_child_module_probe(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "CHILD_MODULE_PROBE_BLOCKED")
            self.assertGreaterEqual(report["summary"]["errors_count"], 1)
        finally:
            td.cleanup()

    def test_blocks_contract_without_required_gate(self):
        td, root, child_rel = self.make_valid_root()
        try:
            path = root / child_rel
            text = path.read_text(encoding="utf-8")
            text = text.replace('"D66_RECHECK",', "")
            path.write_text(text, encoding="utf-8")

            report = run_child_module_probe(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "CHILD_MODULE_PROBE_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
'''.lstrip()

Path("runtime_experimental").mkdir(parents=True, exist_ok=True)
Path("tests").mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(parents=True, exist_ok=True)

print("D76 CHILD MODULE PROBE RUNNER BOOT: repo =", Path.cwd())
Path("runtime_experimental/child_module_probe_runner.py").write_text(RUNNER_CODE, encoding="utf-8")
print("created/updated runtime_experimental/child_module_probe_runner.py")
Path("tests/test_d76_child_module_probe_runner.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d76_child_module_probe_runner.py")

print("\n== compile ==")
subprocess.run([sys.executable, "-m", "py_compile", "runtime_experimental/child_module_probe_runner.py"], check=True)

print("\n== unit tests ==")
subprocess.run([sys.executable, "-m", "unittest", "tests.test_d76_child_module_probe_runner", "-v"], check=True)

print("\n== run D76 child module probe ==")
subprocess.run([
    sys.executable,
    "-c",
    "from runtime_experimental.child_module_probe_runner import run_child_module_probe\n"
    "r=run_child_module_probe()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
rp = Path("reports/d76_child_module_probe_report.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== git add/commit ==")
paths = [
    "D76_CHILD_MODULE_PROBE_RUNNER_BOOT.py",
    "runtime_experimental/child_module_probe_runner.py",
    "tests/test_d76_child_module_probe_runner.py",
    "reports/d76_child_module_probe_report.json",
]
for p in paths:
    if Path(p).exists():
        subprocess.run(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "fix: rebuild D76 child module probe runner boot"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D76 child module probe runner changes to commit.")

print("\n== final status ==")
subprocess.run(["git", "status", "--short"], check=False)
print("\nD76 CHILD MODULE PROBE RUNNER BOOT DONE")
