
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_human_real_apply_intent_scope import create_sandbox_candidate_human_real_apply_intent_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD148SandboxCandidateHumanRealApplyIntentScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        decision_id = "d147-test"
        archive_id = "d146-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d147 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_PROMOTION_DECISION_SCOPE_READY",
            "decision_id": decision_id,
            "archive_id": archive_id,
            "verification_id": "d144-test",
            "apply_id": "d143-test",
            "run_id": "d139-test",
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
            },
            "summary": {
                "promotion_decision": "PROMOTE_TO_REAL_APPLY_PATH",
                "candidate_status": "SANDBOX_CHAIN_AUDITED_ARCHIVED_PROMOTION_PATH_SELECTED_NOT_CORE_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_ONLY",
                "next_step": "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE",
            },
        }

        decision_record = {
            "ok": True,
            "decision_id": decision_id,
            "promotion_decision": "PROMOTE_TO_REAL_APPLY_PATH",
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        readiness_review = {
            "ok": True,
            "decision_id": decision_id,
            "candidate_id": candidate_id,
            "candidate_status": "SANDBOX_CHAIN_AUDITED_ARCHIVED_PROMOTION_PATH_SELECTED_NOT_CORE_APPLIED",
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        d148_scope = {
            "ok": True,
            "decision_id": decision_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D148_SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE",
            "sandbox_candidate_human_real_apply_intent_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d147_by_ai": False,
            "route_insert_allowed_after_d147_by_ai": False,
            "protected_core_mutation_allowed_after_d147_by_ai": False,
            "network_allowed_after_d147_by_ai": False,
            "secret_read_allowed_after_d147_by_ai": False,
            "shell_allowed_after_d147_by_ai": False,
            "git_action_allowed_after_d147_by_ai": False,
        }

        write(root / "reports/d147_sandbox_candidate_promotion_decision_scope.json", d147)
        write(root / "reports/d147_sandbox_candidate_promotion_decision_record.json", decision_record)
        write(root / "reports/d147_sandbox_candidate_real_apply_readiness_review.json", readiness_review)
        write(root / "reports/d147_d148_sandbox_candidate_human_real_apply_intent_scope.json", d148_scope)

        return td, root

    def test_creates_human_real_apply_intent_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_human_real_apply_intent_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertEqual(r["d149_scope"]["allowed_next_gate"], "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE")
            self.assertTrue((root / "reports/d148_sandbox_candidate_human_real_apply_intent_scope.json").exists())
            self.assertTrue((root / "reports/d148_sandbox_candidate_human_real_apply_intent_record.json").exists())
            self.assertTrue((root / "reports/d148_sandbox_candidate_real_apply_authority_guard.json").exists())
            self.assertTrue((root / "reports/d148_d149_sandbox_candidate_guarded_real_apply_preflight_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d147(self):
        td, root = self.root()
        try:
            (root / "reports/d147_sandbox_candidate_promotion_decision_scope.json").unlink()
            r = create_sandbox_candidate_human_real_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d147_summary_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d147_sandbox_candidate_promotion_decision_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["network_status"] = "ACCESSED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_real_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_readiness_review_says_core_mutated(self):
        td, root = self.root()
        try:
            p = root / "reports/d147_sandbox_candidate_real_apply_readiness_review.json"
            data = json.loads(p.read_text())
            data["protected_core_mutated"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_real_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d148_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d147_d148_sandbox_candidate_human_real_apply_intent_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d147_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_real_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
