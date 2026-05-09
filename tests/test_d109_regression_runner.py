
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.regression_runner import create_regression_runner


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD109RegressionRunner(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        (root / "runtime_experimental/ai_sandbox_work").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        writer_id = "d108-test"

        d108 = {
            "ok": True,
            "decision": "SANDBOX_PROPOSAL_WRITER_READY",
            "writer_id": writer_id,
            "validator_id": "d107-test",
            "boundary_id": "d106-test",
            "proposal_id": proposal_id,
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
                "sandbox_write_only": True,
                "proposal_json_copy_only": True,
                "candidate_execution_allowed": False,
            },
        }

        manifest = {
            "ok": True,
            "writer_id": writer_id,
            "proposal_id": proposal_id,
            "sandbox_files": [
                "runtime_experimental/ai_sandbox_work/d108_accepted_proposal.json",
                "runtime_experimental/ai_sandbox_work/d108_sandbox_proposal_manifest.json",
                "runtime_experimental/ai_sandbox_work/d108_writer_receipt.json",
            ],
            "actual_apply_executed": False,
            "candidate_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
        }

        receipt = {
            "ok": True,
            "writer_id": writer_id,
            "proposal_id": proposal_id,
            "written_files": manifest["sandbox_files"],
            "external_ai_called": False,
            "network_accessed": False,
            "shell_executed": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "git_commit_by_ai": False,
        }

        scope = {
            "ok": True,
            "allowed_next_gate": "D109_REGRESSION_RUNNER",
            "actual_apply_allowed_after_d108": False,
            "route_insert_allowed_after_d108": False,
            "protected_core_mutation_allowed_after_d108": False,
            "sandbox_candidate_execution_allowed_after_d108": False,
        }

        sandbox_copy = {
            "ok": True,
            "sandbox_copy_only": True,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "proposal": {"proposal_id": proposal_id},
        }

        write(root / "reports/d108_sandbox_proposal_writer.json", d108)
        write(root / "reports/d108_sandbox_proposal_manifest.json", manifest)
        write(root / "reports/d108_writer_receipt.json", receipt)
        write(root / "reports/d108_d109_regression_runner_scope.json", scope)

        for f in manifest["sandbox_files"]:
            write(root / f, {"ok": True, "file": f})
        write(root / "runtime_experimental/ai_sandbox_work/d108_accepted_proposal.json", sandbox_copy)

        return td, root

    def test_creates_regression_reports_without_executing_commands(self):
        td, root = self.root()
        try:
            r = create_regression_runner(root, execute_commands=False)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "REGRESSION_RUNNER_READY")
            self.assertTrue(r["summary"]["static_ok"])
            self.assertEqual(r["d110_scope"]["allowed_next_gate"], "D110_HUMAN_REVIEW_GATE")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertTrue((root / "reports/d109_regression_runner.json").exists())
            self.assertTrue((root / "reports/d109_sandbox_static_checks.json").exists())
            self.assertTrue((root / "reports/d109_sandbox_regression_results.json").exists())
            self.assertTrue((root / "reports/d109_sandbox_diff_summary.json").exists())
            self.assertTrue((root / "reports/d109_d110_human_review_gate_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d108_report(self):
        td, root = self.root()
        try:
            (root / "reports/d108_sandbox_proposal_writer.json").unlink()
            r = create_regression_runner(root, execute_commands=False)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_missing_sandbox_file(self):
        td, root = self.root()
        try:
            (root / "runtime_experimental/ai_sandbox_work/d108_writer_receipt.json").unlink()
            r = create_regression_runner(root, execute_commands=False)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d108_claims_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d108_sandbox_proposal_writer.json"
            data = json.loads(p.read_text())
            data["guardrails"]["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_regression_runner(root, execute_commands=False)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
