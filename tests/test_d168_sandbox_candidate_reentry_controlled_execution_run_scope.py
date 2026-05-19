
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_controlled_execution_run_scope import create_sandbox_candidate_reentry_controlled_execution_run_scope


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


class TestD168SandboxCandidateReentryControlledExecutionRunScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

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

        work_dir = root / "runtime_experimental" / "ai_sandbox_work" / candidate_id
        work_dir.mkdir(parents=True, exist_ok=True)
        candidate_payload = {
            **no_ai_flags(),
            "ok": True,
            "candidate_id": candidate_id,
            "payload_kind": "NO_OP_REENTRY_PLACEHOLDER_FOR_STATIC_VALIDATION",
            "payload_status": "MATERIALIZED_IN_SANDBOX_ONLY_NO_EXECUTION",
            "operations": [
                {
                    "op": "NO_OP",
                    "writes_core": False,
                    "executes_code": False,
                    "requires_network": False,
                    "requires_secrets": False,
                    "requires_shell": False,
                }
            ],
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }
        write(work_dir / "candidate_payload.json", candidate_payload)

        d167 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_READY",
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
                "sandbox_candidate_reentry_human_execution_intent_scope_only": True,
                "sandbox_candidate_reentry_human_execution_intent_record_only": True,
                "sandbox_candidate_reentry_execution_authority_guard_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "human_execution_intent_present": True,
                "sandbox_execution_intent_only": True,
                "candidate_execution_allowed_next": True,
                "candidate_execution_allowed_after_d167": False,
                "candidate_execution_requested": False,
                "candidate_executed": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "approval_for_d168_sandbox_candidate_reentry_controlled_execution_run_scope_only": True,
                "real_apply_allowed_after_d167_by_ai": False,
                "route_insert_allowed_after_d167_by_ai": False,
                "protected_core_mutation_allowed_after_d167_by_ai": False,
                "network_allowed_after_d167_by_ai": False,
                "secret_read_allowed_after_d167_by_ai": False,
                "shell_allowed_after_d167_by_ai": False,
                "git_action_allowed_after_d167_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D167_PLUS",
                "human_execution_intent_status": "HUMAN_EXECUTION_INTENT_RECORDED_FOR_SANDBOX_ONLY_NO_REAL_APPLY",
                "authority_guard_status": "HUMAN_INTENT_RECORDED_RUN_AUTHORITY_NOT_EXECUTED",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_CONTROLLED_EXECUTION_RUN_SCOPE",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_ONLY",
                "next_step": "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE",
            },
        }

        intent_record = {
            **no_ai_flags(),
            "ok": True,
            "human_execution_intent_status": "HUMAN_EXECUTION_INTENT_RECORDED_FOR_SANDBOX_ONLY_NO_REAL_APPLY",
            "human_execution_intent_present": True,
            "human_execution_intent_required": True,
            "sandbox_execution_intent_only": True,
            "candidate_execution_allowed_next": True,
            "candidate_execution_allowed_after_d167": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_apply_allowed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        authority_guard = {
            **no_ai_flags(),
            "ok": True,
            "authority_mode": "HUMAN_INTENT_RECORDED_SANDBOX_EXECUTION_ONLY_NO_APPLY",
            "authority_guard_status": "HUMAN_INTENT_RECORDED_RUN_AUTHORITY_NOT_EXECUTED",
            "human_execution_intent_present": True,
            "sandbox_execution_only": True,
            "candidate_execution_allowed_next": True,
            "candidate_execution_allowed_after_d167": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "real_apply_allowed": False,
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
            "no_candidate_execution_yet": True,
            "no_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
        }

        d168_scope = {
            "ok": True,
            "allowed_next_gate": "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE",
            "sandbox_candidate_reentry_controlled_execution_run_scope_only": True,
            "human_execution_intent_present": True,
            "sandbox_execution_only": True,
            "candidate_execution_allowed_after_d167_only_in_sandbox": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d167_by_ai": False,
            "route_insert_allowed_after_d167_by_ai": False,
            "protected_core_mutation_allowed_after_d167_by_ai": False,
            "network_allowed_after_d167_by_ai": False,
            "secret_read_allowed_after_d167_by_ai": False,
            "shell_allowed_after_d167_by_ai": False,
            "git_action_allowed_after_d167_by_ai": False,
        }

        write(root / "reports/d167_sandbox_candidate_reentry_human_execution_intent_scope.json", d167)
        write(root / "reports/d167_sandbox_candidate_reentry_human_execution_intent_record.json", intent_record)
        write(root / "reports/d167_sandbox_candidate_reentry_execution_authority_guard.json", authority_guard)
        write(root / "reports/d167_d168_sandbox_candidate_reentry_controlled_execution_run_scope.json", d168_scope)
        return td, root

    def test_creates_controlled_execution_run_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_controlled_execution_run_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE_ONLY")
            self.assertEqual(r["d169_scope"]["allowed_next_gate"], "D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE")
            self.assertTrue(r["guardrails"]["candidate_executed_in_sandbox"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted_by_ai"])
            self.assertTrue((root / "reports/d168_sandbox_candidate_reentry_controlled_execution_run_scope.json").exists())
            self.assertTrue((root / "reports/d168_sandbox_candidate_reentry_execution_run_result.json").exists())
            self.assertTrue((root / "reports/d168_sandbox_candidate_reentry_execution_safety_receipt.json").exists())
            self.assertTrue((root / "reports/d168_d169_sandbox_candidate_reentry_post_execution_verification_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d167(self):
        td, root = self.root()
        try:
            (root / "reports/d167_sandbox_candidate_reentry_human_execution_intent_scope.json").unlink()
            r = create_sandbox_candidate_reentry_controlled_execution_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_candidate_payload_requires_network(self):
        td, root = self.root()
        try:
            p = root / "runtime_experimental" / "ai_sandbox_work" / "d164-test" / "candidate_payload.json"
            data = json.loads(p.read_text())
            data["operations"][0]["requires_network"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_execution_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d168_scope_allows_shell(self):
        td, root = self.root()
        try:
            p = root / "reports/d167_d168_sandbox_candidate_reentry_controlled_execution_run_scope.json"
            data = json.loads(p.read_text())
            data["shell_allowed_after_d167_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_execution_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_authority_guard_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d167_sandbox_candidate_reentry_execution_authority_guard.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_execution_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
