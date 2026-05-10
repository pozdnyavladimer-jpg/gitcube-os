
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_write_once_scope import create_sandbox_candidate_write_once_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD131SandboxCandidateWriteOnceScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

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

        d130 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_WRITE_WINDOW_SCOPE_READY",
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
                "sandbox_candidate_write_window_scope_only": True,
                "write_window_manifest_only": True,
                "write_preflight_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d131_write_once_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "write_window_status": "WRITE_WINDOW_SCOPE_OPENED_NOT_USED",
                "write_preflight_status": "WRITE_PREFLIGHT_CREATED_NO_WRITE",
                "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_ONLY",
                "next_step": "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE",
            },
        }

        write_window_manifest = {
            "ok": True,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "manifest_mode": "WRITE_WINDOW_MANIFEST_ONLY_NO_CANDIDATE_WRITE",
            "write_window_status": "OPENED_FOR_D131_SCOPE_ONLY_NOT_USED",
            "allowed_candidate_write_root": candidate_root,
            "planned_candidate_files_for_later_gate": [
                f"{candidate_root}candidate_manifest.json",
                f"{candidate_root}candidate_summary.md",
                f"{candidate_root}candidate_payload.json",
            ],
            "write_policy": {
                "write_once_only_after_d131_gate": True,
                "candidate_root_only": True,
                "no_overwrite_without_later_gate": True,
                "no_execution_after_write": True,
                "no_apply_after_write": True,
                "human_review_required": True,
            },
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

        write_preflight = {
            "ok": True,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "preflight_mode": "WRITE_WINDOW_PREFLIGHT_ONLY_NO_CANDIDATE_WRITE",
            "preflight_status": "PASS_SCOPE_ONLY",
            "input_checks": {
                "d129_report_ready": True,
                "dry_results_ready": True,
                "integrity_diff_ready": True,
                "dry_results_no_execution": True,
                "integrity_no_git_diff_execution": True,
                "integrity_no_filesystem_scan_execution": True,
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

        d131_scope = {
            "ok": True,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D131_SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE",
            "sandbox_candidate_write_once_scope_only": True,
            "human_review_required": True,
            "candidate_written_after_d130": False,
            "candidate_executed_after_d130_by_ai": False,
            "real_apply_allowed_after_d130_by_ai": False,
            "route_insert_allowed_after_d130_by_ai": False,
            "protected_core_mutation_allowed_after_d130_by_ai": False,
        }

        write(root / "reports/d130_sandbox_candidate_write_window_scope.json", d130)
        write(root / "reports/d130_sandbox_candidate_write_window_manifest.json", write_window_manifest)
        write(root / "reports/d130_sandbox_candidate_write_preflight.json", write_preflight)
        write(root / "reports/d130_d131_sandbox_candidate_write_once_scope.json", d131_scope)
        return td, root

    def test_creates_write_once_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_write_once_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_READY")
            self.assertEqual(r["summary"]["write_once_status"], "WRITE_ONCE_SCOPE_ARMED_NOT_USED")
            self.assertEqual(r["summary"]["approval_scope"], "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d132_scope"]["allowed_next_gate"], "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE")
            self.assertTrue((root / "reports/d131_sandbox_candidate_write_once_scope.json").exists())
            self.assertTrue((root / "reports/d131_sandbox_candidate_write_once_manifest.json").exists())
            self.assertTrue((root / "reports/d131_sandbox_candidate_materialized_preview.json").exists())
            self.assertTrue((root / "reports/d131_d132_sandbox_candidate_static_validation_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d130(self):
        td, root = self.root()
        try:
            (root / "reports/d130_sandbox_candidate_write_window_scope.json").unlink()
            r = create_sandbox_candidate_write_once_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_write_window_manifest_says_candidate_written(self):
        td, root = self.root()
        try:
            p = root / "reports/d130_sandbox_candidate_write_window_manifest.json"
            data = json.loads(p.read_text())
            data["candidate_files_written_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_write_once_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_write_preflight_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d130_sandbox_candidate_write_preflight.json"
            data = json.loads(p.read_text())
            data["route_inserted"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_write_once_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d131_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d130_d131_sandbox_candidate_write_once_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d130_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_write_once_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
