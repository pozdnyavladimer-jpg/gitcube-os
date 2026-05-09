
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.first_controlled_run_seal_scope import create_first_controlled_run_seal_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD120FirstControlledRunSealScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        verification_id = "d119-test"

        d119 = {
            "ok": True,
            "decision": "POST_APPLY_VERIFICATION_GATE_SCOPE_READY",
            "verification_id": verification_id,
            "evidence_id": "d118-test",
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
                "post_apply_verification_scope_only": True,
                "verification_template_only": True,
                "approval_for_d120_seal_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "real_apply_by_ai_status": "BLOCKED",
                "approval_scope": "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE_ONLY",
                "next_step": "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE",
            },
        }

        test_results = {
            "ok": True,
            "verification_id": verification_id,
            "summary_mode": "VERIFICATION_SCOPE_ONLY_NOT_EXECUTED",
            "tests_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "candidate_executed_by_ai": False,
        }

        git_state = {
            "ok": True,
            "verification_id": verification_id,
            "summary_mode": "GIT_STATE_SUMMARY_TEMPLATE_ONLY",
            "git_commands_executed_by_ai": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated_by_ai": False,
        }

        d120_scope = {
            "ok": True,
            "verification_id": verification_id,
            "allowed_next_gate": "D120_FIRST_CONTROLLED_RUN_SEAL_SCOPE",
            "first_controlled_run_seal_scope_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d119_by_ai": False,
            "route_insert_allowed_after_d119_by_ai": False,
            "protected_core_mutation_allowed_after_d119_by_ai": False,
            "sandbox_candidate_execution_allowed_after_d119_by_ai": False,
        }

        write(root / "reports/d119_post_apply_verification_gate_scope.json", d119)
        write(root / "reports/d119_post_apply_test_results_summary.json", test_results)
        write(root / "reports/d119_post_apply_git_state_summary.json", git_state)
        write(root / "reports/d119_d120_first_controlled_run_seal_scope.json", d120_scope)

        return td, root

    def test_creates_first_controlled_run_seal_outputs(self):
        td, root = self.root()
        try:
            r = create_first_controlled_run_seal_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "FIRST_CONTROLLED_RUN_SEAL_SCOPE_READY")
            self.assertEqual(r["summary"]["sealed_range"], "D106-D120")
            self.assertEqual(r["summary"]["first_controlled_run_status"], "SEALED")
            self.assertEqual(r["summary"]["recommended_next_track"], "D121_AI_PROPOSE_ONLY_PROVIDER_ADAPTER")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["git_push_by_ai"])
            self.assertTrue(r["final_chain_integrity_summary"]["ok"])
            self.assertFalse(r["first_run_release_tag_plan"]["tag_created_by_ai"])
            self.assertTrue((root / "reports/d120_first_controlled_run_seal_scope.json").exists())
            self.assertTrue((root / "reports/d120_guarded_autonomy_run_ledger.json").exists())
            self.assertTrue((root / "reports/d120_final_chain_integrity_summary.json").exists())
            self.assertTrue((root / "reports/d120_first_run_release_tag_plan.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d119(self):
        td, root = self.root()
        try:
            (root / "reports/d119_post_apply_verification_gate_scope.json").unlink()
            r = create_first_controlled_run_seal_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_git_state_claims_ai_commit(self):
        td, root = self.root()
        try:
            p = root / "reports/d119_post_apply_git_state_summary.json"
            data = json.loads(p.read_text())
            data["git_commit_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_first_controlled_run_seal_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d119_claims_apply_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d119_post_apply_verification_gate_scope.json"
            data = json.loads(p.read_text())
            data["guardrails"]["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_first_controlled_run_seal_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_scope_allows_apply_by_ai_after_d119(self):
        td, root = self.root()
        try:
            p = root / "reports/d119_d120_first_controlled_run_seal_scope.json"
            data = json.loads(p.read_text())
            data["actual_apply_allowed_after_d119_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_first_controlled_run_seal_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
