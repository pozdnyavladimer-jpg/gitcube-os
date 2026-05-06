#!/usr/bin/env python3
# D80_AI_PROVIDER_BOUNDARY_BOOT.py
#
# Adds D80 AI Provider Boundary to GitCube OS.
#
# Run from repo root:
#     python D80_AI_PROVIDER_BOUNDARY_BOOT.py
#
# Creates:
# - runtime_experimental/ai_provider_boundary.py
# - tests/test_d80_ai_provider_boundary.py
# - reports/d80_ai_provider_boundary.json
# - reports/d80_ai_provider_mock_proposal.json
#
# D80 does NOT call an external AI API.
# D80 does NOT use network access.
# D80 does NOT patch task_dispatcher.py.
# D80 does NOT mutate protected core.
# D80 does NOT overwrite canonical memory.
# D80 does NOT insert a real route.
#
# D80 creates the sealed AI boundary in PROPOSE_ONLY / mock_local mode.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_CODE = json.loads("\"from __future__ import annotations\\n\\nimport hashlib\\nimport json\\nimport os\\nfrom datetime import datetime, timezone\\nfrom pathlib import Path\\nfrom typing import Any, Dict, List\\n\\n\\nD79_REPORT = \\\"reports/d79_policy_verification_gate.json\\\"\\nOUT = \\\"reports/d80_ai_provider_boundary.json\\\"\\nPROPOSAL_OUT = \\\"reports/d80_ai_provider_mock_proposal.json\\\"\\n\\n\\ndef now() -> str:\\n    return datetime.now(timezone.utc).isoformat()\\n\\n\\ndef read_json(path: str | Path, default: Any = None) -> Any:\\n    p = Path(path)\\n    if not p.exists():\\n        return default\\n    try:\\n        return json.loads(p.read_text(encoding=\\\"utf-8\\\"))\\n    except Exception:\\n        return default\\n\\n\\ndef write_json(path: str | Path, data: Dict[str, Any]) -> None:\\n    p = Path(path)\\n    p.parent.mkdir(parents=True, exist_ok=True)\\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=\\\"utf-8\\\")\\n\\n\\ndef safe_path(value: str) -> str:\\n    raw = str(value or \\\"\\\").strip().replace(\\\"\\\\\\\\\\\", \\\"/\\\").lstrip(\\\"/\\\")\\n    return \\\"/\\\".join(x for x in raw.split(\\\"/\\\") if x and x not in (\\\".\\\", \\\"..\\\"))\\n\\n\\ndef sha256_json(data: Dict[str, Any]) -> str:\\n    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode(\\\"utf-8\\\")).hexdigest()\\n\\n\\ndef _validate_d79(d79: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:\\n    if not d79:\\n        errors.append(\\\"D79 policy verification report missing or unreadable\\\")\\n        return {}\\n\\n    if d79.get(\\\"ok\\\") is not True:\\n        errors.append(\\\"D79 ok flag is not true\\\")\\n\\n    if d79.get(\\\"decision\\\") != \\\"POLICY_VERIFIED_DRY_RUN_READY\\\":\\n        errors.append(f\\\"D79 decision is not POLICY_VERIFIED_DRY_RUN_READY: {d79.get('decision')}\\\")\\n\\n    verdict = d79.get(\\\"policy_verdict\\\") if isinstance(d79.get(\\\"policy_verdict\\\"), dict) else {}\\n    if verdict.get(\\\"verdict\\\") != \\\"DRY_RUN_POLICY_APPROVED\\\":\\n        errors.append(f\\\"D79 policy verdict is not DRY_RUN_POLICY_APPROVED: {verdict.get('verdict')}\\\")\\n    if verdict.get(\\\"real_route_insert_allowed\\\") is not False:\\n        errors.append(\\\"D79 real_route_insert_allowed is not false\\\")\\n    if verdict.get(\\\"real_apply_allowed\\\") is not False:\\n        errors.append(\\\"D79 real_apply_allowed is not false\\\")\\n    if verdict.get(\\\"ai_provider_allowed\\\") is not False:\\n        errors.append(\\\"D79 ai_provider_allowed must still be false before D80 boundary is created\\\")\\n\\n    guard = d79.get(\\\"guardrails\\\") if isinstance(d79.get(\\\"guardrails\\\"), dict) else {}\\n    for key in (\\n        \\\"runtime_code_mutated\\\",\\n        \\\"protected_core_mutated\\\",\\n        \\\"canonical_memory_mutated\\\",\\n        \\\"external_ai_called\\\",\\n        \\\"actual_apply_executed\\\",\\n        \\\"route_inserted\\\",\\n    ):\\n        if guard.get(key) is not False:\\n            errors.append(f\\\"D79 guardrail {key} is not false\\\")\\n    if guard.get(\\\"policy_gate_only\\\") is not True:\\n        errors.append(\\\"D79 policy_gate_only is not true\\\")\\n\\n    return verdict\\n\\n\\ndef _mock_ai_proposal(\\n    boundary_id: str,\\n    source_node: str,\\n    child_module_path: str,\\n    adapter_name: str,\\n    d79_gate_id: str,\\n) -> Dict[str, Any]:\\n    proposal_id = \\\"d80-proposal-\\\" + sha256_json(\\n        {\\n            \\\"boundary_id\\\": boundary_id,\\n            \\\"source_node\\\": source_node,\\n            \\\"child_module_path\\\": child_module_path,\\n            \\\"adapter_name\\\": adapter_name,\\n            \\\"d79_gate_id\\\": d79_gate_id,\\n        }\\n    )[:16]\\n\\n    return {\\n        \\\"state\\\": \\\"D80_AI_PROVIDER_MOCK_PROPOSAL\\\",\\n        \\\"ok\\\": True,\\n        \\\"proposal_id\\\": proposal_id,\\n        \\\"provider\\\": \\\"mock_local\\\",\\n        \\\"mode\\\": \\\"PROPOSE_ONLY\\\",\\n        \\\"created_at\\\": now(),\\n        \\\"source\\\": {\\n            \\\"d79_gate_id\\\": d79_gate_id,\\n            \\\"source_node\\\": source_node,\\n            \\\"child_module_path\\\": child_module_path,\\n            \\\"adapter_name\\\": adapter_name,\\n        },\\n        \\\"proposal\\\": {\\n            \\\"type\\\": \\\"NEXT_MODULE_PROPOSAL\\\",\\n            \\\"recommended_next_module\\\": \\\"D81_AI_PROPOSAL_INTAKE\\\",\\n            \\\"action\\\": \\\"CREATE_JSON_INTAKE_GATE_FOR_AI_PROPOSALS\\\",\\n            \\\"reason\\\": \\\"D80 boundary is sealed; next step is to accept only structured proposal JSON, never raw code execution.\\\",\\n            \\\"allowed_output_contract\\\": {\\n                \\\"format\\\": \\\"json\\\",\\n                \\\"required_fields\\\": [\\n                    \\\"proposal_id\\\",\\n                    \\\"proposal_type\\\",\\n                    \\\"target_scope\\\",\\n                    \\\"candidate_files\\\",\\n                    \\\"guardrails\\\",\\n                    \\\"validation_plan\\\",\\n                ],\\n                \\\"forbidden_fields\\\": [\\n                    \\\"raw_shell_command\\\",\\n                    \\\"auto_apply\\\",\\n                    \\\"direct_core_edit\\\",\\n                    \\\"api_secret\\\",\\n                ],\\n            },\\n        },\\n        \\\"guardrails\\\": {\\n            \\\"external_ai_called\\\": False,\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"proposal_only\\\": True,\\n            \\\"mock_provider_only\\\": True,\\n        },\\n    }\\n\\n\\ndef create_ai_provider_boundary(\\n    root: str | Path = \\\".\\\",\\n    d79_report_path: str = D79_REPORT,\\n    output_path: str = OUT,\\n    proposal_output_path: str = PROPOSAL_OUT,\\n    provider: str | None = None,\\n) -> Dict[str, Any]:\\n    root = Path(root).resolve()\\n    d79 = read_json(root / d79_report_path, {}) or {}\\n\\n    errors: List[str] = []\\n    warnings: List[str] = []\\n\\n    _validate_d79(d79, errors)\\n\\n    requested_provider = provider or os.environ.get(\\\"GITCUBE_AI_PROVIDER\\\", \\\"mock_local\\\")\\n    if requested_provider != \\\"mock_local\\\":\\n        warnings.append(f\\\"external provider '{requested_provider}' requested but blocked; D80 allows mock_local only\\\")\\n        requested_provider = \\\"mock_local\\\"\\n\\n    evidence = d79.get(\\\"evidence\\\") if isinstance(d79.get(\\\"evidence\\\"), dict) else {}\\n    summary = d79.get(\\\"summary\\\") if isinstance(d79.get(\\\"summary\\\"), dict) else {}\\n\\n    source_node = safe_path(str(evidence.get(\\\"source_node\\\") or summary.get(\\\"source_node\\\") or \\\"\\\"))\\n    child_module_path = safe_path(str(evidence.get(\\\"child_module_path\\\") or summary.get(\\\"child_module_path\\\") or \\\"\\\"))\\n    adapter_name = str(evidence.get(\\\"adapter_name\\\") or summary.get(\\\"adapter_name\\\") or \\\"\\\")\\n    d79_gate_id = str(d79.get(\\\"gate_id\\\") or summary.get(\\\"gate_id\\\") or \\\"\\\")\\n\\n    if not source_node:\\n        errors.append(\\\"D79 source_node missing\\\")\\n    if not child_module_path:\\n        errors.append(\\\"D79 child_module_path missing\\\")\\n    elif not child_module_path.startswith(\\\"runtime_experimental/differentiated_modules/\\\"):\\n        errors.append(f\\\"D79 child_module_path outside differentiated_modules: {child_module_path}\\\")\\n    if child_module_path and not (root / child_module_path).exists():\\n        errors.append(f\\\"child module does not exist on disk: {child_module_path}\\\")\\n    if not adapter_name:\\n        errors.append(\\\"D79 adapter_name missing\\\")\\n    if not d79_gate_id:\\n        errors.append(\\\"D79 gate_id missing\\\")\\n\\n    boundary_core = {\\n        \\\"d79_gate_id\\\": d79_gate_id,\\n        \\\"source_node\\\": source_node,\\n        \\\"child_module_path\\\": child_module_path,\\n        \\\"adapter_name\\\": adapter_name,\\n        \\\"provider\\\": requested_provider,\\n    }\\n    boundary_id = \\\"d80-\\\" + sha256_json(boundary_core)[:16]\\n\\n    ok = not errors\\n    decision = \\\"AI_PROVIDER_BOUNDARY_READY\\\" if ok else \\\"AI_PROVIDER_BOUNDARY_BLOCKED\\\"\\n    result = \\\"D80_AI_PROVIDER_BOUNDARY_CREATED\\\" if ok else \\\"D80_AI_PROVIDER_BOUNDARY_BLOCKED\\\"\\n\\n    proposal: Dict[str, Any] = {}\\n    if ok:\\n        proposal = _mock_ai_proposal(\\n            boundary_id=boundary_id,\\n            source_node=source_node,\\n            child_module_path=child_module_path,\\n            adapter_name=adapter_name,\\n            d79_gate_id=d79_gate_id,\\n        )\\n        write_json(root / proposal_output_path, proposal)\\n\\n    boundary = {\\n        \\\"boundary_id\\\": boundary_id,\\n        \\\"state\\\": \\\"D80_AI_PROVIDER_BOUNDARY\\\",\\n        \\\"enabled\\\": ok,\\n        \\\"provider\\\": requested_provider,\\n        \\\"mode\\\": \\\"PROPOSE_ONLY\\\",\\n        \\\"network_access_allowed\\\": False,\\n        \\\"external_ai_call_allowed\\\": False,\\n        \\\"api_keys_required\\\": False,\\n        \\\"raw_code_execution_allowed\\\": False,\\n        \\\"shell_command_generation_allowed\\\": False,\\n        \\\"direct_file_write_allowed\\\": False,\\n        \\\"git_commit_allowed\\\": False,\\n        \\\"actual_apply_allowed\\\": False,\\n        \\\"route_insert_allowed\\\": False,\\n        \\\"allowed_input_sources\\\": [\\n            \\\"reports/d79_policy_verification_gate.json\\\",\\n            \\\"reports/d78_narrow_adapter_dry_run_diff.json\\\",\\n            \\\"reports/d77_narrow_adapter_contract.json\\\",\\n            \\\"reports/d76_child_module_probe_report.json\\\",\\n        ],\\n        \\\"allowed_outputs\\\": [\\n            \\\"structured proposal JSON\\\",\\n            \\\"sandbox-only candidate plan\\\",\\n            \\\"validation plan\\\",\\n        ],\\n        \\\"forbidden_outputs\\\": [\\n            \\\"raw patch applied to protected core\\\",\\n            \\\"shell command requiring execution\\\",\\n            \\\"git commit instruction as autonomous action\\\",\\n            \\\"secret/API key request\\\",\\n            \\\"canonical memory overwrite\\\",\\n        ],\\n        \\\"next_required_gate\\\": \\\"D81_AI_PROPOSAL_INTAKE\\\",\\n    }\\n\\n    report = {\\n        \\\"state\\\": \\\"D80_AI_PROVIDER_BOUNDARY\\\",\\n        \\\"result\\\": result,\\n        \\\"route\\\": \\\"FIELD_INTENT_AI_PROVIDER_BOUNDARY\\\",\\n        \\\"ok\\\": ok,\\n        \\\"decision\\\": decision,\\n        \\\"created_at\\\": now(),\\n        \\\"boundary_id\\\": boundary_id,\\n        \\\"boundary\\\": boundary,\\n        \\\"mock_proposal_path\\\": str(root / proposal_output_path) if ok else \\\"\\\",\\n        \\\"input_reports\\\": {\\n            \\\"d79_report_path\\\": str(root / d79_report_path),\\n        },\\n        \\\"evidence\\\": {\\n            \\\"d79_ok\\\": d79.get(\\\"ok\\\"),\\n            \\\"d79_decision\\\": d79.get(\\\"decision\\\"),\\n            \\\"d79_gate_id\\\": d79_gate_id,\\n            \\\"source_node\\\": source_node,\\n            \\\"child_module_path\\\": child_module_path,\\n            \\\"adapter_name\\\": adapter_name,\\n            \\\"provider\\\": requested_provider,\\n        },\\n        \\\"guardrails\\\": {\\n            \\\"external_ai_called\\\": False,\\n            \\\"network_accessed\\\": False,\\n            \\\"runtime_code_mutated\\\": False,\\n            \\\"protected_core_mutated\\\": False,\\n            \\\"canonical_memory_mutated\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"provider_boundary_only\\\": True,\\n            \\\"proposal_only\\\": True,\\n        },\\n        \\\"validation\\\": {\\n            \\\"ok\\\": ok,\\n            \\\"errors\\\": errors,\\n            \\\"warnings\\\": warnings,\\n        },\\n        \\\"summary\\\": {\\n            \\\"decision\\\": decision,\\n            \\\"boundary_id\\\": boundary_id,\\n            \\\"provider\\\": requested_provider,\\n            \\\"mode\\\": \\\"PROPOSE_ONLY\\\",\\n            \\\"source_node\\\": source_node,\\n            \\\"child_module_path\\\": child_module_path,\\n            \\\"adapter_name\\\": adapter_name,\\n            \\\"errors_count\\\": len(errors),\\n            \\\"warnings_count\\\": len(warnings),\\n        },\\n        \\\"success_condition\\\": {\\n            \\\"ai_boundary_created\\\": ok,\\n            \\\"external_ai_called\\\": False,\\n            \\\"actual_apply_executed\\\": False,\\n            \\\"route_inserted\\\": False,\\n            \\\"protected_core_untouched\\\": True,\\n            \\\"next_step\\\": \\\"D81 should validate AI proposal JSON before any sandbox writer receives it.\\\",\\n        },\\n    }\\n\\n    write_json(root / output_path, report)\\n    return report\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    print(json.dumps(create_ai_provider_boundary(), ensure_ascii=False, indent=2))\\n\"")
TEST_CODE = json.loads("\"import json\\nimport tempfile\\nimport unittest\\nfrom pathlib import Path\\n\\nfrom runtime_experimental.ai_provider_boundary import create_ai_provider_boundary\\n\\n\\nclass TestD80AIProviderBoundary(unittest.TestCase):\\n    def make_root(self):\\n        td = tempfile.TemporaryDirectory()\\n        root = Path(td.name)\\n        (root / \\\"reports\\\").mkdir(parents=True)\\n        (root / \\\"runtime_experimental/differentiated_modules\\\").mkdir(parents=True)\\n        (root / \\\"app/orchestration\\\").mkdir(parents=True)\\n\\n        source = \\\"app/orchestration/task_dispatcher.py\\\"\\n        child = \\\"runtime_experimental/differentiated_modules/01_route_policy_child.py\\\"\\n        adapter = \\\"D77_NARROW_ADAPTER_ROUTE_POLICY_CHILD\\\"\\n\\n        (root / source).write_text(\\\"# source unchanged\\\\n\\\", encoding=\\\"utf-8\\\")\\n        (root / child).write_text(\\\"def run_sandbox_probe(event=None): return {'ok': True}\\\\n\\\", encoding=\\\"utf-8\\\")\\n\\n        (root / \\\"reports/d79_policy_verification_gate.json\\\").write_text(\\n            json.dumps(\\n                {\\n                    \\\"ok\\\": True,\\n                    \\\"decision\\\": \\\"POLICY_VERIFIED_DRY_RUN_READY\\\",\\n                    \\\"gate_id\\\": \\\"d79-test-gate\\\",\\n                    \\\"policy_verdict\\\": {\\n                        \\\"verdict\\\": \\\"DRY_RUN_POLICY_APPROVED\\\",\\n                        \\\"scope\\\": \\\"dry_run_diff_only\\\",\\n                        \\\"real_route_insert_allowed\\\": False,\\n                        \\\"real_apply_allowed\\\": False,\\n                        \\\"ai_provider_allowed\\\": False,\\n                    },\\n                    \\\"evidence\\\": {\\n                        \\\"source_node\\\": source,\\n                        \\\"child_module_path\\\": child,\\n                        \\\"adapter_name\\\": adapter,\\n                    },\\n                    \\\"guardrails\\\": {\\n                        \\\"runtime_code_mutated\\\": False,\\n                        \\\"protected_core_mutated\\\": False,\\n                        \\\"canonical_memory_mutated\\\": False,\\n                        \\\"external_ai_called\\\": False,\\n                        \\\"actual_apply_executed\\\": False,\\n                        \\\"route_inserted\\\": False,\\n                        \\\"policy_gate_only\\\": True,\\n                    },\\n                }\\n            ),\\n            encoding=\\\"utf-8\\\",\\n        )\\n\\n        return td, root, source\\n\\n    def test_creates_mock_propose_only_boundary(self):\\n        td, root, source = self.make_root()\\n        try:\\n            before = (root / source).read_text(encoding=\\\"utf-8\\\")\\n            report = create_ai_provider_boundary(root=root)\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"AI_PROVIDER_BOUNDARY_READY\\\")\\n            self.assertEqual(report[\\\"boundary\\\"][\\\"mode\\\"], \\\"PROPOSE_ONLY\\\")\\n            self.assertFalse(report[\\\"boundary\\\"][\\\"external_ai_call_allowed\\\"])\\n            self.assertFalse(report[\\\"boundary\\\"][\\\"actual_apply_allowed\\\"])\\n            self.assertFalse(report[\\\"guardrails\\\"][\\\"external_ai_called\\\"])\\n            self.assertEqual((root / source).read_text(encoding=\\\"utf-8\\\"), before)\\n            self.assertTrue((root / \\\"reports/d80_ai_provider_boundary.json\\\").exists())\\n            self.assertTrue((root / \\\"reports/d80_ai_provider_mock_proposal.json\\\").exists())\\n        finally:\\n            td.cleanup()\\n\\n    def test_blocks_missing_d79(self):\\n        td, root, _ = self.make_root()\\n        try:\\n            (root / \\\"reports/d79_policy_verification_gate.json\\\").unlink()\\n            report = create_ai_provider_boundary(root=root)\\n\\n            self.assertFalse(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"decision\\\"], \\\"AI_PROVIDER_BOUNDARY_BLOCKED\\\")\\n            self.assertGreaterEqual(report[\\\"summary\\\"][\\\"errors_count\\\"], 1)\\n        finally:\\n            td.cleanup()\\n\\n    def test_external_provider_request_is_blocked_to_mock(self):\\n        td, root, _ = self.make_root()\\n        try:\\n            report = create_ai_provider_boundary(root=root, provider=\\\"external_openai\\\")\\n\\n            self.assertTrue(report[\\\"ok\\\"])\\n            self.assertEqual(report[\\\"boundary\\\"][\\\"provider\\\"], \\\"mock_local\\\")\\n            self.assertFalse(report[\\\"boundary\\\"][\\\"network_access_allowed\\\"])\\n            self.assertGreaterEqual(report[\\\"summary\\\"][\\\"warnings_count\\\"], 1)\\n        finally:\\n            td.cleanup()\\n\\n\\nif __name__ == \\\"__main__\\\":\\n    unittest.main()\\n\"")


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

