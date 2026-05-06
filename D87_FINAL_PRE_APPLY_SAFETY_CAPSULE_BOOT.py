#!/usr/bin/env python3
# D87_FINAL_PRE_APPLY_SAFETY_CAPSULE_BOOT.py
#
# Adds D87 Final Pre-Apply Safety Capsule to GitCube OS.
#
# Run from repo root:
#     python D87_FINAL_PRE_APPLY_SAFETY_CAPSULE_BOOT.py
#
# Creates:
# - runtime_experimental/final_pre_apply_safety_capsule.py
# - tests/test_d87_final_pre_apply_safety_capsule.py
# - reports/d87_final_pre_apply_safety_capsule.json
# - reports/d87_pre_apply_safety_capsule.json
# - reports/d87_apply_blockers.json
#
# D87 does NOT call an external AI API.
# D87 does NOT use network access.
# D87 does NOT execute raw code from AI.
# D87 does NOT run shell commands from AI.
# D87 does NOT patch task_dispatcher.py.
# D87 does NOT mutate protected core.
# D87 does NOT overwrite canonical memory.
# D87 does NOT insert a real route.
# D87 does NOT apply changes.
#
# D87 only assembles the final pre-apply safety capsule and hard blockers.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_CODE = json.loads("\"from __future__ import annotations\\n\\nimport hashlib\\nimport json\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nD86_REPORT = \\\"reports/d86_local_regression_runner.json\\\"\\nD86_RESULTS = \\\"reports/d86_local_regression_results.json\\\"\\nD85_REPORT = \\\"reports/d85_regression_rollback_evidence.json\\\"\\nD85_ROLLBACK = \\\"reports/d85_rollback_manifest.json\\\"\\nD85_CHECKLIST = \\\"reports/d85_regression_checklist.json\\\"\\n\\nOUT = \\\"reports/d87_final_pre_apply_safety_capsule.json\\\"\\nCAPSULE_OUT = \\\"reports/d87_pre_apply_safety_capsule.json\\\"\\nBLOCKERS_OUT = \\\"reports/d87_apply_blockers.json\\\"\\n\\n\\nREQUIRED_PRE_APPLY_EVIDENCE = [\\n    \\\"D81_AI_PROPOSAL_INTAKE_READY\\\",\\n    \\\"D82_HUMAN_SIGNED_INTENT_READY\\\",\\n    \\\"D83_SANDBOX_WRITER_HANDOFF_READY\\\",\\n    \\\"D84_SANDBOX_WRITER_OUTPUT_REVIEW_READY\\\",\\n    \\\"D85_REGRESSION_ROLLBACK_EVIDENCE_READY\\\",\\n    \\\"D86_LOCAL_REGRESSION_PASSED\\\",\\n]\\n\\nHARD_BLOCKERS = [\\n    \\\"actual_apply_executed\\\",\\n    \\\"route_inserted\\\",\\n    \\\"protected_core_mutated\\\",\\n    \\\"canonical_memory_mutated\\\",\\n    \\\"external_ai_called\\\",\\n    \\\"network_accessed\\\",\\n    \\\"git_commit_by_ai\\\",\\n]\\n\\n\\ndef now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef sha256_json(data: Dict[str, Any]) -> str:\\n    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode(\\\"utf-8\\\")).hexdigest()\\n\\n\\ndef validate_false_guardrails(name: str, guard: Dict[str, Any], errors: List[str]) -> None:\\n    for key in HARD_BLOCKERS:\\n        if guard.get(key) is not False:\\n            errors.append(f\\\"{name} guardrail {key} is not false\\\")\\n\\n\\ndef validate_d86(d86: Dict[str, Any], results: Dict[str, Any], errors: List[str]) -> None:\\n    if not d86:\\n        errors.append(\\\"D86 report missing or unreadable\\\")\\n        return\\n\\n    if d86.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D86 ok flag is not true\\\")\\n    if d86.get(\\\"decision\\\") != \\\"LOCAL_REGRESSION_PASSED\\\":\\n        errors.append(f\\\"D86 decision invalid: {d86.get('decision')}\\\")\\n\\n    guard = d86.get(\\\"guardrails\\\") if isinstance(d86.get(\\\"guardrails\\\"), dict) else {}\\n    validate_false_guardrails(\\\"D86\\\", guard, errors)\\n\\n    if guard.get(\\\"local_regression_only\\\") is not True:\\n        errors.append(\\\"D86 local_regression_only is not true\\\")\\n    if guard.get(\\\"allowlisted_commands_only\\\") is not True:\\n        errors.append(\\\"D86 allowlisted_commands_only is not true\\\")\\n\\n    summary = d86.get(\\\"summary\\\") if isinstance(d86.get(\\\"summary\\\"), dict) else {}\\n    if int(summary.get(\\\"commands_failed_count\\\") or 0) != 0:\\n        errors.append(\\\"D86 summary reports failed commands\\\")\\n\\n    if not results:\\n        errors.append(\\\"D86 results missing or unreadable\\\")\\n        return\\n\\n    if results.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D86 results ok flag is not true\\\")\\n    if int(results.get(\\\"commands_failed_count\\\") or 0) != 0:\\n        errors.append(\\\"D86 results has failed commands\\\")\\n    if int(results.get(\\\"commands_run_count\\\") or 0) <= 0:\\n        errors.append(\\\"D86 results has no commands run\\\")\\n\\n    for key in (\\n        \\\"actual_apply_executed\\\",\\n        \\\"route_inserted\\\",\\n        \\\"protected_core_touched\\\",\\n        \\\"network_accessed\\\",\\n        \\\"external_ai_called\\\",\\n    ):\\n        if results.get(key) is not False:\\n            errors.append(f\\\"D86 result flag {key} is not false\\\")\\n\\n\\ndef validate_d85(\\n    d85: Dict[str, Any],\\n    rollback: Dict[str, Any],\\n    checklist: Dict[str, Any],\\n    errors: List[str],\\n) -> None:\\n    if not d85:\\n        errors.append(\\\"D85 report missing or unreadable\\\")\\n        return\\n\\n    if d85.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D85 ok flag is not true\\\")\\n    if d85.get(\\\"decision\\\") != \\\"REGRESSION_ROLLBACK_EVIDENCE_READY\\\":\\n        errors.append(f\\\"D85 decision invalid: {d85.get('decision')}\\\")\\n\\n    guard = d85.get(\\\"guardrails\\\") if isinstance(d85.get(\\\"guardrails\\\"), dict) else {}\\n    validate_false_guardrails(\\\"D85\\\", guard, errors)\\n\\n    if guard.get(\\\"rollback_evidence_only\\\") is not True:\\n        errors.append(\\\"D85 rollback_evidence_only is not true\\\")\\n    if guard.get(\\\"regression_evidence_only\\\") is not True:\\n        errors.append(\\\"D85 regression_evidence_only is not true\\\")\\n\\n    if not rollback:\\n        errors.append(\\\"D85 rollback manifest missing or unreadable\\\")\\n    else:\\n        if rollback.get(\\\"human_review_required\\\") is not True:\\n            errors.append(\\\"D85 rollback manifest human_review_required is not true\\\")\\n        for key in (\\n            \\\"actual_rollback_executed\\\",\\n            \\\"actual_apply_executed\\\",\\n            \\\"route_inserted\\\",\\n            \\\"protected_core_touched\\\",\\n        ):\\n            if rollback.get(key) is not False:\\n                errors.append(f\\\"D85 rollback {key} is not false\\\")\\n\\n    if not checklist:\\n        errors.append(\\\"D85 checklist missing or unreadable\\\")\\n    else:\\n        pass_condition = checklist.get(\\\"pass_condition\\\") if isinstance(checklist.get(\\\"pass_condition\\\"), dict) else {}\\n        for key in (\\n            \\\"all_tests_green\\\",\\n            \\\"rollback_manifest_present\\\",\\n            \\\"no_protected_core_mutation\\\",\\n            \\\"no_route_insert\\\",\\n            \\\"no_actual_apply\\\",\\n        ):\\n            if pass_condition.get(key) is not True:\\n                errors.append(f\\\"D85 checklist pass condition {key} is not true\\\")\\n\\n\\ndef create_blockers() -> Dict[str, Any]:\\n    return {\\n        \\\"state\\\": \\\"D87_APPLY_BLOCKERS\\\",\\n        \\\"ok\\\": True,\\n        \\\"created_at\\\": now(),\\n        \\\"apply_allowed_now\\\": False,\\n        \\\"route_insert_allowed_now\\\": False,\\n        \\\"protected_core_mutation_allowed_now\\\": False,\\n        \\\"external_ai_call_allowed_now\\\": False,\\n        \\\"git_action_by_ai_allowed_now\\\": False,\\n        \\\"hard_blockers\\\": [\\n            \\\"no explicit D88 higher policy approval\\\",\\n            \\\"no guarded apply command generated\\\",\\n            \\\"no runtime mutation execution\\\",\\n            \\\"no route insertion permission\\\",\\n            \\\"no protected-core mutation permission\\\",\\n        ],\\n        \\\"required_before_apply_can_be_discussed\\\": [\\n            \\\"D88_HIGHER_POLICY_APPROVAL_REQUEST\\\",\\n            \\\"D89_FINAL_HUMAN_CONFIRMATION\\\",\\n            \\\"D66_RECHECK\\\",\\n            \\\"FULL_TEST_DISCOVERY\\\",\\n            \\\"ROLLBACK_MANIFEST_RECONFIRMATION\\\",\\n        ],\\n    }\\n\\n\\ndef create_final_pre_apply_safety_capsule(\\n    root: str | Path = \\\".\\\",\\n    d86_report_path: str = D86_REPORT,\\n    d86_results_path: str = D86_RESULTS,\\n    d85_report_path: str = D85_REPORT,\\n    d85_rollback_path: str = D85_ROLLBACK,\\n    d85_checklist_path: str = D85_CHECKLIST,\\n    output_path: str = OUT,\\n    capsule_output_path: str = CAPSULE_OUT,\\n    blockers_output_path: str = BLOCKERS_OUT,\\n) -> Dict[str, Any]:\\n    root = Path(root).resolve()\\n\\n    d86 = read_json(root / d86_report_path, {}) or {}\\n    results = read_json(root / d86_results_path, {}) or {}\\n    d85 = read_json(root / d85_report_path, {}) or {}\\n    rollback = read_json(root / d85_rollback_path, {}) or {}\\n    checklist = read_json(root / d85_checklist_path, {}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    validate_d86(d86, results, errors)\\n    validate_d85(d85, rollback, checklist, errors)\\n\\n    package_id = str(d86.get(\\\"package_id\\\") or d85.get(\\\"package_id\\\") or \\\"\\\")\\n    review_id = str(d86.get(\\\"review_id\\\") or (d85.get(\\\"evidence\\\") or {}).get(\\\"review_id\\\") or \\\"\\\")\\n    capsule_id = \\\"d87-\\\" + sha256_json(\\n        {\\n            \\\"package_id\\\": package_id,\\n            \\\"review_id\\\": review_id,\\n            \\\"d86_decision\\\": d86.get(\\\"decision\\\"),\\n            \\\"d85_decision\\\": d85.get(\\\"decision\\\"),\\n        }\\n    )[:16]\\n\\n    ok = not errors\\n    decision = \\\"FINAL_PRE_APPLY_SAFETY_CAPSULE_READY\\\" if ok else \\\"FINAL_PRE_APPLY_SAFETY_CAPSULE_BLOCKED\\\"\\n    result = \\\"D87_FINAL_PRE_APPLY_SAFETY_CAPSULE_CREATED\\\" if ok else \\\"D87_FINAL_PRE_APPLY_SAFETY_CAPSULE_BLOCKED\\\"\\n\\n    blockers = create_blockers()\\n\\n    capsule = {\\n        \\\"state\\\": \\\"D87_PRE_APPLY_SAFETY_CAPSULE\\\",\\n        \\\"ok\\\": ok,\\n        \\\"capsule_id\\\": capsule_id,\\n        \\\"created_at\\\": now(),\\n        \\\"package_id\\\": package_id,\\n        \\\"review_id\\\": review_id,\\n        \\\"evidence_chain\\\": {\\n            \\\"d85_decision\\\": d85.get(\\\"decision\\\"),\\n            \\\"d86_decision\\\": d86.get(\\\"decision\\\"),\\n            \\\"d86_commands_run_count\\\": (results or {}).get(\\\"commands_run_count\\\"),\\n            \\\"d86_commands_failed_count\\\": (results or {}).get(\\\"commands_failed_count\\\"),\\n            \\\"rollback_manifest_present\\\": bool(rollback),\\n            \\\"regression_checklist_present\\\": bool(checklist),\\n        },\\n        \\\"required_pre_apply_evidence\\\": REQUIRED_PRE_APPLY_EVIDENCE,\\n        \\\"approval_state\\\": {\\n            \\\"ready_for_higher_policy_review\\\": ok,\\n            \\\"ready_for_real_apply\\\": False,\\n            \\\"ready_for_route_insert\\\": False,\\n            \\\"ready_for_protected_core_mutation\\\": False,\\n        },\\n        \\\"hard_no_mutation_flags\\\": {\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n        },\\n        \\\"next_gate\\\": \\\"D88_HIGHER_POLICY_APPROVAL_REQUEST\\\",\\n    }\\n\\n    if ok:\\n        write_json(root / capsule_output_path, capsule)\\n        write_json(root / blockers_output_path, blockers)\\n\\n    report = {\\n        \\\"state\\\": \\\"D87_FINAL_PRE_APPLY_SAFETY_CAPSULE\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_FINAL_PRE_APPLY_SAFETY_CAPSULE\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": now(),\\n        \\\"capsule_id\\\": capsule_id,\\n        \\\"capsule_path\\\": str(root / capsule_output_path) if ok else \\\"\\\",\\n        \\\"blockers_path\\\": str(root / blockers_output_path) if ok else \\\"\\\",\\n        \\\"input_reports\\\": {\\n            \\\"d86_report_path\\\": str(root / d86_report_path),\\n            \\\"d86_results_path\\\": str(root / d86_results_path),\\n            \\\"d85_report_path\\\": str(root / d85_report_path),\\n            \\\"d85_rollback_path\\\": str(root / d85_rollback_path),\\n            \\\"d85_checklist_path\\\": str(root / d85_checklist_path),\\n        },\\n        \\\"capsule\\\": capsule if ok else {},\\n        \\\"blockers\\\": blockers,\\n        \\\"guardrails\\\": {\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n            \\\"final_capsule_only\\\": True,\\n            \\\"pre_apply_review_only\\\": True,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"capsule_id\\\": capsule_id,\\n            \\\"package_id\\\": package_id,\\n            \\\"review_id\\\": review_id,\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"final_pre_apply_capsule_created\\\": ok,\\n            \\\"ready_for_higher_policy_review\\\": ok,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D88 should request explicit higher-policy approval. Real apply remains blocked.\\\",\\n        },\\n    }\\n\\n    write_json(root / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(create_final_pre_apply_safety_capsule(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.final_pre_apply_safety_capsule import create_final_pre_apply_safety_capsule\\n\\n\\nclass TestD87FinalPreApplySafetyCapsule(unittest.TestCase):\\n    def make_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n\\n        (root / \\\"reports/d86_local_regression_runner.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"LOCAL_REGRESSION_PASSED\\\",\\n                    \\\"package_id\\\": \\\"d85-test-package\\\",\\n                    \\\"review_id\\\": \\\"d84-test-review\\\",\\n                    \\\"summary\\\": {\\\"commands_failed_count\\\": 0},\\n                    \\\"guardrails\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                        \\\"local_regression_only\\\": True,\\n                        \\\"allowlisted_commands_only\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d86_local_regression_results.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"package_id\\\": \\\"d85-test-package\\\",\\n                    \\\"review_id\\\": \\\"d84-test-review\\\",\\n                    \\\"commands_run_count\\\": 4,\\n                    \\\"commands_failed_count\\\": 0,\\n                    \\\"actual_apply_executed\\\": False,\\n                    \\\"route_inserted\\\": False,\\n                    \\\"protected_core_touched\\\": False,\\n                    \\\"network_accessed\\\": False,\\n                    \\\"external_ai_called\\\": False,\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d85_regression_rollback_evidence.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"REGRESSION_ROLLBACK_EVIDENCE_READY\\\",\\n                    \\\"package_id\\\": \\\"d85-test-package\\\",\\n                    \\\"evidence\\\": {\\\"review_id\\\": \\\"d84-test-review\\\"},\\n                    \\\"guardrails\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                        \\\"rollback_evidence_only\\\": True,\\n                        \\\"regression_evidence_only\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d85_rollback_manifest.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"human_review_required\\\": True,\\n                    \\\"actual_rollback_executed\\\": False,\\n                    \\\"actual_apply_executed\\\": False,\\n                    \\\"route_inserted\\\": False,\\n                    \\\"protected_core_touched\\\": False,\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d85_regression_checklist.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"pass_condition\\\": {\\n                        \\\"all_tests_green\\\": True,\\n                        \\\"rollback_manifest_present\\\": True,\\n                        \\\"no_protected_core_mutation\\\": True,\\n                        \\\"no_route_insert\\\": True,\\n                        \\\"no_actual_apply\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        return td, root\\n\\n    def test_creates_final_pre_apply_capsule(self):\\n        td, root = self.make_root()\\n        try:\\n            report = create_final_pre_apply_safety_capsule(root=root)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"FINAL_PRE_APPLY_SAFETY_CAPSULE_READY\\\")\\n            self.assertFalse(report[\\\"capsule\\\"][\\\"approval_state\\\"][\\\"ready_for_real_apply\\\"])\\n            self.assertFalse(report[\\\"blockers\\\"][\\\"apply_allowed_now\\\"])\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"final_capsule_only\\\"])\\n            self.assertTrue((root / \\\"reports/d87_final_pre_apply_safety_capsule.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d87_pre_apply_safety_capsule.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d87_apply_blockers.json\\\").exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d86(self):\\n        td, root = self.make_root()\\n        try:\\n            (root / \\\"reports/d86_local_regression_runner.json\\\").unlink()\\n            report = create_final_pre_apply_safety_capsule(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"FINAL_PRE_APPLY_SAFETY_CAPSULE_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_failed_regression(self):\\n        td, root = self.make_root()\\n        try:\\n            p = root / \\\"reports/d86_local_regression_results.json\\\"\\n            data = json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n            data[\\\"commands_failed_count\\\"] = 1\\n            p.write_text(json.dumps(data), encoding=\\\"utf-8\\\")\\n\\n            report = create_final_pre_apply_safety_capsule(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"FINAL_PRE_APPLY_SAFETY_CAPSULE_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


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

