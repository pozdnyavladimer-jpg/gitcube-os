import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.regression_rollback_evidence import create_regression_rollback_evidence


class TestD85RegressionRollbackEvidence(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)
        (root / "runtime_experimental/ai_sandbox_work/d84-test").mkdir(parents=True)

        writer_output = root / "runtime_experimental/ai_sandbox_work/d84-test/writer_output_candidate.json"
        writer_output.write_text(
            json.dumps(
                {
                    "ok": True,
                    "mode": "SANDBOX_OUTPUT_CANDIDATE_ONLY",
                    "candidate_files": [
                        "runtime_experimental/ai_sandbox_work/d84-test/candidate_proposal.json",
                        "reports/d84-test_candidate_review.json",
                        "tests/test_d84_test_candidate_probe.py",
                    ],
                    "forbidden_actions": [
                        "direct_core_edit",
                        "route_insert",
                        "actual_apply",
                        "external_ai_network_call",
                        "git_commit_or_push_by_ai",
                        "canonical_memory_overwrite",
                    ],
                    "guardrails": {
                        "sandbox_output_only": True,
                        "actual_apply_executed": False,
                        "route_inserted": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "external_ai_called": False,
                        "network_accessed": False,
                        "git_commit_by_ai": False,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d84_sandbox_writer_output_review.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "SANDBOX_WRITER_OUTPUT_REVIEW_READY",
                    "review_id": "d84-test-review",
                    "writer_output_path": str(writer_output),
                    "evidence": {
                        "handoff_id": "d83-test-handoff",
                        "proposal_id": "d80-proposal-test",
                    },
                    "review": {
                        "approved_for_guarded_apply": False,
                        "approved_for_route_insert": False,
                        "approved_for_protected_core": False,
                        "approved_for_next_sandbox_gate": True,
                    },
                    "guardrails": {
                        "external_ai_called": False,
                        "network_accessed": False,
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "actual_apply_executed": False,
                        "route_inserted": False,
                        "git_commit_by_ai": False,
                        "sandbox_output_review_only": True,
                        "writer_output_candidate_only": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        return td, root

    def test_creates_regression_rollback_bundle(self):
        td, root = self.make_root()
        try:
            report = create_regression_rollback_evidence(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "REGRESSION_ROLLBACK_EVIDENCE_READY")
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertTrue(report["rollback_manifest"]["human_review_required"])
            self.assertTrue((root / "reports/d85_regression_rollback_evidence.json").exists())
            self.assertTrue((root / "reports/d85_rollback_manifest.json").exists())
            self.assertTrue((root / "reports/d85_regression_checklist.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d84(self):
        td, root = self.make_root()
        try:
            (root / "reports/d84_sandbox_writer_output_review.json").unlink()
            report = create_regression_rollback_evidence(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "REGRESSION_ROLLBACK_EVIDENCE_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_protected_candidate_path(self):
        td, root = self.make_root()
        try:
            p = root / "runtime_experimental/ai_sandbox_work/d84-test/writer_output_candidate.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["candidate_files"].append("app/orchestration/task_dispatcher.py")
            p.write_text(json.dumps(data), encoding="utf-8")

            report = create_regression_rollback_evidence(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "REGRESSION_ROLLBACK_EVIDENCE_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
