import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.field_memory_replay_runner import run_field_memory_replay


class TestD63FieldMemoryReplayRunner(unittest.TestCase):
    def test_replay_creates_report_and_bypass_decision(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "app/orchestration").mkdir(parents=True)
            (root / "runtime_experimental").mkdir(parents=True)
            (root / "memory").mkdir(parents=True)
            (root / "reports").mkdir(parents=True)

            (root / "app/orchestration/task_dispatcher.py").write_text("x = 1\n", encoding="utf-8")
            (root / "runtime_experimental/v_kernel_daemon.py").write_text("x = 1\n", encoding="utf-8")
            (root / "runtime_experimental/phase_resync_policy.py").write_text("x = 1\n", encoding="utf-8")

            (root / "runtime_experimental/core_guard_policy.json").write_text(
                json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py", "runtime_experimental/v_kernel_daemon.py", "runtime_experimental/phase_resync_policy.py"]}),
                encoding="utf-8",
            )

            bias_key = "field_intent:d3_o6:hex:phase_drift_hex"
            (root / "memory/field_intent_priority_bias.json").write_text(
                json.dumps({"biases": {bias_key: {"priority_boost_points": 30, "recommended_priority": "critical"}}}),
                encoding="utf-8",
            )
            (root / "memory/field_intent_memory.jsonl").write_text(
                json.dumps({"priority": "critical", "payload": {"resonance_vector": {"memory_key": "D3_O6", "phase_error": 0.34, "jitter": 0.03, "strength": 0.81}, "target_files": ["app/orchestration/task_dispatcher.py"]}}) + "\n",
                encoding="utf-8",
            )
            (root / "reports/d66_core_guard_reviewer_report.json").write_text(
                json.dumps({"state": "D66_CORE_GUARD_REVIEWER", "decision": "FORBIDDEN_CORE_MUTATION", "ok": False}),
                encoding="utf-8",
            )

            report = run_field_memory_replay(root=root, output_path="reports/d63_field_memory_replay_report.json")
            self.assertTrue((root / "reports/d63_field_memory_replay_report.json").exists())
            self.assertTrue(report["ok"])
            self.assertIn(report["macro_decision"]["decision"], {"PLAN_ISOLATED_BYPASS", "HOLD_CORE_LOCK"})
            self.assertFalse(report["success_condition"]["core_code_mutated"])
            self.assertFalse(report["success_condition"]["canonical_memory_mutated"])

    def test_replay_survives_missing_optional_reports(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "runtime_experimental").mkdir(parents=True)
            (root / "memory").mkdir(parents=True)
            (root / "reports").mkdir(parents=True)
            (root / "runtime_experimental/core_guard_policy.json").write_text(json.dumps({"protected_files": []}), encoding="utf-8")

            report = run_field_memory_replay(root=root, output_path="reports/d63_field_memory_replay_report.json")
            self.assertTrue(report["ok"])
            self.assertGreaterEqual(report["summary"]["warnings_count"], 1)


if __name__ == "__main__":
    unittest.main()
