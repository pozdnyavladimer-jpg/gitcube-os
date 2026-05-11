
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_final_real_apply_audit_scope import create_sandbox_candidate_final_real_apply_audit_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD153SandboxCandidateFinalRealApplyAuditScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        verification_id = "d152-test"
        run_apply_id = "d151-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d152 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_POST_REAL_APPLY_VERIFICATION_SCOPE_READY",
            "verification_id": verification_id,
            "run_apply_id": run_apply_id,
            "signature_id": "d150-test",
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
                "route_inserted_by_ai": False,
                "protected_core_mutated": False,
                "protected_core_mutated_by_ai": False,
                "git_action_by_ai": False,
                "sandbox_candidate_post_real_apply_verification_scope_only": True,
                "real_apply_verification_report_only": True,
                "real_apply_integrity_receipt_only": True,
                "approval_for_d153_final_real_apply_audit_scope_only": True,
                "real_apply_allowed_after_d152_by_ai": False,
                "route_insert_allowed_after_d152_by_ai": False,
                "protected_core_mutation_allowed_after_d152_by_ai": False,
                "network_allowed_after_d152_by_ai": False,
                "secret_read_allowed_after_d152_by_ai": False,
                "shell_allowed_after_d152_by_ai": False,
                "git_action_allowed_after_d152_by_ai": False,
            },
            "summary": {
                "verification_status": "REAL_APPLY_RUN_SCOPE_VERIFIED_NO_AI_CORE_MUTATION",
                "integrity_status": "NO_AI_CORE_MUTATION_VERIFIED",
                "candidate_status": "POST_REAL_APPLY_VERIFICATION_READY_FOR_FINAL_AUDIT_NOT_CORE_MUTATED_BY_AI",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_ONLY",
                "next_step": "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE",
            },
        }

        verification_report = {
            "ok": True,
            "verification_id": verification_id,
            "verification_status": "REAL_APPLY_RUN_SCOPE_VERIFIED_NO_AI_CORE_MUTATION",
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

        integrity_receipt = {
            "ok": True,
            "verification_id": verification_id,
            "integrity_status": "NO_AI_CORE_MUTATION_VERIFIED",
            "ai_apply_status": "BLOCKED",
            "ai_route_insert_status": "BLOCKED",
            "ai_protected_core_status": "UNTOUCHED_BY_AI",
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

        d153_scope = {
            "ok": True,
            "verification_id": verification_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D153_SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE",
            "sandbox_candidate_final_real_apply_audit_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d152_by_ai": False,
            "route_insert_allowed_after_d152_by_ai": False,
            "protected_core_mutation_allowed_after_d152_by_ai": False,
            "network_allowed_after_d152_by_ai": False,
            "secret_read_allowed_after_d152_by_ai": False,
            "shell_allowed_after_d152_by_ai": False,
            "git_action_allowed_after_d152_by_ai": False,
        }

        write(root / "reports/d152_sandbox_candidate_post_real_apply_verification_scope.json", d152)
        write(root / "reports/d152_sandbox_candidate_real_apply_verification_report.json", verification_report)
        write(root / "reports/d152_sandbox_candidate_real_apply_integrity_receipt.json", integrity_receipt)
        write(root / "reports/d152_d153_sandbox_candidate_final_real_apply_audit_scope.json", d153_scope)
        return td, root

    def test_creates_final_real_apply_audit_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_final_real_apply_audit_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["real_apply_executed_by_ai"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertFalse(r["guardrails"]["git_action_by_ai"])
            self.assertEqual(r["d154_scope"]["allowed_next_gate"], "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE")
            self.assertTrue((root / "reports/d153_sandbox_candidate_final_real_apply_audit_scope.json").exists())
            self.assertTrue((root / "reports/d153_sandbox_candidate_real_apply_audit_ledger.json").exists())
            self.assertTrue((root / "reports/d153_sandbox_candidate_real_apply_replay_index.json").exists())
            self.assertTrue((root / "reports/d153_d154_sandbox_candidate_real_apply_chain_archive_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d152(self):
        td, root = self.root()
        try:
            (root / "reports/d152_sandbox_candidate_post_real_apply_verification_scope.json").unlink()
            r = create_sandbox_candidate_final_real_apply_audit_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d152_summary_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d152_sandbox_candidate_post_real_apply_verification_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["route_insert_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_final_real_apply_audit_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_integrity_receipt_says_core_mutated_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d152_sandbox_candidate_real_apply_integrity_receipt.json"
            data = json.loads(p.read_text())
            data["protected_core_mutated_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_final_real_apply_audit_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d153_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d152_d153_sandbox_candidate_final_real_apply_audit_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d152_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_final_real_apply_audit_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
