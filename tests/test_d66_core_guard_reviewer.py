import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.core_guard_reviewer import review_core_mutation


POLICY = {
    "protected_files": [
        "runtime_experimental/v_kernel_daemon.py",
        "app/orchestration/task_dispatcher.py",
        "memory/field_intent_priority_bias.json",
    ],
    "forbidden_without_review": [
        "direct_core_edit",
        "validation_bypass",
        "canonical_memory_overwrite",
    ],
}


class TestD66CoreGuardReviewer(unittest.TestCase):
    def test_forbidden_core_mutation_without_two_eyes(self):
        with tempfile.TemporaryDirectory() as td:
            policy_path = Path(td) / "policy.json"
            report_path = Path(td) / "report.json"
            policy_path.write_text(json.dumps(POLICY), encoding="utf-8")

            proposal = {
                "target_files": ["app/orchestration/task_dispatcher.py"],
                "actions": ["direct_core_edit"],
                "validation": {
                    "unit_tests_passed": True,
                    "regression_passed": False,
                    "payload_preserved": True,
                },
            }

            report = review_core_mutation(
                proposal=proposal,
                policy_path=str(policy_path),
                report_path=str(report_path),
            )

            self.assertEqual(report["decision"], "FORBIDDEN_CORE_MUTATION")
            self.assertFalse(report["ok"])
            self.assertTrue(report_path.exists())

    def test_safe_isolated_module_with_two_eyes_approved(self):
        with tempfile.TemporaryDirectory() as td:
            policy_path = Path(td) / "policy.json"
            report_path = Path(td) / "report.json"
            policy_path.write_text(json.dumps(POLICY), encoding="utf-8")

            proposal = {
                "target_files": ["runtime_experimental/new_safe_policy.py"],
                "actions": ["create_isolated_module", "create_test"],
                "validation": {
                    "unit_tests_passed": True,
                    "regression_passed": True,
                    "daemon_smoke_passed": True,
                    "payload_preserved": True,
                    "backup_plan_exists": True,
                },
            }

            report = review_core_mutation(
                proposal=proposal,
                policy_path=str(policy_path),
                report_path=str(report_path),
            )

            self.assertEqual(report["decision"], "APPROVE")
            self.assertTrue(report["ok"])

    def test_memory_overwrite_without_backup_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            policy_path = Path(td) / "policy.json"
            report_path = Path(td) / "report.json"
            policy_path.write_text(json.dumps(POLICY), encoding="utf-8")

            proposal = {
                "target_files": ["memory/field_intent_priority_bias.json"],
                "actions": ["canonical_memory_overwrite"],
                "validation": {
                    "unit_tests_passed": True,
                    "regression_passed": True,
                    "payload_preserved": True,
                    "backup_plan_exists": False,
                },
            }

            report = review_core_mutation(
                proposal=proposal,
                policy_path=str(policy_path),
                report_path=str(report_path),
            )

            self.assertEqual(report["decision"], "UNSAFE_MEMORY_WRITE")
            self.assertFalse(report["ok"])


if __name__ == "__main__":
    unittest.main()
