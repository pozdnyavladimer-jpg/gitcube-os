
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.guarded_apply_dry_run_package import create_guarded_apply_dry_run_package


def write(path, data):
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD92GuardedApplyDryRunPackage(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()
        write(root / "reports/d91_explicit_apply_scope_approval.json", {
            "ok": True,
            "decision": "EXPLICIT_APPLY_SCOPE_APPROVAL_READY",
            "approval_id": "d91-test",
            "evidence": {"plan_id": "d90-test", "package_id": "d85-test"},
            "guardrails": {
                "external_ai_called": False,
                "network_accessed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
                "scope_approval_only": True,
                "d92_dry_run_only": True,
                "approval_for_real_apply": False,
            },
        })
        write(root / "reports/d91_apply_scope_request.json", {
            "ok": True,
            "approval_id": "d91-test",
            "approval_phrase": "APPROVE_D91_SCOPE_FOR_D92_GUARDED_APPLY_DRY_RUN_ONLY",
            "approved_next_gate": "D92_GUARDED_APPLY_DRY_RUN_PACKAGE",
            "source_plan_id": "d90-test",
            "source_package_id": "d85-test",
            "allowed_scope_for_d92": [
                "generate_guarded_apply_dry_run_package",
                "generate_apply_scope_diff_preview",
                "generate_pre_apply_recheck_commands",
                "generate_abort_conditions",
            ],
            "forbidden_real_actions": [
                "actual_apply",
                "route_insert",
                "protected_core_mutation",
                "canonical_memory_overwrite",
                "external_ai_network_call",
                "git_commit_or_push_by_ai",
            ],
        })
        write(root / "reports/d91_apply_still_blocked.json", {
            "ok": True,
            "apply_allowed_now": False,
            "route_insert_allowed_now": False,
            "protected_core_mutation_allowed_now": False,
            "canonical_memory_mutation_allowed_now": False,
            "external_ai_call_allowed_now": False,
            "git_action_by_ai_allowed_now": False,
            "next_required_gate": "D92_GUARDED_APPLY_DRY_RUN_PACKAGE",
        })
        return td, root

    def test_creates_dry_run_package_only(self):
        td, root = self.root()
        try:
            r = create_guarded_apply_dry_run_package(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "GUARDED_APPLY_DRY_RUN_PACKAGE_READY")
            self.assertTrue(r["guardrails"]["guarded_dry_run_package_only"])
            self.assertFalse(r["guardrails"]["apply_allowed_now"])
            self.assertEqual(r["dry_run_package"]["required_next_gate"], "D93_DRY_RUN_RECHECK_GATE")
            self.assertTrue((root / "reports/d92_guarded_apply_dry_run_package.json").exists())
            self.assertTrue((root / "reports/d92_apply_scope_diff_preview.json").exists())
            self.assertTrue((root / "reports/d92_pre_apply_recheck_commands.json").exists())
            self.assertTrue((root / "reports/d92_abort_conditions.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d91(self):
        td, root = self.root()
        try:
            (root / "reports/d91_explicit_apply_scope_approval.json").unlink()
            r = create_guarded_apply_dry_run_package(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "GUARDED_APPLY_DRY_RUN_PACKAGE_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_real_apply_approval(self):
        td, root = self.root()
        try:
            p = root / "reports/d91_explicit_apply_scope_approval.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data))
            r = create_guarded_apply_dry_run_package(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
