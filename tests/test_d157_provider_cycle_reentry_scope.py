
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.provider_cycle_reentry_scope import create_provider_cycle_reentry_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD157ProviderCycleReentryScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        next_cycle_id = "d156-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d156 = {
            "ok": True,
            "decision": "CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE_READY",
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
                "controlled_autonomy_next_cycle_intake_scope_only": True,
                "next_cycle_intake_manifest_only": True,
                "next_cycle_safety_reset_report_only": True,
                "fresh_intent_required": True,
                "inherited_execution_authority": False,
                "approval_for_d157_provider_cycle_reentry_scope_only": True,
                "real_apply_allowed_after_d156_by_ai": False,
                "route_insert_allowed_after_d156_by_ai": False,
                "protected_core_mutation_allowed_after_d156_by_ai": False,
                "network_allowed_after_d156_by_ai": False,
                "secret_read_allowed_after_d156_by_ai": False,
                "shell_allowed_after_d156_by_ai": False,
                "git_action_allowed_after_d156_by_ai": False,
            },
            "summary": {
                "next_cycle_intake_status": "NEXT_CYCLE_INTAKE_CREATED_FRESH_INTENT_REQUIRED_NO_INHERITED_AUTHORITY",
                "safety_reset_status": "SAFETY_FLAGS_RESET_FOR_NEXT_CONTROLLED_CYCLE",
                "candidate_status": "PREVIOUS_CANDIDATE_CLOSED_NEXT_CYCLE_REQUIRES_FRESH_INTENT",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D157_PROVIDER_CYCLE_REENTRY_SCOPE_ONLY",
                "next_step": "D157_PROVIDER_CYCLE_REENTRY_SCOPE",
            },
        }

        intake_manifest = {
            "ok": True,
            "intake_status": "NEXT_CYCLE_INTAKE_CREATED_FRESH_INTENT_REQUIRED_NO_INHERITED_AUTHORITY",
            "fresh_intent_required": True,
            "inherited_execution_authority": False,
            "old_candidate_reuse_allowed": False,
            "old_apply_authority_reuse_allowed": False,
            "operator_review_required": True,
            "provider_reentry_scope_only": True,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        safety_reset = {
            "ok": True,
            "reset_status": "SAFETY_FLAGS_RESET_FOR_NEXT_CONTROLLED_CYCLE",
            "previous_cycle_closed": True,
            "fresh_intent_required": True,
            "provider_must_reenter_dry_scope": True,
            "candidate_must_be_rebuilt": True,
            "review_must_be_repeated": True,
            "apply_authority_must_be_reissued": True,
            "real_apply_allowed_after_d156_by_ai": False,
            "route_insert_allowed_after_d156_by_ai": False,
            "protected_core_mutation_allowed_after_d156_by_ai": False,
            "network_allowed_after_d156_by_ai": False,
            "secret_read_allowed_after_d156_by_ai": False,
            "shell_allowed_after_d156_by_ai": False,
            "git_action_allowed_after_d156_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        d157_scope = {
            "ok": True,
            "allowed_next_gate": "D157_PROVIDER_CYCLE_REENTRY_SCOPE",
            "provider_cycle_reentry_scope_only": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "real_apply_allowed_after_d156_by_ai": False,
            "route_insert_allowed_after_d156_by_ai": False,
            "protected_core_mutation_allowed_after_d156_by_ai": False,
            "network_allowed_after_d156_by_ai": False,
            "secret_read_allowed_after_d156_by_ai": False,
            "shell_allowed_after_d156_by_ai": False,
            "git_action_allowed_after_d156_by_ai": False,
        }

        write(root / "reports/d156_controlled_autonomy_next_cycle_intake_scope.json", d156)
        write(root / "reports/d156_next_cycle_intake_manifest.json", intake_manifest)
        write(root / "reports/d156_next_cycle_safety_reset_report.json", safety_reset)
        write(root / "reports/d156_d157_provider_cycle_reentry_scope.json", d157_scope)
        return td, root

    def test_creates_provider_cycle_reentry_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_provider_cycle_reentry_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "PROVIDER_CYCLE_REENTRY_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["real_provider_call_performed"])
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["secret_read"])
            self.assertEqual(r["d158_scope"]["allowed_next_gate"], "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE")
            self.assertTrue((root / "reports/d157_provider_cycle_reentry_scope.json").exists())
            self.assertTrue((root / "reports/d157_provider_reentry_config_manifest.json").exists())
            self.assertTrue((root / "reports/d157_provider_reentry_dry_ping_scope.json").exists())
            self.assertTrue((root / "reports/d157_d158_proposal_cycle_reentry_intake_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d156(self):
        td, root = self.root()
        try:
            (root / "reports/d156_controlled_autonomy_next_cycle_intake_scope.json").unlink()
            r = create_provider_cycle_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d156_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d156_controlled_autonomy_next_cycle_intake_scope.json"
            data = json.loads(p.read_text())
            data["guardrails"]["network_allowed_after_d156_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_cycle_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_safety_reset_allows_secret_read(self):
        td, root = self.root()
        try:
            p = root / "reports/d156_next_cycle_safety_reset_report.json"
            data = json.loads(p.read_text())
            data["secret_read_allowed_after_d156_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_cycle_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d157_scope_not_fresh_intent(self):
        td, root = self.root()
        try:
            p = root / "reports/d156_d157_provider_cycle_reentry_scope.json"
            data = json.loads(p.read_text())
            data["fresh_intent_required"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_cycle_reentry_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
