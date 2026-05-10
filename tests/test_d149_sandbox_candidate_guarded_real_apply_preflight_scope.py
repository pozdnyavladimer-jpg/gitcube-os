
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_guarded_real_apply_preflight_scope import create_sandbox_candidate_guarded_real_apply_preflight_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD149SandboxCandidateGuardedRealApplyPreflightScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        intent_id = "d148-test"
        decision_id = "d147-test"
        archive_id = "d146-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d148 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_HUMAN_REAL_APPLY_INTENT_SCOPE_READY",
            "intent_id": intent_id,
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
                "sandbox_candidate_human_real_apply_intent_scope_only": True,
                "human_real_apply_intent_record_only": True,
                "real_apply_authority_guard_only": True,
                "approval_for_d149_guarded_real_apply_preflight_scope_only": True,
                "approval_for_real_core_apply_now": False,
                "real_apply_allowed_after_d148_by_ai": False,
                "route_insert_allowed_after_d148_by_ai": False,
                "protected_core_mutation_allowed_after_d148_by_ai": False,
                "network_allowed_after_d148_by_ai": False,
                "secret_read_allowed_after_d148_by_ai": False,
                "shell_allowed_after_d148_by_ai": False,
                "git_action_allowed_after_d148_by_ai": False,
            },
            "summary": {
                "human_real_apply_intent_status": "HUMAN_REAL_APPLY_INTENT_RECORDED_NO_REAL_APPLY",
                "real_apply_authority_status": "REAL_APPLY_AUTHORITY_GUARD_CREATED_NO_REAL_APPLY",
                "candidate_status": "SANDBOX_CHAIN_PROMOTED_TO_REAL_APPLY_PREFLIGHT_PATH_NOT_CORE_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_ONLY",
                "next_step": "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE",
            },
        }

        intent_record = {
            "ok": True,
            "intent_id": intent_id,
            "intent_mode": "HUMAN_REAL_APPLY_INTENT_RECORD_ONLY_NO_REAL_APPLY",
            "approved_for_d149_guarded_real_apply_preflight_scope_only": True,
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
            "intent_id": intent_id,
            "authority_mode": "REAL_APPLY_AUTHORITY_GUARD_ONLY_NO_REAL_APPLY",
            "allow_d149_guarded_real_apply_preflight": True,
            "allow_real_core_apply_now": False,
            "allow_route_insert": False,
            "allow_protected_core_mutation": False,
            "allow_network": False,
            "allow_secret_read": False,
            "allow_shell_exec": False,
            "allow_git_action_by_ai": False,
            "real_apply_allowed_after_d148_by_ai": False,
            "route_insert_allowed_after_d148_by_ai": False,
            "protected_core_mutation_allowed_after_d148_by_ai": False,
            "network_allowed_after_d148_by_ai": False,
            "secret_read_allowed_after_d148_by_ai": False,
            "shell_allowed_after_d148_by_ai": False,
            "git_action_allowed_after_d148_by_ai": False,
        }

        d149_scope = {
            "ok": True,
            "intent_id": intent_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D149_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE",
            "sandbox_candidate_guarded_real_apply_preflight_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d148_by_ai": False,
            "route_insert_allowed_after_d148_by_ai": False,
            "protected_core_mutation_allowed_after_d148_by_ai": False,
            "network_allowed_after_d148_by_ai": False,
            "secret_read_allowed_after_d148_by_ai": False,
            "shell_allowed_after_d148_by_ai": False,
            "git_action_allowed_after_d148_by_ai": False,
        }

        write(root / "reports/d148_sandbox_candidate_human_real_apply_intent_scope.json", d148)
        write(root / "reports/d148_sandbox_candidate_human_real_apply_intent_record.json", intent_record)
        write(root / "reports/d148_sandbox_candidate_real_apply_authority_guard.json", authority_guard)
        write(root / "reports/d148_d149_sandbox_candidate_guarded_real_apply_preflight_scope.json", d149_scope)

        return td, root

    def test_creates_guarded_real_apply_preflight_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_guarded_real_apply_preflight_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertEqual(r["d150_scope"]["allowed_next_gate"], "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE")
            self.assertTrue((root / "reports/d149_sandbox_candidate_guarded_real_apply_preflight_scope.json").exists())
            self.assertTrue((root / "reports/d149_sandbox_candidate_real_apply_preflight_report.json").exists())
            self.assertTrue((root / "reports/d149_sandbox_candidate_real_apply_blockers.json").exists())
            self.assertTrue((root / "reports/d149_d150_sandbox_candidate_human_signed_real_apply_execution_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d148(self):
        td, root = self.root()
        try:
            (root / "reports/d148_sandbox_candidate_human_real_apply_intent_scope.json").unlink()
            r = create_sandbox_candidate_guarded_real_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d148_summary_allows_real_apply_by_ai(self):
        td, root = self.root()
        try:
            p = root / "reports/d148_sandbox_candidate_human_real_apply_intent_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["real_apply_by_ai_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_real_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_authority_guard_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d148_sandbox_candidate_real_apply_authority_guard.json"
            data = json.loads(p.read_text())
            data["allow_route_insert"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_real_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d149_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d148_d149_sandbox_candidate_guarded_real_apply_preflight_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d148_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_guarded_real_apply_preflight_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
