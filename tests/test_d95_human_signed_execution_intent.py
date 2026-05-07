
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.human_signed_execution_intent import create_human_signed_execution_intent


def write(path, data):
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD95HumanSignedExecutionIntent(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d94_final_execution_approval_request.json", {
            "ok": True,
            "decision": "FINAL_EXECUTION_APPROVAL_REQUEST_READY",
            "request_id": "d94-test",
            "gate_id": "d93-test",
            "package_id": "d92-test",
            "approval_request": {
                "mode": "FINAL_EXECUTION_REVIEW_REQUEST_ONLY",
                "review_phrase": "APPROVE_D94_FINAL_EXECUTION_REQUEST_REVIEW_ONLY",
                "approval_not_granted": True,
                "real_apply_allowed": False,
                "route_insert_allowed": False,
                "protected_core_mutation_allowed": False,
                "allowed_next_gate_if_reviewed": "D95_HUMAN_SIGNED_EXECUTION_INTENT",
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
                "final_execution_request_only": True,
                "approval_for_real_apply": False,
                "human_review_required": True,
            },
        })

        write(root / "reports/d94_explicit_human_execution_phrase.json", {
            "ok": True,
            "required_phrase": "APPROVE_D94_FINAL_EXECUTION_REQUEST_REVIEW_ONLY",
            "approval_scope": "REVIEW_REQUEST_ONLY",
            "approved_next_gate_if_reviewed": "D95_HUMAN_SIGNED_EXECUTION_INTENT",
            "not_approved": [
                "actual_apply",
                "route_insert",
                "protected_core_mutation",
                "canonical_memory_overwrite",
                "external_ai_network_call",
                "git_commit_or_push_by_ai",
            ],
        })

        write(root / "reports/d94_final_apply_blockers_report.json", {
            "ok": True,
            "apply_allowed_now": False,
            "route_insert_allowed_now": False,
            "protected_core_mutation_allowed_now": False,
            "canonical_memory_mutation_allowed_now": False,
            "external_ai_call_allowed_now": False,
            "git_action_by_ai_allowed_now": False,
            "next_required_gate": "D95_HUMAN_SIGNED_EXECUTION_INTENT",
        })

        return td, root

    def test_creates_human_signed_intent_for_d96_only(self):
        td, root = self.root()
        try:
            r = create_human_signed_execution_intent(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "HUMAN_SIGNED_EXECUTION_INTENT_READY")
            self.assertTrue(r["guardrails"]["human_signed_intent_only"])
            self.assertTrue(r["guardrails"]["d96_regression_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["signed_intent"]["approved_next_gate"], "D96_FINAL_LOCAL_FULL_REGRESSION")
            self.assertTrue((root / "reports/d95_human_signed_execution_intent.json").exists())
            self.assertTrue((root / "reports/d95_execution_intent_signature.json").exists())
            self.assertTrue((root / "reports/d95_apply_still_blocked.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d94(self):
        td, root = self.root()
        try:
            (root / "reports/d94_final_execution_approval_request.json").unlink()
            r = create_human_signed_execution_intent(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "HUMAN_SIGNED_EXECUTION_INTENT_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_d94_approves_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d94_final_execution_approval_request.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data))
            r = create_human_signed_execution_intent(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
