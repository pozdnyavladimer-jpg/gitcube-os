
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_guarded_apply_scope import create_sandbox_candidate_guarded_apply_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD143SandboxCandidateGuardedApplyScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        intent_id = "d142-test"
        preflight_id = "d141-test"
        verification_id = "d140-test"
        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"
        cdir = root / "runtime_experimental" / "ai_sandbox_work" / candidate_id
        cdir.mkdir(parents=True, exist_ok=True)
        write(cdir / "candidate_manifest.json", {"ok": True, "candidate_id": candidate_id})
        write(cdir / "candidate_payload.json", {"ok": True, "candidate_id": candidate_id})
        (cdir / "candidate_summary.md").write_text("# candidate summary\n", encoding="utf-8")
        write(cdir / "sandbox_execution_result.json", {"ok": True, "candidate_id": candidate_id})

        false_guard = {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False, "secret_read": False,
            "shell_from_ai_executed": False, "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False, "route_inserted": False,
            "git_commit_by_ai": False, "git_push_by_ai": False, "rollback_executed": False, "restore_executed": False,
        }
        d142 = {
            "ok": True, "decision": "SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_READY",
            "intent_id": intent_id, "preflight_id": preflight_id, "verification_id": verification_id,
            "run_id": run_id, "candidate_id": candidate_id, "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_human_apply_intent_scope_only": True,
                "human_apply_intent_record_only": True,
                "apply_authority_guard_only": True,
                "candidate_executed_now": False,
                "approval_for_d143_guarded_apply_scope_only": True,
                "approval_for_real_apply_now": False,
                "approval_for_real_apply_by_ai": False,
                "approval_for_route_insert_by_ai": False,
                "approval_for_protected_core_mutation_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "human_apply_intent_status": "HUMAN_APPLY_INTENT_RECORD_CREATED_NO_APPLY",
                "apply_authority_status": "APPLY_AUTHORITY_GUARD_CREATED_NO_APPLY",
                "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
                "execution_result_status": "PRESENT_AND_VALIDATED",
                "real_provider_status": "NOT_CALLED", "network_status": "NOT_ACCESSED", "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED", "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED", "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_ONLY",
                "next_step": "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE",
            },
        }
        intent_record = {
            "ok": True, "intent_id": intent_id, "candidate_id": candidate_id,
            "record_mode": "HUMAN_APPLY_INTENT_RECORD_ONLY_NO_APPLY",
            "operator_decision": "PENDING_HUMAN_APPLY_INTENT_FOR_D143",
            "approved_for_d143_guarded_apply_scope_only": True,
            "approved_for_real_apply_now": False,
            "approved_for_real_apply_by_ai": False,
            "approved_for_auto_apply": False,
            "approved_for_route_insert": False,
            "approved_for_protected_core_mutation": False,
            "approved_for_git_action_by_ai": False,
            "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
            "candidate_execution_performed_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "real_apply_executed": False,
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
        authority_guard = {
            "ok": True, "intent_id": intent_id, "candidate_id": candidate_id,
            "authority_mode": "SANDBOX_GUARDED_APPLY_AUTHORITY_GUARD_ONLY",
            "guard_mode": "SANDBOX_GUARDED_APPLY_AUTHORITY_GUARD_ONLY",
            "guarded_apply_allowed_now": False,
            "guarded_apply_allowed_next_gate_only": True,
            "real_apply_allowed_now": False,
            "real_apply_allowed_by_ai": False,
            "auto_apply_allowed": False,
            "candidate_execution_performed_now": False,
            "candidate_executed_now": False,
            "actual_apply_executed": False,
            "real_apply_executed": False,
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
        d143_scope = {
            "ok": True, "intent_id": intent_id, "candidate_id": candidate_id,
            "allowed_next_gate": "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE",
            "sandbox_candidate_guarded_apply_scope_only": True,
            "human_review_required": True,
            "candidate_executed_in_sandbox_after_d139": True,
            "candidate_executed_after_d142_by_ai": False,
            "guarded_apply_allowed_after_d142_operator_only": True,
            "real_apply_allowed_after_d142_by_ai": False,
            "auto_apply_allowed_after_d142_by_ai": False,
            "route_insert_allowed_after_d142_by_ai": False,
            "protected_core_mutation_allowed_after_d142_by_ai": False,
            "network_allowed_after_d142_by_ai": False,
            "secret_read_allowed_after_d142_by_ai": False,
            "shell_allowed_after_d142_by_ai": False,
            "git_action_allowed_after_d142_by_ai": False,
        }
        write(root / "reports/d142_sandbox_candidate_human_apply_intent_scope.json", d142)
        write(root / "reports/d142_sandbox_candidate_human_apply_intent_record.json", intent_record)
        write(root / "reports/d142_sandbox_candidate_apply_authority_guard.json", authority_guard)
        write(root / "reports/d142_d143_sandbox_candidate_guarded_apply_scope.json", d143_scope)
        return td, root

    def test_creates_guarded_apply_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_guarded_apply_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_READY")
            self.assertEqual(r["summary"]["guarded_apply_status"], "SANDBOX_GUARDED_APPLY_RECORDED_NO_CORE_MUTATION")
            self.assertEqual(r["summary"]["approval_scope"], "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted"])
            self.assertEqual(r["d144_scope"]["allowed_next_gate"], "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE")
            self.assertTrue((root / "reports/d143_sandbox_candidate_guarded_apply_scope.json").exists())
            self.assertTrue((root / "reports/d143_sandbox_candidate_guarded_apply_plan.json").exists())
            self.assertTrue((root / "reports/d143_sandbox_candidate_guarded_apply_receipt.json").exists())
            self.assertTrue((root / "reports/d143_d144_sandbox_candidate_post_apply_verification_scope.json").exists())
            self.assertTrue((root / "runtime_experimental/ai_sandbox_work/d126-test/sandbox_apply_result.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d142(self):
        td, root = self.root()
        try:
            (root / "reports/d142_sandbox_candidate_human_apply_intent_scope.json").unlink()
            r = create_sandbox_candidate_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_intent_record_says_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d142_sandbox_candidate_human_apply_intent_record.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_authority_guard_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d142_sandbox_candidate_apply_authority_guard.json"
            data = json.loads(p.read_text())
            data["network_accessed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d143_scope_allows_core_mutation(self):
        td, root = self.root()
        try:
            p = root / "reports/d142_d143_sandbox_candidate_guarded_apply_scope.json"
            data = json.loads(p.read_text())
            data["protected_core_mutation_allowed_after_d142_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_apply_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
