
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.manual_apply_command_review_scope import create_manual_apply_command_review_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD117ManualApplyCommandReviewScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        window_id = "d116-test"

        d116 = {
            "ok": True,
            "decision": "MANUAL_APPLY_WINDOW_SCOPE_READY",
            "window_id": window_id,
            "phrase_id": "d115-test",
            "decision_id": "d114-test",
            "review_id": "d113-test",
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
                "manual_apply_window_scope_only": True,
                "operator_command_packet_documentation_only": True,
                "approval_for_d117_command_review_only": True,
                "approval_for_real_apply": False,
                "candidate_execution_allowed": False,
            },
            "summary": {
                "real_apply_current_status": "BLOCKED",
                "approval_scope": "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE_ONLY",
                "next_step": "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE",
            },
        }

        preflight = {
            "ok": True,
            "window_id": window_id,
            "manual_window_mode": "LOCAL_OPERATOR_REVIEW_ONLY",
            "lock_state": "REAL_APPLY_STILL_LOCKED",
            "must_remain_false": {
                "actual_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "external_ai_called": False,
                "network_accessed": False,
                "candidate_executed": False,
                "git_commit_by_ai": False,
                "git_push_by_ai": False,
            },
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        command_packet = {
            "ok": True,
            "window_id": window_id,
            "packet_mode": "DOCUMENTATION_ONLY_NOT_EXECUTED",
            "commands_are_not_executed_by_ai": True,
            "human_may_run_manually_after_d117": True,
            "commands": [
                "git status --short",
                "python -m unittest discover -s tests -v",
                "python -m py_compile runtime_experimental/*.py",
            ],
            "blocked_commands": [
                "git apply",
                "git commit",
                "git push",
                "route insert",
                "execute sandbox candidate",
            ],
            "real_apply_command_included": False,
            "shell_executed_by_ai": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        d117_scope = {
            "ok": True,
            "window_id": window_id,
            "allowed_next_gate": "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE",
            "manual_command_review_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d116": False,
            "route_insert_allowed_after_d116": False,
            "protected_core_mutation_allowed_after_d116": False,
            "sandbox_candidate_execution_allowed_after_d116": False,
        }

        write(root / "reports/d116_manual_apply_window_scope.json", d116)
        write(root / "reports/d116_manual_apply_preflight_checklist.json", preflight)
        write(root / "reports/d116_operator_local_command_packet.json", command_packet)
        write(root / "reports/d116_d117_manual_apply_command_review_scope.json", d117_scope)

        return td, root

    def test_creates_command_review_outputs(self):
        td, root = self.root()
        try:
            r = create_manual_apply_command_review_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "MANUAL_APPLY_COMMAND_REVIEW_SCOPE_READY")
            self.assertEqual(r["summary"]["real_apply_current_status"], "BLOCKED")
            self.assertEqual(r["summary"]["approval_scope"], "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertFalse(r["guardrails"]["commands_executed_by_ai"])
            self.assertEqual(r["d118_scope"]["allowed_next_gate"], "D118_OPERATOR_LOCAL_EXECUTION_EVIDENCE_SCOPE")
            self.assertTrue((root / "reports/d117_manual_apply_command_review_scope.json").exists())
            self.assertTrue((root / "reports/d117_reviewed_operator_command_packet.json").exists())
            self.assertTrue((root / "reports/d117_manual_apply_ready_or_blocked_record.json").exists())
            self.assertTrue((root / "reports/d117_d118_operator_local_execution_evidence_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d116(self):
        td, root = self.root()
        try:
            (root / "reports/d116_manual_apply_window_scope.json").unlink()
            r = create_manual_apply_command_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_command_packet_executed_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d116_operator_local_command_packet.json"
            data = json.loads(p.read_text())
            data["shell_executed_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_manual_apply_command_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_real_apply_command_included(self):
        td, root = self.root()
        try:
            p = root / "reports/d116_operator_local_command_packet.json"
            data = json.loads(p.read_text())
            data["real_apply_command_included"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_manual_apply_command_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_scope_allows_apply_after_d116(self):
        td, root = self.root()
        try:
            p = root / "reports/d116_d117_manual_apply_command_review_scope.json"
            data = json.loads(p.read_text())
            data["actual_apply_allowed_after_d116"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_manual_apply_command_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
