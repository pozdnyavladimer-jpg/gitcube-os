
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_post_execution_verification_scope import create_sandbox_candidate_reentry_post_execution_verification_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


def no_ai_flags():
    return {
        "network_accessed": False,
        "secret_read": False,
        "shell_executed_by_ai": False,
        "actual_apply_executed_by_ai": False,
        "real_apply_executed_by_ai": False,
        "route_inserted": False,
        "route_inserted_by_ai": False,
        "protected_core_mutated": False,
        "protected_core_mutated_by_ai": False,
        "git_action_by_ai": False,
    }


class TestD169SandboxCandidateReentryPostExecutionVerificationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        run_id = "d168-test"
        intent_id = "d167-test"
        preflight_id = "d166-test"
        validation_id = "d165-test"
        candidate_id = "d164-test"
        response_id = "d163-test"
        runner_id = "d162-test"
        plan_id = "d161-test"
        review_id = "d160-test"
        scope_id = "d159-test"
        intake_id = "d158-test"
        reentry_id = "d157-test"
        next_cycle_id = "d156-test"
        proposal_id = "d107-valid-test"

        d168 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_READY",
            "run_id": run_id,
            "intent_id": intent_id,
            "preflight_id": preflight_id,
            "validation_id": validation_id,
            "candidate_id": candidate_id,
            "response_id": response_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "scope_id": scope_id,
            "intake_id": intake_id,
            "reentry_id": reentry_id,
            "next_cycle_id": next_cycle_id,
            "cycle_closure_id": "d155-test",
            "previous_candidate_id": "d126-test",
            "proposal_id": proposal_id,
            "guardrails": {
                **no_ai_flags(),
                "sandbox_candidate_reentry_controlled_execution_run_scope_only": True,
                "sandbox_candidate_reentry_execution_run_result_only": True,
                "sandbox_candidate_reentry_execution_safety_receipt_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "human_execution_intent_present": True,
                "candidate_executed_in_sandbox": True,
                "candidate_executed_by_ai": False,
                "candidate_execution_was_no_op_only": True,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "real_apply_executed": False,
                "actual_apply_executed": False,
                "approval_for_d169_sandbox_candidate_reentry_post_execution_verification_scope_only": True,
                "real_apply_allowed_after_d168_by_ai": False,
                "route_insert_allowed_after_d168_by_ai": False,
                "protected_core_mutation_allowed_after_d168_by_ai": False,
                "network_allowed_after_d168_by_ai": False,
                "secret_read_allowed_after_d168_by_ai": False,
                "shell_allowed_after_d168_by_ai": False,
                "git_action_allowed_after_d168_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D168_PLUS",
                "sandbox_execution_status": "SANDBOX_CANDIDATE_REENTRY_EXECUTED_NO_OP_NO_APPLY",
                "safety_receipt_status": "SANDBOX_EXECUTION_RECORDED_NO_CORE_MUTATION_NO_APPLY",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_EXECUTED_READY_FOR_POST_EXECUTION_VERIFICATION",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_ONLY",
                "next_step": "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE",
            },
        }

        run_result = {
            **no_ai_flags(),
            "ok": True,
            "sandbox_execution_status": "SANDBOX_CANDIDATE_REENTRY_EXECUTED_NO_OP_NO_APPLY",
            "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
            "candidate_executed_in_sandbox": True,
            "candidate_executed": True,
            "candidate_execution_was_no_op_only": True,
            "candidate_executed_by_ai": False,
            "operations_executed": [{"op": "NO_OP", "status": "NO_OP_CONFIRMED_IN_SANDBOX"}],
            "real_apply_executed": False,
            "actual_apply_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        safety_receipt = {
            **no_ai_flags(),
            "ok": True,
            "safety_receipt_status": "SANDBOX_EXECUTION_RECORDED_NO_CORE_MUTATION_NO_APPLY",
            "candidate_executed_in_sandbox": True,
            "candidate_executed_by_ai": False,
            "candidate_execution_was_no_op_only": True,
            "real_apply_executed": False,
            "actual_apply_executed": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "no_real_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
        }

        d169_scope = {
            "ok": True,
            "allowed_next_gate": "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE",
            "sandbox_candidate_reentry_post_execution_verification_scope_only": True,
            "candidate_executed_in_sandbox": True,
            "candidate_execution_verified_required": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d168_by_ai": False,
            "route_insert_allowed_after_d168_by_ai": False,
            "protected_core_mutation_allowed_after_d168_by_ai": False,
            "network_allowed_after_d168_by_ai": False,
            "secret_read_allowed_after_d168_by_ai": False,
            "shell_allowed_after_d168_by_ai": False,
            "git_action_allowed_after_d168_by_ai": False,
        }

        write(root / "reports/d168_sandbox_candidate_reentry_controlled_execution_run_scope.json", d168)
        write(root / "reports/d168_sandbox_candidate_reentry_execution_run_result.json", run_result)
        write(root / "reports/d168_sandbox_candidate_reentry_execution_safety_receipt.json", safety_receipt)
        write(root / "reports/d168_d169_sandbox_candidate_reentry_post_execution_verification_scope.json", d169_scope)
        return td, root

    def test_creates_post_execution_verification_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_post_execution_verification_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE_ONLY")
            self.assertEqual(r["d170_scope"]["allowed_next_gate"], "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE")
            self.assertTrue(r["guardrails"]["post_execution_verified"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted_by_ai"])
            self.assertTrue((root / "reports/d169_sandbox_candidate_reentry_post_execution_verification_scope.json").exists())
            self.assertTrue((root / "reports/d169_sandbox_candidate_reentry_post_execution_verification_report.json").exists())
            self.assertTrue((root / "reports/d169_sandbox_candidate_reentry_execution_integrity_receipt.json").exists())
            self.assertTrue((root / "reports/d169_d170_sandbox_candidate_reentry_apply_preflight_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d168(self):
        td, root = self.root()
        try:
            (root / "reports/d168_sandbox_candidate_reentry_controlled_execution_run_scope.json").unlink()
            r = create_sandbox_candidate_reentry_post_execution_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_run_result_real_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d168_sandbox_candidate_reentry_execution_run_result.json"
            data = json.loads(p.read_text())
            data["real_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_post_execution_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_safety_receipt_shell_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d168_sandbox_candidate_reentry_execution_safety_receipt.json"
            data = json.loads(p.read_text())
            data["shell_executed_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_post_execution_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d169_scope_allows_git_action(self):
        td, root = self.root()
        try:
            p = root / "reports/d168_d169_sandbox_candidate_reentry_post_execution_verification_scope.json"
            data = json.loads(p.read_text())
            data["git_action_allowed_after_d168_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_post_execution_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
