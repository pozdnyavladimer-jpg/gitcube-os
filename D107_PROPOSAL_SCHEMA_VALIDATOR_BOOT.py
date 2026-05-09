#!/usr/bin/env python3
# D107_PROPOSAL_SCHEMA_VALIDATOR_BOOT.py
#
# Creates D107 Proposal Schema Validator.
#
# D107 validates AI JSON proposals after D106 AI Provider Boundary and before D108 Sandbox Writer.
#
# It creates:
# - runtime_experimental/proposal_schema_validator.py
# - tests/test_d107_proposal_schema_validator.py
# - reports/d107_proposal_schema_validator.json
# - reports/d107_proposal_contract_report.json
# - reports/d107_mock_valid_proposal.json
# - reports/d107_rejection_report.json
# - reports/d107_acceptance_manifest.json
# - reports/d107_d108_sandbox_proposal_writer_scope.json
#
# This is validation-only.
# It does NOT call real AI.
# It does NOT read API keys/secrets.
# It does NOT execute shell/subprocess from proposals.
# It does NOT apply patches.
# It does NOT write proposal files to sandbox yet.
# It does NOT mutate core/runtime/app/memory/routes.
# It does NOT commit/push by AI.

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


MODULE = r"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D106_BOUNDARY = "reports/d106_ai_provider_boundary.json"
D106_INPUT_CONTRACT = "reports/d106_provider_input_contract.json"
D106_OUTPUT_CONTRACT = "reports/d106_provider_output_contract.json"
D106_FORBIDDEN_MATRIX = "reports/d106_forbidden_action_matrix.json"
D106_D107_SCOPE = "reports/d106_d107_proposal_schema_validator_scope.json"

OUT = "reports/d107_proposal_schema_validator.json"
CONTRACT_REPORT_OUT = "reports/d107_proposal_contract_report.json"
MOCK_VALID_PROPOSAL_OUT = "reports/d107_mock_valid_proposal.json"
REJECTION_REPORT_OUT = "reports/d107_rejection_report.json"
ACCEPTANCE_MANIFEST_OUT = "reports/d107_acceptance_manifest.json"
D108_SCOPE_OUT = "reports/d107_d108_sandbox_proposal_writer_scope.json"

REQ_D106_DECISION = "AI_PROVIDER_BOUNDARY_READY"
REQ_D107_GATE = "D107_PROPOSAL_SCHEMA_VALIDATOR"
REQ_D108_GATE = "D108_SANDBOX_PROPOSAL_WRITER"

DEFAULT_REQUIRED_FIELDS = [
    "proposal_id",
    "proposal_type",
    "intent",
    "target_scope",
    "candidate_files",
    "risk_flags",
    "guardrails",
    "validation_plan",
    "requires_human_review",
]

DEFAULT_ALLOWED_PROPOSAL_TYPES = [
    "documentation_proposal",
    "test_proposal",
    "sandbox_patch_proposal",
    "analysis_proposal",
    "schema_proposal",
]

DEFAULT_FORBIDDEN_FIELDS = [
    "api_key",
    "api_secret",
    "token",
    "password",
    "raw_shell_command",
    "shell_command",
    "subprocess",
    "exec",
    "eval",
    "auto_apply",
    "apply_now",
    "git_commit",
    "git_push",
    "route_insert",
    "protected_core_mutation",
    "canonical_memory_overwrite",
    "direct_core_edit",
]

DEFAULT_FORBIDDEN_ACTIONS = [
    "real_apply",
    "auto_apply",
    "route_insert",
    "protected_core_mutation",
    "canonical_memory_overwrite",
    "external_ai_network_call",
    "shell_exec",
    "subprocess_exec",
    "git_commit_by_ai",
    "git_push_by_ai",
    "rollback_execute",
    "restore_execute",
    "delete_runtime_candidate",
]

DEFAULT_ALLOWED_PREFIXES = [
    "runtime_experimental/ai_sandbox_work/",
    "reports/",
    "tests/",
    "docs/",
]

