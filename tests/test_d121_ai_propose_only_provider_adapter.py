
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.ai_propose_only_provider_adapter import create_ai_propose_only_provider_adapter_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD121AIProposeOnlyProviderAdapter(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        d120 = {
            "ok": True,
            "decision": "FIRST_CONTROLLED_RUN_SEAL_SCOPE_READY",
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
                "first_controlled_run_seal_scope_only": True,
                "ledger_only": True,
                "tag_plan_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "sealed_range": "D106-D120",
                "first_controlled_run_status": "SEALED",
                "real_apply_by_ai_status": "BLOCKED",
                "recommended_next_track": "D121_AI_PROPOSE_ONLY_PROVIDER_ADAPTER",
            },
        }

        chain = [
            "D106 AI Provider Boundary",
            "D107 Proposal Schema Validator",
            "D108 Sandbox Proposal Writer",
            "D109 Regression Runner",
            "D110 Human Review Gate",
            "D111 Explicit Approval Gate",
            "D112 Dry-Run Apply Scope",
            "D113 Final Apply Review Scope",
            "D114 Final Human Apply Decision Scope",
            "D115 Final Apply Phrase Scope",
            "D116 Manual Apply Window Scope",
            "D117 Manual Apply Command Review Scope",
            "D118 Operator Local Execution Evidence Scope",
            "D119 Post-Apply Verification Gate Scope",
            "D120 First Controlled Run Seal Scope",
        ]

        ledger = {
            "ok": True,
            "seal_id": seal_id,
            "chain": chain,
            "chain_length": 15,
            "run_status": "FIRST_CONTROLLED_RUN_SCOPE_SEALED",
            "real_apply_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "commands_executed_by_ai": False,
        }

        integrity = {
            "ok": True,
            "seal_id": seal_id,
            "sealed_range": "D106-D120",
            "integrity_status": "SEALED_WITH_REAL_APPLY_BY_AI_BLOCKED",
            "checks": {
                "d119_ok": True,
                "test_results_summary_ok": True,
                "git_state_summary_ok": True,
                "real_apply_by_ai_blocked": True,
                "ai_shell_execution_blocked": True,
                "ai_git_action_blocked": True,
                "protected_core_mutation_by_ai_blocked": True,
                "canonical_memory_overwrite_by_ai_blocked": True,
            },
        }

        tag_plan = {
            "ok": True,
            "seal_id": seal_id,
            "tag_plan_only": True,
            "tag_created_by_ai": False,
            "tag_pushed_by_ai": False,
        }

        write(root / "reports/d120_first_controlled_run_seal_scope.json", d120)
        write(root / "reports/d120_guarded_autonomy_run_ledger.json", ledger)
        write(root / "reports/d120_final_chain_integrity_summary.json", integrity)
        write(root / "reports/d120_first_run_release_tag_plan.json", tag_plan)

        return td, root

    def test_creates_provider_adapter_outputs(self):
        td, root = self.root()
        try:
            r = create_ai_propose_only_provider_adapter_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "AI_PROPOSE_ONLY_PROVIDER_ADAPTER_READY")
            self.assertEqual(r["summary"]["provider_mode"], "MOCK_PROPOSE_ONLY")
            self.assertEqual(r["summary"]["real_provider_status"], "DISABLED")
            self.assertEqual(r["summary"]["approval_scope"], "D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["api_key_read"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertTrue(r["provider_adapter_contract"]["mock_provider_only"])
            self.assertFalse(r["mock_provider_request_response"]["real_provider_called"])
            self.assertEqual(r["d122_scope"]["allowed_next_gate"], "D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE")
            self.assertTrue((root / "reports/d121_ai_propose_only_provider_adapter_scope.json").exists())
            self.assertTrue((root / "reports/d121_provider_adapter_contract.json").exists())
            self.assertTrue((root / "reports/d121_mock_provider_request_response.json").exists())
            self.assertTrue((root / "reports/d121_d122_operator_dashboard_start_command_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d120(self):
        td, root = self.root()
        try:
            (root / "reports/d120_first_controlled_run_seal_scope.json").unlink()
            r = create_ai_propose_only_provider_adapter_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d120_not_sealed(self):
        td, root = self.root()
        try:
            p = root / "reports/d120_first_controlled_run_seal_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["first_controlled_run_status"] = "OPEN"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_ai_propose_only_provider_adapter_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_integrity_not_blocking_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d120_final_chain_integrity_summary.json"
            data = json.loads(p.read_text())
            data["checks"]["real_apply_by_ai_blocked"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_ai_propose_only_provider_adapter_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_tag_plan_claims_ai_tag_push(self):
        td, root = self.root()
        try:
            p = root / "reports/d120_first_run_release_tag_plan.json"
            data = json.loads(p.read_text())
            data["tag_pushed_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_ai_propose_only_provider_adapter_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
