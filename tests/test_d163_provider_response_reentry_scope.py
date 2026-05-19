
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.provider_response_reentry_scope import create_provider_response_reentry_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD163ProviderResponseReentryScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        runner_id = "d162-test"
        plan_id = "d161-test"
        review_id = "d160-test"
        scope_id = "d159-test"
        intake_id = "d158-test"
        reentry_id = "d157-test"
        next_cycle_id = "d156-test"
        proposal_id = "d107-valid-test"

        d162 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE_READY",
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
                "sandbox_candidate_reentry_dry_test_runner_scope_only": True,
                "sandbox_candidate_reentry_dry_test_report_only": True,
                "sandbox_candidate_reentry_test_safety_receipt_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "provider_response_required_before_candidate": True,
                "dry_tests_evaluated": True,
                "tests_executed": False,
                "candidate_payload_available": False,
                "candidate_payload_written": False,
                "candidate_files_created": False,
                "candidate_execution_requested": False,
                "candidate_executed": False,
                "provider_response_ingested": False,
                "apply_requested": False,
                "apply_executed": False,
                "approval_for_d163_provider_response_reentry_scope_only": True,
                "real_apply_allowed_after_d162_by_ai": False,
                "route_insert_allowed_after_d162_by_ai": False,
                "protected_core_mutation_allowed_after_d162_by_ai": False,
                "network_allowed_after_d162_by_ai": False,
                "secret_read_allowed_after_d162_by_ai": False,
                "shell_allowed_after_d162_by_ai": False,
                "git_action_allowed_after_d162_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D162_PLUS",
                "dry_test_status": "DRY_TEST_METADATA_EVALUATED_NO_CANDIDATE_EXECUTION",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_STILL_NOT_CREATED_NO_PAYLOAD_WRITTEN",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "test_execution_status": "DRY_METADATA_ONLY_NOT_EXECUTED",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D163_PROVIDER_RESPONSE_REENTRY_SCOPE_ONLY",
                "next_step": "D163_PROVIDER_RESPONSE_REENTRY_SCOPE",
            },
        }

        dry_report = {
            "ok": True,
            "dry_test_report_status": "DRY_TEST_METADATA_EVALUATED_NO_CANDIDATE_EXECUTION",
            "canonical_guard_schema_applied": True,
            "dry_runner_scope_only": True,
            "dry_tests_evaluated": True,
            "tests_executed": False,
            "candidate_payload_available": False,
            "candidate_payload_written": False,
            "candidate_files_created": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "provider_response_required_before_candidate": True,
            "provider_response_ingested": False,
            "evaluated_count": 5,
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

        safety_receipt = {
            "ok": True,
            "safety_receipt_status": "DRY_TEST_RUNNER_RECORDED_NO_TOUCH_NO_CANDIDATE_EXECUTION",
            "canonical_guard_schema_applied": True,
            "dry_tests_evaluated": True,
            "tests_executed": False,
            "candidate_payload_written": False,
            "candidate_files_created": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "no_candidate_payload_write": True,
            "no_candidate_execution": True,
            "no_real_test_execution": True,
            "no_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
            "human_review_required": True,
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

        d163_scope = {
            "ok": True,
            "allowed_next_gate": "D163_PROVIDER_RESPONSE_REENTRY_SCOPE",
            "provider_response_reentry_scope_only": True,
            "fresh_intent_required": True,
            "provider_response_required_before_candidate": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d162_by_ai": False,
            "route_insert_allowed_after_d162_by_ai": False,
            "protected_core_mutation_allowed_after_d162_by_ai": False,
            "network_allowed_after_d162_by_ai": False,
            "secret_read_allowed_after_d162_by_ai": False,
            "shell_allowed_after_d162_by_ai": False,
            "git_action_allowed_after_d162_by_ai": False,
        }

        write(root / "reports/d162_sandbox_candidate_reentry_dry_test_runner_scope.json", d162)
        write(root / "reports/d162_sandbox_candidate_reentry_dry_test_report.json", dry_report)
        write(root / "reports/d162_sandbox_candidate_reentry_test_safety_receipt.json", safety_receipt)
        write(root / "reports/d162_d163_provider_response_reentry_scope.json", d163_scope)
        return td, root

    def test_creates_provider_response_reentry_outputs(self):
        td, root = self.root()
        try:
            r = create_provider_response_reentry_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "PROVIDER_RESPONSE_REENTRY_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_ONLY")
            self.assertEqual(r["d164_scope"]["allowed_next_gate"], "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE")
            self.assertFalse(r["guardrails"]["real_provider_call_performed"])
            self.assertFalse(r["guardrails"]["provider_response_ingested"])
            self.assertTrue(r["guardrails"]["dry_capture_only"])
            self.assertTrue((root / "reports/d163_provider_response_reentry_scope.json").exists())
            self.assertTrue((root / "reports/d163_provider_response_reentry_manifest.json").exists())
            self.assertTrue((root / "reports/d163_provider_response_reentry_dry_capture_receipt.json").exists())
            self.assertTrue((root / "reports/d163_d164_sandbox_candidate_reentry_materialization_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d162(self):
        td, root = self.root()
        try:
            (root / "reports/d162_sandbox_candidate_reentry_dry_test_runner_scope.json").unlink()
            r = create_provider_response_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_dry_report_provider_ingested(self):
        td, root = self.root()
        try:
            p = root / "reports/d162_sandbox_candidate_reentry_dry_test_report.json"
            data = json.loads(p.read_text())
            data["provider_response_ingested"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_response_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_safety_receipt_provider_called(self):
        td, root = self.root()
        try:
            p = root / "reports/d162_sandbox_candidate_reentry_test_safety_receipt.json"
            data = json.loads(p.read_text())
            data["real_provider_call_performed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_response_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d163_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d162_d163_provider_response_reentry_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d162_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_response_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