DEFAULT_BLOCKED_PREFIXES = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]

GUARDRAIL_FALSE_KEYS = [
    "external_ai_called",
    "network_accessed",
    "shell_executed",
    "actual_apply_executed",
    "route_inserted",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "git_commit_by_ai",
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


def as_list(value, default):
    return value if isinstance(value, list) and value else list(default)


def load_contracts(root: Path):
    boundary = read_json(root / D106_BOUNDARY, {}) or {}
    input_contract = read_json(root / D106_INPUT_CONTRACT, {}) or {}
    output_contract = read_json(root / D106_OUTPUT_CONTRACT, {}) or {}
    forbidden_matrix = read_json(root / D106_FORBIDDEN_MATRIX, {}) or {}
    scope = read_json(root / D106_D107_SCOPE, {}) or {}

    output_embedded = boundary.get("output_contract") if isinstance(boundary.get("output_contract"), dict) else {}
    scope_contract = scope.get("proposal_contract") if isinstance(scope.get("proposal_contract"), dict) else {}

    required_fields = as_list(
        output_contract.get("required_output_fields") or output_embedded.get("required_output_fields") or scope_contract.get("required_output_fields"),
        DEFAULT_REQUIRED_FIELDS,
    )
    allowed_types = as_list(
        output_contract.get("allowed_proposal_types") or output_embedded.get("allowed_proposal_types") or scope_contract.get("allowed_proposal_types"),
        DEFAULT_ALLOWED_PROPOSAL_TYPES,
    )
    forbidden_fields = as_list(
        output_contract.get("forbidden_fields") or output_embedded.get("forbidden_fields"),
        DEFAULT_FORBIDDEN_FIELDS,
    )
    forbidden_actions = as_list(
        output_contract.get("forbidden_actions") or output_embedded.get("forbidden_actions"),
        DEFAULT_FORBIDDEN_ACTIONS,
    )
    allowed_prefixes = as_list(
        scope_contract.get("allowed_candidate_prefixes")
        or output_contract.get("allowed_candidate_prefixes")
        or input_contract.get("allowed_scope"),
        DEFAULT_ALLOWED_PREFIXES,
    )
    blocked_prefixes = as_list(
        scope_contract.get("blocked_candidate_prefixes")
        or output_contract.get("blocked_candidate_prefixes")
        or input_contract.get("blocked_scope"),
        DEFAULT_BLOCKED_PREFIXES,
    )

    return {
        "boundary": boundary,
        "input_contract": input_contract,
        "output_contract": output_contract,
        "forbidden_matrix": forbidden_matrix,
        "scope": scope,
        "required_fields": required_fields,
        "allowed_types": allowed_types,
        "forbidden_fields": forbidden_fields,
        "forbidden_actions": forbidden_actions,
        "allowed_prefixes": allowed_prefixes,
        "blocked_prefixes": blocked_prefixes,
    }


def validate_d106(contracts):
    errors = []
    warnings = []

    boundary = contracts["boundary"]
    input_contract = contracts["input_contract"]
    output_contract = contracts["output_contract"]
    forbidden_matrix = contracts["forbidden_matrix"]
    scope = contracts["scope"]

    if not boundary:
        errors.append("missing D106 AI provider boundary")
    else:
        if boundary.get("ok") is not True:
            errors.append("D106 boundary ok must be true")
        if boundary.get("decision") != REQ_D106_DECISION:
            errors.append(f"D106 decision invalid: {boundary.get('decision')}")
        guard = boundary.get("guardrails") if isinstance(boundary.get("guardrails"), dict) else {}
        for key in [
            "external_ai_called",
            "network_accessed",
            "api_key_read",
            "secret_read",
            "shell_executed",
            "runtime_code_mutated",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "actual_apply_executed",
            "route_inserted",
            "git_commit_by_ai",
            "rollback_executed",
            "restore_executed",
        ]:
            if guard.get(key) is not False:
                errors.append(f"D106 guardrails.{key} must be false")
        for key in ["mock_provider_only", "json_only", "proposal_only"]:
            if guard.get(key) is not True:
                errors.append(f"D106 guardrails.{key} must be true")

    for label, data in [
        ("D106 input contract", input_contract),
        ("D106 output contract", output_contract),
        ("D106 forbidden matrix", forbidden_matrix),
        ("D106 D107 scope", scope),
    ]:
        if not data:
            errors.append(f"missing {label}")
        elif data.get("ok") is not True:
            errors.append(f"{label} ok must be true")

    if scope:
        if scope.get("allowed_next_gate") != REQ_D107_GATE:
            errors.append("D106 D107 scope allowed_next_gate must be D107")
        for item in [
            "proposal_schema_validator",
            "proposal_contract_report",
            "proposal_rejection_report",
            "proposal_acceptance_manifest",
        ]:
            if item not in scope.get("d107_allowed_to_create", []):
                errors.append(f"D106 D107 scope missing allowed item: {item}")

    return errors, warnings


def contains_forbidden(obj, forbidden_fields, forbidden_actions):
    found = []
    tokens = set(str(x).lower() for x in list(forbidden_fields) + list(forbidden_actions))

    def walk(x, path=""):
        if isinstance(x, dict):
            for k, v in x.items():
                k_text = str(k)
                if k_text.lower() in tokens:
                    found.append(path + k_text)
                walk(v, path + k_text + ".")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, path + f"{i}.")
        elif isinstance(x, str):
            s = x.lower()
            for token in tokens:
                if token and token in s:
                    found.append(path.rstrip(".") + f":contains:{token}")

    walk(obj)
    return sorted(set(found))


