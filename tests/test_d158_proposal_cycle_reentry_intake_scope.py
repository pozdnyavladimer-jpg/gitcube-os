
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.proposal_cycle_reentry_intake_scope import create_proposal_cycle_reentry_intake_scope
from runtime_experimental.canonical_guard_schema import normalize_guard_flags

def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")

class TestD158ProposalCycleReentryIntakeScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        reentry_id = "d157-test"
        next_cycle_id = "d156-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d157 = {
            "ok": True,
            "decision": "PROVIDER_CYCLE_REENTRY_SCOPE_READY",
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
                "real_provider_call_performed": False,
                "provider_network_call_performed": False,
                "provider_secret_read_performed": False,
                "provider_response_ingested": False,
                "provider_cycle_reentry_scope_only": True,
                "provider_reentry_config_manifest_only": True,
                "provider_reentry_dry_ping_scope_only": True,
                "fresh_intent_required": True,
                "approval_for_d158_proposal_cycle_reentry_intake_scope_only": True,
                "real_apply_allowed_after_d157_by_ai": False,
                "route_insert_allowed_after_d157_by_ai": False,
                "protected_core_mutation_allowed_after_d157_by_ai": False,
                "network_allowed_after_d157_by_ai": False,
                "secret_read_allowed_after_d157_by_ai": False,
                "shell_allowed_after_d157_by_ai": False,
                "git_action_allowed_after_d157_by_ai": False,
            },
            "summary": {
                "provider_reentry_status": "PROVIDER_REENTRY_CONFIG_CREATED_NO_NETWORK_NO_SECRET",
                "dry_ping_status": "DRY_PING_SCOPE_CREATED_PROVIDER_NOT_CALLED",
                "candidate_status": "NEXT_CYCLE_PROVIDER_REENTRY_READY_NO_PROVIDER_CALL",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_ONLY",
                "next_step": "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE",
            },
        }

        config = {
            "ok": True,
            "provider_reentry_status": "PROVIDER_REENTRY_CONFIG_CREATED_NO_NETWORK_NO_SECRET",
            "fresh_intent_required": True,
            "manual_provider_enable_required": True,
            "dry_ping_scope_required": True,
            "human_review_required": True,
            "real_provider_call_performed": False,
            "provider_network_call_performed": False,
            "provider_secret_read_performed": False,
            "provider_response_ingested": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
        }

        dry_ping = {
            "ok": True,
            "dry_ping_status": "DRY_PING_SCOPE_CREATED_PROVIDER_NOT_CALLED",
            "dry_ping_executes_provider": False,
            "real_provider_call_performed": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
        }

        d158_scope = {
            "ok": True,
            "allowed_next_gate": "D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE",
            "proposal_cycle_reentry_intake_scope_only": True,
            "fresh_intent_required": True,
            "provider_response_must_be_dry_or_manual": True,
            "human_review_required": True,
            "real_apply_allowed_after_d157_by_ai": False,
            "route_insert_allowed_after_d157_by_ai": False,
            "protected_core_mutation_allowed_after_d157_by_ai": False,
            "network_allowed_after_d157_by_ai": False,
            "secret_read_allowed_after_d157_by_ai": False,
            "shell_allowed_after_d157_by_ai": False,
            "git_action_allowed_after_d157_by_ai": False,
        }

        write(root / "reports/d157_provider_cycle_reentry_scope.json", d157)
        write(root / "reports/d157_provider_reentry_config_manifest.json", config)
        write(root / "reports/d157_provider_reentry_dry_ping_scope.json", dry_ping)
        write(root / "reports/d157_d158_proposal_cycle_reentry_intake_scope.json", d158_scope)
        return td, root

    def test_creates_proposal_cycle_reentry_intake_outputs(self):
        td, root = self.root()
        try:
            r = create_proposal_cycle_reentry_intake_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE_ONLY")
            self.assertTrue(r["guardrails"]["canonical_guard_schema_applied"])
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["route_inserted_by_ai"])
            self.assertEqual(r["d159_scope"]["allowed_next_gate"], "D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE")
            self.assertTrue((root / "reports/d158_canonical_guard_schema.json").exists())
            self.assertTrue((root / "reports/d158_proposal_cycle_reentry_intake_scope.json").exists())
            self.assertTrue((root / "reports/d158_proposal_reentry_intake_manifest.json").exists())
            self.assertTrue((root / "reports/d158_proposal_reentry_no_execution_assertions.json").exists())
            self.assertTrue((root / "reports/d158_d159_proposal_to_sandbox_candidate_reentry_scope.json").exists())
        finally:
            td.cleanup()

    def test_canonical_schema_normalizes_missing_safe_aliases(self):
        d = normalize_guard_flags({"network_accessed": False})
        self.assertFalse(d["route_inserted_by_ai"])
        self.assertFalse(d["protected_core_mutated_by_ai"])
        self.assertFalse(d["shell_executed_by_ai"])
        self.assertFalse(d["git_action_by_ai"])

    def test_blocks_missing_d157(self):
        td, root = self.root()
        try:
            (root / "reports/d157_provider_cycle_reentry_scope.json").unlink()
            r = create_proposal_cycle_reentry_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d157_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d157_provider_cycle_reentry_scope.json"
            data = json.loads(p.read_text())
            data["guardrails"]["network_allowed_after_d157_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_proposal_cycle_reentry_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_dry_ping_executes_provider(self):
        td, root = self.root()
        try:
            p = root / "reports/d157_provider_reentry_dry_ping_scope.json"
            data = json.loads(p.read_text())
            data["dry_ping_executes_provider"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_proposal_cycle_reentry_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

if __name__ == "__main__":
    unittest.main()
