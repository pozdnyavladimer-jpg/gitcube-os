
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_guarded_real_apply_run_scope import create_sandbox_candidate_guarded_real_apply_run_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD151SandboxCandidateGuardedRealApplyRunScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        signature_id = "d150-test"
        preflight_id = "d149-test"
        intent_id = "d148-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d150 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_READY",
            "signature_id": signature_id,
            "preflight_id": preflight_id,
            "intent_id": intent_id,
            "decision_id": "d147-test",
            "archive_id": "d146-test",
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": {
                "network_accessed": False,
                "secret_read": False,
                "shell_executed_by_ai": False,
                "actual_apply_executed": False,
                "real_apply_executed": False,
                "route_inserted": False,
                "protected_core_mutated": False,
                "git_action_by_ai": False,
                "sandbox_candidate_human_signed_real_apply_execution_scope_only": True,
                "human_signed_real_apply_signature_record_only": True,
                "real_apply_execution_authority_guard_only": True,
                "approval_for_d151_guarded_real_apply_run_scope_only": True,
                "approval_for_real_core_apply_now": False,
                "real_apply_allowed_after_d150_by_ai": False,
                "route_insert_allowed_after_d150_by_ai": False,
                "protected_core_mutation_allowed_after_d150_by_ai": False,
                "network_allowed_after_d150_by_ai": False,
                "secret_read_allowed_after_d150_by_ai": False,
                "shell_allowed_after_d150_by_ai": False,
                "git_action_allowed_after_d150_by_ai": False,
            },
            "summary": {
                "human_signed_real_apply_status": "HUMAN_SIGNED_REAL_APPLY_SCOPE_RECORDED_NO_REAL_APPLY",
                "real_apply_execution_authority_status": "REAL_APPLY_EXECUTION_AUTHORITY_GUARD_CREATED_NO_REAL_APPLY",
                "candidate_status": "SANDBOX_CHAIN_READY_FOR_GUARDED_REAL_APPLY_RUN_SCOPE_NOT_CORE_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_ONLY",
                "next_step": "D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE",
            },
        }

        signature_record = {
            "ok": True,
            "signature_id": signature_id,
            "signature_mode": "HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_RECORD_ONLY_NO_REAL_APPLY",
            "approved_for_d151_guarded_real_apply_run_scope_only": True,
            "approved_for_real_core_apply_now": False,
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        authority_guard = {
            "ok": True,
            "signature_id": signature_id,
            "authority_mode": "HUMAN_SIGNED_REAL_APPLY_EXECUTION_AUTHORITY_GUARD_ONLY_NO_REAL_APPLY",
            "allow_d151_guarded_real_apply_run_scope": True,
            "allow_real_core_apply_now": False,
            "allow_route_insert": False,
            "allow_protected_core_mutation": False,
            "allow_network": False,
            "allow_secret_read": False,
            "allow_shell_exec": False,
            "allow_git_action_by_ai": False,
            "real_apply_allowed_after_d150_by_ai": False,
            "route_insert_allowed_after_d150_by_ai": False,
            "protected_core_mutation_allowed_after_d150_by_ai": False,
            "network_allowed_after_d150_by_ai": False,
            "secret_read_allowed_after_d150_by_ai": False,
            "shell_allowed_after_d150_by_ai": False,
            "git_action_allowed_after_d150_by_ai": False,
        }

        d151_scope = {
            "ok": True,
            "signature_id": signature_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE",
            "sandbox_candidate_guarded_real_apply_run_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d150_by_ai": False,
            "route_insert_allowed_after_d150_by_ai": False,
            "protected_core_mutation_allowed_after_d150_by_ai": False,
            "network_allowed_after_d150_by_ai": False,
            "secret_read_allowed_after_d150_by_ai": False,
            "shell_allowed_after_d150_by_ai": False,
            "git_action_allowed_after_d150_by_ai": False,
        }

        write(root / "reports/d150_sandbox_candidate_human_signed_real_apply_execution_scope.json", d150)
        write(root / "reports/d150_sandbox_candidate_real_apply_signature_record.json", signature_record)
        write(root / "reports/d150_sandbox_candidate_real_apply_execution_authority_guard.json", authority_guard)
        write(root / "reports/d150_d151_sandbox_candidate_guarded_real_apply_run_scope.json", d151_scope)

        return td, root

    def test_creates_guarded_real_apply_run_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_guarded_real_apply_run_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertEqual(r["d152_scope"]["allowed_next_gate"], "D152_SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE")
            self.assertTrue((root / "reports/d151_sandbox_candidate_guarded_real_apply_run_scope.json").exists())
            self.assertTrue((root / "reports/d151_sandbox_candidate_real_apply_run_result.json").exists())
            self.assertTrue((root / "reports/d151_sandbox_candidate_real_apply_run_safety_receipt.json").exists())
            self.assertTrue((root / "reports/d151_d152_sandbox_candidate_post_real_apply_verification_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d150(self):
        td, root = self.root()
        try:
            (root / "reports/d150_sandbox_candidate_human_signed_real_apply_execution_scope.json").unlink()
            r = create_sandbox_candidate_guarded_real_apply_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d150_summary_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d150_sandbox_candidate_human_signed_real_apply_execution_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["route_insert_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_real_apply_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_signature_record_says_real_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d150_sandbox_candidate_real_apply_signature_record.json"
            data = json.loads(p.read_text())
            data["real_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_real_apply_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d151_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d150_d151_sandbox_candidate_guarded_real_apply_run_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d150_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_real_apply_run_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
