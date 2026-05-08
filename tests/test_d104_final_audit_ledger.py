
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.final_audit_ledger import create_final_audit_ledger


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD104FinalAuditLedger(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        false_flags = {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
        }

        write(root / "reports/d103_rollback_evidence_builder.json", {
            "ok": True,
            "decision": "ROLLBACK_EVIDENCE_BUILDER_READY",
            "builder_id": "d103-test",
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "decision_id": "d100-test",
            "rollback_evidence_builder": {
                "ok": True,
                "next_required_gate": "D104_FINAL_AUDIT_LEDGER",
                "rollback_allowed_now": False,
                "restore_allowed_now": False,
                "apply_allowed_now": False,
                "route_insert_allowed_now": False,
                "protected_core_mutation_allowed_now": False,
            },
            "guardrails": {
                **false_flags,
                "rollback_executed": False,
                "restore_executed": False,
                "rollback_evidence_only": True,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d103_rollback_evidence_bundle.json", {
            "ok": True,
            "builder_id": "d103-test",
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "rollback_executed": False,
            "restore_executed": False,
        })

        write(root / "reports/d103_restore_point_reference.json", {
            "ok": True,
            "builder_id": "d103-test",
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "restore_point_created_by_script": False,
            "restore_executed": False,
            "human_review_required": True,
        })

        write(root / "reports/d103_rollback_readiness_summary.json", {
            "ok": True,
            "builder_id": "d103-test",
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "rollback_executed": False,
            "restore_executed": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
            "ready_for_d104": True,
        })

        write(root / "reports/d103_d104_final_audit_ledger_scope.json", {
            "ok": True,
            "builder_id": "d103-test",
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "allowed_next_gate": "D104_FINAL_AUDIT_LEDGER",
            "d104_allowed_to_create": [
                "final_audit_ledger",
                "replay_log_index",
                "guarded_autonomy_chain_summary",
                "terminal_safety_state",
            ],
            "d104_must_not_execute": [
                "actual_apply_by_ai",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "external_ai_network_execution",
                "git_commit_or_push_by_ai",
                "execute_rollback_by_ai",
                "delete_runtime_candidate_by_ai",
                "run_manual_apply_now",
                "execute_post_fix_mutation",
                "execute_rollback_now",
                "restore_files_now",
                "delete_generated_candidate",
                "execute_final_apply",
                "mutate_chain_history",
            ],
            "apply_allowed_after_d103": False,
            "route_insert_allowed_after_d103": False,
            "protected_core_mutation_allowed_after_d103": False,
            "required_phrase_for_later_gate": "APPROVE_D104_FINAL_AUDIT_LEDGER_ONLY",
        })

        return td, root

    def test_creates_final_audit_only(self):
        td, root = self.root()
        try:
            r = create_final_audit_ledger(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "FINAL_AUDIT_LEDGER_READY")
            self.assertTrue(r["guardrails"]["final_audit_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["final_audit_ledger"]["next_required_gate"], "NONE_TERMINAL_AUDIT_STATE")
            self.assertEqual(r["terminal_safety_state"]["terminal_decision"], "GUARDED_AUTONOMY_PRE_EXECUTION_CHAIN_SEALED")
            self.assertTrue((root / "reports/d104_final_audit_ledger.json").exists())
            self.assertTrue((root / "reports/d104_replay_log_index.json").exists())
            self.assertTrue((root / "reports/d104_guarded_autonomy_chain_summary.json").exists())
            self.assertTrue((root / "reports/d104_terminal_safety_state.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d103(self):
        td, root = self.root()
        try:
            (root / "reports/d103_rollback_evidence_builder.json").unlink()
            r = create_final_audit_ledger(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "FINAL_AUDIT_LEDGER_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_restore_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d103_restore_point_reference.json"
            data = json.loads(p.read_text())
            data["restore_executed"] = True
            p.write_text(json.dumps(data))
            r = create_final_audit_ledger(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
