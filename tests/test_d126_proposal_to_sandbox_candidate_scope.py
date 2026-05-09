
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.proposal_to_sandbox_candidate_scope import create_proposal_to_sandbox_candidate_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD126ProposalToSandboxCandidateScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        intake_id = "d125-test"
        ping_id = "d124-test"
        config_id = "d123-test"
        dashboard_id = "d122-test"
        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        d125 = {
            "ok": True,
            "decision": "PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_READY",
            "intake_id": intake_id,
            "ping_id": ping_id,
            "config_id": config_id,
            "dashboard_id": dashboard_id,
            "adapter_id": adapter_id,
            "seal_id": seal_id,
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
                "provider_response_intake_scope_only": True,
                "schema_validation_only": True,
                "rejection_report_only": True,
                "real_provider_called_now": False,
                "approval_for_d126_sandbox_candidate_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "intake_status": "PROPOSAL_SHAPE_ACCEPTED",
                "schema_validator_status": "PASS",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "approval_scope": "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_ONLY",
                "next_step": "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE",
            },
        }

        schema_validator = {
            "ok": True,
            "intake_id": intake_id,
            "ping_id": ping_id,
            "adapter_id": adapter_id,
            "proposal_id": proposal_id,
            "validator_mode": "PROPOSAL_SHAPE_ONLY_NO_EXECUTION",
            "response_shape_valid": True,
            "response_shape_errors": [],
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        rejection_report = {
            "ok": True,
            "intake_id": intake_id,
            "provider_response_rejected": False,
            "accepted_for_d126_sandbox_candidate_scope": True,
            "human_review_required": True,
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        d126_scope = {
            "ok": True,
            "intake_id": intake_id,
            "allowed_next_gate": "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE",
            "proposal_to_sandbox_candidate_scope_only": True,
            "human_review_required": True,
            "schema_validator_ok": True,
            "intake_rejected": False,
            "real_provider_call_executed_after_d125": False,
            "network_call_executed_after_d125": False,
            "api_key_read_after_d125": False,
            "real_apply_allowed_after_d125_by_ai": False,
            "route_insert_allowed_after_d125_by_ai": False,
            "protected_core_mutation_allowed_after_d125_by_ai": False,
        }

        write(root / "reports/d125_provider_response_to_proposal_intake_scope.json", d125)
        write(root / "reports/d125_provider_response_schema_validator.json", schema_validator)
        write(root / "reports/d125_provider_intake_rejection_report.json", rejection_report)
        write(root / "reports/d125_d126_proposal_to_sandbox_candidate_scope.json", d126_scope)

        return td, root

    def test_creates_sandbox_candidate_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_proposal_to_sandbox_candidate_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_READY")
            self.assertEqual(r["summary"]["sandbox_candidate_status"], "PLAN_CREATED_NOT_WRITTEN_NOT_EXECUTED")
            self.assertEqual(r["summary"]["approval_scope"], "D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d127_scope"]["allowed_next_gate"], "D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE")
            self.assertTrue((root / "reports/d126_proposal_to_sandbox_candidate_scope.json").exists())
            self.assertTrue((root / "reports/d126_sandbox_candidate_write_plan.json").exists())
            self.assertTrue((root / "reports/d126_sandbox_candidate_static_scan.json").exists())
            self.assertTrue((root / "reports/d126_d127_sandbox_candidate_human_review_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d125(self):
        td, root = self.root()
        try:
            (root / "reports/d125_provider_response_to_proposal_intake_scope.json").unlink()
            r = create_proposal_to_sandbox_candidate_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_schema_validator_failed(self):
        td, root = self.root()
        try:
            p = root / "reports/d125_provider_response_schema_validator.json"
            data = json.loads(p.read_text())
            data["response_shape_valid"] = False
            data["response_shape_errors"] = ["bad shape"]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_proposal_to_sandbox_candidate_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_intake_rejected(self):
        td, root = self.root()
        try:
            p = root / "reports/d125_provider_intake_rejection_report.json"
            data = json.loads(p.read_text())
            data["provider_response_rejected"] = True
            data["accepted_for_d126_sandbox_candidate_scope"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_proposal_to_sandbox_candidate_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d126_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d125_d126_proposal_to_sandbox_candidate_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d125_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_proposal_to_sandbox_candidate_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
