#!/usr/bin/env python3
# D106_AI_PROPOSE_ONLY_PROVIDER_BOUNDARY_BOOT.py
#
# Creates the D106 AI Propose-Only Provider Boundary after the sealed D90-D104 chain.
#
# Output:
# - runtime_experimental/ai_propose_only_provider_boundary.py
# - tests/test_d106_ai_propose_only_provider_boundary.py
# - reports/d106_ai_provider_boundary.json
# - reports/d106_provider_input_contract.json
# - reports/d106_provider_output_contract.json
# - reports/d106_forbidden_action_matrix.json
# - reports/d106_d107_proposal_schema_validator_scope.json
#
# Safety:
# - no real AI/provider call
# - no API keys or secrets
# - no shell execution from AI
# - no apply/rollback/restore
# - no route insert
# - no protected-core mutation
# - no AI git commit/push

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


MODULE = r"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D104_TERMINAL = "reports/d104_terminal_safety_state.json"
D105_DOC_REPORT = "reports/d105_guarded_autonomy_chain_doc.json"

OUT = "reports/d106_ai_provider_boundary.json"
INPUT_CONTRACT = "reports/d106_provider_input_contract.json"
OUTPUT_CONTRACT = "reports/d106_provider_output_contract.json"
FORBIDDEN_MATRIX = "reports/d106_forbidden_action_matrix.json"
D107_SCOPE = "reports/d106_d107_proposal_schema_validator_scope.json"

REQ_D104_TERMINAL = "GUARDED_AUTONOMY_PRE_EXECUTION_CHAIN_SEALED"

FORBIDDEN_FIELDS = [
    "api_key", "api_secret", "token", "password",
    "raw_shell_command", "shell_command", "subprocess",
    "exec", "eval", "auto_apply", "apply_now",
    "git_commit", "git_push", "route_insert",
    "protected_core_mutation", "canonical_memory_overwrite",
    "direct_core_edit",
]

FORBIDDEN_ACTIONS = [
    "real_apply", "auto_apply", "route_insert",
    "protected_core_mutation", "canonical_memory_overwrite",
    "external_ai_network_call", "shell_exec", "subprocess_exec",
    "git_commit_by_ai", "git_push_by_ai", "rollback_execute",
    "restore_execute", "delete_runtime_candidate",
]

REQUIRED_OUTPUT_FIELDS = [
    "proposal_id", "proposal_type", "intent", "target_scope",
    "candidate_files", "risk_flags", "guardrails",
    "validation_plan", "requires_human_review",
]

ALLOWED_PROPOSAL_TYPES = [
    "documentation_proposal", "test_proposal",
    "sandbox_patch_proposal", "analysis_proposal", "schema_proposal",
]

ALLOWED_TARGET_PREFIXES = [
    "runtime_experimental/ai_sandbox_work/",
    "reports/",
    "tests/",
    "docs/",
]

BLOCKED_TARGET_PREFIXES = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def digest(data) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def path_blocked(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in BLOCKED_TARGET_PREFIXES)


def path_allowed(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in ALLOWED_TARGET_PREFIXES)


def scan_forbidden(obj):
    found = []

    def walk(value, pointer=""):
        if isinstance(value, dict):
            for k, v in value.items():
                key = str(k).lower()
                if key in FORBIDDEN_FIELDS:
                    found.append(pointer + str(k))
                walk(v, pointer + str(k) + ".")
        elif isinstance(value, list):
            for i, v in enumerate(value):
                walk(v, pointer + str(i) + ".")
        elif isinstance(value, str):
            s = value.lower()
            for forbidden in FORBIDDEN_FIELDS:
                if forbidden in s:
                    found.append(pointer.rstrip(".") + f":contains:{forbidden}")

    walk(obj)
    return sorted(set(found))


def validate_terminal_state(d104, d105):
    errors = []
    warnings = []

    if not d104:
        errors.append("missing D104 terminal safety state")
    else:
        if d104.get("ok") is not True:
            errors.append("D104 terminal ok must be true")
        if d104.get("terminal_decision") != REQ_D104_TERMINAL:
            errors.append("D104 terminal decision must be sealed")
        for key in [
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "external_ai_called",
            "network_accessed",
            "git_commit_by_ai",
            "rollback_executed",
            "restore_executed",
            "ai_autonomous_execution_allowed",
        ]:
            if d104.get(key) is not False:
                errors.append(f"D104 terminal {key} must be false")
        if d104.get("human_review_required_for_any_future_execution") is not True:
            errors.append("D104 must require human review for future execution")

    if not d105:
        warnings.append("D105 doc report missing; boundary can still be created but docs should exist")
    elif d105.get("ok") is not True:
        warnings.append("D105 doc report exists but ok is not true")

    return errors, warnings


