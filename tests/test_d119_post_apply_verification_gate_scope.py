
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.post_apply_verification_gate_scope import create_post_apply_verification_gate_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD119PostApplyVerificationGateScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        evidence_id = "d118-test"

        d118 = {
            "ok": True,
            "decision": "OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_READY",
            "evidence_id": evidence_id,
            "review_id": "d117-test",
            "window_id": "d116-test",
            "phrase_id": "d115-test",
            "decision_id": "d114-test",
            "dry_run_id": "d112-test",
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
                "operator_local_evidence_scope_only": True,
                "evidence_template_only": True,
                "approval_for_d119_verification_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "real_apply_by_ai_status": "BLOCKED",
                "approval_scope": "D119_POST_APPLY_VERIFICATION_GATE_SCOPE_ONLY",
                "next_step": "D119_POST_APPLY_VERIFICATION_GATE_SCOPE",
            },
        }

        log_template = {
            "ok": True,
            "evidence_id": evidence_id,
            "template_mode": "HUMAN_LOCAL_EVIDENCE_TEMPLATE_ONLY",
            "shell_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "candidate_executed_by_ai": False,
        }

        result_capture = {
            "ok": True,
            "evidence_id": evidence_id,
            "capture_status": "AWAITING_OPERATOR_LOCAL_EVIDENCE",
            "operator_local_execution_claimed": False,
            "operator_local_execution_evidence_present": False,
            "commands_run": [],
            "exit_codes": {},
            "tests_summary": "not captured yet",
            "working_tree_before": "not captured yet",
            "working_tree_after": "not captured yet",
            "ai_executed_commands": False,
            "shell_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "candidate_executed_by_ai": False,
            "ready_for_d119_verification_scope": True,
        }

        d119_scope = {
            "ok": True,
            "evidence_id": evidence_id,
            "allowed_next_gate": "D119_POST_APPLY_VERIFICATION_GATE_SCOPE",
            "post_apply_verification_scope_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d118_by_ai": False,
            "route_insert_allowed_after_d118_by_ai": False,
            "protected_core_mutation_allowed_after_d118_by_ai": False,
            "sandbox_candidate_execution_allowed_after_d118_by_ai": False,
        }

        write(root / "reports/d118_operator_local_execution_evidence_scope.json", d118)
        write(root / "reports/d118_operator_local_execution_log_template.json", log_template)
        write(root / "reports/d118_operator_local_result_capture.json", result_capture)
        write(root / "reports/d118_d119_post_apply_verification_gate_scope.json", d119_scope)

        return td, root

    def test_creates_verification_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_post_apply_verification_gate_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "POST_APPLY_VERIFICATION_GATE_SCOPE_READY")
            self.assertEqual(r["summary"]["real_apply_by_ai_status"], "BLOCKED")
            self.assertEqual(r["summary"]["approval_scope"], "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["commands_executed_by_ai"])
            self.assertEqual(r["d120_scope"]["allowed_next_gate"], "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE")
            self.assertTrue((root / "reports/d119_post_apply_verification_gate_scope.json").exists())
            self.assertTrue((root / "reports/d119_post_apply_test_results_summary.json").exists())
            self.assertTrue((root / "reports/d119_post_apply_git_state_summary.json").exists())
            self.assertTrue((root / "reports/d119_d120_first_controlled_run_seal_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d118(self):
        td, root = self.root()
        try:
            (root / "reports/d118_operator_local_execution_evidence_scope.json").unlink()
            r = create_post_apply_verification_gate_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_ai_executed_commands(self):
        td, root = self.root()
        try:
            p = root / "reports/d118_operator_local_result_capture.json"
            data = json.loads(p.read_text())
            data["ai_executed_commands"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_post_apply_verification_gate_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_scope_allows_apply_by_ai_after_d118(self):
        td, root = self.root()
        try:
            p = root / "reports/d118_d119_post_apply_verification_gate_scope.json"
            data = json.loads(p.read_text())
            data["actual_apply_allowed_after_d118_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_post_apply_verification_gate_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_log_template_claims_apply_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d118_operator_local_execution_log_template.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_post_apply_verification_gate_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
