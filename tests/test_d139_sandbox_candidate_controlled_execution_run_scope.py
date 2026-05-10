
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_controlled_execution_run_scope import create_sandbox_candidate_controlled_execution_run_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD139SandboxCandidateControlledExecutionRunScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

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

        d138 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_READY",
            "intent_id": "d138-test",
            "scope_id": "d137-test",
            "preflight_id": "d136-test",
            "validation_id": "d135-test",
            "write_materialization_id": "d134-test",
            "materialization_id": "d133-test",
            "static_validation_id": "d132-test",
            "write_once_id": "d131-test",
            "window_id": "d130-test",
            "runner_id": "d129-test",
            "plan_id": "d128-test",
            "review_id": "d127-test",
            "candidate_id": candidate_id,
            "adapter_id": "d121-test",
            "seal_id": "d120-test",
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_human_execution_intent_scope_only": True,
                "human_execution_intent_record_only": True,
                "execution_authority_guard_only": True,
                "candidate_executed_now": False,
                "approval_for_d139_controlled_execution_run_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "human_execution_intent_status": "HUMAN_INTENT_RECORD_CREATED_NO_EXECUTION",
                "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_ONLY",
                "next_step": "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE",
            },
        }

        intent_record = {
            "ok": True,
            "record_mode": "HUMAN_EXECUTION_INTENT_RECORD_ONLY_NO_EXECUTION",
            "candidate_id": candidate_id,
            "required_phrase_for_d139": "APPROVE_D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_ONLY",
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "human_review_required": True,
        }

        authority_guard = {
            "ok": True,
            "authority_mode": "EXECUTION_AUTHORITY_GUARD_ONLY_NO_EXECUTION",
            "candidate_id": candidate_id,
            "allow_d139_controlled_sandbox_execution": True,
            "allow_real_apply": False,
            "allow_route_insert": False,
            "allow_protected_core_mutation": False,
            "allow_network": False,
            "allow_secret_read": False,
            "allow_shell_exec": False,
            "allow_git_action_by_ai": False,
            "human_review_required": True,
        }

        d139_scope = {
            "ok": True,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE",
            "sandbox_candidate_controlled_execution_run_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d138_by_ai": False,
            "route_insert_allowed_after_d138_by_ai": False,
            "protected_core_mutation_allowed_after_d138_by_ai": False,
            "network_allowed_after_d138": False,
            "secret_read_allowed_after_d138": False,
            "shell_allowed_after_d138_by_ai": False,
            "git_action_allowed_after_d138_by_ai": False,
        }

        write(root / "reports/d138_sandbox_candidate_human_execution_intent_scope.json", d138)
        write(root / "reports/d138_sandbox_candidate_human_execution_intent_record.json", intent_record)
        write(root / "reports/d138_sandbox_candidate_execution_authority_guard.json", authority_guard)
        write(root / "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json", d139_scope)

        cdir = root / "runtime_experimental" / "ai_sandbox_work" / candidate_id
        cdir.mkdir(parents=True, exist_ok=True)
        write(cdir / "candidate_manifest.json", {
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "mode": "SANDBOX_CANDIDATE",
        })
        write(cdir / "candidate_payload.json", {
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "payload_mode": "DECLARATIVE_SANDBOX_PAYLOAD",
            "planned_effect": "report_only",
        })
        (cdir / "candidate_summary.md").write_text("# Candidate Summary\n\nSandbox candidate.\n", encoding="utf-8")

        return td, root, candidate_id

    def test_creates_controlled_execution_run_outputs(self):
        td, root, candidate_id = self.root()
        try:
            r = create_sandbox_candidate_controlled_execution_run_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_READY")
            self.assertEqual(r["summary"]["execution_status"], "SANDBOX_CONTROLLED_EXECUTION_COMPLETED")
            self.assertEqual(r["summary"]["candidate_status"], "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED")
            self.assertTrue(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["candidate_executed_by_ai"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d140_scope"]["allowed_next_gate"], "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE")
            self.assertTrue((root / "reports/d139_sandbox_candidate_controlled_execution_run_scope.json").exists())
            self.assertTrue((root / "reports/d139_sandbox_candidate_execution_run_result.json").exists())
            self.assertTrue((root / "reports/d139_sandbox_candidate_execution_safety_receipt.json").exists())
            self.assertTrue((root / "reports/d139_d140_sandbox_candidate_post_execution_verification_scope.json").exists())
            self.assertTrue((root / "runtime_experimental/ai_sandbox_work" / candidate_id / "sandbox_execution_result.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d138(self):
        td, root, _candidate_id = self.root()
        try:
            (root / "reports/d138_sandbox_candidate_human_execution_intent_scope.json").unlink()
            r = create_sandbox_candidate_controlled_execution_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d138_not_ready(self):
        td, root, _candidate_id = self.root()
        try:
            p = root / "reports/d138_sandbox_candidate_human_execution_intent_scope.json"
            data = json.loads(p.read_text())
            data["decision"] = "BLOCKED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_controlled_execution_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_candidate_payload_missing(self):
        td, root, candidate_id = self.root()
        try:
            (root / "runtime_experimental/ai_sandbox_work" / candidate_id / "candidate_payload.json").unlink()
            r = create_sandbox_candidate_controlled_execution_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d139_scope_allows_real_apply(self):
        td, root, _candidate_id = self.root()
        try:
            p = root / "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d138_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_controlled_execution_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
