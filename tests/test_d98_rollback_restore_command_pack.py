
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.rollback_restore_command_pack import create_rollback_restore_command_pack


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD98RollbackRestoreCommandPack(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d97_protected_core_no_touch_reconfirmation.json", {
            "ok": True,
            "decision": "PROTECTED_CORE_NO_TOUCH_RECONFIRMED",
            "reconfirmation_id": "d97-test",
            "regression_id": "d96-test",
            "package_id": "d92-test",
            "guardrails": {
                "external_ai_called": False,
                "network_accessed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
                "protected_core_no_touch_reconfirmation_only": True,
                "hash_snapshot_only": True,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d97_protected_file_hash_snapshot.json", {
            "ok": True,
            "reconfirmation_id": "d97-test",
            "regression_id": "d96-test",
            "state": "D97_PROTECTED_FILE_HASH_SNAPSHOT",
            "snapshot_sha256": "abc123",
            "hashed_files_count": 1,
            "mutation_performed": False,
        })

        write(root / "reports/d97_no_route_insert_reconfirmation.json", {
            "ok": True,
            "reconfirmation_id": "d97-test",
            "regression_id": "d96-test",
            "route_insert_allowed_now": False,
            "route_inserted": False,
            "route_mutation_performed": False,
            "next_required_gate": "D98_ROLLBACK_RESTORE_COMMAND_PACK",
        })

        write(root / "reports/d97_d98_rollback_restore_scope.json", {
            "ok": True,
            "reconfirmation_id": "d97-test",
            "regression_id": "d96-test",
            "allowed_next_gate": "D98_ROLLBACK_RESTORE_COMMAND_PACK",
            "d98_allowed_to_create": [
                "rollback_restore_command_pack",
                "restore_manifest_reference",
                "pre_execution_abort_plan",
            ],
            "d98_must_not_execute": [
                "actual_apply",
                "route_insert",
                "protected_core_mutation",
                "canonical_memory_overwrite",
                "external_ai_network_call",
                "git_commit_or_push_by_ai",
                "execute_rollback_now",
                "delete_runtime_candidate",
            ],
            "apply_allowed_after_d97": False,
            "route_insert_allowed_after_d97": False,
            "protected_core_mutation_allowed_after_d97": False,
            "required_phrase_for_later_gate": "APPROVE_D98_ROLLBACK_RESTORE_COMMAND_PACK_ONLY",
        })

        return td, root

    def test_creates_rollback_pack_documentation_only(self):
        td, root = self.root()
        try:
            r = create_rollback_restore_command_pack(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "ROLLBACK_RESTORE_COMMAND_PACK_READY")
            self.assertTrue(r["guardrails"]["rollback_restore_documentation_only"])
            self.assertFalse(r["guardrails"]["rollback_executed"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["rollback_restore_command_pack"]["next_required_gate"], "D99_FINAL_GUARDED_EXECUTION_CAPSULE")
            self.assertTrue((root / "reports/d98_rollback_restore_command_pack.json").exists())
            self.assertTrue((root / "reports/d98_restore_manifest_reference.json").exists())
            self.assertTrue((root / "reports/d98_pre_execution_abort_plan.json").exists())
            self.assertTrue((root / "reports/d98_d99_final_guarded_execution_capsule_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d97(self):
        td, root = self.root()
        try:
            (root / "reports/d97_protected_core_no_touch_reconfirmation.json").unlink()
            r = create_rollback_restore_command_pack(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "ROLLBACK_RESTORE_COMMAND_PACK_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_route_inserted(self):
        td, root = self.root()
        try:
            p = root / "reports/d97_no_route_insert_reconfirmation.json"
            data = json.loads(p.read_text())
            data["route_inserted"] = True
            p.write_text(json.dumps(data))
            r = create_rollback_restore_command_pack(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
