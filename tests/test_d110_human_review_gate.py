
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.human_review_gate import create_human_review_gate


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD110HumanReviewGate(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        (root / "runtime_experimental/ai_sandbox_work").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"

        d109 = {
            "ok": True,
            "decision": "REGRESSION_RUNNER_READY",
            "runner_id": "d109-test",
            "writer_id": "d108-test",
            "proposal_id": proposal_id,
            "guardrails": {
                "external_ai_called": False,
                "network_accessed": False,
                "api_key_read": False,
                "secret_read": False,
                "shell_from_ai_executed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
                "rollback_executed": False,
                "restore_executed": False,
                "sandbox_regression_only": True,
                "candidate_execution_allowed": False,
            },
            "summary": {
                "regression_ok": True,
                "static_ok": True,
                "next_step": "D110_HUMAN_REVIEW_GATE",
            },
        }

        static_checks = {
            "ok": True,
            "existing_files": ["runtime_experimental/ai_sandbox_work/d108_accepted_proposal.json"],
            "missing_files": [],
            "blocked_paths_detected": [],
            "actual_apply_executed": False,
            "candidate_executed": False,
            "protected_core_mutated": False,
            "route_inserted": False,
        }

        regression_results = {
            "ok": True,
            "failed_count": 0,
            "passed_count": 4,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "shell_from_ai_executed": False,
        }

        diff_summary = {
            "ok": True,
            "documentation_only": True,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        d110_scope = {
            "ok": True,
            "allowed_next_gate": "D110_HUMAN_REVIEW_GATE",
            "human_review_required": True,
            "actual_apply_allowed_after_d109": False,
            "route_insert_allowed_after_d109": False,
            "protected_core_mutation_allowed_after_d109": False,
            "sandbox_candidate_execution_allowed_after_d109": False,
        }

        sandbox_proposal = {
            "ok": True,
            "sandbox_copy_only": True,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "proposal": {
                "proposal_id": proposal_id,
                "proposal_type": "analysis_proposal",
                "intent": "review sandbox proposal",
                "target_scope": "runtime_experimental/ai_sandbox_work/",
                "candidate_files": ["runtime_experimental/ai_sandbox_work/proposal_manifest.json"],
                "risk_flags": ["proposal_only"],
                "requires_human_review": True,
            },
        }

        write(root / "reports/d109_regression_runner.json", d109)
        write(root / "reports/d109_sandbox_static_checks.json", static_checks)
        write(root / "reports/d109_sandbox_regression_results.json", regression_results)
        write(root / "reports/d109_sandbox_diff_summary.json", diff_summary)
        write(root / "reports/d109_d110_human_review_gate_scope.json", d110_scope)
        write(root / "runtime_experimental/ai_sandbox_work/d108_accepted_proposal.json", sandbox_proposal)

        return td, root

    def test_creates_human_review_outputs(self):
        td, root = self.root()
        try:
            r = create_human_review_gate(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "HUMAN_REVIEW_GATE_READY")
            self.assertEqual(r["summary"]["approval_state"], "PENDING_HUMAN_DECISION")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["approval_granted"])
            self.assertEqual(r["d111_scope"]["allowed_next_gate"], "D111_EXPLICIT_APPROVAL_GATE")
            self.assertTrue((root / "reports/d110_human_review_gate.json").exists())
            self.assertTrue((root / "reports/d110_human_review_packet.json").exists())
            self.assertTrue((root / "reports/d110_proposal_review_summary.json").exists())
            self.assertTrue((root / "reports/d110_approval_or_rejection_record.json").exists())
            self.assertTrue((root / "reports/d110_d111_explicit_approval_gate_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d109(self):
        td, root = self.root()
        try:
            (root / "reports/d109_regression_runner.json").unlink()
            r = create_human_review_gate(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_regression_failed(self):
        td, root = self.root()
        try:
            p = root / "reports/d109_sandbox_regression_results.json"
            data = json.loads(p.read_text())
            data["ok"] = False
            data["failed_count"] = 1
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_human_review_gate(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d109_claims_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d109_regression_runner.json"
            data = json.loads(p.read_text())
            data["guardrails"]["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_human_review_gate(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_blocked_candidate_path(self):
        td, root = self.root()
        try:
            p = root / "runtime_experimental/ai_sandbox_work/d108_accepted_proposal.json"
            data = json.loads(p.read_text())
            data["proposal"]["candidate_files"] = ["core/unsafe.py"]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_human_review_gate(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
