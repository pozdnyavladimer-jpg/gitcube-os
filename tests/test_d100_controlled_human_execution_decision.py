
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.controlled_human_execution_decision import create_controlled_human_execution_decision


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD100ControlledHumanExecutionDecision(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d99_final_guarded_execution_capsule.json", {
            "ok": True,
            "decision": "FINAL_GUARDED_EXECUTION_CAPSULE_READY",
            "capsule_id": "d99-test",
            "pack_id": "d98-test",
            "regression_id": "d96-test",
            "package_id": "d92-test",
            "final_guarded_execution_capsule": {
                "ok": True,
                "mode": "FINAL_GUARDED_CAPSULE_REVIEW_ONLY",
                "next_required_gate": "D100_CONTROLLED_HUMAN_EXECUTION_DECISION",
                "apply_allowed_now": False,
                "route_insert_allowed_now": False,
                "protected_core_mutation_allowed_now": False,
                "approval_for_real_apply": False,
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
                "final_guarded_capsule_only": True,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d99_final_no_apply_blocker_state.json", {
            "ok": True,
            "capsule_id": "d99-test",
            "pack_id": "d98-test",
            "apply_allowed_now": False,
            "route_insert_allowed_now": False,
            "protected_core_mutation_allowed_now": False,
            "canonical_memory_mutation_allowed_now": False,
            "external_ai_call_allowed_now": False,
            "git_action_by_ai_allowed_now": False,
            "rollback_allowed_now": False,
            "restore_allowed_now": False,
            "next_required_gate": "D100_CONTROLLED_HUMAN_EXECUTION_DECISION",
        })

        write(root / "reports/d99_post_capsule_manual_review_checklist.json", {
            "ok": True,
            "capsule_id": "d99-test",
            "human_review_required": True,
            "must_remain_false": {
                "external_ai_called": False,
                "network_accessed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
            },
        })

        write(root / "reports/d99_d100_controlled_execution_scope.json", {
            "ok": True,
            "capsule_id": "d99-test",
            "pack_id": "d98-test",
            "allowed_next_gate": "D100_CONTROLLED_HUMAN_EXECUTION_DECISION",
            "d100_allowed_to_create": [
                "controlled_human_execution_decision_request",
                "final_apply_permission_matrix",
                "human_operator_scope_statement",
            ],
            "d100_must_not_execute": [
                "actual_apply",
                "route_insert",
                "protected_core_mutation",
                "canonical_memory_overwrite",
                "external_ai_network_call",
                "git_commit_or_push_by_ai",
                "execute_rollback_now",
                "delete_runtime_candidate",
            ],
            "apply_allowed_after_d99": False,
            "route_insert_allowed_after_d99": False,
            "protected_core_mutation_allowed_after_d99": False,
            "required_phrase_for_later_gate": "APPROVE_D100_CONTROLLED_HUMAN_EXECUTION_DECISION_ONLY",
        })

        return td, root

    def test_creates_controlled_human_decision_only(self):
        td, root = self.root()
        try:
            r = create_controlled_human_execution_decision(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "CONTROLLED_HUMAN_EXECUTION_DECISION_READY")
            self.assertTrue(r["guardrails"]["controlled_human_decision_only"])
            self.assertTrue(r["guardrails"]["approval_for_d101_creation_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["final_apply_permission_matrix"]["next_required_gate"], "D101_ONE_SHOT_MANUAL_EXECUTION_CAPSULE")
            self.assertTrue((root / "reports/d100_controlled_human_execution_decision_request.json").exists())
            self.assertTrue((root / "reports/d100_final_apply_permission_matrix.json").exists())
            self.assertTrue((root / "reports/d100_human_operator_scope_statement.json").exists())
            self.assertTrue((root / "reports/d100_d101_one_shot_manual_execution_capsule_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d99(self):
        td, root = self.root()
        try:
            (root / "reports/d99_final_guarded_execution_capsule.json").unlink()
            r = create_controlled_human_execution_decision(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "CONTROLLED_HUMAN_EXECUTION_DECISION_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_d99_approves_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d99_final_guarded_execution_capsule.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data))
            r = create_controlled_human_execution_decision(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
