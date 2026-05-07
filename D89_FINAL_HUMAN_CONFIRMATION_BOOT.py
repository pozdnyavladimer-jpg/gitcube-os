#!/usr/bin/env python3
# D89_FINAL_HUMAN_CONFIRMATION_BOOT.py
#
# Adds D89 Final Human Confirmation to GitCube OS.
#
# Run from repo root:
#     python D89_FINAL_HUMAN_CONFIRMATION_BOOT.py
#
# Creates:
# - runtime_experimental/final_human_confirmation.py
# - tests/test_d89_final_human_confirmation.py
# - reports/d89_final_human_confirmation.json
# - reports/d89_human_confirmation_statement.json
# - reports/d89_d90_planning_scope.json
#
# D89 does NOT call an external AI API.
# D89 does NOT use network access.
# D89 does NOT execute raw code from AI.
# D89 does NOT run shell commands from AI.
# D89 does NOT patch task_dispatcher.py.
# D89 does NOT mutate protected core.
# D89 does NOT overwrite canonical memory.
# D89 does NOT insert a real route.
# D89 does NOT apply changes.
# D89 does NOT approve real apply.
#
# D89 only confirms that D90 may create a controlled apply plan preview.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_CODE = json.loads("\"from __future__ import annotations\\n\\nimport hashlib\\nimport json\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nD88_REQUEST = \\\"reports/d88_higher_policy_approval_request.json\\\"\\nD88_PACKET = \\\"reports/d88_higher_policy_review_packet.json\\\"\\nD88_BLOCKED = \\\"reports/d88_apply_still_blocked.json\\\"\\n\\nOUT = \\\"reports/d89_final_human_confirmation.json\\\"\\nSTATEMENT_OUT = \\\"reports/d89_human_confirmation_statement.json\\\"\\nSCOPE_OUT = \\\"reports/d89_d90_planning_scope.json\\\"\\n\\n\\nREQUIRED_D88_DECISION = \\\"HIGHER_POLICY_APPROVAL_REQUEST_READY\\\"\\nREQUIRED_REVIEW_PHRASE = \\\"REVIEW_D88_HIGHER_POLICY_REQUEST_ONLY\\\"\\nCONFIRMATION_PHRASE = \\\"CONFIRM_D89_FINAL_HUMAN_REVIEW_FOR_D90_PLANNING_ONLY\\\"\\n\\nHARD_FALSE_FLAGS = [\\n    \\\"external_ai_called\\\",\\n    \\\"network_accessed\\\",\\n    \\\"runtime_code_mutated\\\",\\n    \\\"protected_core_mutated\\\",\\n    \\\"canonical_memory_mutated\\\",\\n    \\\"actual_apply_executed\\\",\\n    \\\"route_inserted\\\",\\n    \\\"git_commit_by_ai\\\",\\n]\\n\\n\\ndef now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef sha256_json(data: Dict[str, Any]) -> str:\\n    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode(\\\"utf-8\\\")).hexdigest()\\n\\n\\ndef validate_false_flags(name: str, data: Dict[str, Any], errors: List[str]) -> None:\\n    for key in HARD_FALSE_FLAGS:\\n        if data.get(key) is not False:\\n            errors.append(f\\\"{name} flag {key} is not false\\\")\\n\\n\\ndef validate_d88(\\n    d88: Dict[str, Any],\\n    packet: Dict[str, Any],\\n    blocked: Dict[str, Any],\\n    errors: List[str],\\n) -> None:\\n    if not d88:\\n        errors.append(\\\"D88 request missing or unreadable\\\")\\n        return\\n\\n    if d88.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D88 ok flag is not true\\\")\\n    if d88.get(\\\"decision\\\") != REQUIRED_D88_DECISION:\\n        errors.append(f\\\"D88 decision invalid: {d88.get('decision')}\\\")\\n\\n    guard = d88.get(\\\"guardrails\\\") if isinstance(d88.get(\\\"guardrails\\\"), dict) else {}\\n    validate_false_flags(\\\"D88 guardrail\\\", guard, errors)\\n\\n    if guard.get(\\\"higher_policy_request_only\\\") is not True:\\n        errors.append(\\\"D88 higher_policy_request_only is not true\\\")\\n    if guard.get(\\\"approval_not_granted\\\") is not True:\\n        errors.append(\\\"D88 approval_not_granted is not true\\\")\\n\\n    if not packet:\\n        errors.append(\\\"D88 higher policy review packet missing or unreadable\\\")\\n    else:\\n        if packet.get(\\\"ok\\\") is not True:\\n            errors.append(\\\"D88 review packet ok flag is not true\\\")\\n        if packet.get(\\\"review_phrase\\\") != REQUIRED_REVIEW_PHRASE:\\n            errors.append(f\\\"D88 review_phrase invalid: {packet.get('review_phrase')}\\\")\\n        if packet.get(\\\"allowed_next_gate_if_reviewed\\\") != \\\"D89_FINAL_HUMAN_CONFIRMATION\\\":\\n            errors.append(f\\\"D88 packet next gate invalid: {packet.get('allowed_next_gate_if_reviewed')}\\\")\\n        if packet.get(\\\"policy_answer_now\\\") != \\\"NOT_APPROVED_YET\\\":\\n            errors.append(\\\"D88 packet policy_answer_now must still be NOT_APPROVED_YET\\\")\\n\\n        for forbidden in (\\n            \\\"actual_apply\\\",\\n            \\\"route_insert\\\",\\n            \\\"protected_core_mutation\\\",\\n            \\\"canonical_memory_overwrite\\\",\\n            \\\"external_ai_network_call\\\",\\n            \\\"git_commit_or_push_by_ai\\\",\\n        ):\\n            if forbidden not in packet.get(\\\"not_allowed\\\", []):\\n                errors.append(f\\\"D88 packet missing not_allowed item: {forbidden}\\\")\\n\\n    if not blocked:\\n        errors.append(\\\"D88 apply-still-blocked report missing or unreadable\\\")\\n    else:\\n        for key in (\\n            \\\"apply_allowed_now\\\",\\n            \\\"route_insert_allowed_now\\\",\\n            \\\"protected_core_mutation_allowed_now\\\",\\n            \\\"canonical_memory_mutation_allowed_now\\\",\\n            \\\"external_ai_call_allowed_now\\\",\\n            \\\"git_action_by_ai_allowed_now\\\",\\n        ):\\n            if blocked.get(key) is not False:\\n                errors.append(f\\\"D88 blocked flag {key} is not false\\\")\\n        if blocked.get(\\\"next_required_gate\\\") != \\\"D89_FINAL_HUMAN_CONFIRMATION\\\":\\n            errors.append(f\\\"D88 blocked next_required_gate invalid: {blocked.get('next_required_gate')}\\\")\\n\\n\\ndef build_confirmation_statement(confirmation_id: str, d88: Dict[str, Any], packet: Dict[str, Any]) -> Dict[str, Any]:\\n    evidence = d88.get(\\\"evidence\\\") if isinstance(d88.get(\\\"evidence\\\"), dict) else {}\\n\\n    return {\\n        \\\"state\\\": \\\"D89_HUMAN_CONFIRMATION_STATEMENT\\\",\\n        \\\"ok\\\": True,\\n        \\\"confirmation_id\\\": confirmation_id,\\n        \\\"created_at\\\": now(),\\n        \\\"confirmation_phrase\\\": CONFIRMATION_PHRASE,\\n        \\\"human_confirmation_scope\\\": \\\"ALLOW_D90_CONTROLLED_APPLY_PLAN_GENERATION_ONLY\\\",\\n        \\\"human_statement\\\": (\\n            \\\"I confirm D88 higher-policy review packet may advance to D90 controlled apply planning only. \\\"\\n            \\\"This does not approve real apply, route insertion, protected-core mutation, external AI calls, or AI git actions.\\\"\\n        ),\\n        \\\"source_request_id\\\": d88.get(\\\"request_id\\\"),\\n        \\\"source_capsule_id\\\": evidence.get(\\\"capsule_id\\\") or packet.get(\\\"source_capsule_id\\\"),\\n        \\\"source_package_id\\\": evidence.get(\\\"package_id\\\") or packet.get(\\\"source_package_id\\\"),\\n        \\\"source_review_id\\\": evidence.get(\\\"review_id\\\") or packet.get(\\\"source_review_id\\\"),\\n        \\\"approved_next_gate\\\": \\\"D90_CONTROLLED_APPLY_PLAN\\\",\\n        \\\"not_approved\\\": [\\n            \\\"actual_apply\\\",\\n            \\\"route_insert\\\",\\n            \\\"protected_core_mutation\\\",\\n            \\\"canonical_memory_overwrite\\\",\\n            \\\"external_ai_network_call\\\",\\n            \\\"git_commit_or_push_by_ai\\\",\\n        ],\\n    }\\n\\n\\ndef build_d90_scope(confirmation_id: str, statement: Dict[str, Any]) -> Dict[str, Any]:\\n    return {\\n        \\\"state\\\": \\\"D89_D90_PLANNING_SCOPE\\\",\\n        \\\"ok\\\": True,\\n        \\\"confirmation_id\\\": confirmation_id,\\n        \\\"created_at\\\": now(),\\n        \\\"d90_allowed_to_create\\\": [\\n            \\\"controlled_apply_plan_json\\\",\\n            \\\"explicit_scope_diff_summary\\\",\\n            \\\"pre_apply_command_preview\\\",\\n            \\\"manual_review_checklist\\\",\\n        ],\\n        \\\"d90_must_not_execute\\\": [\\n            \\\"actual_apply\\\",\\n            \\\"route_insert\\\",\\n            \\\"protected_core_mutation\\\",\\n            \\\"canonical_memory_overwrite\\\",\\n            \\\"external_ai_network_call\\\",\\n            \\\"git_commit_or_push_by_ai\\\",\\n        ],\\n        \\\"d90_required_guards\\\": [\\n            \\\"D66_RECHECK\\\",\\n            \\\"FULL_TEST_DISCOVERY\\\",\\n            \\\"ROLLBACK_MANIFEST_RECONFIRMATION\\\",\\n            \\\"EXPLICIT_APPLY_SCOPE_APPROVAL\\\",\\n            \\\"NO_PROTECTED_CORE_MUTATION\\\",\\n        ],\\n        \\\"apply_allowed_after_d89\\\": False,\\n        \\\"route_insert_allowed_after_d89\\\": False,\\n        \\\"protected_core_mutation_allowed_after_d89\\\": False,\\n        \\\"next_gate\\\": \\\"D90_CONTROLLED_APPLY_PLAN\\\",\\n        \\\"source_confirmation_phrase\\\": statement.get(\\\"confirmation_phrase\\\"),\\n    }\\n\\n\\ndef create_final_human_confirmation(\\n    root: str | Path = \\\".\\\",\\n    d88_request_path: str = D88_REQUEST,\\n    d88_packet_path: str = D88_PACKET,\\n    d88_blocked_path: str = D88_BLOCKED,\\n    output_path: str = OUT,\\n    statement_output_path: str = STATEMENT_OUT,\\n    scope_output_path: str = SCOPE_OUT,\\n) -> Dict[str, Any]:\\n    root = Path(root).resolve()\\n\\n    d88 = read_json(root / d88_request_path, {}) or {}\\n    packet = read_json(root / d88_packet_path, {}) or {}\\n    blocked = read_json(root / d88_blocked_path, {}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    validate_d88(d88, packet, blocked, errors)\\n\\n    request_id = str(d88.get(\\\"request_id\\\") or packet.get(\\\"request_id\\\") or \\\"\\\")\\n    capsule_id = str((d88.get(\\\"evidence\\\") or {}).get(\\\"capsule_id\\\") or packet.get(\\\"source_capsule_id\\\") or \\\"\\\")\\n    package_id = str((d88.get(\\\"evidence\\\") or {}).get(\\\"package_id\\\") or packet.get(\\\"source_package_id\\\") or \\\"\\\")\\n    review_id = str((d88.get(\\\"evidence\\\") or {}).get(\\\"review_id\\\") or packet.get(\\\"source_review_id\\\") or \\\"\\\")\\n\\n    confirmation_id = \\\"d89-\\\" + sha256_json(\\n        {\\n            \\\"request_id\\\": request_id,\\n            \\\"capsule_id\\\": capsule_id,\\n            \\\"package_id\\\": package_id,\\n            \\\"review_id\\\": review_id,\\n            \\\"d88_decision\\\": d88.get(\\\"decision\\\"),\\n        }\\n    )[:16]\\n\\n    ok = not errors\\n    decision = \\\"FINAL_HUMAN_CONFIRMATION_READY\\\" if ok else \\\"FINAL_HUMAN_CONFIRMATION_BLOCKED\\\"\\n    result = \\\"D89_FINAL_HUMAN_CONFIRMATION_CREATED\\\" if ok else \\\"D89_FINAL_HUMAN_CONFIRMATION_BLOCKED\\\"\\n\\n    statement = build_confirmation_statement(confirmation_id, d88, packet)\\n    scope = build_d90_scope(confirmation_id, statement)\\n\\n    if ok:\\n        write_json(root / statement_output_path, statement)\\n        write_json(root / scope_output_path, scope)\\n\\n    report = {\\n        \\\"state\\\": \\\"D89_FINAL_HUMAN_CONFIRMATION\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_FINAL_HUMAN_CONFIRMATION\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": now(),\\n        \\\"confirmation_id\\\": confirmation_id,\\n        \\\"statement_path\\\": str(root / statement_output_path) if ok else \\\"\\\",\\n        \\\"d90_scope_path\\\": str(root / scope_output_path) if ok else \\\"\\\",\\n        \\\"input_reports\\\": {\\n            \\\"d88_request_path\\\": str(root / d88_request_path),\\n            \\\"d88_packet_path\\\": str(root / d88_packet_path),\\n            \\\"d88_blocked_path\\\": str(root / d88_blocked_path),\\n        },\\n        \\\"evidence\\\": {\\n            \\\"request_id\\\": request_id,\\n            \\\"capsule_id\\\": capsule_id,\\n            \\\"package_id\\\": package_id,\\n            \\\"review_id\\\": review_id,\\n            \\\"d88_decision\\\": d88.get(\\\"decision\\\"),\\n            \\\"d88_apply_allowed_now\\\": False,\\n        },\\n        \\\"confirmation_statement\\\": statement if ok else {},\\n        \\\"d90_scope\\\": scope if ok else {},\\n        \\\"guardrails\\\": {\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n            \\\"final_human_confirmation_only\\\": True,\\n            \\\"d90_planning_only\\\": True,\\n            \\\"approval_for_real_apply\\\": False,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"confirmation_id\\\": confirmation_id,\\n            \\\"request_id\\\": request_id,\\n            \\\"capsule_id\\\": capsule_id,\\n            \\\"package_id\\\": package_id,\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"final_human_confirmation_created\\\": ok,\\n            \\\"d90_planning_scope_created\\\": ok,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D90 can create a controlled apply plan preview. Real apply remains blocked until explicit apply-scope approval.\\\",\\n        },\\n    }\\n\\n    write_json(root / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(create_final_human_confirmation(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.final_human_confirmation import create_final_human_confirmation\\n\\n\\nclass TestD89FinalHumanConfirmation(unittest.TestCase):\\n    def make_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n\\n        (root / \\\"reports/d88_higher_policy_approval_request.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"HIGHER_POLICY_APPROVAL_REQUEST_READY\\\",\\n                    \\\"request_id\\\": \\\"d88-test-request\\\",\\n                    \\\"evidence\\\": {\\n                        \\\"capsule_id\\\": \\\"d87-test-capsule\\\",\\n                        \\\"package_id\\\": \\\"d85-test-package\\\",\\n                        \\\"review_id\\\": \\\"d84-test-review\\\",\\n                    },\\n                    \\\"guardrails\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                        \\\"higher_policy_request_only\\\": True,\\n                        \\\"approval_not_granted\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d88_higher_policy_review_packet.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"request_id\\\": \\\"d88-test-request\\\",\\n                    \\\"review_phrase\\\": \\\"REVIEW_D88_HIGHER_POLICY_REQUEST_ONLY\\\",\\n                    \\\"allowed_next_gate_if_reviewed\\\": \\\"D89_FINAL_HUMAN_CONFIRMATION\\\",\\n                    \\\"policy_answer_now\\\": \\\"NOT_APPROVED_YET\\\",\\n                    \\\"source_capsule_id\\\": \\\"d87-test-capsule\\\",\\n                    \\\"source_package_id\\\": \\\"d85-test-package\\\",\\n                    \\\"source_review_id\\\": \\\"d84-test-review\\\",\\n                    \\\"not_allowed\\\": [\\n                        \\\"actual_apply\\\",\\n                        \\\"route_insert\\\",\\n                        \\\"protected_core_mutation\\\",\\n                        \\\"canonical_memory_overwrite\\\",\\n                        \\\"external_ai_network_call\\\",\\n                        \\\"git_commit_or_push_by_ai\\\",\\n                    ],\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d88_apply_still_blocked.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"apply_allowed_now\\\": False,\\n                    \\\"route_insert_allowed_now\\\": False,\\n                    \\\"protected_core_mutation_allowed_now\\\": False,\\n                    \\\"canonical_memory_mutation_allowed_now\\\": False,\\n                    \\\"external_ai_call_allowed_now\\\": False,\\n                    \\\"git_action_by_ai_allowed_now\\\": False,\\n                    \\\"next_required_gate\\\": \\\"D89_FINAL_HUMAN_CONFIRMATION\\\",\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        return td, root\\n\\n    def test_creates_final_human_confirmation_only(self):\\n        td, root = self.make_root()\\n        try:\\n            report = create_final_human_confirmation(root=root)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"FINAL_HUMAN_CONFIRMATION_READY\\\")\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"final_human_confirmation_only\\\"])\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"d90_planning_only\\\"])\\n            self.assertFalse(report[\\\"guardrails\\\"][\\\"approval_for_real_apply\\\"])\\n            self.assertFalse(report[\\\"d90_scope\\\"][\\\"apply_allowed_after_d89\\\"])\\n            self.assertEqual(report[\\\"d90_scope\\\"][\\\"next_gate\\\"], \\\"D90_CONTROLLED_APPLY_PLAN\\\")\\n            self.assertTrue((root / \\\"reports/d89_final_human_confirmation.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d89_human_confirmation_statement.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d89_d90_planning_scope.json\\\").exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d88(self):\\n        td, root = self.make_root()\\n        try:\\n            (root / \\\"reports/d88_higher_policy_approval_request.json\\\").unlink()\\n            report = create_final_human_confirmation(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"FINAL_HUMAN_CONFIRMATION_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_if_d88_apply_allowed(self):\\n        td, root = self.make_root()\\n        try:\\n            p = root / \\\"reports/d88_apply_still_blocked.json\\\"\\n            data = json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n            data[\\\"apply_allowed_now\\\"] = True\\n            p.write_text(json.dumps(data), encoding=\\\"utf-8\\\")\\n\\n            report = create_final_human_confirmation(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"FINAL_HUMAN_CONFIRMATION_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


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

