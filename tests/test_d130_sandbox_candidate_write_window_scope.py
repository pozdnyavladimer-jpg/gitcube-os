
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_write_window_scope import create_sandbox_candidate_write_window_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD130SandboxCandidateWriteWindowScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        runner_id = "d129-test"
        plan_id = "d128-test"
        review_id = "d127-test"
        candidate_id = "d126-test"
        intake_id = "d125-test"
        ping_id = "d124-test"
        config_id = "d123-test"
        dashboard_id = "d122-test"
        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        false_guard = {
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
        }

        d129 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_READY",
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "intake_id": intake_id,
            "ping_id": ping_id,
            "config_id": config_id,
            "dashboard_id": dashboard_id,
            "adapter_id": adapter_id,
            "seal_id": seal_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_dry_test_runner_scope_only": True,
                "dry_test_results_only": True,
                "integrity_diff_summary_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d130_write_window_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "dry_test_status": "DRY_RESULTS_CREATED_NOT_EXECUTED",
                "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
                "integrity_status": "NO_TOUCH_ASSERTIONS_HELD_BY_SCOPE",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "approval_scope": "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_ONLY",
                "next_step": "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE",
            },
        }

        dry_results = {
            "ok": True,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "candidate_id": candidate_id,
            "results_mode": "DRY_TEST_RESULTS_ONLY_NO_CANDIDATE_EXECUTION",
            "test_groups_total": 4,
            "test_groups_dry_passed": 4,
            "checks": [
                {"name": "schema_and_manifest_checks", "status": "DRY_PASS", "dry_only": True, "candidate_executed": False, "actual_apply_executed": False},
                {"name": "path_boundary_checks", "status": "DRY_PASS", "dry_only": True, "candidate_executed": False, "actual_apply_executed": False},
                {"name": "no_touch_assertions", "status": "DRY_PASS", "dry_only": True, "candidate_executed": False, "actual_apply_executed": False},
                {"name": "no_execution_assertions", "status": "DRY_PASS", "dry_only": True, "candidate_executed": False, "actual_apply_executed": False},
            ],
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "human_review_required": True,
        }

        integrity_diff = {
            "ok": True,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "candidate_id": candidate_id,
            "summary_mode": "DECLARED_NO_TOUCH_DIFF_SUMMARY_NO_GIT_DIFF_EXECUTION",
            "git_diff_executed": False,
            "filesystem_scan_executed": False,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "protected_targets": ["app/orchestration/", "core/", "runtime/", "bridges/", "memory/"],
            "protected_targets_status": {
                "app/orchestration/": "NO_TOUCH_ASSERTED",
                "core/": "NO_TOUCH_ASSERTED",
                "runtime/": "NO_TOUCH_ASSERTED",
                "bridges/": "NO_TOUCH_ASSERTED",
                "memory/": "NO_TOUCH_ASSERTED",
            },
            "integrity_status": "NO_TOUCH_ASSERTIONS_HELD_BY_SCOPE",
            "human_review_required": True,
        }

        d130_scope = {
            "ok": True,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE",
            "sandbox_candidate_write_window_scope_only": True,
            "human_review_required": True,
            "candidate_written_after_d129": False,
            "candidate_executed_after_d129_by_ai": False,
            "real_apply_allowed_after_d129_by_ai": False,
            "route_insert_allowed_after_d129_by_ai": False,
            "protected_core_mutation_allowed_after_d129_by_ai": False,
        }

        write(root / "reports/d129_sandbox_candidate_dry_test_runner_scope.json", d129)
        write(root / "reports/d129_sandbox_candidate_dry_test_results.json", dry_results)
        write(root / "reports/d129_sandbox_candidate_integrity_diff_summary.json", integrity_diff)
        write(root / "reports/d129_d130_sandbox_candidate_write_window_scope.json", d130_scope)
        return td, root

    def test_creates_write_window_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_write_window_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_READY")
            self.assertEqual(r["summary"]["write_window_status"], "WRITE_WINDOW_SCOPE_OPENED_NOT_USED")
            self.assertEqual(r["summary"]["approval_scope"], "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d131_scope"]["allowed_next_gate"], "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE")
            self.assertTrue((root / "reports/d130_sandbox_candidate_write_window_scope.json").exists())
            self.assertTrue((root / "reports/d130_sandbox_candidate_write_window_manifest.json").exists())
            self.assertTrue((root / "reports/d130_sandbox_candidate_write_preflight.json").exists())
            self.assertTrue((root / "reports/d130_d131_sandbox_candidate_write_once_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d129(self):
        td, root = self.root()
        try:
            (root / "reports/d129_sandbox_candidate_dry_test_runner_scope.json").unlink()
            r = create_sandbox_candidate_write_window_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_dry_results_say_candidate_written(self):
        td, root = self.root()
        try:
            p = root / "reports/d129_sandbox_candidate_dry_test_results.json"
            data = json.loads(p.read_text())
            data["candidate_files_written_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_write_window_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_integrity_diff_executed_git_diff(self):
        td, root = self.root()
        try:
            p = root / "reports/d129_sandbox_candidate_integrity_diff_summary.json"
            data = json.loads(p.read_text())
            data["git_diff_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_write_window_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d130_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d129_d130_sandbox_candidate_write_window_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d129_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_write_window_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
