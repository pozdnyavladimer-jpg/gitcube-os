#!/usr/bin/env python3
# D72_REVIEWED_APPLY_PLAN_BOOT.py
#
# Adds D72 Reviewed Apply Plan to GitCube OS.
#
# Run from repo root:
#     python D72_REVIEWED_APPLY_PLAN_BOOT.py
#
# Creates:
# - runtime_experimental/reviewed_apply_plan.py
# - tests/test_d72_reviewed_apply_plan.py
# - reports/d72_reviewed_apply_plan.json
#
# D72 does NOT call an external AI API.
# D72 does NOT patch task_dispatcher.py.
# D72 does NOT mutate protected core.
# D72 does NOT overwrite canonical memory.
# D72 does NOT apply sandbox files to runtime.
#
# D72 packages D64 + D71 into a reviewed apply plan with rollback gates.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PLAN_CODE = 'from __future__ import annotations\nimport hashlib, json\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nfrom typing import Any, Dict, List\n\nDEFAULT_D64_REQUEST = "reports/d64_safe_mutation_gate_request.json"\nDEFAULT_D71_DRY_RUN = "reports/d71_route_dry_run_simulation.json"\nDEFAULT_D66_REVIEW = "reports/d66_core_guard_reviewer_report.json"\nDEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"\nDEFAULT_OUTPUT = "reports/d72_reviewed_apply_plan.json"\n\ndef _now() -> str:\n    return datetime.now(timezone.utc).isoformat()\n\ndef _read_json(path: str | Path, default: Any = None) -> Any:\n    p = Path(path)\n    if not p.exists():\n        return default\n    try:\n        return json.loads(p.read_text(encoding="utf-8"))\n    except Exception:\n        return default\n\ndef _write_json(path: str | Path, data: Dict[str, Any]) -> None:\n    p = Path(path)\n    p.parent.mkdir(parents=True, exist_ok=True)\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")\n\ndef _safe_relative_path(path_value: str) -> str:\n    raw = str(path_value or "").strip().replace("\\\\", "/").lstrip("/")\n    return "/".join(part for part in raw.split("/") if part and part not in (".", ".."))\n\ndef _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:\n    for key in ("protected_files", "immutable_core", "core_files"):\n        value = policy.get(key)\n        if isinstance(value, list):\n            return [str(v) for v in value]\n    return []\n\ndef _sha256_json(data: Dict[str, Any]) -> str:\n    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()\n\ndef _validate_route_diff(route_diff: List[Dict[str, Any]], errors: List[str]) -> None:\n    if not route_diff:\n        errors.append("D71 simulated_route_diff is empty")\n        return\n    for idx, item in enumerate(route_diff):\n        if not isinstance(item, dict):\n            errors.append(f"D71 route diff item {idx} is not a dict")\n            continue\n        if item.get("dry_run_only") is not True:\n            errors.append(f"D71 route diff item {idx} is not dry_run_only")\n        if item.get("would_touch_protected_core") is not False:\n            errors.append(f"D71 route diff item {idx} would touch protected core")\n        if item.get("would_touch_canonical_memory") is not False:\n            errors.append(f"D71 route diff item {idx} would touch canonical memory")\n        if item.get("would_execute_runtime_mutation") is not False:\n            errors.append(f"D71 route diff item {idx} would execute runtime mutation")\n        handler = _safe_relative_path(str(item.get("sandbox_handler", "")))\n        if not handler.startswith("runtime_experimental/ai_bypass_proposals/"):\n            errors.append(f"D71 route diff item {idx} has non-sandbox handler: {handler}")\n\ndef build_reviewed_apply_plan(\n    root: str | Path = ".",\n    d64_request_path: str = DEFAULT_D64_REQUEST,\n    d71_dry_run_path: str = DEFAULT_D71_DRY_RUN,\n    d66_review_path: str = DEFAULT_D66_REVIEW,\n    core_policy_path: str = DEFAULT_CORE_POLICY,\n    output_path: str = DEFAULT_OUTPUT,\n) -> Dict[str, Any]:\n    root_path = Path(root).resolve()\n    d64 = _read_json(root_path / d64_request_path, default={}) or {}\n    d71 = _read_json(root_path / d71_dry_run_path, default={}) or {}\n    d66 = _read_json(root_path / d66_review_path, default={}) or {}\n    policy = _read_json(root_path / core_policy_path, default={}) or {}\n\n    errors: List[str] = []\n    warnings: List[str] = []\n    if not d64:\n        errors.append("D64 safe mutation gate request missing or unreadable")\n    if not d71:\n        errors.append("D71 route dry-run simulation missing or unreadable")\n    if not d66:\n        warnings.append("D66 core guard reviewer report missing or unreadable")\n    if not policy:\n        warnings.append("core guard policy missing or unreadable")\n\n    if d64:\n        if d64.get("ok") is not True:\n            errors.append("D64 ok flag is not true")\n        if d64.get("decision") != "CREATE_GUARDED_APPLY_REQUEST":\n            errors.append(f"D64 decision is not CREATE_GUARDED_APPLY_REQUEST: {d64.get(\'decision\')}")\n        d64_guardrails = d64.get("guardrails") if isinstance(d64.get("guardrails"), dict) else {}\n        if d64_guardrails.get("actual_apply_executed") is not False:\n            errors.append("D64 actual_apply_executed is not false")\n        if d64_guardrails.get("gate_only") is not True:\n            errors.append("D64 gate_only is not true")\n\n    if d71:\n        if d71.get("ok") is not True:\n            errors.append("D71 ok flag is not true")\n        if d71.get("decision") != "ROUTE_DRY_RUN_APPROVED":\n            errors.append(f"D71 decision is not ROUTE_DRY_RUN_APPROVED: {d71.get(\'decision\')}")\n        d71_guardrails = d71.get("guardrails") if isinstance(d71.get("guardrails"), dict) else {}\n        if d71_guardrails.get("actual_apply_executed") is not False:\n            errors.append("D71 actual_apply_executed is not false")\n        if d71_guardrails.get("dry_run_only") is not True:\n            errors.append("D71 dry_run_only is not true")\n\n    d64_request = d64.get("guarded_apply_request") if isinstance(d64.get("guarded_apply_request"), dict) else {}\n    if d64_request and d64_request.get("enabled") is not True:\n        errors.append("D64 guarded apply request is not enabled")\n\n    route_diff = d71.get("simulated_route_diff") if isinstance(d71.get("simulated_route_diff"), list) else []\n    _validate_route_diff(route_diff, errors)\n\n    sandbox_candidates_raw = d64_request.get("sandbox_candidates", [])\n    sandbox_candidates = [_safe_relative_path(str(x)) for x in sandbox_candidates_raw if x] if isinstance(sandbox_candidates_raw, list) else []\n    if not sandbox_candidates:\n        errors.append("D64 sandbox candidates missing")\n\n    protected_files = _protected_files_from_policy(policy)\n    target_scope = d71.get("target_scope") if isinstance(d71.get("target_scope"), list) else []\n\n    plan_id = "d72-" + _sha256_json({\n        "sandbox_candidates": sandbox_candidates,\n        "route_diff_count": len(route_diff),\n        "target_scope": target_scope,\n    })[:16]\n\n    approved = len(errors) == 0\n    decision = "REVIEWED_APPLY_PLAN_READY" if approved else "REVIEWED_APPLY_PLAN_BLOCKED"\n    result = "D72_REVIEWED_APPLY_PLAN_CREATED" if approved else "D72_REVIEWED_APPLY_PLAN_BLOCKED"\n\n    reviewed_apply_plan = {\n        "plan_id": plan_id,\n        "enabled": approved,\n        "apply_mode": "MANUAL_GUARDED_APPLY_ONLY",\n        "status": decision,\n        "sandbox_candidates": sandbox_candidates,\n        "simulated_route_diff": route_diff,\n        "target_scope": target_scope,\n        "rollback_plan": {\n            "required": True,\n            "mode": "PRE_APPLY_BACKUP_AND_REVERT",\n            "backup_targets": protected_files,\n            "rollback_artifacts_required": [\n                "pre_apply_git_sha",\n                "protected_file_backup_manifest",\n                "post_apply_validation_report",\n            ],\n            "rollback_command_policy": "git_restore_or_revert_only_after_human_review",\n        },\n        "required_gates_before_real_apply": [\n            "D66_REVIEWER_RECHECK",\n            "D71_DRY_RUN_APPROVED",\n            "UNIT_TESTS",\n            "REGRESSION_TESTS",\n            "ROLLBACK_PLAN_READY",\n            "HUMAN_OR_HIGHER_POLICY_APPROVAL",\n        ],\n        "forbidden_actions": [\n            "direct_core_edit_without_guarded_route",\n            "overwrite_canonical_memory",\n            "auto_commit_runtime_mutation",\n            "apply_without_rollback",\n            "apply_without_D66_recheck",\n        ],\n        "next_allowed_actions": [\n            "generate pre-apply backup manifest",\n            "run D66 reviewer recheck on this plan",\n            "run full unit/regression suite",\n            "prepare D73 guarded apply dry-run package",\n        ],\n    }\n\n    report = {\n        "state": "D72_REVIEWED_APPLY_PLAN",\n        "result": result,\n        "route": "FIELD_INTENT_REVIEWED_APPLY_PLAN",\n        "ok": approved,\n        "decision": decision,\n        "created_at": _now(),\n        "plan_id": plan_id,\n        "reviewed_apply_plan": reviewed_apply_plan,\n        "input_reports": {\n            "d64_request_path": str(root_path / d64_request_path),\n            "d71_dry_run_path": str(root_path / d71_dry_run_path),\n            "d66_review_path": str(root_path / d66_review_path),\n            "core_policy_path": str(root_path / core_policy_path),\n        },\n        "evidence": {\n            "d64_decision": d64.get("decision"),\n            "d64_ok": d64.get("ok"),\n            "d71_decision": d71.get("decision"),\n            "d71_ok": d71.get("ok"),\n            "d66_decision": d66.get("decision"),\n            "route_diff_count": len(route_diff),\n            "sandbox_candidates_count": len(sandbox_candidates),\n        },\n        "guardrails": {\n            "runtime_code_mutated": False,\n            "protected_core_mutated": False,\n            "canonical_memory_mutated": False,\n            "external_ai_called": False,\n            "actual_apply_executed": False,\n            "plan_only": True,\n        },\n        "validation": {"ok": approved, "errors": errors, "warnings": warnings},\n        "summary": {\n            "decision": decision,\n            "plan_id": plan_id,\n            "sandbox_candidates_count": len(sandbox_candidates),\n            "route_diff_count": len(route_diff),\n            "protected_files_count": len(protected_files),\n            "errors_count": len(errors),\n            "warnings_count": len(warnings),\n        },\n        "success_condition": {\n            "reviewed_apply_plan_created": approved,\n            "actual_apply_executed": False,\n            "rollback_required": True,\n            "next_step": "D73 can prepare a guarded apply dry-run package, but no real mutation should run without D66 recheck and rollback evidence.",\n        },\n    }\n    _write_json(root_path / output_path, report)\n    return report\n\nif __name__ == "__main__":\n    print(json.dumps(build_reviewed_apply_plan(), ensure_ascii=False, indent=2))\n'
TEST_CODE = 'import json\nimport tempfile\nimport unittest\nfrom pathlib import Path\n\nfrom runtime_experimental.reviewed_apply_plan import build_reviewed_apply_plan\n\n\nclass TestD72ReviewedApplyPlan(unittest.TestCase):\n    def make_valid_root(self):\n        td = tempfile.TemporaryDirectory()\n        root = Path(td.name)\n        (root / "reports").mkdir(parents=True)\n        (root / "runtime_experimental/ai_bypass_proposals").mkdir(parents=True)\n\n        candidate = "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"\n        (root / candidate).write_text("def run_sandbox_probe(event=None):\\n    return {\'ok\': True}\\n", encoding="utf-8")\n\n        (root / "runtime_experimental/core_guard_policy.json").write_text(\n            json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),\n            encoding="utf-8",\n        )\n        (root / "reports/d64_safe_mutation_gate_request.json").write_text(\n            json.dumps(\n                {\n                    "ok": True,\n                    "decision": "CREATE_GUARDED_APPLY_REQUEST",\n                    "guarded_apply_request": {"enabled": True, "sandbox_candidates": [candidate]},\n                    "guardrails": {"actual_apply_executed": False, "gate_only": True},\n                }\n            ),\n            encoding="utf-8",\n        )\n        (root / "reports/d71_route_dry_run_simulation.json").write_text(\n            json.dumps(\n                {\n                    "ok": True,\n                    "decision": "ROUTE_DRY_RUN_APPROVED",\n                    "target_scope": ["app/orchestration/task_dispatcher.py"],\n                    "guardrails": {"actual_apply_executed": False, "dry_run_only": True},\n                    "simulated_route_diff": [\n                        {\n                            "operation": "SIMULATE_ROUTE_INSERT",\n                            "route_name": "DRY_RUN_DISPATCHER_BYPASS_PROPOSAL",\n                            "sandbox_handler": candidate,\n                            "would_touch_files": [],\n                            "would_touch_protected_core": False,\n                            "would_touch_canonical_memory": False,\n                            "would_execute_runtime_mutation": False,\n                            "dry_run_only": True,\n                        }\n                    ],\n                }\n            ),\n            encoding="utf-8",\n        )\n        return td, root, candidate\n\n    def test_creates_reviewed_apply_plan(self):\n        td, root, candidate = self.make_valid_root()\n        try:\n            report = build_reviewed_apply_plan(root=root)\n            self.assertTrue(report["ok"])\n            self.assertEqual(report["decision"], "REVIEWED_APPLY_PLAN_READY")\n            self.assertFalse(report["guardrails"]["actual_apply_executed"])\n            self.assertTrue(report["guardrails"]["plan_only"])\n            self.assertIn(candidate, report["reviewed_apply_plan"]["sandbox_candidates"])\n            self.assertTrue(report["reviewed_apply_plan"]["rollback_plan"]["required"])\n            self.assertTrue((root / "reports/d72_reviewed_apply_plan.json").exists())\n        finally:\n            td.cleanup()\n\n    def test_blocks_when_d71_rejected(self):\n        td, root, _ = self.make_valid_root()\n        try:\n            (root / "reports/d71_route_dry_run_simulation.json").write_text(\n                json.dumps(\n                    {\n                        "ok": False,\n                        "decision": "ROUTE_DRY_RUN_BLOCKED",\n                        "guardrails": {"actual_apply_executed": False, "dry_run_only": True},\n                        "simulated_route_diff": [],\n                    }\n                ),\n                encoding="utf-8",\n            )\n            report = build_reviewed_apply_plan(root=root)\n            self.assertFalse(report["ok"])\n            self.assertEqual(report["decision"], "REVIEWED_APPLY_PLAN_BLOCKED")\n            self.assertFalse(report["reviewed_apply_plan"]["enabled"])\n        finally:\n            td.cleanup()\n\n    def test_blocks_route_diff_that_touches_core(self):\n        td, root, candidate = self.make_valid_root()\n        try:\n            d71 = json.loads((root / "reports/d71_route_dry_run_simulation.json").read_text(encoding="utf-8"))\n            d71["simulated_route_diff"][0]["would_touch_protected_core"] = True\n            (root / "reports/d71_route_dry_run_simulation.json").write_text(json.dumps(d71), encoding="utf-8")\n\n            report = build_reviewed_apply_plan(root=root)\n            self.assertFalse(report["ok"])\n            self.assertEqual(report["decision"], "REVIEWED_APPLY_PLAN_BLOCKED")\n            self.assertGreaterEqual(report["summary"]["errors_count"], 1)\n        finally:\n            td.cleanup()\n\n\nif __name__ == "__main__":\n    unittest.main()\n'


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

print("D72 REVIEWED APPLY PLAN BOOT: repo =", ROOT)

Path("runtime_experimental/reviewed_apply_plan.py").write_text(PLAN_CODE, encoding="utf-8")
print("created/updated runtime_experimental/reviewed_apply_plan.py")

Path("tests/test_d72_reviewed_apply_plan.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d72_reviewed_apply_plan.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/reviewed_apply_plan.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d72_reviewed_apply_plan", "-v"], check=True)

print("\n== run D72 reviewed apply plan ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.reviewed_apply_plan import build_reviewed_apply_plan\n"
        "r=build_reviewed_apply_plan()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('PLAN_ID:', r.get('plan_id'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d72_reviewed_apply_plan.json")
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
    "runtime_experimental/reviewed_apply_plan.py",
    "tests/test_d72_reviewed_apply_plan.py",
    "reports/d72_reviewed_apply_plan.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D72_REVIEWED_APPLY_PLAN_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D72 reviewed apply plan"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D72 reviewed apply plan changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD72 REVIEWED APPLY PLAN BOOT DONE")
