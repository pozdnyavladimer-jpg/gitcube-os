import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.controlled_apply_plan import create_controlled_apply_plan


class TestD90ControlledApplyPlan(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)

        (root / "reports/d89_final_human_confirmation.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "FINAL_HUMAN_CONFIRMATION_READY",
                    "confirmation_id": "d89-test-confirmation",
                    "evidence": {
                        "request_id": "d88-test-request",
                        "capsule_id": "d87-test-capsule",
                        "package_id": "d85-test-package",
                        "review_id": "d84-test-review",
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
                        "final_human_confirmation_only": True,
                        "d90_planning_only": True,
                        "approval_for_real_apply": False,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d89_human_confirmation_statement.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "confirmation_id": "d89-test-confirmation",
                    "confirmation_phrase": "CONFIRM_D89_FINAL_HUMAN_REVIEW_FOR_D90_PLANNING_ONLY",
                    "approved_next_gate": "D90_CONTROLLED_APPLY_PLAN",
                    "source_request_id": "d88-test-request",
                    "source_package_id": "d85-test-package",
                    "not_approved": [
                        "actual_apply",
                        "route_insert",
                        "protected_core_mutation",
                        "canonical_memory_overwrite",
                        "external_ai_network_call",
                        "git_commit_or_push_by_ai",
                    ],
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d89_d90_planning_scope.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "next_gate": "D90_CONTROLLED_APPLY_PLAN",
                    "d90_allowed_to_create": [
                        "controlled_apply_plan_json",
                        "explicit_scope_diff_summary",
                        "pre_apply_command_preview",
                        "manual_review_checklist",
                    ],
                    "d90_must_not_execute": [
                        "actual_apply",
                        "route_insert",
                        "protected_core_mutation",
                        "canonical_memory_overwrite",
                        "external_ai_network_call",
                        "git_commit_or_push_by_ai",
                    ],
                    "apply_allowed_after_d89": False,
                    "route_insert_allowed_after_d89": False,
                    "protected_core_mutation_allowed_after_d89": False,
                }
            ),
            encoding="utf-8",
        )

        return td, root

    def test_creates_controlled_apply_plan_preview_only(self):
        td, root = self.make_root()
        try:
            report = create_controlled_apply_plan(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "CONTROLLED_APPLY_PLAN_PREVIEW_READY")
            self.assertTrue(report["guardrails"]["controlled_plan_only"])
            self.assertTrue(report["guardrails"]["preview_only"])
            self.assertFalse(report["guardrails"]["approval_for_real_apply"])
            self.assertFalse(report["plan"]["plan_summary"]["real_apply_allowed"])
            self.assertEqual(report["plan"]["required_next_gate"], "D91_EXPLICIT_APPLY_SCOPE_APPROVAL")
            self.assertTrue((root / "reports/d90_controlled_apply_plan.json").exists())
            self.assertTrue((root / "reports/d90_apply_command_preview.json").exists())
            self.assertTrue((root / "reports/d90_manual_review_checklist.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d89(self):
        td, root = self.make_root()
        try:
            (root / "reports/d89_final_human_confirmation.json").unlink()
            report = create_controlled_apply_plan(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "CONTROLLED_APPLY_PLAN_PREVIEW_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_d89_approves_real_apply(self):
        td, root = self.make_root()
        try:
            p = root / "reports/d89_final_human_confirmation.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data), encoding="utf-8")

            report = create_controlled_apply_plan(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "CONTROLLED_APPLY_PLAN_PREVIEW_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
