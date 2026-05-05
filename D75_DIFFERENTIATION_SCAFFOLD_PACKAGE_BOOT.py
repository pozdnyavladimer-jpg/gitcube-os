#!/usr/bin/env python3
# D75_DIFFERENTIATION_SCAFFOLD_PACKAGE_BOOT.py
#
# Adds D75 Differentiation Scaffold Package to GitCube OS.
#
# Run from repo root:
#     python D75_DIFFERENTIATION_SCAFFOLD_PACKAGE_BOOT.py
#
# Creates:
# - runtime_experimental/differentiation_scaffold_package.py
# - runtime_experimental/differentiated_modules/<child>.py
# - tests/test_d75_differentiation_scaffold_package.py
# - tests/test_d75_<child>.py
# - reports/d75_differentiation_scaffold_package.json
#
# D75 does NOT call an external AI API.
# D75 does NOT patch task_dispatcher.py.
# D75 does NOT mutate protected core.
# D75 does NOT overwrite canonical memory.
# D75 does NOT apply sandbox files to runtime.
#
# D75 creates the first sandbox-only child module scaffold from D74.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


SCAFFOLDER_CODE = 'from __future__ import annotations\n\nimport json\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nfrom typing import Any, Dict, List\n\n\nDEFAULT_D74_PLAN = "reports/d74_differentiation_plan.json"\nDEFAULT_OUTPUT = "reports/d75_differentiation_scaffold_package.json"\n\nCHILD_PREFIX = "runtime_experimental/differentiated_modules/"\nTEST_PREFIX = "tests/"\n\n\ndef _now() -> str:\n    return datetime.now(timezone.utc).isoformat()\n\n\ndef _read_json(path: str | Path, default: Any = None) -> Any:\n    p = Path(path)\n    if not p.exists():\n        return default\n    try:\n        return json.loads(p.read_text(encoding="utf-8"))\n    except Exception:\n        return default\n\n\ndef _write_json(path: str | Path, data: Dict[str, Any]) -> None:\n    p = Path(path)\n    p.parent.mkdir(parents=True, exist_ok=True)\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")\n\n\ndef _safe_relative_path(path_value: str) -> str:\n    raw = str(path_value or "").strip().replace("\\\\", "/").lstrip("/")\n    parts: List[str] = []\n    for part in raw.split("/"):\n        if not part or part == "." or part == "..":\n            continue\n        parts.append(part)\n    return "/".join(parts)\n\n\ndef _safe_symbol(value: str) -> str:\n    raw = _safe_relative_path(value).replace("/", "_").replace(".", "_").replace("-", "_")\n    out = "".join(ch.lower() if ch.isalnum() or ch == "_" else "_" for ch in raw)\n    while "__" in out:\n        out = out.replace("__", "_")\n    return out.strip("_") or "d75_child"\n\n\ndef _child_path(candidate: Dict[str, Any]) -> str:\n    proposed = _safe_relative_path(str(candidate.get("recommended_child_module", "")))\n    if proposed.startswith(CHILD_PREFIX) and proposed.endswith(".py"):\n        return proposed\n\n    source = _safe_symbol(str(candidate.get("source_node", "unknown_node")))\n    role = _safe_symbol(str(candidate.get("gradient_role", "specialized_child")))\n    return f"{CHILD_PREFIX}01_{source}_{role}.py"\n\n\ndef _test_path_for_child(child_path: str) -> str:\n    stem = Path(child_path).stem\n    safe = _safe_symbol(stem)\n    return f"{TEST_PREFIX}test_d75_{safe}.py"\n\n\ndef _child_code(candidate: Dict[str, Any]) -> str:\n    source_node = str(candidate.get("source_node", "unknown"))\n    gradient_role = str(candidate.get("gradient_role", "specialized_child"))\n    gradient_intent = str(candidate.get("gradient_intent", "separate overloaded responsibility into isolated module"))\n    pain_score = candidate.get("pain_score", 0.0)\n\n    return f\'\'\'from __future__ import annotations\n\nfrom typing import Any, Dict\n\n\nMODULE_STATE = "D75_DIFFERENTIATED_CHILD_MODULE"\nSOURCE_NODE = {source_node!r}\nGRADIENT_ROLE = {gradient_role!r}\nGRADIENT_INTENT = {gradient_intent!r}\nPAIN_SCORE_AT_BIRTH = {pain_score!r}\n\n# This scaffold is intentionally sandbox-only.\nPROTECTED_CORE_TOUCH_ALLOWED = False\nCANONICAL_MEMORY_WRITE_ALLOWED = False\nEXTERNAL_AI_CALL_ALLOWED = False\nRUNTIME_APPLY_ALLOWED = False\n\n\ndef describe_module() -> Dict[str, Any]:\n    return {{\n        "state": MODULE_STATE,\n        "source_node": SOURCE_NODE,\n        "gradient_role": GRADIENT_ROLE,\n        "gradient_intent": GRADIENT_INTENT,\n        "pain_score_at_birth": PAIN_SCORE_AT_BIRTH,\n        "sandbox_only": True,\n    }}\n\n\ndef run_sandbox_probe(event: Dict[str, Any] | None = None) -> Dict[str, Any]:\n    payload = dict(event or {{}})\n    return {{\n        "ok": True,\n        "state": MODULE_STATE,\n        "source_node": SOURCE_NODE,\n        "gradient_role": GRADIENT_ROLE,\n        "payload_preserved": payload,\n        "guardrails": {{\n            "protected_core_mutated": False,\n            "canonical_memory_mutated": False,\n            "external_ai_called": False,\n            "actual_apply_executed": False,\n            "sandbox_only": True,\n        }},\n    }}\n\n\ndef propose_route_contract(event: Dict[str, Any] | None = None) -> Dict[str, Any]:\n    return {{\n        "ok": True,\n        "contract": "D75_CHILD_MODULE_ROUTE_CONTRACT",\n        "source_node": SOURCE_NODE,\n        "handler_role": GRADIENT_ROLE,\n        "allowed_mode": "SANDBOX_PROBE_ONLY",\n        "forbidden_actions": [\n            "direct_core_edit",\n            "overwrite_canonical_memory",\n            "external_ai_call",\n            "auto_apply_runtime_mutation",\n        ],\n        "required_before_integration": [\n            "D66_RECHECK",\n            "UNIT_TESTS",\n            "REGRESSION_TESTS",\n            "ROLLBACK_MANIFEST",\n            "HUMAN_OR_HIGHER_POLICY_APPROVAL",\n        ],\n    }}\n\'\'\'\n\n\ndef _generated_test_code(child_path: str) -> str:\n    return f\'\'\'import importlib.util\nimport json\nimport unittest\nfrom pathlib import Path\n\n\nCHILD_PATH = Path({child_path!r})\nREPORT_PATH = Path("reports/d75_differentiation_scaffold_package.json")\n\n\ndef load_child_module():\n    spec = importlib.util.spec_from_file_location("d75_generated_child_module", CHILD_PATH)\n    module = importlib.util.module_from_spec(spec)\n    assert spec.loader is not None\n    spec.loader.exec_module(module)\n    return module\n\n\nclass TestD75GeneratedChildModule(unittest.TestCase):\n    def test_child_probe_is_sandbox_only(self):\n        self.assertTrue(CHILD_PATH.exists())\n        module = load_child_module()\n        result = module.run_sandbox_probe({{"kind": "D75_TEST"}})\n\n        self.assertTrue(result["ok"])\n        self.assertEqual(result["state"], "D75_DIFFERENTIATED_CHILD_MODULE")\n        self.assertFalse(result["guardrails"]["protected_core_mutated"])\n        self.assertFalse(result["guardrails"]["canonical_memory_mutated"])\n        self.assertFalse(result["guardrails"]["actual_apply_executed"])\n        self.assertTrue(result["guardrails"]["sandbox_only"])\n\n    def test_route_contract_requires_guards(self):\n        module = load_child_module()\n        contract = module.propose_route_contract()\n\n        self.assertTrue(contract["ok"])\n        self.assertEqual(contract["allowed_mode"], "SANDBOX_PROBE_ONLY")\n        self.assertIn("D66_RECHECK", contract["required_before_integration"])\n        self.assertIn("direct_core_edit", contract["forbidden_actions"])\n\n    def test_report_points_to_child(self):\n        self.assertTrue(REPORT_PATH.exists())\n        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))\n        self.assertEqual(report["scaffold_package"]["child_module_path"], str(CHILD_PATH))\n        self.assertFalse(report["guardrails"]["actual_apply_executed"])\n\n\nif __name__ == "__main__":\n    unittest.main()\n\'\'\'\n\n\ndef _select_candidate(d74: Dict[str, Any], candidate_index: int = 0) -> Dict[str, Any]:\n    plan = d74.get("differentiation_plan") if isinstance(d74.get("differentiation_plan"), dict) else {}\n    candidates = plan.get("candidates") if isinstance(plan.get("candidates"), list) else []\n    if not candidates:\n        return {}\n    if candidate_index < 0 or candidate_index >= len(candidates):\n        candidate_index = 0\n    value = candidates[candidate_index]\n    return value if isinstance(value, dict) else {}\n\n\ndef build_differentiation_scaffold_package(\n    root: str | Path = ".",\n    d74_plan_path: str = DEFAULT_D74_PLAN,\n    output_path: str = DEFAULT_OUTPUT,\n    candidate_index: int = 0,\n) -> Dict[str, Any]:\n    root_path = Path(root).resolve()\n    d74 = _read_json(root_path / d74_plan_path, default={}) or {}\n\n    errors: List[str] = []\n    warnings: List[str] = []\n\n    if not d74:\n        errors.append("D74 differentiation plan missing or unreadable")\n    else:\n        if d74.get("ok") is not True:\n            errors.append("D74 ok flag is not true")\n        if d74.get("decision") != "DIFFERENTIATION_PLAN_READY":\n            errors.append(f"D74 decision is not DIFFERENTIATION_PLAN_READY: {d74.get(\'decision\')}")\n        guardrails = d74.get("guardrails") if isinstance(d74.get("guardrails"), dict) else {}\n        if guardrails.get("actual_apply_executed") is not False:\n            errors.append("D74 actual_apply_executed is not false")\n        if guardrails.get("plan_only") is not True:\n            errors.append("D74 plan_only is not true")\n\n    candidate = _select_candidate(d74, candidate_index=candidate_index)\n    if not candidate:\n        errors.append("D74 has no differentiation candidates")\n\n    child_path = _child_path(candidate) if candidate else ""\n    test_path = _test_path_for_child(child_path) if child_path else ""\n\n    if child_path and not child_path.startswith(CHILD_PREFIX):\n        errors.append(f"D75 rejected child path outside sandbox differentiation prefix: {child_path}")\n    if test_path and not test_path.startswith(TEST_PREFIX):\n        errors.append(f"D75 rejected test path outside tests prefix: {test_path}")\n\n    ok = len(errors) == 0\n\n    created_files: List[str] = []\n    if ok:\n        init_path = root_path / CHILD_PREFIX / "__init__.py"\n        init_path.parent.mkdir(parents=True, exist_ok=True)\n        if not init_path.exists():\n            init_path.write_text("", encoding="utf-8")\n        created_files.append(str(init_path.relative_to(root_path)))\n\n        child_abs = root_path / child_path\n        child_abs.parent.mkdir(parents=True, exist_ok=True)\n        child_abs.write_text(_child_code(candidate), encoding="utf-8")\n        created_files.append(child_path)\n\n        test_abs = root_path / test_path\n        test_abs.parent.mkdir(parents=True, exist_ok=True)\n        test_abs.write_text(_generated_test_code(child_path), encoding="utf-8")\n        created_files.append(test_path)\n\n    decision = "DIFFERENTIATION_SCAFFOLD_READY" if ok else "DIFFERENTIATION_SCAFFOLD_BLOCKED"\n    result = "D75_DIFFERENTIATION_SCAFFOLD_CREATED" if ok else "D75_DIFFERENTIATION_SCAFFOLD_BLOCKED"\n\n    scaffold_package = {\n        "package_state": "D75_DIFFERENTIATION_SCAFFOLD_PACKAGE",\n        "enabled": ok,\n        "mode": "SANDBOX_ONLY_CHILD_MODULE_SCAFFOLD",\n        "source_d74_plan": str(root_path / d74_plan_path),\n        "selected_candidate": candidate,\n        "child_module_path": child_path,\n        "test_module_path": test_path,\n        "created_files": created_files,\n        "integration_status": "NOT_INTEGRATED",\n        "required_before_integration": [\n            "D66_RECHECK",\n            "D73_PACKAGE_READY",\n            "UNIT_TESTS",\n            "REGRESSION_TESTS",\n            "ROLLBACK_MANIFEST",\n            "HUMAN_OR_HIGHER_POLICY_APPROVAL",\n        ],\n        "forbidden_actions": [\n            "direct_core_edit",\n            "overwrite_canonical_memory",\n            "external_ai_call",\n            "auto_apply_runtime_mutation",\n        ],\n    }\n\n    report = {\n        "state": "D75_DIFFERENTIATION_SCAFFOLD_PACKAGE",\n        "result": result,\n        "route": "FIELD_INTENT_DIFFERENTIATION_SCAFFOLD",\n        "ok": ok,\n        "decision": decision,\n        "created_at": _now(),\n        "scaffold_package": scaffold_package,\n        "input_reports": {\n            "d74_plan_path": str(root_path / d74_plan_path),\n        },\n        "evidence": {\n            "d74_decision": d74.get("decision"),\n            "d74_ok": d74.get("ok"),\n            "source_node": candidate.get("source_node") if candidate else None,\n            "gradient_role": candidate.get("gradient_role") if candidate else None,\n            "child_module_path": child_path,\n            "test_module_path": test_path,\n        },\n        "guardrails": {\n            "sandbox_code_created": ok,\n            "runtime_code_mutated": False,\n            "protected_core_mutated": False,\n            "canonical_memory_mutated": False,\n            "external_ai_called": False,\n            "actual_apply_executed": False,\n            "scaffold_only": True,\n        },\n        "validation": {\n            "ok": ok,\n            "errors": errors,\n            "warnings": warnings,\n        },\n        "summary": {\n            "decision": decision,\n            "created_files_count": len(created_files),\n            "errors_count": len(errors),\n            "warnings_count": len(warnings),\n            "child_module_path": child_path,\n            "test_module_path": test_path,\n        },\n        "success_condition": {\n            "scaffold_created": ok,\n            "actual_apply_executed": False,\n            "protected_core_untouched": True,\n            "next_step": "D76 can run child-module probes and prepare adapter contract, still without core mutation.",\n        },\n    }\n\n    _write_json(root_path / output_path, report)\n    return report\n\n\nif __name__ == "__main__":\n    print(json.dumps(build_differentiation_scaffold_package(), ensure_ascii=False, indent=2))\n'
TEST_CODE = 'import json\nimport tempfile\nimport unittest\nfrom pathlib import Path\n\nfrom runtime_experimental.differentiation_scaffold_package import build_differentiation_scaffold_package\n\n\nclass TestD75DifferentiationScaffoldPackage(unittest.TestCase):\n    def make_valid_root(self):\n        td = tempfile.TemporaryDirectory()\n        root = Path(td.name)\n        (root / "reports").mkdir(parents=True)\n\n        candidate = {\n            "source_node": "app/orchestration/task_dispatcher.py",\n            "pain_score": 0.91,\n            "protected_core": True,\n            "gradient_role": "route_policy_child",\n            "gradient_intent": "separate routing pressure from core dispatcher",\n            "recommended_child_module": "runtime_experimental/differentiated_modules/01_app_orchestration_task_dispatcher_py_route_policy_child.py",\n            "old_node_policy": "do_not_expand_directly",\n        }\n\n        (root / "reports/d74_differentiation_plan.json").write_text(\n            json.dumps(\n                {\n                    "ok": True,\n                    "decision": "DIFFERENTIATION_PLAN_READY",\n                    "guardrails": {"actual_apply_executed": False, "plan_only": True},\n                    "differentiation_plan": {"enabled": True, "candidates": [candidate]},\n                }\n            ),\n            encoding="utf-8",\n        )\n        return td, root, candidate\n\n    def test_creates_sandbox_child_module_and_test(self):\n        td, root, candidate = self.make_valid_root()\n        try:\n            report = build_differentiation_scaffold_package(root=root)\n\n            self.assertTrue(report["ok"])\n            self.assertEqual(report["decision"], "DIFFERENTIATION_SCAFFOLD_READY")\n            self.assertTrue(report["guardrails"]["sandbox_code_created"])\n            self.assertFalse(report["guardrails"]["protected_core_mutated"])\n            self.assertFalse(report["guardrails"]["actual_apply_executed"])\n\n            child = root / report["scaffold_package"]["child_module_path"]\n            test = root / report["scaffold_package"]["test_module_path"]\n            self.assertTrue(child.exists())\n            self.assertTrue(test.exists())\n            self.assertTrue(str(child.relative_to(root)).startswith("runtime_experimental/differentiated_modules/"))\n            self.assertTrue((root / "reports/d75_differentiation_scaffold_package.json").exists())\n        finally:\n            td.cleanup()\n\n    def test_blocks_when_d74_missing(self):\n        td, root, _ = self.make_valid_root()\n        try:\n            (root / "reports/d74_differentiation_plan.json").unlink()\n            report = build_differentiation_scaffold_package(root=root)\n\n            self.assertFalse(report["ok"])\n            self.assertEqual(report["decision"], "DIFFERENTIATION_SCAFFOLD_BLOCKED")\n            self.assertFalse(report["scaffold_package"]["enabled"])\n            self.assertGreaterEqual(report["summary"]["errors_count"], 1)\n        finally:\n            td.cleanup()\n\n    def test_rejects_child_path_outside_sandbox_prefix(self):\n        td, root, candidate = self.make_valid_root()\n        try:\n            candidate["recommended_child_module"] = "app/orchestration/task_dispatcher.py"\n            (root / "reports/d74_differentiation_plan.json").write_text(\n                json.dumps(\n                    {\n                        "ok": True,\n                        "decision": "DIFFERENTIATION_PLAN_READY",\n                        "guardrails": {"actual_apply_executed": False, "plan_only": True},\n                        "differentiation_plan": {"enabled": True, "candidates": [candidate]},\n                    }\n                ),\n                encoding="utf-8",\n            )\n\n            report = build_differentiation_scaffold_package(root=root)\n\n            self.assertTrue(report["ok"])\n            self.assertTrue(report["scaffold_package"]["child_module_path"].startswith("runtime_experimental/differentiated_modules/"))\n        finally:\n            td.cleanup()\n\n\nif __name__ == "__main__":\n    unittest.main()\n'