def path_is_allowed(path, allowed_prefixes):
    return any(str(path).startswith(prefix) for prefix in allowed_prefixes)


def path_is_blocked(path, blocked_prefixes):
    return any(str(path).startswith(prefix) for prefix in blocked_prefixes)


def validate_ai_proposal(proposal, contract):
    errors = []
    warnings = []

    if not isinstance(proposal, dict):
        return ["proposal must be a JSON object"], warnings

    required_fields = contract.get("required_fields", DEFAULT_REQUIRED_FIELDS)
    allowed_types = contract.get("allowed_types", DEFAULT_ALLOWED_PROPOSAL_TYPES)
    forbidden_fields = contract.get("forbidden_fields", DEFAULT_FORBIDDEN_FIELDS)
    forbidden_actions = contract.get("forbidden_actions", DEFAULT_FORBIDDEN_ACTIONS)
    allowed_prefixes = contract.get("allowed_prefixes", DEFAULT_ALLOWED_PREFIXES)
    blocked_prefixes = contract.get("blocked_prefixes", DEFAULT_BLOCKED_PREFIXES)

    for field in required_fields:
        if field not in proposal:
            errors.append(f"missing required field: {field}")

    forbidden_hits = contains_forbidden(proposal, forbidden_fields, forbidden_actions)
    if forbidden_hits:
        errors.append("forbidden field/action/content detected: " + ", ".join(forbidden_hits[:20]))

    proposal_type = proposal.get("proposal_type")
    if proposal_type not in allowed_types:
        errors.append(f"invalid proposal_type: {proposal_type}")

    if proposal.get("requires_human_review") is not True:
        errors.append("requires_human_review must be true")

    target_scope = str(proposal.get("target_scope", ""))
    if not target_scope:
        errors.append("target_scope is required")
    elif path_is_blocked(target_scope, blocked_prefixes):
        errors.append(f"target_scope is blocked: {target_scope}")
    elif not path_is_allowed(target_scope, allowed_prefixes):
        errors.append(f"target_scope is not under allowed prefixes: {target_scope}")

    candidate_files = proposal.get("candidate_files")
    if not isinstance(candidate_files, list):
        errors.append("candidate_files must be a list")
    else:
        for item in candidate_files:
            if not isinstance(item, str) or not item:
                errors.append("candidate_files entries must be non-empty strings")
                continue
            if path_is_blocked(item, blocked_prefixes):
                errors.append(f"candidate file is blocked: {item}")
            elif not path_is_allowed(item, allowed_prefixes):
                errors.append(f"candidate file not under allowed prefixes: {item}")

    risk_flags = proposal.get("risk_flags")
    if not isinstance(risk_flags, list):
        errors.append("risk_flags must be a list")

    validation_plan = proposal.get("validation_plan")
    if not isinstance(validation_plan, list) or not validation_plan:
        errors.append("validation_plan must be a non-empty list")

    guardrails = proposal.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append("guardrails must be an object")
    else:
        for key in GUARDRAIL_FALSE_KEYS:
            if guardrails.get(key) is not False:
                errors.append(f"guardrails.{key} must be false")

    return errors, warnings


