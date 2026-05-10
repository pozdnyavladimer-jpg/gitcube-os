
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_human_review_scope import create_sandbox_candidate_human_review_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD127SandboxCandidateHumanReviewScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        candidate_id = "d126-test"
        intake_id = "d125-test"
        ping_id = "d124-test"
        config_id = "d123-test"
        dashboard_id = "d122-test"
        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        d126 = {
            "ok": True,
            "decision": "PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_READY",
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
                "proposal_to_sandbox_candidate_scope_only": True,
                "sandbox_write_plan_only": True,
                "static_scan_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d127_human_review_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "sandbox_candidate_status": "PLAN_CREATED_NOT_WRITTEN_NOT_EXECUTED",
                "static_scan_status": "PASS",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "approval_scope": "D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_ONLY",
                "next_step": "D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE",
            },
        }

        write_plan = {
            "ok": True,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "plan_mode": "SANDBOX_CANDIDATE_PLAN_ONLY_NO_EXECUTION",
            "candidate_root": f"runtime_experimental/ai_sandbox_work/{candidate_id}/",
            "planned_files": [
                {"path": f"runtime_experimental/ai_sandbox_work/{candidate_id}/candidate_manifest.json"},
                {"path": f"runtime_experimental/ai_sandbox_work/{candidate_id}/candidate_summary.md"},
            ],
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "human_review_required": True,
        }

        static_scan = {
            "ok": True,
            "candidate_id": candidate_id,
            "scan_mode": "STATIC_PLAN_SCAN_ONLY_NO_EXECUTION",
            "allowed_prefixes_ok": True,
            "blocked_prefix_hits": [],
            "forbidden_marker_hits": [],
            "errors": [],
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        d127_scope = {
            "ok": True,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE",
            "sandbox_candidate_human_review_scope_only": True,
            "human_review_required": True,
            "static_scan_ok": True,
            "candidate_written_after_d126": False,
            "candidate_executed_after_d126_by_ai": False,
            "real_apply_allowed_after_d126_by_ai": False,
            "route_insert_allowed_after_d126_by_ai": False,
            "protected_core_mutation_allowed_after_d126_by_ai": False,
        }

        write(root / "reports/d126_proposal_to_sandbox_candidate_scope.json", d126)
        write(root / "reports/d126_sandbox_candidate_write_plan.json", write_plan)
        write(root / "reports/d126_sandbox_candidate_static_scan.json", static_scan)
        write(root / "reports/d126_d127_sandbox_candidate_human_review_scope.json", d127_scope)

        return td, root

    def test_creates_human_review_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_human_review_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_READY")
            self.assertEqual(r["summary"]["review_status"], "PENDING_HUMAN_REVIEW_PACKET_CREATED")
            self.assertEqual(r["summary"]["approval_scope"], "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d128_scope"]["allowed_next_gate"], "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE")
            self.assertTrue((root / "reports/d127_sandbox_candidate_human_review_scope.json").exists())
            self.assertTrue((root / "reports/d127_sandbox_candidate_review_packet.json").exists())
            self.assertTrue((root / "reports/d127_sandbox_candidate_approval_or_rejection_record.json").exists())
            self.assertTrue((root / "reports/d127_d128_sandbox_candidate_test_plan_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d126(self):
        td, root = self.root()
        try:
            (root / "reports/d126_proposal_to_sandbox_candidate_scope.json").unlink()
            r = create_sandbox_candidate_human_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_static_scan_failed(self):
        td, root = self.root()
        try:
            p = root / "reports/d126_sandbox_candidate_static_scan.json"
            data = json.loads(p.read_text())
            data["ok"] = False
            data["errors"] = ["bad candidate"]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_write_plan_says_candidate_written(self):
        td, root = self.root()
        try:
            p = root / "reports/d126_sandbox_candidate_write_plan.json"
            data = json.loads(p.read_text())
            data["candidate_files_written_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d127_scope_allows_execution(self):
        td, root = self.root()
        try:
            p = root / "reports/d126_d127_sandbox_candidate_human_review_scope.json"
            data = json.loads(p.read_text())
            data["candidate_executed_after_d126_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_review_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
