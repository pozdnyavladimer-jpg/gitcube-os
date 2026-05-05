from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_D74_PLAN = "reports/d74_differentiation_plan.json"
DEFAULT_OUTPUT = "reports/d75_differentiation_scaffold_package.json"

CHILD_PREFIX = "runtime_experimental/differentiated_modules/"
TEST_PREFIX = "tests/"


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


def _safe_symbol(value: str) -> str:
    raw = _safe_relative_path(value).replace("/", "_").replace(".", "_").replace("-", "_")
    out = "".join(ch.lower() if ch.isalnum() or ch == "_" else "_" for ch in raw)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_") or "d75_child"


def _child_path(candidate: Dict[str, Any]) -> str:
    proposed = _safe_relative_path(str(candidate.get("recommended_child_module", "")))
    if proposed.startswith(CHILD_PREFIX) and proposed.endswith(".py"):
        return proposed

    source = _safe_symbol(str(candidate.get("source_node", "unknown_node")))
    role = _safe_symbol(str(candidate.get("gradient_role", "specialized_child")))
    return f"{CHILD_PREFIX}01_{source}_{role}.py"


def _test_path_for_child(child_path: str) -> str:
    stem = Path(child_path).stem
    safe = _safe_symbol(stem)
    return f"{TEST_PREFIX}test_d75_{safe}.py"


def _child_code(candidate: Dict[str, Any]) -> str:
    source_node = str(candidate.get("source_node", "unknown"))
    gradient_role = str(candidate.get("gradient_role", "specialized_child"))
    gradient_intent = str(candidate.get("gradient_intent", "separate overloaded responsibility into isolated module"))
    pain_score = candidate.get("pain_score", 0.0)

    return f'''from __future__ import annotations

from typing import Any, Dict


MODULE_STATE = "D75_DIFFERENTIATED_CHILD_MODULE"
SOURCE_NODE = {source_node!r}
GRADIENT_ROLE = {gradient_role!r}
GRADIENT_INTENT = {gradient_intent!r}
PAIN_SCORE_AT_BIRTH = {pain_score!r}

# This scaffold is intentionally sandbox-only.
PROTECTED_CORE_TOUCH_ALLOWED = False
CANONICAL_MEMORY_WRITE_ALLOWED = False
EXTERNAL_AI_CALL_ALLOWED = False
RUNTIME_APPLY_ALLOWED = False


def describe_module() -> Dict[str, Any]:
    return {{
        "state": MODULE_STATE,
        "source_node": SOURCE_NODE,
        "gradient_role": GRADIENT_ROLE,
        "gradient_intent": GRADIENT_INTENT,
        "pain_score_at_birth": PAIN_SCORE_AT_BIRTH,
        "sandbox_only": True,
    }}


def run_sandbox_probe(event: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = dict(event or {{}})
    return {{
        "ok": True,
        "state": MODULE_STATE,
        "source_node": SOURCE_NODE,
        "gradient_role": GRADIENT_ROLE,
        "payload_preserved": payload,
        "guardrails": {{
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "sandbox_only": True,
        }},
    }}


def propose_route_contract(event: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {{
        "ok": True,
        "contract": "D75_CHILD_MODULE_ROUTE_CONTRACT",
        "source_node": SOURCE_NODE,
        "handler_role": GRADIENT_ROLE,
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
    }}
'''


def _generated_test_code(child_path: str) -> str:
    return f'''import importlib.util
import json
import unittest
from pathlib import Path


CHILD_PATH = Path({child_path!r})
REPORT_PATH = Path("reports/d75_differentiation_scaffold_package.json")


def load_child_module():
    spec = importlib.util.spec_from_file_location("d75_generated_child_module", CHILD_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestD75GeneratedChildModule(unittest.TestCase):
    def test_child_probe_is_sandbox_only(self):
        self.assertTrue(CHILD_PATH.exists())
        module = load_child_module()
        result = module.run_sandbox_probe({{"kind": "D75_TEST"}})

        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], "D75_DIFFERENTIATED_CHILD_MODULE")
        self.assertFalse(result["guardrails"]["protected_core_mutated"])
        self.assertFalse(result["guardrails"]["canonical_memory_mutated"])
        self.assertFalse(result["guardrails"]["actual_apply_executed"])
        self.assertTrue(result["guardrails"]["sandbox_only"])

    def test_route_contract_requires_guards(self):
        module = load_child_module()
        contract = module.propose_route_contract()

        self.assertTrue(contract["ok"])
        self.assertEqual(contract["allowed_mode"], "SANDBOX_PROBE_ONLY")
        self.assertIn("D66_RECHECK", contract["required_before_integration"])
        self.assertIn("direct_core_edit", contract["forbidden_actions"])

    def test_report_points_to_child(self):
        self.assertTrue(REPORT_PATH.exists())
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(report["scaffold_package"]["child_module_path"], str(CHILD_PATH))
        self.assertFalse(report["guardrails"]["actual_apply_executed"])


if __name__ == "__main__":
    unittest.main()
'''


