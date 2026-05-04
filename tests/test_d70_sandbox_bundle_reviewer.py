import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_bundle_reviewer import review_sandbox_bundle


SANDBOX_FILE = """
from __future__ import annotations

def run_sandbox_probe(event=None):
    return {
        "ok": True,
        "proposal_only": True,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "received": dict(event or {}),
    }
"""


BAD_SANDBOX_FILE = """
from __future__ import annotations

def run_sandbox_probe(event=None):
    return {
        "ok": False,
        "proposal_only": False,
        "protected_core_mutated": True,
        "canonical_memory_mutated": False,
    }
"""


class TestD70SandboxBundleReviewer(unittest.TestCase):
    def test_approves_valid_sandbox_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)
            (root / "runtime_experimental/ai_bypass_proposals").mkdir(parents=True)
            rel = "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"
            (root / rel).write_text(SANDBOX_FILE, encoding="utf-8")
            (root / "runtime_experimental/core_guard_policy.json").parent.mkdir(parents=True, exist_ok=True)
            (root / "runtime_experimental/core_guard_policy.json").write_text(
                json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),
                encoding="utf-8",
            )
            (root / "reports/d69_sandbox_patch_bundle.json").write_text(
                json.dumps({
                    "ok": True,
                    "written_files": [rel],
                    "probe_results": [{"path": rel, "ok": True, "reason": "probe_ok"}],
                    "guardrails": {
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "sandbox_only": True,
                        "external_ai_called": False,
                    },
                }),
                encoding="utf-8",
            )
            (root / "reports/d69_sandbox_patch_write_report.json").write_text(
                json.dumps({"validation": {"ok": True}}), encoding="utf-8"
            )
            report = review_sandbox_bundle(root=root)
            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "APPROVE_SANDBOX_BUNDLE")
            self.assertTrue(report["guardrails"]["d64_apply_allowed"])
            self.assertTrue((root / "reports/d70_sandbox_bundle_review.json").exists())

    def test_rejects_protected_or_bad_probe(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)
            (root / "runtime_experimental/ai_bypass_proposals").mkdir(parents=True)
            bad_rel = "runtime_experimental/ai_bypass_proposals/bad_proposal.py"
            (root / bad_rel).write_text(BAD_SANDBOX_FILE, encoding="utf-8")
            (root / "runtime_experimental/core_guard_policy.json").parent.mkdir(parents=True, exist_ok=True)
            (root / "runtime_experimental/core_guard_policy.json").write_text(
                json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),
                encoding="utf-8",
            )
            (root / "reports/d69_sandbox_patch_bundle.json").write_text(
                json.dumps({
                    "ok": True,
                    "written_files": [bad_rel, "app/orchestration/task_dispatcher.py"],
                    "probe_results": [{"path": bad_rel, "ok": True, "reason": "probe_ok"}],
                    "guardrails": {
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "sandbox_only": True,
                        "external_ai_called": False,
                    },
                }),
                encoding="utf-8",
            )
            report = review_sandbox_bundle(root=root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "REJECT_SANDBOX_BUNDLE")
            self.assertFalse(report["guardrails"]["d64_apply_allowed"])
            self.assertGreaterEqual(report["summary"]["errors_count"], 1)

    def test_rejects_missing_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)
            report = review_sandbox_bundle(root=root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "REJECT_SANDBOX_BUNDLE")
            self.assertGreaterEqual(report["summary"]["errors_count"], 1)


if __name__ == "__main__":
    unittest.main()