def make_input_contract(boundary_id):
    return {
        "state": "D106_PROVIDER_INPUT_CONTRACT",
        "ok": True,
        "boundary_id": boundary_id,
        "mode": "AI_PROVIDER_INPUT_PROPOSE_ONLY",
        "created_at": now(),
        "required_input_fields": [
            "request_id", "task_intent", "human_prompt",
            "allowed_scope", "blocked_scope", "expected_output_contract",
        ],
        "blocked_input_fields": FORBIDDEN_FIELDS,
        "allowed_scope": ALLOWED_TARGET_PREFIXES,
        "blocked_scope": BLOCKED_TARGET_PREFIXES,
        "real_provider_allowed_now": False,
        "mock_provider_only": True,
    }


def make_output_contract(boundary_id):
    return {
        "state": "D106_PROVIDER_OUTPUT_CONTRACT",
        "ok": True,
        "boundary_id": boundary_id,
        "mode": "AI_PROVIDER_OUTPUT_JSON_ONLY",
        "created_at": now(),
        "format": "json",
        "required_output_fields": REQUIRED_OUTPUT_FIELDS,
        "allowed_proposal_types": ALLOWED_PROPOSAL_TYPES,
        "forbidden_fields": FORBIDDEN_FIELDS,
        "forbidden_actions": FORBIDDEN_ACTIONS,
        "candidate_files_must_match_allowed_prefix": True,
        "candidate_files_must_not_match_blocked_prefix": True,
        "requires_human_review_must_be_true": True,
        "next_required_gate": "D107_PROPOSAL_SCHEMA_VALIDATOR",
    }


def make_forbidden_matrix(boundary_id):
    return {
        "state": "D106_FORBIDDEN_ACTION_MATRIX",
        "ok": True,
        "boundary_id": boundary_id,
        "created_at": now(),
        "forbidden_actions": {x: True for x in FORBIDDEN_ACTIONS},
        "forbidden_fields": {x: True for x in FORBIDDEN_FIELDS},
        "blocked_paths": BLOCKED_TARGET_PREFIXES,
        "allowed_paths_for_proposals_only": ALLOWED_TARGET_PREFIXES,
        "ai_may_call_network": False,
        "ai_may_use_secrets": False,
        "ai_may_execute_shell": False,
        "ai_may_apply_patch": False,
        "ai_may_commit_or_push": False,
        "ai_may_mutate_protected_core": False,
    }


def make_d107_scope(boundary_id):
    return {
        "state": "D106_D107_PROPOSAL_SCHEMA_VALIDATOR_SCOPE",
        "ok": True,
        "boundary_id": boundary_id,
        "created_at": now(),
        "allowed_next_gate": "D107_PROPOSAL_SCHEMA_VALIDATOR",
        "d107_allowed_to_create": [
            "proposal_schema_validator",
            "proposal_contract_report",
            "proposal_rejection_report",
            "proposal_acceptance_manifest",
        ],
        "d107_must_not_execute": FORBIDDEN_ACTIONS + [
            "call_real_ai_provider",
            "read_api_key",
            "write_patch_to_core",
            "write_patch_to_runtime",
        ],
        "proposal_contract": {
            "required_output_fields": REQUIRED_OUTPUT_FIELDS,
            "allowed_proposal_types": ALLOWED_PROPOSAL_TYPES,
            "allowed_candidate_prefixes": ALLOWED_TARGET_PREFIXES,
            "blocked_candidate_prefixes": BLOCKED_TARGET_PREFIXES,
        },
        "required_phrase_for_later_gate": "APPROVE_D107_PROPOSAL_SCHEMA_VALIDATOR_ONLY",
    }


