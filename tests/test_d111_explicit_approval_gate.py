
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.explicit_approval_gate import (
    APPROVAL_PHRASE,
    create_explicit_approval_gate,
)


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD111ExplicitApprovalGate(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        proposal_id = "d107-valid-test"
        gate_id = "d110-test"

        d110 = {
            "ok": True,
            "decision": "HUMAN_REVIEW_GATE_READY",
            "gate_id": gate_id,
            "runner_id": "d109-test",
            "writer_id": "d108-test",
            "proposal_id": proposal_id,
            "guardrails": {
                "external_ai_called": False,
                "network_accessed": False,
                "api_key_read": False,
                "secret_read": False,
                "shell_from_ai_executed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
                "rollback_executed": False,
                "restore_executed": False,
                "human_review_packet_only": True,
                "approval_granted": False,
                "candidate_execution_allowed": False,
            },
            "summary": {
                "approval_state": "PENDING_HUMAN_DECISION",
                "next_step": "D111_EXPLICIT_APPROVAL_GATE",
            },
        }

        packet = {
            "ok": True,
            "review_mode": "HUMAN_DECISION_PACKET_ONLY",
            "approval_granted": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "human_decision_options": [
                "REJECT_SANDBOX_PROPOSAL",
                "REQUEST_MORE_SANDBOX_EVIDENCE",
                "PREPARE_D111_EXPLICIT_APPROVAL_GATE_ONLY",
            ],
        }

        review_summary = {
            "ok": True,
            "proposal_id": proposal_id,
            "proposal_type": "analysis_proposal",
            "intent": "review sandbox proposal",
            "target_scope": "runtime_experimental/ai_sandbox_work/",
            "candidate_files": ["runtime_experimental/ai_sandbox_work/proposal_manifest.json"],
            "risk_flags": ["proposal_only"],
            "requires_human_review": True,
            "approval_granted": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "protected_core_mutated": False,
            "route_inserted": False,
        }

        approval_record = {
            "ok": True,
            "decision_state": "PENDING_HUMAN_DECISION",
            "approval_granted_now": False,
            "rejection_recorded_now": False,
            "human_phrase_required_for_later_gate": APPROVAL_PHRASE,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }

        d111_scope = {
            "ok": True,
            "allowed_next_gate": "D111_EXPLICIT_APPROVAL_GATE",
            "human_review_required": True,
            "required_phrase_for_later_gate": APPROVAL_PHRASE,
            "actual_apply_allowed_after_d110": False,
            "route_insert_allowed_after_d110": False,
            "protected_core_mutation_allowed_after_d110": False,
            "sandbox_candidate_execution_allowed_after_d110": False,
        }

        write(root / "reports/d110_human_review_gate.json", d110)
        write(root / "reports/d110_human_review_packet.json", packet)
        write(root / "reports/d110_proposal_review_summary.json", review_summary)
        write(root / "reports/d110_approval_or_rejection_record.json", approval_record)
        write(root / "reports/d110_d111_explicit_approval_gate_scope.json", d111_scope)

        return td, root

    def test_creates_explicit_approval_outputs(self):
        td, root = self.root()
        try:
            r = create_explicit_approval_gate(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "EXPLICIT_APPROVAL_GATE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D112_DRY_RUN_APPLY_SCOPE_ONLY")
            self.assertEqual(r["d112_scope"]["allowed_next_gate"], "D112_DRY_RUN_APPLY_SCOPE")
            self.assertTrue(r["guardrails"]["approval_for_d112_dry_run_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertTrue((root / "reports/d111_explicit_approval_gate.json").exists())
            self.assertTrue((root / "reports/d111_explicit_approval_statement.json").exists())
            self.assertTrue((root / "reports/d111_operator_decision_record.json").exists())
            self.assertTrue((root / "reports/d111_d112_dry_run_apply_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_wrong_phrase(self):
        td, root = self.root()
        try:
            r = create_explicit_approval_gate(root, operator_phrase="WRONG")
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_missing_d110(self):
        td, root = self.root()
        try:
            (root / "reports/d110_human_review_gate.json").unlink()
            r = create_explicit_approval_gate(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d110_claims_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d110_human_review_gate.json"
            data = json.loads(p.read_text())
            data["guardrails"]["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_explicit_approval_gate(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_blocked_candidate_path(self):
        td, root = self.root()
        try:
            p = root / "reports/d110_proposal_review_summary.json"
            data = json.loads(p.read_text())
            data["candidate_files"] = ["core/unsafe.py"]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_explicit_approval_gate(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
