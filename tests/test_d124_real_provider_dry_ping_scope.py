
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.real_provider_dry_ping_scope import create_real_provider_dry_ping_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD124RealProviderDryPingScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        config_id = "d123-test"
        dashboard_id = "d122-test"
        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        d123 = {
            "ok": True,
            "decision": "PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_READY",
            "config_id": config_id,
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
                "provider_config_manual_enable_scope_only": True,
                "placeholder_policy_only": True,
                "network_allowlist_dry_plan_only": True,
                "real_provider_enabled_now": False,
                "real_provider_called_now": False,
                "approval_for_d124_dry_ping_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "provider_config_status": "PLACEHOLDER_ONLY",
                "real_provider_status": "DISABLED",
                "network_status": "DRY_PLAN_ONLY",
                "secret_status": "PLACEHOLDER_ONLY_NOT_READ",
                "approval_scope": "D124_REAL_PROVIDER_DRY_PING_SCOPE_ONLY",
                "next_step": "D124_REAL_PROVIDER_DRY_PING_SCOPE",
            },
        }

        secret_policy = {
            "ok": True,
            "config_id": config_id,
            "policy_mode": "PLACEHOLDER_ONLY_NO_SECRET_READ",
            "secret_read_now": False,
            "api_key_read_now": False,
            "real_provider_enabled_now": False,
        }

        network_plan = {
            "ok": True,
            "config_id": config_id,
            "plan_mode": "DRY_PLAN_ONLY_NO_NETWORK",
            "network_accessed_now": False,
            "real_provider_call_now": False,
            "allowlist_enabled_now": False,
        }

        d124_scope = {
            "ok": True,
            "config_id": config_id,
            "allowed_next_gate": "D124_REAL_PROVIDER_DRY_PING_SCOPE",
            "real_provider_dry_ping_scope_only": True,
            "human_review_required": True,
            "real_provider_enabled_after_d123": False,
            "network_call_executed_after_d123": False,
            "api_key_read_after_d123": False,
            "real_apply_allowed_after_d123_by_ai": False,
            "route_insert_allowed_after_d123_by_ai": False,
            "protected_core_mutation_allowed_after_d123_by_ai": False,
        }

        write(root / "reports/d123_provider_config_manual_enable_scope.json", d123)
        write(root / "reports/d123_provider_secret_placeholder_policy.json", secret_policy)
        write(root / "reports/d123_network_allowlist_dry_plan.json", network_plan)
        write(root / "reports/d123_d124_real_provider_dry_ping_scope.json", d124_scope)

        return td, root

    def test_creates_dry_ping_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_real_provider_dry_ping_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "REAL_PROVIDER_DRY_PING_SCOPE_READY")
            self.assertEqual(r["summary"]["provider_ping_status"], "DRY_SHAPE_PROBE_ONLY")
            self.assertEqual(r["summary"]["real_provider_status"], "NOT_CALLED")
            self.assertEqual(r["summary"]["approval_scope"], "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["api_key_read"])
            self.assertFalse(r["guardrails"]["secret_read"])
            self.assertEqual(r["d125_scope"]["allowed_next_gate"], "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE")
            self.assertTrue((root / "reports/d124_real_provider_dry_ping_scope.json").exists())
            self.assertTrue((root / "reports/d124_provider_request_shape_probe.json").exists())
            self.assertTrue((root / "reports/d124_provider_response_shape_probe.json").exists())
            self.assertTrue((root / "reports/d124_d125_provider_response_to_proposal_intake_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d123(self):
        td, root = self.root()
        try:
            (root / "reports/d123_provider_config_manual_enable_scope.json").unlink()
            r = create_real_provider_dry_ping_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_secret_policy_reads_secret(self):
        td, root = self.root()
        try:
            p = root / "reports/d123_provider_secret_placeholder_policy.json"
            data = json.loads(p.read_text())
            data["secret_read_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_real_provider_dry_ping_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_network_plan_called_provider(self):
        td, root = self.root()
        try:
            p = root / "reports/d123_network_allowlist_dry_plan.json"
            data = json.loads(p.read_text())
            data["real_provider_call_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_real_provider_dry_ping_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d124_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d123_d124_real_provider_dry_ping_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d123_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_real_provider_dry_ping_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