print("D89 FINAL HUMAN CONFIRMATION BOOT: repo =", ROOT)

Path("runtime_experimental/final_human_confirmation.py").write_text(MODULE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/final_human_confirmation.py")

Path("tests/test_d89_final_human_confirmation.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d89_final_human_confirmation.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/final_human_confirmation.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d89_final_human_confirmation", "-v"], check=True)

print("\n== run D89 final human confirmation ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.final_human_confirmation import create_final_human_confirmation\n"
        "r=create_final_human_confirmation()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d89_final_human_confirmation.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== statement preview ==")
sp = Path("reports/d89_human_confirmation_statement.json")
if sp.exists():
    data = json.loads(sp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("CONFIRMATION_ID:", data.get("confirmation_id"))
    print("CONFIRMATION_SCOPE:", data.get("human_confirmation_scope"))
    print("APPROVED_NEXT_GATE:", data.get("approved_next_gate"))

print("\n== D90 scope preview ==")
dp = Path("reports/d89_d90_planning_scope.json")
if dp.exists():
    data = json.loads(dp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("NEXT_GATE:", data.get("next_gate"))
    print("APPLY_ALLOWED_AFTER_D89:", data.get("apply_allowed_after_d89"))
    print("D90_ALLOWED_TO_CREATE:", data.get("d90_allowed_to_create"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/final_human_confirmation.py",
    "tests/test_d89_final_human_confirmation.py",
    "reports/d89_final_human_confirmation.json",
    "reports/d89_human_confirmation_statement.json",
    "reports/d89_d90_planning_scope.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D89_FINAL_HUMAN_CONFIRMATION_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D89 final human confirmation"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D89 final human confirmation changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD89 FINAL HUMAN CONFIRMATION BOOT DONE")
