
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_post_write_validation_scope import create_sandbox_candidate_post_write_validation_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


def write_text(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")


class TestD135SandboxCandidatePostWriteValidationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        write_materialization_id = "d134-test"
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
        expected_files = [
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

        d134 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_READY",
            "write_materialization_id": write_materialization_id,
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
                "sandbox_candidate_write_materialization_scope_only": True,
                "write_materialization_receipt_only": True,
                "write_materialization_postcheck_only": True,
                "candidate_files_materialized": True,
                "candidate_files_written_now": True,
                "candidate_files_verified_existing": False,
                "candidate_executed_now": False,
                "approval_for_d135_post_write_validation_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "write_materialization_status": "CANDIDATE_FILES_MATERIALIZED",
                "candidate_status": "MATERIALIZED_NOT_EXECUTED_NOT_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_ONLY",
                "next_step": "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE",
            },
        }

        receipt = {
            "ok": True,
            "write_materialization_id": write_materialization_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "receipt_mode": "SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_RECEIPT_ONLY",
            "allowed_candidate_write_root": candidate_root,
            "candidate_files_expected": expected_files,
            "candidate_files_written_now_paths": expected_files,
            "candidate_files_verified_existing_paths": [],
            "candidate_files_blocked_existing_paths": [],
            "candidate_files_materialized": True,
            "candidate_files_written_now": True,
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

        postcheck = {
            "ok": True,
            "write_materialization_id": write_materialization_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "postcheck_mode": "SANDBOX_CANDIDATE_WRITE_POSTCHECK_NO_EXECUTION_NO_APPLY",
            "allowed_candidate_write_root": candidate_root,
            "candidate_files_existing": expected_files,
            "candidate_files_missing": [],
            "candidate_file_digest_matches": {path: True for path in expected_files},
            "candidate_files_materialized": True,
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

        d135_scope = {
            "ok": True,
            "write_materialization_id": write_materialization_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE",
            "sandbox_candidate_post_write_validation_scope_only": True,
            "human_review_required": True,
            "candidate_executed_after_d134_by_ai": False,
            "real_apply_allowed_after_d134_by_ai": False,
            "route_insert_allowed_after_d134_by_ai": False,
            "protected_core_mutation_allowed_after_d134_by_ai": False,
        }

        manifest = {
            "state": "SANDBOX_CANDIDATE_MATERIALIZED_MANIFEST",
            "ok": True,
            "write_materialization_id": write_materialization_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "candidate_root": candidate_root,
            "candidate_status": "MATERIALIZED_NOT_EXECUTED_NOT_APPLIED",
            "planned_files": expected_files,
            "guardrails": {
                "sandbox_only": True,
                "candidate_executed": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "shell_executed_by_ai": False,
                "git_action_by_ai": False,
                "network_accessed": False,
                "api_key_read": False,
                "secret_read": False,
            },
        }
        payload = {
            "state": "SANDBOX_CANDIDATE_MATERIALIZED_PAYLOAD",
            "ok": True,
            "write_materialization_id": write_materialization_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "payload_mode": "SAFE_SANDBOX_CANDIDATE_PLACEHOLDER_NO_EXECUTION",
            "execution_mode": "NOT_EXECUTED",
            "apply_mode": "NOT_APPLIED",
            "route_insert_mode": "BLOCKED",
            "protected_core_mode": "UNTOUCHED_BY_AI",
            "next_required_gate": "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE",
        }
        summary = "\n".join([
            "# Sandbox Candidate d126-test",
            "",
            "Guardrails:",
            "- no candidate execution",
            "- no real apply",
            "",
        ])

        write(root / "reports/d134_sandbox_candidate_write_materialization_scope.json", d134)
        write(root / "reports/d134_sandbox_candidate_write_materialization_receipt.json", receipt)
        write(root / "reports/d134_sandbox_candidate_write_materialization_postcheck.json", postcheck)
        write(root / "reports/d134_d135_sandbox_candidate_post_write_validation_scope.json", d135_scope)
        write(root / f"{candidate_root}candidate_manifest.json", manifest)
        write_text(root / f"{candidate_root}candidate_summary.md", summary)
        write(root / f"{candidate_root}candidate_payload.json", payload)
        return td, root, candidate_root

    def test_creates_post_write_validation_scope_outputs(self):
        td, root, candidate_root = self.root()
        try:
            r = create_sandbox_candidate_post_write_validation_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_READY")
            self.assertEqual(r["summary"]["candidate_status"], "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED")
            self.assertEqual(r["summary"]["approval_scope"], "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_ONLY")
            self.assertTrue(r["guardrails"]["candidate_files_validated"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d136_scope"]["allowed_next_gate"], "D136_SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE")
            self.assertTrue((root / "reports/d135_sandbox_candidate_post_write_validation_scope.json").exists())
            self.assertTrue((root / "reports/d135_sandbox_candidate_post_write_validation_report.json").exists())
            self.assertTrue((root / "reports/d135_sandbox_candidate_materialized_file_inventory.json").exists())
            self.assertTrue((root / "reports/d135_d136_sandbox_candidate_execution_preflight_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d134(self):
        td, root, candidate_root = self.root()
        try:
            (root / "reports/d134_sandbox_candidate_write_materialization_scope.json").unlink()
            r = create_sandbox_candidate_post_write_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_missing_candidate_file(self):
        td, root, candidate_root = self.root()
        try:
            (root / f"{candidate_root}candidate_payload.json").unlink()
            r = create_sandbox_candidate_post_write_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_manifest_says_executed(self):
        td, root, candidate_root = self.root()
        try:
            p = root / f"{candidate_root}candidate_manifest.json"
            data = json.loads(p.read_text())
            data["guardrails"]["candidate_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_write_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d135_scope_allows_real_apply(self):
        td, root, candidate_root = self.root()
        try:
            p = root / "reports/d134_d135_sandbox_candidate_post_write_validation_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d134_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_write_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
