
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_proposal_writer import create_sandbox_proposal_writer


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD108SandboxProposalWriter(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal = {
            "proposal_id": "d107-valid-test",
            "proposal_type": "analysis_proposal",
            "intent": "validate_ai_proposal_json_before_sandbox_writer",
            "target_scope": "runtime_experimental/ai_sandbox_work/",
            "candidate_files": ["runtime_experimental/ai_sandbox_work/proposal_manifest.json"],
            "risk_flags": ["proposal_only", "requires_human_review"],
            "guardrails": {
                "external_ai_called": False,
                "network_accessed": False,
                "shell_executed": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "git_commit_by_ai": False,
            },
            "validation_plan": ["Validate fields", "Reject blocked paths", "Require human review"],
            "requires_human_review": True,
        }

        write(root / "reports/d107_proposal_schema_validator.json", {
            "ok": True,
            "decision": "PROPOSAL_SCHEMA_VALIDATOR_READY",
            "validator_id": "d107-test",
            "boundary_id": "d106-test",
            "guardrails": {
                "external_ai_called": False,
                "network_accessed": False,
                "api_key_read": False,
                "secret_read": False,
                "shell_executed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
                "rollback_executed": False,
                "restore_executed": False,
                "schema_validation_only": True,
                "sandbox_writer_not_called": True,
                "proposal_only": True,
            },
        })
        write(root / "reports/d107_mock_valid_proposal.json", proposal)
        write(root / "reports/d107_acceptance_manifest.json", {
            "ok": True,
            "accepted_proposal_id": "d107-valid-test",
            "accepted_for": "D108_SANDBOX_PROPOSAL_WRITER_ONLY",
            "sandbox_write_executed": False,
            "actual_apply_executed": False,
            "protected_core_mutated": False,
            "route_inserted": False,
            "requires_human_review": True,
        })
        write(root / "reports/d107_d108_sandbox_proposal_writer_scope.json", {
            "ok": True,
            "allowed_next_gate": "D108_SANDBOX_PROPOSAL_WRITER",
            "sandbox_write_allowed_after_d107": True,
            "actual_apply_allowed_after_d107": False,
            "route_insert_allowed_after_d107": False,
            "protected_core_mutation_allowed_after_d107": False,
        })
        return td, root

    def test_creates_sandbox_writer_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_proposal_writer(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_PROPOSAL_WRITER_READY")
            self.assertTrue(r["guardrails"]["sandbox_write_only"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d109_scope"]["allowed_next_gate"], "D109_REGRESSION_RUNNER")
            self.assertTrue((root / "runtime_experimental/ai_sandbox_work/d108_accepted_proposal.json").exists())
            self.assertTrue((root / "runtime_experimental/ai_sandbox_work/d108_sandbox_proposal_manifest.json").exists())
            self.assertTrue((root / "runtime_experimental/ai_sandbox_work/d108_writer_receipt.json").exists())
            self.assertTrue((root / "reports/d108_sandbox_proposal_writer.json").exists())
            self.assertTrue((root / "reports/d108_sandbox_proposal_manifest.json").exists())
            self.assertTrue((root / "reports/d108_writer_receipt.json").exists())
            self.assertTrue((root / "reports/d108_d109_regression_runner_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d107(self):
        td, root = self.root()
        try:
            (root / "reports/d107_proposal_schema_validator.json").unlink()
            r = create_sandbox_proposal_writer(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_proposal_to_core(self):
        td, root = self.root()
        try:
            p = root / "reports/d107_mock_valid_proposal.json"
            data = json.loads(p.read_text())
            data["target_scope"] = "core/"
            data["candidate_files"] = ["core/unsafe.py"]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_proposal_writer(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_acceptance_already_wrote_sandbox(self):
        td, root = self.root()
        try:
            p = root / "reports/d107_acceptance_manifest.json"
            data = json.loads(p.read_text())
            data["sandbox_write_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_proposal_writer(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
