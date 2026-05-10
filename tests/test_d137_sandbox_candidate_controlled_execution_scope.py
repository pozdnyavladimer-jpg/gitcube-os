
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_controlled_execution_scope import create_sandbox_candidate_controlled_execution_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD137SandboxCandidateControlledExecutionScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        preflight_id = "d136-test"
        validation_id = "d135-test"
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

        d136 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_EXECUTION_PREFLIGHT_SCOPE_READY",
            "preflight_id": preflight_id,
            "validation_id": validation_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_execution_preflight_scope_only": True,
                "execution_preflight_report_only": True,
                "execution_blockers_only": True,
                "candidate_executed_now": False,
                "approval_for_d137_controlled_execution_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "approval_for_route_insert_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "execution_preflight_status": "PREFLIGHT_PASS_NO_EXECUTION",
                "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_ONLY",
                "next_step": "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE",
            },
        }

        base = f"runtime_experimental/ai_sandbox_work/{candidate_id}"
        preflight_report = {
            "ok": True,
            "preflight_id": preflight_id,
            "candidate_id": candidate_id,
            "preflight_mode": "EXECUTION_PREFLIGHT_ONLY_NO_CANDIDATE_EXECUTION",
            "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
            "materialized_paths": [
                f"{base}/candidate_manifest.json",
                f"{base}/candidate_summary.md",
                f"{base}/candidate_payload.json",
            ],
            "required_checks": [
                {"name": "required_file_candidate_manifest.json", "status": "PREFLIGHT_PASS"},
                {"name": "required_file_candidate_summary.md", "status": "PREFLIGHT_PASS"},
                {"name": "required_file_candidate_payload.json", "status": "PREFLIGHT_PASS"},
            ],
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
        }

        execution_blockers = {
            "ok": True,
            "preflight_id": preflight_id,
            "candidate_id": candidate_id,
            "blocker_mode": "DECLARE_EXECUTION_BOUNDARIES_NO_EXECUTION",
            "still_blocked": [
                "real_apply_by_ai",
                "auto_apply",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "shell_exec_from_ai",
                "git_commit_by_ai",
                "git_push_by_ai",
                "network_provider_call_by_ai",
                "secret_read_by_ai",
            ],
            "candidate_execution_performed": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
        }

        d137_scope = {
            "ok": True,
            "preflight_id": preflight_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D137_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE",
            "sandbox_candidate_controlled_execution_scope_only": True,
            "human_review_required": True,
            "candidate_executed_after_d136_by_ai": False,
            "real_apply_allowed_after_d136_by_ai": False,
            "route_insert_allowed_after_d136_by_ai": False,
            "protected_core_mutation_allowed_after_d136_by_ai": False,
        }

        write(root / "reports/d136_sandbox_candidate_execution_preflight_scope.json", d136)
        write(root / "reports/d136_sandbox_candidate_execution_preflight_report.json", preflight_report)
        write(root / "reports/d136_sandbox_candidate_execution_blockers.json", execution_blockers)
        write(root / "reports/d136_d137_sandbox_candidate_controlled_execution_scope.json", d137_scope)
        return td, root

    def test_creates_controlled_execution_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_controlled_execution_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_READY")
            self.assertEqual(r["summary"]["controlled_execution_scope_status"], "CONTROLLED_EXECUTION_SCOPE_DECLARED_NO_EXECUTION")
            self.assertEqual(r["summary"]["approval_scope"], "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d138_scope"]["allowed_next_gate"], "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE")
            self.assertTrue((root / "reports/d137_sandbox_candidate_controlled_execution_scope.json").exists())
            self.assertTrue((root / "reports/d137_sandbox_candidate_controlled_execution_receipt.json").exists())
            self.assertTrue((root / "reports/d137_sandbox_candidate_no_apply_guard.json").exists())
            self.assertTrue((root / "reports/d137_d138_sandbox_candidate_human_execution_intent_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d136(self):
        td, root = self.root()
        try:
            (root / "reports/d136_sandbox_candidate_execution_preflight_scope.json").unlink()
            r = create_sandbox_candidate_controlled_execution_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_preflight_says_candidate_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d136_sandbox_candidate_execution_preflight_report.json"
            data = json.loads(p.read_text())
            data["candidate_executed_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_controlled_execution_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_blocker_missing_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d136_sandbox_candidate_execution_blockers.json"
            data = json.loads(p.read_text())
            data["still_blocked"].remove("real_apply_by_ai")
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_controlled_execution_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d137_scope_allows_protected_core_mutation(self):
        td, root = self.root()
        try:
            p = root / "reports/d136_d137_sandbox_candidate_controlled_execution_scope.json"
            data = json.loads(p.read_text())
            data["protected_core_mutation_allowed_after_d136_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_controlled_execution_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
