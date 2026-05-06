#!/usr/bin/env python3
# D85_REGRESSION_ROLLBACK_EVIDENCE_BOOT.py
#
# Adds D85 Regression + Rollback Evidence Bundle to GitCube OS.
#
# Run from repo root:
#     python D85_REGRESSION_ROLLBACK_EVIDENCE_BOOT.py
#
# Creates:
# - runtime_experimental/regression_rollback_evidence.py
# - tests/test_d85_regression_rollback_evidence.py
# - reports/d85_regression_rollback_evidence.json
# - reports/d85_rollback_manifest.json
# - reports/d85_regression_checklist.json
#
# D85 does NOT call an external AI API.
# D85 does NOT use network access.
# D85 does NOT execute raw code from AI.
# D85 does NOT run shell commands from AI.
# D85 does NOT patch task_dispatcher.py.
# D85 does NOT mutate protected core.
# D85 does NOT overwrite canonical memory.
# D85 does NOT insert a real route.
# D85 does NOT apply changes.
#
# D85 only creates rollback/regression evidence for reviewed sandbox output.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_CODE = json.loads("\"from __future__ import annotations\\n\\nimport hashlib\\nimport json\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nD84_REPORT = \\\"reports/d84_sandbox_writer_output_review.json\\\"\\nOUT = \\\"reports/d85_regression_rollback_evidence.json\\\"\\nROLLBACK_OUT = \\\"reports/d85_rollback_manifest.json\\\"\\nCHECKLIST_OUT = \\\"reports/d85_regression_checklist.json\\\"\\n\\n\\nPROTECTED_PREFIXES = [\\n    \\\"app/orchestration/\\\",\\n    \\\"core/\\\",\\n    \\\"runtime/\\\",\\n    \\\"bridges/\\\",\\n    \\\"memory/\\\",\\n]\\n\\nALLOWED_CANDIDATE_PREFIXES = [\\n    \\\"runtime_experimental/ai_sandbox_work/\\\",\\n    \\\"reports/\\\",\\n    \\\"tests/\\\",\\n]\\n\\nREQUIRED_ROLLBACK_ITEMS = [\\n    \\\"pre_apply_git_sha\\\",\\n    \\\"candidate_files\\\",\\n    \\\"created_files\\\",\\n    \\\"mutated_files\\\",\\n    \\\"restore_strategy\\\",\\n    \\\"verification_commands\\\",\\n    \\\"human_review_required\\\",\\n]\\n\\n\\ndef now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef safe_path(value: str) -> str:\\n    raw = str(value or \\\"\\\").strip().replace(\\\"\\\\\\\\\\\", \\\"/\\\").lstrip(\\\"/\\\")\\n    return \\\"/\\\".join(x for x in raw.split(\\\"/\\\") if x and x not in (\\\".\\\", \\\"..\\\"))\\n\\n\\ndef sha256_json(data: Dict[str, Any]) -> str:\\n    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode(\\\"utf-8\\\")).hexdigest()\\n\\n\\ndef path_allowed(path: str) -> bool:\\n    p = safe_path(path)\\n    if any(p.startswith(prefix) for prefix in PROTECTED_PREFIXES):\\n        return False\\n    return any(p.startswith(prefix) for prefix in ALLOWED_CANDIDATE_PREFIXES)\\n\\n\\ndef validate_d84(d84: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:\\n    if not d84:\\n        errors.append(\\\"D84 report missing or unreadable\\\")\\n        return {}\\n\\n    if d84.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D84 ok flag is not true\\\")\\n    if d84.get(\\\"decision\\\") != \\\"SANDBOX_WRITER_OUTPUT_REVIEW_READY\\\":\\n        errors.append(f\\\"D84 decision invalid: {d84.get('decision')}\\\")\\n\\n    guard = d84.get(\\\"guardrails\\\") if isinstance(d84.get(\\\"guardrails\\\"), dict) else {}\\n    for key in (\\n        \\\"external_ai_called\\\",\\n        \\\"network_accessed\\\",\\n        \\\"runtime_code_mutated\\\",\\n        \\\"protected_core_mutated\\\",\\n        \\\"canonical_memory_mutated\\\",\\n        \\\"actual_apply_executed\\\",\\n        \\\"route_inserted\\\",\\n        \\\"git_commit_by_ai\\\",\\n    ):\\n        if guard.get(key) is not False:\\n            errors.append(f\\\"D84 guardrail {key} is not false\\\")\\n    if guard.get(\\\"sandbox_output_review_only\\\") is not True:\\n        errors.append(\\\"D84 sandbox_output_review_only is not true\\\")\\n    if guard.get(\\\"writer_output_candidate_only\\\") is not True:\\n        errors.append(\\\"D84 writer_output_candidate_only is not true\\\")\\n\\n    review = d84.get(\\\"review\\\") if isinstance(d84.get(\\\"review\\\"), dict) else {}\\n    if not review:\\n        errors.append(\\\"D84 review object missing\\\")\\n    else:\\n        if review.get(\\\"approved_for_guarded_apply\\\") is not False:\\n            errors.append(\\\"D84 must not approve guarded apply\\\")\\n        if review.get(\\\"approved_for_route_insert\\\") is not False:\\n            errors.append(\\\"D84 must not approve route insert\\\")\\n        if review.get(\\\"approved_for_protected_core\\\") is not False:\\n            errors.append(\\\"D84 must not approve protected core\\\")\\n        if review.get(\\\"approved_for_next_sandbox_gate\\\") is not True:\\n            errors.append(\\\"D84 must approve next sandbox gate\\\")\\n\\n    writer_output_path = str(d84.get(\\\"writer_output_path\\\") or \\\"\\\")\\n    if not writer_output_path:\\n        errors.append(\\\"D84 writer_output_path missing\\\")\\n        return {}\\n\\n    writer_output = read_json(writer_output_path, {}) or {}\\n    if not writer_output:\\n        errors.append(\\\"D84 writer output file missing or unreadable\\\")\\n        return {}\\n\\n    if writer_output.get(\\\"mode\\\") != \\\"SANDBOX_OUTPUT_CANDIDATE_ONLY\\\":\\n        errors.append(f\\\"D84 writer output mode invalid: {writer_output.get('mode')}\\\")\\n\\n    candidate_files = writer_output.get(\\\"candidate_files\\\")\\n    if not isinstance(candidate_files, list) or not candidate_files:\\n        errors.append(\\\"D84 writer output candidate_files missing\\\")\\n    else:\\n        for f in candidate_files:\\n            if not path_allowed(str(f)):\\n                errors.append(f\\\"candidate file outside allowed sandbox scope: {f}\\\")\\n\\n    wguard = writer_output.get(\\\"guardrails\\\") if isinstance(writer_output.get(\\\"guardrails\\\"), dict) else {}\\n    for key in (\\n        \\\"actual_apply_executed\\\",\\n        \\\"route_inserted\\\",\\n        \\\"protected_core_mutated\\\",\\n        \\\"canonical_memory_mutated\\\",\\n        \\\"external_ai_called\\\",\\n        \\\"network_accessed\\\",\\n        \\\"git_commit_by_ai\\\",\\n    ):\\n        if wguard.get(key) is not False:\\n            errors.append(f\\\"D84 writer output guardrail {key} is not false\\\")\\n    if wguard.get(\\\"sandbox_output_only\\\") is not True:\\n        errors.append(\\\"D84 writer output sandbox_output_only is not true\\\")\\n\\n    return writer_output\\n\\n\\ndef build_rollback_manifest(package_id: str, d84: Dict[str, Any], writer_output: Dict[str, Any]) -> Dict[str, Any]:\\n    candidate_files = [safe_path(str(p)) for p in writer_output.get(\\\"candidate_files\\\", [])]\\n    evidence = d84.get(\\\"evidence\\\") if isinstance(d84.get(\\\"evidence\\\"), dict) else {}\\n\\n    return {\\n        \\\"state\\\": \\\"D85_ROLLBACK_MANIFEST\\\",\\n        \\\"ok\\\": True,\\n        \\\"package_id\\\": package_id,\\n        \\\"created_at\\\": now(),\\n        \\\"pre_apply_git_sha\\\": \\\"NO_APPLY_EXECUTED\\\",\\n        \\\"source_review_id\\\": d84.get(\\\"review_id\\\"),\\n        \\\"source_handoff_id\\\": evidence.get(\\\"handoff_id\\\"),\\n        \\\"source_proposal_id\\\": evidence.get(\\\"proposal_id\\\"),\\n        \\\"candidate_files\\\": candidate_files,\\n        \\\"created_files\\\": candidate_files,\\n        \\\"mutated_files\\\": [],\\n        \\\"protected_files\\\": PROTECTED_PREFIXES,\\n        \\\"restore_strategy\\\": {\\n            \\\"type\\\": \\\"delete_created_sandbox_candidates_only\\\",\\n            \\\"commands_are_documentation_only\\\": True,\\n            \\\"commands\\\": [\\n                \\\"git status --short\\\",\\n                \\\"git clean -n runtime_experimental/ai_sandbox_work reports tests\\\",\\n                \\\"manual review before any clean/apply\\\",\\n            ],\\n        },\\n        \\\"verification_commands\\\": [\\n            \\\"python -m py_compile runtime_experimental/sandbox_writer_output_review.py\\\",\\n            \\\"python -m unittest tests.test_d84_sandbox_writer_output_review -v\\\",\\n            \\\"python -m py_compile runtime_experimental/regression_rollback_evidence.py\\\",\\n            \\\"python -m unittest tests.test_d85_regression_rollback_evidence -v\\\",\\n        ],\\n        \\\"human_review_required\\\": True,\\n        \\\"actual_rollback_executed\\\": False,\\n        \\\"actual_apply_executed\\\": False,\\n        \\\"route_inserted\\\": False,\\n        \\\"protected_core_touched\\\": False,\\n    }\\n\\n\\ndef build_regression_checklist(package_id: str, d84: Dict[str, Any]) -> Dict[str, Any]:\\n    return {\\n        \\\"state\\\": \\\"D85_REGRESSION_CHECKLIST\\\",\\n        \\\"ok\\\": True,\\n        \\\"package_id\\\": package_id,\\n        \\\"created_at\\\": now(),\\n        \\\"source_review_id\\\": d84.get(\\\"review_id\\\"),\\n        \\\"required_before_any_apply\\\": [\\n            \\\"D66_RECHECK\\\",\\n            \\\"D64_SAFE_MUTATION_GATE_RECHECK\\\",\\n            \\\"UNIT_TESTS\\\",\\n            \\\"REGRESSION_TESTS\\\",\\n            \\\"ROLLBACK_MANIFEST_PRESENT\\\",\\n            \\\"HUMAN_OR_HIGHER_POLICY_APPROVAL\\\",\\n        ],\\n        \\\"commands_to_run_manually\\\": [\\n            \\\"python -m unittest discover -s tests -v\\\",\\n            \\\"python -m py_compile runtime_experimental/*.py\\\",\\n            \\\"git diff --stat\\\",\\n            \\\"git status --short\\\",\\n        ],\\n        \\\"pass_condition\\\": {\\n            \\\"all_tests_green\\\": True,\\n            \\\"rollback_manifest_present\\\": True,\\n            \\\"no_protected_core_mutation\\\": True,\\n            \\\"no_route_insert\\\": True,\\n            \\\"no_actual_apply\\\": True,\\n        },\\n        \\\"not_allowed\\\": [\\n            \\\"auto_apply_runtime_mutation\\\",\\n            \\\"direct_core_edit\\\",\\n            \\\"route_insert\\\",\\n            \\\"commit_generated_patch_without_human_review\\\",\\n        ],\\n    }\\n\\n\\ndef validate_package(manifest: Dict[str, Any], checklist: Dict[str, Any], errors: List[str]) -> None:\\n    for item in REQUIRED_ROLLBACK_ITEMS:\\n        if item not in manifest:\\n            errors.append(f\\\"rollback manifest missing required item: {item}\\\")\\n\\n    if manifest.get(\\\"actual_rollback_executed\\\") is not False:\\n        errors.append(\\\"rollback manifest actual_rollback_executed must be false\\\")\\n    if manifest.get(\\\"actual_apply_executed\\\") is not False:\\n        errors.append(\\\"rollback manifest actual_apply_executed must be false\\\")\\n    if manifest.get(\\\"route_inserted\\\") is not False:\\n        errors.append(\\\"rollback manifest route_inserted must be false\\\")\\n    if manifest.get(\\\"protected_core_touched\\\") is not False:\\n        errors.append(\\\"rollback manifest protected_core_touched must be false\\\")\\n    if manifest.get(\\\"human_review_required\\\") is not True:\\n        errors.append(\\\"rollback manifest human_review_required must be true\\\")\\n\\n    for f in manifest.get(\\\"candidate_files\\\", []):\\n        if not path_allowed(str(f)):\\n            errors.append(f\\\"rollback candidate path outside allowed scope: {f}\\\")\\n\\n    pass_condition = checklist.get(\\\"pass_condition\\\") if isinstance(checklist.get(\\\"pass_condition\\\"), dict) else {}\\n    for key in (\\n        \\\"all_tests_green\\\",\\n        \\\"rollback_manifest_present\\\",\\n        \\\"no_protected_core_mutation\\\",\\n        \\\"no_route_insert\\\",\\n        \\\"no_actual_apply\\\",\\n    ):\\n        if pass_condition.get(key) is not True:\\n            errors.append(f\\\"regression checklist pass condition {key} is not true\\\")\\n\\n\\ndef create_regression_rollback_evidence(\\n    root: str | Path = \\\".\\\",\\n    d84_report_path: str = D84_REPORT,\\n    output_path: str = OUT,\\n    rollback_output_path: str = ROLLBACK_OUT,\\n    checklist_output_path: str = CHECKLIST_OUT,\\n) -> Dict[str, Any]:\\n    root = Path(root).resolve()\\n    d84 = read_json(root / d84_report_path, {}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    writer_output = validate_d84(d84, errors)\\n\\n    review_id = str(d84.get(\\\"review_id\\\") or \\\"\\\")\\n    handoff_id = str((d84.get(\\\"evidence\\\") or {}).get(\\\"handoff_id\\\") or \\\"\\\")\\n    proposal_id = str((d84.get(\\\"evidence\\\") or {}).get(\\\"proposal_id\\\") or \\\"\\\")\\n\\n    package_id = \\\"d85-\\\" + sha256_json(\\n        {\\n            \\\"review_id\\\": review_id,\\n            \\\"handoff_id\\\": handoff_id,\\n            \\\"proposal_id\\\": proposal_id,\\n            \\\"candidate_files\\\": writer_output.get(\\\"candidate_files\\\") if writer_output else [],\\n        }\\n    )[:16]\\n\\n    rollback_manifest = build_rollback_manifest(package_id, d84, writer_output) if writer_output else {}\\n    regression_checklist = build_regression_checklist(package_id, d84) if d84 else {}\\n\\n    if rollback_manifest and regression_checklist:\\n        validate_package(rollback_manifest, regression_checklist, errors)\\n\\n    ok = not errors\\n    decision = \\\"REGRESSION_ROLLBACK_EVIDENCE_READY\\\" if ok else \\\"REGRESSION_ROLLBACK_EVIDENCE_BLOCKED\\\"\\n    result = \\\"D85_REGRESSION_ROLLBACK_EVIDENCE_CREATED\\\" if ok else \\\"D85_REGRESSION_ROLLBACK_EVIDENCE_BLOCKED\\\"\\n\\n    if ok:\\n        write_json(root / rollback_output_path, rollback_manifest)\\n        write_json(root / checklist_output_path, regression_checklist)\\n\\n    report = {\\n        \\\"state\\\": \\\"D85_REGRESSION_ROLLBACK_EVIDENCE\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_REGRESSION_ROLLBACK_EVIDENCE\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": now(),\\n        \\\"package_id\\\": package_id,\\n        \\\"rollback_manifest_path\\\": str(root / rollback_output_path) if ok else \\\"\\\",\\n        \\\"regression_checklist_path\\\": str(root / checklist_output_path) if ok else \\\"\\\",\\n        \\\"input_reports\\\": {\\n            \\\"d84_report_path\\\": str(root / d84_report_path),\\n        },\\n        \\\"evidence\\\": {\\n            \\\"review_id\\\": review_id,\\n            \\\"handoff_id\\\": handoff_id,\\n            \\\"proposal_id\\\": proposal_id,\\n            \\\"candidate_files\\\": writer_output.get(\\\"candidate_files\\\") if writer_output else [],\\n        },\\n        \\\"rollback_manifest\\\": rollback_manifest if ok else {},\\n        \\\"regression_checklist\\\": regression_checklist if ok else {},\\n        \\\"guardrails\\\": {\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n            \\\"rollback_evidence_only\\\": True,\\n            \\\"regression_evidence_only\\\": True,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"package_id\\\": package_id,\\n            \\\"review_id\\\": review_id,\\n            \\\"candidate_files_count\\\": len(writer_output.get(\\\"candidate_files\\\", [])) if writer_output else 0,\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"regression_rollback_evidence_created\\\": ok,\\n            \\\"rollback_manifest_created\\\": ok,\\n            \\\"regression_checklist_created\\\": ok,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D86 can run local regression command probes and collect results; real apply still blocked.\\\",\\n        },\\n    }\\n\\n    write_json(root / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(create_regression_rollback_evidence(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.regression_rollback_evidence import create_regression_rollback_evidence\\n\\n\\nclass TestD85RegressionRollbackEvidence(unittest.TestCase):\\n    def make_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n        (root / \\\"runtime_experimental/ai_sandbox_work/d84-test\\\").mkdir(parents=True)\\n\\n        writer_output = root / \\\"runtime_experimental/ai_sandbox_work/d84-test/writer_output_candidate.json\\\"\\n        writer_output.write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"mode\\\": \\\"SANDBOX_OUTPUT_CANDIDATE_ONLY\\\",\\n                    \\\"candidate_files\\\": [\\n                        \\\"runtime_experimental/ai_sandbox_work/d84-test/candidate_proposal.json\\\",\\n                        \\\"reports/d84-test_candidate_review.json\\\",\\n                        \\\"tests/test_d84_test_candidate_probe.py\\\",\\n                    ],\\n                    \\\"forbidden_actions\\\": [\\n                        \\\"direct_core_edit\\\",\\n                        \\\"route_insert\\\",\\n                        \\\"actual_apply\\\",\\n                        \\\"external_ai_network_call\\\",\\n                        \\\"git_commit_or_push_by_ai\\\",\\n                        \\\"canonical_memory_overwrite\\\",\\n                    ],\\n                    \\\"guardrails\\\": {\\n                        \\\"sandbox_output_only\\\": True,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d84_sandbox_writer_output_review.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"SANDBOX_WRITER_OUTPUT_REVIEW_READY\\\",\\n                    \\\"review_id\\\": \\\"d84-test-review\\\",\\n                    \\\"writer_output_path\\\": str(writer_output),\\n                    \\\"evidence\\\": {\\n                        \\\"handoff_id\\\": \\\"d83-test-handoff\\\",\\n                        \\\"proposal_id\\\": \\\"d80-proposal-test\\\",\\n                    },\\n                    \\\"review\\\": {\\n                        \\\"approved_for_guarded_apply\\\": False,\\n                        \\\"approved_for_route_insert\\\": False,\\n                        \\\"approved_for_protected_core\\\": False,\\n                        \\\"approved_for_next_sandbox_gate\\\": True,\\n                    },\\n                    \\\"guardrails\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                        \\\"sandbox_output_review_only\\\": True,\\n                        \\\"writer_output_candidate_only\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        return td, root\\n\\n    def test_creates_regression_rollback_bundle(self):\\n        td, root = self.make_root()\\n        try:\\n            report = create_regression_rollback_evidence(root=root)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"REGRESSION_ROLLBACK_EVIDENCE_READY\\\")\\n            self.assertFalse(report[\\\"guardrails\\\"][\\\"actual_apply_executed\\\"])\\n            self.assertTrue(report[\\\"rollback_manifest\\\"][\\\"human_review_required\\\"])\\n            self.assertTrue((root / \\\"reports/d85_regression_rollback_evidence.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d85_rollback_manifest.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d85_regression_checklist.json\\\").exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d84(self):\\n        td, root = self.make_root()\\n        try:\\n            (root / \\\"reports/d84_sandbox_writer_output_review.json\\\").unlink()\\n            report = create_regression_rollback_evidence(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"REGRESSION_ROLLBACK_EVIDENCE_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_protected_candidate_path(self):\\n        td, root = self.make_root()\\n        try:\\n            p = root / \\\"runtime_experimental/ai_sandbox_work/d84-test/writer_output_candidate.json\\\"\\n            data = json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n            data[\\\"candidate_files\\\"].append(\\\"app/orchestration/task_dispatcher.py\\\")\\n            p.write_text(json.dumps(data), encoding=\\\"utf-8\\\")\\n\\n            report = create_regression_rollback_evidence(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"REGRESSION_ROLLBACK_EVIDENCE_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


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

