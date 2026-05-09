
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.operator_local_execution_evidence_scope import create_operator_local_execution_evidence_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD118OperatorLocalExecutionEvidenceScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        review_id = "d117-test"

        d117 = {
            "ok": True,
            "decision": "MANUAL_APPLY_COMMAND_REVIEW_SCOPE_READY",
            "review_id": review_id,
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
                "manual_command_review_only": True,
                "reviewed_command_packet_documentation_only": True,
                "approval_for_d118_evidence_scope_only": True,
                "approval_for_real_apply": False,
                "candidate_execution_allowed": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "real_apply_current_status": "BLOCKED",
                "approval_scope": "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_ONLY",
                "next_step": "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE",
            },
        }

        reviewed_packet = {
            "ok": True,
            "review_id": review_id,
            "review_mode": "COMMAND_REVIEW_ONLY_NOT_EXECUTED",
            "reviewed_commands": [
                "git status --short",
                "python -m unittest discover -s tests -v",
            ],
            "approved_for_d118_evidence_scope_only": True,
            "approved_for_real_apply_now": False,
            "commands_executed_by_ai": False,
            "shell_executed_by_ai": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
        }

        ready_record = {
            "ok": True,
            "review_id": review_id,
            "manual_apply_window_status": "READY_FOR_D118_EVIDENCE_SCOPE_ONLY",
            "real_apply_current_status": "BLOCKED",
            "ready_for": "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE",
            "actual_apply_executed": False,
            "candidate_executed": False,
            "approval_for_real_apply": False,
            "commands_executed_by_ai": False,
        }

        d118_scope = {
            "ok": True,
            "review_id": review_id,
            "allowed_next_gate": "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE",
            "operator_local_evidence_scope_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d117_by_ai": False,
            "route_insert_allowed_after_d117_by_ai": False,
            "protected_core_mutation_allowed_after_d117_by_ai": False,
            "sandbox_candidate_execution_allowed_after_d117_by_ai": False,
        }

        write(root / "reports/d117_manual_apply_command_review_scope.json", d117)
        write(root / "reports/d117_reviewed_operator_command_packet.json", reviewed_packet)
        write(root / "reports/d117_manual_apply_ready_or_blocked_record.json", ready_record)
        write(root / "reports/d117_d118_operator_local_execution_evidence_scope.json", d118_scope)

        return td, root

    def test_creates_evidence_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_operator_local_execution_evidence_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_READY")
            self.assertEqual(r["summary"]["real_apply_by_ai_status"], "BLOCKED")
            self.assertEqual(r["summary"]["approval_scope"], "D119_POST_APPLY_VERIFICATION_GATE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["commands_executed_by_ai"])
            self.assertEqual(r["d119_scope"]["allowed_next_gate"], "D119_POST_APPLY_VERIFICATION_GATE_SCOPE")
            self.assertTrue((root / "reports/d118_operator_local_execution_evidence_scope.json").exists())
            self.assertTrue((root / "reports/d118_operator_local_execution_log_template.json").exists())
            self.assertTrue((root / "reports/d118_operator_local_result_capture.json").exists())
            self.assertTrue((root / "reports/d118_d119_post_apply_verification_gate_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d117(self):
        td, root = self.root()
        try:
            (root / "reports/d117_manual_apply_command_review_scope.json").unlink()
            r = create_operator_local_execution_evidence_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_reviewed_packet_executed_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d117_reviewed_operator_command_packet.json"
            data = json.loads(p.read_text())
            data["commands_executed_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_operator_local_execution_evidence_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_ready_record_claims_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d117_manual_apply_ready_or_blocked_record.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_operator_local_execution_evidence_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_scope_allows_apply_by_ai_after_d117(self):
        td, root = self.root()
        try:
            p = root / "reports/d117_d118_operator_local_execution_evidence_scope.json"
            data = json.loads(p.read_text())
            data["actual_apply_allowed_after_d117_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_operator_local_execution_evidence_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
