import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.narrow_adapter_contract import build_narrow_adapter_contract


class TestD77NarrowAdapterContract(unittest.TestCase):
    def make_valid_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)

        child = "runtime_experimental/differentiated_modules/01_route_policy_child.py"
        source = "app/orchestration/task_dispatcher.py"

        (root / "reports/d76_child_module_probe_report.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "CHILD_MODULE_PROBE_PASSED",
                    "guardrails": {"actual_apply_executed": False, "probe_only": True},
                    "probe_target": {"child_module_path": child},
                    "module_description": {
                        "source_node": source,
                        "gradient_role": "route_policy_child",
                    },
                    "route_contract": {
                        "ok": True,
                        "contract": "D75_CHILD_MODULE_ROUTE_CONTRACT",
                        "source_node": source,
                        "handler_role": "route_policy_child",
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
                    },
                }
            ),
            encoding="utf-8",
        )
        (root / "reports/d75_differentiation_scaffold_package.json").write_text(
            json.dumps({"ok": True, "decision": "DIFFERENTIATION_SCAFFOLD_READY"}),
            encoding="utf-8",
        )
        (root / "reports/d74_differentiation_plan.json").write_text(
            json.dumps({"ok": True, "decision": "DIFFERENTIATION_PLAN_READY"}),
            encoding="utf-8",
        )
        return td, root, child, source

    def test_creates_narrow_adapter_contract(self):
        td, root, child, source = self.make_valid_root()
        try:
            report = build_narrow_adapter_contract(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "NARROW_ADAPTER_CONTRACT_READY")
            self.assertEqual(report["narrow_adapter_contract"]["child_module_path"], child)
            self.assertEqual(report["narrow_adapter_contract"]["source_node"], source)
            self.assertFalse(report["narrow_adapter_contract"]["route_policy"]["route_insert_allowed_now"])
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertTrue(report["guardrails"]["contract_only"])
            self.assertTrue((root / "reports/d77_narrow_adapter_contract.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d76(self):
        td, root, _, _ = self.make_valid_root()
        try:
            (root / "reports/d76_child_module_probe_report.json").unlink()
            report = build_narrow_adapter_contract(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "NARROW_ADAPTER_CONTRACT_BLOCKED")
            self.assertGreaterEqual(report["summary"]["errors_count"], 1)
        finally:
            td.cleanup()

    def test_blocks_missing_required_gate(self):
        td, root, _, _ = self.make_valid_root()
        try:
            path = root / "reports/d76_child_module_probe_report.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["route_contract"]["required_before_integration"].remove("D66_RECHECK")
            path.write_text(json.dumps(data), encoding="utf-8")

            report = build_narrow_adapter_contract(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "NARROW_ADAPTER_CONTRACT_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
