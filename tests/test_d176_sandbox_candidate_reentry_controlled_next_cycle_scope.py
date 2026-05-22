
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_controlled_next_cycle_scope import create_sandbox_candidate_reentry_controlled_next_cycle_scope


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


class TestD176SandboxCandidateReentryControlledNextCycleScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        archive_id = "d175-test"
        final_audit_id = "d174-test"
        post_apply_verification_id = "d173-test"
        guarded_apply_id = "d172-test"
        apply_intent_id = "d171-test"
        apply_preflight_id = "d170-test"
        verification_id = "d169-test"
        run_id = "d168-test"
        intent_id = "d167-test"
        candidate_id = "d164-test"
        response_id = "d163-test"
        proposal_id = "d107-valid-test"

        d175 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE_READY",
            "archive_id": archive_id,
            "final_audit_id": final_audit_id,
            "post_apply_verification_id": post_apply_verification_id,
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
                "sandbox_candidate_reentry_chain_archive_scope_only": True,
                "sandbox_candidate_reentry_chain_archive_manifest_only": True,
                "sandbox_candidate_reentry_chain_closure_receipt_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "archive_manifest_created": True,
                "chain_closure_receipt_created": True,
                "chain_archived": True,
                "archive_ready": True,
                "final_apply_audit_complete": True,
                "final_apply_ledger_created": True,
                "replay_index_created": True,
                "post_apply_verified": True,
                "apply_integrity_verified": True,
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
                "approval_for_d176_sandbox_candidate_reentry_controlled_next_cycle_scope_only": True,
                "real_apply_allowed_after_d175_by_ai": False,
                "route_insert_allowed_after_d175_by_ai": False,
                "protected_core_mutation_allowed_after_d175_by_ai": False,
                "network_allowed_after_d175_by_ai": False,
                "secret_read_allowed_after_d175_by_ai": False,
                "shell_allowed_after_d175_by_ai": False,
                "git_action_allowed_after_d175_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D175_PLUS",
                "archive_status": "CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
                "chain_closure_status": "REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_ONLY",
                "next_step": "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE",
            },
        }

        archive_manifest = {
            **no_ai_flags(),
            "ok": True,
            "archive_status": "CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
            "archive_mode": "LOCAL_JSON_MANIFEST_ONLY",
            "archive_ready": True,
            "archive_uploaded": False,
            "archive_compressed": False,
            "final_apply_audit_complete": True,
            "final_apply_ledger_created": True,
            "replay_index_created": True,
            "post_apply_verified": True,
            "apply_integrity_verified": True,
            "guarded_apply_recorded": True,
            "candidate_apply_recorded": True,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_apply_executed": False,
            "actual_apply_executed": False,
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

        closure_receipt = {
            **no_ai_flags(),
            "ok": True,
            "chain_closure_status": "REENTRY_CHAIN_ARCHIVED_READY_FOR_CONTROLLED_NEXT_CYCLE",
            "closure_mode": "LOCAL_RECORD_ONLY_NO_EXECUTION",
            "archive_ready": True,
            "archive_manifest_created": True,
            "final_apply_audit_complete": True,
            "final_apply_ledger_created": True,
            "replay_index_created": True,
            "post_apply_verified": True,
            "apply_integrity_verified": True,
            "guarded_apply_recorded": True,
            "candidate_apply_recorded": True,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_apply_executed": False,
            "actual_apply_executed": False,
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

        d176_scope = {
            "ok": True,
            "allowed_next_gate": "D176_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE",
            "sandbox_candidate_reentry_controlled_next_cycle_scope_only": True,
            "archive_manifest_created": True,
            "chain_closure_receipt_created": True,
            "chain_archived": True,
            "next_cycle_requires_fresh_intent": True,
            "next_cycle_requires_human_review": True,
            "next_cycle_inherits_no_authority": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_apply_allowed_after_d175_by_ai": False,
            "route_insert_allowed_after_d175_by_ai": False,
            "protected_core_mutation_allowed_after_d175_by_ai": False,
            "network_allowed_after_d175_by_ai": False,
            "secret_read_allowed_after_d175_by_ai": False,
            "shell_allowed_after_d175_by_ai": False,
            "git_action_allowed_after_d175_by_ai": False,
        }

        write(root / "reports/d175_sandbox_candidate_reentry_chain_archive_scope.json", d175)
        write(root / "reports/d175_sandbox_candidate_reentry_chain_archive_manifest.json", archive_manifest)
        write(root / "reports/d175_sandbox_candidate_reentry_chain_closure_receipt.json", closure_receipt)
        write(root / "reports/d175_d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json", d176_scope)
        return td, root

    def test_creates_controlled_next_cycle_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_controlled_next_cycle_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_ONLY")
            self.assertEqual(r["d177_scope"]["allowed_next_gate"], "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE")
            self.assertTrue(r["guardrails"]["controlled_next_cycle_created"])
            self.assertTrue(r["guardrails"]["next_cycle_inherits_no_authority"])
            self.assertFalse(r["guardrails"]["authority_carried_forward"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted_by_ai"])
            self.assertTrue((root / "reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json").exists())
            self.assertTrue((root / "reports/d176_sandbox_candidate_reentry_next_cycle_reset_receipt.json").exists())
            self.assertTrue((root / "reports/d176_d177_controlled_autonomy_cycle_reentry_intake_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d175(self):
        td, root = self.root()
        try:
            (root / "reports/d175_sandbox_candidate_reentry_chain_archive_scope.json").unlink()
            r = create_sandbox_candidate_reentry_controlled_next_cycle_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_archive_not_ready(self):
        td, root = self.root()
        try:
            p = root / "reports/d175_sandbox_candidate_reentry_chain_archive_manifest.json"
            data = json.loads(p.read_text())
            data["archive_ready"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_next_cycle_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_chain_closure_mutated_core(self):
        td, root = self.root()
        try:
            p = root / "reports/d175_sandbox_candidate_reentry_chain_closure_receipt.json"
            data = json.loads(p.read_text())
            data["protected_core_mutated_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_next_cycle_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d176_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d175_d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d175_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_controlled_next_cycle_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
