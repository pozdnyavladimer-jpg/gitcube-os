
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_guarded_apply_scope import create_sandbox_candidate_reentry_guarded_apply_scope


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


class TestD172SandboxCandidateReentryGuardedApplyScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        apply_intent_id = "d171-test"
        apply_preflight_id = "d170-test"
        verification_id = "d169-test"
        run_id = "d168-test"
        intent_id = "d167-test"
        candidate_id = "d164-test"
        response_id = "d163-test"
        proposal_id = "d107-valid-test"

        d171 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_READY",
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
                "sandbox_candidate_reentry_human_apply_intent_scope_only": True,
                "sandbox_candidate_reentry_human_apply_intent_record_only": True,
                "sandbox_candidate_reentry_apply_authority_guard_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "post_execution_verified": True,
                "apply_preflight_created": True,
                "human_apply_intent_present": True,
                "human_apply_intent_required": True,
                "guarded_apply_allowed_next": True,
                "candidate_apply_allowed_after_d171": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "real_apply_executed": False,
                "actual_apply_executed": False,
                "approval_for_d172_sandbox_candidate_reentry_guarded_apply_scope_only": True,
                "real_apply_allowed_after_d171_by_ai": False,
                "route_insert_allowed_after_d171_by_ai": False,
                "protected_core_mutation_allowed_after_d171_by_ai": False,
                "network_allowed_after_d171_by_ai": False,
                "secret_read_allowed_after_d171_by_ai": False,
                "shell_allowed_after_d171_by_ai": False,
                "git_action_allowed_after_d171_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D171_PLUS",
                "human_apply_intent_status": "HUMAN_APPLY_INTENT_RECORDED_FOR_GUARDED_APPLY_NO_AI_APPLY",
                "apply_authority_guard_status": "APPLY_AUTHORITY_GUARD_CREATED_FOR_D172_NO_APPLY_EXECUTED",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_GUARDED_APPLY_SCOPE",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_ONLY",
                "next_step": "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE",
            },
        }

        human_apply_intent_record = {
            **no_ai_flags(),
            "ok": True,
            "human_apply_intent_status": "HUMAN_APPLY_INTENT_RECORDED_FOR_GUARDED_APPLY_NO_AI_APPLY",
            "human_apply_intent_present": True,
            "human_apply_intent_required": True,
            "apply_preflight_created": True,
            "post_execution_verified": True,
            "guarded_apply_intent_only": True,
            "guarded_apply_allowed_next": True,
            "candidate_apply_allowed_after_d171": False,
            "real_apply_allowed": False,
            "real_apply_executed": False,
            "actual_apply_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        apply_authority_guard = {
            **no_ai_flags(),
            "ok": True,
            "authority_mode": "HUMAN_APPLY_INTENT_RECORDED_GUARDED_APPLY_ONLY_NO_APPLY_EXECUTED",
            "authority_guard_status": "APPLY_AUTHORITY_GUARD_CREATED_FOR_D172_NO_APPLY_EXECUTED",
            "human_apply_intent_present": True,
            "human_apply_intent_required": True,
            "apply_preflight_created": True,
            "post_execution_verified": True,
            "guarded_apply_allowed_next": True,
            "candidate_apply_allowed_after_d171": False,
            "real_apply_allowed": False,
            "real_apply_executed": False,
            "actual_apply_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "network_allowed": False,
            "secret_read_allowed": False,
            "shell_allowed": False,
            "git_action_allowed": False,
            "route_insert_allowed": False,
            "protected_core_mutation_allowed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "no_apply_executed_yet": True,
            "no_real_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
        }

        d172_scope = {
            "ok": True,
            "allowed_next_gate": "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE",
            "sandbox_candidate_reentry_guarded_apply_scope_only": True,
            "human_apply_intent_present": True,
            "apply_preflight_created": True,
            "post_execution_verified": True,
            "guarded_apply_allowed_after_d171_only": True,
            "candidate_apply_allowed_after_d171": False,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d171_by_ai": False,
            "route_insert_allowed_after_d171_by_ai": False,
            "protected_core_mutation_allowed_after_d171_by_ai": False,
            "network_allowed_after_d171_by_ai": False,
            "secret_read_allowed_after_d171_by_ai": False,
            "shell_allowed_after_d171_by_ai": False,
            "git_action_allowed_after_d171_by_ai": False,
        }

        write(root / "reports/d171_sandbox_candidate_reentry_human_apply_intent_scope.json", d171)
        write(root / "reports/d171_sandbox_candidate_reentry_human_apply_intent_record.json", human_apply_intent_record)
        write(root / "reports/d171_sandbox_candidate_reentry_apply_authority_guard.json", apply_authority_guard)
        write(root / "reports/d171_d172_sandbox_candidate_reentry_guarded_apply_scope.json", d172_scope)
        return td, root

    def test_creates_guarded_apply_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_guarded_apply_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_ONLY")
            self.assertEqual(r["d173_scope"]["allowed_next_gate"], "D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE")
            self.assertTrue(r["guardrails"]["guarded_apply_recorded"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["candidate_apply_executed_by_ai"])
            self.assertFalse(r["guardrails"]["route_inserted_by_ai"])
            self.assertTrue((root / "reports/d172_sandbox_candidate_reentry_guarded_apply_scope.json").exists())
            self.assertTrue((root / "reports/d172_sandbox_candidate_reentry_guarded_apply_plan.json").exists())
            self.assertTrue((root / "reports/d172_sandbox_candidate_reentry_guarded_apply_receipt.json").exists())
            self.assertTrue((root / "reports/d172_d173_sandbox_candidate_reentry_post_apply_verification_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d171(self):
        td, root = self.root()
        try:
            (root / "reports/d171_sandbox_candidate_reentry_human_apply_intent_scope.json").unlink()
            r = create_sandbox_candidate_reentry_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_human_apply_intent_missing(self):
        td, root = self.root()
        try:
            p = root / "reports/d171_sandbox_candidate_reentry_human_apply_intent_record.json"
            data = json.loads(p.read_text())
            data["human_apply_intent_present"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_authority_guard_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d171_sandbox_candidate_reentry_apply_authority_guard.json"
            data = json.loads(p.read_text())
            data["route_insert_allowed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d172_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d171_d172_sandbox_candidate_reentry_guarded_apply_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d171_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
