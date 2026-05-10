
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_execution_preflight_scope import create_sandbox_candidate_execution_preflight_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD136SandboxCandidateExecutionPreflightScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        validation_id = "d135-test"
        write_materialization_id = "d134-test"
        materialization_id = "d133-test"
        static_validation_id = "d132-test"
        write_once_id = "d131-test"
        window_id = "d130-test"
        runner_id = "d129-test"
        plan_id = "d128-test"
        review_id = "d127-test"
        candidate_id = "d126-test"
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

        d135 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_READY",
            "validation_id": validation_id,
            "write_materialization_id": write_materialization_id,
            "materialization_id": materialization_id,
            "static_validation_id": static_validation_id,
            "write_once_id": write_once_id,
            "window_id": window_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_post_write_validation_scope_only": True,
                "post_write_validation_report_only": True,
                "materialized_file_inventory_only": True,
                "candidate_executed_now": False,
                "approval_for_d136_execution_preflight_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "post_write_validation_status": "POST_WRITE_VALIDATION_PASS_NO_EXECUTION",
                "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_ONLY",
                "next_step": "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE",
            },
        }

        validation_report = {
            "ok": True,
            "validation_id": validation_id,
            "candidate_id": candidate_id,
            "validation_status": "POST_WRITE_VALIDATION_PASS_NO_EXECUTION",
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
        }

        base = f"runtime_experimental/ai_sandbox_work/{candidate_id}"
        inventory = {
            "ok": True,
            "validation_id": validation_id,
            "candidate_id": candidate_id,
            "files": [
                {"path": f"{base}/candidate_manifest.json"},
                {"path": f"{base}/candidate_summary.md"},
                {"path": f"{base}/candidate_payload.json"},
            ],
            "candidate_executed_now": False,
            "actual_apply_executed": False,
        }

        d136_scope = {
            "ok": True,
            "validation_id": validation_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE",
            "sandbox_candidate_execution_preflight_scope_only": True,
            "human_review_required": True,
            "candidate_executed_after_d135_by_ai": False,
            "real_apply_allowed_after_d135_by_ai": False,
            "route_insert_allowed_after_d135_by_ai": False,
            "protected_core_mutation_allowed_after_d135_by_ai": False,
        }

        write(root / "reports/d135_sandbox_candidate_post_write_validation_scope.json", d135)
        write(root / "reports/d135_sandbox_candidate_post_write_validation_report.json", validation_report)
        write(root / "reports/d135_sandbox_candidate_materialized_file_inventory.json", inventory)
        write(root / "reports/d135_d136_sandbox_candidate_execution_preflight_scope.json", d136_scope)
        return td, root

    def test_creates_execution_preflight_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_execution_preflight_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_READY")
            self.assertEqual(r["summary"]["execution_preflight_status"], "PREFLIGHT_PASS_NO_EXECUTION")
            self.assertEqual(r["summary"]["approval_scope"], "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d137_scope"]["allowed_next_gate"], "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE")
            self.assertTrue((root / "reports/d136_sandbox_candidate_execution_preflight_scope.json").exists())
            self.assertTrue((root / "reports/d136_sandbox_candidate_execution_preflight_report.json").exists())
            self.assertTrue((root / "reports/d136_sandbox_candidate_execution_blockers.json").exists())
            self.assertTrue((root / "reports/d136_d137_sandbox_candidate_controlled_execution_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d135(self):
        td, root = self.root()
        try:
            (root / "reports/d135_sandbox_candidate_post_write_validation_scope.json").unlink()
            r = create_sandbox_candidate_execution_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_validation_report_says_execution_happened(self):
        td, root = self.root()
        try:
            p = root / "reports/d135_sandbox_candidate_post_write_validation_report.json"
            data = json.loads(p.read_text())
            data["candidate_executed_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_execution_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_inventory_path_leaves_sandbox(self):
        td, root = self.root()
        try:
            p = root / "reports/d135_sandbox_candidate_materialized_file_inventory.json"
            data = json.loads(p.read_text())
            data["files"][0]["path"] = "core/unsafe_candidate_manifest.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_execution_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d136_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d135_d136_sandbox_candidate_execution_preflight_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d135_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_execution_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
