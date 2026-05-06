import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_writer_handoff import create_sandbox_writer_handoff, sha256_json


def signed_payload():
    payload = {
        "approval_scope": "ALLOW_AI_PROPOSAL_TO_SANDBOX_INTAKE_ONLY",
        "approval_phrase": "APPROVE_D82_AI_PROPOSAL_INTAKE",
        "approver": "human_operator",
        "d81_intake_id": "d81-test-intake",
        "boundary_id": "d80-test-boundary",
        "proposal_id": "d80-proposal-test",
        "intake_contract_mode": "JSON_CONTRACT_ONLY",
        "allowed_next_gate": "D83_SANDBOX_WRITER_HANDOFF",
        "blocked_actions": [
            "actual_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "git_commit_or_push_by_ai",
        ],
    }
    payload["signature_sha256"] = sha256_json(payload)
    return payload


class TestD83SandboxWriterHandoff(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)

        payload = signed_payload()
        intent_id = "d82-test-intent"

        (root / "reports/d82_human_signed_intent.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "HUMAN_SIGNED_INTENT_READY",
                    "intent_id": intent_id,
                    "signed_payload": payload,
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
                        "sandbox_handoff_only": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d82_human_approval_request.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "intent_id": intent_id,
                    "allowed_next_gate": "D83_SANDBOX_WRITER_HANDOFF",
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d81_ai_proposal_intake_contract.json").write_text(
            json.dumps(
                {
                    "enabled": True,
                    "mode": "JSON_CONTRACT_ONLY",
                    "accepted_input": {
                        "candidate_files_prefixes_allowed": [
                            "runtime_experimental/",
                            "reports/",
                            "tests/",
                        ],
                        "candidate_files_prefixes_blocked": [
                            "app/orchestration/",
                            "core/",
                            "runtime/",
                            "bridges/",
                            "memory/",
                        ],
                    },
                }
            ),
            encoding="utf-8",
        )

        return td, root

    def test_creates_sandbox_writer_input_only(self):
        td, root = self.make_root()
        try:
            report = create_sandbox_writer_handoff(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "SANDBOX_WRITER_HANDOFF_READY")
            self.assertTrue(report["guardrails"]["writer_input_only"])
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertFalse(report["guardrails"]["protected_core_mutated"])
            self.assertTrue((root / "reports/d83_sandbox_writer_handoff.json").exists())
            self.assertTrue((root / "reports/d83_sandbox_writer_handoff_manifest.json").exists())
            self.assertTrue(Path(report["writer_input_path"]).exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d82(self):
        td, root = self.make_root()
        try:
            (root / "reports/d82_human_signed_intent.json").unlink()
            report = create_sandbox_writer_handoff(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "SANDBOX_WRITER_HANDOFF_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_bad_signature(self):
        td, root = self.make_root()
        try:
            p = root / "reports/d82_human_signed_intent.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["signed_payload"]["proposal_id"] = "tampered"
            p.write_text(json.dumps(data), encoding="utf-8")

            report = create_sandbox_writer_handoff(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "SANDBOX_WRITER_HANDOFF_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
