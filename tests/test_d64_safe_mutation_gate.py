import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.safe_mutation_gate import build_safe_mutation_gate_request


SANDBOX_FILE = "def run_sandbox_probe(event=None):\n    return {'ok': True}\n"


class TestD64SafeMutationGate(unittest.TestCase):
    def make_valid_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)
        (root / "runtime_experimental/ai_bypass_proposals").mkdir(parents=True)
        rel = "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"
        (root / rel).write_text(SANDBOX_FILE, encoding="utf-8")

        (root / "runtime_experimental/core_guard_policy.json").write_text(
            json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),
            encoding="utf-8",
        )
        (root / "reports/d70_sandbox_bundle_review.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "APPROVE_SANDBOX_BUNDLE",
                    "guardrails": {
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "sandbox_only": True,
                        "external_ai_called": False,
                        "d64_apply_allowed": True,
                    },
                }
            ),
            encoding="utf-8",
        )
        (root / "reports/d69_sandbox_patch_bundle.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "written_files": [rel],
                    "probe_results": [{"path": rel, "ok": True, "reason": "probe_ok"}],
                    "guardrails": {
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "sandbox_only": True,
                        "external_ai_called": False,
                    },
                }
            ),
            encoding="utf-8",
        )
        (root / "reports/d69_sandbox_patch_write_report.json").write_text(
            json.dumps({"validation": {"ok": True}}),
            encoding="utf-8",
        )
        (root / "reports/d63_field_memory_replay_report.json").write_text(
            json.dumps({"macro_decision": {"decision": "PLAN_ISOLATED_BYPASS"}}),
            encoding="utf-8",
        )
        return td, root, rel

    def test_creates_guarded_apply_request_when_d70_approved(self):
        td, root, rel = self.make_valid_root()
        try:
            report = build_safe_mutation_gate_request(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "CREATE_GUARDED_APPLY_REQUEST")
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertTrue(report["guardrails"]["gate_only"])
            self.assertIn(rel, report["sandbox_candidates"])
            self.assertTrue((root / "reports/d64_safe_mutation_gate_request.json").exists())
        finally:
            td.cleanup()

    def test_blocks_when_d70_rejected(self):
        td, root, _ = self.make_valid_root()
        try:
            (root / "reports/d70_sandbox_bundle_review.json").write_text(
                json.dumps({"ok": False, "decision": "REJECT_SANDBOX_BUNDLE"}),
                encoding="utf-8",
            )
            report = build_safe_mutation_gate_request(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "BLOCK_GUARDED_APPLY")
            self.assertFalse(report["guarded_apply_request"]["enabled"])
            self.assertGreaterEqual(report["summary"]["errors_count"], 1)
        finally:
            td.cleanup()

    def test_blocks_non_sandbox_candidate(self):
        td, root, _ = self.make_valid_root()
        try:
            (root / "reports/d69_sandbox_patch_bundle.json").write_text(
                json.dumps(
                    {
                        "ok": True,
                        "written_files": ["app/orchestration/task_dispatcher.py"],
                        "probe_results": [{"path": "app/orchestration/task_dispatcher.py", "ok": True}],
                        "guardrails": {
                            "runtime_code_mutated": False,
                            "protected_core_mutated": False,
                            "canonical_memory_mutated": False,
                            "sandbox_only": True,
                            "external_ai_called": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            report = build_safe_mutation_gate_request(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "BLOCK_GUARDED_APPLY")
            self.assertEqual(report["summary"]["sandbox_candidates_count"], 0)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
