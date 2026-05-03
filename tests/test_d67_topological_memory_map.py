import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.topological_memory_map import build_topological_memory_map


class TestD67TopologicalMemoryMap(unittest.TestCase):
    def test_tenuki_for_protected_stressed_core(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "app/orchestration").mkdir(parents=True)
            (root / "runtime_experimental").mkdir(parents=True)
            (root / "memory").mkdir(parents=True)
            (root / "reports").mkdir(parents=True)

            (root / "app/orchestration/task_dispatcher.py").write_text(
                "from runtime_experimental.phase_resync_policy import compute_phase_resync\n",
                encoding="utf-8",
            )
            (root / "runtime_experimental/phase_resync_policy.py").write_text(
                "def compute_phase_resync(x):\n    return x\n",
                encoding="utf-8",
            )
            (root / "runtime_experimental/core_guard_policy.json").write_text(
                json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),
                encoding="utf-8",
            )
            (root / "memory/field_intent_memory.jsonl").write_text(
                json.dumps({
                    "priority": "critical",
                    "payload": {
                        "target_files": ["app/orchestration/task_dispatcher.py"],
                        "resonance_vector": {
                            "memory_key": "D3_O6",
                            "phase_error": 0.34,
                            "jitter": 0.03,
                            "strength": 0.81
                        }
                    }
                }) + "\n",
                encoding="utf-8",
            )
            (root / "memory/field_intent_priority_bias.json").write_text(
                json.dumps({
                    "biases": {
                        "field_intent:d3_o6:hex:phase_drift_hex": {
                            "priority_boost_points": 30,
                            "recommended_priority": "critical"
                        }
                    }
                }),
                encoding="utf-8",
            )

            result = build_topological_memory_map(
                root=str(root),
                policy_path=str(root / "runtime_experimental/core_guard_policy.json"),
                memory_path=str(root / "memory/field_intent_memory.jsonl"),
                bias_path=str(root / "memory/field_intent_priority_bias.json"),
                map_path=str(root / "reports/map.json"),
                report_path=str(root / "reports/report.json"),
            )

            nodes = {n["id"]: n for n in result["nodes"]}
            node = nodes["app/orchestration/task_dispatcher.py"]
            self.assertTrue(node["protected_core"])
            self.assertGreaterEqual(node["pain_score"], 0.45)
            self.assertEqual(node["suggested_move"]["move_type"], "TENUKI")

    def test_stable_module_is_stable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "runtime_experimental").mkdir(parents=True)
            (root / "reports").mkdir(parents=True)
            (root / "runtime_experimental/stable.py").write_text("x = 1\n", encoding="utf-8")
            (root / "runtime_experimental/core_guard_policy.json").write_text(
                json.dumps({"protected_files": []}),
                encoding="utf-8",
            )

            result = build_topological_memory_map(
                root=str(root),
                policy_path=str(root / "runtime_experimental/core_guard_policy.json"),
                memory_path=str(root / "memory/missing.jsonl"),
                bias_path=str(root / "memory/missing.json"),
                map_path=str(root / "reports/map.json"),
                report_path=str(root / "reports/report.json"),
            )

            nodes = {n["id"]: n for n in result["nodes"]}
            self.assertEqual(nodes["runtime_experimental/stable.py"]["recommendation"], "stable")


if __name__ == "__main__":
    unittest.main()
