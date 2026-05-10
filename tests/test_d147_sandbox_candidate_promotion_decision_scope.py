
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_promotion_decision_scope import create_sandbox_candidate_promotion_decision_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD147SandboxCandidatePromotionDecisionScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        archive_id = "d146-test"
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
            "route_inserted": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "git_action_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
        }

        d146 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_ARCHIVE_SCOPE_READY",
            "archive_id": archive_id,
            "verification_id": verification_id,
            "apply_id": apply_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_archive_scope_only": True,
                "archive_manifest_only": True,
                "chain_closure_receipt_only": True,
                "approval_for_d147_promotion_decision_scope_only": True,
                "candidate_reexecuted_now": False,
                "real_apply_executed_now": False,
                "approval_for_real_apply_by_ai": False,
                "route_insert_allowed_by_ai": False,
                "protected_core_mutation_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            }),
            "summary": {
                "archive_status": "ARCHIVE_MANIFEST_CREATED_NOT_COMPRESSED_NOT_UPLOADED",
                "chain_closure_status": "SANDBOX_CHAIN_ARCHIVED_READY_FOR_PROMOTION_DECISION",
                "candidate_status": "MATERIALIZED_EXECUTED_SANDBOX_APPLY_VERIFIED_ARCHIVED_NOT_CORE_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_ONLY",
                "next_step": "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE",
            },
        }

        archive_manifest = {
            "ok": True,
            "archive_id": archive_id,
            "candidate_id": candidate_id,
            "archive_mode": "ARCHIVE_MANIFEST_ONLY_NOT_COMPRESSED_NOT_UPLOADED",
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
        }
        chain_closure = {
            "ok": True,
            "archive_id": archive_id,
            "candidate_id": candidate_id,
            "closure_status": "SANDBOX_CHAIN_ARCHIVED_READY_FOR_PROMOTION_DECISION",
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
        }
        d147_scope = {
            "ok": True,
            "archive_id": archive_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D147_SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE",
            "sandbox_candidate_promotion_decision_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d146_by_ai": False,
            "route_insert_allowed_after_d146_by_ai": False,
            "protected_core_mutation_allowed_after_d146_by_ai": False,
            "network_allowed_after_d146_by_ai": False,
            "secret_read_allowed_after_d146_by_ai": False,
            "shell_allowed_after_d146_by_ai": False,
            "git_action_allowed_after_d146_by_ai": False,
        }

        write(root / "reports/d146_sandbox_candidate_archive_scope.json", d146)
        write(root / "reports/d146_sandbox_candidate_archive_manifest.json", archive_manifest)
        write(root / "reports/d146_sandbox_candidate_chain_closure_receipt.json", chain_closure)
        write(root / "reports/d146_d147_sandbox_candidate_promotion_decision_scope.json", d147_scope)
        return td, root

    def test_creates_promotion_decision_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_promotion_decision_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_READY")
            self.assertEqual(r["summary"]["promotion_decision"], "PROMOTE_TO_REAL_APPLY_PATH")
            self.assertEqual(r["summary"]["approval_scope"], "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["real_apply_allowed_now"])
            self.assertFalse(r["guardrails"]["route_insert_allowed_now"])
            self.assertFalse(r["guardrails"]["protected_core_mutation_allowed_now"])
            self.assertEqual(r["d148_scope"]["allowed_next_gate"], "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE")
            self.assertTrue((root / "reports/d147_sandbox_candidate_promotion_decision_scope.json").exists())
            self.assertTrue((root / "reports/d147_sandbox_candidate_promotion_decision_record.json").exists())
            self.assertTrue((root / "reports/d147_sandbox_candidate_real_apply_readiness_review.json").exists())
            self.assertTrue((root / "reports/d147_d148_sandbox_candidate_human_real_apply_intent_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d146(self):
        td, root = self.root()
        try:
            (root / "reports/d146_sandbox_candidate_archive_scope.json").unlink()
            r = create_sandbox_candidate_promotion_decision_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d146_summary_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d146_sandbox_candidate_archive_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["real_apply_by_ai_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_promotion_decision_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_archive_manifest_says_core_mutated(self):
        td, root = self.root()
        try:
            p = root / "reports/d146_sandbox_candidate_archive_manifest.json"
            data = json.loads(p.read_text())
            data["protected_core_mutated"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_promotion_decision_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d147_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d146_d147_sandbox_candidate_promotion_decision_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d146_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_promotion_decision_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
