#!/usr/bin/env python3
# D79_POLICY_VERIFICATION_GATE_BOOT.py
#
# Adds D79 Policy Verification Gate to GitCube OS.
#
# Run from repo root:
#     python D79_POLICY_VERIFICATION_GATE_BOOT.py
#
# Creates:
# - runtime_experimental/policy_verification_gate.py
# - tests/test_d79_policy_verification_gate.py
# - reports/d79_policy_verification_gate.json
#
# D79 does NOT call an external AI API.
# D79 does NOT patch task_dispatcher.py.
# D79 does NOT mutate protected core.
# D79 does NOT overwrite canonical memory.
# D79 does NOT insert a real route.
# D79 only verifies D78 dry-run diff against D64/D66/D77/D78 guardrails.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_CODE = json.loads("\"from __future__ import annotations\\n\\nimport hashlib\\nimport json\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nD78_REPORT = \\\"reports/d78_narrow_adapter_dry_run_diff.json\\\"\\nD64_REQUEST = \\\"reports/d64_safe_mutation_gate_request.json\\\"\\nD66_REVIEW = \\\"reports/d66_core_guard_reviewer_report.json\\\"\\nOUT = \\\"reports/d79_policy_verification_gate.json\\\"\\n\\n\\ndef now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef safe_path(value: str) -> str:\\n    raw = str(value or \\\"\\\").strip().replace(\\\"\\\\\\\\\\\", \\\"/\\\").lstrip(\\\"/\\\")\\n    return \\\"/\\\".join(x for x in raw.split(\\\"/\\\") if x and x not in (\\\".\\\", \\\"..\\\"))\\n\\n\\ndef sha256_text(text: str) -> str:\\n    return hashlib.sha256(text.encode(\\\"utf-8\\\")).hexdigest()\\n\\n\\ndef sha256_json(data: Dict[str, Any]) -> str:\\n    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode(\\\"utf-8\\\")).hexdigest()\\n\\n\\ndef _validate_d78(root: Path, d78: Dict[str, Any], errors: List[str], warnings: List[str]) -> Dict[str, Any]:\\n    if not d78:\\n        errors.append(\\\"D78 dry-run diff report missing or unreadable\\\")\\n        return {}\\n\\n    if d78.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D78 ok flag is not true\\\")\\n\\n    if d78.get(\\\"decision\\\") != \\\"NARROW_ADAPTER_DRY_RUN_DIFF_READY\\\":\\n        errors.append(f\\\"D78 decision is not NARROW_ADAPTER_DRY_RUN_DIFF_READY: {d78.get('decision')}\\\")\\n\\n    guard = d78.get(\\\"guardrails\\\") if isinstance(d78.get(\\\"guardrails\\\"), dict) else {}\\n    required_false = [\\n        \\\"runtime_code_mutated\\\",\\n        \\\"protected_core_mutated\\\",\\n        \\\"canonical_memory_mutated\\\",\\n        \\\"external_ai_called\\\",\\n        \\\"actual_apply_executed\\\",\\n        \\\"route_inserted\\\",\\n    ]\\n    for key in required_false:\\n        if guard.get(key) is not False:\\n            errors.append(f\\\"D78 guardrail {key} is not false\\\")\\n    if guard.get(\\\"dry_run_only\\\") is not True:\\n        errors.append(\\\"D78 dry_run_only is not true\\\")\\n\\n    pkg = d78.get(\\\"dry_run_diff_package\\\")\\n    if not isinstance(pkg, dict):\\n        errors.append(\\\"D78 dry_run_diff_package missing or invalid\\\")\\n        return {}\\n\\n    if pkg.get(\\\"route_insert_allowed_now\\\") is not False:\\n        errors.append(\\\"D78 route_insert_allowed_now is not false\\\")\\n    if pkg.get(\\\"apply_allowed_now\\\") is not False:\\n        errors.append(\\\"D78 apply_allowed_now is not false\\\")\\n    if pkg.get(\\\"actual_files_touched\\\") not in ([], None):\\n        errors.append(\\\"D78 actual_files_touched is not empty\\\")\\n\\n    child = safe_path(str(pkg.get(\\\"child_module_path\\\", \\\"\\\")))\\n    if not child:\\n        errors.append(\\\"D78 child_module_path missing\\\")\\n    elif not child.startswith(\\\"runtime_experimental/differentiated_modules/\\\"):\\n        errors.append(f\\\"D78 child module outside differentiated_modules: {child}\\\")\\n    elif not (root / child).exists():\\n        errors.append(f\\\"D78 child module does not exist on disk: {child}\\\")\\n\\n    source = safe_path(str(pkg.get(\\\"source_node\\\", \\\"\\\")))\\n    if not source:\\n        errors.append(\\\"D78 source_node missing\\\")\\n\\n    diff_path = str(pkg.get(\\\"diff_output_path\\\", \\\"\\\"))\\n    diff_abs = Path(diff_path)\\n    if not diff_abs.is_absolute():\\n        diff_abs = root / safe_path(diff_path)\\n\\n    diff_text = \\\"\\\"\\n    if not diff_abs.exists():\\n        errors.append(f\\\"D78 diff file missing: {diff_abs}\\\")\\n    else:\\n        diff_text = diff_abs.read_text(encoding=\\\"utf-8\\\")\\n        if \\\"DRY-RUN ONLY\\\" not in diff_text:\\n            errors.append(\\\"D78 diff does not contain DRY-RUN ONLY marker\\\")\\n        if \\\"DO NOT APPLY AUTOMATICALLY\\\" not in diff_text:\\n            errors.append(\\\"D78 diff does not contain DO NOT APPLY AUTOMATICALLY marker\\\")\\n        for gate in (\\\"D66_RECHECK\\\", \\\"D76_CHILD_PROBE_PASSED\\\", \\\"ROLLBACK_MANIFEST\\\", \\\"HUMAN_OR_HIGHER_POLICY_APPROVAL\\\"):\\n            if gate not in diff_text:\\n                errors.append(f\\\"D78 diff missing required marker: {gate}\\\")\\n\\n        expected_hash = str(pkg.get(\\\"diff_sha256\\\", \\\"\\\"))\\n        actual_hash = sha256_text(diff_text)\\n        if expected_hash and expected_hash != actual_hash:\\n            errors.append(\\\"D78 diff sha256 mismatch\\\")\\n\\n    pkg[\\\"_verified_diff_text_len\\\"] = len(diff_text)\\n    return pkg\\n\\n\\ndef _validate_d64(d64: Dict[str, Any], errors: List[str], warnings: List[str]) -> Dict[str, Any]:\\n    if not d64:\\n        warnings.append(\\\"D64 safe mutation gate request missing; D79 continues in dry-run-only verification mode\\\")\\n        return {\\\"available\\\": False}\\n\\n    if d64.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D64 ok flag is not true\\\")\\n\\n    guard = d64.get(\\\"guardrails\\\") if isinstance(d64.get(\\\"guardrails\\\"), dict) else {}\\n    for key in (\\\"actual_apply_executed\\\", \\\"runtime_code_mutated\\\", \\\"protected_core_mutated\\\", \\\"canonical_memory_mutated\\\", \\\"external_ai_called\\\"):\\n        if key in guard and guard.get(key) is not False:\\n            errors.append(f\\\"D64 guardrail {key} is not false\\\")\\n\\n    return {\\n        \\\"available\\\": True,\\n        \\\"ok\\\": d64.get(\\\"ok\\\"),\\n        \\\"decision\\\": d64.get(\\\"decision\\\"),\\n        \\\"result\\\": d64.get(\\\"result\\\"),\\n    }\\n\\n\\ndef _validate_d66(d66: Dict[str, Any], errors: List[str], warnings: List[str]) -> Dict[str, Any]:\\n    if not d66:\\n        warnings.append(\\\"D66 core guard reviewer report missing; D79 continues but real apply must remain blocked\\\")\\n        return {\\\"available\\\": False}\\n\\n    guard = d66.get(\\\"guardrails\\\") if isinstance(d66.get(\\\"guardrails\\\"), dict) else {}\\n    for key in (\\\"actual_apply_executed\\\", \\\"runtime_code_mutated\\\", \\\"protected_core_mutated\\\", \\\"canonical_memory_mutated\\\", \\\"external_ai_called\\\"):\\n        if key in guard and guard.get(key) is not False:\\n            errors.append(f\\\"D66 guardrail {key} is not false\\\")\\n\\n    # D66 may intentionally reject protected-core edits. That is not a failure for D79.\\n    # D79 only verifies the dry-run package and keeps real apply blocked.\\n    return {\\n        \\\"available\\\": True,\\n        \\\"ok\\\": d66.get(\\\"ok\\\"),\\n        \\\"decision\\\": d66.get(\\\"decision\\\"),\\n        \\\"result\\\": d66.get(\\\"result\\\"),\\n        \\\"reason\\\": d66.get(\\\"reason\\\"),\\n    }\\n\\n\\ndef verify_policy_gate(\\n    root: str | Path = \\\".\\\",\\n    d78_report_path: str = D78_REPORT,\\n    d64_request_path: str = D64_REQUEST,\\n    d66_review_path: str = D66_REVIEW,\\n    output_path: str = OUT,\\n) -> Dict[str, Any]:\\n    root = Path(root).resolve()\\n    d78 = read_json(root / d78_report_path, {}) or {}\\n    d64 = read_json(root / d64_request_path, {}) or {}\\n    d66 = read_json(root / d66_review_path, {}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    pkg = _validate_d78(root, d78, errors, warnings)\\n    d64_evidence = _validate_d64(d64, errors, warnings)\\n    d66_evidence = _validate_d66(d66, errors, warnings)\\n\\n    source = safe_path(str(pkg.get(\\\"source_node\\\", \\\"\\\"))) if pkg else \\\"\\\"\\n    child = safe_path(str(pkg.get(\\\"child_module_path\\\", \\\"\\\"))) if pkg else \\\"\\\"\\n    adapter = str(pkg.get(\\\"adapter_name\\\", \\\"\\\")) if pkg else \\\"\\\"\\n    contract_id = str(pkg.get(\\\"contract_id\\\", \\\"\\\")) if pkg else \\\"\\\"\\n\\n    ok = not errors\\n    decision = \\\"POLICY_VERIFIED_DRY_RUN_READY\\\" if ok else \\\"POLICY_VERIFICATION_BLOCKED\\\"\\n    result = \\\"D79_POLICY_VERIFICATION_PASSED\\\" if ok else \\\"D79_POLICY_VERIFICATION_BLOCKED\\\"\\n    gate_id = \\\"d79-\\\" + sha256_json(\\n        {\\n            \\\"source\\\": source,\\n            \\\"child\\\": child,\\n            \\\"adapter\\\": adapter,\\n            \\\"contract_id\\\": contract_id,\\n            \\\"d78_decision\\\": d78.get(\\\"decision\\\"),\\n        }\\n    )[:16]\\n\\n    report = {\\n        \\\"state\\\": \\\"D79_POLICY_VERIFICATION_GATE\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_POLICY_VERIFICATION_GATE\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": now(),\\n        \\\"gate_id\\\": gate_id,\\n        \\\"policy_verdict\\\": {\\n            \\\"verdict\\\": \\\"DRY_RUN_POLICY_APPROVED\\\" if ok else \\\"DRY_RUN_POLICY_REJECTED\\\",\\n            \\\"scope\\\": \\\"dry_run_diff_only\\\",\\n            \\\"real_route_insert_allowed\\\": False,\\n            \\\"real_apply_allowed\\\": False,\\n            \\\"ai_provider_allowed\\\": False,\\n            \\\"ai_mode_allowed_next\\\": \\\"PROPOSE_ONLY_AFTER_D80_BOUNDARY\\\" if ok else \\\"BLOCKED\\\",\\n        },\\n        \\\"input_reports\\\": {\\n            \\\"d78_report_path\\\": str(root / d78_report_path),\\n            \\\"d64_request_path\\\": str(root / d64_request_path),\\n            \\\"d66_review_path\\\": str(root / d66_review_path),\\n        },\\n        \\\"evidence\\\": {\\n            \\\"d78_ok\\\": d78.get(\\\"ok\\\"),\\n            \\\"d78_decision\\\": d78.get(\\\"decision\\\"),\\n            \\\"d64\\\": d64_evidence,\\n            \\\"d66\\\": d66_evidence,\\n            \\\"source_node\\\": source,\\n            \\\"child_module_path\\\": child,\\n            \\\"adapter_name\\\": adapter,\\n            \\\"contract_id\\\": contract_id,\\n            \\\"diff_sha256\\\": pkg.get(\\\"diff_sha256\\\") if pkg else \\\"\\\",\\n        },\\n        \\\"policy_checks\\\": {\\n            \\\"d78_dry_run_only\\\": bool(d78.get(\\\"guardrails\\\", {}).get(\\\"dry_run_only\\\") is True),\\n            \\\"no_runtime_mutation\\\": bool(d78.get(\\\"guardrails\\\", {}).get(\\\"runtime_code_mutated\\\") is False),\\n            \\\"no_protected_core_mutation\\\": bool(d78.get(\\\"guardrails\\\", {}).get(\\\"protected_core_mutated\\\") is False),\\n            \\\"no_canonical_memory_mutation\\\": bool(d78.get(\\\"guardrails\\\", {}).get(\\\"canonical_memory_mutated\\\") is False),\\n            \\\"no_external_ai_call\\\": bool(d78.get(\\\"guardrails\\\", {}).get(\\\"external_ai_called\\\") is False),\\n            \\\"no_actual_apply\\\": bool(d78.get(\\\"guardrails\\\", {}).get(\\\"actual_apply_executed\\\") is False),\\n            \\\"no_route_insert\\\": bool(d78.get(\\\"guardrails\\\", {}).get(\\\"route_inserted\\\") is False),\\n            \\\"child_module_sandboxed\\\": child.startswith(\\\"runtime_experimental/differentiated_modules/\\\") if child else False,\\n            \\\"diff_file_verified\\\": bool(pkg.get(\\\"_verified_diff_text_len\\\", 0) > 0) if pkg else False,\\n        },\\n        \\\"guardrails\\\": {\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"external_ai_called\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"policy_gate_only\\\": True,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"gate_id\\\": gate_id,\\n            \\\"source_node\\\": source,\\n            \\\"child_module_path\\\": child,\\n            \\\"adapter_name\\\": adapter,\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"policy_verified\\\": ok,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D80 can create AI Provider Boundary in PROPOSE_ONLY mode; real apply remains blocked.\\\",\\n        },\\n    }\\n\\n    write_json(root / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(verify_policy_gate(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.policy_verification_gate import verify_policy_gate, sha256_text\\n\\n\\nclass TestD79PolicyVerificationGate(unittest.TestCase):\\n    def make_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n        (root / \\\"runtime_experimental/differentiated_modules\\\").mkdir(parents=True)\\n        (root / \\\"app/orchestration\\\").mkdir(parents=True)\\n\\n        source = \\\"app/orchestration/task_dispatcher.py\\\"\\n        child = \\\"runtime_experimental/differentiated_modules/01_route_policy_child.py\\\"\\n        diff_path = \\\"reports/d78_narrow_adapter_dry_run.diff\\\"\\n        adapter = \\\"D77_NARROW_ADAPTER_ROUTE_POLICY_CHILD\\\"\\n\\n        (root / source).write_text(\\\"# source stays unchanged\\\\n\\\", encoding=\\\"utf-8\\\")\\n        (root / child).write_text(\\\"def run_sandbox_probe(event=None): return {'ok': True}\\\\n\\\", encoding=\\\"utf-8\\\")\\n\\n        diff = \\\"\\\"\\\"diff --git a/app/orchestration/task_dispatcher.py b/app/orchestration/task_dispatcher.py\\n@@ DRY-RUN ONLY: narrow adapter route proposal, not applied @@\\n+# D78 DRY-RUN ONLY \\u2014 DO NOT APPLY AUTOMATICALLY\\n+# D66_RECHECK\\n+# D76_CHILD_PROBE_PASSED\\n+# ROLLBACK_MANIFEST\\n+# HUMAN_OR_HIGHER_POLICY_APPROVAL\\n\\\"\\\"\\\"\\n        (root / diff_path).write_text(diff, encoding=\\\"utf-8\\\")\\n\\n        (root / \\\"reports/d78_narrow_adapter_dry_run_diff.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"NARROW_ADAPTER_DRY_RUN_DIFF_READY\\\",\\n                    \\\"guardrails\\\": {\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"dry_run_only\\\": True,\\n                    },\\n                    \\\"dry_run_diff_package\\\": {\\n                        \\\"source_node\\\": source,\\n                        \\\"child_module_path\\\": child,\\n                        \\\"adapter_name\\\": adapter,\\n                        \\\"contract_id\\\": \\\"d77-test\\\",\\n                        \\\"diff_output_path\\\": diff_path,\\n                        \\\"diff_sha256\\\": sha256_text(diff),\\n                        \\\"route_insert_allowed_now\\\": False,\\n                        \\\"apply_allowed_now\\\": False,\\n                        \\\"actual_files_touched\\\": [],\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d64_safe_mutation_gate_request.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"CREATE_GUARDED_APPLY_REQUEST\\\",\\n                    \\\"guardrails\\\": {\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"external_ai_called\\\": False,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d66_core_guard_reviewer_report.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": False,\\n                    \\\"decision\\\": \\\"FORBIDDEN_CORE_MUTATION\\\",\\n                    \\\"reason\\\": \\\"protected_core_touched_without_two_eyes\\\",\\n                    \\\"guardrails\\\": {\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"external_ai_called\\\": False,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        return td, root, source\\n\\n    def test_policy_verifies_dry_run_without_mutation(self):\\n        td, root, source = self.make_root()\\n        try:\\n            before = (root / source).read_text(encoding=\\\"utf-8\\\")\\n            report = verify_policy_gate(root=root)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"POLICY_VERIFIED_DRY_RUN_READY\\\")\\n            self.assertEqual(report[\\\"policy_verdict\\\"][\\\"verdict\\\"], \\\"DRY_RUN_POLICY_APPROVED\\\")\\n            self.assertFalse(report[\\\"policy_verdict\\\"][\\\"real_apply_allowed\\\"])\\n            self.assertFalse(report[\\\"policy_verdict\\\"][\\\"real_route_insert_allowed\\\"])\\n            self.assertEqual((root / source).read_text(encoding=\\\"utf-8\\\"), before)\\n            self.assertTrue((root / \\\"reports/d79_policy_verification_gate.json\\\").exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d78(self):\\n        td, root, _ = self.make_root()\\n        try:\\n            (root / \\\"reports/d78_narrow_adapter_dry_run_diff.json\\\").unlink()\\n            report = verify_policy_gate(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"POLICY_VERIFICATION_BLOCKED\\\")\\n            self.assertGreaterEqual(report[\\\"summary\\\"][\\\"errors_count\\\"], 1)\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_when_diff_hash_mismatch(self):\\n        td, root, _ = self.make_root()\\n        try:\\n            p = root / \\\"reports/d78_narrow_adapter_dry_run.diff\\\"\\n            p.write_text(p.read_text(encoding=\\\"utf-8\\\") + \\\"\\\\n# tampered\\\\n\\\", encoding=\\\"utf-8\\\")\\n\\n            report = verify_policy_gate(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"POLICY_VERIFICATION_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


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

print("D79 POLICY VERIFICATION GATE BOOT: repo =", ROOT)

Path("runtime_experimental/policy_verification_gate.py").write_text(MODULE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/policy_verification_gate.py")

Path("tests/test_d79_policy_verification_gate.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d79_policy_verification_gate.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/policy_verification_gate.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d79_policy_verification_gate", "-v"], check=True)

print("\n== run D79 policy verification gate ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.policy_verification_gate import verify_policy_gate\n"
        "r=verify_policy_gate()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d79_policy_verification_gate.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))
    print("VERDICT:", data.get("policy_verdict"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/policy_verification_gate.py",
    "tests/test_d79_policy_verification_gate.py",
    "reports/d79_policy_verification_gate.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D79_POLICY_VERIFICATION_GATE_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D79 policy verification gate"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D79 policy verification gate changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD79 POLICY VERIFICATION GATE BOOT DONE")
