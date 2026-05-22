
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.controlled_autonomy_proposal_reentry_scope import create_controlled_autonomy_proposal_reentry_scope


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


class TestD179ControlledAutonomyProposalReentryScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        d178 = {
            "ok": True,
            "decision": "CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_READY",
            "provider_reentry_id": "d178-test",
            "cycle_intake_id": "d177-test",
            "controlled_next_cycle_id": "d176-test",
            "archive_id": "d175-test",
            "final_audit_id": "d174-test",
            "post_apply_verification_id": "d173-test",
            "guarded_apply_id": "d172-test",
            "apply_intent_id": "d171-test",
            "run_id": "d168-test",
            "intent_id": "d167-test",
            "candidate_id": "d164-test",
            "response_id": "d163-test",
            "proposal_id": "d107-valid-test",
            "guardrails": {
                **no_ai_flags(),
                "controlled_autonomy_provider_reentry_scope_only": True,
                "controlled_autonomy_provider_dry_ping_scope_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "provider_reentry_scope_created": True,
                "provider_dry_ping_scope_created": True,
                "proposal_reentry_scope_created": True,
                "provider_call_authorized": False,
                "provider_response_authorized": False,
                "provider_network_call_performed": False,
                "provider_dry_ping_real_network": False,
                "authority_carried_forward": False,
                "provider_authority_carried_forward": False,
                "candidate_apply_executed": False,
                "candidate_apply_executed_by_ai": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "real_apply_executed": False,
                "actual_apply_executed": False,
                "approval_for_d179_controlled_autonomy_proposal_reentry_scope_only": True,
                "network_allowed_after_d178_by_ai": False,
                "secret_read_allowed_after_d178_by_ai": False,
                "shell_allowed_after_d178_by_ai": False,
                "real_apply_allowed_after_d178_by_ai": False,
                "route_insert_allowed_after_d178_by_ai": False,
                "protected_core_mutation_allowed_after_d178_by_ai": False,
                "git_action_allowed_after_d178_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D178_PLUS",
                "provider_reentry_status": "PROVIDER_REENTRY_SCOPE_CREATED_NO_PROVIDER_CALL",
                "provider_dry_ping_status": "PROVIDER_DRY_PING_SCOPE_CREATED_NO_NETWORK",
                "candidate_status": "CONTROLLED_AUTONOMY_READY_FOR_PROPOSAL_REENTRY_SCOPE",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_ONLY",
                "next_step": "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE",
            },
        }

        provider_dry_ping = {
            **no_ai_flags(),
            "ok": True,
            "provider_dry_ping_status": "PROVIDER_DRY_PING_SCOPE_CREATED_NO_NETWORK",
            "provider_reentry_status": "PROVIDER_REENTRY_SCOPE_CREATED_NO_PROVIDER_CALL",
            "dry_ping_mode": "LOCAL_RECORD_ONLY_NO_NETWORK",
            "provider_call_authorized": False,
            "provider_response_authorized": False,
            "provider_network_call_performed": False,
            "provider_dry_ping_real_network": False,
            "authority_carried_forward": False,
            "provider_authority_carried_forward": False,
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

        d179_scope = {
            "ok": True,
            "allowed_next_gate": "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE",
            "controlled_autonomy_proposal_reentry_scope_only": True,
            "provider_reentry_scope_created": True,
            "provider_dry_ping_scope_created": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "provider_call_authorized": False,
            "provider_response_authorized": False,
            "provider_network_call_performed": False,
            "provider_dry_ping_real_network": False,
            "authority_carried_forward": False,
            "provider_authority_carried_forward": False,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "network_allowed_after_d178_by_ai": False,
            "secret_read_allowed_after_d178_by_ai": False,
            "shell_allowed_after_d178_by_ai": False,
            "real_apply_allowed_after_d178_by_ai": False,
            "route_insert_allowed_after_d178_by_ai": False,
            "protected_core_mutation_allowed_after_d178_by_ai": False,
            "git_action_allowed_after_d178_by_ai": False,
        }

        write(root / "reports/d178_controlled_autonomy_provider_reentry_scope.json", d178)
        write(root / "reports/d178_controlled_autonomy_provider_dry_ping_scope.json", provider_dry_ping)
        write(root / "reports/d178_d179_controlled_autonomy_proposal_reentry_scope.json", d179_scope)
        return td, root

    def test_creates_proposal_reentry_outputs(self):
        td, root = self.root()
        try:
            r = create_controlled_autonomy_proposal_reentry_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D180_CONTROLLED_AUTONOMY_HUMAN_REVIEW_SCOPE_ONLY")
            self.assertEqual(r["d180_scope"]["allowed_next_gate"], "D180_CONTROLLED_AUTONOMY_HUMAN_REVIEW_SCOPE")
            self.assertTrue(r["guardrails"]["proposal_reentry_scope_created"])
            self.assertTrue(r["guardrails"]["proposal_candidate_packet_created"])
            self.assertTrue(r["guardrails"]["requires_human_review_before_any_apply"])
            self.assertFalse(r["guardrails"]["proposal_applied"])
            self.assertTrue((root / "reports/d179_controlled_autonomy_proposal_reentry_scope.json").exists())
            self.assertTrue((root / "reports/d179_controlled_autonomy_proposal_candidate_packet.json").exists())
            self.assertTrue((root / "reports/d179_d180_controlled_autonomy_human_review_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d178(self):
        td, root = self.root()
        try:
            (root / "reports/d178_controlled_autonomy_provider_reentry_scope.json").unlink()
            r = create_controlled_autonomy_proposal_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_provider_dry_ping_network_true(self):
        td, root = self.root()
        try:
            p = root / "reports/d178_controlled_autonomy_provider_dry_ping_scope.json"
            data = json.loads(p.read_text())
            data["provider_dry_ping_real_network"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_proposal_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d179_scope_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d178_d179_controlled_autonomy_proposal_reentry_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d178_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_proposal_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d178_not_ready(self):
        td, root = self.root()
        try:
            p = root / "reports/d178_controlled_autonomy_provider_reentry_scope.json"
            data = json.loads(p.read_text())
            data["decision"] = "BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_proposal_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
