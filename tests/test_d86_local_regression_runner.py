import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.local_regression_runner import create_local_regression_runner


class TestD86LocalRegressionRunner(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)

        (root / "reports/d85_regression_rollback_evidence.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "REGRESSION_ROLLBACK_EVIDENCE_READY",
                    "package_id": "d85-test-package",
                    "evidence": {"review_id": "d84-test-review"},
                    "guardrails": {
                        "external_ai_called": False,
                        "network_accessed": False,
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "actual_apply_executed": False,
                        "route_inserted": False,
                        "git_commit_by_ai": False,
                        "rollback_evidence_only": True,
                        "regression_evidence_only": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d85_rollback_manifest.json").write_text(
            json.dumps(
                {
                    "package_id": "d85-test-package",
                    "human_review_required": True,
                    "actual_rollback_executed": False,
                    "actual_apply_executed": False,
                    "route_inserted": False,
                    "protected_core_touched": False,
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d85_regression_checklist.json").write_text(
            json.dumps(
                {
                    "package_id": "d85-test-package",
                    "pass_condition": {
                        "all_tests_green": True,
                        "rollback_manifest_present": True,
                        "no_protected_core_mutation": True,
                        "no_route_insert": True,
                        "no_actual_apply": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        return td, root

    def test_creates_local_regression_results(self):
        td, root = self.make_root()
        try:
            report = create_local_regression_runner(root=root, execute_commands=False)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "LOCAL_REGRESSION_PASSED")
            self.assertTrue(report["guardrails"]["allowlisted_commands_only"])
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertEqual(report["summary"]["commands_failed_count"], 0)
            self.assertTrue((root / "reports/d86_local_regression_runner.json").exists())
            self.assertTrue((root / "reports/d86_local_regression_results.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d85(self):
        td, root = self.make_root()
        try:
            (root / "reports/d85_regression_rollback_evidence.json").unlink()
            report = create_local_regression_runner(root=root, execute_commands=False)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "LOCAL_REGRESSION_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_d85_apply_flag(self):
        td, root = self.make_root()
        try:
            p = root / "reports/d85_regression_rollback_evidence.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["guardrails"]["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")

            report = create_local_regression_runner(root=root, execute_commands=False)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "LOCAL_REGRESSION_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