print("D80 AI PROVIDER BOUNDARY BOOT: repo =", ROOT)

Path("runtime_experimental/ai_provider_boundary.py").write_text(MODULE_CODE, encoding="utf-8")
print("created/updated runtime_experimental/ai_provider_boundary.py")

Path("tests/test_d80_ai_provider_boundary.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d80_ai_provider_boundary.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/ai_provider_boundary.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d80_ai_provider_boundary", "-v"], check=True)

print("\n== run D80 AI provider boundary ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.ai_provider_boundary import create_ai_provider_boundary\n"
        "r=create_ai_provider_boundary()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('DECISION:', r.get('decision'))\n"
        "print('SUMMARY:', r.get('summary'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d80_ai_provider_boundary.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))
    print("BOUNDARY:", data.get("boundary"))

print("\n== mock proposal preview ==")
pp = Path("reports/d80_ai_provider_mock_proposal.json")
if pp.exists():
    data = json.loads(pp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("PROPOSAL_ID:", data.get("proposal_id"))
    print("MODE:", data.get("mode"))
    print("PROPOSAL:", data.get("proposal"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/ai_provider_boundary.py",
    "tests/test_d80_ai_provider_boundary.py",
    "reports/d80_ai_provider_boundary.json",
    "reports/d80_ai_provider_mock_proposal.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D80_AI_PROVIDER_BOUNDARY_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D80 AI provider boundary"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D80 AI provider boundary changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD80 AI PROVIDER BOUNDARY BOOT DONE")
