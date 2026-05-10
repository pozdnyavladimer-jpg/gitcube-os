
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_write_materialization_scope import create_sandbox_candidate_write_materialization_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD134SandboxCandidateWriteMaterializationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        materialization_id = "d133-test"
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

        d133 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_READY",
            "materialization_id": materialization_id,
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
                "sandbox_candidate_materialization_scope_only": True,
                "materialization_manifest_only": True,
                "materialization_preflight_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d134_write_materialization_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "materialization_status": "MATERIALIZATION_SCOPE_DECLARED_NOT_WRITTEN",
                "materialization_preflight_status": "MATERIALIZATION_PREFLIGHT_PASS_NO_WRITE",
                "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_ONLY",
                "next_step": "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE",
            },
        }

        materialization_manifest = {
            "ok": True,
            "materialization_id": materialization_id,
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "manifest_mode": "MATERIALIZATION_MANIFEST_ONLY_NO_CANDIDATE_WRITE",
            "materialization_status": "MATERIALIZATION_SCOPE_DECLARED_NOT_WRITTEN",
            "allowed_candidate_write_root": candidate_root,
            "planned_materialization_files": planned_files,
            "materialization_policy": {
                "static_validation_required": True,
                "path_boundary_required": True,
                "candidate_root_only": True,
                "write_materialization_next_gate_only": True,
                "single_materialization_attempt": True,
                "no_overwrite_existing_candidate_files": True,
                "no_execution_after_materialization": True,
                "no_apply_after_materialization": True,
                "no_route_insert_after_materialization": True,
                "human_review_required": True,
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

        materialization_preflight = {
            "ok": True,
            "materialization_id": materialization_id,
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "preflight_mode": "MATERIALIZATION_PREFLIGHT_ONLY_NO_FILESYSTEM_WRITE",
            "preflight_status": "MATERIALIZATION_PREFLIGHT_PASS_NO_WRITE",
            "allowed_candidate_write_root": candidate_root,
            "planned_materialization_files": planned_files,
            "checks": {
                "d132_static_validation_scope_ready": True,
                "static_validation_report_passed": True,
                "path_boundary_report_passed": True,
                "candidate_root_safe": True,
                "planned_files_present": True,
                "planned_paths_under_candidate_root": True,
                "no_blocked_paths": True,
                "candidate_not_written": True,
                "candidate_not_executed": True,
                "real_apply_blocked": True,
                "route_insert_blocked": True,
                "protected_core_untouched": True,
                "no_shell": True,
                "no_network": True,
                "no_secret_read": True,
            },
            "filesystem_write_executed": False,
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

        d134_scope = {
            "ok": True,
            "materialization_id": materialization_id,
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE",
            "sandbox_candidate_write_materialization_scope_only": True,
            "human_review_required": True,
            "candidate_written_after_d133": False,
            "candidate_executed_after_d133_by_ai": False,
            "real_apply_allowed_after_d133_by_ai": False,
            "route_insert_allowed_after_d133_by_ai": False,
            "protected_core_mutation_allowed_after_d133_by_ai": False,
        }

        write(root / "reports/d133_sandbox_candidate_materialization_scope.json", d133)
        write(root / "reports/d133_sandbox_candidate_materialization_manifest.json", materialization_manifest)
        write(root / "reports/d133_sandbox_candidate_materialization_preflight.json", materialization_preflight)
        write(root / "reports/d133_d134_sandbox_candidate_write_materialization_scope.json", d134_scope)
        return td, root, candidate_root, planned_files

    def test_creates_write_materialization_scope_outputs_and_candidate_files(self):
        td, root, candidate_root, planned_files = self.root()
        try:
            r = create_sandbox_candidate_write_materialization_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_READY")
            self.assertEqual(r["summary"]["candidate_status"], "MATERIALIZED_NOT_EXECUTED_NOT_APPLIED")
            self.assertEqual(r["summary"]["approval_scope"], "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_ONLY")
            self.assertTrue(r["guardrails"]["candidate_files_materialized"])
            self.assertTrue(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d135_scope"]["allowed_next_gate"], "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE")
            self.assertTrue((root / "reports/d134_sandbox_candidate_write_materialization_scope.json").exists())
            self.assertTrue((root / "reports/d134_sandbox_candidate_write_materialization_receipt.json").exists())
            self.assertTrue((root / "reports/d134_sandbox_candidate_write_materialization_postcheck.json").exists())
            self.assertTrue((root / "reports/d134_d135_sandbox_candidate_post_write_validation_scope.json").exists())
            for path in planned_files:
                self.assertTrue((root / path).exists())
        finally:
            td.cleanup()

    def test_idempotent_rerun_verifies_existing_candidate_files(self):
        td, root, candidate_root, planned_files = self.root()
        try:
            first = create_sandbox_candidate_write_materialization_scope(root)
            self.assertTrue(first["ok"])
            second = create_sandbox_candidate_write_materialization_scope(root)
            self.assertTrue(second["ok"])
            self.assertFalse(second["guardrails"]["candidate_files_written_now"])
            self.assertTrue(second["guardrails"]["candidate_files_verified_existing"])
            self.assertEqual(second["summary"]["write_materialization_status"], "CANDIDATE_FILES_ALREADY_MATERIALIZED_VERIFIED")
        finally:
            td.cleanup()

    def test_blocks_missing_d133(self):
        td, root, candidate_root, planned_files = self.root()
        try:
            (root / "reports/d133_sandbox_candidate_materialization_scope.json").unlink()
            r = create_sandbox_candidate_write_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_preflight_says_network(self):
        td, root, candidate_root, planned_files = self.root()
        try:
            p = root / "reports/d133_sandbox_candidate_materialization_preflight.json"
            data = json.loads(p.read_text())
            data["checks"]["no_network"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_write_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_existing_candidate_file_differs(self):
        td, root, candidate_root, planned_files = self.root()
        try:
            p = root / planned_files[0]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("different", encoding="utf-8")
            r = create_sandbox_candidate_write_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