def make_mock_valid_proposal():
    return {
        "proposal_id": "d107-valid-proposal-" + digest({"gate": "D107", "type": "valid"}),
        "proposal_type": "analysis_proposal",
        "intent": "validate_ai_proposal_json_before_sandbox_writer",
        "target_scope": "runtime_experimental/ai_sandbox_work/",
        "candidate_files": [
            "runtime_experimental/ai_sandbox_work/proposal_manifest.json"
        ],
        "risk_flags": [
            "proposal_only",
            "requires_human_review",
            "sandbox_writer_not_yet_invoked",
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
            "Validate required JSON fields",
            "Reject forbidden fields/actions",
            "Reject blocked target paths",
            "Require human review before D108",
        ],
        "requires_human_review": True,
    }


def make_mock_invalid_proposal():
    return {
        "proposal_id": "d107-invalid-proposal-" + digest({"gate": "D107", "type": "invalid"}),
        "proposal_type": "sandbox_patch_proposal",
        "intent": "should_be_rejected",
        "target_scope": "core/",
        "candidate_files": ["core/secret_patch.py"],
        "risk_flags": ["malformed"],
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
        "validation_plan": ["This should fail."],
        "requires_human_review": True,
        "raw_shell_command": "git push",
    }


def build_contract_report(validator_id, contracts):
    return {
        "state": "D107_PROPOSAL_CONTRACT_REPORT",
        "ok": True,
        "validator_id": validator_id,
        "created_at": now(),
        "required_fields": contracts["required_fields"],
        "allowed_proposal_types": contracts["allowed_types"],
        "forbidden_fields": contracts["forbidden_fields"],
        "forbidden_actions": contracts["forbidden_actions"],
        "allowed_candidate_prefixes": contracts["allowed_prefixes"],
        "blocked_candidate_prefixes": contracts["blocked_prefixes"],
        "requires_human_review_must_be_true": True,
        "json_only": True,
        "next_required_gate": REQ_D108_GATE,
    }


def build_acceptance_manifest(validator_id, valid_proposal):
    return {
        "state": "D107_ACCEPTANCE_MANIFEST",
        "ok": True,
        "validator_id": validator_id,
        "created_at": now(),
        "accepted_proposal_id": valid_proposal.get("proposal_id"),
        "accepted_proposal_type": valid_proposal.get("proposal_type"),
        "accepted_target_scope": valid_proposal.get("target_scope"),
        "accepted_candidate_files": valid_proposal.get("candidate_files", []),
        "accepted_for": "D108_SANDBOX_PROPOSAL_WRITER_ONLY",
        "actual_apply_executed": False,
        "sandbox_write_executed": False,
        "protected_core_mutated": False,
        "route_inserted": False,
        "requires_human_review": True,
    }


def build_rejection_report(validator_id, invalid_proposal, rejection_errors):
    return {
        "state": "D107_REJECTION_REPORT",
        "ok": True,
        "validator_id": validator_id,
        "created_at": now(),
        "rejected_proposal_id": invalid_proposal.get("proposal_id"),
        "rejected": True,
        "rejection_errors": rejection_errors,
        "rejected_for": [
            "blocked target path",
            "forbidden shell/git command content",
            "protected core candidate file",
        ],
        "actual_apply_executed": False,
        "sandbox_write_executed": False,
        "protected_core_mutated": False,
        "route_inserted": False,
    }


