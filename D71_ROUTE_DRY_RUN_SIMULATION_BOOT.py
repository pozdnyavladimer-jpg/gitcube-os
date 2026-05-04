#!/usr/bin/env python3
# D71_ROUTE_DRY_RUN_SIMULATION_BOOT.py
#
# Adds D71 Route Dry-Run Simulation to GitCube OS.
#
# Run from repo root:
#     python D71_ROUTE_DRY_RUN_SIMULATION_BOOT.py
#
# Creates:
# - runtime_experimental/route_dry_run_simulator.py
# - tests/test_d71_route_dry_run_simulator.py
# - reports/d71_route_dry_run_simulation.json
#
# D71 does NOT call an external AI API.
# D71 does NOT patch task_dispatcher.py.
# D71 does NOT mutate protected core.
# D71 does NOT overwrite canonical memory.
# D71 does NOT apply sandbox files to runtime.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


SIMULATOR_CODE = 'from __future__ import annotations\n\nimport hashlib\nimport json\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nfrom typing import Any, Dict, List\n\n\nDEFAULT_D64_REQUEST = "reports/d64_safe_mutation_gate_request.json"\nDEFAULT_D70_REVIEW = "reports/d70_sandbox_bundle_review.json"\nDEFAULT_D69_BUNDLE = "reports/d69_sandbox_patch_bundle.json"\nDEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"\nDEFAULT_OUTPUT = "reports/d71_route_dry_run_simulation.json"\n\nALLOWED_SANDBOX_PREFIXES = ("runtime_experimental/ai_bypass_proposals/",)\n\n\ndef _now() -> str:\n    return datetime.now(timezone.utc).isoformat()\n\n\ndef _read_json(path: str | Path, default: Any = None) -> Any:\n    p = Path(path)\n    if not p.exists():\n        return default\n    try:\n        return json.loads(p.read_text(encoding="utf-8"))\n    except Exception:\n        return default\n\n\ndef _write_json(path: str | Path, data: Dict[str, Any]) -> None:\n    p = Path(path)\n    p.parent.mkdir(parents=True, exist_ok=True)\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")\n\n\ndef _safe_relative_path(path_value: str) -> str:\n    raw = str(path_value or "").strip().replace("\\\\", "/").lstrip("/")\n    parts: List[str] = []\n    for part in raw.split("/"):\n        if not part or part == "." or part == "..":\n            continue\n        parts.append(part)\n    return "/".join(parts)\n\n\ndef _is_allowed_sandbox_file(path_value: str) -> bool:\n    rel = _safe_relative_path(path_value)\n    return rel.endswith(".py") and any(rel.startswith(prefix) for prefix in ALLOWED_SANDBOX_PREFIXES)\n\n\ndef _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:\n    for key in ("protected_files", "immutable_core", "core_files"):\n        value = policy.get(key)\n        if isinstance(value, list):\n            return [str(v) for v in value]\n    return []\n\n\ndef _hash_file(path: Path) -> str:\n    if not path.exists() or not path.is_file():\n        return ""\n    return hashlib.sha256(path.read_bytes()).hexdigest()\n\n\ndef _route_name_for_candidate(candidate: str) -> str:\n    return "DRY_RUN_" + Path(candidate).stem.upper()\n\n\ndef _extract_targets_from_d64(d64: Dict[str, Any]) -> List[str]:\n    evidence = d64.get("evidence") if isinstance(d64.get("evidence"), dict) else {}\n    macro = evidence.get("macro_decision") if isinstance(evidence.get("macro_decision"), dict) else {}\n    targets = macro.get("targets")\n    if isinstance(targets, list):\n        return [str(x) for x in targets if x]\n\n    request = d64.get("guarded_apply_request") if isinstance(d64.get("guarded_apply_request"), dict) else {}\n    candidates = request.get("sandbox_candidates")\n    if isinstance(candidates, list):\n        return [str(x) for x in candidates if x]\n    return []\n\n\ndef simulate_route_dry_run(\n    root: str | Path = ".",\n    d64_request_path: str = DEFAULT_D64_REQUEST,\n    d70_review_path: str = DEFAULT_D70_REVIEW,\n    d69_bundle_path: str = DEFAULT_D69_BUNDLE,\n    core_policy_path: str = DEFAULT_CORE_POLICY,\n    output_path: str = DEFAULT_OUTPUT,\n) -> Dict[str, Any]:\n    root_path = Path(root).resolve()\n\n    d64 = _read_json(root_path / d64_request_path, default={}) or {}\n    d70 = _read_json(root_path / d70_review_path, default={}) or {}\n    d69 = _read_json(root_path / d69_bundle_path, default={}) or {}\n    policy = _read_json(root_path / core_policy_path, default={}) or {}\n\n    errors: List[str] = []\n    warnings: List[str] = []\n\n    if not d64:\n        errors.append("D64 safe mutation gate request missing or unreadable")\n    if not d70:\n        warnings.append("D70 review missing or unreadable")\n    if not d69:\n        warnings.append("D69 sandbox bundle missing or unreadable")\n    if not policy:\n        warnings.append("core guard policy missing or unreadable")\n\n    if d64:\n        if d64.get("ok") is not True:\n            errors.append("D64 request ok flag is not true")\n        if d64.get("decision") != "CREATE_GUARDED_APPLY_REQUEST":\n            errors.append(f"D64 decision is not CREATE_GUARDED_APPLY_REQUEST: {d64.get(\'decision\')}")\n        guardrails = d64.get("guardrails") if isinstance(d64.get("guardrails"), dict) else {}\n        if guardrails.get("actual_apply_executed") is not False:\n            errors.append("D64 actual_apply_executed is not false")\n        if guardrails.get("gate_only") is not True:\n            errors.append("D64 gate_only is not true")\n\n    guarded_request = d64.get("guarded_apply_request") if isinstance(d64.get("guarded_apply_request"), dict) else {}\n    if guarded_request and guarded_request.get("enabled") is not True:\n        errors.append("D64 guarded apply request is not enabled")\n\n    sandbox_candidates_raw = guarded_request.get("sandbox_candidates", [])\n    sandbox_candidates = [_safe_relative_path(str(x)) for x in sandbox_candidates_raw if x] if isinstance(sandbox_candidates_raw, list) else []\n\n    if not sandbox_candidates:\n        errors.append("No sandbox candidates available for dry-run")\n\n    protected_files = _protected_files_from_policy(policy)\n    targets = _extract_targets_from_d64(d64)\n\n    simulated_route_diff: List[Dict[str, Any]] = []\n    candidate_hashes: Dict[str, str] = {}\n\n    for candidate in sandbox_candidates:\n        candidate_path = root_path / candidate\n\n        if not _is_allowed_sandbox_file(candidate):\n            errors.append(f"D71 rejected non-sandbox candidate: {candidate}")\n            continue\n        if candidate in protected_files:\n            errors.append(f"D71 rejected protected candidate: {candidate}")\n            continue\n        if not candidate_path.exists():\n            errors.append(f"D71 candidate missing on disk: {candidate}")\n            continue\n\n        digest = _hash_file(candidate_path)\n        candidate_hashes[candidate] = digest\n\n        simulated_route_diff.append(\n            {\n                "operation": "SIMULATE_ROUTE_INSERT",\n                "route_name": _route_name_for_candidate(candidate),\n                "sandbox_handler": candidate,\n                "handler_sha256": digest,\n                "target_scope": targets,\n                "would_touch_files": [],\n                "would_touch_protected_core": False,\n                "would_touch_canonical_memory": False,\n                "would_execute_runtime_mutation": False,\n                "dry_run_only": True,\n            }\n        )\n\n    if not simulated_route_diff:\n        errors.append("No valid simulated route diff created")\n\n    if d70 and d70.get("decision") != "APPROVE_SANDBOX_BUNDLE":\n        errors.append(f"D70 decision is not APPROVE_SANDBOX_BUNDLE: {d70.get(\'decision\')}")\n\n    gate_passed = len(errors) == 0\n    decision = "ROUTE_DRY_RUN_APPROVED" if gate_passed else "ROUTE_DRY_RUN_BLOCKED"\n    result = "D71_ROUTE_DRY_RUN_COMPLETED" if gate_passed else "D71_ROUTE_DRY_RUN_BLOCKED"\n\n    report = {\n        "state": "D71_ROUTE_DRY_RUN_SIMULATION",\n        "result": result,\n        "route": "FIELD_INTENT_ROUTE_DRY_RUN_SIMULATION",\n        "ok": gate_passed,\n        "decision": decision,\n        "created_at": _now(),\n        "source_d64_request": str(root_path / d64_request_path),\n        "source_d70_review": str(root_path / d70_review_path),\n        "source_d69_bundle": str(root_path / d69_bundle_path),\n        "sandbox_candidates": sandbox_candidates,\n        "candidate_hashes": candidate_hashes,\n        "protected_files": protected_files,\n        "target_scope": targets,\n        "simulated_route_diff": simulated_route_diff,\n        "guardrails": {\n            "runtime_code_mutated": False,\n            "protected_core_mutated": False,\n            "canonical_memory_mutated": False,\n            "external_ai_called": False,\n            "actual_apply_executed": False,\n            "dry_run_only": True,\n        },\n        "validation": {"ok": gate_passed, "errors": errors, "warnings": warnings},\n        "summary": {\n            "decision": decision,\n            "sandbox_candidates_count": len(sandbox_candidates),\n            "simulated_route_diff_count": len(simulated_route_diff),\n            "protected_files_count": len(protected_files),\n            "errors_count": len(errors),\n            "warnings_count": len(warnings),\n        },\n        "success_condition": {\n            "dry_run_completed": gate_passed,\n            "actual_apply_executed": False,\n            "protected_core_untouched": True,\n            "canonical_memory_untouched": True,\n            "next_step": "D72 can package this dry-run as a reviewed apply plan; D64/D66 must still approve before any real mutation.",\n        },\n    }\n\n    _write_json(root_path / output_path, report)\n    return report\n\n\nif __name__ == "__main__":\n    print(json.dumps(simulate_route_dry_run(), ensure_ascii=False, indent=2))\n'
TEST_CODE = 'import json\nimport tempfile\nimport unittest\nfrom pathlib import Path\n\nfrom runtime_experimental.route_dry_run_simulator import simulate_route_dry_run\n\n\nclass TestD71RouteDryRunSimulator(unittest.TestCase):\n    def make_valid_root(self):\n        td = tempfile.TemporaryDirectory()\n        root = Path(td.name)\n        (root / "reports").mkdir(parents=True)\n        (root / "runtime_experimental/ai_bypass_proposals").mkdir(parents=True)\n\n        rel = "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"\n        (root / rel).write_text("def run_sandbox_probe(event=None):\\\\n    return {\'ok\': True}\\\\n", encoding="utf-8")\n\n        (root / "runtime_experimental/core_guard_policy.json").write_text(\n            json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),\n            encoding="utf-8",\n        )\n        (root / "reports/d64_safe_mutation_gate_request.json").write_text(\n            json.dumps(\n                {\n                    "ok": True,\n                    "decision": "CREATE_GUARDED_APPLY_REQUEST",\n                    "guarded_apply_request": {"enabled": True, "sandbox_candidates": [rel]},\n                    "guardrails": {"actual_apply_executed": False, "gate_only": True},\n                    "evidence": {\n                        "macro_decision": {\n                            "decision": "PLAN_ISOLATED_BYPASS",\n                            "targets": ["app/orchestration/task_dispatcher.py"],\n                        }\n                    },\n                }\n            ),\n            encoding="utf-8",\n        )\n        (root / "reports/d70_sandbox_bundle_review.json").write_text(\n            json.dumps({"ok": True, "decision": "APPROVE_SANDBOX_BUNDLE"}),\n            encoding="utf-8",\n        )\n        (root / "reports/d69_sandbox_patch_bundle.json").write_text(\n            json.dumps({"ok": True, "written_files": [rel]}),\n            encoding="utf-8",\n        )\n        return td, root, rel\n\n    def test_creates_dry_run_route_diff(self):\n        td, root, rel = self.make_valid_root()\n        try:\n            report = simulate_route_dry_run(root=root)\n            self.assertTrue(report["ok"])\n            self.assertEqual(report["decision"], "ROUTE_DRY_RUN_APPROVED")\n            self.assertEqual(report["summary"]["simulated_route_diff_count"], 1)\n            self.assertFalse(report["guardrails"]["actual_apply_executed"])\n            self.assertTrue(report["guardrails"]["dry_run_only"])\n            self.assertEqual(report["simulated_route_diff"][0]["sandbox_handler"], rel)\n            self.assertFalse(report["simulated_route_diff"][0]["would_touch_protected_core"])\n        finally:\n            td.cleanup()\n\n    def test_blocks_when_d64_not_enabled(self):\n        td, root, _ = self.make_valid_root()\n        try:\n            (root / "reports/d64_safe_mutation_gate_request.json").write_text(\n                json.dumps(\n                    {\n                        "ok": False,\n                        "decision": "BLOCK_GUARDED_APPLY",\n                        "guarded_apply_request": {"enabled": False, "sandbox_candidates": []},\n                        "guardrails": {"actual_apply_executed": False, "gate_only": True},\n                    }\n                ),\n                encoding="utf-8",\n            )\n            report = simulate_route_dry_run(root=root)\n            self.assertFalse(report["ok"])\n            self.assertEqual(report["decision"], "ROUTE_DRY_RUN_BLOCKED")\n            self.assertGreaterEqual(report["summary"]["errors_count"], 1)\n        finally:\n            td.cleanup()\n\n    def test_blocks_non_sandbox_candidate(self):\n        td, root, _ = self.make_valid_root()\n        try:\n            (root / "reports/d64_safe_mutation_gate_request.json").write_text(\n                json.dumps(\n                    {\n                        "ok": True,\n                        "decision": "CREATE_GUARDED_APPLY_REQUEST",\n                        "guarded_apply_request": {\n                            "enabled": True,\n                            "sandbox_candidates": ["app/orchestration/task_dispatcher.py"],\n                        },\n                        "guardrails": {"actual_apply_executed": False, "gate_only": True},\n                    }\n                ),\n                encoding="utf-8",\n            )\n            report = simulate_route_dry_run(root=root)\n            self.assertFalse(report["ok"])\n            self.assertEqual(report["decision"], "ROUTE_DRY_RUN_BLOCKED")\n            self.assertEqual(report["summary"]["simulated_route_diff_count"], 0)\n        finally:\n            td.cleanup()\n\n\nif __name__ == "__main__":\n    unittest.main()\n'


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

print("D71 ROUTE DRY-RUN SIMULATION BOOT: repo =", ROOT)

Path("runtime_experimental/route_dry_run_simulator.py").write_text(SIMULATOR_CODE, encoding="utf-8")
print("created/updated runtime_experimental/route_dry_run_simulator.py")

Path("tests/test_d71_route_dry_run_simulator.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d71_route_dry_run_simulator.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/route_dry_run_simulator.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d71_route_dry_run_simulator", "-v"], check=True)

print("\n== run D71 route dry-run simulation ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.route_dry_run_simulator import simulate_route_dry_run\n"
        "r=simulate_route_dry_run()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d71_route_dry_run_simulation.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/route_dry_run_simulator.py",
    "tests/test_d71_route_dry_run_simulator.py",
    "reports/d71_route_dry_run_simulation.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D71_ROUTE_DRY_RUN_SIMULATION_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D71 route dry-run simulation"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D71 route dry-run simulation changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD71 ROUTE DRY-RUN SIMULATION BOOT DONE")
