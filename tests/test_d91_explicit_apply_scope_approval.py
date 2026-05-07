import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.explicit_apply_scope_approval import create_explicit_apply_scope_approval


class TestD91ExplicitApplyScopeApproval(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)

        (root / "reports/d90_controlled_apply_plan.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "CONTROLLED_APPLY_PLAN_PREVIEW_READY",
                    "plan_id": "d90-test-plan",
                    "summary": {
                        "plan_id": "d90-test-plan",
                        "confirmation_id": "d89-test-confirmation",
                        "package_id": "d85-test-package",
                    },
                    "plan": {
                        "mode": "PLAN_PREVIEW_ONLY",
                        "required_next_gate": "D91_EXPLICIT_APPLY_SCOPE_APPROVAL",
                        "plan_summary": {
                            "real_apply_allowed": False,
                            "route_insert_allowed": False,
                            "protected_core_mutation_allowed": False,
                            "ai_git_action_allowed": False,
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
                        "controlled_plan_only": True,
                        "preview_only": True,
                        "approval_for_real_apply": False,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d90_apply_command_preview.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "preview_only": True,
                    "commands_are_documentation_only": True,
                    "commands_must_not_be_executed_by_ai": True,
                    "blocked_commands": [
                        "git apply",
                        "git commit",
                        "git push",
                        "route insert",
                    ],
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d90_manual_review_checklist.json").write_text(
            json.dumps(
                {
                    "ok": True,
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
                }
            ),
            encoding="utf-8",
        )

        return td, root

    def test_creates_scope_approval_for_d92_only(self):
        td, root = self.make_root()
        try:
            report = create_explicit_apply_scope_approval(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "EXPLICIT_APPLY_SCOPE_APPROVAL_READY")
            self.assertTrue(report["guardrails"]["scope_approval_only"])
            self.assertTrue(report["guardrails"]["d92_dry_run_only"])
            self.assertFalse(report["guardrails"]["approval_for_real_apply"])
            self.assertFalse(report["apply_still_blocked"]["apply_allowed_now"])
            self.assertEqual(report["scope_request"]["approved_next_gate"], "D92_GUARDED_APPLY_DRY_RUN_PACKAGE")
            self.assertTrue((root / "reports/d91_explicit_apply_scope_approval.json").exists())
            self.assertTrue((root / "reports/d91_apply_scope_request.json").exists())
            self.assertTrue((root / "reports/d91_apply_still_blocked.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d90(self):
        td, root = self.make_root()
        try:
            (root / "reports/d90_controlled_apply_plan.json").unlink()
            report = create_explicit_apply_scope_approval(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "EXPLICIT_APPLY_SCOPE_APPROVAL_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_d90_approves_real_apply(self):
        td, root = self.make_root()
        try:
            p = root / "reports/d90_controlled_apply_plan.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data), encoding="utf-8")

            report = create_explicit_apply_scope_approval(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "EXPLICIT_APPLY_SCOPE_APPROVAL_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
