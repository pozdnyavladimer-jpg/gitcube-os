
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.controlled_autonomy_provider_reentry_scope import create_controlled_autonomy_provider_reentry_scope


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


class TestD178ControlledAutonomyProviderReentryScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        d177 = {
            "ok": True,
            "decision": "CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_READY",
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
                "controlled_autonomy_cycle_reentry_intake_scope_only": True,
                "controlled_autonomy_cycle_fresh_intent_packet_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_cycle_intake_required": True,
                "previous_chain_closed": True,
                "previous_chain_archived": True,
                "no_inherited_authority": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "cycle_reentry_intake_created": True,
                "fresh_intent_packet_created": True,
                "authority_carried_forward": False,
                "provider_authority_carried_forward": False,
                "provider_call_authorized": False,
                "provider_response_authorized": False,
                "candidate_apply_executed": False,
                "candidate_apply_executed_by_ai": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "real_apply_executed": False,
                "actual_apply_executed": False,
                "approval_for_d178_controlled_autonomy_provider_reentry_scope_only": True,
                "network_allowed_after_d177_by_ai": False,
                "secret_read_allowed_after_d177_by_ai": False,
                "shell_allowed_after_d177_by_ai": False,
                "real_apply_allowed_after_d177_by_ai": False,
                "route_insert_allowed_after_d177_by_ai": False,
                "protected_core_mutation_allowed_after_d177_by_ai": False,
                "git_action_allowed_after_d177_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D177_PLUS",
                "cycle_reentry_intake_status": "FRESH_CYCLE_REENTRY_INTAKE_CREATED_NO_INHERITED_AUTHORITY",
                "fresh_intent_packet_status": "FRESH_INTENT_PACKET_CREATED_NO_INHERITED_AUTHORITY",
                "candidate_status": "CONTROLLED_AUTONOMY_READY_FOR_PROVIDER_REENTRY_SCOPE",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "EXECUTED_IN_SANDBOX_NO_OP_ONLY",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_ONLY",
                "next_step": "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE",
            },
        }

        fresh_intent_packet = {
            **no_ai_flags(),
            "ok": True,
            "fresh_intent_packet_status": "FRESH_INTENT_PACKET_CREATED_NO_INHERITED_AUTHORITY",
            "packet_mode": "CONTROLLED_AUTONOMY_REENTRY_RECORD_ONLY",
            "previous_chain_archived": True,
            "previous_chain_closed": True,
            "fresh_cycle_intake_required": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "no_inherited_authority": True,
            "authority_carried_forward": False,
            "provider_authority_carried_forward": False,
            "provider_call_authorized": False,
            "provider_response_authorized": False,
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

        d178_scope = {
            "ok": True,
            "allowed_next_gate": "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE",
            "controlled_autonomy_provider_reentry_scope_only": True,
            "fresh_intent_packet_created": True,
            "fresh_cycle_intake_required": True,
            "previous_chain_archived": True,
            "previous_chain_closed": True,
            "no_inherited_authority": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "provider_call_authorized": False,
            "provider_response_authorized": False,
            "authority_carried_forward": False,
            "provider_authority_carried_forward": False,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "network_allowed_after_d177_by_ai": False,
            "secret_read_allowed_after_d177_by_ai": False,
            "shell_allowed_after_d177_by_ai": False,
            "real_apply_allowed_after_d177_by_ai": False,
            "route_insert_allowed_after_d177_by_ai": False,
            "protected_core_mutation_allowed_after_d177_by_ai": False,
            "git_action_allowed_after_d177_by_ai": False,
        }

        write(root / "reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json", d177)
        write(root / "reports/d177_controlled_autonomy_cycle_fresh_intent_packet.json", fresh_intent_packet)
        write(root / "reports/d177_d178_controlled_autonomy_provider_reentry_scope.json", d178_scope)
        return td, root

    def test_creates_provider_reentry_outputs(self):
        td, root = self.root()
        try:
            r = create_controlled_autonomy_provider_reentry_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE_ONLY")
            self.assertEqual(r["d179_scope"]["allowed_next_gate"], "D179_CONTROLLED_AUTONOMY_PROPOSAL_REENTRY_SCOPE")
            self.assertTrue(r["guardrails"]["provider_reentry_scope_created"])
            self.assertTrue(r["guardrails"]["provider_dry_ping_scope_created"])
            self.assertFalse(r["guardrails"]["provider_call_authorized"])
            self.assertFalse(r["guardrails"]["provider_network_call_performed"])
            self.assertTrue((root / "reports/d178_controlled_autonomy_provider_reentry_scope.json").exists())
            self.assertTrue((root / "reports/d178_controlled_autonomy_provider_dry_ping_scope.json").exists())
            self.assertTrue((root / "reports/d178_d179_controlled_autonomy_proposal_reentry_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d177(self):
        td, root = self.root()
        try:
            (root / "reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json").unlink()
            r = create_controlled_autonomy_provider_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_fresh_packet_authorizes_provider(self):
        td, root = self.root()
        try:
            p = root / "reports/d177_controlled_autonomy_cycle_fresh_intent_packet.json"
            data = json.loads(p.read_text())
            data["provider_call_authorized"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_provider_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d178_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d177_d178_controlled_autonomy_provider_reentry_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d177_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_provider_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d177_not_ready(self):
        td, root = self.root()
        try:
            p = root / "reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json"
            data = json.loads(p.read_text())
            data["decision"] = "BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_provider_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
