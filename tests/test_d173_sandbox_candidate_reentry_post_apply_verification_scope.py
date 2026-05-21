
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_post_apply_verification_scope import create_sandbox_candidate_reentry_post_apply_verification_scope


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


class TestD173SandboxCandidateReentryPostApplyVerificationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        guarded_apply_id = "d172-test"
        apply_intent_id = "d171-test"
        apply_preflight_id = "d170-test"
        verification_id = "d169-test"
        run_id = "d168-test"
        intent_id = "d167-test"
        candidate_id = "d164-test"
        response_id = "d163-test"
        proposal_id = "d107-valid-test"

        d172 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_READY",
            "guarded_apply_id": guarded_apply_id,
            "apply_intent_id": apply_intent_id,
            "apply_preflight_id": apply_preflight_id,
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
                "sandbox_candidate_reentry_guarded_apply_scope_only": True,
                "sandbox_candidate_reentry_guarded_apply_plan_only": True,
                "sandbox_candidate_reentry_guarded_apply_receipt_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "human_apply_intent_present": True,
                "post_execution_verified": True,
                "apply_preflight_created": True,
                "guarded_apply_recorded": True,
                "candidate_apply_recorded": True,
                "candidate_apply_executed": False,
                "candidate_apply_executed_by_ai": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "real_apply_executed": False,
                "actual_apply_executed": False,
                "approval_for_d173_sandbox_candidate_reentry_post_apply_verification_scope_only": True,
                "real_apply_allowed_after_d172_by_ai": False,
                "route_insert_allowed_after_d172_by_ai": False,
                "protected_core_mutation_allowed_after_d172_by_ai": False,
                "network_allowed_after_d172_by_ai": False,
                "secret_read_allowed_after_d172_by_ai": False,
                "shell_allowed_after_d172_by_ai": False,
                "git_action_allowed_after_d172_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D172_PLUS",
                "guarded_apply_status": "SANDBOX_GUARDED_APPLY_RECORDED_NO_CORE_MUTATION_NO_REAL_APPLY",
                "guarded_apply_receipt_status": "GUARDED_APPLY_RECORDED_NO_CORE_MUTATION_NO_AI_APPLY",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_RECORDED_READY_FOR_POST_APPLY_VERIFICATION",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_ONLY",
                "next_step": "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE",
            },
        }

        guarded_apply_plan = {
            **no_ai_flags(),
            "ok": True,
            "guarded_apply_plan_status": "GUARDED_APPLY_PLAN_CREATED_NO_CORE_MUTATION",
            "apply_mode": "SANDBOX_GUARDED_NO_OP_APPLY_RECORD_ONLY",
            "human_apply_intent_present": True,
            "apply_preflight_created": True,
            "post_execution_verified": True,
            "guarded_apply_scope_only": True,
            "candidate_apply_recorded": True,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_apply_allowed": False,
            "real_apply_executed": False,
            "actual_apply_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        guarded_apply_receipt = {
            **no_ai_flags(),
            "ok": True,
            "guarded_apply_receipt_status": "GUARDED_APPLY_RECORDED_NO_CORE_MUTATION_NO_AI_APPLY",
            "human_apply_intent_present": True,
            "guarded_apply_recorded": True,
            "guarded_apply_scope_only": True,
            "candidate_apply_recorded": True,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_apply_allowed": False,
            "real_apply_executed": False,
            "actual_apply_executed": False,
            "apply_requested": False,
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

        d173_scope = {
            "ok": True,
            "allowed_next_gate": "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE",
            "sandbox_candidate_reentry_post_apply_verification_scope_only": True,
            "human_apply_intent_present": True,
            "guarded_apply_recorded": True,
            "guarded_apply_scope_only": True,
            "candidate_apply_recorded": True,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d172_by_ai": False,
            "route_insert_allowed_after_d172_by_ai": False,
            "protected_core_mutation_allowed_after_d172_by_ai": False,
            "network_allowed_after_d172_by_ai": False,
            "secret_read_allowed_after_d172_by_ai": False,
            "shell_allowed_after_d172_by_ai": False,
            "git_action_allowed_after_d172_by_ai": False,
        }

        write(root / "reports/d172_sandbox_candidate_reentry_guarded_apply_scope.json", d172)
        write(root / "reports/d172_sandbox_candidate_reentry_guarded_apply_plan.json", guarded_apply_plan)
        write(root / "reports/d172_sandbox_candidate_reentry_guarded_apply_receipt.json", guarded_apply_receipt)
        write(root / "reports/d172_d173_sandbox_candidate_reentry_post_apply_verification_scope.json", d173_scope)
        return td, root

    def test_creates_post_apply_verification_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_post_apply_verification_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_ONLY")
            self.assertEqual(r["d174_scope"]["allowed_next_gate"], "D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE")
            self.assertTrue(r["guardrails"]["post_apply_verified"])
            self.assertTrue(r["guardrails"]["apply_integrity_verified"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["candidate_apply_executed_by_ai"])
            self.assertFalse(r["guardrails"]["route_inserted_by_ai"])
            self.assertTrue((root / "reports/d173_sandbox_candidate_reentry_post_apply_verification_scope.json").exists())
            self.assertTrue((root / "reports/d173_sandbox_candidate_reentry_post_apply_verification_report.json").exists())
            self.assertTrue((root / "reports/d173_sandbox_candidate_reentry_apply_integrity_receipt.json").exists())
            self.assertTrue((root / "reports/d173_d174_sandbox_candidate_reentry_final_apply_audit_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d172(self):
        td, root = self.root()
        try:
            (root / "reports/d172_sandbox_candidate_reentry_guarded_apply_scope.json").unlink()
            r = create_sandbox_candidate_reentry_post_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_guarded_apply_plan_executed_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d172_sandbox_candidate_reentry_guarded_apply_plan.json"
            data = json.loads(p.read_text())
            data["candidate_apply_executed_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_post_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_receipt_real_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d172_sandbox_candidate_reentry_guarded_apply_receipt.json"
            data = json.loads(p.read_text())
            data["real_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_post_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d173_scope_allows_secret_read(self):
        td, root = self.root()
        try:
            p = root / "reports/d172_d173_sandbox_candidate_reentry_post_apply_verification_scope.json"
            data = json.loads(p.read_text())
            data["secret_read_allowed_after_d172_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_post_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
