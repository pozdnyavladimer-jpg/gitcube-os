
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_post_execution_verification_scope import create_sandbox_candidate_post_execution_verification_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD140SandboxCandidatePostExecutionVerificationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"
        sandbox_rel = f"runtime_experimental/ai_sandbox_work/{candidate_id}/sandbox_execution_result.json"

        d139 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_READY",
            "run_id": run_id,
            "candidate_id": candidate_id,
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
                "git_push_by_ai": False,
                "rollback_executed": False,
                "restore_executed": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "run_id": run_id,
                "candidate_id": candidate_id,
                "proposal_id": proposal_id,
                "execution_status": "SANDBOX_CONTROLLED_EXECUTION_COMPLETED",
                "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
                "sandbox_result_path": sandbox_rel,
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_ONLY",
                "next_step": "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE",
            },
        }

        run_result = {
            "ok": True,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "sandbox_result_path": sandbox_rel,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        safety_receipt = {
            "ok": True,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
        }

        d140_scope = {
            "ok": True,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE",
            "sandbox_candidate_post_execution_verification_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d139_by_ai": False,
            "route_insert_allowed_after_d139_by_ai": False,
            "protected_core_mutation_allowed_after_d139_by_ai": False,
            "network_allowed_after_d139_by_ai": False,
            "secret_read_allowed_after_d139_by_ai": False,
            "shell_allowed_after_d139_by_ai": False,
            "git_action_allowed_after_d139_by_ai": False,
        }

        sandbox_result = {
            "ok": True,
            "state": "D139_SANDBOX_CANDIDATE_EXECUTION_RESULT",
            "run_id": run_id,
            "candidate_id": candidate_id,
            "execution_status": "SANDBOX_CONTROLLED_EXECUTION_COMPLETED",
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
        }

        write(root / "reports/d139_sandbox_candidate_controlled_execution_run_scope.json", d139)
        write(root / "reports/d139_sandbox_candidate_execution_run_result.json", run_result)
        write(root / "reports/d139_sandbox_candidate_execution_safety_receipt.json", safety_receipt)
        write(root / "reports/d139_d140_sandbox_candidate_post_execution_verification_scope.json", d140_scope)
        write(root / sandbox_rel, sandbox_result)
        return td, root

    def test_creates_post_execution_verification_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_post_execution_verification_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_READY")
            self.assertEqual(r["summary"]["post_execution_validation_status"], "SANDBOX_EXECUTION_VERIFIED_NO_APPLY")
            self.assertEqual(r["summary"]["approval_scope"], "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted"])
            self.assertEqual(r["d141_scope"]["allowed_next_gate"], "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE")
            self.assertTrue((root / "reports/d140_sandbox_candidate_post_execution_verification_scope.json").exists())
            self.assertTrue((root / "reports/d140_sandbox_candidate_post_execution_verification_report.json").exists())
            self.assertTrue((root / "reports/d140_sandbox_candidate_execution_integrity_receipt.json").exists())
            self.assertTrue((root / "reports/d140_d141_sandbox_candidate_apply_preflight_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d139(self):
        td, root = self.root()
        try:
            (root / "reports/d139_sandbox_candidate_controlled_execution_run_scope.json").unlink()
            r = create_sandbox_candidate_post_execution_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d139_not_ready(self):
        td, root = self.root()
        try:
            p = root / "reports/d139_sandbox_candidate_controlled_execution_run_scope.json"
            data = json.loads(p.read_text())
            data["ok"] = False
            data["decision"] = "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_execution_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d139_sandbox_candidate_execution_safety_receipt.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_execution_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_missing_sandbox_result(self):
        td, root = self.root()
        try:
            p = root / "runtime_experimental/ai_sandbox_work/d126-test/sandbox_execution_result.json"
            p.unlink()
            r = create_sandbox_candidate_post_execution_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