def make_mock_provider_response(task_intent: str, human_prompt: str):
    return {
        "proposal_id": "mock-proposal-" + digest({"intent": task_intent, "prompt": human_prompt}),
        "proposal_type": "analysis_proposal",
        "intent": task_intent,
        "target_scope": "runtime_experimental/ai_sandbox_work/",
        "candidate_files": [],
        "risk_flags": [
            "mock_provider_only",
            "no_real_ai_network_call",
            "proposal_requires_d107_validation",
        ],
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "shell_executed": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "git_commit_by_ai": False,
        },
        "validation_plan": [
            "D107 validates JSON schema",
            "D107 rejects forbidden fields/actions",
            "D108 may write only to sandbox after D107",
        ],
        "requires_human_review": True,
    }


def validate_provider_response(response):
    errors = []

    forbidden = scan_forbidden(response)
    if forbidden:
        errors.append("forbidden keys/content detected: " + ", ".join(forbidden))

    for field in REQUIRED_OUTPUT_FIELDS:
        if field not in response:
            errors.append(f"missing required field: {field}")

    if response.get("proposal_type") not in ALLOWED_PROPOSAL_TYPES:
        errors.append("invalid proposal_type")

    if response.get("requires_human_review") is not True:
        errors.append("requires_human_review must be true")

    target = str(response.get("target_scope", ""))
    if target:
        if path_blocked(target):
            errors.append("target_scope uses blocked prefix")
        if not path_allowed(target):
            errors.append("target_scope must use allowed proposal prefix")

    files = response.get("candidate_files", [])
    if not isinstance(files, list):
        errors.append("candidate_files must be list")
    else:
        for path in files:
            path = str(path)
            if path_blocked(path):
                errors.append(f"candidate file uses blocked prefix: {path}")
            if path and not path_allowed(path):
                errors.append(f"candidate file not under allowed prefix: {path}")

    guard = response.get("guardrails", {})
    if not isinstance(guard, dict):
        errors.append("guardrails must be object")
    else:
        for key in [
            "external_ai_called",
            "network_accessed",
            "shell_executed",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "git_commit_by_ai",
        ]:
            if guard.get(key) is not False:
                errors.append(f"guardrails.{key} must be false")

    return errors


