
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_d138_d139_authority_repair import repair_d138_d139_narrow_execution_authority


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD138D139NarrowExecutionAuthorityRepair(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        d138 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_READY",
            "intent_id": "d138-test",
            "scope_id": "d137-test",
            "candidate_id": "d126-test",
            "proposal_id": "d107-test",
            "guardrails": {},
            "summary": {"next_step": "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE"},
        }
        intent_record = {
            "ok": True,
            "intent_id": "d138-test",
            "candidate_id": "d126-test",
            "record_mode": "HUMAN_EXECUTION_INTENT_RECORD_ONLY_NO_EXECUTION",
            "real_apply_executed": True,
            "network_accessed": True,
        }
        authority_guard = {
            "ok": True,
            "intent_id": "d138-test",
            "candidate_id": "d126-test",
            "guard_mode": "HUMAN_INTENT_REQUIRED_SANDBOX_EXECUTION_ONLY_NO_APPLY",
            "allow_real_apply": True,
            "allow_network": True,
            "allow_secret_read": True,
            "allow_shell_exec": True,
            "allow_git_action_by_ai": True,
        }
        d139_scope = {
            "ok": True,
            "intent_id": "d138-test",
            "candidate_id": "d126-test",
            "allowed_next_gate": "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE",
            "sandbox_candidate_controlled_execution_run_scope_only": True,
            "human_review_required": True,
            "network_allowed_after_d138": True,
            "secret_read_allowed_after_d138": True,
            "shell_allowed_after_d138_by_ai": True,
            "git_action_allowed_after_d138_by_ai": True,
        }

        write(root / "reports/d138_sandbox_candidate_human_execution_intent_scope.json", d138)
        write(root / "reports/d138_sandbox_candidate_human_execution_intent_record.json", intent_record)
        write(root / "reports/d138_sandbox_candidate_execution_authority_guard.json", authority_guard)
        write(root / "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json", d139_scope)
        return td, root

    def test_repairs_broad_authority_flags_to_false(self):
        td, root = self.root()
        try:
            r = repair_d138_d139_narrow_execution_authority(root)
            self.assertTrue(r["ok"])
            guard = json.loads((root / "reports/d138_sandbox_candidate_execution_authority_guard.json").read_text())
            self.assertFalse(guard["allow_real_apply"])
            self.assertFalse(guard["allow_network"])
            self.assertFalse(guard["allow_secret_read"])
            self.assertFalse(guard["allow_shell_exec"])
            self.assertFalse(guard["allow_git_action_by_ai"])
            scope = json.loads((root / "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json").read_text())
            self.assertFalse(scope["network_allowed_after_d138"])
            self.assertFalse(scope["secret_read_allowed_after_d138"])
            self.assertFalse(scope["shell_allowed_after_d138_by_ai"])
            self.assertFalse(scope["git_action_allowed_after_d138_by_ai"])
            self.assertTrue(scope["candidate_execution_allowed_after_d138_only_in_sandbox"])
            self.assertEqual(scope["allowed_next_gate"], "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE")
        finally:
            td.cleanup()

    def test_does_not_execute_candidate(self):
        td, root = self.root()
        try:
            r = repair_d138_d139_narrow_execution_authority(root)
            self.assertTrue(r["ok"])
            self.assertFalse(r["guardrails"]["candidate_executed_now"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["secret_read"])
        finally:
            td.cleanup()

    def test_blocks_missing_d138(self):
        td, root = self.root()
        try:
            (root / "reports/d138_sandbox_candidate_human_execution_intent_scope.json").unlink()
            r = repair_d138_d139_narrow_execution_authority(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_preserves_blocked_non_execution_actions(self):
        td, root = self.root()
        try:
            r = repair_d138_d139_narrow_execution_authority(root)
            self.assertTrue(r["ok"])
            scope = json.loads((root / "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json").read_text())
            for item in ["real_apply_by_ai", "route_insert_by_ai", "network_provider_call_by_ai", "secret_read_by_ai"]:
                self.assertIn(item, scope["d139_must_not_execute"])
        finally:
            td.cleanup()

    def test_writes_repair_report(self):
        td, root = self.root()
        try:
            r = repair_d138_d139_narrow_execution_authority(root)
            self.assertTrue(r["ok"])
            self.assertTrue((root / "reports/d138_d139_narrow_execution_authority_repair.json").exists())
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
