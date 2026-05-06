#!/usr/bin/env python3
# D83_SANDBOX_WRITER_HANDOFF_BOOT.py
#
# Adds D83 Sandbox Writer Handoff to GitCube OS.
#
# Run from repo root:
#     python D83_SANDBOX_WRITER_HANDOFF_BOOT.py
#
# Creates:
# - runtime_experimental/sandbox_writer_handoff.py
# - tests/test_d83_sandbox_writer_handoff.py
# - reports/d83_sandbox_writer_handoff.json
# - reports/d83_sandbox_writer_handoff_manifest.json
# - runtime_experimental/ai_sandbox_inbox/<handoff_id>_sandbox_writer_input.json
#
# D83 does NOT call an external AI API.
# D83 does NOT use network access.
# D83 does NOT execute raw code.
# D83 does NOT run shell commands from AI.
# D83 does NOT patch task_dispatcher.py.
# D83 does NOT mutate protected core.
# D83 does NOT overwrite canonical memory.
# D83 does NOT insert a real route.
#
# D83 only hands signed JSON-only AI proposal into sandbox writer inbox.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_CODE = json.loads("\"from __future__ import annotations\\n\\nimport hashlib\\nimport json\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nD82_REPORT = \\\"reports/d82_human_signed_intent.json\\\"\\nD82_REQUEST = \\\"reports/d82_human_approval_request.json\\\"\\nD81_CONTRACT = \\\"reports/d81_ai_proposal_intake_contract.json\\\"\\nOUT = \\\"reports/d83_sandbox_writer_handoff.json\\\"\\nMANIFEST_OUT = \\\"reports/d83_sandbox_writer_handoff_manifest.json\\\"\\nINBOX_DIR = \\\"runtime_experimental/ai_sandbox_inbox\\\"\\n\\n\\ndef now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef safe_path(value: str) -> str:\\n    raw = str(value or \\\"\\\").strip().replace(\\\"\\\\\\\\\\\", \\\"/\\\").lstrip(\\\"/\\\")\\n    return \\\"/\\\".join(x for x in raw.split(\\\"/\\\") if x and x not in (\\\".\\\", \\\"..\\\"))\\n\\n\\ndef sha256_json(data: Dict[str, Any]) -> str:\\n    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode(\\\"utf-8\\\")).hexdigest()\\n\\n\\ndef verify_signed_payload(payload: Dict[str, Any]) -> bool:\\n    if not isinstance(payload, dict):\\n        return False\\n    signature = payload.get(\\\"signature_sha256\\\")\\n    if not signature:\\n        return False\\n    unsigned = dict(payload)\\n    unsigned.pop(\\\"signature_sha256\\\", None)\\n    return sha256_json(unsigned) == signature\\n\\n\\ndef validate_d82(d82: Dict[str, Any], request: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:\\n    if not d82:\\n        errors.append(\\\"D82 signed intent report missing or unreadable\\\")\\n        return {}\\n\\n    if d82.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D82 ok flag is not true\\\")\\n    if d82.get(\\\"decision\\\") != \\\"HUMAN_SIGNED_INTENT_READY\\\":\\n        errors.append(f\\\"D82 decision is not HUMAN_SIGNED_INTENT_READY: {d82.get('decision')}\\\")\\n\\n    payload = d82.get(\\\"signed_payload\\\") if isinstance(d82.get(\\\"signed_payload\\\"), dict) else {}\\n    if not payload:\\n        errors.append(\\\"D82 signed_payload missing or invalid\\\")\\n    elif not verify_signed_payload(payload):\\n        errors.append(\\\"D82 signed_payload signature invalid\\\")\\n\\n    if payload.get(\\\"approval_scope\\\") != \\\"ALLOW_AI_PROPOSAL_TO_SANDBOX_INTAKE_ONLY\\\":\\n        errors.append(f\\\"D82 approval_scope invalid: {payload.get('approval_scope')}\\\")\\n    if payload.get(\\\"allowed_next_gate\\\") != \\\"D83_SANDBOX_WRITER_HANDOFF\\\":\\n        errors.append(f\\\"D82 allowed_next_gate invalid: {payload.get('allowed_next_gate')}\\\")\\n\\n    blocked = payload.get(\\\"blocked_actions\\\")\\n    if not isinstance(blocked, list):\\n        errors.append(\\\"D82 blocked_actions missing or invalid\\\")\\n    else:\\n        for item in (\\n            \\\"actual_apply\\\",\\n            \\\"route_insert\\\",\\n            \\\"protected_core_mutation\\\",\\n            \\\"canonical_memory_overwrite\\\",\\n            \\\"external_ai_network_call\\\",\\n            \\\"git_commit_or_push_by_ai\\\",\\n        ):\\n            if item not in blocked:\\n                errors.append(f\\\"D82 missing blocked action: {item}\\\")\\n\\n    guard = d82.get(\\\"guardrails\\\") if isinstance(d82.get(\\\"guardrails\\\"), dict) else {}\\n    for key in (\\n        \\\"external_ai_called\\\",\\n        \\\"network_accessed\\\",\\n        \\\"runtime_code_mutated\\\",\\n        \\\"protected_core_mutated\\\",\\n        \\\"canonical_memory_mutated\\\",\\n        \\\"actual_apply_executed\\\",\\n        \\\"route_inserted\\\",\\n        \\\"git_commit_by_ai\\\",\\n    ):\\n        if guard.get(key) is not False:\\n            errors.append(f\\\"D82 guardrail {key} is not false\\\")\\n    if guard.get(\\\"human_signed_intent_only\\\") is not True:\\n        errors.append(\\\"D82 human_signed_intent_only is not true\\\")\\n    if guard.get(\\\"sandbox_handoff_only\\\") is not True:\\n        errors.append(\\\"D82 sandbox_handoff_only is not true\\\")\\n\\n    if not request:\\n        errors.append(\\\"D82 approval request missing or unreadable\\\")\\n    else:\\n        if request.get(\\\"ok\\\") is not True:\\n            errors.append(\\\"D82 approval request ok flag is not true\\\")\\n        if request.get(\\\"allowed_next_gate\\\") != \\\"D83_SANDBOX_WRITER_HANDOFF\\\":\\n            errors.append(\\\"D82 approval request allowed_next_gate is not D83_SANDBOX_WRITER_HANDOFF\\\")\\n        if request.get(\\\"intent_id\\\") != d82.get(\\\"intent_id\\\"):\\n            errors.append(\\\"D82 approval request intent_id does not match report intent_id\\\")\\n\\n    return payload\\n\\n\\ndef validate_d81_contract(contract: Dict[str, Any], errors: List[str]) -> None:\\n    if not contract:\\n        errors.append(\\\"D81 intake contract missing or unreadable\\\")\\n        return\\n\\n    if contract.get(\\\"enabled\\\") is not True:\\n        errors.append(\\\"D81 intake contract enabled is not true\\\")\\n    if contract.get(\\\"mode\\\") != \\\"JSON_CONTRACT_ONLY\\\":\\n        errors.append(f\\\"D81 intake contract mode is not JSON_CONTRACT_ONLY: {contract.get('mode')}\\\")\\n\\n    accepted = contract.get(\\\"accepted_input\\\") if isinstance(contract.get(\\\"accepted_input\\\"), dict) else {}\\n    allowed = accepted.get(\\\"candidate_files_prefixes_allowed\\\") if isinstance(accepted.get(\\\"candidate_files_prefixes_allowed\\\"), list) else []\\n    blocked = accepted.get(\\\"candidate_files_prefixes_blocked\\\") if isinstance(accepted.get(\\\"candidate_files_prefixes_blocked\\\"), list) else []\\n\\n    for prefix in (\\\"runtime_experimental/\\\", \\\"reports/\\\", \\\"tests/\\\"):\\n        if prefix not in allowed:\\n            errors.append(f\\\"D81 allowed prefix missing: {prefix}\\\")\\n    for prefix in (\\\"app/orchestration/\\\", \\\"core/\\\", \\\"runtime/\\\", \\\"bridges/\\\", \\\"memory/\\\"):\\n        if prefix not in blocked:\\n            errors.append(f\\\"D81 blocked prefix missing: {prefix}\\\")\\n\\n\\ndef create_sandbox_writer_handoff(\\n    root: str | Path = \\\".\\\",\\n    d82_report_path: str = D82_REPORT,\\n    d82_request_path: str = D82_REQUEST,\\n    d81_contract_path: str = D81_CONTRACT,\\n    output_path: str = OUT,\\n    manifest_output_path: str = MANIFEST_OUT,\\n    inbox_dir: str = INBOX_DIR,\\n) -> Dict[str, Any]:\\n    root = Path(root).resolve()\\n    d82 = read_json(root / d82_report_path, {}) or {}\\n    request = read_json(root / d82_request_path, {}) or {}\\n    d81_contract = read_json(root / d81_contract_path, {}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    payload = validate_d82(d82, request, errors)\\n    validate_d81_contract(d81_contract, errors)\\n\\n    intent_id = str(d82.get(\\\"intent_id\\\") or \\\"\\\")\\n    proposal_id = str(payload.get(\\\"proposal_id\\\") or \\\"\\\")\\n    boundary_id = str(payload.get(\\\"boundary_id\\\") or \\\"\\\")\\n    d81_intake_id = str(payload.get(\\\"d81_intake_id\\\") or \\\"\\\")\\n\\n    if not intent_id:\\n        errors.append(\\\"D82 intent_id missing\\\")\\n    if not proposal_id:\\n        errors.append(\\\"D82 proposal_id missing\\\")\\n    if not d81_intake_id:\\n        errors.append(\\\"D82 d81_intake_id missing\\\")\\n\\n    handoff_id = \\\"d83-\\\" + sha256_json(\\n        {\\n            \\\"intent_id\\\": intent_id,\\n            \\\"proposal_id\\\": proposal_id,\\n            \\\"boundary_id\\\": boundary_id,\\n            \\\"d81_intake_id\\\": d81_intake_id,\\n        }\\n    )[:16]\\n\\n    inbox_file_rel = safe_path(f\\\"{inbox_dir}/{handoff_id}_sandbox_writer_input.json\\\")\\n    inbox_file_abs = root / inbox_file_rel\\n\\n    ok = not errors\\n    decision = \\\"SANDBOX_WRITER_HANDOFF_READY\\\" if ok else \\\"SANDBOX_WRITER_HANDOFF_BLOCKED\\\"\\n    result = \\\"D83_SANDBOX_WRITER_HANDOFF_CREATED\\\" if ok else \\\"D83_SANDBOX_WRITER_HANDOFF_BLOCKED\\\"\\n\\n    handoff_payload = {\\n        \\\"state\\\": \\\"D83_SANDBOX_WRITER_INPUT\\\",\\n        \\\"ok\\\": ok,\\n        \\\"handoff_id\\\": handoff_id,\\n        \\\"mode\\\": \\\"SANDBOX_WRITER_INPUT_ONLY\\\",\\n        \\\"created_at\\\": now(),\\n        \\\"source\\\": {\\n            \\\"intent_id\\\": intent_id,\\n            \\\"proposal_id\\\": proposal_id,\\n            \\\"boundary_id\\\": boundary_id,\\n            \\\"d81_intake_id\\\": d81_intake_id,\\n        },\\n        \\\"allowed_writer_scope\\\": {\\n            \\\"write_prefixes\\\": [\\n                \\\"runtime_experimental/ai_sandbox_work/\\\",\\n                \\\"reports/\\\",\\n                \\\"tests/\\\",\\n            ],\\n            \\\"read_prefixes\\\": [\\n                \\\"reports/\\\",\\n                \\\"runtime_experimental/\\\",\\n                \\\"tests/\\\",\\n            ],\\n            \\\"blocked_prefixes\\\": [\\n                \\\"app/orchestration/\\\",\\n                \\\"core/\\\",\\n                \\\"runtime/\\\",\\n                \\\"bridges/\\\",\\n                \\\"memory/\\\",\\n            ],\\n        },\\n        \\\"required_before_any_apply\\\": [\\n            \\\"D84_SANDBOX_WRITER_OUTPUT_REVIEW\\\",\\n            \\\"D66_RECHECK\\\",\\n            \\\"UNIT_TESTS\\\",\\n            \\\"REGRESSION_TESTS\\\",\\n            \\\"ROLLBACK_MANIFEST\\\",\\n            \\\"HUMAN_OR_HIGHER_POLICY_APPROVAL\\\",\\n        ],\\n        \\\"forbidden_actions\\\": [\\n            \\\"direct_core_edit\\\",\\n            \\\"route_insert\\\",\\n            \\\"actual_apply\\\",\\n            \\\"external_ai_network_call\\\",\\n            \\\"git_commit_or_push_by_ai\\\",\\n            \\\"canonical_memory_overwrite\\\",\\n        ],\\n        \\\"guardrails\\\": {\\n            \\\"proposal_only\\\": True,\\n            \\\"sandbox_only\\\": True,\\n            \\\"actual_apply_allowed\\\": False,\\n            \\\"route_insert_allowed\\\": False,\\n            \\\"protected_core_mutation_allowed\\\": False,\\n            \\\"external_ai_call_allowed\\\": False,\\n            \\\"git_action_allowed\\\": False,\\n        },\\n    }\\n\\n    manifest = {\\n        \\\"state\\\": \\\"D83_SANDBOX_WRITER_HANDOFF_MANIFEST\\\",\\n        \\\"ok\\\": ok,\\n        \\\"handoff_id\\\": handoff_id,\\n        \\\"created_at\\\": now(),\\n        \\\"writer_input_path\\\": str(inbox_file_abs) if ok else \\\"\\\",\\n        \\\"source_reports\\\": [\\n            str(root / d82_report_path),\\n            str(root / d82_request_path),\\n            str(root / d81_contract_path),\\n        ],\\n        \\\"actual_files_created\\\": [inbox_file_rel] if ok else [],\\n        \\\"actual_files_mutated\\\": [],\\n        \\\"protected_core_touched\\\": False,\\n        \\\"next_gate\\\": \\\"D84_SANDBOX_WRITER_OUTPUT_REVIEW\\\",\\n    }\\n\\n    if ok:\\n        write_json(inbox_file_abs, handoff_payload)\\n        write_json(root / manifest_output_path, manifest)\\n\\n    report = {\\n        \\\"state\\\": \\\"D83_SANDBOX_WRITER_HANDOFF\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_SANDBOX_WRITER_HANDOFF\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": now(),\\n        \\\"handoff_id\\\": handoff_id,\\n        \\\"writer_input_path\\\": str(inbox_file_abs) if ok else \\\"\\\",\\n        \\\"manifest_path\\\": str(root / manifest_output_path) if ok else \\\"\\\",\\n        \\\"input_reports\\\": {\\n            \\\"d82_report_path\\\": str(root / d82_report_path),\\n            \\\"d82_request_path\\\": str(root / d82_request_path),\\n            \\\"d81_contract_path\\\": str(root / d81_contract_path),\\n        },\\n        \\\"evidence\\\": {\\n            \\\"intent_id\\\": intent_id,\\n            \\\"proposal_id\\\": proposal_id,\\n            \\\"boundary_id\\\": boundary_id,\\n            \\\"d81_intake_id\\\": d81_intake_id,\\n            \\\"signature_sha256\\\": payload.get(\\\"signature_sha256\\\") if payload else \\\"\\\",\\n            \\\"writer_input_path\\\": str(inbox_file_abs) if ok else \\\"\\\",\\n        },\\n        \\\"handoff_manifest\\\": manifest,\\n        \\\"guardrails\\\": {\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n            \\\"sandbox_handoff_only\\\": True,\\n            \\\"writer_input_only\\\": True,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"handoff_id\\\": handoff_id,\\n            \\\"intent_id\\\": intent_id,\\n            \\\"proposal_id\\\": proposal_id,\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"sandbox_writer_handoff_created\\\": ok,\\n            \\\"writer_input_created\\\": ok,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D84 should review sandbox writer output before any generated artifact can approach guarded apply.\\\",\\n        },\\n    }\\n\\n    write_json(root / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(create_sandbox_writer_handoff(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.sandbox_writer_handoff import create_sandbox_writer_handoff, sha256_json\\n\\n\\ndef signed_payload():\\n    payload = {\\n        \\\"approval_scope\\\": \\\"ALLOW_AI_PROPOSAL_TO_SANDBOX_INTAKE_ONLY\\\",\\n        \\\"approval_phrase\\\": \\\"APPROVE_D82_AI_PROPOSAL_INTAKE\\\",\\n        \\\"approver\\\": \\\"human_operator\\\",\\n        \\\"d81_intake_id\\\": \\\"d81-test-intake\\\",\\n        \\\"boundary_id\\\": \\\"d80-test-boundary\\\",\\n        \\\"proposal_id\\\": \\\"d80-proposal-test\\\",\\n        \\\"intake_contract_mode\\\": \\\"JSON_CONTRACT_ONLY\\\",\\n        \\\"allowed_next_gate\\\": \\\"D83_SANDBOX_WRITER_HANDOFF\\\",\\n        \\\"blocked_actions\\\": [\\n            \\\"actual_apply\\\",\\n            \\\"route_insert\\\",\\n            \\\"protected_core_mutation\\\",\\n            \\\"canonical_memory_overwrite\\\",\\n            \\\"external_ai_network_call\\\",\\n            \\\"git_commit_or_push_by_ai\\\",\\n        ],\\n    }\\n    payload[\\\"signature_sha256\\\"] = sha256_json(payload)\\n    return payload\\n\\n\\nclass TestD83SandboxWriterHandoff(unittest.TestCase):\\n    def make_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n\\n        payload = signed_payload()\\n        intent_id = \\\"d82-test-intent\\\"\\n\\n        (root / \\\"reports/d82_human_signed_intent.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"HUMAN_SIGNED_INTENT_READY\\\",\\n                    \\\"intent_id\\\": intent_id,\\n                    \\\"signed_payload\\\": payload,\\n                    \\\"guardrails\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                        \\\"human_signed_intent_only\\\": True,\\n                        \\\"sandbox_handoff_only\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d82_human_approval_request.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"intent_id\\\": intent_id,\\n                    \\\"allowed_next_gate\\\": \\\"D83_SANDBOX_WRITER_HANDOFF\\\",\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d81_ai_proposal_intake_contract.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"enabled\\\": True,\\n                    \\\"mode\\\": \\\"JSON_CONTRACT_ONLY\\\",\\n                    \\\"accepted_input\\\": {\\n                        \\\"candidate_files_prefixes_allowed\\\": [\\n                            \\\"runtime_experimental/\\\",\\n                            \\\"reports/\\\",\\n                            \\\"tests/\\\",\\n                        ],\\n                        \\\"candidate_files_prefixes_blocked\\\": [\\n                            \\\"app/orchestration/\\\",\\n                            \\\"core/\\\",\\n                            \\\"runtime/\\\",\\n                            \\\"bridges/\\\",\\n                            \\\"memory/\\\",\\n                        ],\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        return td, root\\n\\n    def test_creates_sandbox_writer_input_only(self):\\n        td, root = self.make_root()\\n        try:\\n            report = create_sandbox_writer_handoff(root=root)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"SANDBOX_WRITER_HANDOFF_READY\\\")\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"writer_input_only\\\"])\\n            self.assertFalse(report[\\\"guardrails\\\"][\\\"actual_apply_executed\\\"])\\n            self.assertFalse(report[\\\"guardrails\\\"][\\\"protected_core_mutated\\\"])\\n            self.assertTrue((root / \\\"reports/d83_sandbox_writer_handoff.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d83_sandbox_writer_handoff_manifest.json\\\").exists())\\n            self.assertTrue(Path(report[\\\"writer_input_path\\\"]).exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d82(self):\\n        td, root = self.make_root()\\n        try:\\n            (root / \\\"reports/d82_human_signed_intent.json\\\").unlink()\\n            report = create_sandbox_writer_handoff(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"SANDBOX_WRITER_HANDOFF_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_bad_signature(self):\\n        td, root = self.make_root()\\n        try:\\n            p = root / \\\"reports/d82_human_signed_intent.json\\\"\\n            data = json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n            data[\\\"signed_payload\\\"][\\\"proposal_id\\\"] = \\\"tampered\\\"\\n            p.write_text(json.dumps(data), encoding=\\\"utf-8\\\")\\n\\n            report = create_sandbox_writer_handoff(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"SANDBOX_WRITER_HANDOFF_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


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

