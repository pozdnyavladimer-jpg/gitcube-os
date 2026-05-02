import json
import unittest
from pathlib import Path


class TestD46D60ClosedLoopPolicy(unittest.TestCase):
    def test_d60_closed_loop_policy_locked(self):
        p = Path("memory/field_intent_closed_loop_policy.json")
        self.assertTrue(p.exists(), "D60 closed-loop policy file missing")

        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(data.get("state"), "D60_FIELD_INTENT_CLOSED_LOOP_MEMORY_POLICY")
        self.assertEqual(data.get("result"), "CLOSED_LOOP_POLICY_LOCKED")
        self.assertIs(data.get("locked"), True)

        scope = data.get("scope", {})
        self.assertEqual(scope.get("memory_key"), "D3_O6")
        self.assertEqual(scope.get("orbital_mode"), "HEX")
        self.assertEqual(scope.get("field_case"), "PHASE_DRIFT_HEX")

        loop = data.get("closed_loop", {})
        self.assertIs(loop.get("d56_memory_write"), True)
        self.assertIs(loop.get("d57_memory_recall"), True)
        self.assertIs(loop.get("d58_memory_bias_created"), True)
        self.assertIs(loop.get("d59_dispatch_bias_applied"), True)

    def test_d58_bias_store_contains_d3_o6_hex_phase_drift(self):
        p = Path("memory/field_intent_priority_bias.json")
        self.assertTrue(p.exists(), "D58 bias store missing")

        data = json.loads(p.read_text(encoding="utf-8"))
        biases = data.get("biases", {})
        key = "field_intent:d3_o6:hex:phase_drift_hex"

        self.assertIn(key, biases)
        bias = biases[key]

        self.assertEqual(bias.get("recommended_priority"), "critical")
        self.assertGreaterEqual(bias.get("priority_boost_points", 0), 30)
        self.assertEqual(bias.get("memory_key"), "D3_O6")
        self.assertEqual(bias.get("orbital_mode"), "HEX")
        self.assertEqual(bias.get("field_case"), "PHASE_DRIFT_HEX")

    def test_d56_memory_contains_recalled_atom(self):
        p = Path("memory/field_intent_memory.jsonl")
        self.assertTrue(p.exists(), "field intent memory file missing")

        lines = [line for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertTrue(lines, "field intent memory is empty")

        atoms = [json.loads(line) for line in lines]
        matches = [
            atom for atom in atoms
            if atom.get("memory_key") == "D3_O6"
            and atom.get("orbital_mode") == "HEX"
            and atom.get("field_case") == "PHASE_DRIFT_HEX"
        ]

        self.assertTrue(matches, "D3_O6 HEX PHASE_DRIFT_HEX memory atom not found")

    def test_d59_dispatch_probe_applied_bias(self):
        p = Path("reports/d59_memory_priority_bias_dispatch_probe.json")
        self.assertTrue(p.exists(), "D59 dispatch probe report missing")

        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(data.get("result"), "MEMORY_PRIORITY_BIAS_APPLIED")
        self.assertIs(data.get("memory_bias_applied"), True)
        self.assertIn(data.get("priority_before_memory_bias"), ["low", "normal"])
        self.assertEqual(data.get("priority_after_memory_bias"), "critical")
        self.assertEqual(data.get("task_priority_after_prepare"), "critical")


if __name__ == "__main__":
    unittest.main()
