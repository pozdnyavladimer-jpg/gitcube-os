#!/usr/bin/env python3
# D64_SAFE_MUTATION_GATE_BOOT.py
#
# Adds D64 Safe Mutation Gate to GitCube OS.
#
# Run from repo root:
#     python D64_SAFE_MUTATION_GATE_BOOT.py
#
# Creates:
# - runtime_experimental/safe_mutation_gate.py
# - tests/test_d64_safe_mutation_gate.py
# - reports/d64_safe_mutation_gate_request.json
#
# D64 does NOT call an external AI API.
# D64 does NOT patch task_dispatcher.py.
# D64 does NOT mutate protected core.
# D64 does NOT overwrite canonical memory.
# D64 does NOT apply sandbox files to runtime.
#
# D64 consumes D70 APPROVE evidence and D69 sandbox bundle,
# then emits a guarded apply request contract for the next dry-run / apply stage.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def sh(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, text=True, capture_output=False, check=check)


def find_repo_root() -> Path:
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p
    return here


ROOT = find_repo_root()
os.chdir(ROOT)

Path("runtime_experimental").mkdir(parents=True, exist_ok=True)
Path("tests").mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(parents=True, exist_ok=True)

print("D64 SAFE MUTATION GATE BOOT: repo =", ROOT)


