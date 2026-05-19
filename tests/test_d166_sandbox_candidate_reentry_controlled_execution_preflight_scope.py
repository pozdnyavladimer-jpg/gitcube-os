
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_controlled_execution_preflight_scope import create_sandbox_candidate_reentry_controlled_execution_preflight_scope


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


class TestD166SandboxCandidateReentryControlledExecutionPreflightScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

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

        d165 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_READY",
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
                "sandbox_candidate_reentry_static_validation_scope_only": True,
                "sandbox_candidate_reentry_static_validation_report_only": True,
                "sandbox_candidate_reentry_static_validation_receipt_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "candidate_files_static_validated": True,
                "candidate_payload_written": True,
                "candidate_files_created": True,
                "candidate_execution_requested": False,
                "candidate_executed": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "approval_for_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope_only": True,
                "real_apply_allowed_after_d165_by_ai": False,
                "route_insert_allowed_after_d165_by_ai": False,
                "protected_core_mutation_allowed_after_d165_by_ai": False,
                "network_allowed_after_d165_by_ai": False,
                "secret_read_allowed_after_d165_by_ai": False,
                "shell_allowed_after_d165_by_ai": False,
                "git_action_allowed_after_d165_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D165_PLUS",
                "static_validation_status": "STATIC_VALIDATION_PASSED_NO_EXECUTION",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATED_READY_FOR_CONTROLLED_EXECUTION_PREFLIGHT",
                "source_response_mode": "DRY_CAPTURE_PLACEHOLDER_ONLY",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_ONLY",
                "next_step": "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE",
            },
        }

        validation_report = {
            **no_ai_flags(),
            "ok": True,
            "static_validation_status": "STATIC_VALIDATION_PASSED_NO_EXECUTION",
            "candidate_files_static_validated": True,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        validation_receipt = {
            **no_ai_flags(),
            "ok": True,
            "receipt_status": "STATIC_VALIDATION_RECORDED_NO_EXECUTION_NO_APPLY",
            "candidate_files_static_validated": True,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "no_candidate_execution": True,
            "no_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
            "human_review_required": True,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        d166_scope = {
            "ok": True,
            "allowed_next_gate": "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE",
            "sandbox_candidate_reentry_controlled_execution_preflight_scope_only": True,
            "candidate_files_static_validated": True,
            "candidate_execution_allowed_next_only_after_preflight": True,
            "candidate_execution_allowed_after_d165": False,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d165_by_ai": False,
            "route_insert_allowed_after_d165_by_ai": False,
            "protected_core_mutation_allowed_after_d165_by_ai": False,
            "network_allowed_after_d165_by_ai": False,
            "secret_read_allowed_after_d165_by_ai": False,
            "shell_allowed_after_d165_by_ai": False,
            "git_action_allowed_after_d165_by_ai": False,
        }

        write(root / "reports/d165_sandbox_candidate_reentry_static_validation_scope.json", d165)
        write(root / "reports/d165_sandbox_candidate_reentry_static_validation_report.json", validation_report)
        write(root / "reports/d165_sandbox_candidate_reentry_static_validation_receipt.json", validation_receipt)
        write(root / "reports/d165_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json", d166_scope)
        return td, root

    def test_creates_controlled_execution_preflight_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_controlled_execution_preflight_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_ONLY")
            self.assertEqual(r["d167_scope"]["allowed_next_gate"], "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE")
            self.assertTrue(r["guardrails"]["execution_authority_guard_created"])
            self.assertFalse(r["guardrails"]["candidate_executed"])
            self.assertFalse(r["guardrails"]["apply_executed"])
            self.assertTrue((root / "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json").exists())
            self.assertTrue((root / "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_report.json").exists())
            self.assertTrue((root / "reports/d166_sandbox_candidate_reentry_execution_authority_guard.json").exists())
            self.assertTrue((root / "reports/d166_d167_sandbox_candidate_reentry_human_execution_intent_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d165(self):
        td, root = self.root()
        try:
            (root / "reports/d165_sandbox_candidate_reentry_static_validation_scope.json").unlink()
            r = create_sandbox_candidate_reentry_controlled_execution_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_validation_report_executed_candidate(self):
        td, root = self.root()
        try:
            p = root / "reports/d165_sandbox_candidate_reentry_static_validation_report.json"
            data = json.loads(p.read_text())
            data["candidate_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_execution_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d166_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d165_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d165_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_execution_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_receipt_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d165_sandbox_candidate_reentry_static_validation_receipt.json"
            data = json.loads(p.read_text())
            data["apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_execution_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
