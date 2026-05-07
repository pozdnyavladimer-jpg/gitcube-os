
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.final_execution_approval_request import create_final_execution_approval_request


def write(path, data):
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD94FinalExecutionApprovalRequest(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d93_dry_run_recheck_gate.json", {
            "ok": True,
            "decision": "DRY_RUN_RECHECK_GATE_READY",
            "gate_id": "d93-test",
            "package_id": "d92-test",
            "guardrails": {
                "external_ai_called": False,
                "network_accessed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
                "dry_run_recheck_only": True,
                "commands_executed_by_d93": False,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d93_recheck_results.json", {
            "ok": True,
            "verified_conditions": {
                "actual_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "external_ai_called": False,
                "network_accessed": False,
                "git_commit_by_ai": False,
            },
            "commands_executed_by_d93": [],
        })

        write(root / "reports/d93_apply_still_blocked.json", {
            "ok": True,
            "apply_allowed_now": False,
            "route_insert_allowed_now": False,
            "protected_core_mutation_allowed_now": False,
            "canonical_memory_mutation_allowed_now": False,
            "external_ai_call_allowed_now": False,
            "git_action_by_ai_allowed_now": False,
            "next_required_gate": "D94_FINAL_EXECUTION_APPROVAL_REQUEST",
        })

        write(root / "reports/d93_d94_execution_gate_scope.json", {
            "ok": True,
            "allowed_next_gate": "D94_FINAL_EXECUTION_APPROVAL_REQUEST",
            "d94_allowed_to_create": [
                "final_execution_approval_request",
                "explicit_human_execution_phrase",
                "final_apply_blockers_report",
            ],
            "d94_must_not_execute": [
                "actual_apply",
                "route_insert",
                "protected_core_mutation",
                "canonical_memory_overwrite",
                "external_ai_network_call",
                "git_commit_or_push_by_ai",
            ],
            "apply_allowed_after_d93": False,
            "route_insert_allowed_after_d93": False,
            "protected_core_mutation_allowed_after_d93": False,
            "human_review_required": True,
            "required_phrase_for_later_gate": "APPROVE_D94_FINAL_EXECUTION_REQUEST_REVIEW_ONLY",
        })

        return td, root

    def test_creates_final_execution_request_only(self):
        td, root = self.root()
        try:
            r = create_final_execution_approval_request(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "FINAL_EXECUTION_APPROVAL_REQUEST_READY")
            self.assertTrue(r["guardrails"]["final_execution_request_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertTrue(r["guardrails"]["human_review_required"])
            self.assertEqual(r["approval_request"]["allowed_next_gate_if_reviewed"], "D95_HUMAN_SIGNED_EXECUTION_INTENT")
            self.assertTrue((root / "reports/d94_final_execution_approval_request.json").exists())
            self.assertTrue((root / "reports/d94_explicit_human_execution_phrase.json").exists())
            self.assertTrue((root / "reports/d94_final_apply_blockers_report.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d93(self):
        td, root = self.root()
        try:
            (root / "reports/d93_dry_run_recheck_gate.json").unlink()
            r = create_final_execution_approval_request(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "FINAL_EXECUTION_APPROVAL_REQUEST_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_d93_approves_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d93_dry_run_recheck_gate.json"
            data = json.loads(p.read_text())
            data["guardrails"]["approval_for_real_apply"] = True
            p.write_text(json.dumps(data))
            r = create_final_execution_approval_request(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
