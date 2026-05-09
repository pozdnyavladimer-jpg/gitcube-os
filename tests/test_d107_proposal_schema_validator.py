
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.proposal_schema_validator import (
    create_proposal_schema_validator,
    load_contracts,
    make_mock_valid_proposal,
    make_mock_invalid_proposal,
    validate_ai_proposal,
)


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD107ProposalSchemaValidator(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        forbidden_fields = [
            "api_key",
            "api_secret",
            "token",
            "password",
            "raw_shell_command",
            "shell_command",
            "subprocess",
            "exec",
            "eval",
            "auto_apply",
            "apply_now",
            "git_commit",
            "git_push",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "direct_core_edit",
        ]
        forbidden_actions = [
            "real_apply",
            "auto_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "shell_exec",
            "subprocess_exec",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute",
            "restore_execute",
            "delete_runtime_candidate",
        ]
        allowed_prefixes = [
            "runtime_experimental/ai_sandbox_work/",
            "reports/",
            "tests/",
            "docs/",
        ]
        blocked_prefixes = [
            "app/orchestration/",
            "core/",
            "runtime/",
            "bridges/",
            "memory/",
        ]
        required_fields = [
            "proposal_id",
            "proposal_type",
            "intent",
            "target_scope",
            "candidate_files",
            "risk_flags",
            "guardrails",
            "validation_plan",
            "requires_human_review",
        ]
        allowed_types = [
            "documentation_proposal",
            "test_proposal",
            "sandbox_patch_proposal",
            "analysis_proposal",
            "schema_proposal",
        ]

        write(root / "reports/d106_ai_provider_boundary.json", {
            "ok": True,
            "decision": "AI_PROVIDER_BOUNDARY_READY",
            "boundary_id": "d106-test",
            "guardrails": {
                "external_ai_called": False,
                "network_accessed": False,
                "api_key_read": False,
                "secret_read": False,
                "shell_executed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
                "rollback_executed": False,
                "restore_executed": False,
                "mock_provider_only": True,
                "json_only": True,
                "proposal_only": True,
            },
        })
        write(root / "reports/d106_provider_input_contract.json", {
            "ok": True,
            "allowed_scope": allowed_prefixes,
            "blocked_scope": blocked_prefixes,
        })
        write(root / "reports/d106_provider_output_contract.json", {
            "ok": True,
            "required_output_fields": required_fields,
            "allowed_proposal_types": allowed_types,
            "forbidden_fields": forbidden_fields,
            "forbidden_actions": forbidden_actions,
        })
        write(root / "reports/d106_forbidden_action_matrix.json", {
            "ok": True,
            "forbidden_actions": {x: True for x in forbidden_actions},
            "forbidden_fields": {x: True for x in forbidden_fields},
        })
        write(root / "reports/d106_d107_proposal_schema_validator_scope.json", {
            "ok": True,
            "allowed_next_gate": "D107_PROPOSAL_SCHEMA_VALIDATOR",
            "d107_allowed_to_create": [
                "proposal_schema_validator",
                "proposal_contract_report",
                "proposal_rejection_report",
                "proposal_acceptance_manifest",
            ],
            "proposal_contract": {
                "required_output_fields": required_fields,
                "allowed_proposal_types": allowed_types,
                "allowed_candidate_prefixes": allowed_prefixes,
                "blocked_candidate_prefixes": blocked_prefixes,
            },
        })

        return td, root

    def test_creates_validator_reports(self):
        td, root = self.root()
        try:
            r = create_proposal_schema_validator(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "PROPOSAL_SCHEMA_VALIDATOR_READY")
            self.assertTrue(r["summary"]["valid_mock_accepted"])
            self.assertTrue(r["summary"]["invalid_mock_rejected"])
            self.assertEqual(r["d108_scope"]["allowed_next_gate"], "D108_SANDBOX_PROPOSAL_WRITER")
            self.assertTrue((root / "reports/d107_proposal_schema_validator.json").exists())
            self.assertTrue((root / "reports/d107_proposal_contract_report.json").exists())
            self.assertTrue((root / "reports/d107_mock_valid_proposal.json").exists())
            self.assertTrue((root / "reports/d107_rejection_report.json").exists())
            self.assertTrue((root / "reports/d107_acceptance_manifest.json").exists())
            self.assertTrue((root / "reports/d107_d108_sandbox_proposal_writer_scope.json").exists())
        finally:
            td.cleanup()

    def test_accepts_valid_proposal(self):
        td, root = self.root()
        try:
            contract = load_contracts(root)
            proposal = make_mock_valid_proposal()
            errors, warnings = validate_ai_proposal(proposal, contract)
            self.assertEqual(errors, [])
        finally:
            td.cleanup()

    def test_rejects_forbidden_shell_field(self):
        td, root = self.root()
        try:
            contract = load_contracts(root)
            proposal = make_mock_valid_proposal()
            proposal["shell_command"] = "git push"
            errors, warnings = validate_ai_proposal(proposal, contract)
            self.assertTrue(errors)
        finally:
            td.cleanup()

    def test_rejects_blocked_core_path(self):
        td, root = self.root()
        try:
            contract = load_contracts(root)
            proposal = make_mock_valid_proposal()
            proposal["candidate_files"] = ["core/unsafe.py"]
            errors, warnings = validate_ai_proposal(proposal, contract)
            self.assertTrue(errors)
        finally:
            td.cleanup()

    def test_rejects_missing_human_review(self):
        td, root = self.root()
        try:
            contract = load_contracts(root)
            proposal = make_mock_valid_proposal()
            proposal["requires_human_review"] = False
            errors, warnings = validate_ai_proposal(proposal, contract)
            self.assertTrue(errors)
        finally:
            td.cleanup()

    def test_blocks_if_d106_missing(self):
        td, root = self.root()
        try:
            (root / "reports/d106_ai_provider_boundary.json").unlink()
            r = create_proposal_schema_validator(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "PROPOSAL_SCHEMA_VALIDATOR_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