print("D87 FINAL PRE-APPLY SAFETY CAPSULE BOOT: repo =", ROOT)

Path("runtime_experimental/final_pre_apply_safety_capsule.py").write_text(MODULE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/final_pre_apply_safety_capsule.py")

Path("tests/test_d87_final_pre_apply_safety_capsule.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d87_final_pre_apply_safety_capsule.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/final_pre_apply_safety_capsule.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d87_final_pre_apply_safety_capsule", "-v"], check=True)

print("\n== run D87 final pre-apply safety capsule ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.final_pre_apply_safety_capsule import create_final_pre_apply_safety_capsule\n"
        "r=create_final_pre_apply_safety_capsule()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d87_final_pre_apply_safety_capsule.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== capsule preview ==")
cp = Path("reports/d87_pre_apply_safety_capsule.json")
if cp.exists():
    data = json.loads(cp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("CAPSULE_ID:", data.get("capsule_id"))
    print("NEXT_GATE:", data.get("next_gate"))
    print("APPROVAL_STATE:", data.get("approval_state"))

print("\n== blockers preview ==")
bp = Path("reports/d87_apply_blockers.json")
if bp.exists():
    data = json.loads(bp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("APPLY_ALLOWED_NOW:", data.get("apply_allowed_now"))
    print("ROUTE_INSERT_ALLOWED_NOW:", data.get("route_insert_allowed_now"))
    print("REQUIRED_BEFORE_APPLY:", data.get("required_before_apply_can_be_discussed"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/final_pre_apply_safety_capsule.py",
    "tests/test_d87_final_pre_apply_safety_capsule.py",
    "reports/d87_final_pre_apply_safety_capsule.json",
    "reports/d87_pre_apply_safety_capsule.json",
    "reports/d87_apply_blockers.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D87_FINAL_PRE_APPLY_SAFETY_CAPSULE_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D87 final pre-apply safety capsule"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D87 final pre-apply safety capsule changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD87 FINAL PRE-APPLY SAFETY CAPSULE BOOT DONE")
