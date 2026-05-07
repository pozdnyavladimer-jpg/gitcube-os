import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.final_human_confirmation import create_final_human_confirmation


class TestD89FinalHumanConfirmation(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)

        (root / "reports/d88_higher_policy_approval_request.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "HIGHER_POLICY_APPROVAL_REQUEST_READY",
                    "request_id": "d88-test-request",
                    "evidence": {
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
                        "higher_policy_request_only": True,
                        "approval_not_granted": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d88_higher_policy_review_packet.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "request_id": "d88-test-request",
                    "review_phrase": "REVIEW_D88_HIGHER_POLICY_REQUEST_ONLY",
                    "allowed_next_gate_if_reviewed": "D89_FINAL_HUMAN_CONFIRMATION",
                    "policy_answer_now": "NOT_APPROVED_YET",
                    "source_capsule_id": "d87-test-capsule",
                    "source_package_id": "d85-test-package",
                    "source_review_id": "d84-test-review",
                    "not_allowed": [
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

        (root / "reports/d88_apply_still_blocked.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "apply_allowed_now": False,
                    "route_insert_allowed_now": False,
                    "protected_core_mutation_allowed_now": False,
                    "canonical_memory_mutation_allowed_now": False,
                    "external_ai_call_allowed_now": False,
                    "git_action_by_ai_allowed_now": False,
                    "next_required_gate": "D89_FINAL_HUMAN_CONFIRMATION",
                }
            ),
            encoding="utf-8",
        )

        return td, root

    def test_creates_final_human_confirmation_only(self):
        td, root = self.make_root()
        try:
            report = create_final_human_confirmation(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "FINAL_HUMAN_CONFIRMATION_READY")
            self.assertTrue(report["guardrails"]["final_human_confirmation_only"])
            self.assertTrue(report["guardrails"]["d90_planning_only"])
            self.assertFalse(report["guardrails"]["approval_for_real_apply"])
            self.assertFalse(report["d90_scope"]["apply_allowed_after_d89"])
            self.assertEqual(report["d90_scope"]["next_gate"], "D90_CONTROLLED_APPLY_PLAN")
            self.assertTrue((root / "reports/d89_final_human_confirmation.json").exists())
            self.assertTrue((root / "reports/d89_human_confirmation_statement.json").exists())
            self.assertTrue((root / "reports/d89_d90_planning_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d88(self):
        td, root = self.make_root()
        try:
            (root / "reports/d88_higher_policy_approval_request.json").unlink()
            report = create_final_human_confirmation(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "FINAL_HUMAN_CONFIRMATION_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_d88_apply_allowed(self):
        td, root = self.make_root()
        try:
            p = root / "reports/d88_apply_still_blocked.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["apply_allowed_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")

            report = create_final_human_confirmation(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "FINAL_HUMAN_CONFIRMATION_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
