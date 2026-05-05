import importlib.util
import json
import unittest
from pathlib import Path


CHILD_PATH = Path('runtime_experimental/differentiated_modules/01_app_orchestration_task_dispatcher_py_route_policy_child.py')
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
        result = module.run_sandbox_probe({"kind": "D75_TEST"})

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
