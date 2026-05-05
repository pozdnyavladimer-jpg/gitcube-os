import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.guarded_apply_dry_run_package import build_guarded_apply_dry_run_package


class TestD73GuardedApplyDryRunPackage(unittest.TestCase):
    def make_valid_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)
        (root / "runtime_experimental/ai_bypass_proposals").mkdir(parents=True)
        (root / "app/orchestration").mkdir(parents=True)

        protected = "app/orchestration/task_dispatcher.py"
        candidate = "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"

        (root / protected).write_text("# protected dispatcher\n", encoding="utf-8")
        (root / candidate).write_text("def run_sandbox_probe(event=None):\n    return {'ok': True}\n", encoding="utf-8")

        route_diff = [
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
        ]

        (root / "runtime_experimental/core_guard_policy.json").write_text(
            json.dumps({"protected_files": [protected]}),
            encoding="utf-8",
        )
        (root / "reports/d72_reviewed_apply_plan.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "REVIEWED_APPLY_PLAN_READY",
                    "plan_id": "d72-test-plan",
                    "guardrails": {"actual_apply_executed": False, "plan_only": True},
                    "reviewed_apply_plan": {
                        "enabled": True,
                        "sandbox_candidates": [candidate],
                        "simulated_route_diff": route_diff,
                        "rollback_plan": {"required": True, "backup_targets": [protected]},
                    },
                }
            ),
            encoding="utf-8",
        )
        (root / "reports/d71_route_dry_run_simulation.json").write_text(
            json.dumps({"ok": True, "decision": "ROUTE_DRY_RUN_APPROVED"}),
            encoding="utf-8",
        )
        (root / "reports/d64_safe_mutation_gate_request.json").write_text(
            json.dumps({"ok": True, "decision": "CREATE_GUARDED_APPLY_REQUEST"}),
            encoding="utf-8",
        )
        return td, root, candidate, protected

    def test_creates_guarded_apply_dry_run_package(self):
        td, root, candidate, protected = self.make_valid_root()
        try:
            report = build_guarded_apply_dry_run_package(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "GUARDED_APPLY_DRY_RUN_PACKAGE_READY")
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertTrue(report["guardrails"]["package_only"])
            self.assertIn(candidate, report["dry_run_package"]["sandbox_candidates"])
            self.assertEqual(report["dry_run_package"]["backup_manifest"][0]["path"], protected)
            self.assertTrue((root / "reports/d73_guarded_apply_dry_run_package.json").exists())
        finally:
            td.cleanup()

    def test_blocks_when_d72_blocked(self):
        td, root, _, _ = self.make_valid_root()
        try:
            d72_path = root / "reports/d72_reviewed_apply_plan.json"
            data = json.loads(d72_path.read_text(encoding="utf-8"))
            data["ok"] = False
            data["decision"] = "REVIEWED_APPLY_PLAN_BLOCKED"
            d72_path.write_text(json.dumps(data), encoding="utf-8")

            report = build_guarded_apply_dry_run_package(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "GUARDED_APPLY_DRY_RUN_PACKAGE_BLOCKED")
            self.assertFalse(report["dry_run_package"]["enabled"])
        finally:
            td.cleanup()

    def test_blocks_without_route_diff(self):
        td, root, _, _ = self.make_valid_root()
        try:
            d72_path = root / "reports/d72_reviewed_apply_plan.json"
            data = json.loads(d72_path.read_text(encoding="utf-8"))
            data["reviewed_apply_plan"]["simulated_route_diff"] = []
            d72_path.write_text(json.dumps(data), encoding="utf-8")

            report = build_guarded_apply_dry_run_package(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "GUARDED_APPLY_DRY_RUN_PACKAGE_BLOCKED")
            self.assertGreaterEqual(report["summary"]["errors_count"], 1)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
