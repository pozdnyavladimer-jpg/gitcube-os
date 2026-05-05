import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.reviewed_apply_plan import build_reviewed_apply_plan


class TestD72ReviewedApplyPlan(unittest.TestCase):
    def make_valid_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)
        (root / "runtime_experimental/ai_bypass_proposals").mkdir(parents=True)

        candidate = "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"
        (root / candidate).write_text("def run_sandbox_probe(event=None):\n    return {'ok': True}\n", encoding="utf-8")

        (root / "runtime_experimental/core_guard_policy.json").write_text(
            json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),
            encoding="utf-8",
        )
        (root / "reports/d64_safe_mutation_gate_request.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "CREATE_GUARDED_APPLY_REQUEST",
                    "guarded_apply_request": {"enabled": True, "sandbox_candidates": [candidate]},
                    "guardrails": {"actual_apply_executed": False, "gate_only": True},
                }
            ),
            encoding="utf-8",
        )
        (root / "reports/d71_route_dry_run_simulation.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "ROUTE_DRY_RUN_APPROVED",
                    "target_scope": ["app/orchestration/task_dispatcher.py"],
                    "guardrails": {"actual_apply_executed": False, "dry_run_only": True},
                    "simulated_route_diff": [
                        {
                            "operation": "SIMULATE_ROUTE_INSERT",
                            "route_name": "DRY_RUN_DISPATCHER_BYPASS_PROPOSAL",
                            "sandbox_handler": candidate,
                            "would_touch_files": [],
                            "would_touch_protected_core": False,
                            "would_touch_canonical_memory": False,
                            "would_execute_runtime_mutation": False,
                            "dry_run_only": True,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return td, root, candidate

    def test_creates_reviewed_apply_plan(self):
        td, root, candidate = self.make_valid_root()
        try:
            report = build_reviewed_apply_plan(root=root)
            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "REVIEWED_APPLY_PLAN_READY")
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertTrue(report["guardrails"]["plan_only"])
            self.assertIn(candidate, report["reviewed_apply_plan"]["sandbox_candidates"])
            self.assertTrue(report["reviewed_apply_plan"]["rollback_plan"]["required"])
            self.assertTrue((root / "reports/d72_reviewed_apply_plan.json").exists())
        finally:
            td.cleanup()

    def test_blocks_when_d71_rejected(self):
        td, root, _ = self.make_valid_root()
        try:
            (root / "reports/d71_route_dry_run_simulation.json").write_text(
                json.dumps(
                    {
                        "ok": False,
                        "decision": "ROUTE_DRY_RUN_BLOCKED",
                        "guardrails": {"actual_apply_executed": False, "dry_run_only": True},
                        "simulated_route_diff": [],
                    }
                ),
                encoding="utf-8",
            )
            report = build_reviewed_apply_plan(root=root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "REVIEWED_APPLY_PLAN_BLOCKED")
            self.assertFalse(report["reviewed_apply_plan"]["enabled"])
        finally:
            td.cleanup()

    def test_blocks_route_diff_that_touches_core(self):
        td, root, candidate = self.make_valid_root()
        try:
            d71 = json.loads((root / "reports/d71_route_dry_run_simulation.json").read_text(encoding="utf-8"))
            d71["simulated_route_diff"][0]["would_touch_protected_core"] = True
            (root / "reports/d71_route_dry_run_simulation.json").write_text(json.dumps(d71), encoding="utf-8")

            report = build_reviewed_apply_plan(root=root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "REVIEWED_APPLY_PLAN_BLOCKED")
            self.assertGreaterEqual(report["summary"]["errors_count"], 1)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
