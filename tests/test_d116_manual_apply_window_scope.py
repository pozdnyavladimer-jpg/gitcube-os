
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.manual_apply_window_scope import create_manual_apply_window_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD116ManualApplyWindowScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        phrase_id = "d115-test"

        d115 = {
            "ok": True,
            "decision": "FINAL_APPLY_PHRASE_SCOPE_READY",
            "phrase_id": phrase_id,
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
                "final_phrase_scope_only": True,
                "approval_for_d116_manual_window_only": True,
                "approval_for_real_apply": False,
                "candidate_execution_allowed": False,
            },
            "summary": {
                "real_apply_current_status": "BLOCKED",
                "approval_scope": "D116_MANUAL_APPLY_WINDOW_SCOPE_ONLY",
                "next_step": "D116_MANUAL_APPLY_WINDOW_SCOPE",
            },
        }

        phrase_statement = {
            "ok": True,
            "phrase_id": phrase_id,
            "phrase_scope": "D116_MANUAL_APPLY_WINDOW_SCOPE_ONLY",
            "required_phrase": "APPROVE_D116_MANUAL_APPLY_WINDOW_SCOPE_ONLY",
            "real_apply_approved_now": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        pre_apply_lock = {
            "ok": True,
            "phrase_id": phrase_id,
            "lock_state": "REAL_APPLY_STILL_LOCKED",
            "real_apply_permission": "NOT_GRANTED",
            "real_apply_approved_now": False,
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
        }

        d116_scope = {
            "ok": True,
            "phrase_id": phrase_id,
            "allowed_next_gate": "D116_MANUAL_APPLY_WINDOW_SCOPE",
            "manual_apply_window_scope_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d115": False,
            "route_insert_allowed_after_d115": False,
            "protected_core_mutation_allowed_after_d115": False,
            "sandbox_candidate_execution_allowed_after_d115": False,
            "required_phrase_for_later_gate": "APPROVE_D116_MANUAL_APPLY_WINDOW_SCOPE_ONLY",
        }

        write(root / "reports/d115_final_apply_phrase_scope.json", d115)
        write(root / "reports/d115_final_apply_phrase_statement.json", phrase_statement)
        write(root / "reports/d115_final_pre_apply_lock_report.json", pre_apply_lock)
        write(root / "reports/d115_d116_manual_apply_window_scope.json", d116_scope)

        return td, root

    def test_creates_manual_window_outputs(self):
        td, root = self.root()
        try:
            r = create_manual_apply_window_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "MANUAL_APPLY_WINDOW_SCOPE_READY")
            self.assertEqual(r["summary"]["real_apply_current_status"], "BLOCKED")
            self.assertEqual(r["summary"]["approval_scope"], "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["d117_scope"]["allowed_next_gate"], "D117_MANUAL_APPLY_COMMAND_REVIEW_SCOPE")
            self.assertTrue((root / "reports/d116_manual_apply_window_scope.json").exists())
            self.assertTrue((root / "reports/d116_manual_apply_preflight_checklist.json").exists())
            self.assertTrue((root / "reports/d116_operator_local_command_packet.json").exists())
            self.assertTrue((root / "reports/d116_d117_manual_apply_command_review_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d115(self):
        td, root = self.root()
        try:
            (root / "reports/d115_final_apply_phrase_scope.json").unlink()
            r = create_manual_apply_window_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_real_apply_permission_granted(self):
        td, root = self.root()
        try:
            p = root / "reports/d115_final_pre_apply_lock_report.json"
            data = json.loads(p.read_text())
            data["real_apply_permission"] = "GRANTED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_manual_apply_window_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d115_claims_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d115_final_apply_phrase_scope.json"
            data = json.loads(p.read_text())
            data["guardrails"]["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_manual_apply_window_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_scope_allows_apply_after_d115(self):
        td, root = self.root()
        try:
            p = root / "reports/d115_d116_manual_apply_window_scope.json"
            data = json.loads(p.read_text())
            data["actual_apply_allowed_after_d115"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_manual_apply_window_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
