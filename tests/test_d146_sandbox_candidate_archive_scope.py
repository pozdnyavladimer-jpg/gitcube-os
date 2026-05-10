
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_archive_scope import create_sandbox_candidate_archive_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD146SandboxCandidateArchiveScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        audit_id = "d145-test"
        verification_id = "d144-test"
        apply_id = "d143-test"
        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        false_guard = {
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "shell_executed_by_ai": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
        }

        d145 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_FINAL_AUDIT_SCOPE_READY",
            "audit_id": audit_id,
            "verification_id": verification_id,
            "apply_id": apply_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_final_audit_scope_only": True,
                "final_audit_ledger_only": True,
                "replay_index_only": True,
                "approval_for_d146_archive_scope_only": True,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "final_audit_status": "FINAL_AUDIT_LEDGER_CREATED",
                "replay_index_status": "INDEX_CREATED_NOT_REPLAYED",
                "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_FINAL_AUDIT_READY_NOT_CORE_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE_ONLY",
                "next_step": "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE",
            },
        }

        ledger = dict(false_guard, **{
            "state": "D145_SANDBOX_CANDIDATE_FINAL_AUDIT_LEDGER",
            "ok": True,
            "audit_id": audit_id,
            "candidate_id": candidate_id,
            "ledger_status": "FINAL_AUDIT_LEDGER_CREATED",
        })

        replay_index = dict(false_guard, **{
            "state": "D145_SANDBOX_CANDIDATE_REPLAY_INDEX",
            "ok": True,
            "audit_id": audit_id,
            "candidate_id": candidate_id,
            "index_status": "INDEX_CREATED_NOT_REPLAYED",
            "replay_executed": False,
        })

        d146_scope = dict(false_guard, **{
            "state": "D145_D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE",
            "ok": True,
            "audit_id": audit_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D146_SANDBOX_CANDIDATE_ARCHIVE_SCOPE",
            "sandbox_candidate_archive_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d145_by_ai": False,
            "route_insert_allowed_after_d145_by_ai": False,
            "protected_core_mutation_allowed_after_d145_by_ai": False,
            "network_allowed_after_d145_by_ai": False,
            "secret_read_allowed_after_d145_by_ai": False,
            "shell_allowed_after_d145_by_ai": False,
            "git_action_allowed_after_d145_by_ai": False,
            "candidate_execution_allowed_after_d145_by_ai": False,
        })

        write(root / "reports/d145_sandbox_candidate_final_audit_scope.json", d145)
        write(root / "reports/d145_sandbox_candidate_final_audit_ledger.json", ledger)
        write(root / "reports/d145_sandbox_candidate_replay_index.json", replay_index)
        write(root / "reports/d145_d146_sandbox_candidate_archive_scope.json", d146_scope)
        write(root / "reports/d139_sandbox_candidate_controlled_execution_run_scope.json", {"ok": True})
        return td, root

    def test_creates_archive_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_archive_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_ARCHIVE_SCOPE_READY")
            self.assertEqual(r["summary"]["archive_status"], "ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED")
            self.assertEqual(r["summary"]["approval_scope"], "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_ONLY")
            self.assertEqual(r["d147_scope"]["allowed_next_gate"], "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["route_inserted"])
            self.assertTrue((root / "reports/d146_sandbox_candidate_archive_scope.json").exists())
            self.assertTrue((root / "reports/d146_sandbox_candidate_archive_manifest.json").exists())
            self.assertTrue((root / "reports/d146_sandbox_candidate_chain_closure_receipt.json").exists())
            self.assertTrue((root / "reports/d146_d147_sandbox_candidate_promotion_decision_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d145(self):
        td, root = self.root()
        try:
            (root / "reports/d145_sandbox_candidate_final_audit_scope.json").unlink()
            r = create_sandbox_candidate_archive_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d145_real_apply_not_blocked(self):
        td, root = self.root()
        try:
            p = root / "reports/d145_sandbox_candidate_final_audit_scope.json"
            d = json.loads(p.read_text())
            d["summary"]["real_apply_by_ai_status"] = "ALLOWED"
            p.write_text(json.dumps(d), encoding="utf-8")
            r = create_sandbox_candidate_archive_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_ledger_says_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d145_sandbox_candidate_final_audit_ledger.json"
            d = json.loads(p.read_text())
            d["actual_apply_executed"] = True
            p.write_text(json.dumps(d), encoding="utf-8")
            r = create_sandbox_candidate_archive_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d146_scope_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d145_d146_sandbox_candidate_archive_scope.json"
            d = json.loads(p.read_text())
            d["route_insert_allowed_after_d145_by_ai"] = True
            p.write_text(json.dumps(d), encoding="utf-8")
            r = create_sandbox_candidate_archive_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
