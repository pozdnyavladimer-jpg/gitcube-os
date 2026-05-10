
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_dry_test_runner_scope import create_sandbox_candidate_dry_test_runner_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD129SandboxCandidateDryTestRunnerScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

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

        d128 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_READY",
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
                "sandbox_candidate_test_plan_scope_only": True,
                "test_matrix_only": True,
                "no_touch_assertions_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d129_dry_test_runner_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "test_plan_status": "PLAN_CREATED_NOT_RUN",
                "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
                "no_touch_status": "ASSERTIONS_CREATED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "approval_scope": "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_ONLY",
                "next_step": "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE",
            },
        }

        test_matrix = {
            "ok": True,
            "plan_id": plan_id,
            "candidate_id": candidate_id,
            "matrix_mode": "TEST_PLAN_ONLY_NO_EXECUTION",
            "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
            "test_groups": [
                {"name": "schema_and_manifest_checks", "dry_only": True},
                {"name": "path_boundary_checks", "dry_only": True},
                {"name": "no_touch_assertions", "dry_only": True},
                {"name": "no_execution_assertions", "dry_only": True},
            ],
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "human_review_required": True,
        }

        no_touch = {
            "ok": True,
            "plan_id": plan_id,
            "candidate_id": candidate_id,
            "assertion_mode": "NO_TOUCH_ASSERTIONS_ONLY_NO_EXECUTION",
            "no_touch_targets": ["app/orchestration/", "core/", "runtime/", "bridges/", "memory/"],
            "must_remain_false": {
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "external_ai_called": False,
                "network_accessed": False,
                "api_key_read": False,
                "secret_read": False,
                "shell_from_ai_executed": False,
                "git_commit_by_ai": False,
                "git_push_by_ai": False,
                "rollback_executed": False,
                "restore_executed": False,
            },
            "human_review_required": True,
        }

        d129_scope = {
            "ok": True,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D129_SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE",
            "sandbox_candidate_dry_test_runner_scope_only": True,
            "human_review_required": True,
            "candidate_written_after_d128": False,
            "candidate_executed_after_d128_by_ai": False,
            "real_apply_allowed_after_d128_by_ai": False,
            "route_insert_allowed_after_d128_by_ai": False,
            "protected_core_mutation_allowed_after_d128_by_ai": False,
        }

        write(root / "reports/d128_sandbox_candidate_test_plan_scope.json", d128)
        write(root / "reports/d128_sandbox_candidate_test_matrix.json", test_matrix)
        write(root / "reports/d128_sandbox_candidate_no_touch_assertions.json", no_touch)
        write(root / "reports/d128_d129_sandbox_candidate_dry_test_runner_scope.json", d129_scope)
        return td, root

    def test_creates_dry_test_runner_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_dry_test_runner_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_DRY_TEST_RUNNER_SCOPE_READY")
            self.assertEqual(r["summary"]["dry_test_status"], "DRY_RESULTS_CREATED_NOT_EXECUTED")
            self.assertEqual(r["summary"]["approval_scope"], "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d130_scope"]["allowed_next_gate"], "D130_SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE")
            self.assertTrue((root / "reports/d129_sandbox_candidate_dry_test_runner_scope.json").exists())
            self.assertTrue((root / "reports/d129_sandbox_candidate_dry_test_results.json").exists())
            self.assertTrue((root / "reports/d129_sandbox_candidate_integrity_diff_summary.json").exists())
            self.assertTrue((root / "reports/d129_d130_sandbox_candidate_write_window_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d128(self):
        td, root = self.root()
        try:
            (root / "reports/d128_sandbox_candidate_test_plan_scope.json").unlink()
            r = create_sandbox_candidate_dry_test_runner_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_test_matrix_says_candidate_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d128_sandbox_candidate_test_matrix.json"
            data = json.loads(p.read_text())
            data["candidate_executed_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_dry_test_runner_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_no_touch_assertion_breaks(self):
        td, root = self.root()
        try:
            p = root / "reports/d128_sandbox_candidate_no_touch_assertions.json"
            data = json.loads(p.read_text())
            data["must_remain_false"]["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_dry_test_runner_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d129_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d128_d129_sandbox_candidate_dry_test_runner_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d128_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_dry_test_runner_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
