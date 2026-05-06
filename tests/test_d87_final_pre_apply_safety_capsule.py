import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.final_pre_apply_safety_capsule import create_final_pre_apply_safety_capsule


class TestD87FinalPreApplySafetyCapsule(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)

        (root / "reports/d86_local_regression_runner.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "LOCAL_REGRESSION_PASSED",
                    "package_id": "d85-test-package",
                    "review_id": "d84-test-review",
                    "summary": {"commands_failed_count": 0},
                    "guardrails": {
                        "external_ai_called": False,
                        "network_accessed": False,
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "actual_apply_executed": False,
                        "route_inserted": False,
                        "git_commit_by_ai": False,
                        "local_regression_only": True,
                        "allowlisted_commands_only": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d86_local_regression_results.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "package_id": "d85-test-package",
                    "review_id": "d84-test-review",
                    "commands_run_count": 4,
                    "commands_failed_count": 0,
                    "actual_apply_executed": False,
                    "route_inserted": False,
                    "protected_core_touched": False,
                    "network_accessed": False,
                    "external_ai_called": False,
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d85_regression_rollback_evidence.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "REGRESSION_ROLLBACK_EVIDENCE_READY",
                    "package_id": "d85-test-package",
                    "evidence": {"review_id": "d84-test-review"},
                    "guardrails": {
                        "external_ai_called": False,
                        "network_accessed": False,
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "actual_apply_executed": False,
                        "route_inserted": False,
                        "git_commit_by_ai": False,
                        "rollback_evidence_only": True,
                        "regression_evidence_only": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d85_rollback_manifest.json").write_text(
            json.dumps(
                {
                    "human_review_required": True,
                    "actual_rollback_executed": False,
                    "actual_apply_executed": False,
                    "route_inserted": False,
                    "protected_core_touched": False,
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d85_regression_checklist.json").write_text(
            json.dumps(
                {
                    "pass_condition": {
                        "all_tests_green": True,
                        "rollback_manifest_present": True,
                        "no_protected_core_mutation": True,
                        "no_route_insert": True,
                        "no_actual_apply": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        return td, root

    def test_creates_final_pre_apply_capsule(self):
        td, root = self.make_root()
        try:
            report = create_final_pre_apply_safety_capsule(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "FINAL_PRE_APPLY_SAFETY_CAPSULE_READY")
            self.assertFalse(report["capsule"]["approval_state"]["ready_for_real_apply"])
            self.assertFalse(report["blockers"]["apply_allowed_now"])
            self.assertTrue(report["guardrails"]["final_capsule_only"])
            self.assertTrue((root / "reports/d87_final_pre_apply_safety_capsule.json").exists())
            self.assertTrue((root / "reports/d87_pre_apply_safety_capsule.json").exists())
            self.assertTrue((root / "reports/d87_apply_blockers.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d86(self):
        td, root = self.make_root()
        try:
            (root / "reports/d86_local_regression_runner.json").unlink()
            report = create_final_pre_apply_safety_capsule(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "FINAL_PRE_APPLY_SAFETY_CAPSULE_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_failed_regression(self):
        td, root = self.make_root()
        try:
            p = root / "reports/d86_local_regression_results.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["commands_failed_count"] = 1
            p.write_text(json.dumps(data), encoding="utf-8")

            report = create_final_pre_apply_safety_capsule(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "FINAL_PRE_APPLY_SAFETY_CAPSULE_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
