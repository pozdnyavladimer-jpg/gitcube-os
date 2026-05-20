
import json, tempfile, unittest
from pathlib import Path
from runtime_experimental.sandbox_candidate_reentry_human_apply_intent_scope import create_sandbox_candidate_reentry_human_apply_intent_scope

def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")

def no_ai():
    return {"network_accessed": False, "secret_read": False, "shell_executed_by_ai": False, "actual_apply_executed_by_ai": False, "real_apply_executed_by_ai": False, "route_inserted": False, "route_inserted_by_ai": False, "protected_core_mutated": False, "protected_core_mutated_by_ai": False, "git_action_by_ai": False}

class TestD171SandboxCandidateReentryHumanApplyIntentScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory(); root = Path(td.name); (root / "reports").mkdir(parents=True)
        ids = {"apply_preflight_id":"d170-test", "verification_id":"d169-test", "run_id":"d168-test", "intent_id":"d167-test", "preflight_id":"d166-test", "validation_id":"d165-test", "candidate_id":"d164-test", "response_id":"d163-test", "runner_id":"d162-test", "plan_id":"d161-test", "review_id":"d160-test", "scope_id":"d159-test", "intake_id":"d158-test", "reentry_id":"d157-test", "next_cycle_id":"d156-test", "proposal_id":"d107-valid-test"}
        d170 = {"ok": True, "decision": "SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE_READY", **ids,
            "guardrails": {**no_ai(), "sandbox_candidate_reentry_apply_preflight_scope_only": True, "sandbox_candidate_reentry_apply_preflight_report_only": True, "sandbox_candidate_reentry_apply_blockers_only": True, "canonical_guard_schema_applied": True, "fresh_intent_required": True, "human_review_required": True, "post_execution_verified": True, "apply_preflight_created": True, "human_apply_intent_required": True, "candidate_apply_allowed_after_d170": False, "candidate_apply_allowed_next": False, "real_provider_call_performed": False, "provider_response_ingested": False, "provider_response_captured": False, "apply_requested": False, "apply_executed": False, "real_apply_executed": False, "actual_apply_executed": False, "approval_for_d171_sandbox_candidate_reentry_human_apply_intent_scope_only": True, "real_apply_allowed_after_d170_by_ai": False, "route_insert_allowed_after_d170_by_ai": False, "protected_core_mutation_allowed_after_d170_by_ai": False, "network_allowed_after_d170_by_ai": False, "secret_read_allowed_after_d170_by_ai": False, "shell_allowed_after_d170_by_ai": False, "git_action_allowed_after_d170_by_ai": False},
            "summary": {"next_step": "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE", "real_apply_by_ai_status": "BLOCKED"}}
        pre = {**no_ai(), "ok": True, "apply_preflight_status": "APPLY_PREFLIGHT_CREATED_NO_APPLY", "apply_policy": "HUMAN_APPLY_INTENT_REQUIRED_BEFORE_ANY_REAL_APPLY", "post_execution_verified": True, "candidate_executed_in_sandbox": True, "candidate_execution_was_no_op_only": True, "human_apply_intent_required": True, "candidate_apply_allowed_next": False, "candidate_apply_allowed_after_d170": False, "real_apply_allowed": False, "real_apply_executed": False, "actual_apply_executed": False, "apply_requested": False, "apply_executed": False, "real_provider_call_performed": False, "provider_response_ingested": False}
        blockers = {**no_ai(), "ok": True, "blocker_status": "REAL_APPLY_BLOCKED_UNTIL_HUMAN_APPLY_INTENT", "human_apply_intent_required": True, "candidate_apply_allowed_next": False, "candidate_apply_allowed_after_d170": False, "real_apply_allowed": False, "real_apply_executed": False, "actual_apply_executed": False, "apply_requested": False, "apply_executed": False, "route_insert_allowed": False, "protected_core_mutation_allowed": False, "network_allowed": False, "secret_read_allowed": False, "shell_allowed": False, "git_action_allowed": False, "real_provider_call_performed": False, "provider_response_ingested": False}
        scope = {"ok": True, "allowed_next_gate": "D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE", "sandbox_candidate_reentry_human_apply_intent_scope_only": True, "apply_preflight_created": True, "post_execution_verified": True, "human_apply_intent_required": True, "candidate_apply_allowed_after_d170": False, "fresh_intent_required": True, "human_review_required": True, "canonical_guard_schema_required": True, "real_apply_allowed_after_d170_by_ai": False, "route_insert_allowed_after_d170_by_ai": False, "protected_core_mutation_allowed_after_d170_by_ai": False, "network_allowed_after_d170_by_ai": False, "secret_read_allowed_after_d170_by_ai": False, "shell_allowed_after_d170_by_ai": False, "git_action_allowed_after_d170_by_ai": False}
        write(root / "reports/d170_sandbox_candidate_reentry_apply_preflight_scope.json", d170)
        write(root / "reports/d170_sandbox_candidate_reentry_apply_preflight_report.json", pre)
        write(root / "reports/d170_sandbox_candidate_reentry_apply_blockers.json", blockers)
        write(root / "reports/d170_d171_sandbox_candidate_reentry_human_apply_intent_scope.json", scope)
        return td, root
    def test_creates_human_apply_intent_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_human_apply_intent_scope(root)
            self.assertTrue(r["ok"]); self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE_READY")
            self.assertEqual(r["d172_scope"]["allowed_next_gate"], "D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE")
            self.assertTrue(r["guardrails"]["human_apply_intent_present"]); self.assertFalse(r["guardrails"]["real_apply_executed"])
            self.assertTrue((root / "reports/d171_sandbox_candidate_reentry_human_apply_intent_scope.json").exists())
            self.assertTrue((root / "reports/d171_sandbox_candidate_reentry_human_apply_intent_record.json").exists())
            self.assertTrue((root / "reports/d171_sandbox_candidate_reentry_apply_authority_guard.json").exists())
            self.assertTrue((root / "reports/d171_d172_sandbox_candidate_reentry_guarded_apply_scope.json").exists())
        finally: td.cleanup()
    def test_blocks_missing_d170(self):
        td, root = self.root()
        try: (root / "reports/d170_sandbox_candidate_reentry_apply_preflight_scope.json").unlink(); self.assertFalse(create_sandbox_candidate_reentry_human_apply_intent_scope(root)["ok"])
        finally: td.cleanup()
    def test_blocks_if_preflight_allows_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d170_sandbox_candidate_reentry_apply_preflight_report.json"; d = json.loads(p.read_text()); d["real_apply_allowed"] = True; write(p, d)
            self.assertFalse(create_sandbox_candidate_reentry_human_apply_intent_scope(root)["ok"])
        finally: td.cleanup()
    def test_blocks_if_blockers_missing_human_intent_requirement(self):
        td, root = self.root()
        try:
            p = root / "reports/d170_sandbox_candidate_reentry_apply_blockers.json"; d = json.loads(p.read_text()); d["human_apply_intent_required"] = False; write(p, d)
            self.assertFalse(create_sandbox_candidate_reentry_human_apply_intent_scope(root)["ok"])
        finally: td.cleanup()
    def test_blocks_if_scope_allows_git_action(self):
        td, root = self.root()
        try:
            p = root / "reports/d170_d171_sandbox_candidate_reentry_human_apply_intent_scope.json"; d = json.loads(p.read_text()); d["git_action_allowed_after_d170_by_ai"] = True; write(p, d)
            self.assertFalse(create_sandbox_candidate_reentry_human_apply_intent_scope(root)["ok"])
        finally: td.cleanup()
if __name__ == "__main__": unittest.main()