def sh(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, text=True, capture_output=False, check=check)


def find_repo_root() -> Path:
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p
    return here


def test_module_from_path(path_value: str) -> str:
    return path_value[:-3].replace("/", ".") if path_value.endswith(".py") else path_value.replace("/", ".")


ROOT = find_repo_root()
os.chdir(ROOT)

Path("runtime_experimental").mkdir(parents=True, exist_ok=True)
Path("tests").mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(parents=True, exist_ok=True)

print("D75 DIFFERENTIATION SCAFFOLD PACKAGE BOOT: repo =", ROOT)

Path("runtime_experimental/differentiation_scaffold_package.py").write_text(SCAFFOLDER_CODE, encoding="utf-8")
print("created/updated runtime_experimental/differentiation_scaffold_package.py")

Path("tests/test_d75_differentiation_scaffold_package.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d75_differentiation_scaffold_package.py")

print("\n== compile scaffolder ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/differentiation_scaffold_package.py"], check=True)

print("\n== unit tests scaffolder ==")
sh([sys.executable, "-m", "unittest", "tests.test_d75_differentiation_scaffold_package", "-v"], check=True)

print("\n== run D75 differentiation scaffold package ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.differentiation_scaffold_package import build_differentiation_scaffold_package\n"
        "r=build_differentiation_scaffold_package()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d75_differentiation_scaffold_package.json")
