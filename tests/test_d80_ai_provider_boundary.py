import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.ai_provider_boundary import create_ai_provider_boundary


class TestD80AIProviderBoundary(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)
        (root / "runtime_experimental/differentiated_modules").mkdir(parents=True)
        (root / "app/orchestration").mkdir(parents=True)

        source = "app/orchestration/task_dispatcher.py"
        child = "runtime_experimental/differentiated_modules/01_route_policy_child.py"
        adapter = "D77_NARROW_ADAPTER_ROUTE_POLICY_CHILD"

        (root / source).write_text("# source unchanged\n", encoding="utf-8")
        (root / child).write_text("def run_sandbox_probe(event=None): return {'ok': True}\n", encoding="utf-8")

        (root / "reports/d79_policy_verification_gate.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "POLICY_VERIFIED_DRY_RUN_READY",
                    "gate_id": "d79-test-gate",
                    "policy_verdict": {
                        "verdict": "DRY_RUN_POLICY_APPROVED",
                        "scope": "dry_run_diff_only",
                        "real_route_insert_allowed": False,
                        "real_apply_allowed": False,
                        "ai_provider_allowed": False,
                    },
                    "evidence": {
                        "source_node": source,
                        "child_module_path": child,
                        "adapter_name": adapter,
                    },
                    "guardrails": {
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "external_ai_called": False,
                        "actual_apply_executed": False,
                        "route_inserted": False,
                        "policy_gate_only": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        return td, root, source

    def test_creates_mock_propose_only_boundary(self):
        td, root, source = self.make_root()
        try:
            before = (root / source).read_text(encoding="utf-8")
            report = create_ai_provider_boundary(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "AI_PROVIDER_BOUNDARY_READY")
            self.assertEqual(report["boundary"]["mode"], "PROPOSE_ONLY")
            self.assertFalse(report["boundary"]["external_ai_call_allowed"])
            self.assertFalse(report["boundary"]["actual_apply_allowed"])
            self.assertFalse(report["guardrails"]["external_ai_called"])
            self.assertEqual((root / source).read_text(encoding="utf-8"), before)
            self.assertTrue((root / "reports/d80_ai_provider_boundary.json").exists())
            self.assertTrue((root / "reports/d80_ai_provider_mock_proposal.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d79(self):
        td, root, _ = self.make_root()
        try:
            (root / "reports/d79_policy_verification_gate.json").unlink()
            report = create_ai_provider_boundary(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "AI_PROVIDER_BOUNDARY_BLOCKED")
            self.assertGreaterEqual(report["summary"]["errors_count"], 1)
        finally:
            td.cleanup()

    def test_external_provider_request_is_blocked_to_mock(self):
        td, root, _ = self.make_root()
        try:
            report = create_ai_provider_boundary(root=root, provider="external_openai")

            self.assertTrue(report["ok"])
            self.assertEqual(report["boundary"]["provider"], "mock_local")
            self.assertFalse(report["boundary"]["network_access_allowed"])
            self.assertGreaterEqual(report["summary"]["warnings_count"], 1)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
