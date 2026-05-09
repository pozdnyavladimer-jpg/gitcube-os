
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.final_apply_review_scope import create_final_apply_review_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD113FinalApplyReviewScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        dry_run_id = "d112-test"

        d112 = {
            "ok": True,
            "decision": "DRY_RUN_APPLY_SCOPE_READY",
            "dry_run_id": dry_run_id,
            "approval_id": "d111-test",
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
                "dry_run_only": True,
                "patch_generated": False,
                "patch_applied": False,
                "candidate_execution_allowed": False,
                "approval_for_real_apply": False,
            },
            "summary": {
                "dry_run_only": True,
                "next_step": "D113_FINAL_APPLY_REVIEW_SCOPE",
            },
        }

        plan = {
            "ok": True,
            "dry_run_id": dry_run_id,
            "proposal_id": proposal_id,
            "dry_run_only": True,
            "candidate_files": ["runtime_experimental/ai_sandbox_work/proposal_manifest.json"],
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        patch_preview = {
            "ok": True,
            "dry_run_id": dry_run_id,
            "dry_run_only": True,
            "candidate_files_preview": plan["candidate_files"],
            "blocked_path_hits": [],
            "patch_generated": False,
            "patch_applied": False,
            "files_mutated": [],
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        no_touch = {
            "ok": True,
            "dry_run_id": dry_run_id,
            "safe_to_prepare_d113": True,
            "blocked_path_hits": [],
            "verified_false": {
                "actual_apply_executed": False,
                "candidate_executed": False,
                "patch_applied": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "external_ai_called": False,
                "network_accessed": False,
                "git_commit_by_ai": False,
                "git_push_by_ai": False,
            },
        }

        d113_scope = {
            "ok": True,
            "dry_run_id": dry_run_id,
            "allowed_next_gate": "D113_FINAL_APPLY_REVIEW_SCOPE",
            "final_apply_review_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d112": False,
            "route_insert_allowed_after_d112": False,
            "protected_core_mutation_allowed_after_d112": False,
            "sandbox_candidate_execution_allowed_after_d112": False,
        }

        write(root / "reports/d112_dry_run_apply_scope.json", d112)
        write(root / "reports/d112_dry_run_plan.json", plan)
        write(root / "reports/d112_dry_run_patch_preview.json", patch_preview)
        write(root / "reports/d112_no_touch_verification.json", no_touch)
        write(root / "reports/d112_d113_final_apply_review_scope.json", d113_scope)

        return td, root

    def test_creates_final_review_outputs(self):
        td, root = self.root()
        try:
            r = create_final_apply_review_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "FINAL_APPLY_REVIEW_SCOPE_READY")
            self.assertEqual(r["summary"]["real_apply_current_status"], "BLOCKED")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["d114_scope"]["allowed_next_gate"], "D114_FINAL_HUMAN_APPLY_DECISION_SCOPE")
            self.assertTrue((root / "reports/d113_final_apply_review_scope.json").exists())
            self.assertTrue((root / "reports/d113_final_apply_evidence_packet.json").exists())
            self.assertTrue((root / "reports/d113_final_apply_blocker_matrix.json").exists())
            self.assertTrue((root / "reports/d113_d114_final_human_apply_decision_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d112(self):
        td, root = self.root()
        try:
            (root / "reports/d112_dry_run_apply_scope.json").unlink()
            r = create_final_apply_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_patch_applied(self):
        td, root = self.root()
        try:
            p = root / "reports/d112_dry_run_patch_preview.json"
            data = json.loads(p.read_text())
            data["patch_applied"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_final_apply_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_no_touch_failed(self):
        td, root = self.root()
        try:
            p = root / "reports/d112_no_touch_verification.json"
            data = json.loads(p.read_text())
            data["ok"] = False
            data["safe_to_prepare_d113"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_final_apply_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_blocked_candidate_path(self):
        td, root = self.root()
        try:
            p = root / "reports/d112_dry_run_plan.json"
            data = json.loads(p.read_text())
            data["candidate_files"] = ["core/unsafe.py"]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_final_apply_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
