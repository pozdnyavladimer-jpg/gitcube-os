
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.final_apply_phrase_scope import create_final_apply_phrase_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD115FinalApplyPhraseScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        decision_id = "d114-test"

        d114 = {
            "ok": True,
            "decision": "FINAL_HUMAN_APPLY_DECISION_SCOPE_READY",
            "decision_id": decision_id,
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
                "final_human_decision_only": True,
                "approval_for_d115_phrase_scope_only": True,
                "approval_for_real_apply": False,
                "candidate_execution_allowed": False,
            },
            "summary": {
                "real_apply_current_status": "BLOCKED",
                "approval_scope": "D115_FINAL_APPLY_PHRASE_SCOPE_ONLY",
                "next_step": "D115_FINAL_APPLY_PHRASE_SCOPE",
            },
        }

        permission_matrix = {
            "ok": True,
            "decision_id": decision_id,
            "real_apply_permission": "NOT_GRANTED",
            "d115_phrase_scope_permission": "GRANTED_FOR_PHRASE_SCOPE_ONLY",
            "permissions": {
                "create_d115_final_apply_phrase_scope": True,
                "prepare_final_apply_phrase_text": True,
                "prepare_operator_final_decision_statement": True,
                "real_apply_now": False,
                "auto_apply_now": False,
                "route_insert_now": False,
                "protected_core_mutation_now": False,
                "canonical_memory_overwrite_now": False,
                "external_ai_or_network_call_now": False,
                "sandbox_candidate_execution_now": False,
                "ai_git_commit_or_push_now": False,
            },
        }

        operator_statement = {
            "ok": True,
            "decision_id": decision_id,
            "human_decision_scope": "D115_FINAL_APPLY_PHRASE_SCOPE_ONLY",
            "d115_phrase_scope_approved": True,
            "real_apply_approved_now": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        d115_scope = {
            "ok": True,
            "decision_id": decision_id,
            "allowed_next_gate": "D115_FINAL_APPLY_PHRASE_SCOPE",
            "final_phrase_scope_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d114": False,
            "route_insert_allowed_after_d114": False,
            "protected_core_mutation_allowed_after_d114": False,
            "sandbox_candidate_execution_allowed_after_d114": False,
            "required_phrase_for_later_gate": "APPROVE_D115_FINAL_APPLY_PHRASE_SCOPE_ONLY",
        }

        write(root / "reports/d114_final_human_apply_decision_scope.json", d114)
        write(root / "reports/d114_final_apply_permission_matrix.json", permission_matrix)
        write(root / "reports/d114_final_operator_decision_statement.json", operator_statement)
        write(root / "reports/d114_d115_final_apply_phrase_scope.json", d115_scope)

        return td, root

    def test_creates_final_phrase_outputs(self):
        td, root = self.root()
        try:
            r = create_final_apply_phrase_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "FINAL_APPLY_PHRASE_SCOPE_READY")
            self.assertEqual(r["summary"]["real_apply_current_status"], "BLOCKED")
            self.assertEqual(r["summary"]["approval_scope"], "D116_MANUAL_APPLY_WINDOW_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["d116_scope"]["allowed_next_gate"], "D116_MANUAL_APPLY_WINDOW_SCOPE")
            self.assertTrue((root / "reports/d115_final_apply_phrase_scope.json").exists())
            self.assertTrue((root / "reports/d115_final_apply_phrase_statement.json").exists())
            self.assertTrue((root / "reports/d115_final_pre_apply_lock_report.json").exists())
            self.assertTrue((root / "reports/d115_d116_manual_apply_window_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d114(self):
        td, root = self.root()
        try:
            (root / "reports/d114_final_human_apply_decision_scope.json").unlink()
            r = create_final_apply_phrase_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_real_apply_permission_granted(self):
        td, root = self.root()
        try:
            p = root / "reports/d114_final_apply_permission_matrix.json"
            data = json.loads(p.read_text())
            data["real_apply_permission"] = "GRANTED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_final_apply_phrase_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_operator_claims_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d114_final_operator_decision_statement.json"
            data = json.loads(p.read_text())
            data["real_apply_approved_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_final_apply_phrase_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_scope_allows_apply_after_d114(self):
        td, root = self.root()
        try:
            p = root / "reports/d114_d115_final_apply_phrase_scope.json"
            data = json.loads(p.read_text())
            data["actual_apply_allowed_after_d114"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_final_apply_phrase_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
