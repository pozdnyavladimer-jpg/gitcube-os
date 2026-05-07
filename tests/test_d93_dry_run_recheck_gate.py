
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.dry_run_recheck_gate import create_dry_run_recheck_gate


def write(path, data):
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD93DryRunRecheckGate(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d92_guarded_apply_dry_run_package.json", {
            "ok": True,
            "decision": "GUARDED_APPLY_DRY_RUN_PACKAGE_READY",
            "result": "D92_GUARDED_APPLY_DRY_RUN_PACKAGE_CREATED",
            "package_id": "d92-test",
            "dry_run_package": {
                "mode": "GUARDED_DRY_RUN_PACKAGE_ONLY",
                "required_next_gate": "D93_DRY_RUN_RECHECK_GATE",
                "dry_run_contract": {
                    "external_ai_called": False,
                    "network_accessed": False,
                    "runtime_code_mutated": False,
                    "protected_core_mutated": False,
                    "canonical_memory_mutated": False,
                    "actual_apply_executed": False,
                    "route_inserted": False,
                    "git_commit_by_ai": False,
                    "dry_run_package_only": True,
                },
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
                "guarded_dry_run_package_only": True,
                "apply_allowed_now": False,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d92_apply_scope_diff_preview.json", {
            "ok": True,
            "package_id": "d92-test",
            "dry_run_only": True,
            "documentation_only": True,
            "planned_files_to_touch": [],
            "protected_files_to_touch": [],
            "route_insertions": [],
            "runtime_mutations": [],
            "canonical_memory_changes": [],
            "external_calls": [],
            "allowed_next_gate": "D93_DRY_RUN_RECHECK_GATE",
        })

        write(root / "reports/d92_pre_apply_recheck_commands.json", {
            "ok": True,
            "package_id": "d92-test",
            "commands_are_documentation_only": True,
            "commands_must_not_be_executed_by_ai": True,
            "human_may_run_manually": True,
            "blocked_commands": ["git apply", "git commit", "git push", "route insert"],
        })

        write(root / "reports/d92_abort_conditions.json", {
            "ok": True,
            "package_id": "d92-test",
            "abort_if": [
                "any unit test fails",
                "D66 recheck is missing or failed",
                "D85 rollback manifest is missing",
                "planned diff touches protected core",
                "external AI/network call is required",
            ],
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

        return td, root

    def test_creates_recheck_gate_only(self):
        td, root = self.root()
        try:
            r = create_dry_run_recheck_gate(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "DRY_RUN_RECHECK_GATE_READY")
            self.assertTrue(r["guardrails"]["dry_run_recheck_only"])
            self.assertFalse(r["guardrails"]["commands_executed_by_d93"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["d94_scope"]["allowed_next_gate"], "D94_FINAL_EXECUTION_APPROVAL_REQUEST")
            self.assertTrue((root / "reports/d93_dry_run_recheck_gate.json").exists())
            self.assertTrue((root / "reports/d93_recheck_results.json").exists())
            self.assertTrue((root / "reports/d93_apply_still_blocked.json").exists())
            self.assertTrue((root / "reports/d93_d94_execution_gate_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d92(self):
        td, root = self.root()
        try:
            (root / "reports/d92_guarded_apply_dry_run_package.json").unlink()
            r = create_dry_run_recheck_gate(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "DRY_RUN_RECHECK_GATE_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_diff_touches_file(self):
        td, root = self.root()
        try:
            p = root / "reports/d92_apply_scope_diff_preview.json"
            data = json.loads(p.read_text())
            data["planned_files_to_touch"] = ["app/orchestration/task_dispatcher.py"]
            p.write_text(json.dumps(data))
            r = create_dry_run_recheck_gate(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
