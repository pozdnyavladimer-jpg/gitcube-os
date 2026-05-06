#!/usr/bin/env python3
# D84_SANDBOX_WRITER_OUTPUT_REVIEW_BOOT.py
#
# Adds D84 Sandbox Writer Output Review to GitCube OS.
#
# Run from repo root:
#     python D84_SANDBOX_WRITER_OUTPUT_REVIEW_BOOT.py
#
# Creates:
# - runtime_experimental/sandbox_writer_output_review.py
# - tests/test_d84_sandbox_writer_output_review.py
# - reports/d84_sandbox_writer_output_review.json
# - runtime_experimental/ai_sandbox_work/<review_id>/writer_output_candidate.json
#
# D84 does NOT call an external AI API.
# D84 does NOT use network access.
# D84 does NOT execute raw code from AI.
# D84 does NOT run shell commands from AI.
# D84 does NOT patch task_dispatcher.py.
# D84 does NOT mutate protected core.
# D84 does NOT overwrite canonical memory.
# D84 does NOT insert a real route.
#
# D84 only reviews sandbox writer output candidates.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_CODE = json.loads("\"from __future__ import annotations\\n\\nimport hashlib\\nimport json\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nD83_REPORT = \\\"reports/d83_sandbox_writer_handoff.json\\\"\\nD83_MANIFEST = \\\"reports/d83_sandbox_writer_handoff_manifest.json\\\"\\nOUT = \\\"reports/d84_sandbox_writer_output_review.json\\\"\\nWRITER_OUTPUT_DIR = \\\"runtime_experimental/ai_sandbox_work\\\"\\n\\n\\nALLOWED_WRITE_PREFIXES = [\\n    \\\"runtime_experimental/ai_sandbox_work/\\\",\\n    \\\"reports/\\\",\\n    \\\"tests/\\\",\\n]\\n\\nBLOCKED_WRITE_PREFIXES = [\\n    \\\"app/orchestration/\\\",\\n    \\\"core/\\\",\\n    \\\"runtime/\\\",\\n    \\\"bridges/\\\",\\n    \\\"memory/\\\",\\n]\\n\\nFORBIDDEN_ACTIONS = [\\n    \\\"direct_core_edit\\\",\\n    \\\"route_insert\\\",\\n    \\\"actual_apply\\\",\\n    \\\"external_ai_network_call\\\",\\n    \\\"git_commit_or_push_by_ai\\\",\\n    \\\"canonical_memory_overwrite\\\",\\n]\\n\\n\\ndef now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef safe_path(value: str) -> str:\\n    raw = str(value or \\\"\\\").strip().replace(\\\"\\\\\\\\\\\", \\\"/\\\").lstrip(\\\"/\\\")\\n    return \\\"/\\\".join(x for x in raw.split(\\\"/\\\") if x and x not in (\\\".\\\", \\\"..\\\"))\\n\\n\\ndef sha256_json(data: Dict[str, Any]) -> str:\\n    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode(\\\"utf-8\\\")).hexdigest()\\n\\n\\ndef is_allowed_write_path(path: str) -> bool:\\n    p = safe_path(path)\\n    if any(p.startswith(prefix) for prefix in BLOCKED_WRITE_PREFIXES):\\n        return False\\n    return any(p.startswith(prefix) for prefix in ALLOWED_WRITE_PREFIXES)\\n\\n\\ndef validate_d83(d83: Dict[str, Any], manifest: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:\\n    if not d83:\\n        errors.append(\\\"D83 sandbox writer handoff report missing or unreadable\\\")\\n        return {}\\n\\n    if d83.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D83 ok flag is not true\\\")\\n    if d83.get(\\\"decision\\\") != \\\"SANDBOX_WRITER_HANDOFF_READY\\\":\\n        errors.append(f\\\"D83 decision is not SANDBOX_WRITER_HANDOFF_READY: {d83.get('decision')}\\\")\\n\\n    guard = d83.get(\\\"guardrails\\\") if isinstance(d83.get(\\\"guardrails\\\"), dict) else {}\\n    for key in (\\n        \\\"external_ai_called\\\",\\n        \\\"network_accessed\\\",\\n        \\\"runtime_code_mutated\\\",\\n        \\\"protected_core_mutated\\\",\\n        \\\"canonical_memory_mutated\\\",\\n        \\\"actual_apply_executed\\\",\\n        \\\"route_inserted\\\",\\n        \\\"git_commit_by_ai\\\",\\n    ):\\n        if guard.get(key) is not False:\\n            errors.append(f\\\"D83 guardrail {key} is not false\\\")\\n    if guard.get(\\\"sandbox_handoff_only\\\") is not True:\\n        errors.append(\\\"D83 sandbox_handoff_only is not true\\\")\\n    if guard.get(\\\"writer_input_only\\\") is not True:\\n        errors.append(\\\"D83 writer_input_only is not true\\\")\\n\\n    if not manifest:\\n        errors.append(\\\"D83 manifest missing or unreadable\\\")\\n        return {}\\n\\n    if manifest.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D83 manifest ok flag is not true\\\")\\n    if manifest.get(\\\"next_gate\\\") != \\\"D84_SANDBOX_WRITER_OUTPUT_REVIEW\\\":\\n        errors.append(f\\\"D83 manifest next_gate invalid: {manifest.get('next_gate')}\\\")\\n    if manifest.get(\\\"protected_core_touched\\\") is not False:\\n        errors.append(\\\"D83 manifest protected_core_touched is not false\\\")\\n    if manifest.get(\\\"actual_files_mutated\\\") not in ([], None):\\n        errors.append(\\\"D83 manifest actual_files_mutated is not empty\\\")\\n\\n    writer_input_path = manifest.get(\\\"writer_input_path\\\") or d83.get(\\\"writer_input_path\\\") or \\\"\\\"\\n    if not writer_input_path:\\n        errors.append(\\\"D83 writer input path missing\\\")\\n        return {}\\n\\n    writer_input = read_json(writer_input_path, {}) or {}\\n    if not writer_input:\\n        errors.append(\\\"D83 writer input file missing or unreadable\\\")\\n        return {}\\n\\n    if writer_input.get(\\\"mode\\\") != \\\"SANDBOX_WRITER_INPUT_ONLY\\\":\\n        errors.append(f\\\"D83 writer input mode invalid: {writer_input.get('mode')}\\\")\\n\\n    wguard = writer_input.get(\\\"guardrails\\\") if isinstance(writer_input.get(\\\"guardrails\\\"), dict) else {}\\n    for key in (\\n        \\\"actual_apply_allowed\\\",\\n        \\\"route_insert_allowed\\\",\\n        \\\"protected_core_mutation_allowed\\\",\\n        \\\"external_ai_call_allowed\\\",\\n        \\\"git_action_allowed\\\",\\n    ):\\n        if wguard.get(key) is not False:\\n            errors.append(f\\\"D83 writer input guardrail {key} is not false\\\")\\n    if wguard.get(\\\"proposal_only\\\") is not True:\\n        errors.append(\\\"D83 writer input proposal_only is not true\\\")\\n    if wguard.get(\\\"sandbox_only\\\") is not True:\\n        errors.append(\\\"D83 writer input sandbox_only is not true\\\")\\n\\n    return writer_input\\n\\n\\ndef build_mock_writer_output(review_id: str, writer_input: Dict[str, Any]) -> Dict[str, Any]:\\n    source = writer_input.get(\\\"source\\\") if isinstance(writer_input.get(\\\"source\\\"), dict) else {}\\n    output_path = f\\\"{WRITER_OUTPUT_DIR}/{review_id}/candidate_proposal.json\\\"\\n    test_path = f\\\"tests/test_{review_id}_candidate_probe.py\\\"\\n    report_path = f\\\"reports/{review_id}_candidate_review.json\\\"\\n\\n    return {\\n        \\\"state\\\": \\\"D84_SANDBOX_WRITER_MOCK_OUTPUT\\\",\\n        \\\"ok\\\": True,\\n        \\\"mode\\\": \\\"SANDBOX_OUTPUT_CANDIDATE_ONLY\\\",\\n        \\\"created_at\\\": now(),\\n        \\\"review_id\\\": review_id,\\n        \\\"source\\\": source,\\n        \\\"candidate_files\\\": [\\n            output_path,\\n            test_path,\\n            report_path,\\n        ],\\n        \\\"candidate_payload\\\": {\\n            \\\"proposal_type\\\": \\\"SANDBOX_CHILD_MODULE_REVIEW_CANDIDATE\\\",\\n            \\\"target_scope\\\": \\\"sandbox_only\\\",\\n            \\\"source_handoff_id\\\": writer_input.get(\\\"handoff_id\\\"),\\n            \\\"summary\\\": \\\"Candidate output remains sandbox-only and waits for D85/D66 review before any guarded apply discussion.\\\",\\n        },\\n        \\\"forbidden_actions\\\": FORBIDDEN_ACTIONS,\\n        \\\"guardrails\\\": {\\n            \\\"sandbox_output_only\\\": True,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n        },\\n    }\\n\\n\\ndef review_writer_output(writer_output: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:\\n    if not writer_output:\\n        errors.append(\\\"writer output missing or unreadable\\\")\\n        return\\n\\n    if writer_output.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"writer output ok flag is not true\\\")\\n    if writer_output.get(\\\"mode\\\") != \\\"SANDBOX_OUTPUT_CANDIDATE_ONLY\\\":\\n        errors.append(f\\\"writer output mode invalid: {writer_output.get('mode')}\\\")\\n\\n    candidate_files = writer_output.get(\\\"candidate_files\\\")\\n    if not isinstance(candidate_files, list) or not candidate_files:\\n        errors.append(\\\"writer output candidate_files missing or empty\\\")\\n    else:\\n        for f in candidate_files:\\n            p = safe_path(str(f))\\n            if p != str(f).replace(\\\"\\\\\\\\\\\", \\\"/\\\").lstrip(\\\"/\\\"):\\n                errors.append(f\\\"candidate path is unsafe: {f}\\\")\\n            if not is_allowed_write_path(p):\\n                errors.append(f\\\"candidate file outside sandbox/reports/tests scope: {p}\\\")\\n\\n    forbidden = writer_output.get(\\\"forbidden_actions\\\")\\n    if not isinstance(forbidden, list):\\n        errors.append(\\\"writer output forbidden_actions missing or invalid\\\")\\n    else:\\n        for action in FORBIDDEN_ACTIONS:\\n            if action not in forbidden:\\n                errors.append(f\\\"writer output missing forbidden action: {action}\\\")\\n\\n    guard = writer_output.get(\\\"guardrails\\\") if isinstance(writer_output.get(\\\"guardrails\\\"), dict) else {}\\n    for key in (\\n        \\\"actual_apply_executed\\\",\\n        \\\"route_inserted\\\",\\n        \\\"protected_core_mutated\\\",\\n        \\\"canonical_memory_mutated\\\",\\n        \\\"external_ai_called\\\",\\n        \\\"network_accessed\\\",\\n        \\\"git_commit_by_ai\\\",\\n    ):\\n        if guard.get(key) is not False:\\n            errors.append(f\\\"writer output guardrail {key} is not false\\\")\\n    if guard.get(\\\"sandbox_output_only\\\") is not True:\\n        errors.append(\\\"writer output sandbox_output_only is not true\\\")\\n\\n\\ndef create_sandbox_writer_output_review(\\n    root: str | Path = \\\".\\\",\\n    d83_report_path: str = D83_REPORT,\\n    d83_manifest_path: str = D83_MANIFEST,\\n    output_path: str = OUT,\\n    writer_output_dir: str = WRITER_OUTPUT_DIR,\\n    injected_writer_output: Dict[str, Any] | None = None,\\n) -> Dict[str, Any]:\\n    root = Path(root).resolve()\\n    d83 = read_json(root / d83_report_path, {}) or {}\\n    manifest = read_json(root / d83_manifest_path, {}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    writer_input = validate_d83(d83, manifest, errors)\\n\\n    handoff_id = str(d83.get(\\\"handoff_id\\\") or manifest.get(\\\"handoff_id\\\") or \\\"\\\")\\n    intent_id = str((d83.get(\\\"evidence\\\") or {}).get(\\\"intent_id\\\") or \\\"\\\")\\n    proposal_id = str((d83.get(\\\"evidence\\\") or {}).get(\\\"proposal_id\\\") or \\\"\\\")\\n    review_id = \\\"d84-\\\" + sha256_json(\\n        {\\n            \\\"handoff_id\\\": handoff_id,\\n            \\\"intent_id\\\": intent_id,\\n            \\\"proposal_id\\\": proposal_id,\\n        }\\n    )[:16]\\n\\n    writer_output = injected_writer_output or build_mock_writer_output(review_id, writer_input)\\n    review_writer_output(writer_output, errors, warnings)\\n\\n    ok = not errors\\n    decision = \\\"SANDBOX_WRITER_OUTPUT_REVIEW_READY\\\" if ok else \\\"SANDBOX_WRITER_OUTPUT_REVIEW_BLOCKED\\\"\\n    result = \\\"D84_SANDBOX_WRITER_OUTPUT_REVIEW_CREATED\\\" if ok else \\\"D84_SANDBOX_WRITER_OUTPUT_REVIEW_BLOCKED\\\"\\n\\n    writer_output_rel = safe_path(f\\\"{writer_output_dir}/{review_id}/writer_output_candidate.json\\\")\\n    writer_output_abs = root / writer_output_rel\\n\\n    if ok:\\n        write_json(writer_output_abs, writer_output)\\n\\n    report = {\\n        \\\"state\\\": \\\"D84_SANDBOX_WRITER_OUTPUT_REVIEW\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_SANDBOX_WRITER_OUTPUT_REVIEW\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": now(),\\n        \\\"review_id\\\": review_id,\\n        \\\"writer_output_path\\\": str(writer_output_abs) if ok else \\\"\\\",\\n        \\\"input_reports\\\": {\\n            \\\"d83_report_path\\\": str(root / d83_report_path),\\n            \\\"d83_manifest_path\\\": str(root / d83_manifest_path),\\n        },\\n        \\\"evidence\\\": {\\n            \\\"handoff_id\\\": handoff_id,\\n            \\\"intent_id\\\": intent_id,\\n            \\\"proposal_id\\\": proposal_id,\\n            \\\"writer_output_mode\\\": writer_output.get(\\\"mode\\\") if isinstance(writer_output, dict) else None,\\n            \\\"candidate_files\\\": writer_output.get(\\\"candidate_files\\\") if isinstance(writer_output, dict) else [],\\n        },\\n        \\\"review\\\": {\\n            \\\"candidate_files_count\\\": len(writer_output.get(\\\"candidate_files\\\", [])) if isinstance(writer_output, dict) else 0,\\n            \\\"allowed_write_prefixes\\\": ALLOWED_WRITE_PREFIXES,\\n            \\\"blocked_write_prefixes\\\": BLOCKED_WRITE_PREFIXES,\\n            \\\"forbidden_actions\\\": FORBIDDEN_ACTIONS,\\n            \\\"approved_for_guarded_apply\\\": False,\\n            \\\"approved_for_route_insert\\\": False,\\n            \\\"approved_for_protected_core\\\": False,\\n            \\\"approved_for_next_sandbox_gate\\\": ok,\\n        },\\n        \\\"guardrails\\\": {\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"git_commit_by_ai\\\": False,\\n            \\\"sandbox_output_review_only\\\": True,\\n            \\\"writer_output_candidate_only\\\": True,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"review_id\\\": review_id,\\n            \\\"handoff_id\\\": handoff_id,\\n            \\\"proposal_id\\\": proposal_id,\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"sandbox_writer_output_reviewed\\\": ok,\\n            \\\"writer_output_candidate_created\\\": ok,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D85 can create regression/rollback evidence bundle for reviewed sandbox output; real apply still blocked.\\\",\\n        },\\n    }\\n\\n    write_json(root / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(create_sandbox_writer_output_review(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.sandbox_writer_output_review import create_sandbox_writer_output_review\\n\\n\\nclass TestD84SandboxWriterOutputReview(unittest.TestCase):\\n    def make_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n        (root / \\\"runtime_experimental/ai_sandbox_inbox\\\").mkdir(parents=True)\\n\\n        handoff_id = \\\"d83-test-handoff\\\"\\n        writer_input_path = root / \\\"runtime_experimental/ai_sandbox_inbox/d83-test-handoff_sandbox_writer_input.json\\\"\\n\\n        writer_input_path.write_text(\\n            json.dumps(\\n                {\\n                    \\\"state\\\": \\\"D83_SANDBOX_WRITER_INPUT\\\",\\n                    \\\"ok\\\": True,\\n                    \\\"handoff_id\\\": handoff_id,\\n                    \\\"mode\\\": \\\"SANDBOX_WRITER_INPUT_ONLY\\\",\\n                    \\\"source\\\": {\\n                        \\\"intent_id\\\": \\\"d82-test-intent\\\",\\n                        \\\"proposal_id\\\": \\\"d80-proposal-test\\\",\\n                        \\\"boundary_id\\\": \\\"d80-test-boundary\\\",\\n                        \\\"d81_intake_id\\\": \\\"d81-test-intake\\\",\\n                    },\\n                    \\\"guardrails\\\": {\\n                        \\\"proposal_only\\\": True,\\n                        \\\"sandbox_only\\\": True,\\n                        \\\"actual_apply_allowed\\\": False,\\n                        \\\"route_insert_allowed\\\": False,\\n                        \\\"protected_core_mutation_allowed\\\": False,\\n                        \\\"external_ai_call_allowed\\\": False,\\n                        \\\"git_action_allowed\\\": False,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d83_sandbox_writer_handoff.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"SANDBOX_WRITER_HANDOFF_READY\\\",\\n                    \\\"handoff_id\\\": handoff_id,\\n                    \\\"writer_input_path\\\": str(writer_input_path),\\n                    \\\"evidence\\\": {\\n                        \\\"intent_id\\\": \\\"d82-test-intent\\\",\\n                        \\\"proposal_id\\\": \\\"d80-proposal-test\\\",\\n                    },\\n                    \\\"guardrails\\\": {\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"network_accessed\\\": False,\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"git_commit_by_ai\\\": False,\\n                        \\\"sandbox_handoff_only\\\": True,\\n                        \\\"writer_input_only\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        (root / \\\"reports/d83_sandbox_writer_handoff_manifest.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"handoff_id\\\": handoff_id,\\n                    \\\"writer_input_path\\\": str(writer_input_path),\\n                    \\\"actual_files_created\\\": [\\\"runtime_experimental/ai_sandbox_inbox/d83-test-handoff_sandbox_writer_input.json\\\"],\\n                    \\\"actual_files_mutated\\\": [],\\n                    \\\"protected_core_touched\\\": False,\\n                    \\\"next_gate\\\": \\\"D84_SANDBOX_WRITER_OUTPUT_REVIEW\\\",\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        return td, root\\n\\n    def test_reviews_sandbox_writer_output_only(self):\\n        td, root = self.make_root()\\n        try:\\n            report = create_sandbox_writer_output_review(root=root)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"SANDBOX_WRITER_OUTPUT_REVIEW_READY\\\")\\n            self.assertFalse(report[\\\"guardrails\\\"][\\\"actual_apply_executed\\\"])\\n            self.assertFalse(report[\\\"review\\\"][\\\"approved_for_guarded_apply\\\"])\\n            self.assertTrue(report[\\\"guardrails\\\"][\\\"writer_output_candidate_only\\\"])\\n            self.assertTrue((root / \\\"reports/d84_sandbox_writer_output_review.json\\\").exists())\\n            self.assertTrue(Path(report[\\\"writer_output_path\\\"]).exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d83(self):\\n        td, root = self.make_root()\\n        try:\\n            (root / \\\"reports/d83_sandbox_writer_handoff.json\\\").unlink()\\n            report = create_sandbox_writer_output_review(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"SANDBOX_WRITER_OUTPUT_REVIEW_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_protected_candidate_path(self):\\n        td, root = self.make_root()\\n        try:\\n            bad_output = {\\n                \\\"ok\\\": True,\\n                \\\"mode\\\": \\\"SANDBOX_OUTPUT_CANDIDATE_ONLY\\\",\\n                \\\"candidate_files\\\": [\\\"app/orchestration/task_dispatcher.py\\\"],\\n                \\\"forbidden_actions\\\": [\\n                    \\\"direct_core_edit\\\",\\n                    \\\"route_insert\\\",\\n                    \\\"actual_apply\\\",\\n                    \\\"external_ai_network_call\\\",\\n                    \\\"git_commit_or_push_by_ai\\\",\\n                    \\\"canonical_memory_overwrite\\\",\\n                ],\\n                \\\"guardrails\\\": {\\n                    \\\"sandbox_output_only\\\": True,\\n                    \\\"actual_apply_executed\\\": False,\\n                    \\\"route_inserted\\\": False,\\n                    \\\"protected_core_mutated\\\": False,\\n                    \\\"canonical_memory_mutated\\\": False,\\n                    \\\"external_ai_called\\\": False,\\n                    \\\"network_accessed\\\": False,\\n                    \\\"git_commit_by_ai\\\": False,\\n                },\\n            }\\n            report = create_sandbox_writer_output_review(root=root, injected_writer_output=bad_output)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"SANDBOX_WRITER_OUTPUT_REVIEW_BLOCKED\\\")\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


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