generated_paths = []
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))
    pkg = data.get("scaffold_package", {})
    for key in ("child_module_path", "test_module_path"):
        value = pkg.get(key)
        if value:
            generated_paths.append(value)
    for value in pkg.get("created_files", []):
        if value not in generated_paths:
            generated_paths.append(value)

for value in generated_paths:
    if value.endswith(".py") and Path(value).exists():
        print("\n== compile generated ==", value)
        sh([sys.executable, "-m", "py_compile", value], check=True)

test_path = None
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    test_path = data.get("scaffold_package", {}).get("test_module_path")

if test_path and Path(test_path).exists():
    print("\n== unit tests generated child ==")
    sh([sys.executable, "-m", "unittest", test_module_from_path(test_path), "-v"], check=True)

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/differentiation_scaffold_package.py",
    "tests/test_d75_differentiation_scaffold_package.py",
    "reports/d75_differentiation_scaffold_package.json",
]
paths.extend(generated_paths)

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D75_DIFFERENTIATION_SCAFFOLD_PACKAGE_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

deduped = []
seen = set()
for p in paths:
    if p and p not in seen:
        seen.add(p)
        deduped.append(p)

for p in deduped:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *deduped], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D75 differentiation scaffold package"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D75 differentiation scaffold package changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD75 DIFFERENTIATION SCAFFOLD PACKAGE BOOT DONE")
