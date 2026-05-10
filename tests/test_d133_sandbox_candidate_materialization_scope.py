
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_materialization_scope import create_sandbox_candidate_materialization_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD133SandboxCandidateMaterializationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        static_validation_id = "d132-test"
        write_once_id = "d131-test"
        window_id = "d130-test"
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
        candidate_root = f"runtime_experimental/ai_sandbox_work/{candidate_id}/"
        planned_files = [
            f"{candidate_root}candidate_manifest.json",
            f"{candidate_root}candidate_summary.md",
            f"{candidate_root}candidate_payload.json",
        ]

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

        d132 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_READY",
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "window_id": window_id,
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
                "sandbox_candidate_static_validation_scope_only": True,
                "static_validation_report_only": True,
                "path_boundary_report_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d133_materialization_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "static_validation_status": "STATIC_VALIDATION_PASS_NO_WRITE",
                "path_boundary_status": "STATIC_PATH_BOUNDARY_PASS_NO_SCAN",
                "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_ONLY",
                "next_step": "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE",
            },
        }

        static_validation_report = {
            "ok": True,
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "validation_mode": "STATIC_VALIDATION_ONLY_NO_CANDIDATE_WRITE_EXECUTION",
            "static_validation_status": "PASS_STATIC_ONLY",
            "allowed_candidate_write_root": candidate_root,
            "planned_candidate_files": planned_files,
            "preview_files_count": 3,
            "preview_digest": "preview-digest-test",
            "checks": {
                "write_once_manifest_present": True,
                "materialized_preview_present": True,
                "candidate_root_safe": True,
                "planned_paths_under_candidate_root": True,
                "preview_paths_under_candidate_root": True,
                "preview_matches_planned_count": True,
                "candidate_not_written": True,
                "candidate_not_executed": True,
                "real_apply_blocked": True,
                "route_insert_blocked": True,
                "protected_core_untouched": True,
                "no_shell": True,
                "no_network": True,
                "no_secret_read": True,
            },
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "human_review_required": True,
        }

        path_boundary_report = {
            "ok": True,
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "boundary_mode": "PATH_BOUNDARY_STATIC_ONLY_NO_FILESYSTEM_SCAN",
            "boundary_status": "STATIC_PATH_BOUNDARY_PASS",
            "allowed_candidate_write_root": candidate_root,
            "static_paths_checked": planned_files,
            "blocked_paths": [],
            "protected_targets": ["app/orchestration/", "core/", "runtime/", "bridges/", "memory/"],
            "protected_targets_status": {
                "app/orchestration/": "OUT_OF_CANDIDATE_WRITE_SCOPE",
                "core/": "OUT_OF_CANDIDATE_WRITE_SCOPE",
                "runtime/": "OUT_OF_CANDIDATE_WRITE_SCOPE",
                "bridges/": "OUT_OF_CANDIDATE_WRITE_SCOPE",
                "memory/": "OUT_OF_CANDIDATE_WRITE_SCOPE",
            },
            "filesystem_scan_executed": False,
            "git_diff_executed": False,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "human_review_required": True,
        }

        d133_scope = {
            "ok": True,
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE",
            "sandbox_candidate_materialization_scope_only": True,
            "human_review_required": True,
            "candidate_written_after_d132": False,
            "candidate_executed_after_d132_by_ai": False,
            "real_apply_allowed_after_d132_by_ai": False,
            "route_insert_allowed_after_d132_by_ai": False,
            "protected_core_mutation_allowed_after_d132_by_ai": False,
        }

        write(root / "reports/d132_sandbox_candidate_static_validation_scope.json", d132)
        write(root / "reports/d132_sandbox_candidate_static_validation_report.json", static_validation_report)
        write(root / "reports/d132_sandbox_candidate_path_boundary_report.json", path_boundary_report)
        write(root / "reports/d132_d133_sandbox_candidate_materialization_scope.json", d133_scope)
        return td, root

    def test_creates_materialization_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_materialization_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_READY")
            self.assertEqual(r["summary"]["materialization_status"], "MATERIALIZATION_SCOPE_DECLARED_NOT_WRITTEN")
            self.assertEqual(r["summary"]["approval_scope"], "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d134_scope"]["allowed_next_gate"], "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE")
            self.assertTrue((root / "reports/d133_sandbox_candidate_materialization_scope.json").exists())
            self.assertTrue((root / "reports/d133_sandbox_candidate_materialization_manifest.json").exists())
            self.assertTrue((root / "reports/d133_sandbox_candidate_materialization_preflight.json").exists())
            self.assertTrue((root / "reports/d133_d134_sandbox_candidate_write_materialization_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d132(self):
        td, root = self.root()
        try:
            (root / "reports/d132_sandbox_candidate_static_validation_scope.json").unlink()
            r = create_sandbox_candidate_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_static_validation_check_fails(self):
        td, root = self.root()
        try:
            p = root / "reports/d132_sandbox_candidate_static_validation_report.json"
            data = json.loads(p.read_text())
            data["checks"]["no_network"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_path_boundary_has_blocked_path(self):
        td, root = self.root()
        try:
            p = root / "reports/d132_sandbox_candidate_path_boundary_report.json"
            data = json.loads(p.read_text())
            data["blocked_paths"] = ["core/unsafe.py"]
            data["ok"] = False
            data["boundary_status"] = "STATIC_PATH_BOUNDARY_BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d133_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d132_d133_sandbox_candidate_materialization_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d132_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
