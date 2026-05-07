#!/usr/bin/env python3
# D91_EXPLICIT_APPLY_SCOPE_APPROVAL_BOOT.py
#
# Adds D91 Explicit Apply Scope Approval to GitCube OS.
#
# Run from repo root:
#     python D91_EXPLICIT_APPLY_SCOPE_APPROVAL_BOOT.py
#
# Creates:
# - runtime_experimental/explicit_apply_scope_approval.py
# - tests/test_d91_explicit_apply_scope_approval.py
# - reports/d91_explicit_apply_scope_approval.json
# - reports/d91_apply_scope_request.json
# - reports/d91_apply_still_blocked.json
#
# D91 does NOT call an external AI API.
# D91 does NOT use network access.
# D91 does NOT execute raw code from AI.
# D91 does NOT run shell commands from AI.
# D91 does NOT patch task_dispatcher.py.
# D91 does NOT mutate protected core.
# D91 does NOT overwrite canonical memory.
# D91 does NOT insert a real route.
# D91 does NOT apply changes.
# D91 does NOT approve real apply.
#
# D91 approves only D92 guarded apply dry-run package generation.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_CODE = json.loads("\"from __future__ import annotations\\n\\nimport hashlib\\nimport json\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nD90_REPORT = \\\"reports/d90_controlled_apply_plan.json\\\"\\nD90_PREVIEW = \\\"reports/d90_apply_command_preview.json\\\"\\nD90_CHECKLIST = \\\"reports/d90_manual_review_checklist.json\\\"\\n\\nOUT = \\\"reports/d91_explicit_apply_scope_approval.json\\\"\\nSCOPE_REQUEST_OUT = \\\"reports/d91_apply_scope_request.json\\\"\\nSTILL_BLOCKED_OUT = \\\"reports/d91_apply_still_blocked.json\\\"\\n\\n\\nREQUIRED_D90_DECISION = \\\"CONTROLLED_APPLY_PLAN_PREVIEW_READY\\\"\\nREQUIRED_NEXT_GATE = \\\"D91_EXPLICIT_APPLY_SCOPE_APPROVAL\\\"\\nAPPROVAL_PHRASE = \\\"APPROVE_D91_SCOPE_FOR_D92_GUARDED_APPLY_DRY_RUN_ONLY\\\"\\n\\nHARD_FALSE_FLAGS = [\\n    \\\"external_ai_called\\\",\\n    \\\"network_accessed\\\",\\n    \\\"runtime_code_mutated\\\",\\n    \\\"protected_core_mutated\\\",\\n    \\\"canonical_memory_mutated\\\",\\n    \\\"actual_apply_executed\\\",\\n    \\\"route_inserted\\\",\\n    \\\"git_commit_by_ai\\\",\\n]\\n\\nFORBIDDEN_REAL_ACTIONS = [\\n    \\\"actual_apply\\\",\\n    \\\"route_insert\\\",\\n    \\\"protected_core_mutation\\\",\\n    \\\"canonical_memory_overwrite\\\",\\n    \\\"external_ai_network_call\\\",\\n    \\\"git_commit_or_push_by_ai\\\",\\n]\\n\\n\\ndef now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef sha256_json(data: Dict[str, Any]) -> str:\\n    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode(\\\"utf-8\\\")).hexdigest()\\n\\n\\ndef validate_false_flags(name: str, data: Dict[str, Any], errors: List[str]) -> None:\\n    for key in HARD_FALSE_FLAGS:\\n        if data.get(key) is not False:\\n            errors.append(f\\\"{name} flag {key} is not false\\\")\\n\\n\\ndef validate_d90(\\n    d90: Dict[str, Any],\\n    preview: Dict[str, Any],\\n    checklist: Dict[str, Any],\\n    errors: List[str],\\n) -> None:\\n    if not d90:\\n        errors.append(\\\"D90 controlled apply plan report missing or unreadable\\\")\\n        return\\n\\n    if d90.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D90 ok flag is not true\\\")\\n    if d90.get(\\\"decision\\\") != REQUIRED_D90_DECISION:\\n        errors.append(f\\\"D90 decision invalid: {d90.get('decision')}\\\")\\n\\n    guard = d90.get(\\\"guardrails\\\") if isinstance(d90.get(\\\"guardrails\\\"), dict) else {}\\n    validate_false_flags(\\\"D90 guardrail\\\", guard, errors)\\n\\n    if guard.get(\\\"controlled_plan_only\\\") is not True:\\n        errors.append(\\\"D90 controlled_plan_only is not true\\\")\\n    if guard.get(\\\"preview_only\\\") is not True:\\n        errors.append(\\\"D90 preview_only is not true\\\")\\n    if guard.get(\\\"approval_for_real_apply\\\") is not False:\\n        errors.append(\\\"D90 approval_for_real_apply is not false\\\")\\n\\n    plan = d90.get(\\\"plan\\\") if isinstance(d90.get(\\\"plan\\\"), dict) else {}\\n    if not plan:\\n        errors.append(\\\"D90 embedded plan missing\\\")\\n    else:\\n        if plan.get(\\\"mode\\\") != \\\"PLAN_PREVIEW_ONLY\\\":\\n            errors.append(f\\\"D90 plan mode invalid: {plan.get('mode')}\\\")\\n        if plan.get(\\\"required_next_gate\\\") != REQUIRED_NEXT_GATE:\\n            errors.append(f\\\"D90 required_next_gate invalid: {plan.get('required_next_gate')}\\\")\\n\\n        summary = plan.get(\\\"plan_summary\\\") if isinstance(plan.get(\\\"plan_summary\\\"), dict) else {}\\n        for key in (\\n            \\\"real_apply_allowed\\\",\\n            \\\"route_insert_allowed\\\",\\n            \\\"protected_core_mutation_allowed\\\",\\n            \\\"ai_git_action_allowed\\\",\\n        ):\\n            if summary.get(key) is not False:\\n                errors.append(f\\\"D90 plan_summary {key} is not false\\\")\\n\\n    if not preview:\\n        errors.append(\\\"D90 command preview missing or unreadable\\\")\\n    else:\\n        if preview.get(\\\"ok\\\") is not True:\\n            errors.append(\\\"D90 preview ok flag is not true\\\")\\n        if preview.get(\\\"preview_only\\\") is not True:\\n            errors.append(\\\"D90 preview_only is not true\\\")\\n        if preview.get(\\\"commands_are_documentation_only\\\") is not True:\\n            errors.append(\\\"D90 commands_are_documentation_only is not true\\\")\\n        if preview.get(\\\"commands_must_not_be_executed_by_ai\\\") is not True:\\n            errors.append(\\\"D90 commands_must_not_be_executed_by_ai is not true\\\")\\n\\n        blocked = preview.get(\\\"blocked_commands\\\")\\n        if not isinstance(blocked, list) or not blocked:\\n            errors.append(\\\"D90 blocked_commands missing\\\")\\n        else:\\n            for item in (\\\"git apply\\\", \\\"git commit\\\", \\\"git push\\\", \\\"route insert\\\"):\\n                if item not in blocked:\\n                    errors.append(f\\\"D90 blocked_commands missing item: {item}\\\")\\n\\n    if not checklist:\\n        errors.append(\\\"D90 manual review checklist missing or unreadable\\\")\\n    else:\\n        if checklist.get(\\\"ok\\\") is not True:\\n            errors.append(\\\"D90 checklist ok flag is not true\\\")\\n        if checklist.get(\\\"human_review_required\\\") is not True:\\n            errors.append(\\\"D90 checklist human_review_required is not true\\\")\\n\\n        must = checklist.get(\\\"must_remain_false\\\") if isinstance(checklist.get(\\\"must_remain_false\\\"), dict) else {}\\n        validate_false_flags(\\\"D90 checklist must_remain_false\\\", must, errors)\\n\\n\\ndef build_scope_request(approval_id: str, d90: Dict[str, Any], preview: Dict[str, Any]) -> Dict[str, Any]:\\n    summary = d90.get(\\\"summary\\\") if isinstance(d90.get(\\\"summary\\\"), dict) else {}\\n    plan = d90.get(\\\"plan\\\") if isinstance(d90.get(\\\"plan\\\"), dict) else {}\\n\\n    return {\\n        \\\"state\\\": \\\"D91_APPLY_SCOPE_REQUEST\\\",\\n        \\\"ok\\\": True,\\n        \\\"approval_id\\\": approval_id,\\n        \\\"created_at\\\": now(),\\n        \\\"approval_phrase\\\": APPROVAL_PHRASE,\\n        \\\"approval_mode\\\": \\\"SCOPE_APPROVAL_FOR_D92_GUARDED_APPLY_DRY_RUN_ONLY\\\",\\n        \\\"source_plan_id\\\": d90.get(\\\"plan_id\\\") or summary.get(\\\"plan_id\\\"),\\n        \\\"source_confirmation_id\\\": summary.get(\\\"confirmation_id\\\") or plan.get(\\\"source_confirmation_id\\\"),\\n        \\\"source_package_id\\\": summary.get(\\\"package_id\\\") or plan.get(\\\"source_package_id\\\"),\\n        \\\"scope_statement\\\": (\\n            \\\"D91 approves only the creation of a D92 guarded apply dry-run package. \\\"\\n            \\\"It does not approve real apply, route insertion, protected-core mutation, external AI calls, or AI git actions.\\\"\\n        ),\\n        \\\"approved_next_gate\\\": \\\"D92_GUARDED_APPLY_DRY_RUN_PACKAGE\\\",\\n        \\\"allowed_scope_for_d92\\\": [\\n            \\\"generate_guarded_apply_dry_run_package\\\",\\n            \\\"generate_apply_scope_diff_preview\\\",\\n            \\\"generate_pre_apply_recheck_commands\\\",\\n            \\\"generate_abort_conditions\\\",\\n        ],\\n        \\\"forbidden_real_actions\\\": FORBIDDEN_REAL_ACTIONS,\\n        \\\"source_preview_commands_are_documentation_only\\\": preview.get(\\\"commands_are_documentation_only\\\"),\\n    }\\n\\n\\ndef build_apply_still_blocked(approval_id: str) -> Dict[str, Any]:\\n    return {\\n        \\\"state\\\": \\\"D91_APPLY_STILL_BLOCKED\\\",\\n        \\\"ok\\\": True,\\n        \\\"approval_id\\\": approval_id,\\n        \\\"created_at\\\": now(),\\n        \\\"apply_allowed_now\\\": False,\\n        \\\"route_insert_allowed_now\\\": False,\\n        \\\"protected_core_mutation_allowed_now\\\": False,\\n        \\\"canonical_memory_mutation_allowed_now\\\": False,\\n        \\\"external_ai_call_allowed_now\\\": False,\\n        \\\"git_action_by_ai_allowed_now\\\": False,\\n        \\\"reason\\\": \\\"D91 approves D92 dry-run package generation only. Real apply still requires a later explicit execution gate.\\\",\\n        \\\"next_required_gate\\\": \\\"D92_GUARDED_APPLY_DRY_RUN_PACKAGE\\\",\\n    }\\n\\n\\ndef create_explicit_apply_scope_approval(\\n    root: str | Path = \\\".\\\",\\n    d90_report_path: str = D90_REPORT,\\n    d90_preview_path: str = D90_PREVIEW,\\n    d90_checklist_path: str = D90_CHECKLIST,\\n    output_path: str = OUT,\\n    scope_request_output_path: str = SCOPE_REQUEST_OUT,\\n    still_blocked_output_path: str = STILL_BLOCKED_OUT,\\n) -> Dict[str, Any]:\\n    root = Path(root).resolve()\\n\\n    d90 = read_json(root / d90_report_path, {}) or {}\\n    preview = read_json(root / d90_preview_path, {}) or {}\\n    checklist = read_json(root / d90_checklist_path, {}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    validate_d90(d90, preview, checklist, errors)\\n\\n    plan_id = str(d90.get(\\\"plan_id\\\") or (d90.get(\\\"summary\\\") or {}).get(\\\"plan_id\\\") or \\\"\\\")\\n    confirmation_id = str((d90.get(\\\"summary\\\") or {}).get(\\\"confirmation_id\\\") or \\\"\\\")\\n    package_id = str((d90.get(\\\"summary\\\") or {}).get(\\\"package_id\\\") or \\\"\\\")\\n\\n    approval_id = \\\"d91-\\\" + sha256_json(\\n        {\\n            \\\"plan_id\\\": plan_id,\\n            \\\"confirmation_id\\\": confirmation_id,\\n            \\\"package_id\\\": package_id,\\n            \\\"d90_decision\\\": d90.get(\\\"decision\\\"),\\n        }\\n    )[:16]\\n\\n    ok = not errors\\n    decision = \\\"EXPLICIT_APPLY_SCOPE_APPROVAL_READY\\\" if ok else \\\"EXPLICIT_APPLY_SCOPE_APPROVAL_BLOCKED\\\"\\n    result = \\\"D91_EXPLICIT_APPLY_SCOPE_APPROVAL_CREATED\\\" if ok else \\\"D91_EXPLICIT_APPLY_SCOPE_APPROVAL_BLOCKED\\\"\\n\\n    scope_request = build_scope_request(approval_id, d90, preview)\\n    still_blocked = build_apply_still_blocked(approval_id)\\n\\n    if ok:\\n        write_json(root / scope_request_output_path, scope_request)\\n        write_json(root / still_blocked_output_path, still_blocked)\\n\\n    report = {\\n        \\\"state\\\": \\\"D91_EXPLICIT_APPLY_SCOPE_APPROVAL\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_EXPLICIT_APPLY_SCOPE_APPROVAL\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": now(),\\n        \\\"approval_id\\\": approval_id,\\n        \\\"scope_request_path\\\": str(root / scope_request_output_path) if ok else \\\"\\\",\\n        \\\"apply_still_blocked_path\\\": str(root / still_blocked_output_path) if ok else \\\"\\\",\\n        \\\"input_reports\\\": {\\n            \\\"d90_report_path\\\": str(root / d90_report_path),\\n            \\\"d90_preview_path\\\": str(root / d90_preview_path),\\n            \\\"d90_checklist_path\\\": str(root / d90_checklist_path),\\n        },\\n        \\\"evidence\\\": {\\n            \\\"plan_id\\\": plan_id,\\n            \\\"confirmation_id\\\": confirmation_id,\\n            \\\"package_id\\\": package_id,\\n            \\\"d90_decision\\\": d90.get(\\\"decision\\\"),\\n            \\\"d90_required_next_gate\\\": (d90.get(\\\"plan\\\") or {}).get(\\\"required_next_gate\\\") if isinstance(d90.get(\\\"plan\\\"), dict) else \\\"\\\",\\n            \\\"apply_allowed_now\\\": False,\\n        },\\n        \\\"scope_request\\\": scope_request if ok else {},\\n        \\\"apply_still_blocked\\\": still_blocked,\\n        \\\"guardrails\\\": {\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n            \\\"scope_approval_only\\\": True,\\n            \\\"d92_dry_run_only\\\": True,\\n            \\\"approval_for_real_apply\\\": False,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"approval_id\\\": approval_id,\\n            \\\"plan_id\\\": plan_id,\\n            \\\"confirmation_id\\\": confirmation_id,\\n            \\\"package_id\\\": package_id,\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"explicit_apply_scope_approval_created\\\": ok,\\n            \\\"d92_dry_run_scope_created\\\": ok,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D92 can create a guarded apply dry-run package. Real apply remains blocked.\\\",\\n        },\\n    }\\n\\n    write_json(root / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(create_explicit_apply_scope_approval(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.explicit_apply_scope_approval import create_explicit_apply_scope_approval\\n\\n\\nclass TestD91ExplicitApplyScopeApproval(unittest.TestCase):\\n    def make_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n\\n        (root / \\\"reports/d90_controlled_apply_plan.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"CONTROLLED_APPLY_PLAN_PREVIEW_READY\\\",\\n                    \\\"plan_id\\\": \\\"d90-test-plan\\\",\\n                    \\\"summary\\\": {\\n                        \\\"plan_id\\\": \\\"d90-test-plan\\\",\\n                        \\\"confirmation_id\\\": \\\"d89-test-confirmation\\\",\\n                        \\\"package_id\\\": \\\"d85-test-package\\\",\\n                    },\\n                    \\\"plan\\\": {\\n                        \\\"mode\\\": \\\"PLAN_PREVIEW_ONLY\\\",\\n                        \\\"required_next_gate\\\": \\\"D91_EXPLICIT_APPLY_SCOPE_APPROVAL\\\",\\n                        \\\"plan_summary\\\": {\\n                            \\\"real_apply_allowed\\\": False,\\n                            \\\"route_insert_allowed\\\": False,\\n                            \\\"protected_core_mutation_allowed\\\": False,\\n                            \\\"ai_git_action_allowed\\\": False,\\n                        },\\n                    },\\n                    \\\"guardrails\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                        \\\"controlled_plan_only\\\": True,\\n                        \\\"preview_only\\\": True,\\n                        \\\"approval_for_real_apply\\\": False,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d90_apply_command_preview.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"preview_only\\\": True,\\n                    \\\"commands_are_documentation_only\\\": True,\\n                    \\\"commands_must_not_be_executed_by_ai\\\": True,\\n                    \\\"blocked_commands\\\": [\\n                        \\\"git apply\\\",\\n                        \\\"git commit\\\",\\n                        \\\"git push\\\",\\n                        \\\"route insert\\\",\\n                    ],\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d90_manual_review_checklist.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"human_review_required\\\": True,\\n                    \\\"must_remain_false\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        return td, root\\n\\n    def test_creates_scope_approval_for_d92_only(self):\\n        td, root = self.make_root()\\n        try:\\n            report = create_explicit_apply_scope_approval(root=root)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"EXPLICIT_APPLY_SCOPE_APPROVAL_READY\\\")\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"scope_approval_only\\\"])\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"d92_dry_run_only\\\"])\\n            self.assertFalse(report[\\\"guardrails\\\"][\\\"approval_for_real_apply\\\"])\\n            self.assertFalse(report[\\\"apply_still_blocked\\\"][\\\"apply_allowed_now\\\"])\\n            self.assertEqual(report[\\\"scope_request\\\"][\\\"approved_next_gate\\\"], \\\"D92_GUARDED_APPLY_DRY_RUN_PACKAGE\\\")\\n            self.assertTrue((root / \\\"reports/d91_explicit_apply_scope_approval.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d91_apply_scope_request.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d91_apply_still_blocked.json\\\").exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d90(self):\\n        td, root = self.make_root()\\n        try:\\n            (root / \\\"reports/d90_controlled_apply_plan.json\\\").unlink()\\n            report = create_explicit_apply_scope_approval(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"EXPLICIT_APPLY_SCOPE_APPROVAL_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_if_d90_approves_real_apply(self):\\n        td, root = self.make_root()\\n        try:\\n            p = root / \\\"reports/d90_controlled_apply_plan.json\\\"\\n            data = json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n            data[\\\"guardrails\\\"][\\\"approval_for_real_apply\\\"] = True\\n            p.write_text(json.dumps(data), encoding=\\\"utf-8\\\")\\n\\n            report = create_explicit_apply_scope_approval(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"EXPLICIT_APPLY_SCOPE_APPROVAL_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


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

