
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_human_execution_intent_scope import create_sandbox_candidate_reentry_human_execution_intent_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


def no_ai_flags():
    return {
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
    }


class TestD167SandboxCandidateReentryHumanExecutionIntentScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        preflight_id = "d166-test"
        validation_id = "d165-test"
        candidate_id = "d164-test"
        response_id = "d163-test"
        runner_id = "d162-test"
        plan_id = "d161-test"
        review_id = "d160-test"
        scope_id = "d159-test"
        intake_id = "d158-test"
        reentry_id = "d157-test"
        next_cycle_id = "d156-test"
        proposal_id = "d107-valid-test"

        d166 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_READY",
            "preflight_id": preflight_id,
            "validation_id": validation_id,
            "candidate_id": candidate_id,
            "response_id": response_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "scope_id": scope_id,
            "intake_id": intake_id,
            "reentry_id": reentry_id,
            "next_cycle_id": next_cycle_id,
            "cycle_closure_id": "d155-test",
            "previous_candidate_id": "d126-test",
            "proposal_id": proposal_id,
            "guardrails": {
                **no_ai_flags(),
                "sandbox_candidate_reentry_controlled_execution_preflight_scope_only": True,
                "sandbox_candidate_reentry_controlled_execution_preflight_report_only": True,
                "sandbox_candidate_reentry_execution_authority_guard_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "candidate_files_static_validated": True,
                "controlled_execution_preflight_created": True,
                "execution_authority_guard_created": True,
                "candidate_execution_allowed_after_d166": False,
                "candidate_execution_requested": False,
                "candidate_executed": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "approval_for_d167_sandbox_candidate_reentry_human_execution_intent_scope_only": True,
                "real_apply_allowed_after_d166_by_ai": False,
                "route_insert_allowed_after_d166_by_ai": False,
                "protected_core_mutation_allowed_after_d166_by_ai": False,
                "network_allowed_after_d166_by_ai": False,
                "secret_read_allowed_after_d166_by_ai": False,
                "shell_allowed_after_d166_by_ai": False,
                "git_action_allowed_after_d166_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D166_PLUS",
                "controlled_execution_preflight_status": "CONTROLLED_EXECUTION_PREFLIGHT_CREATED_NO_EXECUTION",
                "authority_guard_status": "EXECUTION_AUTHORITY_GUARD_CREATED_NO_EXECUTION",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_HUMAN_EXECUTION_INTENT",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_ONLY",
                "next_step": "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE",
            },
        }

        preflight_report = {
            **no_ai_flags(),
            "ok": True,
            "controlled_execution_preflight_status": "CONTROLLED_EXECUTION_PREFLIGHT_CREATED_NO_EXECUTION",
            "candidate_execution_policy": "HUMAN_INTENT_REQUIRED_BEFORE_ANY_SANDBOX_EXECUTION",
            "candidate_files_static_validated": True,
            "candidate_execution_allowed_after_d166": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
        }

        authority_guard = {
            **no_ai_flags(),
            "ok": True,
            "authority_mode": "SANDBOX_EXECUTION_AUTHORITY_GUARD_ONLY_NO_EXECUTION",
            "authority_guard_status": "EXECUTION_AUTHORITY_GUARD_CREATED_NO_EXECUTION",
            "human_execution_intent_required": True,
            "candidate_execution_allowed": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "real_apply_allowed": False,
            "apply_requested": False,
            "apply_executed": False,
            "network_allowed": False,
            "secret_read_allowed": False,
            "shell_allowed": False,
            "git_action_allowed": False,
            "route_insert_allowed": False,
            "protected_core_mutation_allowed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "no_candidate_execution": True,
            "no_apply": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
        }

        d167_scope = {
            "ok": True,
            "allowed_next_gate": "D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE",
            "sandbox_candidate_reentry_human_execution_intent_scope_only": True,
            "human_execution_intent_required": True,
            "candidate_files_static_validated": True,
            "controlled_execution_preflight_created": True,
            "execution_authority_guard_created": True,
            "candidate_execution_allowed_after_d166": False,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "real_apply_allowed_after_d166_by_ai": False,
            "route_insert_allowed_after_d166_by_ai": False,
            "protected_core_mutation_allowed_after_d166_by_ai": False,
            "network_allowed_after_d166_by_ai": False,
            "secret_read_allowed_after_d166_by_ai": False,
            "shell_allowed_after_d166_by_ai": False,
            "git_action_allowed_after_d166_by_ai": False,
        }

        write(root / "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json", d166)
        write(root / "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_report.json", preflight_report)
        write(root / "reports/d166_sandbox_candidate_reentry_execution_authority_guard.json", authority_guard)
        write(root / "reports/d166_d167_sandbox_candidate_reentry_human_execution_intent_scope.json", d167_scope)
        return td, root

    def test_creates_human_execution_intent_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_human_execution_intent_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE_ONLY")
            self.assertEqual(r["d168_scope"]["allowed_next_gate"], "D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE")
            self.assertTrue(r["guardrails"]["human_execution_intent_present"])
            self.assertTrue(r["guardrails"]["candidate_execution_allowed_next"])
            self.assertFalse(r["guardrails"]["candidate_executed"])
            self.assertFalse(r["guardrails"]["apply_executed"])
            self.assertTrue((root / "reports/d167_sandbox_candidate_reentry_human_execution_intent_scope.json").exists())
            self.assertTrue((root / "reports/d167_sandbox_candidate_reentry_human_execution_intent_record.json").exists())
            self.assertTrue((root / "reports/d167_sandbox_candidate_reentry_execution_authority_guard.json").exists())
            self.assertTrue((root / "reports/d167_d168_sandbox_candidate_reentry_controlled_execution_run_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d166(self):
        td, root = self.root()
        try:
            (root / "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json").unlink()
            r = create_sandbox_candidate_reentry_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_preflight_report_executed_candidate(self):
        td, root = self.root()
        try:
            p = root / "reports/d166_sandbox_candidate_reentry_controlled_execution_preflight_report.json"
            data = json.loads(p.read_text())
            data["candidate_executed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d167_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d166_d167_sandbox_candidate_reentry_human_execution_intent_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d166_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_authority_guard_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d166_sandbox_candidate_reentry_execution_authority_guard.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_human_execution_intent_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
