
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.post_execution_verifier import create_post_execution_verifier


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD102PostExecutionVerifier(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d101_one_shot_manual_execution_capsule.json", {
            "ok": True,
            "decision": "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_READY",
            "capsule_id": "d101-test",
            "decision_id": "d100-test",
            "source_capsule_id": "d99-test",
            "pack_id": "d98-test",
            "regression_id": "d96-test",
            "one_shot_manual_execution_capsule": {
                "ok": True,
                "mode": "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_PREVIEW_ONLY",
                "manual_only": True,
                "ai_execution_allowed": False,
                "real_apply_allowed_now": False,
                "route_insert_allowed_now": False,
                "protected_core_mutation_allowed_now": False,
                "next_required_gate": "D102_POST_EXECUTION_VERIFIER",
            },
            "guardrails": {
                "external_ai_called": False,
                "network_accessed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
                "rollback_executed": False,
                "restore_executed": False,
                "manual_capsule_preview_only": True,
                "human_manual_only": True,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d101_manual_command_preview.json", {
            "ok": True,
            "capsule_id": "d101-test",
            "decision_id": "d100-test",
            "commands_are_preview_only": True,
            "commands_must_be_run_by_human_only": True,
            "ai_must_not_execute": True,
        })

        write(root / "reports/d101_post_execution_required_checks.json", {
            "ok": True,
            "capsule_id": "d101-test",
            "must_remain_false_until_later_gate": {
                "ai_executed_apply": False,
                "ai_inserted_route": False,
                "ai_committed_or_pushed": False,
                "external_ai_called_for_execution": False,
            },
        })

        write(root / "reports/d101_abort_on_mismatch_policy.json", {
            "ok": True,
            "capsule_id": "d101-test",
            "abort_action": "STOP_AND_REQUEST_HUMAN_REVIEW",
            "rollback_not_executed_here": True,
        })

        write(root / "reports/d101_d102_post_execution_verifier_scope.json", {
            "ok": True,
            "capsule_id": "d101-test",
            "decision_id": "d100-test",
            "allowed_next_gate": "D102_POST_EXECUTION_VERIFIER",
            "d102_allowed_to_create": [
                "post_execution_verifier",
                "post_execution_evidence_report",
                "changed_files_manifest",
                "execution_integrity_summary",
            ],
            "d102_must_not_execute": [
                "actual_apply_by_ai",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "external_ai_network_execution",
                "git_commit_or_push_by_ai",
                "execute_rollback_by_ai",
                "delete_runtime_candidate_by_ai",
                "run_manual_apply_now",
                "execute_post_fix_mutation",
            ],
            "apply_allowed_after_d101": False,
            "route_insert_allowed_after_d101": False,
            "protected_core_mutation_allowed_after_d101": False,
            "required_phrase_for_later_gate": "APPROVE_D102_POST_EXECUTION_VERIFIER_ONLY",
        })

        return td, root

    def test_creates_post_execution_verifier_only(self):
        td, root = self.root()
        try:
            r = create_post_execution_verifier(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "POST_EXECUTION_VERIFIER_READY")
            self.assertTrue(r["guardrails"]["post_execution_verifier_only"])
            self.assertFalse(r["guardrails"]["manual_execution_performed"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["post_execution_verifier"]["next_required_gate"], "D103_ROLLBACK_EVIDENCE_BUILDER")
            self.assertTrue(r["execution_integrity_summary"]["ready_for_d103"])
            self.assertTrue((root / "reports/d102_post_execution_verifier.json").exists())
            self.assertTrue((root / "reports/d102_post_execution_evidence_report.json").exists())
            self.assertTrue((root / "reports/d102_changed_files_manifest.json").exists())
            self.assertTrue((root / "reports/d102_execution_integrity_summary.json").exists())
            self.assertTrue((root / "reports/d102_d103_rollback_evidence_builder_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d101(self):
        td, root = self.root()
        try:
            (root / "reports/d101_one_shot_manual_execution_capsule.json").unlink()
            r = create_post_execution_verifier(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "POST_EXECUTION_VERIFIER_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d101_one_shot_manual_execution_capsule.json"
            data = json.loads(p.read_text())
            data["guardrails"]["actual_apply_executed"] = True
            p.write_text(json.dumps(data))
            r = create_post_execution_verifier(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
