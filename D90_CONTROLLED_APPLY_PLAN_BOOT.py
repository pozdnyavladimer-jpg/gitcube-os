#!/usr/bin/env python3
# D90_CONTROLLED_APPLY_PLAN_BOOT.py
#
# Adds D90 Controlled Apply Plan Preview to GitCube OS.
#
# Run from repo root:
#     python D90_CONTROLLED_APPLY_PLAN_BOOT.py
#
# Creates:
# - runtime_experimental/controlled_apply_plan.py
# - tests/test_d90_controlled_apply_plan.py
# - reports/d90_controlled_apply_plan.json
# - reports/d90_apply_command_preview.json
# - reports/d90_manual_review_checklist.json
#
# D90 does NOT call an external AI API.
# D90 does NOT use network access.
# D90 does NOT execute raw code from AI.
# D90 does NOT run shell commands from AI.
# D90 does NOT patch task_dispatcher.py.
# D90 does NOT mutate protected core.
# D90 does NOT overwrite canonical memory.
# D90 does NOT insert a real route.
# D90 does NOT apply changes.
# D90 does NOT approve real apply.
#
# D90 only creates a controlled apply plan preview and manual checklist.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_CODE = json.loads("\"from __future__ import annotations\\n\\nimport hashlib\\nimport json\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nD89_REPORT = \\\"reports/d89_final_human_confirmation.json\\\"\\nD89_STATEMENT = \\\"reports/d89_human_confirmation_statement.json\\\"\\nD89_SCOPE = \\\"reports/d89_d90_planning_scope.json\\\"\\n\\nOUT = \\\"reports/d90_controlled_apply_plan.json\\\"\\nPREVIEW_OUT = \\\"reports/d90_apply_command_preview.json\\\"\\nCHECKLIST_OUT = \\\"reports/d90_manual_review_checklist.json\\\"\\n\\n\\nREQUIRED_D89_DECISION = \\\"FINAL_HUMAN_CONFIRMATION_READY\\\"\\nREQUIRED_D90_GATE = \\\"D90_CONTROLLED_APPLY_PLAN\\\"\\nREQUIRED_CONFIRMATION_PHRASE = \\\"CONFIRM_D89_FINAL_HUMAN_REVIEW_FOR_D90_PLANNING_ONLY\\\"\\n\\nHARD_FALSE_FLAGS = [\\n    \\\"external_ai_called\\\",\\n    \\\"network_accessed\\\",\\n    \\\"runtime_code_mutated\\\",\\n    \\\"protected_core_mutated\\\",\\n    \\\"canonical_memory_mutated\\\",\\n    \\\"actual_apply_executed\\\",\\n    \\\"route_inserted\\\",\\n    \\\"git_commit_by_ai\\\",\\n]\\n\\nD90_NOT_EXECUTE = [\\n    \\\"actual_apply\\\",\\n    \\\"route_insert\\\",\\n    \\\"protected_core_mutation\\\",\\n    \\\"canonical_memory_overwrite\\\",\\n    \\\"external_ai_network_call\\\",\\n    \\\"git_commit_or_push_by_ai\\\",\\n]\\n\\n\\ndef now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef sha256_json(data: Dict[str, Any]) -> str:\\n    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode(\\\"utf-8\\\")).hexdigest()\\n\\n\\ndef validate_false_flags(name: str, data: Dict[str, Any], errors: List[str]) -> None:\\n    for key in HARD_FALSE_FLAGS:\\n        if data.get(key) is not False:\\n            errors.append(f\\\"{name} flag {key} is not false\\\")\\n\\n\\ndef validate_d89(\\n    d89: Dict[str, Any],\\n    statement: Dict[str, Any],\\n    scope: Dict[str, Any],\\n    errors: List[str],\\n) -> None:\\n    if not d89:\\n        errors.append(\\\"D89 final human confirmation report missing or unreadable\\\")\\n        return\\n\\n    if d89.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D89 ok flag is not true\\\")\\n    if d89.get(\\\"decision\\\") != REQUIRED_D89_DECISION:\\n        errors.append(f\\\"D89 decision invalid: {d89.get('decision')}\\\")\\n\\n    guard = d89.get(\\\"guardrails\\\") if isinstance(d89.get(\\\"guardrails\\\"), dict) else {}\\n    validate_false_flags(\\\"D89 guardrail\\\", guard, errors)\\n\\n    if guard.get(\\\"final_human_confirmation_only\\\") is not True:\\n        errors.append(\\\"D89 final_human_confirmation_only is not true\\\")\\n    if guard.get(\\\"d90_planning_only\\\") is not True:\\n        errors.append(\\\"D89 d90_planning_only is not true\\\")\\n    if guard.get(\\\"approval_for_real_apply\\\") is not False:\\n        errors.append(\\\"D89 approval_for_real_apply is not false\\\")\\n\\n    if not statement:\\n        errors.append(\\\"D89 human confirmation statement missing or unreadable\\\")\\n    else:\\n        if statement.get(\\\"ok\\\") is not True:\\n            errors.append(\\\"D89 statement ok flag is not true\\\")\\n        if statement.get(\\\"confirmation_phrase\\\") != REQUIRED_CONFIRMATION_PHRASE:\\n            errors.append(f\\\"D89 confirmation phrase invalid: {statement.get('confirmation_phrase')}\\\")\\n        if statement.get(\\\"approved_next_gate\\\") != REQUIRED_D90_GATE:\\n            errors.append(f\\\"D89 approved_next_gate invalid: {statement.get('approved_next_gate')}\\\")\\n        for item in D90_NOT_EXECUTE:\\n            if item not in statement.get(\\\"not_approved\\\", []):\\n                errors.append(f\\\"D89 statement missing not_approved item: {item}\\\")\\n\\n    if not scope:\\n        errors.append(\\\"D89 D90 planning scope missing or unreadable\\\")\\n    else:\\n        if scope.get(\\\"ok\\\") is not True:\\n            errors.append(\\\"D89 D90 scope ok flag is not true\\\")\\n        if scope.get(\\\"next_gate\\\") != REQUIRED_D90_GATE:\\n            errors.append(f\\\"D89 D90 scope next_gate invalid: {scope.get('next_gate')}\\\")\\n        for key in (\\n            \\\"apply_allowed_after_d89\\\",\\n            \\\"route_insert_allowed_after_d89\\\",\\n            \\\"protected_core_mutation_allowed_after_d89\\\",\\n        ):\\n            if scope.get(key) is not False:\\n                errors.append(f\\\"D89 D90 scope {key} is not false\\\")\\n\\n        allowed = scope.get(\\\"d90_allowed_to_create\\\")\\n        if not isinstance(allowed, list):\\n            errors.append(\\\"D89 D90 scope d90_allowed_to_create missing\\\")\\n        else:\\n            for item in (\\n                \\\"controlled_apply_plan_json\\\",\\n                \\\"explicit_scope_diff_summary\\\",\\n                \\\"pre_apply_command_preview\\\",\\n                \\\"manual_review_checklist\\\",\\n            ):\\n                if item not in allowed:\\n                    errors.append(f\\\"D89 D90 scope missing allowed create item: {item}\\\")\\n\\n        must_not = scope.get(\\\"d90_must_not_execute\\\")\\n        if not isinstance(must_not, list):\\n            errors.append(\\\"D89 D90 scope d90_must_not_execute missing\\\")\\n        else:\\n            for item in D90_NOT_EXECUTE:\\n                if item not in must_not:\\n                    errors.append(f\\\"D89 D90 scope missing must-not-execute item: {item}\\\")\\n\\n\\ndef build_apply_command_preview(plan_id: str, d89: Dict[str, Any], statement: Dict[str, Any]) -> Dict[str, Any]:\\n    evidence = d89.get(\\\"evidence\\\") if isinstance(d89.get(\\\"evidence\\\"), dict) else {}\\n\\n    return {\\n        \\\"state\\\": \\\"D90_APPLY_COMMAND_PREVIEW\\\",\\n        \\\"ok\\\": True,\\n        \\\"plan_id\\\": plan_id,\\n        \\\"created_at\\\": now(),\\n        \\\"preview_only\\\": True,\\n        \\\"source_confirmation_id\\\": d89.get(\\\"confirmation_id\\\") or statement.get(\\\"confirmation_id\\\"),\\n        \\\"source_request_id\\\": evidence.get(\\\"request_id\\\") or statement.get(\\\"source_request_id\\\"),\\n        \\\"source_package_id\\\": evidence.get(\\\"package_id\\\") or statement.get(\\\"source_package_id\\\"),\\n        \\\"commands_are_documentation_only\\\": True,\\n        \\\"commands_must_not_be_executed_by_ai\\\": True,\\n        \\\"pre_apply_command_preview\\\": [\\n            \\\"# PREVIEW ONLY \\u2014 do not execute automatically\\\",\\n            \\\"python -m unittest discover -s tests -v\\\",\\n            \\\"python -m py_compile runtime_experimental/*.py\\\",\\n            \\\"git diff --stat\\\",\\n            \\\"git status --short\\\",\\n            \\\"# Apply remains blocked until D91 explicit apply-scope approval.\\\",\\n        ],\\n        \\\"blocked_commands\\\": [\\n            \\\"git apply\\\",\\n            \\\"python -c '<runtime mutation>'\\\",\\n            \\\"git commit\\\",\\n            \\\"git push\\\",\\n            \\\"route insert\\\",\\n            \\\"direct protected-core edit\\\",\\n        ],\\n    }\\n\\n\\ndef build_manual_review_checklist(plan_id: str) -> Dict[str, Any]:\\n    return {\\n        \\\"state\\\": \\\"D90_MANUAL_REVIEW_CHECKLIST\\\",\\n        \\\"ok\\\": True,\\n        \\\"plan_id\\\": plan_id,\\n        \\\"created_at\\\": now(),\\n        \\\"human_review_required\\\": True,\\n        \\\"checklist\\\": [\\n            \\\"Confirm D89 statement exists and scope is D90 planning only.\\\",\\n            \\\"Confirm D85 rollback manifest exists.\\\",\\n            \\\"Confirm D86 local regression results passed.\\\",\\n            \\\"Confirm no protected core mutation is planned.\\\",\\n            \\\"Confirm no route insertion is planned.\\\",\\n            \\\"Confirm no external AI/network call is required.\\\",\\n            \\\"Confirm D91 explicit apply-scope approval is required before any real apply.\\\",\\n        ],\\n        \\\"must_remain_false\\\": {\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n        },\\n    }\\n\\n\\ndef build_controlled_plan(plan_id: str, d89: Dict[str, Any], statement: Dict[str, Any], scope: Dict[str, Any]) -> Dict[str, Any]:\\n    evidence = d89.get(\\\"evidence\\\") if isinstance(d89.get(\\\"evidence\\\"), dict) else {}\\n\\n    return {\\n        \\\"state\\\": \\\"D90_CONTROLLED_APPLY_PLAN_PREVIEW\\\",\\n        \\\"ok\\\": True,\\n        \\\"plan_id\\\": plan_id,\\n        \\\"created_at\\\": now(),\\n        \\\"mode\\\": \\\"PLAN_PREVIEW_ONLY\\\",\\n        \\\"source_confirmation_id\\\": d89.get(\\\"confirmation_id\\\") or statement.get(\\\"confirmation_id\\\"),\\n        \\\"source_request_id\\\": evidence.get(\\\"request_id\\\") or statement.get(\\\"source_request_id\\\"),\\n        \\\"source_capsule_id\\\": evidence.get(\\\"capsule_id\\\") or statement.get(\\\"source_capsule_id\\\"),\\n        \\\"source_package_id\\\": evidence.get(\\\"package_id\\\") or statement.get(\\\"source_package_id\\\"),\\n        \\\"source_review_id\\\": evidence.get(\\\"review_id\\\") or statement.get(\\\"source_review_id\\\"),\\n        \\\"allowed_to_create\\\": scope.get(\\\"d90_allowed_to_create\\\", []),\\n        \\\"must_not_execute\\\": scope.get(\\\"d90_must_not_execute\\\", []),\\n        \\\"plan_summary\\\": {\\n            \\\"goal\\\": \\\"Create a controlled apply plan preview for human review only.\\\",\\n            \\\"real_apply_allowed\\\": False,\\n            \\\"route_insert_allowed\\\": False,\\n            \\\"protected_core_mutation_allowed\\\": False,\\n            \\\"ai_git_action_allowed\\\": False,\\n        },\\n        \\\"explicit_scope_diff_summary\\\": {\\n            \\\"planned_files_to_touch\\\": [],\\n            \\\"protected_files_to_touch\\\": [],\\n            \\\"route_insertions\\\": [],\\n            \\\"runtime_mutations\\\": [],\\n            \\\"status\\\": \\\"NO_REAL_DIFF_PREPARED_D90_IS_PREVIEW_ONLY\\\",\\n        },\\n        \\\"required_next_gate\\\": \\\"D91_EXPLICIT_APPLY_SCOPE_APPROVAL\\\",\\n    }\\n\\n\\ndef create_controlled_apply_plan(\\n    root: str | Path = \\\".\\\",\\n    d89_report_path: str = D89_REPORT,\\n    d89_statement_path: str = D89_STATEMENT,\\n    d89_scope_path: str = D89_SCOPE,\\n    output_path: str = OUT,\\n    preview_output_path: str = PREVIEW_OUT,\\n    checklist_output_path: str = CHECKLIST_OUT,\\n) -> Dict[str, Any]:\\n    root = Path(root).resolve()\\n\\n    d89 = read_json(root / d89_report_path, {}) or {}\\n    statement = read_json(root / d89_statement_path, {}) or {}\\n    scope = read_json(root / d89_scope_path, {}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    validate_d89(d89, statement, scope, errors)\\n\\n    confirmation_id = str(d89.get(\\\"confirmation_id\\\") or statement.get(\\\"confirmation_id\\\") or \\\"\\\")\\n    request_id = str((d89.get(\\\"evidence\\\") or {}).get(\\\"request_id\\\") or statement.get(\\\"source_request_id\\\") or \\\"\\\")\\n    package_id = str((d89.get(\\\"evidence\\\") or {}).get(\\\"package_id\\\") or statement.get(\\\"source_package_id\\\") or \\\"\\\")\\n\\n    plan_id = \\\"d90-\\\" + sha256_json(\\n        {\\n            \\\"confirmation_id\\\": confirmation_id,\\n            \\\"request_id\\\": request_id,\\n            \\\"package_id\\\": package_id,\\n            \\\"d89_decision\\\": d89.get(\\\"decision\\\"),\\n        }\\n    )[:16]\\n\\n    ok = not errors\\n    decision = \\\"CONTROLLED_APPLY_PLAN_PREVIEW_READY\\\" if ok else \\\"CONTROLLED_APPLY_PLAN_PREVIEW_BLOCKED\\\"\\n    result = \\\"D90_CONTROLLED_APPLY_PLAN_CREATED\\\" if ok else \\\"D90_CONTROLLED_APPLY_PLAN_BLOCKED\\\"\\n\\n    plan = build_controlled_plan(plan_id, d89, statement, scope)\\n    preview = build_apply_command_preview(plan_id, d89, statement)\\n    checklist = build_manual_review_checklist(plan_id)\\n\\n    if ok:\\n        write_json(root / preview_output_path, preview)\\n        write_json(root / checklist_output_path, checklist)\\n\\n    report = {\\n        \\\"state\\\": \\\"D90_CONTROLLED_APPLY_PLAN\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_CONTROLLED_APPLY_PLAN\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": now(),\\n        \\\"plan_id\\\": plan_id,\\n        \\\"apply_command_preview_path\\\": str(root / preview_output_path) if ok else \\\"\\\",\\n        \\\"manual_review_checklist_path\\\": str(root / checklist_output_path) if ok else \\\"\\\",\\n        \\\"input_reports\\\": {\\n            \\\"d89_report_path\\\": str(root / d89_report_path),\\n            \\\"d89_statement_path\\\": str(root / d89_statement_path),\\n            \\\"d89_scope_path\\\": str(root / d89_scope_path),\\n        },\\n        \\\"plan\\\": plan if ok else {},\\n        \\\"apply_command_preview\\\": preview if ok else {},\\n        \\\"manual_review_checklist\\\": checklist if ok else {},\\n        \\\"guardrails\\\": {\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n            \\\"controlled_plan_only\\\": True,\\n            \\\"preview_only\\\": True,\\n            \\\"approval_for_real_apply\\\": False,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"plan_id\\\": plan_id,\\n            \\\"confirmation_id\\\": confirmation_id,\\n            \\\"request_id\\\": request_id,\\n            \\\"package_id\\\": package_id,\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"controlled_apply_plan_preview_created\\\": ok,\\n            \\\"manual_review_checklist_created\\\": ok,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D91 should request explicit apply-scope approval. Real apply remains blocked.\\\",\\n        },\\n    }\\n\\n    write_json(root / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(create_controlled_apply_plan(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.controlled_apply_plan import create_controlled_apply_plan\\n\\n\\nclass TestD90ControlledApplyPlan(unittest.TestCase):\\n    def make_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n\\n        (root / \\\"reports/d89_final_human_confirmation.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"FINAL_HUMAN_CONFIRMATION_READY\\\",\\n                    \\\"confirmation_id\\\": \\\"d89-test-confirmation\\\",\\n                    \\\"evidence\\\": {\\n                        \\\"request_id\\\": \\\"d88-test-request\\\",\\n                        \\\"capsule_id\\\": \\\"d87-test-capsule\\\",\\n                        \\\"package_id\\\": \\\"d85-test-package\\\",\\n                        \\\"review_id\\\": \\\"d84-test-review\\\",\\n                    },\\n                    \\\"guardrails\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                        \\\"final_human_confirmation_only\\\": True,\\n                        \\\"d90_planning_only\\\": True,\\n                        \\\"approval_for_real_apply\\\": False,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d89_human_confirmation_statement.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"confirmation_id\\\": \\\"d89-test-confirmation\\\",\\n                    \\\"confirmation_phrase\\\": \\\"CONFIRM_D89_FINAL_HUMAN_REVIEW_FOR_D90_PLANNING_ONLY\\\",\\n                    \\\"approved_next_gate\\\": \\\"D90_CONTROLLED_APPLY_PLAN\\\",\\n                    \\\"source_request_id\\\": \\\"d88-test-request\\\",\\n                    \\\"source_package_id\\\": \\\"d85-test-package\\\",\\n                    \\\"not_approved\\\": [\\n                        \\\"actual_apply\\\",\\n                        \\\"route_insert\\\",\\n                        \\\"protected_core_mutation\\\",\\n                        \\\"canonical_memory_overwrite\\\",\\n                        \\\"external_ai_network_call\\\",\\n                        \\\"git_commit_or_push_by_ai\\\",\\n                    ],\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d89_d90_planning_scope.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"next_gate\\\": \\\"D90_CONTROLLED_APPLY_PLAN\\\",\\n                    \\\"d90_allowed_to_create\\\": [\\n                        \\\"controlled_apply_plan_json\\\",\\n                        \\\"explicit_scope_diff_summary\\\",\\n                        \\\"pre_apply_command_preview\\\",\\n                        \\\"manual_review_checklist\\\",\\n                    ],\\n                    \\\"d90_must_not_execute\\\": [\\n                        \\\"actual_apply\\\",\\n                        \\\"route_insert\\\",\\n                        \\\"protected_core_mutation\\\",\\n                        \\\"canonical_memory_overwrite\\\",\\n                        \\\"external_ai_network_call\\\",\\n                        \\\"git_commit_or_push_by_ai\\\",\\n                    ],\\n                    \\\"apply_allowed_after_d89\\\": False,\\n                    \\\"route_insert_allowed_after_d89\\\": False,\\n                    \\\"protected_core_mutation_allowed_after_d89\\\": False,\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        return td, root\\n\\n    def test_creates_controlled_apply_plan_preview_only(self):\\n        td, root = self.make_root()\\n        try:\\n            report = create_controlled_apply_plan(root=root)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"CONTROLLED_APPLY_PLAN_PREVIEW_READY\\\")\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"controlled_plan_only\\\"])\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"preview_only\\\"])\\n            self.assertFalse(report[\\\"guardrails\\\"][\\\"approval_for_real_apply\\\"])\\n            self.assertFalse(report[\\\"plan\\\"][\\\"plan_summary\\\"][\\\"real_apply_allowed\\\"])\\n            self.assertEqual(report[\\\"plan\\\"][\\\"required_next_gate\\\"], \\\"D91_EXPLICIT_APPLY_SCOPE_APPROVAL\\\")\\n            self.assertTrue((root / \\\"reports/d90_controlled_apply_plan.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d90_apply_command_preview.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d90_manual_review_checklist.json\\\").exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d89(self):\\n        td, root = self.make_root()\\n        try:\\n            (root / \\\"reports/d89_final_human_confirmation.json\\\").unlink()\\n            report = create_controlled_apply_plan(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"CONTROLLED_APPLY_PLAN_PREVIEW_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_if_d89_approves_real_apply(self):\\n        td, root = self.make_root()\\n        try:\\n            p = root / \\\"reports/d89_final_human_confirmation.json\\\"\\n            data = json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n            data[\\\"guardrails\\\"][\\\"approval_for_real_apply\\\"] = True\\n            p.write_text(json.dumps(data), encoding=\\\"utf-8\\\")\\n\\n            report = create_controlled_apply_plan(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"CONTROLLED_APPLY_PLAN_PREVIEW_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


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

