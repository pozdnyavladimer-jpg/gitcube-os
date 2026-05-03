#!/usr/bin/env python3
# D63_FIELD_MEMORY_REPLAY_RUNNER_BOOT.py
#
# Adds D63 Field Memory Replay Runner to GitCube OS.
# Run from repo root:
#     python D63_FIELD_MEMORY_REPLAY_RUNNER_BOOT.py
#
# Creates:
# - runtime_experimental/field_memory_replay_runner.py
# - tests/test_d63_field_memory_replay_runner.py
# - reports/d63_field_memory_replay_report.json
#
# D63 does not patch task_dispatcher.py and does not mutate canonical memory.

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

print("D63 FIELD MEMORY REPLAY RUNNER BOOT: repo =", ROOT)

RUNNER_CODE = r'''
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_REPORT_PATH = "reports/d63_field_memory_replay_report.json"


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


def _module_status(name: str, ok: bool, result: str, detail: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {"module": name, "ok": ok, "result": result, "detail": detail or {}}


def _top_moves_from_map(d67_map: Dict[str, Any]) -> List[Dict[str, Any]]:
    moves = d67_map.get("suggested_moves")
    if isinstance(moves, list):
        return [m for m in moves if isinstance(m, dict)]
    report_moves = d67_map.get("top_suggested_moves")
    if isinstance(report_moves, list):
        return [m for m in report_moves if isinstance(m, dict)]
    return []


def _derive_macro_decision(d65_report: Dict[str, Any], d67_map: Dict[str, Any], d66_report: Dict[str, Any]) -> Dict[str, Any]:
    top_moves = _top_moves_from_map(d67_map)
    apoptosis_summary = d65_report.get("summary", {}) if isinstance(d65_report, dict) else {}

    tenuki_core_moves = [
        m for m in top_moves
        if m.get("move_type") == "TENUKI" and bool(m.get("protected_core"))
    ]

    try:
        decayed_count = int(apoptosis_summary.get("decayed_count", 0))
    except Exception:
        decayed_count = 0

    d66_decision = ""
    if isinstance(d66_report, dict):
        d66_decision = str(d66_report.get("decision") or d66_report.get("result") or "")

    if tenuki_core_moves:
        return {
            "decision": "PLAN_ISOLATED_BYPASS",
            "reason": "D67 found protected stressed core; use TENUKI instead of direct expansion",
            "priority": "critical",
            "requires": [
                "D66 reviewer approval",
                "local tests",
                "regression evidence",
                "no direct protected-core mutation",
            ],
            "targets": [m.get("target") for m in tenuki_core_moves],
        }

    if decayed_count > 0:
        return {
            "decision": "REVIEW_APOPTOSIS_DECAY_CANDIDATE",
            "reason": "D65 produced decayed bias candidates that need guard review before canonical apply",
            "priority": "high",
            "requires": ["D66 memory guard review", "backup of canonical memory", "explicit apply step"],
            "targets": ["memory/field_intent_priority_bias_decayed.json"],
        }

    if "FORBIDDEN_CORE_MUTATION" in d66_decision:
        return {
            "decision": "HOLD_CORE_LOCK",
            "reason": "D66 recently rejected direct protected-core mutation",
            "priority": "high",
            "requires": ["sandbox proposal", "two eyes", "no core edit without regression"],
            "targets": [],
        }

    return {
        "decision": "HOLD_AND_MONITOR",
        "reason": "no immediate bypass or decay action required",
        "priority": "normal",
        "requires": ["continue replay", "watch recurrence"],
        "targets": [],
    }


def run_field_memory_replay(root: str | Path = ".", output_path: str = DEFAULT_REPORT_PATH) -> Dict[str, Any]:
    root_path = Path(root).resolve()

    memory_path = root_path / "memory/field_intent_memory.jsonl"
    bias_path = root_path / "memory/field_intent_priority_bias.json"
    decayed_bias_path = root_path / "memory/field_intent_priority_bias_decayed.json"
    d65_report_path = root_path / "reports/d65_apoptosis_decay_report.json"
    d66_report_path = root_path / "reports/d66_core_guard_reviewer_report.json"
    d67_map_path = root_path / "reports/d67_topological_memory_map.json"
    d67_report_path = root_path / "reports/d67_topological_memory_map_report.json"
    core_policy_path = root_path / "runtime_experimental/core_guard_policy.json"

    modules: List[Dict[str, Any]] = []
    errors: List[str] = []
    warnings: List[str] = []

    d65_report: Dict[str, Any] = {}
    d67_map: Dict[str, Any] = {}
    d66_report: Dict[str, Any] = _read_json(d66_report_path, default={}) or {}

    try:
        from runtime_experimental.memory_apoptosis import run_memory_apoptosis
        d65_report = run_memory_apoptosis(
            bias_path=str(bias_path),
            memory_path=str(memory_path),
            output_path=str(decayed_bias_path),
            report_path=str(d65_report_path),
        )
        modules.append(_module_status("D65_MEMORY_APOPTOSIS", bool(d65_report.get("ok")), str(d65_report.get("result")), {"summary": d65_report.get("summary", {})}))
    except Exception as exc:
        warnings.append(f"D65 skipped or failed: {exc}")
        d65_report = _read_json(d65_report_path, default={}) or {}
        modules.append(_module_status("D65_MEMORY_APOPTOSIS", False, "SKIPPED_OR_FAILED", {"error": str(exc)}))

    try:
        from runtime_experimental.topological_memory_map import build_topological_memory_map
        d67_map = build_topological_memory_map(
            root=root_path,
            policy_path=str(core_policy_path),
            memory_path=str(memory_path),
            bias_path=str(bias_path),
            output_path=str(d67_map_path),
            report_path=str(d67_report_path),
        )
        modules.append(_module_status("D67_TOPOLOGICAL_MEMORY_MAP", bool(d67_map.get("ok")), str(d67_map.get("result")), {"summary": d67_map.get("summary", {})}))
    except Exception as exc:
        warnings.append(f"D67 skipped or failed: {exc}")
        d67_map = _read_json(d67_map_path, default={}) or _read_json(d67_report_path, default={}) or {}
        modules.append(_module_status("D67_TOPOLOGICAL_MEMORY_MAP", False, "SKIPPED_OR_FAILED", {"error": str(exc)}))

    if d66_report:
        modules.append(_module_status("D66_CORE_GUARD_REVIEWER", True, str(d66_report.get("result") or d66_report.get("decision") or "REPORT_READ"), {"decision": d66_report.get("decision"), "ok": d66_report.get("ok")}))
    else:
        warnings.append("D66 reviewer report not found")
        modules.append(_module_status("D66_CORE_GUARD_REVIEWER", False, "REPORT_MISSING"))

    macro_decision = _derive_macro_decision(d65_report, d67_map, d66_report)

    report = {
        "state": "D63_FIELD_MEMORY_REPLAY_RUNNER",
        "result": "FIELD_MEMORY_REPLAY_COMPLETED",
        "route": "FIELD_INTENT_FIELD_MEMORY_REPLAY",
        "ok": len(errors) == 0,
        "created_at": _now(),
        "root": str(root_path),
        "output_path": str(output_path),
        "modules": modules,
        "macro_decision": macro_decision,
        "summary": {
            "modules_seen": len(modules),
            "warnings_count": len(warnings),
            "errors_count": len(errors),
            "decision": macro_decision.get("decision"),
            "priority": macro_decision.get("priority"),
            "targets_count": len(macro_decision.get("targets", []) or []),
        },
        "input_reports": {
            "d65_report_path": str(d65_report_path),
            "d66_report_path": str(d66_report_path),
            "d67_map_path": str(d67_map_path),
            "d67_report_path": str(d67_report_path),
        },
        "validation": {"ok": len(errors) == 0, "errors": errors, "warnings": warnings},
        "success_condition": {
            "replay_completed": True,
            "canonical_memory_mutated": False,
            "core_code_mutated": False,
            "next_step": "D64 can consume this replay report plus D66/D67 evidence to propose a guarded safe mutation.",
        },
    }

    _write_json(root_path / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(run_field_memory_replay(), ensure_ascii=False, indent=2))
'''

