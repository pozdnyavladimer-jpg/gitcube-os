import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.route_dry_run_simulator import simulate_route_dry_run


class TestD71RouteDryRunSimulator(unittest.TestCase):
    def make_valid_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)
        (root / "runtime_experimental/ai_bypass_proposals").mkdir(parents=True)

        rel = "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"
        (root / rel).write_text("def run_sandbox_probe(event=None):\\n    return {'ok': True}\\n", encoding="utf-8")

        (root / "runtime_experimental/core_guard_policy.json").write_text(
            json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),
            encoding="utf-8",
        )
        (root / "reports/d64_safe_mutation_gate_request.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "CREATE_GUARDED_APPLY_REQUEST",
                    "guarded_apply_request": {"enabled": True, "sandbox_candidates": [rel]},
                    "guardrails": {"actual_apply_executed": False, "gate_only": True},
                    "evidence": {
                        "macro_decision": {
                            "decision": "PLAN_ISOLATED_BYPASS",
                            "targets": ["app/orchestration/task_dispatcher.py"],
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        (root / "reports/d70_sandbox_bundle_review.json").write_text(
            json.dumps({"ok": True, "decision": "APPROVE_SANDBOX_BUNDLE"}),
            encoding="utf-8",
        )
        (root / "reports/d69_sandbox_patch_bundle.json").write_text(
            json.dumps({"ok": True, "written_files": [rel]}),
            encoding="utf-8",
        )
        return td, root, rel

    def test_creates_dry_run_route_diff(self):
        td, root, rel = self.make_valid_root()
        try:
            report = simulate_route_dry_run(root=root)
            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "ROUTE_DRY_RUN_APPROVED")
            self.assertEqual(report["summary"]["simulated_route_diff_count"], 1)
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertTrue(report["guardrails"]["dry_run_only"])
            self.assertEqual(report["simulated_route_diff"][0]["sandbox_handler"], rel)
            self.assertFalse(report["simulated_route_diff"][0]["would_touch_protected_core"])
        finally:
            td.cleanup()

    def test_blocks_when_d64_not_enabled(self):
        td, root, _ = self.make_valid_root()
        try:
            (root / "reports/d64_safe_mutation_gate_request.json").write_text(
                json.dumps(
                    {
                        "ok": False,
                        "decision": "BLOCK_GUARDED_APPLY",
                        "guarded_apply_request": {"enabled": False, "sandbox_candidates": []},
                        "guardrails": {"actual_apply_executed": False, "gate_only": True},
                    }
                ),
                encoding="utf-8",
            )
            report = simulate_route_dry_run(root=root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "ROUTE_DRY_RUN_BLOCKED")
            self.assertGreaterEqual(report["summary"]["errors_count"], 1)
        finally:
            td.cleanup()

    def test_blocks_non_sandbox_candidate(self):
        td, root, _ = self.make_valid_root()
        try:
            (root / "reports/d64_safe_mutation_gate_request.json").write_text(
                json.dumps(
                    {
                        "ok": True,
                        "decision": "CREATE_GUARDED_APPLY_REQUEST",
                        "guarded_apply_request": {
                            "enabled": True,
                            "sandbox_candidates": ["app/orchestration/task_dispatcher.py"],
                        },
                        "guardrails": {"actual_apply_executed": False, "gate_only": True},
                    }
                ),
                encoding="utf-8",
            )
            report = simulate_route_dry_run(root=root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "ROUTE_DRY_RUN_BLOCKED")
            self.assertEqual(report["summary"]["simulated_route_diff_count"], 0)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