print("D84 SANDBOX WRITER OUTPUT REVIEW BOOT: repo =", ROOT)

Path("runtime_experimental/sandbox_writer_output_review.py").write_text(MODULE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/sandbox_writer_output_review.py")

Path("tests/test_d84_sandbox_writer_output_review.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d84_sandbox_writer_output_review.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_writer_output_review.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d84_sandbox_writer_output_review", "-v"], check=True)

print("\n== run D84 sandbox writer output review ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.sandbox_writer_output_review import create_sandbox_writer_output_review\n"
        "r=create_sandbox_writer_output_review()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n"
        "print('WRITER_OUTPUT:', r.get('writer_output_path'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d84_sandbox_writer_output_review.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))
    print("WRITER_OUTPUT:", data.get("writer_output_path"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_writer_output_review.py",
    "tests/test_d84_sandbox_writer_output_review.py",
    "reports/d84_sandbox_writer_output_review.json",
]

work = Path("runtime_experimental/ai_sandbox_work")
if work.exists():
    for p in work.glob("d84-*/writer_output_candidate.json"):
        paths.append(str(p))

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D84_SANDBOX_WRITER_OUTPUT_REVIEW_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D84 sandbox writer output review"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D84 sandbox writer output review changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD84 SANDBOX WRITER OUTPUT REVIEW BOOT DONE")