GATE_CODE = r'''
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_D70_REVIEW = "reports/d70_sandbox_bundle_review.json"
DEFAULT_D69_BUNDLE = "reports/d69_sandbox_patch_bundle.json"
DEFAULT_D69_REPORT = "reports/d69_sandbox_patch_write_report.json"
DEFAULT_D68_PROPOSAL = "reports/d68_ai_patch_proposal.json"
DEFAULT_D67_REPORT = "reports/d67_topological_memory_map_report.json"
DEFAULT_D63_REPORT = "reports/d63_field_memory_replay_report.json"
DEFAULT_D66_REPORT = "reports/d66_core_guard_reviewer_report.json"
DEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"
DEFAULT_OUTPUT = "reports/d64_safe_mutation_gate_request.json"

ALLOWED_SANDBOX_PREFIXES = (
    "runtime_experimental/ai_bypass_proposals/",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_relative_path(path_value: str) -> str:
    raw = str(path_value or "").strip().replace("\\", "/")
    raw = raw.lstrip("/")
    parts: List[str] = []
    for part in raw.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            continue
        parts.append(part)
    return "/".join(parts)


def _is_allowed_sandbox_file(path_value: str) -> bool:
    rel = _safe_relative_path(path_value)
    return rel.endswith(".py") and any(rel.startswith(prefix) for prefix in ALLOWED_SANDBOX_PREFIXES)


def _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:
    for key in ("protected_files", "immutable_core", "core_files"):
        value = policy.get(key)
        if isinstance(value, list):
            return [str(v) for v in value]
    return []


def _guardrails_clean(source_name: str, guardrails: Dict[str, Any], errors: List[str]) -> None:
    required_false = [
        "runtime_code_mutated",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "external_ai_called",
    ]
    for key in required_false:
        if guardrails.get(key) is not False:
            errors.append(f"{source_name}.guardrail_not_false:{key}")

    if guardrails.get("sandbox_only") is not True:
        errors.append(f"{source_name}.guardrail_sandbox_only_not_true")


def _extract_macro_decision(d63: Dict[str, Any]) -> Dict[str, Any]:
    value = d63.get("macro_decision")
    return value if isinstance(value, dict) else {}


def build_safe_mutation_gate_request(
    root: str | Path = ".",
    d70_review_path: str = DEFAULT_D70_REVIEW,
    d69_bundle_path: str = DEFAULT_D69_BUNDLE,
    d69_report_path: str = DEFAULT_D69_REPORT,
    d68_proposal_path: str = DEFAULT_D68_PROPOSAL,
    d67_report_path: str = DEFAULT_D67_REPORT,
    d63_report_path: str = DEFAULT_D63_REPORT,
    d66_report_path: str = DEFAULT_D66_REPORT,
    core_policy_path: str = DEFAULT_CORE_POLICY,
    output_path: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()

    d70 = _read_json(root_path / d70_review_path, default={}) or {}
    d69_bundle = _read_json(root_path / d69_bundle_path, default={}) or {}
    d69_report = _read_json(root_path / d69_report_path, default={}) or {}
    d68 = _read_json(root_path / d68_proposal_path, default={}) or {}
    d67 = _read_json(root_path / d67_report_path, default={}) or {}
    d63 = _read_json(root_path / d63_report_path, default={}) or {}
    d66 = _read_json(root_path / d66_report_path, default={}) or {}
    policy = _read_json(root_path / core_policy_path, default={}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    if not d70:
        errors.append("D70 review missing or unreadable")
    if not d69_bundle:
        errors.append("D69 sandbox bundle missing or unreadable")
    if not policy:
        warnings.append("core guard policy missing or unreadable")
    if not d63:
        warnings.append("D63 replay report missing or unreadable")
    if not d67:
        warnings.append("D67 topology report missing or unreadable")
    if not d66:
        warnings.append("D66 reviewer report missing or unreadable")
    if not d68:
        warnings.append("D68 proposal report missing or unreadable")

    if d70:
        if d70.get("ok") is not True:
            errors.append("D70 review ok flag is not true")
        if d70.get("decision") != "APPROVE_SANDBOX_BUNDLE":
            errors.append(f"D70 decision is not APPROVE_SANDBOX_BUNDLE: {d70.get('decision')}")
        if d70.get("guardrails", {}).get("d64_apply_allowed") is not True:
            errors.append("D70 does not allow D64 consumption")

    if d69_bundle:
        if d69_bundle.get("ok") is not True:
            errors.append("D69 bundle ok flag is not true")
        _guardrails_clean("D69", d69_bundle.get("guardrails", {}) if isinstance(d69_bundle.get("guardrails"), dict) else {}, errors)

    if d70:
        _guardrails_clean("D70", d70.get("guardrails", {}) if isinstance(d70.get("guardrails"), dict) else {}, errors)

    d69_validation = d69_report.get("validation", {}) if isinstance(d69_report.get("validation"), dict) else {}
    if d69_report and d69_validation.get("ok") is not True:
        errors.append("D69 report validation is not ok")

    protected_files = _protected_files_from_policy(policy)

    written_files_raw = d69_bundle.get("written_files", [])
    written_files = [_safe_relative_path(str(x)) for x in written_files_raw] if isinstance(written_files_raw, list) else []

    if not written_files:
        errors.append("D69 bundle has no sandbox written_files")

    sandbox_candidates: List[str] = []
    for rel in written_files:
        if not _is_allowed_sandbox_file(rel):
            errors.append(f"D64 rejected non-sandbox candidate: {rel}")
            continue
        if rel in protected_files:
            errors.append(f"D64 rejected protected candidate: {rel}")
            continue
        if not (root_path / rel).exists():
            errors.append(f"D64 candidate missing on disk: {rel}")
            continue
        sandbox_candidates.append(rel)

    probe_results = d69_bundle.get("probe_results", [])
    if isinstance(probe_results, list):
        for item in probe_results:
            if isinstance(item, dict) and item.get("ok") is not True:
                errors.append(f"D69 probe not ok for {item.get('path')}: {item.get('reason')}")
    else:
        errors.append("D69 probe_results missing or invalid")

    macro_decision = _extract_macro_decision(d63)
    macro_decision_value = macro_decision.get("decision", "UNKNOWN")

    gate_passed = len(errors) == 0
    decision = "CREATE_GUARDED_APPLY_REQUEST" if gate_passed else "BLOCK_GUARDED_APPLY"
    result = "D64_GUARDED_APPLY_REQUEST_CREATED" if gate_passed else "D64_GUARDED_APPLY_BLOCKED"

    guarded_apply_request = {
        "request_state": "D64_GUARDED_APPLY_REQUEST",
        "enabled": gate_passed,
        "apply_mode": "DRY_RUN_FIRST_SANDBOX_TO_GUARDED_ROUTE",
        "source_sandbox_bundle": str(root_path / d69_bundle_path),
        "source_d70_review": str(root_path / d70_review_path),
        "sandbox_candidates": sandbox_candidates,
        "protected_files": protected_files,
        "forbidden_actions": [
            "direct_core_edit",
            "overwrite_canonical_memory",
            "auto_commit_without_review",
            "apply_without_dry_run",
            "apply_without_rollback",
        ],
        "required_next_evidence": [
            "D71_ROUTE_DRY_RUN_SIMULATION",
            "D66_REVIEWER_RECHECK",
            "UNIT_TESTS",
            "REGRESSION_TESTS",
            "ROLLBACK_PLAN",
        ],
        "allowed_next_scope": [
            "generate dry-run route diff",
            "generate rollback plan",
            "generate validation bundle",
        ],
        "disallowed_next_scope": [
            "mutate protected core immediately",
            "write canonical memory directly",
            "commit runtime mutation automatically",
        ],
    }

    report = {
        "state": "D64_SAFE_MUTATION_GATE",
        "result": result,
        "route": "FIELD_INTENT_SAFE_MUTATION_GATE",
        "ok": gate_passed,
        "decision": decision,
        "created_at": _now(),
        "macro_decision": macro_decision_value,
        "sandbox_candidates": sandbox_candidates,
        "protected_files": protected_files,
        "guarded_apply_request": guarded_apply_request,
        "input_reports": {
            "d70_review_path": str(root_path / d70_review_path),
            "d69_bundle_path": str(root_path / d69_bundle_path),
            "d69_report_path": str(root_path / d69_report_path),
            "d68_proposal_path": str(root_path / d68_proposal_path),
            "d67_report_path": str(root_path / d67_report_path),
            "d63_report_path": str(root_path / d63_report_path),
            "d66_report_path": str(root_path / d66_report_path),
            "core_policy_path": str(root_path / core_policy_path),
        },
        "evidence": {
            "d70_decision": d70.get("decision"),
            "d70_ok": d70.get("ok"),
            "d69_bundle_ok": d69_bundle.get("ok"),
            "d68_proposed_action": d68.get("proposed_action"),
            "d67_result": d67.get("result"),
            "d66_decision": d66.get("decision"),
            "macro_decision": macro_decision,
        },
        "guardrails": {
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "gate_only": True,
        },
        "validation": {
            "ok": gate_passed,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "sandbox_candidates_count": len(sandbox_candidates),
            "protected_files_count": len(protected_files),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "gate_evaluated": True,
            "guarded_apply_request_created": gate_passed,
            "actual_apply_executed": False,
            "next_step": "D71 should run a route dry-run simulation before any real guarded apply.",
        },
    }

    _write_json(root_path / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(build_safe_mutation_gate_request(), ensure_ascii=False, indent=2))
'''

