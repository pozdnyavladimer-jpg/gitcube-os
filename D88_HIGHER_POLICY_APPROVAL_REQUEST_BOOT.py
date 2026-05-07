#!/usr/bin/env python3
# D88_HIGHER_POLICY_APPROVAL_REQUEST_BOOT.py
#
# Adds D88 Higher Policy Approval Request to GitCube OS.
#
# Run from repo root:
#     python D88_HIGHER_POLICY_APPROVAL_REQUEST_BOOT.py
#
# Creates:
# - runtime_experimental/higher_policy_approval_request.py
# - tests/test_d88_higher_policy_approval_request.py
# - reports/d88_higher_policy_approval_request.json
# - reports/d88_higher_policy_review_packet.json
# - reports/d88_apply_still_blocked.json
#
# D88 does NOT call an external AI API.
# D88 does NOT use network access.
# D88 does NOT execute raw code from AI.
# D88 does NOT run shell commands from AI.
# D88 does NOT patch task_dispatcher.py.
# D88 does NOT mutate protected core.
# D88 does NOT overwrite canonical memory.
# D88 does NOT insert a real route.
# D88 does NOT apply changes.
# D88 does NOT grant approval.
#
# D88 only creates a higher-policy review request. Real apply remains blocked.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_CODE = json.loads("\"from __future__ import annotations\\n\\nimport hashlib\\nimport json\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nD87_REPORT = \\\"reports/d87_final_pre_apply_safety_capsule.json\\\"\\nD87_CAPSULE = \\\"reports/d87_pre_apply_safety_capsule.json\\\"\\nD87_BLOCKERS = \\\"reports/d87_apply_blockers.json\\\"\\n\\nOUT = \\\"reports/d88_higher_policy_approval_request.json\\\"\\nPACKET_OUT = \\\"reports/d88_higher_policy_review_packet.json\\\"\\nBLOCKERS_OUT = \\\"reports/d88_apply_still_blocked.json\\\"\\n\\n\\nREQUIRED_D87_DECISION = \\\"FINAL_PRE_APPLY_SAFETY_CAPSULE_READY\\\"\\nREQUIRED_NEXT_GATE = \\\"D88_HIGHER_POLICY_APPROVAL_REQUEST\\\"\\n\\nREVIEW_PHRASE = \\\"REVIEW_D88_HIGHER_POLICY_REQUEST_ONLY\\\"\\n\\nHARD_FALSE_FLAGS = [\\n    \\\"external_ai_called\\\",\\n    \\\"network_accessed\\\",\\n    \\\"runtime_code_mutated\\\",\\n    \\\"protected_core_mutated\\\",\\n    \\\"canonical_memory_mutated\\\",\\n    \\\"actual_apply_executed\\\",\\n    \\\"route_inserted\\\",\\n    \\\"git_commit_by_ai\\\",\\n]\\n\\n\\ndef now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef sha256_json(data: Dict[str, Any]) -> str:\\n    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode(\\\"utf-8\\\")).hexdigest()\\n\\n\\ndef validate_false_flags(name: str, data: Dict[str, Any], errors: List[str]) -> None:\\n    for key in HARD_FALSE_FLAGS:\\n        if data.get(key) is not False:\\n            errors.append(f\\\"{name} flag {key} is not false\\\")\\n\\n\\ndef validate_d87(\\n    d87: Dict[str, Any],\\n    capsule: Dict[str, Any],\\n    blockers: Dict[str, Any],\\n    errors: List[str],\\n) -> None:\\n    if not d87:\\n        errors.append(\\\"D87 final pre-apply safety capsule report missing or unreadable\\\")\\n        return\\n\\n    if d87.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D87 ok flag is not true\\\")\\n    if d87.get(\\\"decision\\\") != REQUIRED_D87_DECISION:\\n        errors.append(f\\\"D87 decision invalid: {d87.get('decision')}\\\")\\n\\n    guard = d87.get(\\\"guardrails\\\") if isinstance(d87.get(\\\"guardrails\\\"), dict) else {}\\n    validate_false_flags(\\\"D87 guardrail\\\", guard, errors)\\n\\n    if guard.get(\\\"final_capsule_only\\\") is not True:\\n        errors.append(\\\"D87 final_capsule_only is not true\\\")\\n    if guard.get(\\\"pre_apply_review_only\\\") is not True:\\n        errors.append(\\\"D87 pre_apply_review_only is not true\\\")\\n\\n    if not capsule:\\n        errors.append(\\\"D87 pre-apply safety capsule missing or unreadable\\\")\\n    else:\\n        if capsule.get(\\\"ok\\\") is not True:\\n            errors.append(\\\"D87 capsule ok flag is not true\\\")\\n        if capsule.get(\\\"next_gate\\\") != REQUIRED_NEXT_GATE:\\n            errors.append(f\\\"D87 capsule next_gate invalid: {capsule.get('next_gate')}\\\")\\n\\n        approval = capsule.get(\\\"approval_state\\\") if isinstance(capsule.get(\\\"approval_state\\\"), dict) else {}\\n        if approval.get(\\\"ready_for_higher_policy_review\\\") is not True:\\n            errors.append(\\\"D87 capsule is not ready for higher policy review\\\")\\n        for key in (\\n            \\\"ready_for_real_apply\\\",\\n            \\\"ready_for_route_insert\\\",\\n            \\\"ready_for_protected_core_mutation\\\",\\n        ):\\n            if approval.get(key) is not False:\\n                errors.append(f\\\"D87 capsule approval_state {key} is not false\\\")\\n\\n        hard = capsule.get(\\\"hard_no_mutation_flags\\\") if isinstance(capsule.get(\\\"hard_no_mutation_flags\\\"), dict) else {}\\n        validate_false_flags(\\\"D87 capsule hard_no_mutation\\\", hard, errors)\\n\\n    if not blockers:\\n        errors.append(\\\"D87 apply blockers missing or unreadable\\\")\\n    else:\\n        for key in (\\n            \\\"apply_allowed_now\\\",\\n            \\\"route_insert_allowed_now\\\",\\n            \\\"protected_core_mutation_allowed_now\\\",\\n            \\\"external_ai_call_allowed_now\\\",\\n            \\\"git_action_by_ai_allowed_now\\\",\\n        ):\\n            if blockers.get(key) is not False:\\n                errors.append(f\\\"D87 blocker {key} is not false\\\")\\n\\n        required = blockers.get(\\\"required_before_apply_can_be_discussed\\\")\\n        if not isinstance(required, list):\\n            errors.append(\\\"D87 blockers required_before_apply_can_be_discussed missing\\\")\\n        else:\\n            for item in (\\n                \\\"D88_HIGHER_POLICY_APPROVAL_REQUEST\\\",\\n                \\\"D89_FINAL_HUMAN_CONFIRMATION\\\",\\n                \\\"D66_RECHECK\\\",\\n                \\\"FULL_TEST_DISCOVERY\\\",\\n                \\\"ROLLBACK_MANIFEST_RECONFIRMATION\\\",\\n            ):\\n                if item not in required:\\n                    errors.append(f\\\"D87 blockers missing required item: {item}\\\")\\n\\n\\ndef build_review_packet(\\n    request_id: str,\\n    d87: Dict[str, Any],\\n    capsule: Dict[str, Any],\\n    blockers: Dict[str, Any],\\n) -> Dict[str, Any]:\\n    summary = d87.get(\\\"summary\\\") if isinstance(d87.get(\\\"summary\\\"), dict) else {}\\n    cap_chain = capsule.get(\\\"evidence_chain\\\") if isinstance(capsule.get(\\\"evidence_chain\\\"), dict) else {}\\n\\n    return {\\n        \\\"state\\\": \\\"D88_HIGHER_POLICY_REVIEW_PACKET\\\",\\n        \\\"ok\\\": True,\\n        \\\"request_id\\\": request_id,\\n        \\\"created_at\\\": now(),\\n        \\\"review_mode\\\": \\\"HIGHER_POLICY_REVIEW_REQUEST_ONLY\\\",\\n        \\\"review_phrase\\\": REVIEW_PHRASE,\\n        \\\"source_capsule_id\\\": capsule.get(\\\"capsule_id\\\") or summary.get(\\\"capsule_id\\\"),\\n        \\\"source_package_id\\\": capsule.get(\\\"package_id\\\") or summary.get(\\\"package_id\\\"),\\n        \\\"source_review_id\\\": capsule.get(\\\"review_id\\\") or summary.get(\\\"review_id\\\"),\\n        \\\"evidence_chain\\\": {\\n            \\\"d87_decision\\\": d87.get(\\\"decision\\\"),\\n            \\\"d85_decision\\\": cap_chain.get(\\\"d85_decision\\\"),\\n            \\\"d86_decision\\\": cap_chain.get(\\\"d86_decision\\\"),\\n            \\\"d86_commands_failed_count\\\": cap_chain.get(\\\"d86_commands_failed_count\\\"),\\n            \\\"rollback_manifest_present\\\": cap_chain.get(\\\"rollback_manifest_present\\\"),\\n            \\\"regression_checklist_present\\\": cap_chain.get(\\\"regression_checklist_present\\\"),\\n        },\\n        \\\"policy_question\\\": \\\"May this reviewed sandbox-only candidate move to D89 final human confirmation planning?\\\",\\n        \\\"policy_answer_now\\\": \\\"NOT_APPROVED_YET\\\",\\n        \\\"allowed_next_gate_if_reviewed\\\": \\\"D89_FINAL_HUMAN_CONFIRMATION\\\",\\n        \\\"blocked_now\\\": blockers.get(\\\"hard_blockers\\\", []),\\n        \\\"required_before_any_real_apply\\\": [\\n            \\\"D89_FINAL_HUMAN_CONFIRMATION\\\",\\n            \\\"D66_RECHECK\\\",\\n            \\\"FULL_TEST_DISCOVERY\\\",\\n            \\\"ROLLBACK_MANIFEST_RECONFIRMATION\\\",\\n            \\\"EXPLICIT_APPLY_SCOPE_APPROVAL\\\",\\n        ],\\n        \\\"not_allowed\\\": [\\n            \\\"actual_apply\\\",\\n            \\\"route_insert\\\",\\n            \\\"protected_core_mutation\\\",\\n            \\\"canonical_memory_overwrite\\\",\\n            \\\"external_ai_network_call\\\",\\n            \\\"git_commit_or_push_by_ai\\\",\\n        ],\\n    }\\n\\n\\ndef build_apply_still_blocked(request_id: str) -> Dict[str, Any]:\\n    return {\\n        \\\"state\\\": \\\"D88_APPLY_STILL_BLOCKED\\\",\\n        \\\"ok\\\": True,\\n        \\\"request_id\\\": request_id,\\n        \\\"created_at\\\": now(),\\n        \\\"apply_allowed_now\\\": False,\\n        \\\"route_insert_allowed_now\\\": False,\\n        \\\"protected_core_mutation_allowed_now\\\": False,\\n        \\\"canonical_memory_mutation_allowed_now\\\": False,\\n        \\\"external_ai_call_allowed_now\\\": False,\\n        \\\"git_action_by_ai_allowed_now\\\": False,\\n        \\\"reason\\\": \\\"D88 creates a higher-policy review request only. It does not grant apply permission.\\\",\\n        \\\"next_required_gate\\\": \\\"D89_FINAL_HUMAN_CONFIRMATION\\\",\\n    }\\n\\n\\ndef create_higher_policy_approval_request(\\n    root: str | Path = \\\".\\\",\\n    d87_report_path: str = D87_REPORT,\\n    d87_capsule_path: str = D87_CAPSULE,\\n    d87_blockers_path: str = D87_BLOCKERS,\\n    output_path: str = OUT,\\n    packet_output_path: str = PACKET_OUT,\\n    blockers_output_path: str = BLOCKERS_OUT,\\n) -> Dict[str, Any]:\\n    root = Path(root).resolve()\\n\\n    d87 = read_json(root / d87_report_path, {}) or {}\\n    capsule = read_json(root / d87_capsule_path, {}) or {}\\n    blockers = read_json(root / d87_blockers_path, {}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    validate_d87(d87, capsule, blockers, errors)\\n\\n    capsule_id = str(capsule.get(\\\"capsule_id\\\") or (d87.get(\\\"summary\\\") or {}).get(\\\"capsule_id\\\") or \\\"\\\")\\n    package_id = str(capsule.get(\\\"package_id\\\") or (d87.get(\\\"summary\\\") or {}).get(\\\"package_id\\\") or \\\"\\\")\\n    review_id = str(capsule.get(\\\"review_id\\\") or (d87.get(\\\"summary\\\") or {}).get(\\\"review_id\\\") or \\\"\\\")\\n\\n    request_id = \\\"d88-\\\" + sha256_json(\\n        {\\n            \\\"capsule_id\\\": capsule_id,\\n            \\\"package_id\\\": package_id,\\n            \\\"review_id\\\": review_id,\\n            \\\"d87_decision\\\": d87.get(\\\"decision\\\"),\\n        }\\n    )[:16]\\n\\n    ok = not errors\\n    decision = \\\"HIGHER_POLICY_APPROVAL_REQUEST_READY\\\" if ok else \\\"HIGHER_POLICY_APPROVAL_REQUEST_BLOCKED\\\"\\n    result = \\\"D88_HIGHER_POLICY_APPROVAL_REQUEST_CREATED\\\" if ok else \\\"D88_HIGHER_POLICY_APPROVAL_REQUEST_BLOCKED\\\"\\n\\n    review_packet = build_review_packet(request_id, d87, capsule, blockers)\\n    apply_still_blocked = build_apply_still_blocked(request_id)\\n\\n    if ok:\\n        write_json(root / packet_output_path, review_packet)\\n        write_json(root / blockers_output_path, apply_still_blocked)\\n\\n    report = {\\n        \\\"state\\\": \\\"D88_HIGHER_POLICY_APPROVAL_REQUEST\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_HIGHER_POLICY_APPROVAL_REQUEST\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": now(),\\n        \\\"request_id\\\": request_id,\\n        \\\"review_packet_path\\\": str(root / packet_output_path) if ok else \\\"\\\",\\n        \\\"apply_still_blocked_path\\\": str(root / blockers_output_path) if ok else \\\"\\\",\\n        \\\"input_reports\\\": {\\n            \\\"d87_report_path\\\": str(root / d87_report_path),\\n            \\\"d87_capsule_path\\\": str(root / d87_capsule_path),\\n            \\\"d87_blockers_path\\\": str(root / d87_blockers_path),\\n        },\\n        \\\"evidence\\\": {\\n            \\\"capsule_id\\\": capsule_id,\\n            \\\"package_id\\\": package_id,\\n            \\\"review_id\\\": review_id,\\n            \\\"d87_decision\\\": d87.get(\\\"decision\\\"),\\n            \\\"d87_next_gate\\\": capsule.get(\\\"next_gate\\\"),\\n            \\\"apply_allowed_now\\\": False,\\n        },\\n        \\\"review_packet\\\": review_packet if ok else {},\\n        \\\"apply_still_blocked\\\": apply_still_blocked,\\n        \\\"guardrails\\\": {\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n            \\\"higher_policy_request_only\\\": True,\\n            \\\"approval_not_granted\\\": True,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"request_id\\\": request_id,\\n            \\\"capsule_id\\\": capsule_id,\\n            \\\"package_id\\\": package_id,\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"higher_policy_request_created\\\": ok,\\n            \\\"review_packet_created\\\": ok,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D89 should create final human confirmation artifact. Real apply remains blocked.\\\",\\n        },\\n    }\\n\\n    write_json(root / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(create_higher_policy_approval_request(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.higher_policy_approval_request import create_higher_policy_approval_request\\n\\n\\nclass TestD88HigherPolicyApprovalRequest(unittest.TestCase):\\n    def make_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n\\n        (root / \\\"reports/d87_final_pre_apply_safety_capsule.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"FINAL_PRE_APPLY_SAFETY_CAPSULE_READY\\\",\\n                    \\\"summary\\\": {\\n                        \\\"capsule_id\\\": \\\"d87-test-capsule\\\",\\n                        \\\"package_id\\\": \\\"d85-test-package\\\",\\n                        \\\"review_id\\\": \\\"d84-test-review\\\",\\n                    },\\n                    \\\"guardrails\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                        \\\"final_capsule_only\\\": True,\\n                        \\\"pre_apply_review_only\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d87_pre_apply_safety_capsule.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"capsule_id\\\": \\\"d87-test-capsule\\\",\\n                    \\\"package_id\\\": \\\"d85-test-package\\\",\\n                    \\\"review_id\\\": \\\"d84-test-review\\\",\\n                    \\\"next_gate\\\": \\\"D88_HIGHER_POLICY_APPROVAL_REQUEST\\\",\\n                    \\\"evidence_chain\\\": {\\n                        \\\"d85_decision\\\": \\\"REGRESSION_ROLLBACK_EVIDENCE_READY\\\",\\n                        \\\"d86_decision\\\": \\\"LOCAL_REGRESSION_PASSED\\\",\\n                        \\\"d86_commands_failed_count\\\": 0,\\n                        \\\"rollback_manifest_present\\\": True,\\n                        \\\"regression_checklist_present\\\": True,\\n                    },\\n                    \\\"approval_state\\\": {\\n                        \\\"ready_for_higher_policy_review\\\": True,\\n                        \\\"ready_for_real_apply\\\": False,\\n                        \\\"ready_for_route_insert\\\": False,\\n                        \\\"ready_for_protected_core_mutation\\\": False,\\n                    },\\n                    \\\"hard_no_mutation_flags\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d87_apply_blockers.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"apply_allowed_now\\\": False,\\n                    \\\"route_insert_allowed_now\\\": False,\\n                    \\\"protected_core_mutation_allowed_now\\\": False,\\n                    \\\"external_ai_call_allowed_now\\\": False,\\n                    \\\"git_action_by_ai_allowed_now\\\": False,\\n                    \\\"hard_blockers\\\": [\\\"no explicit D88 higher policy approval\\\"],\\n                    \\\"required_before_apply_can_be_discussed\\\": [\\n                        \\\"D88_HIGHER_POLICY_APPROVAL_REQUEST\\\",\\n                        \\\"D89_FINAL_HUMAN_CONFIRMATION\\\",\\n                        \\\"D66_RECHECK\\\",\\n                        \\\"FULL_TEST_DISCOVERY\\\",\\n                        \\\"ROLLBACK_MANIFEST_RECONFIRMATION\\\",\\n                    ],\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        return td, root\\n\\n    def test_creates_higher_policy_request_only(self):\\n        td, root = self.make_root()\\n        try:\\n            report = create_higher_policy_approval_request(root=root)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"HIGHER_POLICY_APPROVAL_REQUEST_READY\\\")\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"higher_policy_request_only\\\"])\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"approval_not_granted\\\"])\\n            self.assertFalse(report[\\\"apply_still_blocked\\\"][\\\"apply_allowed_now\\\"])\\n            self.assertEqual(report[\\\"review_packet\\\"][\\\"allowed_next_gate_if_reviewed\\\"], \\\"D89_FINAL_HUMAN_CONFIRMATION\\\")\\n            self.assertTrue((root / \\\"reports/d88_higher_policy_approval_request.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d88_higher_policy_review_packet.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d88_apply_still_blocked.json\\\").exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d87(self):\\n        td, root = self.make_root()\\n        try:\\n            (root / \\\"reports/d87_final_pre_apply_safety_capsule.json\\\").unlink()\\n            report = create_higher_policy_approval_request(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"HIGHER_POLICY_APPROVAL_REQUEST_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_if_apply_allowed(self):\\n        td, root = self.make_root()\\n        try:\\n            p = root / \\\"reports/d87_apply_blockers.json\\\"\\n            data = json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n            data[\\\"apply_allowed_now\\\"] = True\\n            p.write_text(json.dumps(data), encoding=\\\"utf-8\\\")\\n\\n            report = create_higher_policy_approval_request(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"HIGHER_POLICY_APPROVAL_REQUEST_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


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

