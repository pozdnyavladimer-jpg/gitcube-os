
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.one_shot_manual_execution_capsule import create_one_shot_manual_execution_capsule


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD101OneShotManualExecutionCapsule(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d100_controlled_human_execution_decision_request.json", {
            "ok": True,
            "decision": "CONTROLLED_HUMAN_EXECUTION_DECISION_READY",
            "decision_id": "d100-test",
            "capsule_id": "d99-test",
            "pack_id": "d98-test",
            "regression_id": "d96-test",
            "controlled_human_execution_decision_request": {
                "ok": True,
                "mode": "CONTROLLED_HUMAN_DECISION_REQUEST_ONLY",
                "approved_next_gate_if_reviewed": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
                "allowed_answer_now": "APPROVE_D100_CONTROLLED_HUMAN_EXECUTION_DECISION_ONLY",
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
                "controlled_human_decision_only": True,
                "approval_for_real_apply": False,
                "approval_for_d101_creation_only": True,
            },
        })

        write(root / "reports/d100_final_apply_permission_matrix.json", {
            "ok": True,
            "decision_id": "d100-test",
            "capsule_id": "d99-test",
            "matrix_mode": "HUMAN_DECISION_REQUEST_ONLY",
            "ai_permissions": {
                "run_real_apply": False,
                "insert_route": False,
                "mutate_protected_core": False,
                "overwrite_canonical_memory": False,
                "call_external_network_for_execution": False,
                "git_commit_or_push": False,
                "execute_rollback": False,
                "delete_runtime_candidate": False,
            },
            "apply_allowed_now": False,
            "route_insert_allowed_now": False,
            "protected_core_mutation_allowed_now": False,
            "next_required_gate": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
        })

        write(root / "reports/d100_human_operator_scope_statement.json", {
            "ok": True,
            "decision_id": "d100-test",
            "capsule_id": "d99-test",
            "required_phrase": "APPROVE_D100_CONTROLLED_HUMAN_EXECUTION_DECISION_ONLY",
            "approval_scope": "D101_CAPSULE_CREATION_ONLY",
            "approved_next_gate_if_reviewed": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
            "not_approved": [
                "actual_apply_by_ai",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "external_ai_network_execution",
                "git_commit_or_push_by_ai",
                "execute_rollback_by_ai",
                "delete_runtime_candidate_by_ai",
            ],
        })

        write(root / "reports/d100_d101_one_shot_manual_execution_capsule_scope.json", {
            "ok": True,
            "decision_id": "d100-test",
            "capsule_id": "d99-test",
            "allowed_next_gate": "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE",
            "d101_allowed_to_create": [
                "one_shot_manual_execution_capsule",
                "manual_command_preview",
                "post_execution_required_checks",
                "abort_on_mismatch_policy",
            ],
            "d101_must_not_execute": [
                "actual_apply_by_ai",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "external_ai_network_execution",
                "git_commit_or_push_by_ai",
                "execute_rollback_by_ai",
                "delete_runtime_candidate_by_ai",
            ],
            "apply_allowed_after_d100": False,
            "route_insert_allowed_after_d100": False,
            "protected_core_mutation_allowed_after_d100": False,
            "required_phrase_for_later_gate": "APPROVE_D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE_ONLY",
        })

        return td, root

    def test_creates_manual_capsule_preview_only(self):
        td, root = self.root()
        try:
            r = create_one_shot_manual_execution_capsule(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_READY")
            self.assertTrue(r["guardrails"]["manual_capsule_preview_only"])
            self.assertTrue(r["guardrails"]["human_manual_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertFalse(r["one_shot_manual_execution_capsule"]["real_apply_allowed_now"])
            self.assertEqual(r["one_shot_manual_execution_capsule"]["next_required_gate"], "D102_POST_EXECUTION_VERIFIER")
            self.assertTrue((root / "reports/d101_one_shot_manual_execution_capsule.json").exists())
            self.assertTrue((root / "reports/d101_manual_command_preview.json").exists())
            self.assertTrue((root / "reports/d101_post_execution_required_checks.json").exists())
            self.assertTrue((root / "reports/d101_abort_on_mismatch_policy.json").exists())
            self.assertTrue((root / "reports/d101_d102_post_execution_verifier_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d100(self):
        td, root = self.root()
        try:
            (root / "reports/d100_controlled_human_execution_decision_request.json").unlink()
            r = create_one_shot_manual_execution_capsule(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "ONE_SHOT_MANUAL_EXECUTION_CAPSULE_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_ai_apply_allowed(self):
        td, root = self.root()
        try:
            p = root / "reports/d100_final_apply_permission_matrix.json"
            data = json.loads(p.read_text())
            data["ai_permissions"]["run_real_apply"] = True
            p.write_text(json.dumps(data))
            r = create_one_shot_manual_execution_capsule(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
