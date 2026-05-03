import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.memory_apoptosis import run_memory_apoptosis


class TestD65MemoryApoptosis(unittest.TestCase):
    def test_inactive_bias_decays_without_overwriting_canonical(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "memory").mkdir()
            (root / "reports").mkdir()

            bias_path = root / "memory/field_intent_priority_bias.json"
            memory_path = root / "memory/field_intent_memory.jsonl"
            output_path = root / "memory/field_intent_priority_bias_decayed.json"
            report_path = root / "reports/d65_apoptosis_decay_report.json"

            bias_key = "field_intent:d3_o6:hex:phase_drift_hex"
            bias_path.write_text(
                json.dumps({"biases": {bias_key: {"priority_boost_points": 30, "recommended_priority": "critical"}}}),
                encoding="utf-8",
            )
            memory_path.write_text("", encoding="utf-8")

            report = run_memory_apoptosis(
                bias_path=str(bias_path),
                memory_path=str(memory_path),
                output_path=str(output_path),
                report_path=str(report_path),
                decay_points=10,
            )

            self.assertTrue(report["ok"])
            self.assertFalse(report["canonical_overwritten"])
            canonical = json.loads(bias_path.read_text(encoding="utf-8"))
            decayed = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(canonical["biases"][bias_key]["priority_boost_points"], 30)
            self.assertEqual(decayed["biases"][bias_key]["priority_boost_points"], 20)
            self.assertEqual(decayed["biases"][bias_key]["apoptosis"]["action"], "decay")

    def test_active_bias_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "memory").mkdir()
            (root / "reports").mkdir()

            bias_key = "field_intent:d3_o6:hex:phase_drift_hex"
            bias_path = root / "memory/field_intent_priority_bias.json"
            memory_path = root / "memory/field_intent_memory.jsonl"
            output_path = root / "memory/field_intent_priority_bias_decayed.json"
            report_path = root / "reports/d65_apoptosis_decay_report.json"

            bias_path.write_text(
                json.dumps({"biases": {bias_key: {"priority_boost_points": 30, "recommended_priority": "critical"}}}),
                encoding="utf-8",
            )
            memory_path.write_text(
                json.dumps({"payload": {"resonance_vector": {"memory_key": "D3_O6", "phase_error": 0.34, "jitter": 0.03}}}) + "\n",
                encoding="utf-8",
            )

            report = run_memory_apoptosis(
                bias_path=str(bias_path),
                memory_path=str(memory_path),
                output_path=str(output_path),
                report_path=str(report_path),
                decay_points=10,
            )

            self.assertTrue(report["ok"])
            decayed = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(decayed["biases"][bias_key]["priority_boost_points"], 30)
            self.assertEqual(decayed["biases"][bias_key]["apoptosis"]["action"], "preserve_or_reinforce")

    def test_missing_inputs_do_not_crash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "memory").mkdir()
            (root / "reports").mkdir()

            report = run_memory_apoptosis(
                bias_path=str(root / "memory/missing_bias.json"),
                memory_path=str(root / "memory/missing_memory.jsonl"),
                output_path=str(root / "memory/field_intent_priority_bias_decayed.json"),
                report_path=str(root / "reports/d65_apoptosis_decay_report.json"),
            )

            self.assertTrue(report["ok"])
            self.assertGreaterEqual(len(report["validation"]["warnings"]), 1)
            self.assertTrue(report["success_condition"]["invalid_memory_does_not_crash"])


if __name__ == "__main__":
    unittest.main()
