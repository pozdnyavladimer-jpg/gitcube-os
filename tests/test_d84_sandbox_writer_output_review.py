import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_writer_output_review import create_sandbox_writer_output_review


class TestD84SandboxWriterOutputReview(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)
        (root / "runtime_experimental/ai_sandbox_inbox").mkdir(parents=True)

        handoff_id = "d83-test-handoff"
        writer_input_path = root / "runtime_experimental/ai_sandbox_inbox/d83-test-handoff_sandbox_writer_input.json"

        writer_input_path.write_text(
            json.dumps(
                {
                    "state": "D83_SANDBOX_WRITER_INPUT",
                    "ok": True,
                    "handoff_id": handoff_id,
                    "mode": "SANDBOX_WRITER_INPUT_ONLY",
                    "source": {
                        "intent_id": "d82-test-intent",
                        "proposal_id": "d80-proposal-test",
                        "boundary_id": "d80-test-boundary",
                        "d81_intake_id": "d81-test-intake",
                    },
                    "guardrails": {
                        "proposal_only": True,
                        "sandbox_only": True,
                        "actual_apply_allowed": False,
                        "route_insert_allowed": False,
                        "protected_core_mutation_allowed": False,
                        "external_ai_call_allowed": False,
                        "git_action_allowed": False,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d83_sandbox_writer_handoff.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "SANDBOX_WRITER_HANDOFF_READY",
                    "handoff_id": handoff_id,
                    "writer_input_path": str(writer_input_path),
                    "evidence": {
                        "intent_id": "d82-test-intent",
                        "proposal_id": "d80-proposal-test",
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
                        "sandbox_handoff_only": True,
                        "writer_input_only": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d83_sandbox_writer_handoff_manifest.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "handoff_id": handoff_id,
                    "writer_input_path": str(writer_input_path),
                    "actual_files_created": ["runtime_experimental/ai_sandbox_inbox/d83-test-handoff_sandbox_writer_input.json"],
                    "actual_files_mutated": [],
                    "protected_core_touched": False,
                    "next_gate": "D84_SANDBOX_WRITER_OUTPUT_REVIEW",
                }
            ),
            encoding="utf-8",
        )

        return td, root

    def test_reviews_sandbox_writer_output_only(self):
        td, root = self.make_root()
        try:
            report = create_sandbox_writer_output_review(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "SANDBOX_WRITER_OUTPUT_REVIEW_READY")
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertFalse(report["review"]["approved_for_guarded_apply"])
            self.assertTrue(report["guardrails"]["writer_output_candidate_only"])
            self.assertTrue((root / "reports/d84_sandbox_writer_output_review.json").exists())
            self.assertTrue(Path(report["writer_output_path"]).exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d83(self):
        td, root = self.make_root()
        try:
            (root / "reports/d83_sandbox_writer_handoff.json").unlink()
            report = create_sandbox_writer_output_review(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "SANDBOX_WRITER_OUTPUT_REVIEW_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_protected_candidate_path(self):
        td, root = self.make_root()
        try:
            bad_output = {
                "ok": True,
                "mode": "SANDBOX_OUTPUT_CANDIDATE_ONLY",
                "candidate_files": ["app/orchestration/task_dispatcher.py"],
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
            report = create_sandbox_writer_output_review(root=root, injected_writer_output=bad_output)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "SANDBOX_WRITER_OUTPUT_REVIEW_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