def _select_candidate(d74: Dict[str, Any], candidate_index: int = 0) -> Dict[str, Any]:
    plan = d74.get("differentiation_plan") if isinstance(d74.get("differentiation_plan"), dict) else {}
    candidates = plan.get("candidates") if isinstance(plan.get("candidates"), list) else []
    if not candidates:
        return {}
    if candidate_index < 0 or candidate_index >= len(candidates):
        candidate_index = 0
    value = candidates[candidate_index]
    return value if isinstance(value, dict) else {}


def build_differentiation_scaffold_package(
    root: str | Path = ".",
    d74_plan_path: str = DEFAULT_D74_PLAN,
    output_path: str = DEFAULT_OUTPUT,
    candidate_index: int = 0,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()
    d74 = _read_json(root_path / d74_plan_path, default={}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    if not d74:
        errors.append("D74 differentiation plan missing or unreadable")
    else:
        if d74.get("ok") is not True:
            errors.append("D74 ok flag is not true")
        if d74.get("decision") != "DIFFERENTIATION_PLAN_READY":
            errors.append(f"D74 decision is not DIFFERENTIATION_PLAN_READY: {d74.get('decision')}")
        guardrails = d74.get("guardrails") if isinstance(d74.get("guardrails"), dict) else {}
        if guardrails.get("actual_apply_executed") is not False:
            errors.append("D74 actual_apply_executed is not false")
        if guardrails.get("plan_only") is not True:
            errors.append("D74 plan_only is not true")

    candidate = _select_candidate(d74, candidate_index=candidate_index)
    if not candidate:
        errors.append("D74 has no differentiation candidates")

    child_path = _child_path(candidate) if candidate else ""
    test_path = _test_path_for_child(child_path) if child_path else ""

    if child_path and not child_path.startswith(CHILD_PREFIX):
        errors.append(f"D75 rejected child path outside sandbox differentiation prefix: {child_path}")
    if test_path and not test_path.startswith(TEST_PREFIX):
        errors.append(f"D75 rejected test path outside tests prefix: {test_path}")

    ok = len(errors) == 0

    created_files: List[str] = []
    if ok:
        init_path = root_path / CHILD_PREFIX / "__init__.py"
        init_path.parent.mkdir(parents=True, exist_ok=True)
        if not init_path.exists():
            init_path.write_text("", encoding="utf-8")
        created_files.append(str(init_path.relative_to(root_path)))

        child_abs = root_path / child_path
        child_abs.parent.mkdir(parents=True, exist_ok=True)
        child_abs.write_text(_child_code(candidate), encoding="utf-8")
        created_files.append(child_path)

        test_abs = root_path / test_path
        test_abs.parent.mkdir(parents=True, exist_ok=True)
        test_abs.write_text(_generated_test_code(child_path), encoding="utf-8")
        created_files.append(test_path)

    decision = "DIFFERENTIATION_SCAFFOLD_READY" if ok else "DIFFERENTIATION_SCAFFOLD_BLOCKED"
    result = "D75_DIFFERENTIATION_SCAFFOLD_CREATED" if ok else "D75_DIFFERENTIATION_SCAFFOLD_BLOCKED"

    scaffold_package = {
        "package_state": "D75_DIFFERENTIATION_SCAFFOLD_PACKAGE",
        "enabled": ok,
        "mode": "SANDBOX_ONLY_CHILD_MODULE_SCAFFOLD",
        "source_d74_plan": str(root_path / d74_plan_path),
        "selected_candidate": candidate,
        "child_module_path": child_path,
        "test_module_path": test_path,
        "created_files": created_files,
        "integration_status": "NOT_INTEGRATED",
        "required_before_integration": [
            "D66_RECHECK",
            "D73_PACKAGE_READY",
            "UNIT_TESTS",
            "REGRESSION_TESTS",
            "ROLLBACK_MANIFEST",
            "HUMAN_OR_HIGHER_POLICY_APPROVAL",
        ],
        "forbidden_actions": [
            "direct_core_edit",
            "overwrite_canonical_memory",
            "external_ai_call",
            "auto_apply_runtime_mutation",
        ],
    }

    report = {
        "state": "D75_DIFFERENTIATION_SCAFFOLD_PACKAGE",
        "result": result,
        "route": "FIELD_INTENT_DIFFERENTIATION_SCAFFOLD",
        "ok": ok,
        "decision": decision,
        "created_at": _now(),
        "scaffold_package": scaffold_package,
        "input_reports": {
            "d74_plan_path": str(root_path / d74_plan_path),
        },
        "evidence": {
            "d74_decision": d74.get("decision"),
            "d74_ok": d74.get("ok"),
            "source_node": candidate.get("source_node") if candidate else None,
            "gradient_role": candidate.get("gradient_role") if candidate else None,
            "child_module_path": child_path,
            "test_module_path": test_path,
        },
        "guardrails": {
            "sandbox_code_created": ok,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "scaffold_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "created_files_count": len(created_files),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
            "child_module_path": child_path,
            "test_module_path": test_path,
        },
        "success_condition": {
            "scaffold_created": ok,
            "actual_apply_executed": False,
            "protected_core_untouched": True,
            "next_step": "D76 can run child-module probes and prepare adapter contract, still without core mutation.",
        },
    }

    _write_json(root_path / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(build_differentiation_scaffold_package(), ensure_ascii=False, indent=2))
