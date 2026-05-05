
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.differentiation_planner import build_differentiation_plan


class TestD74DifferentiationPlanner(unittest.TestCase):
    def make_valid_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)
        (root / "runtime_experimental").mkdir(parents=True)
        target = "app/orchestration/task_dispatcher.py"

        (root / "runtime_experimental/core_guard_policy.json").write_text(
            json.dumps({"protected_files": [target]}), encoding="utf-8"
        )
        (root / "reports/d73_guarded_apply_dry_run_package.json").write_text(
            json.dumps({
                "ok": True,
                "decision": "GUARDED_APPLY_DRY_RUN_PACKAGE_READY",
                "guardrails": {"actual_apply_executed": False, "package_only": True},
                "dry_run_package": {
                    "sandbox_candidates": ["runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"],
                    "simulated_route_diff": [{"target_scope": [target]}],
                },
            }), encoding="utf-8"
        )
        (root / "reports/d67_topological_memory_map_report.json").write_text(
            json.dumps({
                "result": "D67_MAP_BUILD_COMPLETED",
                "top_suggested_moves": [{
                    "target": target,
                    "pain_score": 0.91,
                    "move_type": "TENUKI",
                    "reason": "protected core has stress; direct expansion risks core mutation",
                }],
            }), encoding="utf-8"
        )
        return td, root, target

    def test_creates_differentiation_plan(self):
        td, root, target = self.make_valid_root()
        try:
            report = build_differentiation_plan(root=root)
            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "DIFFERENTIATION_PLAN_READY")
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertTrue(report["guardrails"]["plan_only"])
            self.assertGreaterEqual(report["summary"]["candidate_count"], 1)
            candidate = report["differentiation_plan"]["candidates"][0]
            self.assertEqual(candidate["source_node"], target)
            self.assertTrue(candidate["protected_core"])
            self.assertEqual(candidate["old_node_policy"], "do_not_expand_directly")
            self.assertTrue((root / "reports/d74_differentiation_plan.json").exists())
        finally:
            td.cleanup()

    def test_blocks_when_d73_missing(self):
        td, root, _ = self.make_valid_root()
        try:
            (root / "reports/d73_guarded_apply_dry_run_package.json").unlink()
            report = build_differentiation_plan(root=root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "DIFFERENTIATION_PLAN_BLOCKED")
        finally:
            td.cleanup()

    def test_falls_back_to_d73_targets_without_d67(self):
        td, root, _ = self.make_valid_root()
        try:
            (root / "reports/d67_topological_memory_map_report.json").unlink()
            report = build_differentiation_plan(root=root)
            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "DIFFERENTIATION_PLAN_READY")
            self.assertGreaterEqual(report["summary"]["warnings_count"], 1)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