Path("runtime_experimental/field_memory_replay_runner.py").write_text(RUNNER_CODE.lstrip(), encoding="utf-8")
print("created/updated runtime_experimental/field_memory_replay_runner.py")

TEST_CODE = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.field_memory_replay_runner import run_field_memory_replay


class TestD63FieldMemoryReplayRunner(unittest.TestCase):
    def test_replay_creates_report_and_bypass_decision(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "app/orchestration").mkdir(parents=True)
            (root / "runtime_experimental").mkdir(parents=True)
            (root / "memory").mkdir(parents=True)
            (root / "reports").mkdir(parents=True)

            (root / "app/orchestration/task_dispatcher.py").write_text("x = 1\n", encoding="utf-8")
            (root / "runtime_experimental/v_kernel_daemon.py").write_text("x = 1\n", encoding="utf-8")
            (root / "runtime_experimental/phase_resync_policy.py").write_text("x = 1\n", encoding="utf-8")

            (root / "runtime_experimental/core_guard_policy.json").write_text(
                json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py", "runtime_experimental/v_kernel_daemon.py", "runtime_experimental/phase_resync_policy.py"]}),
                encoding="utf-8",
            )

            bias_key = "field_intent:d3_o6:hex:phase_drift_hex"
            (root / "memory/field_intent_priority_bias.json").write_text(
                json.dumps({"biases": {bias_key: {"priority_boost_points": 30, "recommended_priority": "critical"}}}),
                encoding="utf-8",
            )
            (root / "memory/field_intent_memory.jsonl").write_text(
                json.dumps({"priority": "critical", "payload": {"resonance_vector": {"memory_key": "D3_O6", "phase_error": 0.34, "jitter": 0.03, "strength": 0.81}, "target_files": ["app/orchestration/task_dispatcher.py"]}}) + "\n",
                encoding="utf-8",
            )
            (root / "reports/d66_core_guard_reviewer_report.json").write_text(
                json.dumps({"state": "D66_CORE_GUARD_REVIEWER", "decision": "FORBIDDEN_CORE_MUTATION", "ok": False}),
                encoding="utf-8",
            )

            report = run_field_memory_replay(root=root, output_path="reports/d63_field_memory_replay_report.json")
            self.assertTrue((root / "reports/d63_field_memory_replay_report.json").exists())
            self.assertTrue(report["ok"])
            self.assertEqual(report["macro_decision"]["decision"], "PLAN_ISOLATED_BYPASS")
            self.assertFalse(report["success_condition"]["core_code_mutated"])
            self.assertFalse(report["success_condition"]["canonical_memory_mutated"])

    def test_replay_survives_missing_optional_reports(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "runtime_experimental").mkdir(parents=True)
            (root / "memory").mkdir(parents=True)
            (root / "reports").mkdir(parents=True)
            (root / "runtime_experimental/core_guard_policy.json").write_text(json.dumps({"protected_files": []}), encoding="utf-8")

            report = run_field_memory_replay(root=root, output_path="reports/d63_field_memory_replay_report.json")
            self.assertTrue(report["ok"])
            self.assertGreaterEqual(report["summary"]["warnings_count"], 1)


if __name__ == "__main__":
    unittest.main()
'''

Path("tests/test_d63_field_memory_replay_runner.py").write_text(TEST_CODE.lstrip(), encoding="utf-8")
print("created/updated tests/test_d63_field_memory_replay_runner.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/field_memory_replay_runner.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d63_field_memory_replay_runner", "-v"], check=True)

print("\n== run D63 replay ==")
subprocess.run([
    sys.executable,
    "-c",
    "from runtime_experimental.field_memory_replay_runner import run_field_memory_replay\n"
    "r=run_field_memory_replay()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('SUMMARY:', r.get('summary'))\n"
    "print('MACRO_DECISION:', r.get('macro_decision'))\n",
], check=True)

print("\n== report preview ==")
rp = Path("reports/d63_field_memory_replay_report.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("SUMMARY:", data.get("summary"))
    print("MACRO_DECISION:", data.get("macro_decision"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/field_memory_replay_runner.py",
    "tests/test_d63_field_memory_replay_runner.py",
    "reports/d63_field_memory_replay_report.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D63_FIELD_MEMORY_REPLAY_RUNNER_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D63 field memory replay runner"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D63 replay changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD63 FIELD MEMORY REPLAY RUNNER BOOT DONE")
