import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.differentiation_scaffold_package import build_differentiation_scaffold_package


class TestD75DifferentiationScaffoldPackage(unittest.TestCase):
    def make_valid_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)

        candidate = {
            "source_node": "app/orchestration/task_dispatcher.py",
            "pain_score": 0.91,
            "protected_core": True,
            "gradient_role": "route_policy_child",
            "gradient_intent": "separate routing pressure from core dispatcher",
            "recommended_child_module": "runtime_experimental/differentiated_modules/01_app_orchestration_task_dispatcher_py_route_policy_child.py",
            "old_node_policy": "do_not_expand_directly",
        }

        (root / "reports/d74_differentiation_plan.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "DIFFERENTIATION_PLAN_READY",
                    "guardrails": {"actual_apply_executed": False, "plan_only": True},
                    "differentiation_plan": {"enabled": True, "candidates": [candidate]},
                }
            ),
            encoding="utf-8",
        )
        return td, root, candidate

    def test_creates_sandbox_child_module_and_test(self):
        td, root, candidate = self.make_valid_root()
        try:
            report = build_differentiation_scaffold_package(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "DIFFERENTIATION_SCAFFOLD_READY")
            self.assertTrue(report["guardrails"]["sandbox_code_created"])
            self.assertFalse(report["guardrails"]["protected_core_mutated"])
            self.assertFalse(report["guardrails"]["actual_apply_executed"])

            child = root / report["scaffold_package"]["child_module_path"]
            test = root / report["scaffold_package"]["test_module_path"]
            self.assertTrue(child.exists())
            self.assertTrue(test.exists())
            self.assertTrue(str(child.relative_to(root)).startswith("runtime_experimental/differentiated_modules/"))
            self.assertTrue((root / "reports/d75_differentiation_scaffold_package.json").exists())
        finally:
            td.cleanup()

    def test_blocks_when_d74_missing(self):
        td, root, _ = self.make_valid_root()
        try:
            (root / "reports/d74_differentiation_plan.json").unlink()
            report = build_differentiation_scaffold_package(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "DIFFERENTIATION_SCAFFOLD_BLOCKED")
            self.assertFalse(report["scaffold_package"]["enabled"])
            self.assertGreaterEqual(report["summary"]["errors_count"], 1)
        finally:
            td.cleanup()

    def test_rejects_child_path_outside_sandbox_prefix(self):
        td, root, candidate = self.make_valid_root()
        try:
            candidate["recommended_child_module"] = "app/orchestration/task_dispatcher.py"
            (root / "reports/d74_differentiation_plan.json").write_text(
                json.dumps(
                    {
                        "ok": True,
                        "decision": "DIFFERENTIATION_PLAN_READY",
                        "guardrails": {"actual_apply_executed": False, "plan_only": True},
                        "differentiation_plan": {"enabled": True, "candidates": [candidate]},
                    }
                ),
                encoding="utf-8",
            )

            report = build_differentiation_scaffold_package(root=root)

            self.assertTrue(report["ok"])
            self.assertTrue(report["scaffold_package"]["child_module_path"].startswith("runtime_experimental/differentiated_modules/"))
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
