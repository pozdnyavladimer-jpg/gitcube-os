import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.ai_patch_proposal_adapter import build_ai_patch_proposal


class TestD68AIPatchProposalAdapter(unittest.TestCase):
    def test_builds_isolated_bypass_contract_without_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)
            (root / "runtime_experimental").mkdir(parents=True)
            (root / "reports/d63_field_memory_replay_report.json").write_text(
                json.dumps({"macro_decision": {"decision": "PLAN_ISOLATED_BYPASS", "priority": "critical", "targets": ["app/orchestration/task_dispatcher.py", "runtime_experimental/v_kernel_daemon.py"]}}),
                encoding="utf-8",
            )
            (root / "reports/d67_topological_memory_map.json").write_text(
                json.dumps({"suggested_moves": [{"target": "app/orchestration/task_dispatcher.py", "move_type": "TENUKI", "protected_core": True, "pain_score": 0.8125}]}),
                encoding="utf-8",
            )
            (root / "reports/d66_core_guard_reviewer_report.json").write_text(
                json.dumps({"decision": "FORBIDDEN_CORE_MUTATION", "ok": False}), encoding="utf-8"
            )
            (root / "runtime_experimental/core_guard_policy.json").write_text(
                json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}), encoding="utf-8"
            )
            report = build_ai_patch_proposal(root=root, output_path="reports/d68_ai_patch_proposal.json")
            self.assertTrue(report["ok"])
            self.assertEqual(report["proposed_action"], "CREATE_ISOLATED_BYPASS_MODULE")
            self.assertTrue(report["guardrails"]["proposal_only"])
            self.assertFalse(report["guardrails"]["external_ai_called"])
            self.assertFalse(report["guardrails"]["protected_core_mutated"])
            self.assertIn("D66_CORE_GUARD_REVIEW_REQUIRED", report["validation_gates"])
            self.assertTrue((root / "reports/d68_ai_patch_proposal.json").exists())

    def test_missing_inputs_still_creates_hold_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)
            report = build_ai_patch_proposal(root=root, output_path="reports/d68_ai_patch_proposal.json")
            self.assertTrue(report["ok"])
            self.assertEqual(report["proposed_action"], "NO_CODE_CHANGE_MONITOR")
            self.assertGreaterEqual(report["summary"]["warnings_count"], 1)
            self.assertTrue(report["success_condition"]["proposal_contract_created"])


if __name__ == "__main__":
    unittest.main()