Path("runtime_experimental/safe_mutation_gate.py").write_text(GATE_CODE.lstrip(), encoding="utf-8")
print("created/updated runtime_experimental/safe_mutation_gate.py")


TEST_CODE = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.safe_mutation_gate import build_safe_mutation_gate_request


SANDBOX_FILE = "def run_sandbox_probe(event=None):\n    return {'ok': True}\n"


class TestD64SafeMutationGate(unittest.TestCase):
    def make_valid_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)
        (root / "runtime_experimental/ai_bypass_proposals").mkdir(parents=True)
        rel = "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"
        (root / rel).write_text(SANDBOX_FILE, encoding="utf-8")

        (root / "runtime_experimental/core_guard_policy.json").write_text(
            json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),
            encoding="utf-8",
        )
        (root / "reports/d70_sandbox_bundle_review.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "decision": "APPROVE_SANDBOX_BUNDLE",
                    "guardrails": {
                        "runtime_code_mutated": False,
                        "protected_core_mutated": False,
                        "canonical_memory_mutated": False,
                        "sandbox_only": True,
                        "external_ai_called": False,
                        "d64_apply_allowed": True,
                    },
                }
            ),
            encoding="utf-8",
        )
        (root / "reports/d69_sandbox_patch_bundle.json").write_text(
            json.dumps(
                {
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
                }
            ),
            encoding="utf-8",
        )
        (root / "reports/d69_sandbox_patch_write_report.json").write_text(
            json.dumps({"validation": {"ok": True}}),
            encoding="utf-8",
        )
        (root / "reports/d63_field_memory_replay_report.json").write_text(
            json.dumps({"macro_decision": {"decision": "PLAN_ISOLATED_BYPASS"}}),
            encoding="utf-8",
        )
        return td, root, rel

    def test_creates_guarded_apply_request_when_d70_approved(self):
        td, root, rel = self.make_valid_root()
        try:
            report = build_safe_mutation_gate_request(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "CREATE_GUARDED_APPLY_REQUEST")
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertTrue(report["guardrails"]["gate_only"])
            self.assertIn(rel, report["sandbox_candidates"])
            self.assertTrue((root / "reports/d64_safe_mutation_gate_request.json").exists())
        finally:
            td.cleanup()

    def test_blocks_when_d70_rejected(self):
        td, root, _ = self.make_valid_root()
        try:
            (root / "reports/d70_sandbox_bundle_review.json").write_text(
                json.dumps({"ok": False, "decision": "REJECT_SANDBOX_BUNDLE"}),
                encoding="utf-8",
            )
            report = build_safe_mutation_gate_request(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "BLOCK_GUARDED_APPLY")
            self.assertFalse(report["guarded_apply_request"]["enabled"])
            self.assertGreaterEqual(report["summary"]["errors_count"], 1)
        finally:
            td.cleanup()

    def test_blocks_non_sandbox_candidate(self):
        td, root, _ = self.make_valid_root()
        try:
            (root / "reports/d69_sandbox_patch_bundle.json").write_text(
                json.dumps(
                    {
                        "ok": True,
                        "written_files": ["app/orchestration/task_dispatcher.py"],
                        "probe_results": [{"path": "app/orchestration/task_dispatcher.py", "ok": True}],
                        "guardrails": {
                            "runtime_code_mutated": False,
                            "protected_core_mutated": False,
                            "canonical_memory_mutated": False,
                            "sandbox_only": True,
                            "external_ai_called": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            report = build_safe_mutation_gate_request(root=root)

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "BLOCK_GUARDED_APPLY")
            self.assertEqual(report["summary"]["sandbox_candidates_count"], 0)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
'''

Path("tests/test_d64_safe_mutation_gate.py").write_text(TEST_CODE.lstrip(), encoding="utf-8")
print("created/updated tests/test_d64_safe_mutation_gate.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/safe_mutation_gate.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d64_safe_mutation_gate", "-v"], check=True)

print("\n== run D64 safe mutation gate ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.safe_mutation_gate import build_safe_mutation_gate_request\n"
        "r=build_safe_mutation_gate_request()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d64_safe_mutation_gate_request.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/safe_mutation_gate.py",
    "tests/test_d64_safe_mutation_gate.py",
    "reports/d64_safe_mutation_gate_request.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D64_SAFE_MUTATION_GATE_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D64 safe mutation gate"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D64 safe mutation gate changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD64 SAFE MUTATION GATE BOOT DONE")