print("D91 EXPLICIT APPLY SCOPE APPROVAL BOOT: repo =", ROOT)

Path("runtime_experimental/explicit_apply_scope_approval.py").write_text(MODULE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/explicit_apply_scope_approval.py")

Path("tests/test_d91_explicit_apply_scope_approval.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d91_explicit_apply_scope_approval.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/explicit_apply_scope_approval.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d91_explicit_apply_scope_approval", "-v"], check=True)

print("\n== run D91 explicit apply scope approval ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.explicit_apply_scope_approval import create_explicit_apply_scope_approval\n"
        "r=create_explicit_apply_scope_approval()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d91_explicit_apply_scope_approval.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== scope request preview ==")
sp = Path("reports/d91_apply_scope_request.json")
if sp.exists():
    data = json.loads(sp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("APPROVAL_ID:", data.get("approval_id"))
    print("APPROVED_NEXT_GATE:", data.get("approved_next_gate"))
    print("APPROVAL_MODE:", data.get("approval_mode"))

print("\n== still blocked preview ==")
bp = Path("reports/d91_apply_still_blocked.json")
if bp.exists():
    data = json.loads(bp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("APPLY_ALLOWED_NOW:", data.get("apply_allowed_now"))
    print("NEXT_REQUIRED_GATE:", data.get("next_required_gate"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/explicit_apply_scope_approval.py",
    "tests/test_d91_explicit_apply_scope_approval.py",
    "reports/d91_explicit_apply_scope_approval.json",
    "reports/d91_apply_scope_request.json",
    "reports/d91_apply_still_blocked.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D91_EXPLICIT_APPLY_SCOPE_APPROVAL_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D91 explicit apply scope approval"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D91 explicit apply scope approval changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD91 EXPLICIT APPLY SCOPE APPROVAL BOOT DONE")
