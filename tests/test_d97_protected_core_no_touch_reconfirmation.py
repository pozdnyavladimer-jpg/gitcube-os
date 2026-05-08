
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.protected_core_no_touch_reconfirmation import create_protected_core_no_touch_reconfirmation


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD97ProtectedCoreNoTouchReconfirmation(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()
        (root / "core").mkdir()
        (root / "core/sample.py").write_text("x = 1\n", encoding="utf-8")

        write(root / "reports/d96_final_local_full_regression.json", {
            "ok": True,
            "decision": "FINAL_LOCAL_FULL_REGRESSION_PASSED",
            "regression_id": "d96-test",
            "intent_id": "d95-test",
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
                "local_regression_only": True,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d96_full_regression_results.json", {
            "ok": True,
            "network_accessed": False,
            "external_ai_called": False,
            "summary": {"failed_count": 0, "passed_count": 8, "commands_count": 8},
        })

        write(root / "reports/d96_apply_still_blocked.json", {
            "ok": True,
            "regression_id": "d96-test",
            "apply_allowed_now": False,
            "route_insert_allowed_now": False,
            "protected_core_mutation_allowed_now": False,
            "canonical_memory_mutation_allowed_now": False,
            "external_ai_call_allowed_now": False,
            "git_action_by_ai_allowed_now": False,
            "next_required_gate": "D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION",
        })

        write(root / "reports/d96_d97_no_touch_reconfirmation_scope.json", {
            "ok": True,
            "regression_id": "d96-test",
            "intent_id": "d95-test",
            "allowed_next_gate": "D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION",
            "d97_allowed_to_create": [
                "protected_core_no_touch_reconfirmation",
                "protected_file_hash_snapshot",
                "no_route_insert_reconfirmation",
            ],
            "d97_must_not_execute": [
                "actual_apply",
                "route_insert",
                "protected_core_mutation",
                "canonical_memory_overwrite",
                "external_ai_network_call",
                "git_commit_or_push_by_ai",
            ],
            "apply_allowed_after_d96": False,
            "route_insert_allowed_after_d96": False,
            "protected_core_mutation_allowed_after_d96": False,
            "required_phrase_for_later_gate": "APPROVE_D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION_ONLY",
        })

        return td, root

    def test_creates_no_touch_reconfirmation(self):
        td, root = self.root()
        try:
            r = create_protected_core_no_touch_reconfirmation(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "PROTECTED_CORE_NO_TOUCH_RECONFIRMED")
            self.assertTrue(r["guardrails"]["protected_core_no_touch_reconfirmation_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["d98_scope"]["allowed_next_gate"], "D98_ROLLBACK_RESTORE_COMMAND_PACK")
            self.assertGreaterEqual(r["summary"]["hashed_files_count"], 1)
            self.assertTrue((root / "reports/d97_protected_core_no_touch_reconfirmation.json").exists())
            self.assertTrue((root / "reports/d97_protected_file_hash_snapshot.json").exists())
            self.assertTrue((root / "reports/d97_no_route_insert_reconfirmation.json").exists())
            self.assertTrue((root / "reports/d97_d98_rollback_restore_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d96(self):
        td, root = self.root()
        try:
            (root / "reports/d96_final_local_full_regression.json").unlink()
            r = create_protected_core_no_touch_reconfirmation(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "PROTECTED_CORE_NO_TOUCH_RECONFIRMATION_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_d96_approves_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d96_final_local_full_regression.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data))
            r = create_protected_core_no_touch_reconfirmation(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
