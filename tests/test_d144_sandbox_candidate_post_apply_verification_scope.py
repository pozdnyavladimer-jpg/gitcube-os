
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_post_apply_verification_scope import create_sandbox_candidate_post_apply_verification_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD144SandboxCandidatePostApplyVerificationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        apply_id = "d143-test"
        intent_id = "d142-test"
        preflight_id = "d141-test"
        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"
        cdir = root / "runtime_experimental" / "ai_sandbox_work" / candidate_id
        cdir.mkdir(parents=True, exist_ok=True)
        write(cdir / "candidate_manifest.json", {"ok": True, "candidate_id": candidate_id})
        write(cdir / "candidate_payload.json", {"ok": True, "candidate_id": candidate_id})
        (cdir / "candidate_summary.md").write_text("# candidate summary\n", encoding="utf-8")
        write(cdir / "sandbox_execution_result.json", {"ok": True, "candidate_id": candidate_id})
        write(cdir / "sandbox_apply_result.json", {
            "ok": True,
            "apply_id": apply_id,
            "candidate_id": candidate_id,
            "result_mode": "SANDBOX_APPLY_RESULT_ONLY_NO_CORE_MUTATION",
            "sandbox_apply_status": "SANDBOX_APPLY_RESULT_RECORDED",
            "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_RECORDED_NOT_CORE_APPLIED",
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "candidate_executed_now": False,
            "human_review_required": True,
        })

        false_guard = {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False, "secret_read": False,
            "shell_from_ai_executed": False, "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False, "route_inserted": False,
            "git_commit_by_ai": False, "git_push_by_ai": False, "rollback_executed": False, "restore_executed": False,
        }
        d143 = {
            "ok": True, "decision": "SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_READY",
            "apply_id": apply_id, "intent_id": intent_id, "preflight_id": preflight_id,
            "run_id": run_id, "candidate_id": candidate_id, "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_guarded_apply_scope_only": True,
                "guarded_apply_plan_only": True,
                "guarded_apply_receipt_only": True,
                "sandbox_apply_result_written": True,
                "candidate_executed_now": False,
                "approval_for_d144_post_apply_verification_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "approval_for_route_insert_by_ai": False,
                "approval_for_protected_core_mutation_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "guarded_apply_status": "SANDBOX_GUARDED_APPLY_RECORDED_NO_CORE_MUTATION",
                "sandbox_apply_result_status": "CREATED",
                "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_RECORDED_NOT_CORE_APPLIED",
                "execution_result_status": "PRESENT_AND_VALIDATED",
                "real_provider_status": "NOT_CALLED", "network_status": "NOT_ACCESSED", "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED", "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED", "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_ONLY",
                "next_step": "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE",
            },
        }
        apply_plan = {
            "ok": True, "apply_id": apply_id, "candidate_id": candidate_id,
            "plan_mode": "SANDBOX_GUARDED_APPLY_PLAN_WITHOUT_CORE_MUTATION",
            "apply_target_scope": "SANDBOX_EVIDENCE_ONLY",
            "guarded_apply_allowed_by_operator_scope": True,
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "candidate_executed_now": False,
            "human_review_required": True,
        }
        apply_receipt = {
            "ok": True, "apply_id": apply_id, "candidate_id": candidate_id,
            "receipt_mode": "SANDBOX_GUARDED_APPLY_RECEIPT_NO_CORE_MUTATION",
            "sandbox_apply_result_created": True,
            "guarded_apply_status": "SANDBOX_GUARDED_APPLY_RECORDED_NO_CORE_MUTATION",
            "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_RECORDED_NOT_CORE_APPLIED",
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "shell_executed_by_ai": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "candidate_executed_now": False,
            "candidate_executed_by_ai": False,
            "human_review_required": True,
        }
        d144_scope = {
            "ok": True, "apply_id": apply_id, "candidate_id": candidate_id,
            "allowed_next_gate": "D144_SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE",
            "sandbox_candidate_post_apply_verification_scope_only": True,
            "human_review_required": True,
            "sandbox_apply_result_created_after_d143": True,
            "candidate_executed_after_d143_by_ai": False,
            "real_apply_allowed_after_d143_by_ai": False,
            "auto_apply_allowed_after_d143_by_ai": False,
            "route_insert_allowed_after_d143_by_ai": False,
            "protected_core_mutation_allowed_after_d143_by_ai": False,
            "network_allowed_after_d143_by_ai": False,
            "secret_read_allowed_after_d143_by_ai": False,
            "shell_allowed_after_d143_by_ai": False,
            "git_action_allowed_after_d143_by_ai": False,
        }
        write(root / "reports/d143_sandbox_candidate_guarded_apply_scope.json", d143)
        write(root / "reports/d143_sandbox_candidate_guarded_apply_plan.json", apply_plan)
        write(root / "reports/d143_sandbox_candidate_guarded_apply_receipt.json", apply_receipt)
        write(root / "reports/d143_d144_sandbox_candidate_post_apply_verification_scope.json", d144_scope)
        return td, root

    def test_creates_post_apply_verification_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_post_apply_verification_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_READY")
            self.assertEqual(r["summary"]["post_apply_verification_status"], "SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION")
            self.assertEqual(r["summary"]["approval_scope"], "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted"])
            self.assertEqual(r["d145_scope"]["allowed_next_gate"], "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE")
            self.assertTrue((root / "reports/d144_sandbox_candidate_post_apply_verification_scope.json").exists())
            self.assertTrue((root / "reports/d144_sandbox_candidate_post_apply_verification_report.json").exists())
            self.assertTrue((root / "reports/d144_sandbox_candidate_apply_integrity_receipt.json").exists())
            self.assertTrue((root / "reports/d144_d145_sandbox_candidate_final_audit_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d143(self):
        td, root = self.root()
        try:
            (root / "reports/d143_sandbox_candidate_guarded_apply_scope.json").unlink()
            r = create_sandbox_candidate_post_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_apply_plan_says_core_mutated(self):
        td, root = self.root()
        try:
            p = root / "reports/d143_sandbox_candidate_guarded_apply_plan.json"
            data = json.loads(p.read_text())
            data["protected_core_mutated"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_sandbox_apply_result_says_real_apply(self):
        td, root = self.root()
        try:
            p = root / "runtime_experimental/ai_sandbox_work/d126-test/sandbox_apply_result.json"
            data = json.loads(p.read_text())
            data["real_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d144_scope_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d143_d144_sandbox_candidate_post_apply_verification_scope.json"
            data = json.loads(p.read_text())
            data["route_insert_allowed_after_d143_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
