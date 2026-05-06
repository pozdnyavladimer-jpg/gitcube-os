#!/usr/bin/env python3
# D77_NARROW_ADAPTER_CONTRACT_BOOT.py
#
# Adds D77 Narrow Adapter Contract to GitCube OS.
#
# Run from repo root:
#     python D77_NARROW_ADAPTER_CONTRACT_BOOT.py
#
# Creates:
# - runtime_experimental/narrow_adapter_contract.py
# - tests/test_d77_narrow_adapter_contract.py
# - reports/d77_narrow_adapter_contract.json
#
# D77 does NOT call an external AI API.
# D77 does NOT patch task_dispatcher.py.
# D77 does NOT mutate protected core.
# D77 does NOT overwrite canonical memory.
# D77 does NOT insert a real route.
#
# D77 creates only the contract for a narrow adapter between the old stressed node
# and the new D75/D76 child module.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


CONTRACT_CODE = json.loads("\"from __future__ import annotations\\n\\nimport hashlib\\nimport json\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nDEFAULT_D76_REPORT = \\\"reports/d76_child_module_probe_report.json\\\"\\nDEFAULT_D75_REPORT = \\\"reports/d75_differentiation_scaffold_package.json\\\"\\nDEFAULT_D74_PLAN = \\\"reports/d74_differentiation_plan.json\\\"\\nDEFAULT_OUTPUT = \\\"reports/d77_narrow_adapter_contract.json\\\"\\n\\n\\ndef _now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef _read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef _write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef _safe_relative_path(path_value: str) -> str:\\n    raw = str(path_value or \\\"\\\").strip().replace(\\\"\\\\\\\\\\\", \\\"/\\\").lstrip(\\\"/\\\")\\n    parts: List[str] = []\\n    for part in raw.split(\\\"/\\\"):\\n        if not part or part == \\\".\\\" or part == \\\"..\\\":\\n            continue\\n        parts.append(part)\\n    return \\\"/\\\".join(parts)\\n\\n\\ndef _safe_symbol(value: str) -> str:\\n    raw = _safe_relative_path(value).replace(\\\"/\\\", \\\"_\\\").replace(\\\".\\\", \\\"_\\\").replace(\\\"-\\\", \\\"_\\\")\\n    out = \\\"\\\".join(ch.lower() if ch.isalnum() or ch == \\\"_\\\" else \\\"_\\\" for ch in raw)\\n    while \\\"__\\\" in out:\\n        out = out.replace(\\\"__\\\", \\\"_\\\")\\n    return out.strip(\\\"_\\\") or \\\"adapter\\\"\\n\\n\\ndef _sha256_json(data: Dict[str, Any]) -> str:\\n    payload = json.dumps(data, ensure_ascii=False, sort_keys=True).encode(\\\"utf-8\\\")\\n    return hashlib.sha256(payload).hexdigest()\\n\\n\\ndef _validate_d76(d76: Dict[str, Any], errors: List[str]) -> None:\\n    if not d76:\\n        errors.append(\\\"D76 child module probe report missing or unreadable\\\")\\n        return\\n\\n    if d76.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D76 ok flag is not true\\\")\\n\\n    if d76.get(\\\"decision\\\") != \\\"CHILD_MODULE_PROBE_PASSED\\\":\\n        errors.append(f\\\"D76 decision is not CHILD_MODULE_PROBE_PASSED: {d76.get('decision')}\\\")\\n\\n    guardrails = d76.get(\\\"guardrails\\\") if isinstance(d76.get(\\\"guardrails\\\"), dict) else {}\\n    if guardrails.get(\\\"actual_apply_executed\\\") is not False:\\n        errors.append(\\\"D76 actual_apply_executed is not false\\\")\\n    if guardrails.get(\\\"probe_only\\\") is not True:\\n        errors.append(\\\"D76 probe_only is not true\\\")\\n\\n\\ndef _validate_route_contract(contract: Dict[str, Any], errors: List[str]) -> None:\\n    if not isinstance(contract, dict) or not contract:\\n        errors.append(\\\"D76 route contract missing or unreadable\\\")\\n        return\\n\\n    if contract.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D76 route contract ok flag is not true\\\")\\n\\n    if contract.get(\\\"allowed_mode\\\") != \\\"SANDBOX_PROBE_ONLY\\\":\\n        errors.append(f\\\"D76 route contract allowed_mode is not SANDBOX_PROBE_ONLY: {contract.get('allowed_mode')}\\\")\\n\\n    forbidden = contract.get(\\\"forbidden_actions\\\")\\n    if not isinstance(forbidden, list):\\n        errors.append(\\\"D76 route contract forbidden_actions is not a list\\\")\\n    else:\\n        for action in (\\\"direct_core_edit\\\", \\\"overwrite_canonical_memory\\\", \\\"auto_apply_runtime_mutation\\\"):\\n            if action not in forbidden:\\n                errors.append(f\\\"D76 route contract missing forbidden action: {action}\\\")\\n\\n    required = contract.get(\\\"required_before_integration\\\")\\n    if not isinstance(required, list):\\n        errors.append(\\\"D76 route contract required_before_integration is not a list\\\")\\n    else:\\n        for gate in (\\\"D66_RECHECK\\\", \\\"UNIT_TESTS\\\", \\\"REGRESSION_TESTS\\\", \\\"ROLLBACK_MANIFEST\\\"):\\n            if gate not in required:\\n                errors.append(f\\\"D76 route contract missing required gate: {gate}\\\")\\n\\n\\ndef build_narrow_adapter_contract(\\n    root: str | Path = \\\".\\\",\\n    d76_report_path: str = DEFAULT_D76_REPORT,\\n    d75_report_path: str = DEFAULT_D75_REPORT,\\n    d74_plan_path: str = DEFAULT_D74_PLAN,\\n    output_path: str = DEFAULT_OUTPUT,\\n) -> Dict[str, Any]:\\n    root_path = Path(root).resolve()\\n\\n    d76 = _read_json(root_path / d76_report_path, default={}) or {}\\n    d75 = _read_json(root_path / d75_report_path, default={}) or {}\\n    d74 = _read_json(root_path / d74_plan_path, default={}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    _validate_d76(d76, errors)\\n\\n    if not d75:\\n        warnings.append(\\\"D75 scaffold report missing or unreadable; using D76 probe target only\\\")\\n    if not d74:\\n        warnings.append(\\\"D74 differentiation plan missing or unreadable; source intent may be incomplete\\\")\\n\\n    probe_target = d76.get(\\\"probe_target\\\") if isinstance(d76.get(\\\"probe_target\\\"), dict) else {}\\n    module_description = d76.get(\\\"module_description\\\") if isinstance(d76.get(\\\"module_description\\\"), dict) else {}\\n    route_contract = d76.get(\\\"route_contract\\\") if isinstance(d76.get(\\\"route_contract\\\"), dict) else {}\\n\\n    _validate_route_contract(route_contract, errors)\\n\\n    child_module_path = _safe_relative_path(\\n        str(probe_target.get(\\\"child_module_path\\\") or route_contract.get(\\\"child_module_path\\\") or \\\"\\\")\\n    )\\n    if not child_module_path:\\n        errors.append(\\\"child module path missing\\\")\\n    elif not child_module_path.startswith(\\\"runtime_experimental/differentiated_modules/\\\"):\\n        errors.append(f\\\"child module path outside differentiated_modules: {child_module_path}\\\")\\n\\n    source_node = str(\\n        route_contract.get(\\\"source_node\\\")\\n        or module_description.get(\\\"source_node\\\")\\n        or d76.get(\\\"summary\\\", {}).get(\\\"source_node\\\", \\\"\\\")\\n        or \\\"UNKNOWN_SOURCE_NODE\\\"\\n    )\\n\\n    handler_role = str(\\n        route_contract.get(\\\"handler_role\\\")\\n        or module_description.get(\\\"gradient_role\\\")\\n        or \\\"specialized_child\\\"\\n    )\\n\\n    source_slug = _safe_symbol(source_node)\\n    role_slug = _safe_symbol(handler_role)\\n    adapter_name = f\\\"D77_NARROW_ADAPTER_{source_slug}_{role_slug}\\\".upper()\\n    contract_id = \\\"d77-\\\" + _sha256_json(\\n        {\\n            \\\"source_node\\\": source_node,\\n            \\\"child_module_path\\\": child_module_path,\\n            \\\"handler_role\\\": handler_role,\\n        }\\n    )[:16]\\n\\n    ok = len(errors) == 0\\n    decision = \\\"NARROW_ADAPTER_CONTRACT_READY\\\" if ok else \\\"NARROW_ADAPTER_CONTRACT_BLOCKED\\\"\\n    result = \\\"D77_NARROW_ADAPTER_CONTRACT_CREATED\\\" if ok else \\\"D77_NARROW_ADAPTER_CONTRACT_BLOCKED\\\"\\n\\n    narrow_adapter_contract = {\\n        \\\"contract_id\\\": contract_id,\\n        \\\"contract_state\\\": \\\"D77_NARROW_ADAPTER_CONTRACT\\\",\\n        \\\"enabled\\\": ok,\\n        \\\"mode\\\": \\\"CONTRACT_ONLY_NO_ROUTE_INSERT\\\",\\n        \\\"adapter_name\\\": adapter_name,\\n        \\\"source_node\\\": source_node,\\n        \\\"child_module_path\\\": child_module_path,\\n        \\\"handler_role\\\": handler_role,\\n        \\\"boundary\\\": {\\n            \\\"input\\\": \\\"event: dict[str, Any]\\\",\\n            \\\"output\\\": \\\"sandbox probe result with payload preservation and guardrails\\\",\\n            \\\"adapter_width\\\": \\\"narrow\\\",\\n            \\\"allowed_call\\\": \\\"child_module.run_sandbox_probe(event)\\\",\\n            \\\"forbidden_call\\\": \\\"direct protected-core mutation\\\",\\n        },\\n        \\\"route_policy\\\": {\\n            \\\"integration_status\\\": \\\"NOT_INTEGRATED\\\",\\n            \\\"route_insert_allowed_now\\\": False,\\n            \\\"contract_only\\\": True,\\n            \\\"allowed_next_step\\\": \\\"generate adapter dry-run diff only\\\",\\n        },\\n        \\\"required_before_integration\\\": [\\n            \\\"D66_RECHECK\\\",\\n            \\\"D73_PACKAGE_READY\\\",\\n            \\\"D76_CHILD_PROBE_PASSED\\\",\\n            \\\"UNIT_TESTS\\\",\\n            \\\"REGRESSION_TESTS\\\",\\n            \\\"ROLLBACK_MANIFEST\\\",\\n            \\\"HUMAN_OR_HIGHER_POLICY_APPROVAL\\\",\\n        ],\\n        \\\"forbidden_actions\\\": [\\n            \\\"direct_core_edit\\\",\\n            \\\"protected_core_mutation\\\",\\n            \\\"overwrite_canonical_memory\\\",\\n            \\\"external_ai_call\\\",\\n            \\\"auto_apply_runtime_mutation\\\",\\n            \\\"route_insert_without_D66_recheck\\\",\\n            \\\"route_insert_without_rollback_manifest\\\",\\n        ],\\n    }\\n\\n    report = {\\n        \\\"state\\\": \\\"D77_NARROW_ADAPTER_CONTRACT\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_NARROW_ADAPTER_CONTRACT\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": _now(),\\n        \\\"contract_id\\\": contract_id,\\n        \\\"narrow_adapter_contract\\\": narrow_adapter_contract,\\n        \\\"input_reports\\\": {\\n            \\\"d76_report_path\\\": str(root_path / d76_report_path),\\n            \\\"d75_report_path\\\": str(root_path / d75_report_path),\\n            \\\"d74_plan_path\\\": str(root_path / d74_plan_path),\\n        },\\n        \\\"evidence\\\": {\\n            \\\"d76_decision\\\": d76.get(\\\"decision\\\"),\\n            \\\"d76_ok\\\": d76.get(\\\"ok\\\"),\\n            \\\"d75_decision\\\": d75.get(\\\"decision\\\"),\\n            \\\"d74_decision\\\": d74.get(\\\"decision\\\"),\\n            \\\"child_module_path\\\": child_module_path,\\n            \\\"handler_role\\\": handler_role,\\n            \\\"source_node\\\": source_node,\\n        },\\n        \\\"guardrails\\\": {\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"external_ai_called\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"contract_only\\\": True,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"contract_id\\\": contract_id,\\n            \\\"adapter_name\\\": adapter_name,\\n            \\\"source_node\\\": source_node,\\n            \\\"child_module_path\\\": child_module_path,\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"narrow_adapter_contract_created\\\": ok,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D78 can generate a narrow adapter dry-run diff package, still without route insertion.\\\",\\n        },\\n    }\\n\\n    _write_json(root_path / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(build_narrow_adapter_contract(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.narrow_adapter_contract import build_narrow_adapter_contract\\n\\n\\nclass TestD77NarrowAdapterContract(unittest.TestCase):\\n    def make_valid_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n\\n        child = \\\"runtime_experimental/differentiated_modules/01_route_policy_child.py\\\"\\n        source = \\\"app/orchestration/task_dispatcher.py\\\"\\n\\n        (root / \\\"reports/d76_child_module_probe_report.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"CHILD_MODULE_PROBE_PASSED\\\",\\n                    \\\"guardrails\\\": {\\\"actual_apply_executed\\\": False, \\\"probe_only\\\": True},\\n                    \\\"probe_target\\\": {\\\"child_module_path\\\": child},\\n                    \\\"module_description\\\": {\\n                        \\\"source_node\\\": source,\\n                        \\\"gradient_role\\\": \\\"route_policy_child\\\",\\n                    },\\n                    \\\"route_contract\\\": {\\n                        \\\"ok\\\": True,\\n                        \\\"contract\\\": \\\"D75_CHILD_MODULE_ROUTE_CONTRACT\\\",\\n                        \\\"source_node\\\": source,\\n                        \\\"handler_role\\\": \\\"route_policy_child\\\",\\n                        \\\"allowed_mode\\\": \\\"SANDBOX_PROBE_ONLY\\\",\\n                        \\\"forbidden_actions\\\": [\\n                            \\\"direct_core_edit\\\",\\n                            \\\"overwrite_canonical_memory\\\",\\n                            \\\"external_ai_call\\\",\\n                            \\\"auto_apply_runtime_mutation\\\",\\n                        ],\\n                        \\\"required_before_integration\\\": [\\n                            \\\"D66_RECHECK\\\",\\n                            \\\"UNIT_TESTS\\\",\\n                            \\\"REGRESSION_TESTS\\\",\\n                            \\\"ROLLBACK_MANIFEST\\\",\\n                            \\\"HUMAN_OR_HIGHER_POLICY_APPROVAL\\\",\\n                        ],\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n        (root / \\\"reports/d75_differentiation_scaffold_package.json\\\").write_text(\\n            json.dumps({\\\"ok\\\": True, \\\"decision\\\": \\\"DIFFERENTIATION_SCAFFOLD_READY\\\"}),\\n            encoding=\\\"utf-8\\\",\\n        )\\n        (root / \\\"reports/d74_differentiation_plan.json\\\").write_text(\\n            json.dumps({\\\"ok\\\": True, \\\"decision\\\": \\\"DIFFERENTIATION_PLAN_READY\\\"}),\\n            encoding=\\\"utf-8\\\",\\n        )\\n        return td, root, child, source\\n\\n    def test_creates_narrow_adapter_contract(self):\\n        td, root, child, source = self.make_valid_root()\\n        try:\\n            report = build_narrow_adapter_contract(root=root)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"NARROW_ADAPTER_CONTRACT_READY\\\")\\n            self.assertEqual(report[\\\"narrow_adapter_contract\\\"][\\\"child_module_path\\\"], child)\\n            self.assertEqual(report[\\\"narrow_adapter_contract\\\"][\\\"source_node\\\"], source)\\n            self.assertFalse(report[\\\"narrow_adapter_contract\\\"][\\\"route_policy\\\"][\\\"route_insert_allowed_now\\\"])\\n            self.assertFalse(report[\\\"guardrails\\\"][\\\"actual_apply_executed\\\"])\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"contract_only\\\"])\\n            self.assertTrue((root / \\\"reports/d77_narrow_adapter_contract.json\\\").exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d76(self):\\n        td, root, _, _ = self.make_valid_root()\\n        try:\\n            (root / \\\"reports/d76_child_module_probe_report.json\\\").unlink()\\n            report = build_narrow_adapter_contract(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"NARROW_ADAPTER_CONTRACT_BLOCKED\\\")\\n            self.assertGreaterEqual(report[\\\"summary\\\"][\\\"errors_count\\\"], 1)\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_required_gate(self):\\n        td, root, _, _ = self.make_valid_root()\\n        try:\\n            path = root / \\\"reports/d76_child_module_probe_report.json\\\"\\n            data = json.loads(path.read_text(encoding=\\\"utf-8\\\"))\\n            data[\\\"route_contract\\\"][\\\"required_before_integration\\\"].remove(\\\"D66_RECHECK\\\")\\n            path.write_text(json.dumps(data), encoding=\\\"utf-8\\\")\\n\\n            report = build_narrow_adapter_contract(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"NARROW_ADAPTER_CONTRACT_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


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

print("D77 NARROW ADAPTER CONTRACT BOOT: repo =", ROOT)

Path("runtime_experimental/narrow_adapter_contract.py").write_text(CONTRACT_CODE, encoding="utf-8")
print("created/updated runtime_experimental/narrow_adapter_contract.py")

Path("tests/test_d77_narrow_adapter_contract.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d77_narrow_adapter_contract.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/narrow_adapter_contract.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d77_narrow_adapter_contract", "-v"], check=True)

print("\n== run D77 narrow adapter contract ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.narrow_adapter_contract import build_narrow_adapter_contract\n"
        "r=build_narrow_adapter_contract()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d77_narrow_adapter_contract.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/narrow_adapter_contract.py",
    "tests/test_d77_narrow_adapter_contract.py",
    "reports/d77_narrow_adapter_contract.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D77_NARROW_ADAPTER_CONTRACT_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D77 narrow adapter contract"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D77 narrow adapter contract changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD77 NARROW ADAPTER CONTRACT BOOT DONE")
