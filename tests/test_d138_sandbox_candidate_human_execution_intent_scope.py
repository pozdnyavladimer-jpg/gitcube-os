
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_human_execution_intent_scope import create_sandbox_candidate_human_execution_intent_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD138SandboxCandidateHumanExecutionIntentScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        scope_id = "d137-test"
        preflight_id = "d136-test"
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

        d137 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_SCOPE_READY",
            "scope_id": scope_id,
            "preflight_id": preflight_id,
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
            "adapter_id": adapter_id,
            "seal_id": seal_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_controlled_execution_scope_only": True,
                "controlled_execution_receipt_only": True,
                "no_apply_guard_only": True,
                "candidate_executed_now": False,
                "approval_for_d138_human_execution_intent_scope_only": True,
                "approval_for_candidate_execution": False,
                "approval_for_real_apply_by_ai": False,
                "approval_for_route_insert_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "controlled_execution_scope_status": "CONTROLLED_EXECUTION_SCOPE_DECLARED_NO_EXECUTION",
                "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_ONLY",
                "next_step": "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE",
            },
        }

        receipt = {
            "ok": True,
            "scope_id": scope_id,
            "preflight_id": preflight_id,
            "candidate_id": candidate_id,
            "receipt_mode": "CONTROLLED_EXECUTION_SCOPE_RECEIPT_NO_EXECUTION",
            "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
            "materialized_paths": [
                f"runtime_experimental/ai_sandbox_work/{candidate_id}/candidate_manifest.json",
                f"runtime_experimental/ai_sandbox_work/{candidate_id}/candidate_summary.md",
                f"runtime_experimental/ai_sandbox_work/{candidate_id}/candidate_payload.json",
            ],
            "allowed_execution_zone": "SANDBOX_ONLY_AFTER_HUMAN_EXECUTION_INTENT",
            "candidate_execution_performed": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "human_review_required": True,
        }

        no_apply_guard = {
            "ok": True,
            "scope_id": scope_id,
            "candidate_id": candidate_id,
            "guard_mode": "NO_APPLY_NO_ROUTE_NO_PROTECTED_MUTATION_GUARD",
            "blocked_actions": [
                "real_apply_by_ai",
                "auto_apply",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "shell_exec_from_ai",
                "git_commit_by_ai",
                "git_push_by_ai",
                "rollback_execute_by_ai",
                "restore_execute_by_ai",
                "network_provider_call_by_ai",
                "secret_read_by_ai",
            ],
            "candidate_execution_allowed_now": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "human_review_required": True,
        }

        d138_scope = {
            "ok": True,
            "scope_id": scope_id,
            "preflight_id": preflight_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D138_SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE",
            "sandbox_candidate_human_execution_intent_scope_only": True,
            "human_review_required": True,
            "candidate_executed_after_d137_by_ai": False,
            "real_apply_allowed_after_d137_by_ai": False,
            "route_insert_allowed_after_d137_by_ai": False,
            "protected_core_mutation_allowed_after_d137_by_ai": False,
        }

        write(root / "reports/d137_sandbox_candidate_controlled_execution_scope.json", d137)
        write(root / "reports/d137_sandbox_candidate_controlled_execution_receipt.json", receipt)
        write(root / "reports/d137_sandbox_candidate_no_apply_guard.json", no_apply_guard)
        write(root / "reports/d137_d138_sandbox_candidate_human_execution_intent_scope.json", d138_scope)
        return td, root

    def test_creates_human_execution_intent_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_human_execution_intent_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_READY")
            self.assertEqual(r["summary"]["human_execution_intent_status"], "HUMAN_INTENT_RECORD_CREATED_NO_EXECUTION")
            self.assertEqual(r["summary"]["approval_scope"], "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d139_scope"]["allowed_next_gate"], "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE")
            self.assertTrue((root / "reports/d138_sandbox_candidate_human_execution_intent_scope.json").exists())
            self.assertTrue((root / "reports/d138_sandbox_candidate_human_execution_intent_record.json").exists())
            self.assertTrue((root / "reports/d138_sandbox_candidate_execution_authority_guard.json").exists())
            self.assertTrue((root / "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d137(self):
        td, root = self.root()
        try:
            (root / "reports/d137_sandbox_candidate_controlled_execution_scope.json").unlink()
            r = create_sandbox_candidate_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_receipt_says_candidate_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d137_sandbox_candidate_controlled_execution_receipt.json"
            data = json.loads(p.read_text())
            data["candidate_executed_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_no_apply_guard_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d137_sandbox_candidate_no_apply_guard.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d138_scope_allows_protected_core_mutation(self):
        td, root = self.root()
        try:
            p = root / "reports/d137_d138_sandbox_candidate_human_execution_intent_scope.json"
            data = json.loads(p.read_text())
            data["protected_core_mutation_allowed_after_d137_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
