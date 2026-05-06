import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.human_signed_intent import create_human_signed_intent


class TestD82HumanSignedIntent(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)

        (root / "reports/d81_ai_proposal_intake.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "AI_PROPOSAL_INTAKE_READY",
                    "intake_id": "d81-test-intake",
                    "evidence": {
                        "boundary_id": "d80-test-boundary",
                        "proposal_id": "d80-proposal-test",
                    },
                    "guardrails": {
                        "external_ai_called": False,
                        "network_accessed": False,
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "actual_apply_executed": False,
                        "route_inserted": False,
                        "proposal_intake_only": True,
                        "json_only": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d81_ai_proposal_intake_contract.json").write_text(
            json.dumps(
                {
                    "enabled": True,
                    "mode": "JSON_CONTRACT_ONLY",
                    "next_gate": "D82_HUMAN_APPROVAL_SIGNED_INTENT",
                    "required_guardrails": {
                        "external_ai_called": False,
                        "network_accessed": False,
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "actual_apply_executed": False,
                        "route_inserted": False,
                        "proposal_only": True,
                        "json_only": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        return td, root

    def test_creates_signed_intent(self):
        td, root = self.make_root()
        try:
            report = create_human_signed_intent(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "HUMAN_SIGNED_INTENT_READY")
            self.assertEqual(report["signed_payload"]["approval_phrase"], "APPROVE_D82_AI_PROPOSAL_INTAKE")
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertTrue(report["guardrails"]["sandbox_handoff_only"])
            self.assertTrue((root / "reports/d82_human_signed_intent.json").exists())
            self.assertTrue((root / "reports/d82_human_approval_request.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d81(self):
        td, root = self.make_root()
        try:
            (root / "reports/d81_ai_proposal_intake.json").unlink()
            report = create_human_signed_intent(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "HUMAN_SIGNED_INTENT_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_bad_phrase(self):
        td, root = self.make_root()
        try:
            report = create_human_signed_intent(root=root, approval_phrase="WRONG")

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "HUMAN_SIGNED_INTENT_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
