
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_guarded_autonomy_cycle_closure_scope import create_sandbox_candidate_guarded_autonomy_cycle_closure_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD155SandboxCandidateGuardedAutonomyCycleClosureScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        archive2_id = "d154-test"
        audit_id = "d153-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d154 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REAL_APPLY_CHAIN_ARCHIVE_SCOPE_READY",
            "archive2_id": archive2_id,
            "audit_id": audit_id,
            "verification_id": "d152-test",
            "run_apply_id": "d151-test",
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
                "archive_upload_performed": False,
                "archive_compression_performed": False,
                "sandbox_candidate_real_apply_chain_archive_scope_only": True,
                "real_apply_chain_archive_manifest_only": True,
                "real_apply_chain_closure_receipt_only": True,
                "approval_for_d155_guarded_autonomy_cycle_closure_scope_only": True,
                "real_apply_allowed_after_d154_by_ai": False,
                "route_insert_allowed_after_d154_by_ai": False,
                "protected_core_mutation_allowed_after_d154_by_ai": False,
                "network_allowed_after_d154_by_ai": False,
                "secret_read_allowed_after_d154_by_ai": False,
                "shell_allowed_after_d154_by_ai": False,
                "git_action_allowed_after_d154_by_ai": False,
            },
            "summary": {
                "real_apply_chain_archive_status": "REAL_APPLY_CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
                "chain_closure_status": "REAL_APPLY_CHAIN_ARCHIVED_READY_FOR_GUARDED_AUTONOMY_CYCLE_CLOSURE",
                "candidate_status": "REAL_APPLY_CHAIN_ARCHIVED_READY_FOR_GUARDED_AUTONOMY_CYCLE_CLOSURE_NOT_CORE_MUTATED_BY_AI",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE_ONLY",
                "next_step": "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE",
            },
        }

        archive_manifest = {
            "ok": True,
            "archive2_id": archive2_id,
            "archive_mode": "real-apply-chain-archive-manifest-only",
            "archive_status": "REAL_APPLY_CHAIN_ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
            "archived_without_real_apply_again": True,
            "archive_upload_performed": False,
            "archive_compression_performed": False,
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

        closure_receipt = {
            "ok": True,
            "archive2_id": archive2_id,
            "closure_status": "REAL_APPLY_CHAIN_ARCHIVED_READY_FOR_GUARDED_AUTONOMY_CYCLE_CLOSURE",
            "chain_closed_for_ai_execution": True,
            "no_second_apply": True,
            "no_ai_core_mutation": True,
            "no_ai_route_insert": True,
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

        d155_scope = {
            "ok": True,
            "archive2_id": archive2_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D155_SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE",
            "sandbox_candidate_guarded_autonomy_cycle_closure_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d154_by_ai": False,
            "route_insert_allowed_after_d154_by_ai": False,
            "protected_core_mutation_allowed_after_d154_by_ai": False,
            "network_allowed_after_d154_by_ai": False,
            "secret_read_allowed_after_d154_by_ai": False,
            "shell_allowed_after_d154_by_ai": False,
            "git_action_allowed_after_d154_by_ai": False,
        }

        write(root / "reports/d154_sandbox_candidate_real_apply_chain_archive_scope.json", d154)
        write(root / "reports/d154_sandbox_candidate_real_apply_chain_archive_manifest.json", archive_manifest)
        write(root / "reports/d154_sandbox_candidate_real_apply_chain_closure_receipt.json", closure_receipt)
        write(root / "reports/d154_d155_sandbox_candidate_guarded_autonomy_cycle_closure_scope.json", d155_scope)

        return td, root

    def test_creates_guarded_autonomy_cycle_closure_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_guarded_autonomy_cycle_closure_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["real_apply_executed_by_ai"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertFalse(r["guardrails"]["git_action_by_ai"])
            self.assertTrue(r["guarded_autonomy_cycle_closure_report"]["next_cycle_requires_fresh_intent"])
            self.assertEqual(r["d156_scope"]["allowed_next_gate"], "D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE")
            self.assertTrue((root / "reports/d155_sandbox_candidate_guarded_autonomy_cycle_closure_scope.json").exists())
            self.assertTrue((root / "reports/d155_sandbox_candidate_guarded_autonomy_cycle_closure_report.json").exists())
            self.assertTrue((root / "reports/d155_sandbox_candidate_guarded_autonomy_cycle_replay_index.json").exists())
            self.assertTrue((root / "reports/d155_d156_controlled_autonomy_next_cycle_intake_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d154(self):
        td, root = self.root()
        try:
            (root / "reports/d154_sandbox_candidate_real_apply_chain_archive_scope.json").unlink()
            r = create_sandbox_candidate_guarded_autonomy_cycle_closure_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d154_summary_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d154_sandbox_candidate_real_apply_chain_archive_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["route_insert_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_autonomy_cycle_closure_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_archive_manifest_uploaded(self):
        td, root = self.root()
        try:
            p = root / "reports/d154_sandbox_candidate_real_apply_chain_archive_manifest.json"
            data = json.loads(p.read_text())
            data["archive_upload_performed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_autonomy_cycle_closure_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d155_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d154_d155_sandbox_candidate_guarded_autonomy_cycle_closure_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d154_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_autonomy_cycle_closure_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
