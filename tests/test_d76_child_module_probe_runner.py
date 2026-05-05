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