def build_d108_scope(validator_id, valid_proposal):
    return {
        "state": "D107_D108_SANDBOX_PROPOSAL_WRITER_SCOPE",
        "ok": True,
        "validator_id": validator_id,
        "created_at": now(),
        "allowed_next_gate": REQ_D108_GATE,
        "accepted_proposal_id": valid_proposal.get("proposal_id"),
        "d108_allowed_to_create": [
            "sandbox_proposal_writer",
            "sandbox_proposal_manifest",
            "sandbox_candidate_copy",
            "sandbox_writer_receipt",
        ],
        "d108_must_not_execute": DEFAULT_FORBIDDEN_ACTIONS + [
            "call_real_ai_provider",
            "read_api_key",
            "write_patch_to_core",
            "write_patch_to_runtime",
            "write_patch_to_app_orchestration",
            "execute_candidate",
            "commit_candidate",
        ],
        "allowed_write_prefixes": [
            "runtime_experimental/ai_sandbox_work/",
            "reports/",
        ],
        "blocked_write_prefixes": DEFAULT_BLOCKED_PREFIXES,
        "sandbox_write_allowed_after_d107": True,
        "actual_apply_allowed_after_d107": False,
        "route_insert_allowed_after_d107": False,
        "protected_core_mutation_allowed_after_d107": False,
        "required_phrase_for_later_gate": "APPROVE_D108_SANDBOX_PROPOSAL_WRITER_ONLY",
    }