print("D88 HIGHER POLICY APPROVAL REQUEST BOOT: repo =", ROOT)

Path("runtime_experimental/higher_policy_approval_request.py").write_text(MODULE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/higher_policy_approval_request.py")

Path("tests/test_d88_higher_policy_approval_request.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d88_higher_policy_approval_request.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/higher_policy_approval_request.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d88_higher_policy_approval_request", "-v"], check=True)

print("\n== run D88 higher policy approval request ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.higher_policy_approval_request import create_higher_policy_approval_request\n"
        "r=create_higher_policy_approval_request()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d88_higher_policy_approval_request.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== review packet preview ==")
pp = Path("reports/d88_higher_policy_review_packet.json")
if pp.exists():
    data = json.loads(pp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("REQUEST_ID:", data.get("request_id"))
    print("REVIEW_MODE:", data.get("review_mode"))
    print("ALLOWED_NEXT_GATE:", data.get("allowed_next_gate_if_reviewed"))
    print("POLICY_ANSWER_NOW:", data.get("policy_answer_now"))

print("\n== blockers preview ==")
bp = Path("reports/d88_apply_still_blocked.json")
if bp.exists():
    data = json.loads(bp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("APPLY_ALLOWED_NOW:", data.get("apply_allowed_now"))
    print("NEXT_REQUIRED_GATE:", data.get("next_required_gate"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/higher_policy_approval_request.py",
    "tests/test_d88_higher_policy_approval_request.py",
    "reports/d88_higher_policy_approval_request.json",
    "reports/d88_higher_policy_review_packet.json",
    "reports/d88_apply_still_blocked.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D88_HIGHER_POLICY_APPROVAL_REQUEST_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D88 higher policy approval request"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D88 higher policy approval request changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD88 HIGHER POLICY APPROVAL REQUEST BOOT DONE")