print("D83 SANDBOX WRITER HANDOFF BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_writer_handoff.py").write_text(MODULE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/sandbox_writer_handoff.py")

Path("tests/test_d83_sandbox_writer_handoff.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d83_sandbox_writer_handoff.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_writer_handoff.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d83_sandbox_writer_handoff", "-v"], check=True)

print("\n== run D83 sandbox writer handoff ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.sandbox_writer_handoff import create_sandbox_writer_handoff\n"
        "r=create_sandbox_writer_handoff()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n"
        "print('WRITER_INPUT:', r.get('writer_input_path'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d83_sandbox_writer_handoff.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))
    print("WRITER_INPUT:", data.get("writer_input_path"))

print("\n== manifest preview ==")
mp = Path("reports/d83_sandbox_writer_handoff_manifest.json")
if mp.exists():
    data = json.loads(mp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("HANDOFF_ID:", data.get("handoff_id"))
    print("NEXT_GATE:", data.get("next_gate"))
    print("ACTUAL_FILES_CREATED:", data.get("actual_files_created"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_writer_handoff.py",
    "tests/test_d83_sandbox_writer_handoff.py",
    "reports/d83_sandbox_writer_handoff.json",
    "reports/d83_sandbox_writer_handoff_manifest.json",
]

# Add any generated inbox package.
inbox = Path("runtime_experimental/ai_sandbox_inbox")
if inbox.exists():
    for p in inbox.glob("*_sandbox_writer_input.json"):
        paths.append(str(p))

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D83_SANDBOX_WRITER_HANDOFF_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D83 sandbox writer handoff"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D83 sandbox writer handoff changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD83 SANDBOX WRITER HANDOFF BOOT DONE")
