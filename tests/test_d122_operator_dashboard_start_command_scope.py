
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.operator_dashboard_start_command_scope import create_operator_dashboard_start_command_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD122OperatorDashboardStartCommandScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        d121 = {
            "ok": True,
            "decision": "AI_PROPOSE_ONLY_PROVIDER_ADAPTER_READY",
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
                "provider_adapter_scope_only": True,
                "real_provider_enabled_now": False,
                "mock_provider_only": True,
                "proposal_output_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "provider_mode": "MOCK_PROPOSE_ONLY",
                "real_provider_status": "DISABLED",
                "network_status": "BLOCKED",
                "real_apply_by_ai_status": "BLOCKED",
                "approval_scope": "D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE_ONLY",
                "next_step": "D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE",
            },
        }

        contract = {
            "ok": True,
            "adapter_id": adapter_id,
            "mode": "AI_PROVIDER_PROPOSE_ONLY",
            "real_provider_enabled_now": False,
            "mock_provider_only": True,
            "network_allowed_now": False,
            "secrets_allowed_now": False,
            "api_key_read_allowed_now": False,
            "output_contract": {
                "required_fields": [
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
            },
        }

        mock_exchange = {
            "ok": True,
            "adapter_id": adapter_id,
            "mock_only": True,
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "forbidden_hits": [],
            "response_valid_shape": True,
        }

        d122_scope = {
            "ok": True,
            "adapter_id": adapter_id,
            "allowed_next_gate": "D122_OPERATOR_DASHBOARD_START_COMMAND_SCOPE",
            "operator_dashboard_scope_only": True,
            "human_review_required": True,
            "real_provider_enablement_allowed_now": False,
            "real_apply_allowed_after_d121_by_ai": False,
            "route_insert_allowed_after_d121_by_ai": False,
            "protected_core_mutation_allowed_after_d121_by_ai": False,
            "sandbox_candidate_execution_allowed_after_d121_by_ai": False,
            "d122_must_not_execute": [
                "real_apply_by_ai",
                "auto_apply",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "external_ai_network_call_now",
                "shell_exec_from_ai",
                "git_commit_by_ai",
                "git_push_by_ai",
                "rollback_execute_by_ai",
                "restore_execute_by_ai",
                "execute_sandbox_candidate_by_ai",
                "commit_sandbox_candidate_by_ai",
            ],
        }

        write(root / "reports/d121_ai_propose_only_provider_adapter_scope.json", d121)
        write(root / "reports/d121_provider_adapter_contract.json", contract)
        write(root / "reports/d121_mock_provider_request_response.json", mock_exchange)
        write(root / "reports/d121_d122_operator_dashboard_start_command_scope.json", d122_scope)

        return td, root

    def test_creates_dashboard_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_operator_dashboard_start_command_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "OPERATOR_DASHBOARD_START_COMMAND_SCOPE_READY")
            self.assertEqual(r["summary"]["dashboard_mode"], "MOCK_PROPOSE_ONLY_SINGLE_ENTRY")
            self.assertEqual(r["summary"]["real_provider_status"], "DISABLED")
            self.assertEqual(r["summary"]["approval_scope"], "D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["api_key_read"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d123_scope"]["allowed_next_gate"], "D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE")
            self.assertTrue((root / "reports/d122_operator_dashboard_start_command_scope.json").exists())
            self.assertTrue((root / "reports/d122_single_entry_prompt_to_proposal_flow.json").exists())
            self.assertTrue((root / "reports/d122_dashboard_preflight_checklist.json").exists())
            self.assertTrue((root / "reports/d122_d123_provider_config_manual_enable_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d121(self):
        td, root = self.root()
        try:
            (root / "reports/d121_ai_propose_only_provider_adapter_scope.json").unlink()
            r = create_operator_dashboard_start_command_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_provider_enabled(self):
        td, root = self.root()
        try:
            p = root / "reports/d121_provider_adapter_contract.json"
            data = json.loads(p.read_text())
            data["real_provider_enabled_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_operator_dashboard_start_command_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_mock_called_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d121_mock_provider_request_response.json"
            data = json.loads(p.read_text())
            data["network_accessed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_operator_dashboard_start_command_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d122_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d121_d122_operator_dashboard_start_command_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d121_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_operator_dashboard_start_command_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
