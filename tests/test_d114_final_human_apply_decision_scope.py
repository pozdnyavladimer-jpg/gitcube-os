
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.final_human_apply_decision_scope import create_final_human_apply_decision_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD114FinalHumanApplyDecisionScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        review_id = "d113-test"
        dry_run_id = "d112-test"

        d113 = {
            "ok": True,
            "decision": "FINAL_APPLY_REVIEW_SCOPE_READY",
            "review_id": review_id,
            "dry_run_id": dry_run_id,
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
                "final_apply_review_only": True,
                "approval_for_real_apply": False,
                "candidate_execution_allowed": False,
            },
            "summary": {
                "real_apply_current_status": "BLOCKED",
                "next_step": "D114_FINAL_HUMAN_APPLY_DECISION_SCOPE",
            },
        }

        evidence = {
            "ok": True,
            "review_id": review_id,
            "dry_run_id": dry_run_id,
            "proposal_id": proposal_id,
            "review_mode": "FINAL_APPLY_REVIEW_ONLY",
            "evidence_files": {
                "d112_report": "reports/d112_dry_run_apply_scope.json",
            },
            "dry_run_summary": {
                "dry_run_only": True,
                "candidate_files": ["runtime_experimental/ai_sandbox_work/proposal_manifest.json"],
                "patch_generated": False,
                "patch_applied": False,
                "files_mutated": [],
                "safe_to_prepare_d113": True,
            },
            "actual_apply_executed": False,
            "candidate_executed": False,
            "approval_for_real_apply": False,
        }

        blocker_matrix = {
            "ok": True,
            "review_id": review_id,
            "real_apply_current_status": "BLOCKED",
            "blocked_until": "D114_FINAL_HUMAN_APPLY_DECISION_SCOPE",
            "blockers": {
                "no_d114_final_human_apply_decision": True,
                "no_d115_final_apply_phrase": True,
            },
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

        d114_scope = {
            "ok": True,
            "review_id": review_id,
            "dry_run_id": dry_run_id,
            "proposal_id": proposal_id,
            "allowed_next_gate": "D114_FINAL_HUMAN_APPLY_DECISION_SCOPE",
            "final_human_decision_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d113": False,
            "route_insert_allowed_after_d113": False,
            "protected_core_mutation_allowed_after_d113": False,
            "sandbox_candidate_execution_allowed_after_d113": False,
        }

        write(root / "reports/d113_final_apply_review_scope.json", d113)
        write(root / "reports/d113_final_apply_evidence_packet.json", evidence)
        write(root / "reports/d113_final_apply_blocker_matrix.json", blocker_matrix)
        write(root / "reports/d113_d114_final_human_apply_decision_scope.json", d114_scope)

        return td, root

    def test_creates_final_human_decision_outputs(self):
        td, root = self.root()
        try:
            r = create_final_human_apply_decision_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "FINAL_HUMAN_APPLY_DECISION_SCOPE_READY")
            self.assertEqual(r["summary"]["real_apply_current_status"], "BLOCKED")
            self.assertEqual(r["summary"]["approval_scope"], "D115_FINAL_APPLY_PHRASE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["d115_scope"]["allowed_next_gate"], "D115_FINAL_APPLY_PHRASE_SCOPE")
            self.assertTrue((root / "reports/d114_final_human_apply_decision_scope.json").exists())
            self.assertTrue((root / "reports/d114_final_apply_permission_matrix.json").exists())
            self.assertTrue((root / "reports/d114_final_operator_decision_statement.json").exists())
            self.assertTrue((root / "reports/d114_d115_final_apply_phrase_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d113(self):
        td, root = self.root()
        try:
            (root / "reports/d113_final_apply_review_scope.json").unlink()
            r = create_final_human_apply_decision_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d113_claims_real_apply_approval(self):
        td, root = self.root()
        try:
            p = root / "reports/d113_final_apply_review_scope.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_final_human_apply_decision_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_patch_applied(self):
        td, root = self.root()
        try:
            p = root / "reports/d113_final_apply_evidence_packet.json"
            data = json.loads(p.read_text())
            data["dry_run_summary"]["patch_applied"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_final_human_apply_decision_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_blocked_candidate_path(self):
        td, root = self.root()
        try:
            p = root / "reports/d113_final_apply_evidence_packet.json"
            data = json.loads(p.read_text())
            data["dry_run_summary"]["candidate_files"] = ["core/unsafe.py"]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_final_human_apply_decision_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
