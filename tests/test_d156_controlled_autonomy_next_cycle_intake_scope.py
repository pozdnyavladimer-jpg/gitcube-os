
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.controlled_autonomy_next_cycle_intake_scope import create_controlled_autonomy_next_cycle_intake_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD156ControlledAutonomyNextCycleIntakeScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)
        base_false = {
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
        after_false = {
            "real_apply_allowed_after_d155_by_ai": False,
            "route_insert_allowed_after_d155_by_ai": False,
            "protected_core_mutation_allowed_after_d155_by_ai": False,
            "network_allowed_after_d155_by_ai": False,
            "secret_read_allowed_after_d155_by_ai": False,
            "shell_allowed_after_d155_by_ai": False,
            "git_action_allowed_after_d155_by_ai": False,
        }
        d155 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_GUARDED_AUTONOMY_CYCLE_CLOSURE_SCOPE_READY",
            "cycle_closure_id": "d155-test",
            "archive2_id": "d154-test",
            "audit_id": "d153-test",
            "candidate_id": "d126-test",
            "proposal_id": "d107-valid-test",
            "guardrails": {
                **base_false,
                **after_false,
                "sandbox_candidate_guarded_autonomy_cycle_closure_scope_only": True,
                "guarded_autonomy_cycle_closure_report_only": True,
                "guarded_autonomy_cycle_replay_index_only": True,
                "approval_for_d156_controlled_autonomy_next_cycle_intake_scope_only": True,
            },
            "summary": {
                "cycle_closure_status": "GUARDED_AUTONOMY_CYCLE_CLOSED_READY_FOR_CONTROLLED_NEXT_CYCLE_INTAKE",
                "replay_index_status": "GUARDED_AUTONOMY_CYCLE_REPLAY_INDEX_CREATED_NO_EXECUTION",
                "candidate_status": "GUARDED_AUTONOMY_CYCLE_CLOSED_NEXT_CYCLE_REQUIRES_FRESH_INTENT_NOT_CORE_MUTATED_BY_AI",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE_ONLY",
                "next_step": "D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE",
            },
        }
        closure = {
            "ok": True,
            "cycle_closure_status": "GUARDED_AUTONOMY_CYCLE_CLOSED_READY_FOR_CONTROLLED_NEXT_CYCLE_INTAKE",
            "real_apply_chain_closed": True,
            "next_cycle_requires_fresh_intent": True,
            "no_ai_core_mutation": True,
            "no_ai_route_insert": True,
            "no_ai_network": True,
            "no_ai_secret_read": True,
            "no_ai_shell": True,
            "no_ai_git_action": True,
            **base_false,
        }
        replay = {
            "ok": True,
            "replay_index_mode": "GUARDED_AUTONOMY_CYCLE_REPLAY_INDEX_ONLY_NO_EXECUTION",
            "replay_status": "GUARDED_AUTONOMY_CYCLE_REPLAY_INDEX_CREATED_NO_EXECUTION",
            "replay_executes_anything": False,
            "next_cycle_starts_from_new_intent_only": True,
            **base_false,
        }
        d156_scope = {
            "ok": True,
            "allowed_next_gate": "D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE",
            "controlled_autonomy_next_cycle_intake_scope_only": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            **after_false,
        }
        write(root / "reports/d155_sandbox_candidate_guarded_autonomy_cycle_closure_scope.json", d155)
        write(root / "reports/d155_sandbox_candidate_guarded_autonomy_cycle_closure_report.json", closure)
        write(root / "reports/d155_sandbox_candidate_guarded_autonomy_cycle_replay_index.json", replay)
        write(root / "reports/d155_d156_controlled_autonomy_next_cycle_intake_scope.json", d156_scope)
        return td, root

    def test_creates_next_cycle_intake_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_controlled_autonomy_next_cycle_intake_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D157_PROVIDER_CYCLE_REENTRY_SCOPE_ONLY")
            self.assertTrue(r["guardrails"]["fresh_intent_required"])
            self.assertFalse(r["guardrails"]["inherited_execution_authority"])
            self.assertEqual(r["d157_scope"]["allowed_next_gate"], "D157_PROVIDER_CYCLE_REENTRY_SCOPE")
            self.assertTrue((root / "reports/d156_controlled_autonomy_next_cycle_intake_scope.json").exists())
            self.assertTrue((root / "reports/d156_next_cycle_intake_manifest.json").exists())
            self.assertTrue((root / "reports/d156_next_cycle_safety_reset_report.json").exists())
            self.assertTrue((root / "reports/d156_d157_provider_cycle_reentry_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d155(self):
        td, root = self.root()
        try:
            (root / "reports/d155_sandbox_candidate_guarded_autonomy_cycle_closure_scope.json").unlink()
            self.assertFalse(create_controlled_autonomy_next_cycle_intake_scope(root)["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d155_summary_allows_route_insert(self):
        td, root = self.root()
        try:
            p = root / "reports/d155_sandbox_candidate_guarded_autonomy_cycle_closure_scope.json"
            d = json.loads(p.read_text())
            d["summary"]["route_insert_status"] = "ALLOWED"
            p.write_text(json.dumps(d), encoding="utf-8")
            self.assertFalse(create_controlled_autonomy_next_cycle_intake_scope(root)["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_replay_executes_anything(self):
        td, root = self.root()
        try:
            p = root / "reports/d155_sandbox_candidate_guarded_autonomy_cycle_replay_index.json"
            d = json.loads(p.read_text())
            d["replay_executes_anything"] = True
            p.write_text(json.dumps(d), encoding="utf-8")
            self.assertFalse(create_controlled_autonomy_next_cycle_intake_scope(root)["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d156_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d155_d156_controlled_autonomy_next_cycle_intake_scope.json"
            d = json.loads(p.read_text())
            d["network_allowed_after_d155_by_ai"] = True
            p.write_text(json.dumps(d), encoding="utf-8")
            self.assertFalse(create_controlled_autonomy_next_cycle_intake_scope(root)["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
