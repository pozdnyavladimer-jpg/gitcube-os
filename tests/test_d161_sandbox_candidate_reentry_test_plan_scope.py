
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_test_plan_scope import create_sandbox_candidate_reentry_test_plan_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD161SandboxCandidateReentryTestPlanScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        review_id = "d160-test"
        scope_id = "d159-test"
        intake_id = "d158-test"
        reentry_id = "d157-test"
        next_cycle_id = "d156-test"
        proposal_id = "d107-valid-test"

        d160 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE_READY",
            "review_id": review_id,
            "scope_id": scope_id,
            "intake_id": intake_id,
            "reentry_id": reentry_id,
            "next_cycle_id": next_cycle_id,
            "cycle_closure_id": "d155-test",
            "previous_candidate_id": "d126-test",
            "proposal_id": proposal_id,
            "guardrails": {
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
                "sandbox_candidate_reentry_human_review_scope_only": True,
                "sandbox_candidate_reentry_review_packet_only": True,
                "sandbox_candidate_reentry_no_apply_assertions_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "provider_response_required_before_candidate": True,
                "candidate_payload_available": False,
                "candidate_payload_written": False,
                "candidate_files_created": False,
                "candidate_execution_requested": False,
                "candidate_executed": False,
                "apply_requested": False,
                "apply_executed": False,
                "approval_for_d161_sandbox_candidate_reentry_test_plan_scope_only": True,
                "real_apply_allowed_after_d160_by_ai": False,
                "route_insert_allowed_after_d160_by_ai": False,
                "protected_core_mutation_allowed_after_d160_by_ai": False,
                "network_allowed_after_d160_by_ai": False,
                "secret_read_allowed_after_d160_by_ai": False,
                "shell_allowed_after_d160_by_ai": False,
                "git_action_allowed_after_d160_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D160_PLUS",
                "review_status": "HUMAN_REVIEW_PACKET_CREATED_NO_CANDIDATE_PAYLOAD_NO_EXECUTION",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_STILL_NOT_CREATED_NO_PAYLOAD_WRITTEN",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D161_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE_ONLY",
                "next_step": "D161_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE",
            },
        }

        review_packet = {
            "ok": True,
            "review_packet_status": "REVIEW_PACKET_CREATED_NO_CANDIDATE_PAYLOAD_NO_EXECUTION",
            "canonical_guard_schema_applied": True,
            "human_review_required": True,
            "fresh_intent_required": True,
            "provider_response_required_before_candidate": True,
            "candidate_payload_available": False,
            "candidate_payload_written": False,
            "candidate_files_created": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
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

        assertions = {
            "ok": True,
            "canonical_guard_schema_applied": True,
            "no_candidate_payload_write": True,
            "no_candidate_execution": True,
            "no_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
            "human_review_required": True,
            "candidate_payload_written": False,
            "candidate_files_created": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
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

        d161_scope = {
            "ok": True,
            "allowed_next_gate": "D161_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE",
            "sandbox_candidate_reentry_test_plan_scope_only": True,
            "fresh_intent_required": True,
            "provider_response_required_before_candidate": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d160_by_ai": False,
            "route_insert_allowed_after_d160_by_ai": False,
            "protected_core_mutation_allowed_after_d160_by_ai": False,
            "network_allowed_after_d160_by_ai": False,
            "secret_read_allowed_after_d160_by_ai": False,
            "shell_allowed_after_d160_by_ai": False,
            "git_action_allowed_after_d160_by_ai": False,
        }

        write(root / "reports/d160_sandbox_candidate_reentry_human_review_scope.json", d160)
        write(root / "reports/d160_sandbox_candidate_reentry_review_packet.json", review_packet)
        write(root / "reports/d160_sandbox_candidate_reentry_no_apply_assertions.json", assertions)
        write(root / "reports/d160_d161_sandbox_candidate_reentry_test_plan_scope.json", d161_scope)
        return td, root

    def test_creates_sandbox_candidate_reentry_test_plan_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_test_plan_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D162_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE_ONLY")
            self.assertEqual(r["d162_scope"]["allowed_next_gate"], "D162_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE")
            self.assertFalse(r["guardrails"]["candidate_payload_written"])
            self.assertFalse(r["guardrails"]["candidate_executed"])
            self.assertFalse(r["guardrails"]["tests_executed"])
            self.assertTrue((root / "reports/d161_sandbox_candidate_reentry_test_plan_scope.json").exists())
            self.assertTrue((root / "reports/d161_sandbox_candidate_reentry_test_matrix.json").exists())
            self.assertTrue((root / "reports/d161_sandbox_candidate_reentry_no_touch_assertions.json").exists())
            self.assertTrue((root / "reports/d161_d162_sandbox_candidate_reentry_dry_test_runner_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d160(self):
        td, root = self.root()
        try:
            (root / "reports/d160_sandbox_candidate_reentry_human_review_scope.json").unlink()
            r = create_sandbox_candidate_reentry_test_plan_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_review_packet_candidate_payload_written(self):
        td, root = self.root()
        try:
            p = root / "reports/d160_sandbox_candidate_reentry_review_packet.json"
            data = json.loads(p.read_text())
            data["candidate_payload_written"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_test_plan_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_assertions_candidate_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d160_sandbox_candidate_reentry_no_apply_assertions.json"
            data = json.loads(p.read_text())
            data["candidate_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_test_plan_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d161_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d160_d161_sandbox_candidate_reentry_test_plan_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d160_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_test_plan_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
