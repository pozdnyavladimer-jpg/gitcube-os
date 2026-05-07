
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.final_local_full_regression import create_final_local_full_regression


def write(path, data):
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD96FinalLocalFullRegression(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d95_human_signed_execution_intent.json", {
            "ok": True,
            "decision": "HUMAN_SIGNED_EXECUTION_INTENT_READY",
            "intent_id": "d95-test",
            "request_id": "d94-test",
            "package_id": "d92-test",
            "signed_intent": {
                "signed_phrase": "APPROVE_D95_HUMAN_SIGNED_EXECUTION_INTENT_FOR_D96_REGRESSION_ONLY",
                "approved_next_gate": "D96_FINAL_LOCAL_FULL_REGRESSION",
                "apply_allowed_now": False,
                "route_insert_allowed_now": False,
                "protected_core_mutation_allowed_now": False,
                "not_approved": [
                    "actual_apply",
                    "route_insert",
                    "protected_core_mutation",
                    "canonical_memory_overwrite",
                    "external_ai_network_call",
                    "git_commit_or_push_by_ai",
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
                "human_signed_intent_only": True,
                "d96_regression_only": True,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d95_execution_intent_signature.json", {
            "ok": True,
            "intent_id": "d95-test",
            "approval_phrase": "APPROVE_D95_HUMAN_SIGNED_EXECUTION_INTENT_FOR_D96_REGRESSION_ONLY",
            "signed_scope": "D96_FINAL_LOCAL_FULL_REGRESSION_ONLY",
            "signature_sha256": "abc123",
            "not_approved": [
                "actual_apply",
                "route_insert",
                "protected_core_mutation",
                "canonical_memory_overwrite",
                "external_ai_network_call",
                "git_commit_or_push_by_ai",
            ],
        })

        write(root / "reports/d95_apply_still_blocked.json", {
            "ok": True,
            "intent_id": "d95-test",
            "apply_allowed_now": False,
            "route_insert_allowed_now": False,
            "protected_core_mutation_allowed_now": False,
            "canonical_memory_mutation_allowed_now": False,
            "external_ai_call_allowed_now": False,
            "git_action_by_ai_allowed_now": False,
            "next_required_gate": "D96_FINAL_LOCAL_FULL_REGRESSION",
        })

        return td, root

    def test_creates_regression_artifact_without_running_commands(self):
        td, root = self.root()
        try:
            r = create_final_local_full_regression(root, run_commands=False)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "FINAL_LOCAL_FULL_REGRESSION_PASSED")
            self.assertTrue(r["guardrails"]["local_regression_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["d97_scope"]["allowed_next_gate"], "D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION")
            self.assertTrue((root / "reports/d96_final_local_full_regression.json").exists())
            self.assertTrue((root / "reports/d96_full_regression_results.json").exists())
            self.assertTrue((root / "reports/d96_apply_still_blocked.json").exists())
            self.assertTrue((root / "reports/d96_d97_no_touch_reconfirmation_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d95(self):
        td, root = self.root()
        try:
            (root / "reports/d95_human_signed_execution_intent.json").unlink()
            r = create_final_local_full_regression(root, run_commands=False)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "FINAL_LOCAL_FULL_REGRESSION_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_d95_approves_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d95_human_signed_execution_intent.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data))
            r = create_final_local_full_regression(root, run_commands=False)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
