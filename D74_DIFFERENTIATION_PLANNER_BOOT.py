#!/usr/bin/env python3
# D74_DIFFERENTIATION_PLANNER_BOOT.py
# Adds D74 Differentiation Planner to GitCube OS.
# Run from repo root:
#     python D74_DIFFERENTIATION_PLANNER_BOOT.py
# Creates:
# - runtime_experimental/differentiation_planner.py
# - tests/test_d74_differentiation_planner.py
# - reports/d74_differentiation_plan.json
#
# D74 is PLAN-ONLY. It does not mutate protected core, canonical memory,
# task_dispatcher.py, v_kernel_daemon.py, or runtime routes.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PLANNER_CODE = r'''
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_D73_PACKAGE = "reports/d73_guarded_apply_dry_run_package.json"
DEFAULT_D67_REPORT = "reports/d67_topological_memory_map_report.json"
DEFAULT_D67_MAP = "reports/d67_topological_memory_map.json"
DEFAULT_D65_REPORT = "reports/d65_apoptosis_decay_report.json"
DEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"
DEFAULT_OUTPUT = "reports/d74_differentiation_plan.json"


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
    raw = str(path_value or "").strip().replace("\\", "/").lstrip("/")
    parts: List[str] = []
    for part in raw.split("/"):
        if not part or part == "." or part == "..":
            continue
        parts.append(part)
    return "/".join(parts)


def _slug(path_value: str) -> str:
    rel = _safe_relative_path(path_value)
    cleaned = rel.replace("/", "_").replace(".", "_").replace("-", "_")
    cleaned = "".join(ch.lower() if ch.isalnum() or ch == "_" else "_" for ch in cleaned)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "unknown_node"