def create_ai_provider_boundary(root="."):
    root = Path(root).resolve()
    d104 = read_json(root / D104_TERMINAL, {}) or {}
    d105 = read_json(root / D105_DOC_REPORT, {}) or {}

    errors, warnings = validate_terminal_state(d104, d105)

    boundary_id = "d106-" + digest({
        "ledger_id": d104.get("ledger_id"),
        "terminal": d104.get("terminal_decision"),
        "doc_sha": d105.get("doc_sha256"),
    })

    input_contract = make_input_contract(boundary_id)
    output_contract = make_output_contract(boundary_id)
    forbidden_matrix = make_forbidden_matrix(boundary_id)
    d107_scope = make_d107_scope(boundary_id)

    mock_response = make_mock_provider_response(
        "bootstrap_ai_propose_only_loop",
        "Create a safe AI provider boundary that can only return JSON proposals.",
    )
    errors.extend([f"mock_response: {e}" for e in validate_provider_response(mock_response)])

    ok = not errors
    decision = "AI_PROVIDER_BOUNDARY_READY" if ok else "AI_PROVIDER_BOUNDARY_BLOCKED"
    result = "D106_AI_PROVIDER_BOUNDARY_CREATED" if ok else "D106_AI_PROVIDER_BOUNDARY_BLOCKED"

    if ok:
        write_json(root / INPUT_CONTRACT, input_contract)
        write_json(root / OUTPUT_CONTRACT, output_contract)
        write_json(root / FORBIDDEN_MATRIX, forbidden_matrix)
        write_json(root / D107_SCOPE, d107_scope)

    report = {
        "state": "D106_AI_PROVIDER_BOUNDARY",
        "result": result,
        "route": "FIELD_INTENT_AI_PROPOSE_ONLY_PROVIDER_BOUNDARY",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "boundary_id": boundary_id,
        "source_terminal_state": D104_TERMINAL,
        "source_doc_report": D105_DOC_REPORT,
        "input_contract": input_contract if ok else {},
        "output_contract": output_contract if ok else {},
        "forbidden_action_matrix": forbidden_matrix if ok else {},
        "d107_scope": d107_scope if ok else {},
        "mock_provider_response": mock_response,
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_executed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
            "mock_provider_only": True,
            "json_only": True,
            "proposal_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "boundary_id": boundary_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
            "next_step": "D107_PROPOSAL_SCHEMA_VALIDATOR",
        },
        "success_condition": {
            "provider_boundary_created": ok,
            "input_contract_created": ok,
            "output_contract_created": ok,
            "forbidden_matrix_created": ok,
            "mock_provider_only": True,
            "real_provider_called": False,
            "actual_apply_executed": False,
            "protected_core_untouched": True,
            "next_step": "D107 can validate AI proposal JSON before any sandbox writer sees it.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_ai_provider_boundary(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.ai_propose_only_provider_boundary import (
    create_ai_provider_boundary,
    make_mock_provider_response,
    validate_provider_response,
)


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD106AIProposeOnlyProviderBoundary(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        write(root / "reports/d104_terminal_safety_state.json", {
            "ok": True,
            "ledger_id": "d104-test",
            "builder_id": "d103-test",
            "terminal_decision": "GUARDED_AUTONOMY_PRE_EXECUTION_CHAIN_SEALED",
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
            "ai_autonomous_execution_allowed": False,
            "human_review_required_for_any_future_execution": True,
        })

        write(root / "reports/d105_guarded_autonomy_chain_doc.json", {
            "ok": True,
            "doc_sha256": "abc",
            "main_readme_modified": False,
        })

        return td, root

    def test_creates_boundary_and_contracts(self):
        td, root = self.root()
        try:
            r = create_ai_provider_boundary(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "AI_PROVIDER_BOUNDARY_READY")
            self.assertTrue(r["guardrails"]["mock_provider_only"])
            self.assertTrue(r["guardrails"]["json_only"])
            self.assertTrue(r["guardrails"]["proposal_only"])
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertEqual(r["d107_scope"]["allowed_next_gate"], "D107_PROPOSAL_SCHEMA_VALIDATOR")
            self.assertTrue((root / "reports/d106_ai_provider_boundary.json").exists())
            self.assertTrue((root / "reports/d106_provider_input_contract.json").exists())
            self.assertTrue((root / "reports/d106_provider_output_contract.json").exists())
            self.assertTrue((root / "reports/d106_forbidden_action_matrix.json").exists())
            self.assertTrue((root / "reports/d106_d107_proposal_schema_validator_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_if_d104_missing(self):
        td, root = self.root()
        try:
            (root / "reports/d104_terminal_safety_state.json").unlink()
            r = create_ai_provider_boundary(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "AI_PROVIDER_BOUNDARY_BLOCKED")
        finally:
            td.cleanup()

    def test_rejects_forbidden_payload(self):
        payload = make_mock_provider_response("x", "y")
        payload["raw_shell_command"] = "git push"
        errors = validate_provider_response(payload)
        self.assertTrue(errors)

    def test_rejects_blocked_candidate_path(self):
        payload = make_mock_provider_response("x", "y")
        payload["candidate_files"] = ["core/evil.py"]
        errors = validate_provider_response(payload)
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
"""


def sh(cmd, check=False):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, text=True, capture_output=False, check=check)


def repo_root():
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p
    return here


ROOT = repo_root()
os.chdir(ROOT)
Path("runtime_experimental").mkdir(exist_ok=True)
Path("tests").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)

print("D106 AI PROPOSE-ONLY PROVIDER BOUNDARY BOOT: repo =", ROOT)

Path("runtime_experimental/ai_propose_only_provider_boundary.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d106_ai_propose_only_provider_boundary.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/ai_propose_only_provider_boundary.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d106_ai_propose_only_provider_boundary", "-v"], check=True)

print("\n== run D106 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.ai_propose_only_provider_boundary import create_ai_provider_boundary\n"
    "r=create_ai_provider_boundary()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/ai_propose_only_provider_boundary.py",
    "tests/test_d106_ai_propose_only_provider_boundary.py",
    "reports/d106_ai_provider_boundary.json",
    "reports/d106_provider_input_contract.json",
    "reports/d106_provider_output_contract.json",
    "reports/d106_forbidden_action_matrix.json",
    "reports/d106_d107_proposal_schema_validator_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D106_AI_PROPOSE_ONLY_PROVIDER_BOUNDARY_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D106 AI propose-only provider boundary"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D106 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD106 AI PROPOSE-ONLY PROVIDER BOUNDARY BOOT DONE")
