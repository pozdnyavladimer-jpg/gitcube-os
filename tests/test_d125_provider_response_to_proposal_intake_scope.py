
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.provider_response_to_proposal_intake_scope import create_provider_response_to_proposal_intake_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD125ProviderResponseToProposalIntakeScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        ping_id = "d124-test"
        config_id = "d123-test"
        dashboard_id = "d122-test"
        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        d124 = {
            "ok": True,
            "decision": "REAL_PROVIDER_DRY_PING_SCOPE_READY",
            "ping_id": ping_id,
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
                "real_provider_dry_ping_scope_only": True,
                "request_shape_probe_only": True,
                "response_shape_probe_only": True,
                "real_provider_called_now": False,
                "approval_for_d125_intake_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "provider_ping_status": "DRY_SHAPE_PROBE_ONLY",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "approval_scope": "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_ONLY",
                "next_step": "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE",
            },
        }

        request_probe = {
            "ok": True,
            "ping_id": ping_id,
            "probe_mode": "REQUEST_SHAPE_ONLY_NO_NETWORK",
            "dry_ping_only": True,
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
        }

        response_probe = {
            "ok": True,
            "ping_id": ping_id,
            "probe_mode": "MOCK_RESPONSE_SHAPE_ONLY_NO_PROVIDER_CALL",
            "dry_ping_only": True,
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "response_valid_shape": True,
            "response_shape": {
                "proposal_id": "d124-shape-probe-proposal",
                "proposal_type": "analysis_proposal",
                "intent": "Verify proposal intake.",
                "target_scope": "reports/",
                "candidate_files": [],
                "risk_flags": [],
                "guardrails": {
                    "propose_only": True,
                    "requires_human_review": True,
                    "no_secret_values": True,
                    "no_network_side_effects": True,
                    "no_apply_side_effects": True,
                    "no_git_side_effects": True,
                },
                "validation_plan": ["schema validation"],
                "requires_human_review": True,
            },
        }

        d125_scope = {
            "ok": True,
            "ping_id": ping_id,
            "allowed_next_gate": "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE",
            "provider_response_intake_scope_only": True,
            "human_review_required": True,
            "real_provider_call_executed_after_d124": False,
            "network_call_executed_after_d124": False,
            "api_key_read_after_d124": False,
            "real_apply_allowed_after_d124_by_ai": False,
            "route_insert_allowed_after_d124_by_ai": False,
            "protected_core_mutation_allowed_after_d124_by_ai": False,
        }

        write(root / "reports/d124_real_provider_dry_ping_scope.json", d124)
        write(root / "reports/d124_provider_request_shape_probe.json", request_probe)
        write(root / "reports/d124_provider_response_shape_probe.json", response_probe)
        write(root / "reports/d124_d125_provider_response_to_proposal_intake_scope.json", d125_scope)

        return td, root

    def test_creates_intake_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_provider_response_to_proposal_intake_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_READY")
            self.assertEqual(r["summary"]["intake_status"], "PROPOSAL_SHAPE_ACCEPTED")
            self.assertEqual(r["summary"]["approval_scope"], "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["api_key_read"])
            self.assertFalse(r["guardrails"]["secret_read"])
            self.assertEqual(r["d126_scope"]["allowed_next_gate"], "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE")
            self.assertTrue((root / "reports/d125_provider_response_to_proposal_intake_scope.json").exists())
            self.assertTrue((root / "reports/d125_provider_response_schema_validator.json").exists())
            self.assertTrue((root / "reports/d125_provider_intake_rejection_report.json").exists())
            self.assertTrue((root / "reports/d125_d126_proposal_to_sandbox_candidate_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d124(self):
        td, root = self.root()
        try:
            (root / "reports/d124_real_provider_dry_ping_scope.json").unlink()
            r = create_provider_response_to_proposal_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_response_missing_required_field(self):
        td, root = self.root()
        try:
            p = root / "reports/d124_provider_response_shape_probe.json"
            data = json.loads(p.read_text())
            del data["response_shape"]["proposal_id"]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_response_to_proposal_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_candidate_file_targets_blocked_prefix(self):
        td, root = self.root()
        try:
            p = root / "reports/d124_provider_response_shape_probe.json"
            data = json.loads(p.read_text())
            data["response_shape"]["candidate_files"] = [{"path": "core/unsafe.py"}]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_response_to_proposal_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d125_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d124_d125_provider_response_to_proposal_intake_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d124_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_response_to_proposal_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
