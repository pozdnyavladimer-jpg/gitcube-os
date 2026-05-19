
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.proposal_to_sandbox_candidate_reentry_scope import create_proposal_to_sandbox_candidate_reentry_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD159ProposalToSandboxCandidateReentryScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        intake_id = "d158-test"
        reentry_id = "d157-test"
        next_cycle_id = "d156-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        schema = {
            "state": "D158_CANONICAL_GUARD_SCHEMA",
            "ok": True,
            "schema_status": "CANONICAL_GUARD_SCHEMA_CREATED_FOR_D158_PLUS",
            "normalization_rule": "MISSING_SAFE_ALIASES_NORMALIZE_TO_FALSE_DANGEROUS_TRUE_FLAGS_BLOCK",
        }

        d158 = {
            "ok": True,
            "decision": "PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_READY",
            "intake_id": intake_id,
            "reentry_id": reentry_id,
            "next_cycle_id": next_cycle_id,
            "cycle_closure_id": "d155-test",
            "candidate_id": candidate_id,
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
                "proposal_cycle_reentry_intake_scope_only": True,
                "proposal_reentry_intake_manifest_only": True,
                "proposal_reentry_no_execution_assertions_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "provider_response_ingested": False,
                "proposal_materialized": False,
                "candidate_created": False,
                "approval_for_d159_proposal_to_sandbox_candidate_reentry_scope_only": True,
                "real_apply_allowed_after_d158_by_ai": False,
                "route_insert_allowed_after_d158_by_ai": False,
                "protected_core_mutation_allowed_after_d158_by_ai": False,
                "network_allowed_after_d158_by_ai": False,
                "secret_read_allowed_after_d158_by_ai": False,
                "shell_allowed_after_d158_by_ai": False,
                "git_action_allowed_after_d158_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_CREATED_FOR_D158_PLUS",
                "proposal_reentry_status": "PROPOSAL_REENTRY_INTAKE_CREATED_NO_PROVIDER_RESPONSE_NO_EXECUTION",
                "candidate_status": "PROPOSAL_REENTRY_READY_FOR_SANDBOX_CANDIDATE_REENTRY_NOT_CREATED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE_ONLY",
                "next_step": "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE",
            },
        }

        manifest = {
            "ok": True,
            "proposal_reentry_status": "PROPOSAL_REENTRY_INTAKE_CREATED_NO_PROVIDER_RESPONSE_NO_EXECUTION",
            "fresh_intent_required": True,
            "provider_response_required_before_candidate": True,
            "human_review_required": True,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "proposal_materialized": False,
            "candidate_created": False,
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
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_apply": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
            "human_review_required": True,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "proposal_materialized": False,
            "candidate_created": False,
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

        d159_scope = {
            "ok": True,
            "allowed_next_gate": "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE",
            "proposal_to_sandbox_candidate_reentry_scope_only": True,
            "fresh_intent_required": True,
            "provider_response_required_before_candidate": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d158_by_ai": False,
            "route_insert_allowed_after_d158_by_ai": False,
            "protected_core_mutation_allowed_after_d158_by_ai": False,
            "network_allowed_after_d158_by_ai": False,
            "secret_read_allowed_after_d158_by_ai": False,
            "shell_allowed_after_d158_by_ai": False,
            "git_action_allowed_after_d158_by_ai": False,
        }

        write(root / "reports/d158_canonical_guard_schema.json", schema)
        write(root / "reports/d158_proposal_cycle_reentry_intake_scope.json", d158)
        write(root / "reports/d158_proposal_reentry_intake_manifest.json", manifest)
        write(root / "reports/d158_proposal_reentry_no_execution_assertions.json", assertions)
        write(root / "reports/d158_d159_proposal_to_sandbox_candidate_reentry_scope.json", d159_scope)
        return td, root

    def test_creates_proposal_to_sandbox_candidate_reentry_outputs(self):
        td, root = self.root()
        try:
            r = create_proposal_to_sandbox_candidate_reentry_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D160_SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE_ONLY")
            self.assertEqual(r["d160_scope"]["allowed_next_gate"], "D160_SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE")
            self.assertFalse(r["guardrails"]["candidate_payload_written"])
            self.assertFalse(r["guardrails"]["provider_response_ingested"])
            self.assertTrue((root / "reports/d159_proposal_to_sandbox_candidate_reentry_scope.json").exists())
            self.assertTrue((root / "reports/d159_sandbox_candidate_reentry_manifest.json").exists())
            self.assertTrue((root / "reports/d159_sandbox_candidate_reentry_no_touch_assertions.json").exists())
            self.assertTrue((root / "reports/d159_d160_sandbox_candidate_reentry_human_review_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d158(self):
        td, root = self.root()
        try:
            (root / "reports/d158_proposal_cycle_reentry_intake_scope.json").unlink()
            r = create_proposal_to_sandbox_candidate_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d158_candidate_created(self):
        td, root = self.root()
        try:
            p = root / "reports/d158_proposal_cycle_reentry_intake_scope.json"
            data = json.loads(p.read_text())
            data["guardrails"]["candidate_created"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_proposal_to_sandbox_candidate_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_manifest_provider_response_ingested(self):
        td, root = self.root()
        try:
            p = root / "reports/d158_proposal_reentry_intake_manifest.json"
            data = json.loads(p.read_text())
            data["provider_response_ingested"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_proposal_to_sandbox_candidate_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d159_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d158_d159_proposal_to_sandbox_candidate_reentry_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d158_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_proposal_to_sandbox_candidate_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
