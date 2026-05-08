
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.rollback_evidence_builder import create_rollback_evidence_builder


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD103RollbackEvidenceBuilder(unittest.TestCase):
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

        write(root / "reports/d102_post_execution_verifier.json", {
            "ok": True,
            "decision": "POST_EXECUTION_VERIFIER_READY",
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "decision_id": "d100-test",
            "post_execution_verifier": {
                "ok": True,
                "mode": "POST_EXECUTION_VERIFIER_NO_EXECUTION_RECORDED",
                "next_required_gate": "D103_ROLLBACK_EVIDENCE_BUILDER",
            },
            "guardrails": {
                **false_flags,
                "rollback_executed": False,
                "restore_executed": False,
                "post_execution_verifier_only": True,
                "manual_execution_performed": False,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d102_post_execution_evidence_report.json", {
            "ok": True,
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "decision_id": "d100-test",
            "real_apply_observed": False,
            "route_insert_observed": False,
            "protected_core_mutation_observed": False,
            "external_ai_execution_observed": False,
            "rollback_execution_observed": False,
        })

        write(root / "reports/d102_changed_files_manifest.json", {
            "ok": True,
            "manifest_mode": "DECLARATIVE_NO_EXECUTION_MANIFEST",
            "manual_execution_performed": False,
        })

        write(root / "reports/d102_execution_integrity_summary.json", {
            "ok": True,
            "manual_execution_performed": False,
            "ai_execution_performed": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "network_accessed": False,
            "external_ai_called": False,
            "git_commit_by_ai": False,
            "rollback_executed": False,
            "ready_for_d103": True,
        })

        write(root / "reports/d102_d103_rollback_evidence_builder_scope.json", {
            "ok": True,
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "allowed_next_gate": "D103_ROLLBACK_EVIDENCE_BUILDER",
            "d103_allowed_to_create": [
                "rollback_evidence_builder",
                "rollback_evidence_bundle",
                "restore_point_reference",
                "rollback_readiness_summary",
            ],
            "d103_must_not_execute": [
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
            ],
            "apply_allowed_after_d102": False,
            "route_insert_allowed_after_d102": False,
            "protected_core_mutation_allowed_after_d102": False,
            "required_phrase_for_later_gate": "APPROVE_D103_ROLLBACK_EVIDENCE_BUILDER_ONLY",
        })

        return td, root

    def test_creates_rollback_evidence_only(self):
        td, root = self.root()
        try:
            r = create_rollback_evidence_builder(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "ROLLBACK_EVIDENCE_BUILDER_READY")
            self.assertTrue(r["guardrails"]["rollback_evidence_only"])
            self.assertFalse(r["guardrails"]["rollback_executed"])
            self.assertFalse(r["guardrails"]["restore_executed"])
            self.assertEqual(r["rollback_evidence_builder"]["next_required_gate"], "D104_FINAL_AUDIT_LEDGER")
            self.assertTrue(r["rollback_readiness_summary"]["ready_for_d104"])
            self.assertTrue((root / "reports/d103_rollback_evidence_builder.json").exists())
            self.assertTrue((root / "reports/d103_rollback_evidence_bundle.json").exists())
            self.assertTrue((root / "reports/d103_restore_point_reference.json").exists())
            self.assertTrue((root / "reports/d103_rollback_readiness_summary.json").exists())
            self.assertTrue((root / "reports/d103_d104_final_audit_ledger_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d102(self):
        td, root = self.root()
        try:
            (root / "reports/d102_post_execution_verifier.json").unlink()
            r = create_rollback_evidence_builder(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "ROLLBACK_EVIDENCE_BUILDER_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_rollback_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d102_execution_integrity_summary.json"
            data = json.loads(p.read_text())
            data["rollback_executed"] = True
            p.write_text(json.dumps(data))
            r = create_rollback_evidence_builder(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
