
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_human_signed_real_apply_execution_scope import create_sandbox_candidate_human_signed_real_apply_execution_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD150SandboxCandidateHumanSignedRealApplyExecutionScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        preflight_id = "d149-test"
        intent_id = "d148-test"
        decision_id = "d147-test"
        archive_id = "d146-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"

        d149 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_PREFLIGHT_SCOPE_READY",
            "preflight_id": preflight_id,
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
                "sandbox_candidate_guarded_real_apply_preflight_scope_only": True,
                "real_apply_preflight_report_only": True,
                "real_apply_blockers_only": True,
                "approval_for_d150_human_signed_real_apply_execution_scope_only": True,
                "approval_for_real_core_apply_now": False,
                "real_apply_allowed_after_d149_by_ai": False,
                "route_insert_allowed_after_d149_by_ai": False,
                "protected_core_mutation_allowed_after_d149_by_ai": False,
                "network_allowed_after_d149_by_ai": False,
                "secret_read_allowed_after_d149_by_ai": False,
                "shell_allowed_after_d149_by_ai": False,
                "git_action_allowed_after_d149_by_ai": False,
            },
            "summary": {
                "real_apply_preflight_status": "REAL_APPLY_PREFLIGHT_CREATED_NO_EXECUTION",
                "real_apply_blocker_status": "AI_REAL_APPLY_BLOCKERS_DECLARED",
                "candidate_status": "SANDBOX_CHAIN_READY_FOR_HUMAN_SIGNED_REAL_APPLY_EXECUTION_NOT_CORE_APPLIED",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_ONLY",
                "next_step": "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE",
            },
        }

        preflight_report = {
            "ok": True,
            "preflight_id": preflight_id,
            "preflight_mode": "REAL_APPLY_PREFLIGHT_ONLY_NO_REAL_APPLY",
            "preflight_status": "REAL_APPLY_PREFLIGHT_CREATED_NO_EXECUTION",
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        blockers = {
            "ok": True,
            "preflight_id": preflight_id,
            "blocker_mode": "REAL_APPLY_BLOCKERS_DECLARED_NO_EXECUTION",
            "hard_blockers_for_ai": [
                "real_core_apply_by_ai",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "shell_exec_from_ai",
                "network_call_by_ai",
                "secret_read_by_ai",
                "git_commit_by_ai",
                "git_push_by_ai",
            ],
            "actual_apply_executed": False,
            "real_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
        }

        d150_scope = {
            "ok": True,
            "preflight_id": preflight_id,
            "candidate_id": candidate_id,
            "allowed_next_gate": "D150_SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE",
            "sandbox_candidate_human_signed_real_apply_execution_scope_only": True,
            "human_review_required": True,
            "real_apply_allowed_after_d149_by_ai": False,
            "route_insert_allowed_after_d149_by_ai": False,
            "protected_core_mutation_allowed_after_d149_by_ai": False,
            "network_allowed_after_d149_by_ai": False,
            "secret_read_allowed_after_d149_by_ai": False,
            "shell_allowed_after_d149_by_ai": False,
            "git_action_allowed_after_d149_by_ai": False,
        }

        write(root / "reports/d149_sandbox_candidate_guarded_real_apply_preflight_scope.json", d149)
        write(root / "reports/d149_sandbox_candidate_real_apply_preflight_report.json", preflight_report)
        write(root / "reports/d149_sandbox_candidate_real_apply_blockers.json", blockers)
        write(root / "reports/d149_d150_sandbox_candidate_human_signed_real_apply_execution_scope.json", d150_scope)

        return td, root

    def test_creates_human_signed_real_apply_execution_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_human_signed_real_apply_execution_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_HUMAN_SIGNED_REAL_APPLY_EXECUTION_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertFalse(r["guardrails"]["protected_core_mutated"])
            self.assertEqual(r["d151_scope"]["allowed_next_gate"], "D151_SANDBOX_CANDIDATE_GUARDED_REAL_APPLY_RUN_SCOPE")
            self.assertTrue((root / "reports/d150_sandbox_candidate_human_signed_real_apply_execution_scope.json").exists())
            self.assertTrue((root / "reports/d150_sandbox_candidate_real_apply_signature_record.json").exists())
            self.assertTrue((root / "reports/d150_sandbox_candidate_real_apply_execution_authority_guard.json").exists())
            self.assertTrue((root / "reports/d150_d151_sandbox_candidate_guarded_real_apply_run_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d149(self):
        td, root = self.root()
        try:
            (root / "reports/d149_sandbox_candidate_guarded_real_apply_preflight_scope.json").unlink()
            r = create_sandbox_candidate_human_signed_real_apply_execution_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d149_summary_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d149_sandbox_candidate_guarded_real_apply_preflight_scope.json"
            data = json.loads(p.read_text())
            data["summary"]["route_insert_status"] = "ALLOWED"
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_signed_real_apply_execution_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_preflight_report_says_real_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d149_sandbox_candidate_real_apply_preflight_report.json"
            data = json.loads(p.read_text())
            data["real_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_signed_real_apply_execution_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d150_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d149_d150_sandbox_candidate_human_signed_real_apply_execution_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d149_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_signed_real_apply_execution_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
