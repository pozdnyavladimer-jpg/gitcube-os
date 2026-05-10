
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_static_validation_scope import create_sandbox_candidate_static_validation_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD132SandboxCandidateStaticValidationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

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

        d131 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_WRITE_ONCE_SCOPE_READY",
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
                "sandbox_candidate_write_once_scope_only": True,
                "write_once_manifest_only": True,
                "materialized_preview_only": True,
                "candidate_files_written_now": False,
                "candidate_executed_now": False,
                "approval_for_d132_static_validation_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "write_once_status": "WRITE_ONCE_SCOPE_ARMED_NOT_USED",
                "materialized_preview_status": "PREVIEW_CREATED_NO_CANDIDATE_WRITE",
                "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_ONLY",
                "next_step": "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE",
            },
        }

        write_once_manifest = {
            "ok": True,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "manifest_mode": "WRITE_ONCE_MANIFEST_ONLY_NO_CANDIDATE_WRITE",
            "write_once_status": "WRITE_ONCE_SCOPE_ARMED_NOT_USED",
            "allowed_candidate_write_root": candidate_root,
            "planned_candidate_files_for_later_gate": planned_files,
            "write_once_policy": {
                "candidate_root_only": True,
                "single_materialization_window": True,
                "no_overwrite_existing_candidate_files": True,
                "hash_preview_before_write": True,
                "no_execution_after_write": True,
                "no_apply_after_write": True,
                "no_route_insert_after_write": True,
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

        materialized_preview = {
            "ok": True,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "preview_mode": "MATERIALIZED_PREVIEW_ONLY_NO_CANDIDATE_WRITE",
            "allowed_candidate_write_root": candidate_root,
            "preview_files": [
                {"path": planned_files[0], "role": "candidate_manifest.json", "planned_for_later_write_gate": True, "written_now": False, "preview_digest": "aaaabbbbcccc1111"},
                {"path": planned_files[1], "role": "candidate_summary.md", "planned_for_later_write_gate": True, "written_now": False, "preview_digest": "dddd111122223333"},
                {"path": planned_files[2], "role": "candidate_payload.json", "planned_for_later_write_gate": True, "written_now": False, "preview_digest": "eeee444455556666"},
            ],
            "preview_digest": "preview-digest-test",
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

        d132_scope = {
            "ok": True,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D132_SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE",
            "sandbox_candidate_static_validation_scope_only": True,
            "human_review_required": True,
            "candidate_written_after_d131": False,
            "candidate_executed_after_d131_by_ai": False,
            "real_apply_allowed_after_d131_by_ai": False,
            "route_insert_allowed_after_d131_by_ai": False,
            "protected_core_mutation_allowed_after_d131_by_ai": False,
        }

        write(root / "reports/d131_sandbox_candidate_write_once_scope.json", d131)
        write(root / "reports/d131_sandbox_candidate_write_once_manifest.json", write_once_manifest)
        write(root / "reports/d131_sandbox_candidate_materialized_preview.json", materialized_preview)
        write(root / "reports/d131_d132_sandbox_candidate_static_validation_scope.json", d132_scope)
        return td, root

    def test_creates_static_validation_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_static_validation_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_STATIC_VALIDATION_SCOPE_READY")
            self.assertEqual(r["summary"]["static_validation_status"], "STATIC_VALIDATION_PASS_NO_WRITE")
            self.assertEqual(r["summary"]["approval_scope"], "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_files_written_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d133_scope"]["allowed_next_gate"], "D133_SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE")
            self.assertTrue((root / "reports/d132_sandbox_candidate_static_validation_scope.json").exists())
            self.assertTrue((root / "reports/d132_sandbox_candidate_static_validation_report.json").exists())
            self.assertTrue((root / "reports/d132_sandbox_candidate_path_boundary_report.json").exists())
            self.assertTrue((root / "reports/d132_d133_sandbox_candidate_materialization_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d131(self):
        td, root = self.root()
        try:
            (root / "reports/d131_sandbox_candidate_write_once_scope.json").unlink()
            r = create_sandbox_candidate_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_materialized_preview_says_candidate_written(self):
        td, root = self.root()
        try:
            p = root / "reports/d131_sandbox_candidate_materialized_preview.json"
            data = json.loads(p.read_text())
            data["candidate_files_written_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_preview_path_leaves_candidate_root(self):
        td, root = self.root()
        try:
            p = root / "reports/d131_sandbox_candidate_materialized_preview.json"
            data = json.loads(p.read_text())
            data["preview_files"][0]["path"] = "core/unsafe.py"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d132_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d131_d132_sandbox_candidate_static_validation_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d131_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
