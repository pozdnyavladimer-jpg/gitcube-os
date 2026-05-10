
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_apply_preflight_scope import create_sandbox_candidate_apply_preflight_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD141SandboxCandidateApplyPreflightScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        verification_id = "d140-test"
        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        false_guard = {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False, "secret_read": False,
            "shell_from_ai_executed": False, "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False, "route_inserted": False,
            "git_commit_by_ai": False, "git_push_by_ai": False, "rollback_executed": False, "restore_executed": False,
        }

        d140 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_READY",
            "verification_id": verification_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_post_execution_verification_scope_only": True,
                "post_execution_verification_report_only": True,
                "execution_integrity_receipt_only": True,
                "candidate_executed_now": False,
                "approval_for_d141_apply_preflight_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "post_execution_validation_status": "SANDBOX_EXECUTION_VERIFIED_NO_APPLY",
                "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
                "execution_result_status": "PRESENT_AND_VALIDATED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_ONLY",
                "next_step": "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE",
            },
        }

        verify_report = {
            "ok": True,
            "verification_id": verification_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "verification_mode": "POST_EXECUTION_VERIFICATION_ONLY_NO_APPLY",
            "sandbox_result_present": True,
            "sandbox_result_ok": True,
            "execution_status_verified": True,
            "candidate_status_verified": True,
            "post_execution_validation_status": "SANDBOX_EXECUTION_VERIFIED_NO_APPLY",
            "result_integrity_status": "PASS",
            "candidate_executed_in_sandbox": True,
            "candidate_executed_by_ai": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "human_review_required": True,
        }

        integrity_receipt = {
            "ok": True,
            "verification_id": verification_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "receipt_mode": "EXECUTION_INTEGRITY_RECEIPT_ONLY_NO_APPLY",
            "sandbox_execution_completed": True,
            "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "candidate_executed_by_ai": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "shell_executed_by_ai": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "human_review_required": True,
        }

        d141_scope = {
            "ok": True,
            "verification_id": verification_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "allowed_next_gate": "D141_SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE",
            "sandbox_candidate_apply_preflight_scope_only": True,
            "human_review_required": True,
            "candidate_executed_in_sandbox_after_d139": True,
            "candidate_executed_after_d140_by_ai": False,
            "real_apply_allowed_after_d140_by_ai": False,
            "route_insert_allowed_after_d140_by_ai": False,
            "protected_core_mutation_allowed_after_d140_by_ai": False,
            "network_allowed_after_d140_by_ai": False,
            "secret_read_allowed_after_d140_by_ai": False,
            "shell_allowed_after_d140_by_ai": False,
            "git_action_allowed_after_d140_by_ai": False,
        }

        write(root / "reports/d140_sandbox_candidate_post_execution_verification_scope.json", d140)
        write(root / "reports/d140_sandbox_candidate_post_execution_verification_report.json", verify_report)
        write(root / "reports/d140_sandbox_candidate_execution_integrity_receipt.json", integrity_receipt)
        write(root / "reports/d140_d141_sandbox_candidate_apply_preflight_scope.json", d141_scope)
        return td, root

    def test_creates_apply_preflight_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_apply_preflight_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_READY")
            self.assertEqual(r["summary"]["apply_preflight_status"], "APPLY_PREFLIGHT_CREATED_NO_APPLY")
            self.assertEqual(r["summary"]["approval_scope"], "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertEqual(r["d142_scope"]["allowed_next_gate"], "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE")
            self.assertTrue((root / "reports/d141_sandbox_candidate_apply_preflight_scope.json").exists())
            self.assertTrue((root / "reports/d141_sandbox_candidate_apply_preflight_report.json").exists())
            self.assertTrue((root / "reports/d141_sandbox_candidate_apply_blockers.json").exists())
            self.assertTrue((root / "reports/d141_d142_sandbox_candidate_human_apply_intent_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d140(self):
        td, root = self.root()
        try:
            (root / "reports/d140_sandbox_candidate_post_execution_verification_scope.json").unlink()
            r = create_sandbox_candidate_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_verification_report_says_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d140_sandbox_candidate_post_execution_verification_report.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d141_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d140_d141_sandbox_candidate_apply_preflight_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d140_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d140_summary_not_validated(self):
        td, root = self.root()
        try:
            p = root / "reports/d140_sandbox_candidate_post_execution_verification_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["execution_result_status"] = "BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