def create_proposal_schema_validator(root="."):
    root = Path(root).resolve()
    contracts = load_contracts(root)

    d106_errors, warnings = validate_d106(contracts)

    validator_id = "d107-" + digest({
        "boundary_id": contracts["boundary"].get("boundary_id"),
        "required_fields": contracts["required_fields"],
        "allowed_types": contracts["allowed_types"],
    })

    valid_proposal = make_mock_valid_proposal()
    invalid_proposal = make_mock_invalid_proposal()

    valid_errors, valid_warnings = validate_ai_proposal(valid_proposal, contracts)
    invalid_errors, _invalid_warnings = validate_ai_proposal(invalid_proposal, contracts)

    errors = list(d106_errors)
    if valid_errors:
        errors.extend([f"valid_mock_proposal: {e}" for e in valid_errors])
    if not invalid_errors:
        errors.append("invalid_mock_proposal was not rejected")

    ok = not errors
    decision = "PROPOSAL_SCHEMA_VALIDATOR_READY" if ok else "PROPOSAL_SCHEMA_VALIDATOR_BLOCKED"
    result = "D107_PROPOSAL_SCHEMA_VALIDATOR_CREATED" if ok else "D107_PROPOSAL_SCHEMA_VALIDATOR_BLOCKED"

    contract_report = build_contract_report(validator_id, contracts)
    acceptance_manifest = build_acceptance_manifest(validator_id, valid_proposal)
    rejection_report = build_rejection_report(validator_id, invalid_proposal, invalid_errors)
    d108_scope = build_d108_scope(validator_id, valid_proposal)

    if ok:
        write_json(root / CONTRACT_REPORT_OUT, contract_report)
        write_json(root / MOCK_VALID_PROPOSAL_OUT, valid_proposal)
        write_json(root / REJECTION_REPORT_OUT, rejection_report)
        write_json(root / ACCEPTANCE_MANIFEST_OUT, acceptance_manifest)
        write_json(root / D108_SCOPE_OUT, d108_scope)

    report = {
        "state": "D107_PROPOSAL_SCHEMA_VALIDATOR",
        "result": result,
        "route": "FIELD_INTENT_PROPOSAL_SCHEMA_VALIDATOR",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "validator_id": validator_id,
        "boundary_id": contracts["boundary"].get("boundary_id"),
        "source_boundary_report": D106_BOUNDARY,
        "source_output_contract": D106_OUTPUT_CONTRACT,
        "contract_report": contract_report if ok else {},
        "mock_valid_proposal": valid_proposal,
        "valid_proposal_validation": {
            "ok": not valid_errors,
            "errors": valid_errors,
            "warnings": valid_warnings,
        },
        "mock_invalid_proposal": invalid_proposal,
        "invalid_proposal_validation": {
            "rejected": bool(invalid_errors),
            "errors": invalid_errors,
        },
        "acceptance_manifest": acceptance_manifest if ok else {},
        "rejection_report": rejection_report if ok else {},
        "d108_scope": d108_scope if ok else {},
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
            "schema_validation_only": True,
            "sandbox_writer_not_called": True,
            "proposal_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "validator_id": validator_id,
            "boundary_id": contracts["boundary"].get("boundary_id"),
            "valid_mock_accepted": not valid_errors,
            "invalid_mock_rejected": bool(invalid_errors),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
            "next_step": REQ_D108_GATE,
        },
        "success_condition": {
            "proposal_schema_validator_created": ok,
            "contract_report_created": ok,
            "valid_mock_proposal_created": ok,
            "rejection_report_created": ok,
            "acceptance_manifest_created": ok,
            "real_ai_called": False,
            "sandbox_write_executed": False,
            "actual_apply_executed": False,
            "protected_core_untouched": True,
            "next_step": "D108 may write the accepted validated JSON proposal into sandbox only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_proposal_schema_validator(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.proposal_schema_validator import (
    create_proposal_schema_validator,
    load_contracts,
    make_mock_valid_proposal,
    make_mock_invalid_proposal,
    validate_ai_proposal,
)


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD107ProposalSchemaValidator(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        forbidden_fields = [
            "api_key",
            "api_secret",
            "token",
            "password",
            "raw_shell_command",
            "shell_command",
            "subprocess",
            "exec",
            "eval",
            "auto_apply",
            "apply_now",
            "git_commit",
            "git_push",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "direct_core_edit",
        ]
        forbidden_actions = [
            "real_apply",
            "auto_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "shell_exec",
            "subprocess_exec",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute",
            "restore_execute",
            "delete_runtime_candidate",
        ]
        allowed_prefixes = [
            "runtime_experimental/ai_sandbox_work/",
            "reports/",
            "tests/",
            "docs/",
        ]
        blocked_prefixes = [
            "app/orchestration/",
            "core/",
            "runtime/",
            "bridges/",
            "memory/",
        ]
        required_fields = [
            "proposal_id",
            "proposal_type",
            "intent",
            "target_scope",
            "candidate_files",
            "risk_flags",
            "guardrails",
            "validation_plan",
            "requires_human_review",
        ]
        allowed_types = [
            "documentation_proposal",
            "test_proposal",
            "sandbox_patch_proposal",
            "analysis_proposal",
            "schema_proposal",
        ]

        write(root / "reports/d106_ai_provider_boundary.json", {
            "ok": True,
            "decision": "AI_PROVIDER_BOUNDARY_READY",
            "boundary_id": "d106-test",
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
        })
        write(root / "reports/d106_provider_input_contract.json", {
            "ok": True,
            "allowed_scope": allowed_prefixes,
            "blocked_scope": blocked_prefixes,
        })
        write(root / "reports/d106_provider_output_contract.json", {
            "ok": True,
            "required_output_fields": required_fields,
            "allowed_proposal_types": allowed_types,
            "forbidden_fields": forbidden_fields,
            "forbidden_actions": forbidden_actions,
        })
        write(root / "reports/d106_forbidden_action_matrix.json", {
            "ok": True,
            "forbidden_actions": {x: True for x in forbidden_actions},
            "forbidden_fields": {x: True for x in forbidden_fields},
        })
        write(root / "reports/d106_d107_proposal_schema_validator_scope.json", {
            "ok": True,
            "allowed_next_gate": "D107_PROPOSAL_SCHEMA_VALIDATOR",
            "d107_allowed_to_create": [
                "proposal_schema_validator",
                "proposal_contract_report",
                "proposal_rejection_report",
                "proposal_acceptance_manifest",
            ],
            "proposal_contract": {
                "required_output_fields": required_fields,
                "allowed_proposal_types": allowed_types,
                "allowed_candidate_prefixes": allowed_prefixes,
                "blocked_candidate_prefixes": blocked_prefixes,
            },
        })

        return td, root

    def test_creates_validator_reports(self):
        td, root = self.root()
        try:
            r = create_proposal_schema_validator(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "PROPOSAL_SCHEMA_VALIDATOR_READY")
            self.assertTrue(r["summary"]["valid_mock_accepted"])
            self.assertTrue(r["summary"]["invalid_mock_rejected"])
            self.assertEqual(r["d108_scope"]["allowed_next_gate"], "D108_SANDBOX_PROPOSAL_WRITER")
            self.assertTrue((root / "reports/d107_proposal_schema_validator.json").exists())
            self.assertTrue((root / "reports/d107_proposal_contract_report.json").exists())
            self.assertTrue((root / "reports/d107_mock_valid_proposal.json").exists())
            self.assertTrue((root / "reports/d107_rejection_report.json").exists())
            self.assertTrue((root / "reports/d107_acceptance_manifest.json").exists())
            self.assertTrue((root / "reports/d107_d108_sandbox_proposal_writer_scope.json").exists())
        finally:
            td.cleanup()

    def test_accepts_valid_proposal(self):
        td, root = self.root()
        try:
            contract = load_contracts(root)
            proposal = make_mock_valid_proposal()
            errors, warnings = validate_ai_proposal(proposal, contract)
            self.assertEqual(errors, [])
        finally:
            td.cleanup()

    def test_rejects_forbidden_shell_field(self):
        td, root = self.root()
        try:
            contract = load_contracts(root)
            proposal = make_mock_valid_proposal()
            proposal["shell_command"] = "git push"
            errors, warnings = validate_ai_proposal(proposal, contract)
            self.assertTrue(errors)
        finally:
            td.cleanup()

    def test_rejects_blocked_core_path(self):
        td, root = self.root()
        try:
            contract = load_contracts(root)
            proposal = make_mock_valid_proposal()
            proposal["candidate_files"] = ["core/unsafe.py"]
            errors, warnings = validate_ai_proposal(proposal, contract)
            self.assertTrue(errors)
        finally:
            td.cleanup()

    def test_rejects_missing_human_review(self):
        td, root = self.root()
        try:
            contract = load_contracts(root)
            proposal = make_mock_valid_proposal()
            proposal["requires_human_review"] = False
            errors, warnings = validate_ai_proposal(proposal, contract)
            self.assertTrue(errors)
        finally:
            td.cleanup()

    def test_blocks_if_d106_missing(self):
        td, root = self.root()
        try:
            (root / "reports/d106_ai_provider_boundary.json").unlink()
            r = create_proposal_schema_validator(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "PROPOSAL_SCHEMA_VALIDATOR_BLOCKED")
        finally:
            td.cleanup()


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

print("D107 PROPOSAL SCHEMA VALIDATOR BOOT: repo =", ROOT)

Path("runtime_experimental/proposal_schema_validator.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d107_proposal_schema_validator.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/proposal_schema_validator.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d107_proposal_schema_validator", "-v"], check=True)

print("\n== run D107 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.proposal_schema_validator import create_proposal_schema_validator\n"
    "r=create_proposal_schema_validator()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d107_proposal_schema_validator.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/proposal_schema_validator.py",
    "tests/test_d107_proposal_schema_validator.py",
    "reports/d107_proposal_schema_validator.json",
    "reports/d107_proposal_contract_report.json",
    "reports/d107_mock_valid_proposal.json",
    "reports/d107_rejection_report.json",
    "reports/d107_acceptance_manifest.json",
    "reports/d107_d108_sandbox_proposal_writer_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D107_PROPOSAL_SCHEMA_VALIDATOR_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D107 proposal schema validator"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D107 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD107 PROPOSAL SCHEMA VALIDATOR BOOT DONE")
