
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.ai_propose_only_provider_boundary import (
    create_ai_provider_boundary,
    make_mock_provider_response,
    validate_provider_response,
)


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD106AIProposeOnlyProviderBoundary(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d104_terminal_safety_state.json", {
            "ok": True,
            "ledger_id": "d104-test",
            "builder_id": "d103-test",
            "terminal_decision": "GUARDED_AUTONOMY_PRE_EXECUTION_CHAIN_SEALED",
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
            "ai_autonomous_execution_allowed": False,
            "human_review_required_for_any_future_execution": True,
        })

        write(root / "reports/d105_guarded_autonomy_chain_doc.json", {
            "ok": True,
            "doc_sha256": "abc",
            "main_readme_modified": False,
        })

        return td, root

    def test_creates_boundary_and_contracts(self):
        td, root = self.root()
        try:
            r = create_ai_provider_boundary(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "AI_PROVIDER_BOUNDARY_READY")
            self.assertTrue(r["guardrails"]["mock_provider_only"])
            self.assertTrue(r["guardrails"]["json_only"])
            self.assertTrue(r["guardrails"]["proposal_only"])
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d107_scope"]["allowed_next_gate"], "D107_PROPOSAL_SCHEMA_VALIDATOR")
            self.assertTrue((root / "reports/d106_ai_provider_boundary.json").exists())
            self.assertTrue((root / "reports/d106_provider_input_contract.json").exists())
            self.assertTrue((root / "reports/d106_provider_output_contract.json").exists())
            self.assertTrue((root / "reports/d106_forbidden_action_matrix.json").exists())
            self.assertTrue((root / "reports/d106_d107_proposal_schema_validator_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_if_d104_missing(self):
        td, root = self.root()
        try:
            (root / "reports/d104_terminal_safety_state.json").unlink()
            r = create_ai_provider_boundary(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "AI_PROVIDER_BOUNDARY_BLOCKED")
        finally:
            td.cleanup()

    def test_rejects_forbidden_payload(self):
        payload = make_mock_provider_response("x", "y")
        payload["raw_shell_command"] = "git push"
        errors = validate_provider_response(payload)
        self.assertTrue(errors)

    def test_rejects_blocked_candidate_path(self):
        payload = make_mock_provider_response("x", "y")
        payload["candidate_files"] = ["core/evil.py"]
        errors = validate_provider_response(payload)
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
