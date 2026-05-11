
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_real_apply_chain_archive_scope import create_sandbox_candidate_real_apply_chain_archive_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD154SandboxCandidateRealApplyChainArchiveScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        audit_id = "d153-test"
        verification_id = "d152-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"
        d153 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_FINAL_REAL_APPLY_AUDIT_SCOPE_READY",
            "audit_id": audit_id,
            "verification_id": verification_id,
            "run_apply_id": "d151-test",
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
                "sandbox_candidate_final_real_apply_audit_scope_only": True,
                "real_apply_audit_ledger_only": True,
                "real_apply_replay_index_only": True,
                "approval_for_d154_real_apply_chain_archive_scope_only": True,
                "real_apply_allowed_after_d153_by_ai": False,
                "route_insert_allowed_after_d153_by_ai": False,
                "protected_core_mutation_allowed_after_d153_by_ai": False,
                "network_allowed_after_d153_by_ai": False,
                "secret_read_allowed_after_d153_by_ai": False,
                "shell_allowed_after_d153_by_ai": False,
                "git_action_allowed_after_d153_by_ai": False,
            },
            "summary": {
                "final_real_apply_audit_status": "FINAL_REAL_APPLY_AUDIT_LEDGER_CREATED_NO_AI_CORE_MUTATION",
                "replay_index_status": "REAL_APPLY_CHAIN_REPLAY_INDEX_CREATED_NO_EXECUTION",
                "candidate_status": "FINAL_REAL_APPLY_AUDIT_READY_FOR_CHAIN_ARCHIVE_NOT_CORE_MUTATED_BY_AI",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE_ONLY",
                "next_step": "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE",
            },
        }
        audit_ledger = {
            "ok": True,
            "audit_id": audit_id,
            "ledger_mode": "FINAL_REAL_APPLY_AUDIT_LEDGER_ONLY_NO_ACTION",
            "audit_status": "FINAL_REAL_APPLY_AUDIT_LEDGER_CREATED_NO_AI_CORE_MUTATION",
            "audit_entries": ["D147", "D148", "D149", "D150", "D151", "D152"],
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
        replay_index = {
            "ok": True,
            "audit_id": audit_id,
            "replay_index_mode": "REAL_APPLY_REPLAY_INDEX_ONLY_NO_EXECUTION",
            "replay_status": "REAL_APPLY_CHAIN_REPLAY_INDEX_CREATED_NO_EXECUTION",
            "replay_executes_anything": False,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }
        d154_scope = {
            "ok": True,
            "audit_id": audit_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D154_SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE",
            "sandbox_candidate_real_apply_chain_archive_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d153_by_ai": False,
            "route_insert_allowed_after_d153_by_ai": False,
            "protected_core_mutation_allowed_after_d153_by_ai": False,
            "network_allowed_after_d153_by_ai": False,
            "secret_read_allowed_after_d153_by_ai": False,
            "shell_allowed_after_d153_by_ai": False,
            "git_action_allowed_after_d153_by_ai": False,
        }
        write(root / "reports/d153_sandbox_candidate_final_real_apply_audit_scope.json", d153)
        write(root / "reports/d153_sandbox_candidate_real_apply_audit_ledger.json", audit_ledger)
        write(root / "reports/d153_sandbox_candidate_real_apply_replay_index.json", replay_index)
        write(root / "reports/d153_d154_sandbox_candidate_real_apply_chain_archive_scope.json", d154_scope)
        return td, root

    def test_creates_real_apply_chain_archive_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_real_apply_chain_archive_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["real_apply_executed_by_ai"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertFalse(r["guardrails"]["archive_upload_performed"])
            self.assertEqual(r["d155_scope"]["allowed_next_gate"], "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE")
            self.assertTrue((root / "reports/d154_sandbox_candidate_real_apply_chain_archive_scope.json").exists())
            self.assertTrue((root / "reports/d154_sandbox_candidate_real_apply_chain_archive_manifest.json").exists())
            self.assertTrue((root / "reports/d154_sandbox_candidate_real_apply_chain_closure_receipt.json").exists())
            self.assertTrue((root / "reports/d154_d155_sandbox_candidate_guarded_autonomy_cycle_closure_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d153(self):
        td, root = self.root()
        try:
            (root / "reports/d153_sandbox_candidate_final_real_apply_audit_scope.json").unlink()
            r = create_sandbox_candidate_real_apply_chain_archive_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d153_summary_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d153_sandbox_candidate_final_real_apply_audit_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["route_insert_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_real_apply_chain_archive_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_replay_index_executes_anything(self):
        td, root = self.root()
        try:
            p = root / "reports/d153_sandbox_candidate_real_apply_replay_index.json"
            data = json.loads(p.read_text())
            data["replay_executes_anything"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_real_apply_chain_archive_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d154_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d153_d154_sandbox_candidate_real_apply_chain_archive_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d153_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_real_apply_chain_archive_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

if __name__ == "__main__":
    unittest.main()
