import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.higher_policy_approval_request import create_higher_policy_approval_request


class TestD88HigherPolicyApprovalRequest(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)

        (root / "reports/d87_final_pre_apply_safety_capsule.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "FINAL_PRE_APPLY_SAFETY_CAPSULE_READY",
                    "summary": {
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
                        "final_capsule_only": True,
                        "pre_apply_review_only": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d87_pre_apply_safety_capsule.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "capsule_id": "d87-test-capsule",
                    "package_id": "d85-test-package",
                    "review_id": "d84-test-review",
                    "next_gate": "D88_HIGHER_POLICY_APPROVAL_REQUEST",
                    "evidence_chain": {
                        "d85_decision": "REGRESSION_ROLLBACK_EVIDENCE_READY",
                        "d86_decision": "LOCAL_REGRESSION_PASSED",
                        "d86_commands_failed_count": 0,
                        "rollback_manifest_present": True,
                        "regression_checklist_present": True,
                    },
                    "approval_state": {
                        "ready_for_higher_policy_review": True,
                        "ready_for_real_apply": False,
                        "ready_for_route_insert": False,
                        "ready_for_protected_core_mutation": False,
                    },
                    "hard_no_mutation_flags": {
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

        (root / "reports/d87_apply_blockers.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "apply_allowed_now": False,
                    "route_insert_allowed_now": False,
                    "protected_core_mutation_allowed_now": False,
                    "external_ai_call_allowed_now": False,
                    "git_action_by_ai_allowed_now": False,
                    "hard_blockers": ["no explicit D88 higher policy approval"],
                    "required_before_apply_can_be_discussed": [
                        "D88_HIGHER_POLICY_APPROVAL_REQUEST",
                        "D89_FINAL_HUMAN_CONFIRMATION",
                        "D66_RECHECK",
                        "FULL_TEST_DISCOVERY",
                        "ROLLBACK_MANIFEST_RECONFIRMATION",
                    ],
                }
            ),
            encoding="utf-8",
        )

        return td, root

    def test_creates_higher_policy_request_only(self):
        td, root = self.make_root()
        try:
            report = create_higher_policy_approval_request(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "HIGHER_POLICY_APPROVAL_REQUEST_READY")
            self.assertTrue(report["guardrails"]["higher_policy_request_only"])
            self.assertTrue(report["guardrails"]["approval_not_granted"])
            self.assertFalse(report["apply_still_blocked"]["apply_allowed_now"])
            self.assertEqual(report["review_packet"]["allowed_next_gate_if_reviewed"], "D89_FINAL_HUMAN_CONFIRMATION")
            self.assertTrue((root / "reports/d88_higher_policy_approval_request.json").exists())
            self.assertTrue((root / "reports/d88_higher_policy_review_packet.json").exists())
            self.assertTrue((root / "reports/d88_apply_still_blocked.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d87(self):
        td, root = self.make_root()
        try:
            (root / "reports/d87_final_pre_apply_safety_capsule.json").unlink()
            report = create_higher_policy_approval_request(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "HIGHER_POLICY_APPROVAL_REQUEST_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_apply_allowed(self):
        td, root = self.make_root()
        try:
            p = root / "reports/d87_apply_blockers.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["apply_allowed_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")

            report = create_higher_policy_approval_request(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "HIGHER_POLICY_APPROVAL_REQUEST_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