print("D90 CONTROLLED APPLY PLAN BOOT: repo =", ROOT)

Path("runtime_experimental/controlled_apply_plan.py").write_text(MODULE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/controlled_apply_plan.py")

Path("tests/test_d90_controlled_apply_plan.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d90_controlled_apply_plan.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/controlled_apply_plan.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d90_controlled_apply_plan", "-v"], check=True)

print("\n== run D90 controlled apply plan ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.controlled_apply_plan import create_controlled_apply_plan\n"
        "r=create_controlled_apply_plan()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d90_controlled_apply_plan.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== preview ==")
pp = Path("reports/d90_apply_command_preview.json")
if pp.exists():
    data = json.loads(pp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("PREVIEW_ONLY:", data.get("preview_only"))
    print("COMMANDS_DOCUMENTATION_ONLY:", data.get("commands_are_documentation_only"))

print("\n== checklist ==")
cp = Path("reports/d90_manual_review_checklist.json")
if cp.exists():
    data = json.loads(cp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("HUMAN_REVIEW_REQUIRED:", data.get("human_review_required"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/controlled_apply_plan.py",
    "tests/test_d90_controlled_apply_plan.py",
    "reports/d90_controlled_apply_plan.json",
    "reports/d90_apply_command_preview.json",
    "reports/d90_manual_review_checklist.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D90_CONTROLLED_APPLY_PLAN_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D90 controlled apply plan preview"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D90 controlled apply plan changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD90 CONTROLLED APPLY PLAN BOOT DONE")
