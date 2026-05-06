import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.policy_verification_gate import verify_policy_gate, sha256_text


class TestD79PolicyVerificationGate(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)
        (root / "runtime_experimental/differentiated_modules").mkdir(parents=True)
        (root / "app/orchestration").mkdir(parents=True)

        source = "app/orchestration/task_dispatcher.py"
        child = "runtime_experimental/differentiated_modules/01_route_policy_child.py"
        diff_path = "reports/d78_narrow_adapter_dry_run.diff"
        adapter = "D77_NARROW_ADAPTER_ROUTE_POLICY_CHILD"

        (root / source).write_text("# source stays unchanged\n", encoding="utf-8")
        (root / child).write_text("def run_sandbox_probe(event=None): return {'ok': True}\n", encoding="utf-8")

        diff = """diff --git a/app/orchestration/task_dispatcher.py b/app/orchestration/task_dispatcher.py
@@ DRY-RUN ONLY: narrow adapter route proposal, not applied @@
+# D78 DRY-RUN ONLY — DO NOT APPLY AUTOMATICALLY
+# D66_RECHECK
+# D76_CHILD_PROBE_PASSED
+# ROLLBACK_MANIFEST
+# HUMAN_OR_HIGHER_POLICY_APPROVAL
"""
        (root / diff_path).write_text(diff, encoding="utf-8")

        (root / "reports/d78_narrow_adapter_dry_run_diff.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "NARROW_ADAPTER_DRY_RUN_DIFF_READY",
                    "guardrails": {
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "external_ai_called": False,
                        "actual_apply_executed": False,
                        "route_inserted": False,
                        "dry_run_only": True,
                    },
                    "dry_run_diff_package": {
                        "source_node": source,
                        "child_module_path": child,
                        "adapter_name": adapter,
                        "contract_id": "d77-test",
                        "diff_output_path": diff_path,
                        "diff_sha256": sha256_text(diff),
                        "route_insert_allowed_now": False,
                        "apply_allowed_now": False,
                        "actual_files_touched": [],
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d64_safe_mutation_gate_request.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "CREATE_GUARDED_APPLY_REQUEST",
                    "guardrails": {
                        "actual_apply_executed": False,
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "external_ai_called": False,
                    },
                }
            ),
            encoding="utf-8",
        )

        (root / "reports/d66_core_guard_reviewer_report.json").write_text(
            json.dumps(
                {
                    "ok": False,
                    "decision": "FORBIDDEN_CORE_MUTATION",
                    "reason": "protected_core_touched_without_two_eyes",
                    "guardrails": {
                        "actual_apply_executed": False,
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "external_ai_called": False,
                    },
                }
            ),
            encoding="utf-8",
        )

        return td, root, source

    def test_policy_verifies_dry_run_without_mutation(self):
        td, root, source = self.make_root()
        try:
            before = (root / source).read_text(encoding="utf-8")
            report = verify_policy_gate(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "POLICY_VERIFIED_DRY_RUN_READY")
            self.assertEqual(report["policy_verdict"]["verdict"], "DRY_RUN_POLICY_APPROVED")
            self.assertFalse(report["policy_verdict"]["real_apply_allowed"])
            self.assertFalse(report["policy_verdict"]["real_route_insert_allowed"])
            self.assertEqual((root / source).read_text(encoding="utf-8"), before)
            self.assertTrue((root / "reports/d79_policy_verification_gate.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d78(self):
        td, root, _ = self.make_root()
        try:
            (root / "reports/d78_narrow_adapter_dry_run_diff.json").unlink()
            report = verify_policy_gate(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "POLICY_VERIFICATION_BLOCKED")
            self.assertGreaterEqual(report["summary"]["errors_count"], 1)
        finally:
            td.cleanup()

    def test_blocks_when_diff_hash_mismatch(self):
        td, root, _ = self.make_root()
        try:
            p = root / "reports/d78_narrow_adapter_dry_run.diff"
            p.write_text(p.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")

            report = verify_policy_gate(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "POLICY_VERIFICATION_BLOCKED")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
