
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.dry_run_apply_scope import create_dry_run_apply_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD112DryRunApplyScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        approval_id = "d111-test"

        d111 = {
            "ok": True,
            "decision": "EXPLICIT_APPROVAL_GATE_READY",
            "approval_id": approval_id,
            "gate_id": "d110-test",
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
                "rollback_executed": False,
                "restore_executed": False,
                "explicit_approval_gate_only": True,
                "approval_for_d112_dry_run_only": True,
                "approval_for_real_apply": False,
                "candidate_execution_allowed": False,
            },
            "summary": {
                "approval_scope": "D112_DRY_RUN_APPLY_SCOPE_ONLY",
                "next_step": "D112_DRY_RUN_APPLY_SCOPE",
            },
        }

        approval_statement = {
            "ok": True,
            "approval_id": approval_id,
            "approval_scope": "D112_DRY_RUN_APPLY_SCOPE_ONLY",
            "approval_for_real_apply": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        operator_decision = {
            "ok": True,
            "approval_id": approval_id,
            "decision": "APPROVED_FOR_D112_DRY_RUN_SCOPE_ONLY",
            "operator_phrase_matched": True,
            "approval_for_real_apply": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
        }

        d112_scope = {
            "ok": True,
            "approval_id": approval_id,
            "allowed_next_gate": "D112_DRY_RUN_APPLY_SCOPE",
            "dry_run_only": True,
            "human_review_required": True,
            "actual_apply_allowed_after_d111": False,
            "route_insert_allowed_after_d111": False,
            "protected_core_mutation_allowed_after_d111": False,
            "sandbox_candidate_execution_allowed_after_d111": False,
        }

        review_summary = {
            "ok": True,
            "proposal_id": proposal_id,
            "target_scope": "runtime_experimental/ai_sandbox_work/",
            "candidate_files": ["runtime_experimental/ai_sandbox_work/proposal_manifest.json"],
        }

        write(root / "reports/d111_explicit_approval_gate.json", d111)
        write(root / "reports/d111_explicit_approval_statement.json", approval_statement)
        write(root / "reports/d111_operator_decision_record.json", operator_decision)
        write(root / "reports/d111_d112_dry_run_apply_scope.json", d112_scope)
        write(root / "reports/d110_proposal_review_summary.json", review_summary)

        return td, root

    def test_creates_dry_run_outputs(self):
        td, root = self.root()
        try:
            r = create_dry_run_apply_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "DRY_RUN_APPLY_SCOPE_READY")
            self.assertTrue(r["summary"]["dry_run_only"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["patch_applied"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["d113_scope"]["allowed_next_gate"], "D113_FINAL_APPLY_REVIEW_SCOPE")
            self.assertTrue((root / "reports/d112_dry_run_apply_scope.json").exists())
            self.assertTrue((root / "reports/d112_dry_run_plan.json").exists())
            self.assertTrue((root / "reports/d112_dry_run_patch_preview.json").exists())
            self.assertTrue((root / "reports/d112_no_touch_verification.json").exists())
            self.assertTrue((root / "reports/d112_d113_final_apply_review_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d111(self):
        td, root = self.root()
        try:
            (root / "reports/d111_explicit_approval_gate.json").unlink()
            r = create_dry_run_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d111_claims_real_apply_approval(self):
        td, root = self.root()
        try:
            p = root / "reports/d111_explicit_approval_gate.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_dry_run_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_operator_phrase_not_matched(self):
        td, root = self.root()
        try:
            p = root / "reports/d111_operator_decision_record.json"
            data = json.loads(p.read_text())
            data["operator_phrase_matched"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_dry_run_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_blocked_candidate_path(self):
        td, root = self.root()
        try:
            p = root / "reports/d110_proposal_review_summary.json"
            data = json.loads(p.read_text())
            data["candidate_files"] = ["core/unsafe.py"]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_dry_run_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
