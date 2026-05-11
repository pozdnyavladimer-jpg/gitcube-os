
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_post_real_apply_verification_scope import create_sandbox_candidate_post_real_apply_verification_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD152SandboxCandidatePostRealApplyVerificationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        run_apply_id = "d151-test"
        signature_id = "d150-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d151 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_READY",
            "run_apply_id": run_apply_id,
            "signature_id": signature_id,
            "preflight_id": "d149-test",
            "intent_id": "d148-test",
            "decision_id": "d147-test",
            "archive_id": "d146-test",
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": {
                "network_accessed": False,
                "secret_read": False,
                "shell_executed_by_ai": False,
                "actual_apply_executed_by_ai": False,
                "real_apply_executed_by_ai": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "protected_core_mutated_by_ai": False,
                "git_action_by_ai": False,
                "sandbox_candidate_guarded_real_apply_run_scope_only": True,
                "real_apply_run_result_only": True,
                "real_apply_run_safety_receipt_only": True,
                "approval_for_d152_post_real_apply_verification_scope_only": True,
                "approval_for_real_core_apply_by_ai": False,
                "real_apply_allowed_after_d151_by_ai": False,
                "route_insert_allowed_after_d151_by_ai": False,
                "protected_core_mutation_allowed_after_d151_by_ai": False,
                "network_allowed_after_d151_by_ai": False,
                "secret_read_allowed_after_d151_by_ai": False,
                "shell_allowed_after_d151_by_ai": False,
                "git_action_allowed_after_d151_by_ai": False,
            },
            "summary": {
                "real_apply_run_status": "GUARDED_REAL_APPLY_RUN_SCOPE_RECORDED_NO_AI_CORE_MUTATION",
                "safety_receipt_status": "AI_DID_NOT_EXECUTE_REAL_CORE_APPLY",
                "candidate_status": "REAL_APPLY_RUN_SCOPE_RECORDED_POST_VERIFICATION_REQUIRED_NOT_CORE_MUTATED_BY_AI",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_ONLY",
                "next_step": "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE",
            },
        }

        run_result = {
            "ok": True,
            "run_apply_id": run_apply_id,
            "real_apply_run_status": "GUARDED_REAL_APPLY_RUN_RECORDED_NO_AI_EXECUTION",
            "operator_authorized_run_scope": True,
            "operator_actual_core_apply_executed": False,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        safety_receipt = {
            "ok": True,
            "run_apply_id": run_apply_id,
            "safety_status": "AI_DID_NOT_EXECUTE_REAL_CORE_APPLY",
            "no_ai_apply": True,
            "no_ai_route_insert": True,
            "no_ai_protected_core_mutation": True,
            "no_ai_network": True,
            "no_ai_secret_read": True,
            "no_ai_shell": True,
            "no_ai_git_action": True,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        d152_scope = {
            "ok": True,
            "run_apply_id": run_apply_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE",
            "sandbox_candidate_post_real_apply_verification_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d151_by_ai": False,
            "route_insert_allowed_after_d151_by_ai": False,
            "protected_core_mutation_allowed_after_d151_by_ai": False,
            "network_allowed_after_d151_by_ai": False,
            "secret_read_allowed_after_d151_by_ai": False,
            "shell_allowed_after_d151_by_ai": False,
            "git_action_allowed_after_d151_by_ai": False,
        }

        write(root / "reports/d151_sandbox_candidate_guarded_real_apply_run_scope.json", d151)
        write(root / "reports/d151_sandbox_candidate_real_apply_run_result.json", run_result)
        write(root / "reports/d151_sandbox_candidate_real_apply_run_safety_receipt.json", safety_receipt)
        write(root / "reports/d151_d152_sandbox_candidate_post_real_apply_verification_scope.json", d152_scope)

        return td, root

    def test_creates_post_real_apply_verification_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_post_real_apply_verification_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["real_apply_executed_by_ai"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertFalse(r["guardrails"]["git_action_by_ai"])
            self.assertEqual(r["d153_scope"]["allowed_next_gate"], "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE")
            self.assertTrue((root / "reports/d152_sandbox_candidate_post_real_apply_verification_scope.json").exists())
            self.assertTrue((root / "reports/d152_sandbox_candidate_real_apply_verification_report.json").exists())
            self.assertTrue((root / "reports/d152_sandbox_candidate_real_apply_integrity_receipt.json").exists())
            self.assertTrue((root / "reports/d152_d153_sandbox_candidate_final_real_apply_audit_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d151(self):
        td, root = self.root()
        try:
            (root / "reports/d151_sandbox_candidate_guarded_real_apply_run_scope.json").unlink()
            r = create_sandbox_candidate_post_real_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d151_summary_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d151_sandbox_candidate_guarded_real_apply_run_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["route_insert_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_real_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_run_result_says_core_mutated_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d151_sandbox_candidate_real_apply_run_result.json"
            data = json.loads(p.read_text())
            data["protected_core_mutated_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_real_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d152_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d151_d152_sandbox_candidate_post_real_apply_verification_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d151_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_post_real_apply_verification_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