print("D85 REGRESSION ROLLBACK EVIDENCE BOOT: repo =", ROOT)

Path("runtime_experimental/regression_rollback_evidence.py").write_text(MODULE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/regression_rollback_evidence.py")

Path("tests/test_d85_regression_rollback_evidence.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d85_regression_rollback_evidence.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/regression_rollback_evidence.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d85_regression_rollback_evidence", "-v"], check=True)

print("\n== run D85 regression rollback evidence ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.regression_rollback_evidence import create_regression_rollback_evidence\n"
        "r=create_regression_rollback_evidence()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d85_regression_rollback_evidence.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== rollback manifest preview ==")
mp = Path("reports/d85_rollback_manifest.json")
if mp.exists():
    data = json.loads(mp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("PACKAGE_ID:", data.get("package_id"))
    print("HUMAN_REVIEW_REQUIRED:", data.get("human_review_required"))
    print("ACTUAL_APPLY_EXECUTED:", data.get("actual_apply_executed"))

print("\n== regression checklist preview ==")
cp = Path("reports/d85_regression_checklist.json")
if cp.exists():
    data = json.loads(cp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("REQUIRED:", data.get("required_before_any_apply"))
    print("NOT_ALLOWED:", data.get("not_allowed"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/regression_rollback_evidence.py",
    "tests/test_d85_regression_rollback_evidence.py",
    "reports/d85_regression_rollback_evidence.json",
    "reports/d85_rollback_manifest.json",
    "reports/d85_regression_checklist.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D85_REGRESSION_ROLLBACK_EVIDENCE_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D85 regression rollback evidence"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D85 regression rollback evidence changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD85 REGRESSION ROLLBACK EVIDENCE BOOT DONE")