def _sha256_json(data: Dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:
    for key in ("protected_files", "immutable_core", "core_files"):
        value = policy.get(key)
        if isinstance(value, list):
            return [str(v) for v in value]
    return []


def _extract_topology_moves(d67_report: Dict[str, Any], d67_map: Dict[str, Any]) -> List[Dict[str, Any]]:
    for source in (d67_report, d67_map):
        for key in ("top_suggested_moves", "suggested_moves"):
            moves = source.get(key)
            if isinstance(moves, list) and moves:
                return [m for m in moves if isinstance(m, dict)]
    return []


def _extract_targets_from_d73(d73: Dict[str, Any]) -> List[str]:
    pkg = d73.get("dry_run_package") if isinstance(d73.get("dry_run_package"), dict) else {}
    targets: List[str] = []

    route_diff = pkg.get("simulated_route_diff")
    if isinstance(route_diff, list):
        for item in route_diff:
            if not isinstance(item, dict):
                continue
            scope = item.get("target_scope")
            if isinstance(scope, list):
                targets.extend(str(x) for x in scope if x)

    candidates = pkg.get("sandbox_candidates")
    if isinstance(candidates, list):
        targets.extend(str(x) for x in candidates if x)

    seen = set()
    out: List[str] = []
    for t in targets:
        rel = _safe_relative_path(t)
        if rel and rel not in seen:
            seen.add(rel)
            out.append(rel)
    return out


def _move_to_target(move: Dict[str, Any]) -> str:
    for key in ("target", "node", "path", "file", "source_node"):
        value = move.get(key)
        if value:
            return _safe_relative_path(str(value))
    return ""


def _move_to_pain(move: Dict[str, Any]) -> float:
    for key in ("pain_score", "score", "stress", "weight"):
        try:
            return float(move.get(key))
        except Exception:
            pass
    return 0.0


def _classify_gradient(target: str, reason: str) -> Dict[str, str]:
    text = (target + " " + reason).lower()
    if "dispatcher" in text or "route" in text:
        return {"role": "route_policy_child", "intent": "separate routing pressure from core dispatcher"}
    if "memory" in text or "bias" in text or "apoptosis" in text:
        return {"role": "memory_policy_child", "intent": "separate memory pressure from canonical memory"}
    if "daemon" in text or "kernel" in text:
        return {"role": "daemon_bridge_child", "intent": "separate daemon bridge pressure from kernel loop"}
    if "phase" in text or "resync" in text:
        return {"role": "phase_resync_child", "intent": "separate phase repair pressure into isolated policy"}
    return {"role": "specialized_child", "intent": "separate overloaded responsibility into isolated module"}


def _build_candidate(target: str, pain_score: float, protected: bool, reason: str, move_type: str, index: int) -> Dict[str, Any]:
    gradient = _classify_gradient(target, reason)
    slug = _slug(target)
    child_module = f"runtime_experimental/differentiated_modules/{index:02d}_{slug}_{gradient['role']}.py"
    test_module = f"tests/test_d74_{index:02d}_{slug}_{gradient['role']}.py"
    return {
        "source_node": target,
        "pain_score": pain_score,
        "protected_core": protected,
        "differentiation_type": "TENUKI_CHILD_MODULE",
        "gradient_role": gradient["role"],
        "gradient_intent": gradient["intent"],
        "recommended_child_module": child_module,
        "recommended_test_module": test_module,
        "integration_strategy": "narrow_adapter_route_after_D66_recheck",
        "old_node_policy": "do_not_expand_directly",
        "apoptosis_policy": "after child module is stable, reduce pressure on old node through D65 decay",
        "reason": reason or "topology pressure suggests isolated child module",
        "move_type": move_type or "TENUKI",
        "required_gates": [
            "D73_PACKAGE_READY",
            "D66_RECHECK",
            "UNIT_TESTS",
            "REGRESSION_TESTS",
            "ROLLBACK_MANIFEST",
            "HUMAN_OR_HIGHER_POLICY_APPROVAL",
        ],
    }


def build_differentiation_plan(
    root: str | Path = ".",
    d73_package_path: str = DEFAULT_D73_PACKAGE,
    d67_report_path: str = DEFAULT_D67_REPORT,
    d67_map_path: str = DEFAULT_D67_MAP,
    d65_report_path: str = DEFAULT_D65_REPORT,
    core_policy_path: str = DEFAULT_CORE_POLICY,
    output_path: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()

    d73 = _read_json(root_path / d73_package_path, default={}) or {}
    d67_report = _read_json(root_path / d67_report_path, default={}) or {}
    d67_map = _read_json(root_path / d67_map_path, default={}) or {}
    d65 = _read_json(root_path / d65_report_path, default={}) or {}
    policy = _read_json(root_path / core_policy_path, default={}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    if not d73:
        errors.append("D73 guarded apply dry-run package missing or unreadable")
    else:
        if d73.get("ok") is not True:
            errors.append("D73 ok flag is not true")
        if d73.get("decision") != "GUARDED_APPLY_DRY_RUN_PACKAGE_READY":
            errors.append(f"D73 decision is not GUARDED_APPLY_DRY_RUN_PACKAGE_READY: {d73.get('decision')}")
        guardrails = d73.get("guardrails") if isinstance(d73.get("guardrails"), dict) else {}
        if guardrails.get("actual_apply_executed") is not False:
            errors.append("D73 actual_apply_executed is not false")
        if guardrails.get("package_only") is not True:
            errors.append("D73 package_only is not true")

    if not d67_report and not d67_map:
        warnings.append("D67 topology evidence missing; falling back to D73 targets only")
    if not d65:
        warnings.append("D65 apoptosis evidence missing; plan will still require decay policy later")
    if not policy:
        warnings.append("core guard policy missing or unreadable")

    protected_files = _protected_files_from_policy(policy)
    protected_set = set(protected_files)

    target_records: List[Dict[str, Any]] = []
    for move in _extract_topology_moves(d67_report, d67_map):
        target = _move_to_target(move)
        if target:
            target_records.append({
                "target": target,
                "pain_score": _move_to_pain(move),
                "reason": str(move.get("reason", "")),
                "move_type": str(move.get("move_type", move.get("recommendation", "TENUKI"))),
            })

    existing = {r["target"] for r in target_records}
    for target in _extract_targets_from_d73(d73):
        if target not in existing:
            target_records.append({
                "target": target,
                "pain_score": 0.5,
                "reason": "D73 dry-run package target requires differentiation review",
                "move_type": "TENUKI",
            })
            existing.add(target)

    target_records.sort(key=lambda r: (-float(r.get("pain_score", 0.0)), str(r.get("target", ""))))

    if not target_records:
        errors.append("No topology targets available for differentiation planning")

    candidates: List[Dict[str, Any]] = []
    for idx, record in enumerate(target_records[:8], start=1):
        target = _safe_relative_path(record["target"])
        candidates.append(_build_candidate(
            target=target,
            pain_score=float(record.get("pain_score", 0.0)),
            protected=target in protected_set,
            reason=str(record.get("reason", "")),
            move_type=str(record.get("move_type", "TENUKI")),
            index=idx,
        ))

    plan_core = {
        "candidate_count": len(candidates),
        "targets": [c["source_node"] for c in candidates],
        "d73_decision": d73.get("decision"),
    }
    plan_id = "d74-" + _sha256_json(plan_core)[:16]

    ok = len(errors) == 0
    decision = "DIFFERENTIATION_PLAN_READY" if ok else "DIFFERENTIATION_PLAN_BLOCKED"
    result = "D74_DIFFERENTIATION_PLAN_CREATED" if ok else "D74_DIFFERENTIATION_PLAN_BLOCKED"

    differentiation_plan = {
        "plan_id": plan_id,
        "enabled": ok,
        "mode": "PLAN_ONLY_NO_CODE_MUTATION",
        "principle": "do not expand stressed core directly; create isolated child modules and route through narrow adapters",
        "candidates": candidates,
        "required_next_gates": [
            "D66_RECHECK",
            "D73_PACKAGE_READY",
            "UNIT_TESTS",
            "REGRESSION_TESTS",
            "ROLLBACK_MANIFEST",
            "HUMAN_OR_HIGHER_POLICY_APPROVAL",
        ],
        "forbidden_actions": [
            "direct_core_edit",
            "overwrite_canonical_memory",
            "auto_commit_runtime_mutation",
            "apply_without_D66_recheck",
            "apply_without_rollback",
        ],
        "next_allowed_actions": [
            "generate child-module scaffold proposal",
            "generate tests for first child module",
            "run sandbox-only probes",
            "prepare D75 differentiation scaffold package",
        ],
    }

    report = {
        "state": "D74_DIFFERENTIATION_PLANNER",
        "result": result,
        "route": "FIELD_INTENT_DIFFERENTIATION_PLANNER",
        "ok": ok,
        "decision": decision,
        "created_at": _now(),
        "plan_id": plan_id,
        "differentiation_plan": differentiation_plan,
        "input_reports": {
            "d73_package_path": str(root_path / d73_package_path),
            "d67_report_path": str(root_path / d67_report_path),
            "d67_map_path": str(root_path / d67_map_path),
            "d65_report_path": str(root_path / d65_report_path),
            "core_policy_path": str(root_path / core_policy_path),
        },
        "evidence": {
            "d73_decision": d73.get("decision"),
            "d73_ok": d73.get("ok"),
            "d67_result": d67_report.get("result") or d67_map.get("result"),
            "d65_result": d65.get("result"),
            "protected_files_count": len(protected_files),
            "target_records_count": len(target_records),
        },
        "guardrails": {
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "plan_only": True,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": warnings},
        "summary": {
            "decision": decision,
            "plan_id": plan_id,
            "candidate_count": len(candidates),
            "protected_candidate_count": sum(1 for c in candidates if c.get("protected_core")),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "differentiation_plan_created": ok,
            "actual_apply_executed": False,
            "next_step": "D75 can scaffold the first isolated child module proposal, still sandbox-only.",
        },
    }

    _write_json(root_path / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(build_differentiation_plan(), ensure_ascii=False, indent=2))
'''

TEST_CODE = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.differentiation_planner import build_differentiation_plan


class TestD74DifferentiationPlanner(unittest.TestCase):
    def make_valid_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True)
        (root / "runtime_experimental").mkdir(parents=True)
        target = "app/orchestration/task_dispatcher.py"

        (root / "runtime_experimental/core_guard_policy.json").write_text(
            json.dumps({"protected_files": [target]}), encoding="utf-8"
        )
        (root / "reports/d73_guarded_apply_dry_run_package.json").write_text(
            json.dumps({
                "ok": True,
                "decision": "GUARDED_APPLY_DRY_RUN_PACKAGE_READY",
                "guardrails": {"actual_apply_executed": False, "package_only": True},
                "dry_run_package": {
                    "sandbox_candidates": ["runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"],
                    "simulated_route_diff": [{"target_scope": [target]}],
                },
            }), encoding="utf-8"
        )
        (root / "reports/d67_topological_memory_map_report.json").write_text(
            json.dumps({
                "result": "D67_MAP_BUILD_COMPLETED",
                "top_suggested_moves": [{
                    "target": target,
                    "pain_score": 0.91,
                    "move_type": "TENUKI",
                    "reason": "protected core has stress; direct expansion risks core mutation",
                }],
            }), encoding="utf-8"
        )
        return td, root, target

    def test_creates_differentiation_plan(self):
        td, root, target = self.make_valid_root()
        try:
            report = build_differentiation_plan(root=root)
            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "DIFFERENTIATION_PLAN_READY")
            self.assertFalse(report["guardrails"]["actual_apply_executed"])
            self.assertTrue(report["guardrails"]["plan_only"])
            self.assertGreaterEqual(report["summary"]["candidate_count"], 1)
            candidate = report["differentiation_plan"]["candidates"][0]
            self.assertEqual(candidate["source_node"], target)
            self.assertTrue(candidate["protected_core"])
            self.assertEqual(candidate["old_node_policy"], "do_not_expand_directly")
            self.assertTrue((root / "reports/d74_differentiation_plan.json").exists())
        finally:
            td.cleanup()

    def test_blocks_when_d73_missing(self):
        td, root, _ = self.make_valid_root()
        try:
            (root / "reports/d73_guarded_apply_dry_run_package.json").unlink()
            report = build_differentiation_plan(root=root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "DIFFERENTIATION_PLAN_BLOCKED")
        finally:
            td.cleanup()

    def test_falls_back_to_d73_targets_without_d67(self):
        td, root, _ = self.make_valid_root()
        try:
            (root / "reports/d67_topological_memory_map_report.json").unlink()
            report = build_differentiation_plan(root=root)
            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "DIFFERENTIATION_PLAN_READY")
            self.assertGreaterEqual(report["summary"]["warnings_count"], 1)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
'''


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

print("D74 DIFFERENTIATION PLANNER BOOT: repo =", ROOT)

Path("runtime_experimental/differentiation_planner.py").write_text(PLANNER_CODE, encoding="utf-8")
print("created/updated runtime_experimental/differentiation_planner.py")

Path("tests/test_d74_differentiation_planner.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d74_differentiation_planner.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/differentiation_planner.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d74_differentiation_planner", "-v"], check=True)

print("\n== run D74 differentiation planner ==")
subprocess.run([
    sys.executable,
    "-c",
    "from runtime_experimental.differentiation_planner import build_differentiation_plan\n"
    "r=build_differentiation_plan()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('PLAN_ID:', r.get('plan_id'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
rp = Path("reports/d74_differentiation_plan.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("PLAN_ID:", data.get("plan_id"))
    print("SUMMARY:", data.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/differentiation_planner.py",
    "tests/test_d74_differentiation_planner.py",
    "reports/d74_differentiation_plan.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D74_DIFFERENTIATION_PLANNER_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D74 differentiation planner"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D74 differentiation planner changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD74 DIFFERENTIATION PLANNER BOOT DONE")
