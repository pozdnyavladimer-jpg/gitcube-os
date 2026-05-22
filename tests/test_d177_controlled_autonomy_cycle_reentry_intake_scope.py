
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.controlled_autonomy_cycle_reentry_intake_scope import create_controlled_autonomy_cycle_reentry_intake_scope


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


class TestD177ControlledAutonomyCycleReentryIntakeScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        d176 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_NEXT_CYCLE_SCOPE_READY",
            "controlled_next_cycle_id": "d176-test",
            "archive_id": "d175-test",
            "final_audit_id": "d174-test",
            "run_id": "d168-test",
            "intent_id": "d167-test",
            "candidate_id": "d164-test",
            "response_id": "d163-test",
            "proposal_id": "d107-valid-test",
            "guardrails": {
                **no_ai_flags(),
                "sandbox_candidate_reentry_controlled_next_cycle_scope_only": True,
                "sandbox_candidate_reentry_next_cycle_reset_receipt_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "previous_chain_archived": True,
                "previous_chain_closed": True,
                "controlled_next_cycle_created": True,
                "next_cycle_reset_receipt_created": True,
                "fresh_cycle_intake_required": True,
                "next_cycle_requires_fresh_intent": True,
                "next_cycle_requires_human_review": True,
                "next_cycle_inherits_no_authority": True,
                "no_inherited_authority": True,
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
                "approval_for_d177_controlled_autonomy_cycle_reentry_intake_scope_only": True,
                "real_apply_allowed_after_d176_by_ai": False,
                "route_insert_allowed_after_d176_by_ai": False,
                "protected_core_mutation_allowed_after_d176_by_ai": False,
                "network_allowed_after_d176_by_ai": False,
                "secret_read_allowed_after_d176_by_ai": False,
                "shell_allowed_after_d176_by_ai": False,
                "git_action_allowed_after_d176_by_ai": False,
            },
            "summary": {
                "approval_scope": "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_ONLY",
                "next_step": "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE",
            },
        }

        reset_receipt = {
            **no_ai_flags(),
            "ok": True,
            "next_cycle_reset_status": "REENTRY_CHAIN_CLOSED_FRESH_INTENT_REQUIRED_NO_INHERITED_AUTHORITY",
            "previous_chain_archived": True,
            "next_cycle_requires_fresh_intent": True,
            "next_cycle_requires_human_review": True,
            "next_cycle_inherits_no_authority": True,
            "authority_carried_forward": False,
            "provider_authority_carried_forward": False,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_apply_executed": False,
            "actual_apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        d177_scope = {
            "ok": True,
            "allowed_next_gate": "D177_CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE",
            "controlled_autonomy_cycle_reentry_intake_scope_only": True,
            "fresh_cycle_intake_required": True,
            "previous_chain_closed": True,
            "previous_chain_archived": True,
            "no_inherited_authority": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "authority_carried_forward": False,
            "provider_authority_carried_forward": False,
            "candidate_apply_executed": False,
            "candidate_apply_executed_by_ai": False,
            "real_apply_allowed_after_d176_by_ai": False,
            "route_insert_allowed_after_d176_by_ai": False,
            "protected_core_mutation_allowed_after_d176_by_ai": False,
            "network_allowed_after_d176_by_ai": False,
            "secret_read_allowed_after_d176_by_ai": False,
            "shell_allowed_after_d176_by_ai": False,
            "git_action_allowed_after_d176_by_ai": False,
        }

        write(root / "reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json", d176)
        write(root / "reports/d176_sandbox_candidate_reentry_next_cycle_reset_receipt.json", reset_receipt)
        write(root / "reports/d176_d177_controlled_autonomy_cycle_reentry_intake_scope.json", d177_scope)
        return td, root

    def test_creates_cycle_reentry_intake_outputs(self):
        td, root = self.root()
        try:
            r = create_controlled_autonomy_cycle_reentry_intake_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "CONTROLLED_AUTONOMY_CYCLE_REENTRY_INTAKE_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE_ONLY")
            self.assertEqual(r["d178_scope"]["allowed_next_gate"], "D178_CONTROLLED_AUTONOMY_PROVIDER_REENTRY_SCOPE")
            self.assertTrue(r["guardrails"]["cycle_reentry_intake_created"])
            self.assertTrue(r["guardrails"]["fresh_intent_packet_created"])
            self.assertFalse(r["guardrails"]["authority_carried_forward"])
            self.assertFalse(r["guardrails"]["provider_call_authorized"])
            self.assertTrue((root / "reports/d177_controlled_autonomy_cycle_reentry_intake_scope.json").exists())
            self.assertTrue((root / "reports/d177_controlled_autonomy_cycle_fresh_intent_packet.json").exists())
            self.assertTrue((root / "reports/d177_d178_controlled_autonomy_provider_reentry_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d176(self):
        td, root = self.root()
        try:
            (root / "reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json").unlink()
            r = create_controlled_autonomy_cycle_reentry_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_reset_carries_authority(self):
        td, root = self.root()
        try:
            p = root / "reports/d176_sandbox_candidate_reentry_next_cycle_reset_receipt.json"
            data = json.loads(p.read_text())
            data["authority_carried_forward"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_cycle_reentry_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d177_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d176_d177_controlled_autonomy_cycle_reentry_intake_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d176_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_cycle_reentry_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d176_not_ready(self):
        td, root = self.root()
        try:
            p = root / "reports/d176_sandbox_candidate_reentry_controlled_next_cycle_scope.json"
            data = json.loads(p.read_text())
            data["decision"] = "BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_controlled_autonomy_cycle_reentry_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
