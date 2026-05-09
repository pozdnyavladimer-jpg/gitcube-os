
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.provider_config_manual_enable_scope import create_provider_config_manual_enable_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD123ProviderConfigManualEnableScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        dashboard_id = "d122-test"
        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        d122 = {
            "ok": True,
            "decision": "OPERATOR_DASHBOARD_START_COMMAND_SCOPE_READY",
            "dashboard_id": dashboard_id,
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
                "operator_dashboard_scope_only": True,
                "single_entry_prompt_flow_only": True,
                "real_provider_enabled_now": False,
                "mock_provider_only": True,
                "proposal_output_only": True,
                "approval_for_d123_config_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "dashboard_mode": "MOCK_PROPOSE_ONLY_SINGLE_ENTRY",
                "real_provider_status": "DISABLED",
                "network_status": "BLOCKED",
                "real_apply_by_ai_status": "BLOCKED",
                "approval_scope": "D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_ONLY",
                "next_step": "D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE",
            },
        }

        flow = {
            "ok": True,
            "dashboard_id": dashboard_id,
            "flow_mode": "MOCK_PROVIDER_PROPOSE_ONLY_NO_EXECUTION",
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        preflight = {
            "ok": True,
            "dashboard_id": dashboard_id,
            "dashboard_scope_only": True,
            "must_remain_false": {
                "real_provider_enabled_now": False,
                "external_ai_called": False,
                "network_accessed": False,
                "api_key_read": False,
                "secret_read": False,
                "shell_from_ai_executed": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "git_commit_by_ai": False,
                "git_push_by_ai": False,
            },
        }

        d123_scope = {
            "ok": True,
            "dashboard_id": dashboard_id,
            "allowed_next_gate": "D123_PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE",
            "provider_config_manual_enable_scope_only": True,
            "human_review_required": True,
            "real_provider_enabled_after_d122": False,
            "network_allowed_after_d122": False,
            "api_key_read_allowed_after_d122": False,
            "real_apply_allowed_after_d122_by_ai": False,
            "route_insert_allowed_after_d122_by_ai": False,
            "protected_core_mutation_allowed_after_d122_by_ai": False,
        }

        write(root / "reports/d122_operator_dashboard_start_command_scope.json", d122)
        write(root / "reports/d122_single_entry_prompt_to_proposal_flow.json", flow)
        write(root / "reports/d122_dashboard_preflight_checklist.json", preflight)
        write(root / "reports/d122_d123_provider_config_manual_enable_scope.json", d123_scope)
        return td, root

    def test_creates_provider_config_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_provider_config_manual_enable_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_READY")
            self.assertEqual(r["summary"]["provider_config_status"], "PLACEHOLDER_ONLY")
            self.assertEqual(r["summary"]["real_provider_status"], "DISABLED")
            self.assertEqual(r["summary"]["approval_scope"], "D124_REAL_PROVIDER_DRY_PING_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["api_key_read"])
            self.assertFalse(r["guardrails"]["secret_read"])
            self.assertEqual(r["d124_scope"]["allowed_next_gate"], "D124_REAL_PROVIDER_DRY_PING_SCOPE")
            self.assertTrue((root / "reports/d123_provider_config_manual_enable_scope.json").exists())
            self.assertTrue((root / "reports/d123_provider_secret_placeholder_policy.json").exists())
            self.assertTrue((root / "reports/d123_network_allowlist_dry_plan.json").exists())
            self.assertTrue((root / "reports/d123_d124_real_provider_dry_ping_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d122(self):
        td, root = self.root()
        try:
            (root / "reports/d122_operator_dashboard_start_command_scope.json").unlink()
            r = create_provider_config_manual_enable_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_flow_called_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d122_single_entry_prompt_to_proposal_flow.json"
            data = json.loads(p.read_text())
            data["network_accessed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_config_manual_enable_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_preflight_allows_secret(self):
        td, root = self.root()
        try:
            p = root / "reports/d122_dashboard_preflight_checklist.json"
            data = json.loads(p.read_text())
            data["must_remain_false"]["secret_read"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_config_manual_enable_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d123_scope_allows_provider_now(self):
        td, root = self.root()
        try:
            p = root / "reports/d122_d123_provider_config_manual_enable_scope.json"
            data = json.loads(p.read_text())
            data["real_provider_enabled_after_d122"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_config_manual_enable_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
