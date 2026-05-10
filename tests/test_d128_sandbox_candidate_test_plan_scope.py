
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_test_plan_scope import create_sandbox_candidate_test_plan_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD128SandboxCandidateTestPlanScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        review_id = "d127-test"
        candidate_id = "d126-test"
        intake_id = "d125-test"
        ping_id = "d124-test"
        config_id = "d123-test"
        dashboard_id = "d122-test"
        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        d127 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_READY",
            "review_id": review_id,
            "candidate_id": candidate_id,
            "intake_id": intake_id,
            "ping_id": ping_id,
            "config_id": config_id,
            "dashboard_id": dashboard_id,
            "adapter_id": adapter_id,
            "seal_id": seal_id,
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
                "git_push_by_ai": False,
                "rollback_executed": False,
                "restore_executed": False,
                "sandbox_candidate_human_review_scope_only": True,
                "review_packet_only": True,
                "approval_record_template_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d128_test_plan_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "review_status": "PENDING_HUMAN_REVIEW_PACKET_CREATED",
                "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
                "static_scan_status": "PASS",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "approval_scope": "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_ONLY",
                "next_step": "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE",
            },
        }

        review_packet = {
            "ok": True,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "packet_mode": "HUMAN_REVIEW_PACKET_ONLY_NO_EXECUTION",
            "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
            "planned_files": [
                {"path": f"runtime_experimental/ai_sandbox_work/{candidate_id}/candidate_manifest.json"},
                {"path": f"runtime_experimental/ai_sandbox_work/{candidate_id}/candidate_summary.md"},
            ],
            "static_scan_ok": True,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "human_review_required": True,
        }

        approval_record = {
            "ok": True,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "record_mode": "REVIEW_RECORD_TEMPLATE_ONLY",
            "operator_decision": "PENDING_HUMAN_REVIEW",
            "approved_for_d128_test_plan_scope_now": True,
            "approved_for_candidate_execution": False,
            "approved_for_real_apply": False,
            "approved_for_route_insert": False,
            "approved_for_protected_core_mutation": False,
            "approved_for_git_action_by_ai": False,
            "human_review_required": True,
        }

        d128_scope = {
            "ok": True,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE",
            "sandbox_candidate_test_plan_scope_only": True,
            "human_review_required": True,
            "candidate_written_after_d127": False,
            "candidate_executed_after_d127_by_ai": False,
            "real_apply_allowed_after_d127_by_ai": False,
            "route_insert_allowed_after_d127_by_ai": False,
            "protected_core_mutation_allowed_after_d127_by_ai": False,
        }

        write(root / "reports/d127_sandbox_candidate_human_review_scope.json", d127)
        write(root / "reports/d127_sandbox_candidate_review_packet.json", review_packet)
        write(root / "reports/d127_sandbox_candidate_approval_or_rejection_record.json", approval_record)
        write(root / "reports/d127_d128_sandbox_candidate_test_plan_scope.json", d128_scope)

        return td, root

    def test_creates_test_plan_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_test_plan_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_READY")
            self.assertEqual(r["summary"]["test_plan_status"], "PLAN_CREATED_NOT_RUN")
            self.assertEqual(r["summary"]["approval_scope"], "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d129_scope"]["allowed_next_gate"], "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE")
            self.assertTrue((root / "reports/d128_sandbox_candidate_test_plan_scope.json").exists())
            self.assertTrue((root / "reports/d128_sandbox_candidate_test_matrix.json").exists())
            self.assertTrue((root / "reports/d128_sandbox_candidate_no_touch_assertions.json").exists())
            self.assertTrue((root / "reports/d128_d129_sandbox_candidate_dry_test_runner_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d127(self):
        td, root = self.root()
        try:
            (root / "reports/d127_sandbox_candidate_human_review_scope.json").unlink()
            r = create_sandbox_candidate_test_plan_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_review_packet_says_candidate_written(self):
        td, root = self.root()
        try:
            p = root / "reports/d127_sandbox_candidate_review_packet.json"
            data = json.loads(p.read_text())
            data["candidate_files_written_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_test_plan_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_approval_record_allows_execution(self):
        td, root = self.root()
        try:
            p = root / "reports/d127_sandbox_candidate_approval_or_rejection_record.json"
            data = json.loads(p.read_text())
            data["approved_for_candidate_execution"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_test_plan_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d128_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d127_d128_sandbox_candidate_test_plan_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d127_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_test_plan_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
