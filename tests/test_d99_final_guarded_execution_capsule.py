
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.final_guarded_execution_capsule import create_final_guarded_execution_capsule


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD99FinalGuardedExecutionCapsule(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d98_rollback_restore_command_pack.json", {
            "ok": True,
            "decision": "ROLLBACK_RESTORE_COMMAND_PACK_READY",
            "pack_id": "d98-test",
            "reconfirmation_id": "d97-test",
            "regression_id": "d96-test",
            "package_id": "d92-test",
            "rollback_restore_command_pack": {
                "ok": True,
                "commands_are_documentation_only": True,
                "commands_must_not_be_executed_by_ai": True,
                "next_required_gate": "D99_FINAL_GUARDED_EXECUTION_CAPSULE",
                "not_approved": [
                    "actual_apply",
                    "route_insert",
                    "protected_core_mutation",
                    "canonical_memory_overwrite",
                    "external_ai_network_call",
                    "git_commit_or_push_by_ai",
                    "execute_rollback_now",
                    "delete_runtime_candidate",
                ],
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
                "rollback_restore_documentation_only": True,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d98_restore_manifest_reference.json", {
            "ok": True,
            "restore_reference_mode": "DOCUMENTATION_ONLY",
            "restore_not_executed": True,
            "source_snapshot_sha256": "abc123",
        })

        write(root / "reports/d98_pre_execution_abort_plan.json", {
            "ok": True,
            "human_review_required": True,
            "must_remain_false": {
                "actual_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "runtime_code_mutated": False,
                "external_ai_called": False,
                "network_accessed": False,
                "git_commit_by_ai": False,
                "rollback_executed": False,
            },
        })

        write(root / "reports/d98_d99_final_guarded_execution_capsule_scope.json", {
            "ok": True,
            "pack_id": "d98-test",
            "reconfirmation_id": "d97-test",
            "regression_id": "d96-test",
            "allowed_next_gate": "D99_FINAL_GUARDED_EXECUTION_CAPSULE",
            "d99_allowed_to_create": [
                "final_guarded_execution_capsule",
                "final_no_apply_blocker_state",
                "post_capsule_manual_review_checklist",
            ],
            "d99_must_not_execute": [
                "actual_apply",
                "route_insert",
                "protected_core_mutation",
                "canonical_memory_overwrite",
                "external_ai_network_call",
                "git_commit_or_push_by_ai",
                "execute_rollback_now",
                "delete_runtime_candidate",
            ],
            "apply_allowed_after_d98": False,
            "route_insert_allowed_after_d98": False,
            "protected_core_mutation_allowed_after_d98": False,
            "required_phrase_for_later_gate": "APPROVE_D99_FINAL_GUARDED_EXECUTION_CAPSULE_ONLY",
        })

        return td, root

    def test_creates_final_guarded_capsule_only(self):
        td, root = self.root()
        try:
            r = create_final_guarded_execution_capsule(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "FINAL_GUARDED_EXECUTION_CAPSULE_READY")
            self.assertTrue(r["guardrails"]["final_guarded_capsule_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertFalse(r["final_guarded_execution_capsule"]["apply_allowed_now"])
            self.assertEqual(r["final_no_apply_blocker_state"]["next_required_gate"], "D100_CONTROLLED_HUMAN_EXECUTION_DECISION")
            self.assertTrue((root / "reports/d99_final_guarded_execution_capsule.json").exists())
            self.assertTrue((root / "reports/d99_final_no_apply_blocker_state.json").exists())
            self.assertTrue((root / "reports/d99_post_capsule_manual_review_checklist.json").exists())
            self.assertTrue((root / "reports/d99_d100_controlled_execution_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d98(self):
        td, root = self.root()
        try:
            (root / "reports/d98_rollback_restore_command_pack.json").unlink()
            r = create_final_guarded_execution_capsule(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "FINAL_GUARDED_EXECUTION_CAPSULE_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_d98_approves_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d98_rollback_restore_command_pack.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data))
            r = create_final_guarded_execution_capsule(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
