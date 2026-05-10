
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_human_apply_intent_scope import create_sandbox_candidate_human_apply_intent_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD142SandboxCandidateHumanApplyIntentScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        preflight_id = "d141-test"
        verification_id = "d140-test"
        run_id = "d139-test"
        candidate_id = "d126-test"
        proposal_id = "d107-valid-test"
        false_guard = {
            "external_ai_called": False, "network_accessed": False, "api_key_read": False, "secret_read": False,
            "shell_from_ai_executed": False, "runtime_code_mutated": False, "protected_core_mutated": False,
            "canonical_memory_mutated": False, "actual_apply_executed": False, "route_inserted": False,
            "git_commit_by_ai": False, "git_push_by_ai": False, "rollback_executed": False, "restore_executed": False,
        }
        d141 = {
            "ok": True, "decision": "SANDBOX_CANDIDATE_APPLY_PREFLIGHT_SCOPE_READY",
            "preflight_id": preflight_id, "verification_id": verification_id, "run_id": run_id,
            "candidate_id": candidate_id, "proposal_id": proposal_id,
            "guardrails": dict(false_guard, **{
                "sandbox_candidate_apply_preflight_scope_only": True, "apply_preflight_report_only": True,
                "apply_blockers_only": True, "candidate_executed_now": False,
                "approval_for_d142_human_apply_intent_scope_only": True, "approval_for_real_apply_by_ai": False,
                "approval_for_route_insert_by_ai": False, "approval_for_protected_core_mutation_by_ai": False,
                "candidate_execution_allowed_by_ai": False, "commands_executed_by_ai": False,
            }),
            "summary": {
                "apply_preflight_status": "APPLY_PREFLIGHT_CREATED_NO_APPLY",
                "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
                "execution_result_status": "PRESENT_AND_VALIDATED",
                "real_provider_status": "NOT_CALLED", "network_status": "NOT_ACCESSED", "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED", "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED", "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_ONLY",
                "next_step": "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE",
            },
        }
        preflight_report = {
            "ok": True, "preflight_id": preflight_id, "verification_id": verification_id, "run_id": run_id,
            "candidate_id": candidate_id, "proposal_id": proposal_id,
            "preflight_mode": "APPLY_PREFLIGHT_ONLY_NO_APPLY",
            "post_execution_validation_required": True,
            "post_execution_validation_status": "SANDBOX_EXECUTION_VERIFIED_NO_APPLY",
            "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
            "apply_preflight_status": "APPLY_PREFLIGHT_CREATED_NO_APPLY",
            "apply_readiness_status": "READY_FOR_HUMAN_APPLY_INTENT_SCOPE_ONLY",
            "candidate_executed_in_sandbox": True,
            "candidate_executed_now": False, "candidate_executed_by_ai": False,
            "actual_apply_executed": False, "real_apply_executed": False, "route_inserted": False,
            "protected_core_mutated": False, "canonical_memory_mutated": False, "network_accessed": False,
            "secret_read": False, "shell_executed_by_ai": False, "git_action_by_ai": False,
            "human_review_required": True,
        }
        blockers = {
            "ok": True, "preflight_id": preflight_id, "verification_id": verification_id, "candidate_id": candidate_id,
            "blocker_mode": "APPLY_BLOCKERS_ONLY_NO_APPLY",
            "must_remain_blocked_until_d142_or_later": {
                "real_apply_by_ai": True, "auto_apply": True, "route_insert_by_ai": True,
                "protected_core_mutation_by_ai": True, "canonical_memory_overwrite_by_ai": True,
                "shell_exec_from_ai": True, "external_network_call_by_ai": True, "secret_read_by_ai": True,
                "git_commit_by_ai": True, "git_push_by_ai": True,
            },
            "must_remain_false_now": {
                "actual_apply_executed": False, "real_apply_executed": False, "route_inserted": False,
                "protected_core_mutated": False, "canonical_memory_mutated": False, "network_accessed": False,
                "secret_read": False, "shell_executed_by_ai": False, "git_action_by_ai": False,
                "candidate_executed_now": False,
            },
            "human_review_required": True,
        }
        d142_scope = {
            "ok": True, "preflight_id": preflight_id, "verification_id": verification_id, "run_id": run_id,
            "candidate_id": candidate_id, "proposal_id": proposal_id,
            "allowed_next_gate": "D142_SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE",
            "sandbox_candidate_human_apply_intent_scope_only": True, "human_review_required": True,
            "candidate_executed_in_sandbox_after_d139": True,
            "candidate_executed_after_d141_by_ai": False, "real_apply_allowed_after_d141_by_ai": False,
            "route_insert_allowed_after_d141_by_ai": False, "protected_core_mutation_allowed_after_d141_by_ai": False,
            "network_allowed_after_d141_by_ai": False, "secret_read_allowed_after_d141_by_ai": False,
            "shell_allowed_after_d141_by_ai": False, "git_action_allowed_after_d141_by_ai": False,
        }
        write(root / "reports/d141_sandbox_candidate_apply_preflight_scope.json", d141)
        write(root / "reports/d141_sandbox_candidate_apply_preflight_report.json", preflight_report)
        write(root / "reports/d141_sandbox_candidate_apply_blockers.json", blockers)
        write(root / "reports/d141_d142_sandbox_candidate_human_apply_intent_scope.json", d142_scope)
        return td, root

    def test_creates_human_apply_intent_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_human_apply_intent_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_HUMAN_APPLY_INTENT_SCOPE_READY")
            self.assertEqual(r["summary"]["human_apply_intent_status"], "HUMAN_APPLY_INTENT_RECORD_CREATED_NO_APPLY")
            self.assertEqual(r["summary"]["approval_scope"], "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply_now"])
            self.assertEqual(r["d143_scope"]["allowed_next_gate"], "D143_SANDBOX_CANDIDATE_GUARDED_APPLY_SCOPE")
            self.assertTrue((root / "reports/d142_sandbox_candidate_human_apply_intent_scope.json").exists())
            self.assertTrue((root / "reports/d142_sandbox_candidate_human_apply_intent_record.json").exists())
            self.assertTrue((root / "reports/d142_sandbox_candidate_apply_authority_guard.json").exists())
            self.assertTrue((root / "reports/d142_d143_sandbox_candidate_guarded_apply_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d141(self):
        td, root = self.root()
        try:
            (root / "reports/d141_sandbox_candidate_apply_preflight_scope.json").unlink()
            r = create_sandbox_candidate_human_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_preflight_report_says_apply_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d141_sandbox_candidate_apply_preflight_report.json"
            data = json.loads(p.read_text())
            data["actual_apply_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_apply_blocker_false(self):
        td, root = self.root()
        try:
            p = root / "reports/d141_sandbox_candidate_apply_blockers.json"
            data = json.loads(p.read_text())
            data["must_remain_blocked_until_d142_or_later"]["route_insert_by_ai"] = False
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d142_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d141_d142_sandbox_candidate_human_apply_intent_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d141_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_human_apply_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
