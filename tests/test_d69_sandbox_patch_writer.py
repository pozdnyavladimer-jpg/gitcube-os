import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_patch_writer import write_sandbox_patch_bundle


class TestD69SandboxPatchWriter(unittest.TestCase):
    def test_writes_sandbox_files_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)
            (root / "runtime_experimental").mkdir(parents=True)

            (root / "runtime_experimental/core_guard_policy.json").write_text(
                json.dumps(
                    {
                        "protected_files": [
                            "app/orchestration/task_dispatcher.py",
                            "runtime_experimental/v_kernel_daemon.py",
                        ]
                    }
                ),
                encoding="utf-8",
            )

            (root / "reports/d68_ai_patch_proposal.json").write_text(
                json.dumps(
                    {
                        "state": "D68_AI_PATCH_PROPOSAL",
                        "proposed_action": "CREATE_ISOLATED_BYPASS_MODULE",
                        "decision_source": "PLAN_ISOLATED_BYPASS",
                        "priority": "critical",
                        "hot_targets": ["app/orchestration/task_dispatcher.py"],
                        "candidate_created_files": [
                            "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"
                        ],
                        "validation_gates": ["D66_CORE_GUARD_REVIEW_REQUIRED"],
                    }
                ),
                encoding="utf-8",
            )

            report = write_sandbox_patch_bundle(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["summary"]["written_files_count"], 1)
            self.assertTrue((root / "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py").exists())
            self.assertFalse((root / "app/orchestration/task_dispatcher.py").exists())
            self.assertTrue(report["success_condition"]["protected_core_untouched"])
            self.assertTrue(report["success_condition"]["canonical_memory_untouched"])

    def test_rejects_candidate_outside_sandbox(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)
            (root / "runtime_experimental").mkdir(parents=True)

            (root / "runtime_experimental/core_guard_policy.json").write_text(
                json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),
                encoding="utf-8",
            )

            (root / "reports/d68_ai_patch_proposal.json").write_text(
                json.dumps(
                    {
                        "state": "D68_AI_PATCH_PROPOSAL",
                        "candidate_created_files": [
                            "app/orchestration/task_dispatcher.py"
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = write_sandbox_patch_bundle(root=root)

            self.assertTrue(report["ok"])
            self.assertGreaterEqual(report["summary"]["rejected_files_count"], 1)
            self.assertTrue((root / "runtime_experimental/ai_bypass_proposals/monitor_only_bypass_proposal.py").exists())
            self.assertFalse((root / "app/orchestration/task_dispatcher.py").exists())

    def test_missing_contract_creates_monitor_only_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)

            report = write_sandbox_patch_bundle(root=root)

            self.assertTrue(report["ok"])
            self.assertGreaterEqual(report["summary"]["warnings_count"], 1)
            self.assertTrue(report["success_condition"]["sandbox_files_written"])


if __name__ == "__main__":
    unittest.main()
