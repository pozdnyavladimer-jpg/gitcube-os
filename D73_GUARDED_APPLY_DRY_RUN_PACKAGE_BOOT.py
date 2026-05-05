#!/usr/bin/env python3
# D73_GUARDED_APPLY_DRY_RUN_PACKAGE_BOOT.py
#
# Adds D73 Guarded Apply Dry-Run Package to GitCube OS.
#
# Run from repo root:
#     python D73_GUARDED_APPLY_DRY_RUN_PACKAGE_BOOT.py
#
# Creates:
# - runtime_experimental/guarded_apply_dry_run_package.py
# - tests/test_d73_guarded_apply_dry_run_package.py
# - reports/d73_guarded_apply_dry_run_package.json
#
# D73 does NOT call an external AI API.
# D73 does NOT patch task_dispatcher.py.
# D73 does NOT mutate protected core.
# D73 does NOT overwrite canonical memory.
# D73 does NOT apply sandbox files to runtime.
#
# D73 packages D72 into pre-apply dry-run evidence with rollback manifest.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PACKAGE_CODE = 'from __future__ import annotations\n\nimport hashlib\nimport json\nimport subprocess\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nfrom typing import Any, Dict, List\n\n\nDEFAULT_D72_PLAN = "reports/d72_reviewed_apply_plan.json"\nDEFAULT_D71_DRY_RUN = "reports/d71_route_dry_run_simulation.json"\nDEFAULT_D64_REQUEST = "reports/d64_safe_mutation_gate_request.json"\nDEFAULT_D66_REVIEW = "reports/d66_core_guard_reviewer_report.json"\nDEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"\nDEFAULT_OUTPUT = "reports/d73_guarded_apply_dry_run_package.json"\n\n\ndef _now() -> str:\n    return datetime.now(timezone.utc).isoformat()\n\n\ndef _read_json(path: str | Path, default: Any = None) -> Any:\n    p = Path(path)\n    if not p.exists():\n        return default\n    try:\n        return json.loads(p.read_text(encoding="utf-8"))\n    except Exception:\n        return default\n\n\ndef _write_json(path: str | Path, data: Dict[str, Any]) -> None:\n    p = Path(path)\n    p.parent.mkdir(parents=True, exist_ok=True)\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")\n\n\ndef _safe_relative_path(path_value: str) -> str:\n    raw = str(path_value or "").strip().replace("\\\\", "/").lstrip("/")\n    parts: List[str] = []\n    for part in raw.split("/"):\n        if not part or part == "." or part == "..":\n            continue\n        parts.append(part)\n    return "/".join(parts)\n\n\ndef _sha256_file(path: Path) -> str:\n    if not path.exists() or not path.is_file():\n        return ""\n    return hashlib.sha256(path.read_bytes()).hexdigest()\n\n\ndef _git_sha(root: Path) -> str:\n    try:\n        proc = subprocess.run(\n            ["git", "rev-parse", "HEAD"],\n            cwd=root,\n            text=True,\n            capture_output=True,\n            check=False,\n        )\n        if proc.returncode == 0:\n            return proc.stdout.strip()\n    except Exception:\n        pass\n    return "UNKNOWN"\n\n\ndef _git_status_porcelain(root: Path) -> str:\n    try:\n        proc = subprocess.run(\n            ["git", "status", "--porcelain"],\n            cwd=root,\n            text=True,\n            capture_output=True,\n            check=False,\n        )\n        if proc.returncode == 0:\n            return proc.stdout.strip()\n    except Exception:\n        pass\n    return "UNKNOWN"\n\n\ndef _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:\n    for key in ("protected_files", "immutable_core", "core_files"):\n        value = policy.get(key)\n        if isinstance(value, list):\n            return [str(v) for v in value]\n    return []\n\n\ndef _backup_manifest(root: Path, protected_files: List[str]) -> List[Dict[str, Any]]:\n    manifest: List[Dict[str, Any]] = []\n    for raw in protected_files:\n        rel = _safe_relative_path(raw)\n        path = root / rel\n        manifest.append(\n            {\n                "path": rel,\n                "exists": path.exists(),\n                "is_file": path.is_file(),\n                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,\n                "sha256": _sha256_file(path),\n                "backup_required_before_apply": True,\n                "restore_policy": "git restore -- " + rel,\n            }\n        )\n    return manifest\n\n\ndef _validate_d72(d72: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:\n    plan = d72.get("reviewed_apply_plan") if isinstance(d72.get("reviewed_apply_plan"), dict) else {}\n\n    if not d72:\n        errors.append("D72 reviewed apply plan missing or unreadable")\n        return {}\n\n    if d72.get("ok") is not True:\n        errors.append("D72 ok flag is not true")\n\n    if d72.get("decision") != "REVIEWED_APPLY_PLAN_READY":\n        errors.append(f"D72 decision is not REVIEWED_APPLY_PLAN_READY: {d72.get(\'decision\')}")\n\n    guardrails = d72.get("guardrails") if isinstance(d72.get("guardrails"), dict) else {}\n    if guardrails.get("actual_apply_executed") is not False:\n        errors.append("D72 actual_apply_executed is not false")\n    if guardrails.get("plan_only") is not True:\n        errors.append("D72 plan_only is not true")\n\n    if plan.get("enabled") is not True:\n        errors.append("D72 reviewed apply plan is not enabled")\n\n    rollback = plan.get("rollback_plan") if isinstance(plan.get("rollback_plan"), dict) else {}\n    if rollback.get("required") is not True:\n        errors.append("D72 rollback plan is not required=true")\n\n    return plan\n\n\ndef build_guarded_apply_dry_run_package(\n    root: str | Path = ".",\n    d72_plan_path: str = DEFAULT_D72_PLAN,\n    d71_dry_run_path: str = DEFAULT_D71_DRY_RUN,\n    d64_request_path: str = DEFAULT_D64_REQUEST,\n    d66_review_path: str = DEFAULT_D66_REVIEW,\n    core_policy_path: str = DEFAULT_CORE_POLICY,\n    output_path: str = DEFAULT_OUTPUT,\n) -> Dict[str, Any]:\n    root_path = Path(root).resolve()\n\n    d72 = _read_json(root_path / d72_plan_path, default={}) or {}\n    d71 = _read_json(root_path / d71_dry_run_path, default={}) or {}\n    d64 = _read_json(root_path / d64_request_path, default={}) or {}\n    d66 = _read_json(root_path / d66_review_path, default={}) or {}\n    policy = _read_json(root_path / core_policy_path, default={}) or {}\n\n    errors: List[str] = []\n    warnings: List[str] = []\n\n    plan = _validate_d72(d72, errors)\n\n    if not d71:\n        warnings.append("D71 dry-run report missing or unreadable")\n    elif d71.get("decision") != "ROUTE_DRY_RUN_APPROVED":\n        errors.append(f"D71 decision is not ROUTE_DRY_RUN_APPROVED: {d71.get(\'decision\')}")\n\n    if not d64:\n        warnings.append("D64 gate request missing or unreadable")\n    elif d64.get("decision") != "CREATE_GUARDED_APPLY_REQUEST":\n        errors.append(f"D64 decision is not CREATE_GUARDED_APPLY_REQUEST: {d64.get(\'decision\')}")\n\n    if not d66:\n        warnings.append("D66 reviewer report missing or unreadable; D73 will still require recheck before apply")\n\n    if not policy:\n        warnings.append("core guard policy missing or unreadable")\n\n    protected_files = _protected_files_from_policy(policy)\n    if not protected_files:\n        rollback = plan.get("rollback_plan") if isinstance(plan.get("rollback_plan"), dict) else {}\n        backup_targets = rollback.get("backup_targets")\n        if isinstance(backup_targets, list):\n            protected_files = [str(x) for x in backup_targets if x]\n\n    sandbox_candidates_raw = plan.get("sandbox_candidates", [])\n    sandbox_candidates = [_safe_relative_path(str(x)) for x in sandbox_candidates_raw if x] if isinstance(sandbox_candidates_raw, list) else []\n\n    route_diff = plan.get("simulated_route_diff", [])\n    if not isinstance(route_diff, list):\n        route_diff = []\n        errors.append("D72 simulated_route_diff is not a list")\n\n    if not sandbox_candidates:\n        errors.append("D73 has no sandbox candidates from D72")\n\n    if not route_diff:\n        errors.append("D73 has no route diff from D72")\n\n    backup_manifest = _backup_manifest(root_path, protected_files)\n    pre_apply_sha = _git_sha(root_path)\n    status_before = _git_status_porcelain(root_path)\n\n    package_ready = len(errors) == 0\n    decision = "GUARDED_APPLY_DRY_RUN_PACKAGE_READY" if package_ready else "GUARDED_APPLY_DRY_RUN_PACKAGE_BLOCKED"\n    result = "D73_GUARDED_APPLY_DRY_RUN_PACKAGE_CREATED" if package_ready else "D73_GUARDED_APPLY_DRY_RUN_PACKAGE_BLOCKED"\n\n    dry_run_package = {\n        "package_state": "D73_GUARDED_APPLY_DRY_RUN_PACKAGE",\n        "enabled": package_ready,\n        "mode": "DRY_RUN_PACKAGE_ONLY",\n        "pre_apply_git_sha": pre_apply_sha,\n        "git_status_before_package": status_before,\n        "source_plan_id": d72.get("plan_id"),\n        "sandbox_candidates": sandbox_candidates,\n        "simulated_route_diff": route_diff,\n        "backup_manifest": backup_manifest,\n        "rollback_instructions": {\n            "rollback_required": True,\n            "restore_protected_files": ["git restore -- " + item["path"] for item in backup_manifest],\n            "revert_commit_policy": "only_after_human_or_higher_policy_review",\n            "must_preserve_reports": True,\n        },\n        "required_validation_commands": [\n            "python -m py_compile runtime_experimental/reviewed_apply_plan.py",\n            "python -m py_compile runtime_experimental/route_dry_run_simulator.py",\n            "python -m unittest tests.test_d64_safe_mutation_gate -v",\n            "python -m unittest tests.test_d70_sandbox_bundle_reviewer -v",\n            "python -m unittest tests.test_d71_route_dry_run_simulator -v",\n            "python -m unittest tests.test_d72_reviewed_apply_plan -v",\n            "python -m unittest tests.test_d73_guarded_apply_dry_run_package -v",\n        ],\n        "required_gates_before_real_apply": [\n            "D66_REVIEWER_RECHECK",\n            "D71_ROUTE_DRY_RUN_APPROVED",\n            "D72_REVIEWED_APPLY_PLAN_READY",\n            "ROLLBACK_MANIFEST_READY",\n            "FULL_TEST_SUITE_OK",\n            "HUMAN_OR_HIGHER_POLICY_APPROVAL",\n        ],\n        "forbidden_actions": [\n            "direct_core_edit",\n            "overwrite_canonical_memory",\n            "auto_commit_runtime_mutation",\n            "apply_without_backup_manifest",\n            "apply_without_D66_recheck",\n            "apply_without_explicit_approval",\n        ],\n    }\n\n    report = {\n        "state": "D73_GUARDED_APPLY_DRY_RUN_PACKAGE",\n        "result": result,\n        "route": "FIELD_INTENT_GUARDED_APPLY_DRY_RUN_PACKAGE",\n        "ok": package_ready,\n        "decision": decision,\n        "created_at": _now(),\n        "dry_run_package": dry_run_package,\n        "input_reports": {\n            "d72_plan_path": str(root_path / d72_plan_path),\n            "d71_dry_run_path": str(root_path / d71_dry_run_path),\n            "d64_request_path": str(root_path / d64_request_path),\n            "d66_review_path": str(root_path / d66_review_path),\n            "core_policy_path": str(root_path / core_policy_path),\n        },\n        "evidence": {\n            "d72_decision": d72.get("decision"),\n            "d72_ok": d72.get("ok"),\n            "d71_decision": d71.get("decision"),\n            "d64_decision": d64.get("decision"),\n            "d66_decision": d66.get("decision"),\n            "pre_apply_git_sha": pre_apply_sha,\n            "backup_manifest_count": len(backup_manifest),\n            "sandbox_candidates_count": len(sandbox_candidates),\n            "route_diff_count": len(route_diff),\n        },\n        "guardrails": {\n            "runtime_code_mutated": False,\n            "protected_core_mutated": False,\n            "canonical_memory_mutated": False,\n            "external_ai_called": False,\n            "actual_apply_executed": False,\n            "package_only": True,\n        },\n        "validation": {\n            "ok": package_ready,\n            "errors": errors,\n            "warnings": warnings,\n        },\n        "summary": {\n            "decision": decision,\n            "sandbox_candidates_count": len(sandbox_candidates),\n            "route_diff_count": len(route_diff),\n            "backup_manifest_count": len(backup_manifest),\n            "errors_count": len(errors),\n            "warnings_count": len(warnings),\n        },\n        "success_condition": {\n            "dry_run_package_created": package_ready,\n            "actual_apply_executed": False,\n            "backup_manifest_ready": len(backup_manifest) > 0,\n            "next_step": "D74 should analyze differentiation / module extraction pressure. Real apply remains blocked until D66 recheck and explicit approval.",\n        },\n    }\n\n    _write_json(root_path / output_path, report)\n    return report\n\n\nif __name__ == "__main__":\n    print(json.dumps(build_guarded_apply_dry_run_package(), ensure_ascii=False, indent=2))\n'
TEST_CODE = 'import json\nimport tempfile\nimport unittest\nfrom pathlib import Path\n\nfrom runtime_experimental.guarded_apply_dry_run_package import build_guarded_apply_dry_run_package\n\n\nclass TestD73GuardedApplyDryRunPackage(unittest.TestCase):\n    def make_valid_root(self):\n        td = tempfile.TemporaryDirectory()\n        root = Path(td.name)\n        (root / "reports").mkdir(parents=True)\n        (root / "runtime_experimental/ai_bypass_proposals").mkdir(parents=True)\n        (root / "app/orchestration").mkdir(parents=True)\n\n        protected = "app/orchestration/task_dispatcher.py"\n        candidate = "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"\n\n        (root / protected).write_text("# protected dispatcher\\n", encoding="utf-8")\n        (root / candidate).write_text("def run_sandbox_probe(event=None):\\n    return {\'ok\': True}\\n", encoding="utf-8")\n\n        route_diff = [\n            {\n                "operation": "SIMULATE_ROUTE_INSERT",\n                "route_name": "DRY_RUN_DISPATCHER_BYPASS_PROPOSAL",\n                "sandbox_handler": candidate,\n                "would_touch_files": [],\n                "would_touch_protected_core": False,\n                "would_touch_canonical_memory": False,\n                "would_execute_runtime_mutation": False,\n                "dry_run_only": True,\n            }\n        ]\n\n        (root / "runtime_experimental/core_guard_policy.json").write_text(\n            json.dumps({"protected_files": [protected]}),\n            encoding="utf-8",\n        )\n        (root / "reports/d72_reviewed_apply_plan.json").write_text(\n            json.dumps(\n                {\n                    "ok": True,\n                    "decision": "REVIEWED_APPLY_PLAN_READY",\n                    "plan_id": "d72-test-plan",\n                    "guardrails": {"actual_apply_executed": False, "plan_only": True},\n                    "reviewed_apply_plan": {\n                        "enabled": True,\n                        "sandbox_candidates": [candidate],\n                        "simulated_route_diff": route_diff,\n                        "rollback_plan": {"required": True, "backup_targets": [protected]},\n                    },\n                }\n            ),\n            encoding="utf-8",\n        )\n        (root / "reports/d71_route_dry_run_simulation.json").write_text(\n            json.dumps({"ok": True, "decision": "ROUTE_DRY_RUN_APPROVED"}),\n            encoding="utf-8",\n        )\n        (root / "reports/d64_safe_mutation_gate_request.json").write_text(\n            json.dumps({"ok": True, "decision": "CREATE_GUARDED_APPLY_REQUEST"}),\n            encoding="utf-8",\n        )\n        return td, root, candidate, protected\n\n    def test_creates_guarded_apply_dry_run_package(self):\n        td, root, candidate, protected = self.make_valid_root()\n        try:\n            report = build_guarded_apply_dry_run_package(root=root)\n\n            self.assertTrue(report["ok"])\n            self.assertEqual(report["decision"], "GUARDED_APPLY_DRY_RUN_PACKAGE_READY")\n            self.assertFalse(report["guardrails"]["actual_apply_executed"])\n            self.assertTrue(report["guardrails"]["package_only"])\n            self.assertIn(candidate, report["dry_run_package"]["sandbox_candidates"])\n            self.assertEqual(report["dry_run_package"]["backup_manifest"][0]["path"], protected)\n            self.assertTrue((root / "reports/d73_guarded_apply_dry_run_package.json").exists())\n        finally:\n            td.cleanup()\n\n    def test_blocks_when_d72_blocked(self):\n        td, root, _, _ = self.make_valid_root()\n        try:\n            d72_path = root / "reports/d72_reviewed_apply_plan.json"\n            data = json.loads(d72_path.read_text(encoding="utf-8"))\n            data["ok"] = False\n            data["decision"] = "REVIEWED_APPLY_PLAN_BLOCKED"\n            d72_path.write_text(json.dumps(data), encoding="utf-8")\n\n            report = build_guarded_apply_dry_run_package(root=root)\n\n            self.assertFalse(report["ok"])\n            self.assertEqual(report["decision"], "GUARDED_APPLY_DRY_RUN_PACKAGE_BLOCKED")\n            self.assertFalse(report["dry_run_package"]["enabled"])\n        finally:\n            td.cleanup()\n\n    def test_blocks_without_route_diff(self):\n        td, root, _, _ = self.make_valid_root()\n        try:\n            d72_path = root / "reports/d72_reviewed_apply_plan.json"\n            data = json.loads(d72_path.read_text(encoding="utf-8"))\n            data["reviewed_apply_plan"]["simulated_route_diff"] = []\n            d72_path.write_text(json.dumps(data), encoding="utf-8")\n\n            report = build_guarded_apply_dry_run_package(root=root)\n\n            self.assertFalse(report["ok"])\n            self.assertEqual(report["decision"], "GUARDED_APPLY_DRY_RUN_PACKAGE_BLOCKED")\n            self.assertGreaterEqual(report["summary"]["errors_count"], 1)\n        finally:\n            td.cleanup()\n\n\nif __name__ == "__main__":\n    unittest.main()\n'


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

print("D73 GUARDED APPLY DRY-RUN PACKAGE BOOT: repo =", ROOT)

Path("runtime_experimental/guarded_apply_dry_run_package.py").write_text(PACKAGE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/guarded_apply_dry_run_package.py")

Path("tests/test_d73_guarded_apply_dry_run_package.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d73_guarded_apply_dry_run_package.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/guarded_apply_dry_run_package.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d73_guarded_apply_dry_run_package", "-v"], check=True)

print("\n== run D73 guarded apply dry-run package ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.guarded_apply_dry_run_package import build_guarded_apply_dry_run_package\n"
        "r=build_guarded_apply_dry_run_package()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d73_guarded_apply_dry_run_package.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/guarded_apply_dry_run_package.py",
    "tests/test_d73_guarded_apply_dry_run_package.py",
    "reports/d73_guarded_apply_dry_run_package.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D73_GUARDED_APPLY_DRY_RUN_PACKAGE_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D73 guarded apply dry-run package"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D73 guarded apply dry-run package changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD73 GUARDED APPLY DRY-RUN PACKAGE BOOT DONE")
