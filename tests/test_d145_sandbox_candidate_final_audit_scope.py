
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_final_audit_scope import create_sandbox_candidate_final_audit_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD145SandboxCandidateFinalAuditScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        verification_id = "d144-test"
        apply_id = "d143-test"
        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"
        cdir = root / "runtime_experimental" / "ai_sandbox_work" / candidate_id
        cdir.mkdir(parents=True, exist_ok=True)
        for name in ["candidate_manifest.json", "candidate_payload.json", "sandbox_execution_result.json", "sandbox_apply_result.json"]:
            write(cdir / name, {"ok": True, "name": name})
        (cdir / "candidate_summary.md").write_text("# candidate\n", encoding="utf-8")

        false_guard = {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False,
            "secret_read": False, "shell_from_ai_executed": False,
            "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False,
            "route_inserted": False, "git_commit_by_ai": False, "git_push_by_ai": False,
            "rollback_executed": False, "restore_executed": False,
        }
        d144 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_POST_APPLY_VERIFICATION_SCOPE_READY",
            "verification_id": verification_id,
            "apply_id": apply_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_post_apply_verification_scope_only": True,
                "post_apply_verification_report_only": True,
                "apply_integrity_receipt_only": True,
                "candidate_executed_now": False,
                "approval_for_d145_final_audit_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "approval_for_route_insert_by_ai": False,
                "approval_for_protected_core_mutation_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "post_apply_verification_status": "SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION",
                "sandbox_apply_integrity_status": "SANDBOX_APPLY_EVIDENCE_PRESENT_AND_VALIDATED",
                "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_NOT_CORE_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_ONLY",
                "next_step": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE",
            },
        }
        post_apply_report = {
            "ok": True,
            "verification_id": verification_id,
            "candidate_id": candidate_id,
            "report_mode": "POST_SANDBOX_APPLY_VERIFICATION_ONLY_NO_CORE_MUTATION",
            "post_apply_verification_status": "SANDBOX_APPLY_VERIFIED_NO_CORE_MUTATION",
            "sandbox_apply_result_present": True,
            "sandbox_apply_result_ok": True,
            "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_NOT_CORE_APPLIED",
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "real_core_apply_executed": False,
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
        integrity = {
            "ok": True,
            "verification_id": verification_id,
            "candidate_id": candidate_id,
            "receipt_mode": "SANDBOX_APPLY_INTEGRITY_RECEIPT_NO_CORE_MUTATION",
            "candidate_files_all_present": True,
            "sandbox_apply_integrity_status": "SANDBOX_APPLY_EVIDENCE_PRESENT_AND_VALIDATED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "route_insert_status": "BLOCKED",
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "real_core_apply_executed": False,
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
        d145_scope = {
            "ok": True,
            "verification_id": verification_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE",
            "sandbox_candidate_final_audit_scope_only": True,
            "sandbox_apply_verified_after_d144": True,
            "human_review_required": True,
            "candidate_executed_after_d144_by_ai": False,
            "real_apply_allowed_after_d144_by_ai": False,
            "auto_apply_allowed_after_d144_by_ai": False,
            "route_insert_allowed_after_d144_by_ai": False,
            "protected_core_mutation_allowed_after_d144_by_ai": False,
            "network_allowed_after_d144_by_ai": False,
            "secret_read_allowed_after_d144_by_ai": False,
            "shell_allowed_after_d144_by_ai": False,
            "git_action_allowed_after_d144_by_ai": False,
        }
        write(root / "reports/d144_sandbox_candidate_post_apply_verification_scope.json", d144)
        write(root / "reports/d144_sandbox_candidate_post_apply_verification_report.json", post_apply_report)
        write(root / "reports/d144_sandbox_candidate_apply_integrity_receipt.json", integrity)
        write(root / "reports/d144_d145_sandbox_candidate_final_audit_scope.json", d145_scope)
        # Some previous audit files are optional but present entries become richer.
        for i in range(126, 145):
            write(root / f"reports/d{i}_dummy_chain_marker.json", {"ok": True, "d": i})
        return td, root

    def test_creates_final_audit_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_final_audit_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_READY")
            self.assertEqual(r["summary"]["final_audit_status"], "FINAL_AUDIT_LEDGER_CREATED")
            self.assertEqual(r["summary"]["approval_scope"], "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted"])
            self.assertEqual(r["d146_scope"]["allowed_next_gate"], "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE")
            self.assertTrue((root / "reports/d145_sandbox_candidate_final_audit_scope.json").exists())
            self.assertTrue((root / "reports/d145_sandbox_candidate_final_audit_ledger.json").exists())
            self.assertTrue((root / "reports/d145_sandbox_candidate_replay_index.json").exists())
            self.assertTrue((root / "reports/d145_d146_sandbox_candidate_archive_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d144(self):
        td, root = self.root()
        try:
            (root / "reports/d144_sandbox_candidate_post_apply_verification_scope.json").unlink()
            r = create_sandbox_candidate_final_audit_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d144_summary_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d144_sandbox_candidate_post_apply_verification_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["route_insert_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_final_audit_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_post_apply_report_says_core_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d144_sandbox_candidate_post_apply_verification_report.json"
            data = json.loads(p.read_text())
            data["real_core_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_final_audit_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d145_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d144_d145_sandbox_candidate_final_audit_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d144_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_final_audit_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
