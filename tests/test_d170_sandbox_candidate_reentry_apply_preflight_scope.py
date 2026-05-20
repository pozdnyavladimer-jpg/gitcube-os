
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_apply_preflight_scope import create_sandbox_candidate_reentry_apply_preflight_scope


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


class TestD170SandboxCandidateReentryApplyPreflightScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        verification_id = "d169-test"
        run_id = "d168-test"
        intent_id = "d167-test"
        candidate_id = "d164-test"
        response_id = "d163-test"
        proposal_id = "d107-valid-test"

        d169 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_READY",
            "verification_id": verification_id,
            "run_id": run_id,
            "intent_id": intent_id,
            "preflight_id": "d166-test",
            "validation_id": "d165-test",
            "candidate_id": candidate_id,
            "response_id": response_id,
            "runner_id": "d162-test",
            "plan_id": "d161-test",
            "review_id": "d160-test",
            "scope_id": "d159-test",
            "intake_id": "d158-test",
            "reentry_id": "d157-test",
            "next_cycle_id": "d156-test",
            "cycle_closure_id": "d155-test",
            "previous_candidate_id": "d126-test",
            "proposal_id": proposal_id,
            "guardrails": {
                **no_ai_flags(),
                "sandbox_candidate_reentry_post_execution_verification_scope_only": True,
                "sandbox_candidate_reentry_post_execution_verification_report_only": True,
                "sandbox_candidate_reentry_execution_integrity_receipt_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "post_execution_verified": True,
                "candidate_executed_in_sandbox": True,
                "candidate_execution_was_no_op_only": True,
                "candidate_executed_by_ai": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "real_apply_executed": False,
                "actual_apply_executed": False,
                "approval_for_d170_sandbox_candidate_reentry_apply_preflight_scope_only": True,
                "real_apply_allowed_after_d169_by_ai": False,
                "route_insert_allowed_after_d169_by_ai": False,
                "protected_core_mutation_allowed_after_d169_by_ai": False,
                "network_allowed_after_d169_by_ai": False,
                "secret_read_allowed_after_d169_by_ai": False,
                "shell_allowed_after_d169_by_ai": False,
                "git_action_allowed_after_d169_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D169_PLUS",
                "post_execution_verification_status": "SANDBOX_EXECUTION_VERIFIED_NO_CORE_MUTATION_NO_APPLY",
                "integrity_receipt_status": "POST_EXECUTION_INTEGRITY_VERIFIED_NO_APPLY_NO_CORE_MUTATION",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFIED_READY_FOR_APPLY_PREFLIGHT",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE_ONLY",
                "next_step": "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE",
            },
        }

        verification_report = {
            **no_ai_flags(),
            "ok": True,
            "post_execution_verification_status": "SANDBOX_EXECUTION_VERIFIED_NO_CORE_MUTATION_NO_APPLY",
            "candidate_executed_in_sandbox": True,
            "candidate_execution_was_no_op_only": True,
            "candidate_executed_by_ai": False,
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

        integrity_receipt = {
            **no_ai_flags(),
            "ok": True,
            "integrity_receipt_status": "POST_EXECUTION_INTEGRITY_VERIFIED_NO_APPLY_NO_CORE_MUTATION",
            "candidate_executed_in_sandbox": True,
            "candidate_execution_was_no_op_only": True,
            "candidate_executed_by_ai": False,
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

        d170_scope = {
            "ok": True,
            "allowed_next_gate": "D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE",
            "sandbox_candidate_reentry_apply_preflight_scope_only": True,
            "post_execution_verified": True,
            "candidate_executed_in_sandbox": True,
            "candidate_execution_was_no_op_only": True,
            "candidate_apply_allowed_after_d169": False,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d169_by_ai": False,
            "route_insert_allowed_after_d169_by_ai": False,
            "protected_core_mutation_allowed_after_d169_by_ai": False,
            "network_allowed_after_d169_by_ai": False,
            "secret_read_allowed_after_d169_by_ai": False,
            "shell_allowed_after_d169_by_ai": False,
            "git_action_allowed_after_d169_by_ai": False,
        }

        write(root / "reports/d169_sandbox_candidate_reentry_post_execution_verification_scope.json", d169)
        write(root / "reports/d169_sandbox_candidate_reentry_post_execution_verification_report.json", verification_report)
        write(root / "reports/d169_sandbox_candidate_reentry_execution_integrity_receipt.json", integrity_receipt)
        write(root / "reports/d169_d170_sandbox_candidate_reentry_apply_preflight_scope.json", d170_scope)
        return td, root

    def test_creates_apply_preflight_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_apply_preflight_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_ONLY")
            self.assertEqual(r["d171_scope"]["allowed_next_gate"], "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE")
            self.assertTrue(r["guardrails"]["apply_preflight_created"])
            self.assertTrue(r["guardrails"]["human_apply_intent_required"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted_by_ai"])
            self.assertTrue((root / "reports/d170_sandbox_candidate_reentry_apply_preflight_scope.json").exists())
            self.assertTrue((root / "reports/d170_sandbox_candidate_reentry_apply_preflight_report.json").exists())
            self.assertTrue((root / "reports/d170_sandbox_candidate_reentry_apply_blockers.json").exists())
            self.assertTrue((root / "reports/d170_d171_sandbox_candidate_reentry_human_apply_intent_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d169(self):
        td, root = self.root()
        try:
            (root / "reports/d169_sandbox_candidate_reentry_post_execution_verification_scope.json").unlink()
            r = create_sandbox_candidate_reentry_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_verification_real_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d169_sandbox_candidate_reentry_post_execution_verification_report.json"
            data = json.loads(p.read_text())
            data["real_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_integrity_receipt_shell_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d169_sandbox_candidate_reentry_execution_integrity_receipt.json"
            data = json.loads(p.read_text())
            data["shell_executed_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d170_scope_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d169_d170_sandbox_candidate_reentry_apply_preflight_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d169_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
