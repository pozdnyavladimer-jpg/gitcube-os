#!/usr/bin/env python3
# D82_HUMAN_SIGNED_INTENT_BOOT.py
#
# Adds D82 Human Approval / Signed Intent to GitCube OS.
#
# Run from repo root:
#     python D82_HUMAN_SIGNED_INTENT_BOOT.py
#
# Creates:
# - runtime_experimental/human_signed_intent.py
# - tests/test_d82_human_signed_intent.py
# - reports/d82_human_signed_intent.json
# - reports/d82_human_approval_request.json
#
# D82 does NOT call an external AI API.
# D82 does NOT use network access.
# D82 does NOT execute raw code.
# D82 does NOT run shell commands from AI.
# D82 does NOT patch task_dispatcher.py.
# D82 does NOT mutate protected core.
# D82 does NOT overwrite canonical memory.
# D82 does NOT insert a real route.
#
# D82 only signs human intent for JSON-only AI proposal to enter sandbox handoff.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_CODE = json.loads("\"from __future__ import annotations\\n\\nimport hashlib\\nimport json\\nimport os\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nD81_REPORT = \\\"reports/d81_ai_proposal_intake.json\\\"\\nD81_CONTRACT = \\\"reports/d81_ai_proposal_intake_contract.json\\\"\\nOUT = \\\"reports/d82_human_signed_intent.json\\\"\\nREQUEST_OUT = \\\"reports/d82_human_approval_request.json\\\"\\n\\n\\nAPPROVAL_PHRASE = \\\"APPROVE_D82_AI_PROPOSAL_INTAKE\\\"\\nDEFAULT_APPROVER = \\\"human_operator\\\"\\n\\n\\ndef now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef sha256_json(data: Dict[str, Any]) -> str:\\n    payload = json.dumps(data, ensure_ascii=False, sort_keys=True).encode(\\\"utf-8\\\")\\n    return hashlib.sha256(payload).hexdigest()\\n\\n\\ndef validate_d81(report: Dict[str, Any], contract: Dict[str, Any], errors: List[str]) -> None:\\n    if not report:\\n        errors.append(\\\"D81 report missing or unreadable\\\")\\n        return\\n\\n    if report.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D81 ok flag is not true\\\")\\n\\n    if report.get(\\\"decision\\\") != \\\"AI_PROPOSAL_INTAKE_READY\\\":\\n        errors.append(f\\\"D81 decision is not AI_PROPOSAL_INTAKE_READY: {report.get('decision')}\\\")\\n\\n    guard = report.get(\\\"guardrails\\\") if isinstance(report.get(\\\"guardrails\\\"), dict) else {}\\n    for key in (\\n        \\\"external_ai_called\\\",\\n        \\\"network_accessed\\\",\\n        \\\"runtime_code_mutated\\\",\\n        \\\"protected_core_mutated\\\",\\n        \\\"canonical_memory_mutated\\\",\\n        \\\"actual_apply_executed\\\",\\n        \\\"route_inserted\\\",\\n    ):\\n        if guard.get(key) is not False:\\n            errors.append(f\\\"D81 guardrail {key} is not false\\\")\\n\\n    if guard.get(\\\"proposal_intake_only\\\") is not True:\\n        errors.append(\\\"D81 proposal_intake_only is not true\\\")\\n    if guard.get(\\\"json_only\\\") is not True:\\n        errors.append(\\\"D81 json_only is not true\\\")\\n\\n    if not contract:\\n        errors.append(\\\"D81 intake contract missing or unreadable\\\")\\n        return\\n\\n    if contract.get(\\\"enabled\\\") is not True:\\n        errors.append(\\\"D81 intake contract enabled is not true\\\")\\n    if contract.get(\\\"mode\\\") != \\\"JSON_CONTRACT_ONLY\\\":\\n        errors.append(f\\\"D81 intake contract mode is not JSON_CONTRACT_ONLY: {contract.get('mode')}\\\")\\n    if contract.get(\\\"next_gate\\\") != \\\"D82_HUMAN_APPROVAL_SIGNED_INTENT\\\":\\n        errors.append(f\\\"D81 next gate is not D82_HUMAN_APPROVAL_SIGNED_INTENT: {contract.get('next_gate')}\\\")\\n\\n    req_guard = contract.get(\\\"required_guardrails\\\") if isinstance(contract.get(\\\"required_guardrails\\\"), dict) else {}\\n    for key in (\\n        \\\"external_ai_called\\\",\\n        \\\"network_accessed\\\",\\n        \\\"runtime_code_mutated\\\",\\n        \\\"protected_core_mutated\\\",\\n        \\\"canonical_memory_mutated\\\",\\n        \\\"actual_apply_executed\\\",\\n        \\\"route_inserted\\\",\\n    ):\\n        if req_guard.get(key) is not False:\\n            errors.append(f\\\"D81 required guardrail {key} is not false\\\")\\n    if req_guard.get(\\\"proposal_only\\\") is not True:\\n        errors.append(\\\"D81 required guardrail proposal_only is not true\\\")\\n    if req_guard.get(\\\"json_only\\\") is not True:\\n        errors.append(\\\"D81 required guardrail json_only is not true\\\")\\n\\n\\ndef create_signed_payload(\\n    d81_report: Dict[str, Any],\\n    d81_contract: Dict[str, Any],\\n    approver: str,\\n    approval_phrase: str,\\n) -> Dict[str, Any]:\\n    evidence = d81_report.get(\\\"evidence\\\") if isinstance(d81_report.get(\\\"evidence\\\"), dict) else {}\\n    summary = d81_report.get(\\\"summary\\\") if isinstance(d81_report.get(\\\"summary\\\"), dict) else {}\\n\\n    payload = {\\n        \\\"approval_scope\\\": \\\"ALLOW_AI_PROPOSAL_TO_SANDBOX_INTAKE_ONLY\\\",\\n        \\\"approval_phrase\\\": approval_phrase,\\n        \\\"approver\\\": approver,\\n        \\\"d81_intake_id\\\": d81_report.get(\\\"intake_id\\\") or summary.get(\\\"intake_id\\\"),\\n        \\\"boundary_id\\\": evidence.get(\\\"boundary_id\\\") or summary.get(\\\"boundary_id\\\"),\\n        \\\"proposal_id\\\": evidence.get(\\\"proposal_id\\\") or summary.get(\\\"proposal_id\\\"),\\n        \\\"intake_contract_mode\\\": d81_contract.get(\\\"mode\\\"),\\n        \\\"allowed_next_gate\\\": \\\"D83_SANDBOX_WRITER_HANDOFF\\\",\\n        \\\"blocked_actions\\\": [\\n            \\\"actual_apply\\\",\\n            \\\"route_insert\\\",\\n            \\\"protected_core_mutation\\\",\\n            \\\"canonical_memory_overwrite\\\",\\n            \\\"external_ai_network_call\\\",\\n            \\\"git_commit_or_push_by_ai\\\",\\n        ],\\n    }\\n    payload[\\\"signature_sha256\\\"] = sha256_json(payload)\\n    return payload\\n\\n\\ndef create_human_signed_intent(\\n    root: str | Path = \\\".\\\",\\n    d81_report_path: str = D81_REPORT,\\n    d81_contract_path: str = D81_CONTRACT,\\n    output_path: str = OUT,\\n    request_output_path: str = REQUEST_OUT,\\n    approver: str | None = None,\\n    approval_phrase: str | None = None,\\n) -> Dict[str, Any]:\\n    root = Path(root).resolve()\\n    d81 = read_json(root / d81_report_path, {}) or {}\\n    contract = read_json(root / d81_contract_path, {}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    validate_d81(d81, contract, errors)\\n\\n    approver = approver or os.environ.get(\\\"D82_APPROVER\\\", DEFAULT_APPROVER)\\n    phrase = approval_phrase or os.environ.get(\\\"D82_APPROVAL_PHRASE\\\", APPROVAL_PHRASE)\\n\\n    if phrase != APPROVAL_PHRASE:\\n        errors.append(\\\"approval phrase mismatch; expected APPROVE_D82_AI_PROPOSAL_INTAKE\\\")\\n\\n    signed_payload = create_signed_payload(d81, contract, approver, phrase)\\n    intent_id = \\\"d82-\\\" + sha256_json(\\n        {\\n            \\\"d81_intake_id\\\": signed_payload.get(\\\"d81_intake_id\\\"),\\n            \\\"proposal_id\\\": signed_payload.get(\\\"proposal_id\\\"),\\n            \\\"boundary_id\\\": signed_payload.get(\\\"boundary_id\\\"),\\n            \\\"signature\\\": signed_payload.get(\\\"signature_sha256\\\"),\\n        }\\n    )[:16]\\n\\n    ok = not errors\\n    decision = \\\"HUMAN_SIGNED_INTENT_READY\\\" if ok else \\\"HUMAN_SIGNED_INTENT_BLOCKED\\\"\\n    result = \\\"D82_HUMAN_SIGNED_INTENT_CREATED\\\" if ok else \\\"D82_HUMAN_SIGNED_INTENT_BLOCKED\\\"\\n\\n    approval_request = {\\n        \\\"state\\\": \\\"D82_HUMAN_APPROVAL_REQUEST\\\",\\n        \\\"ok\\\": ok,\\n        \\\"intent_id\\\": intent_id,\\n        \\\"required_phrase\\\": APPROVAL_PHRASE,\\n        \\\"approval_scope\\\": signed_payload[\\\"approval_scope\\\"],\\n        \\\"allowed_next_gate\\\": \\\"D83_SANDBOX_WRITER_HANDOFF\\\",\\n        \\\"human_statement\\\": \\\"I approve only structured AI proposal JSON to move into sandbox handoff. I do not approve protected-core mutation, route insertion, auto-apply, external AI calls, or git actions.\\\",\\n        \\\"blocked_actions\\\": signed_payload[\\\"blocked_actions\\\"],\\n    }\\n    write_json(root / request_output_path, approval_request)\\n\\n    report = {\\n        \\\"state\\\": \\\"D82_HUMAN_APPROVAL_SIGNED_INTENT\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_HUMAN_SIGNED_INTENT\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": now(),\\n        \\\"intent_id\\\": intent_id,\\n        \\\"approval_request_path\\\": str(root / request_output_path),\\n        \\\"signed_payload\\\": signed_payload if ok else {},\\n        \\\"input_reports\\\": {\\n            \\\"d81_report_path\\\": str(root / d81_report_path),\\n            \\\"d81_contract_path\\\": str(root / d81_contract_path),\\n        },\\n        \\\"evidence\\\": {\\n            \\\"d81_ok\\\": d81.get(\\\"ok\\\"),\\n            \\\"d81_decision\\\": d81.get(\\\"decision\\\"),\\n            \\\"d81_intake_id\\\": signed_payload.get(\\\"d81_intake_id\\\"),\\n            \\\"proposal_id\\\": signed_payload.get(\\\"proposal_id\\\"),\\n            \\\"boundary_id\\\": signed_payload.get(\\\"boundary_id\\\"),\\n            \\\"approver\\\": approver,\\n            \\\"signature_sha256\\\": signed_payload.get(\\\"signature_sha256\\\") if ok else \\\"\\\",\\n        },\\n        \\\"policy_checks\\\": {\\n            \\\"human_phrase_verified\\\": phrase == APPROVAL_PHRASE,\\n            \\\"d81_json_only\\\": contract.get(\\\"mode\\\") == \\\"JSON_CONTRACT_ONLY\\\",\\n            \\\"d81_next_gate_matches\\\": contract.get(\\\"next_gate\\\") == \\\"D82_HUMAN_APPROVAL_SIGNED_INTENT\\\",\\n            \\\"sandbox_only_next\\\": True,\\n            \\\"real_apply_allowed\\\": False,\\n            \\\"route_insert_allowed\\\": False,\\n            \\\"external_ai_call_allowed\\\": False,\\n        },\\n        \\\"guardrails\\\": {\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n            \\\"human_signed_intent_only\\\": True,\\n            \\\"sandbox_handoff_only\\\": True,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"intent_id\\\": intent_id,\\n            \\\"approver\\\": approver,\\n            \\\"d81_intake_id\\\": signed_payload.get(\\\"d81_intake_id\\\"),\\n            \\\"proposal_id\\\": signed_payload.get(\\\"proposal_id\\\"),\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"human_signed_intent_created\\\": ok,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D83 can hand off the approved JSON-only proposal to a sandbox writer, still with no protected-core mutation.\\\",\\n        },\\n    }\\n\\n    write_json(root / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(create_human_signed_intent(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.human_signed_intent import create_human_signed_intent\\n\\n\\nclass TestD82HumanSignedIntent(unittest.TestCase):\\n    def make_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n\\n        (root / \\\"reports/d81_ai_proposal_intake.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"AI_PROPOSAL_INTAKE_READY\\\",\\n                    \\\"intake_id\\\": \\\"d81-test-intake\\\",\\n                    \\\"evidence\\\": {\\n                        \\\"boundary_id\\\": \\\"d80-test-boundary\\\",\\n                        \\\"proposal_id\\\": \\\"d80-proposal-test\\\",\\n                    },\\n                    \\\"guardrails\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"proposal_intake_only\\\": True,\\n                        \\\"json_only\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d81_ai_proposal_intake_contract.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"enabled\\\": True,\\n                    \\\"mode\\\": \\\"JSON_CONTRACT_ONLY\\\",\\n                    \\\"next_gate\\\": \\\"D82_HUMAN_APPROVAL_SIGNED_INTENT\\\",\\n                    \\\"required_guardrails\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"proposal_only\\\": True,\\n                        \\\"json_only\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        return td, root\\n\\n    def test_creates_signed_intent(self):\\n        td, root = self.make_root()\\n        try:\\n            report = create_human_signed_intent(root=root)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"HUMAN_SIGNED_INTENT_READY\\\")\\n            self.assertEqual(report[\\\"signed_payload\\\"][\\\"approval_phrase\\\"], \\\"APPROVE_D82_AI_PROPOSAL_INTAKE\\\")\\n            self.assertFalse(report[\\\"guardrails\\\"][\\\"actual_apply_executed\\\"])\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"sandbox_handoff_only\\\"])\\n            self.assertTrue((root / \\\"reports/d82_human_signed_intent.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d82_human_approval_request.json\\\").exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d81(self):\\n        td, root = self.make_root()\\n        try:\\n            (root / \\\"reports/d81_ai_proposal_intake.json\\\").unlink()\\n            report = create_human_signed_intent(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"HUMAN_SIGNED_INTENT_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_bad_phrase(self):\\n        td, root = self.make_root()\\n        try:\\n            report = create_human_signed_intent(root=root, approval_phrase=\\\"WRONG\\\")\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"HUMAN_SIGNED_INTENT_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


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

print("D82 HUMAN SIGNED INTENT BOOT: repo =", ROOT)

Path("runtime_experimental/human_signed_intent.py").write_text(MODULE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/human_signed_intent.py")

Path("tests/test_d82_human_signed_intent.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d82_human_signed_intent.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/human_signed_intent.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d82_human_signed_intent", "-v"], check=True)

print("\n== run D82 human signed intent ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.human_signed_intent import create_human_signed_intent\n"
        "r=create_human_signed_intent()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d82_human_signed_intent.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== approval request preview ==")
ap = Path("reports/d82_human_approval_request.json")
if ap.exists():
    data = json.loads(ap.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("INTENT_ID:", data.get("intent_id"))
    print("REQUIRED_PHRASE:", data.get("required_phrase"))
    print("ALLOWED_NEXT_GATE:", data.get("allowed_next_gate"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/human_signed_intent.py",
    "tests/test_d82_human_signed_intent.py",
    "reports/d82_human_signed_intent.json",
    "reports/d82_human_approval_request.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D82_HUMAN_SIGNED_INTENT_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D82 human signed intent"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D82 human signed intent changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD82 HUMAN SIGNED INTENT BOOT DONE")
