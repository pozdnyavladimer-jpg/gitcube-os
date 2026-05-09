#!/usr/bin/env python3
# D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_BOOT.py
#
# Creates D125 Provider Response To Proposal Intake Scope.
#
# D125 consumes D124 dry provider ping / shape-probe artifacts and creates
# provider-response intake artifacts:
# - runtime_experimental/provider_response_to_proposal_intake_scope.py
# - tests/test_d125_provider_response_to_proposal_intake_scope.py
# - reports/d125_provider_response_to_proposal_intake_scope.json
# - reports/d125_provider_response_schema_validator.json
# - reports/d125_provider_intake_rejection_report.json
# - reports/d125_d126_proposal_to_sandbox_candidate_scope.json
#
# This is PROVIDER RESPONSE TO PROPOSAL INTAKE SCOPE ONLY.
# It does NOT call a real provider.
# It does NOT read API keys or secrets.
# It does NOT access network.
# It does NOT execute shell commands.
# It does NOT apply patches.
# It does NOT mutate protected runtime/core/memory/routes.
# It does NOT commit/push/tag by AI.
#
# D125 opens D126 Proposal To Sandbox Candidate Scope.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE = r'''
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D124_REPORT = "reports/d124_real_provider_dry_ping_scope.json"
D124_REQUEST_PROBE = "reports/d124_provider_request_shape_probe.json"
D124_RESPONSE_PROBE = "reports/d124_provider_response_shape_probe.json"
D124_D125_SCOPE = "reports/d124_d125_provider_response_to_proposal_intake_scope.json"

OUT = "reports/d125_provider_response_to_proposal_intake_scope.json"
SCHEMA_VALIDATOR_OUT = "reports/d125_provider_response_schema_validator.json"
REJECTION_REPORT_OUT = "reports/d125_provider_intake_rejection_report.json"
D126_SCOPE_OUT = "reports/d125_d126_proposal_to_sandbox_candidate_scope.json"

REQ_D124_DECISION = "REAL_PROVIDER_DRY_PING_SCOPE_READY"
REQ_D125_GATE = "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE"
REQ_D126_GATE = "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE"
REQ_D124_APPROVAL_SCOPE = "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_ONLY"

FALSE_GUARD_KEYS = [
    "external_ai_called",
    "network_accessed",
    "api_key_read",
    "secret_read",
    "shell_from_ai_executed",
    "runtime_code_mutated",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "actual_apply_executed",
    "route_inserted",
    "git_commit_by_ai",
    "git_push_by_ai",
    "rollback_executed",
    "restore_executed",
]

REQUIRED_PROPOSAL_FIELDS = [
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

ALLOWED_PROPOSAL_TYPES = [
    "documentation_proposal",
    "test_proposal",
    "sandbox_patch_proposal",
    "analysis_proposal",
    "schema_proposal",
]

FORBIDDEN_OUTPUT_FIELDS = [
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

BLOCKED_CANDIDATE_PREFIXES = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]

ALLOWED_CANDIDATE_PREFIXES = [
    "runtime_experimental/ai_sandbox_work/",
    "reports/",
    "tests/",
    "docs/",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


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


def contains_forbidden_output_field(obj):
    hits = []

    def walk(value, path=""):
        if isinstance(value, dict):
            for key, inner in value.items():
                key_s = str(key)
                low = key_s.lower()
                if low in FORBIDDEN_OUTPUT_FIELDS:
                    hits.append(f"forbidden key: {path}.{key_s}".strip("."))
                walk(inner, f"{path}.{key_s}".strip("."))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                walk(item, f"{path}[{i}]")
        elif isinstance(value, str):
            low = value.lower()
            for field in FORBIDDEN_OUTPUT_FIELDS:
                if field in low:
                    hits.append(f"forbidden text at {path}: {field}")
                    break

    walk(obj)
    return hits


def validate_proposal_shape(proposal):
    errors = []

    if not isinstance(proposal, dict):
        return ["proposal must be object"]

    for field in REQUIRED_PROPOSAL_FIELDS:
        if field not in proposal:
            errors.append(f"missing required proposal field: {field}")

    if proposal.get("proposal_type") not in ALLOWED_PROPOSAL_TYPES:
        errors.append("proposal_type is not allowed")

    if not isinstance(proposal.get("candidate_files", []), list):
        errors.append("candidate_files must be list")

    for item in proposal.get("candidate_files", []):
        if not isinstance(item, dict):
            errors.append("candidate_files entries must be objects")
            continue
        path = item.get("path", "")
        if any(str(path).startswith(prefix) for prefix in BLOCKED_CANDIDATE_PREFIXES):
            errors.append(f"candidate file targets blocked prefix: {path}")
        if path and not any(str(path).startswith(prefix) for prefix in ALLOWED_CANDIDATE_PREFIXES):
            errors.append(f"candidate file does not match allowed prefixes: {path}")

    if proposal.get("requires_human_review") is not True:
        errors.append("requires_human_review must be true")

    guardrails = proposal.get("guardrails", {})
    if not isinstance(guardrails, dict):
        errors.append("guardrails must be object")
    else:
        if guardrails.get("propose_only") is not True:
            errors.append("guardrails.propose_only must be true")
        if guardrails.get("requires_human_review") is not True:
            errors.append("guardrails.requires_human_review must be true")

    errors.extend(contains_forbidden_output_field(proposal))
    return errors


def validate_d124(d124, request_probe, response_probe, d125_scope):
    errors = []

    if not d124:
        errors.append("missing D124 real provider dry ping scope report")
        return errors

    if d124.get("ok") is not True:
        errors.append("D124 ok must be true")
    if d124.get("decision") != REQ_D124_DECISION:
        errors.append("D124 decision must be REAL_PROVIDER_DRY_PING_SCOPE_READY")

    guard = d124.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D124 guardrails.{key} must be false")
    for key in [
        "real_provider_dry_ping_scope_only",
        "request_shape_probe_only",
        "response_shape_probe_only",
        "approval_for_d125_intake_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D124 guardrails.{key} must be true")
    for key in [
        "real_provider_called_now",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D124 guardrails.{key} must be false")

    summary = d124.get("summary", {})
    if summary.get("provider_ping_status") != "DRY_SHAPE_PROBE_ONLY":
        errors.append("D124 provider_ping_status must be DRY_SHAPE_PROBE_ONLY")
    if summary.get("real_provider_status") != "NOT_CALLED":
        errors.append("D124 real_provider_status must be NOT_CALLED")
    if summary.get("network_status") != "NOT_ACCESSED":
        errors.append("D124 network_status must be NOT_ACCESSED")
    if summary.get("secret_status") != "NOT_READ":
        errors.append("D124 secret_status must be NOT_READ")
    if summary.get("approval_scope") != REQ_D124_APPROVAL_SCOPE:
        errors.append("D124 approval_scope must be D125 intake scope only")
    if summary.get("next_step") != REQ_D125_GATE:
        errors.append("D124 next_step must be D125")

    if not request_probe:
        errors.append("missing D124 provider request shape probe")
    else:
        if request_probe.get("ok") is not True:
            errors.append("D124 request probe ok must be true")
        if request_probe.get("probe_mode") != "REQUEST_SHAPE_ONLY_NO_NETWORK":
            errors.append("D124 request probe mode must be REQUEST_SHAPE_ONLY_NO_NETWORK")
        if request_probe.get("dry_ping_only") is not True:
            errors.append("D124 request probe dry_ping_only must be true")
        for key in ["real_provider_called", "network_accessed", "api_key_read", "secret_read"]:
            if request_probe.get(key) is not False:
                errors.append(f"D124 request probe {key} must be false")

    if not response_probe:
        errors.append("missing D124 provider response shape probe")
    else:
        if response_probe.get("ok") is not True:
            errors.append("D124 response probe ok must be true")
        if response_probe.get("probe_mode") != "MOCK_RESPONSE_SHAPE_ONLY_NO_PROVIDER_CALL":
            errors.append("D124 response probe mode must be mock response shape only")
        if response_probe.get("dry_ping_only") is not True:
            errors.append("D124 response probe dry_ping_only must be true")
        if response_probe.get("response_valid_shape") is not True:
            errors.append("D124 response probe response_valid_shape must be true")
        for key in ["real_provider_called", "network_accessed", "api_key_read", "secret_read"]:
            if response_probe.get(key) is not False:
                errors.append(f"D124 response probe {key} must be false")

    if not d125_scope:
        errors.append("missing D124 D125 provider response to proposal intake scope")
    else:
        if d125_scope.get("ok") is not True:
            errors.append("D124 D125 scope ok must be true")
        if d125_scope.get("allowed_next_gate") != REQ_D125_GATE:
            errors.append("D124 D125 scope allowed_next_gate must be D125")
        if d125_scope.get("provider_response_intake_scope_only") is not True:
            errors.append("D124 D125 scope must be provider response intake scope only")
        if d125_scope.get("human_review_required") is not True:
            errors.append("D124 D125 scope must require human review")
        for key in [
            "real_provider_call_executed_after_d124",
            "network_call_executed_after_d124",
            "api_key_read_after_d124",
            "real_apply_allowed_after_d124_by_ai",
            "route_insert_allowed_after_d124_by_ai",
            "protected_core_mutation_allowed_after_d124_by_ai",
        ]:
            if d125_scope.get(key) is not False:
                errors.append(f"D124 D125 scope {key} must be false")

    return errors


def build_schema_validator(intake_id, d124, response_probe):
    response_shape = response_probe.get("response_shape", {})
    shape_errors = validate_proposal_shape(response_shape)
    return {
        "state": "D125_PROVIDER_RESPONSE_SCHEMA_VALIDATOR",
        "ok": not shape_errors,
        "intake_id": intake_id,
        "ping_id": d124.get("ping_id"),
        "config_id": d124.get("config_id"),
        "adapter_id": d124.get("adapter_id"),
        "proposal_id": d124.get("proposal_id"),
        "created_at": now(),
        "validator_mode": "PROPOSAL_SHAPE_ONLY_NO_EXECUTION",
        "required_fields": REQUIRED_PROPOSAL_FIELDS,
        "allowed_proposal_types": ALLOWED_PROPOSAL_TYPES,
        "allowed_candidate_prefixes": ALLOWED_CANDIDATE_PREFIXES,
        "blocked_candidate_prefixes": BLOCKED_CANDIDATE_PREFIXES,
        "forbidden_output_fields": FORBIDDEN_OUTPUT_FIELDS,
        "response_shape_valid": not shape_errors,
        "response_shape_errors": shape_errors,
        "real_provider_called": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "actual_apply_executed": False,
        "candidate_executed": False,
    }


def build_rejection_report(intake_id, schema_validator):
    rejected = schema_validator.get("response_shape_valid") is not True
    return {
        "state": "D125_PROVIDER_INTAKE_REJECTION_REPORT",
        "ok": True,
        "intake_id": intake_id,
        "created_at": now(),
        "report_mode": "REJECTION_REPORT_TEMPLATE_ONLY",
        "provider_response_rejected": rejected,
        "rejection_reasons": schema_validator.get("response_shape_errors", []),
        "accepted_for_d126_sandbox_candidate_scope": not rejected,
        "human_review_required": True,
        "real_provider_called": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "actual_apply_executed": False,
        "candidate_executed": False,
    }


def build_d126_scope(intake_id, d124, schema_validator, rejection_report):
    accepted = rejection_report.get("accepted_for_d126_sandbox_candidate_scope") is True
    return {
        "state": "D125_D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE",
        "ok": accepted,
        "intake_id": intake_id,
        "ping_id": d124.get("ping_id"),
        "config_id": d124.get("config_id"),
        "dashboard_id": d124.get("dashboard_id"),
        "adapter_id": d124.get("adapter_id"),
        "seal_id": d124.get("seal_id"),
        "proposal_id": d124.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D126_GATE if accepted else "BLOCKED",
        "d126_allowed_to_create": [
            "proposal_to_sandbox_candidate_scope",
            "sandbox_candidate_write_plan",
            "sandbox_candidate_static_scan",
            "d127_sandbox_candidate_human_review_scope",
        ] if accepted else [],
        "d126_must_not_execute": [
            "real_apply_by_ai",
            "auto_apply",
            "route_insert_by_ai",
            "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai",
            "shell_exec_from_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute_by_ai",
            "restore_execute_by_ai",
            "execute_sandbox_candidate_by_ai",
            "commit_sandbox_candidate_by_ai",
        ],
        "proposal_to_sandbox_candidate_scope_only": accepted,
        "human_review_required": True,
        "schema_validator_ok": schema_validator.get("ok") is True,
        "intake_rejected": not accepted,
        "real_provider_call_executed_after_d125": False,
        "network_call_executed_after_d125": False,
        "api_key_read_after_d125": False,
        "real_apply_allowed_after_d125_by_ai": False,
        "route_insert_allowed_after_d125_by_ai": False,
        "protected_core_mutation_allowed_after_d125_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_ONLY",
    }


def create_provider_response_to_proposal_intake_scope(root="."):
    root = Path(root).resolve()

    d124 = read_json(root / D124_REPORT, {}) or {}
    request_probe = read_json(root / D124_REQUEST_PROBE, {}) or {}
    response_probe = read_json(root / D124_RESPONSE_PROBE, {}) or {}
    d125_scope = read_json(root / D124_D125_SCOPE, {}) or {}

    errors = validate_d124(d124, request_probe, response_probe, d125_scope)

    intake_id = "d125-" + digest({
        "ping_id": d124.get("ping_id"),
        "config_id": d124.get("config_id"),
        "adapter_id": d124.get("adapter_id"),
        "proposal_id": d124.get("proposal_id"),
    })

    schema_validator = build_schema_validator(intake_id, d124, response_probe)
    rejection_report = build_rejection_report(intake_id, schema_validator)
    d126_scope = build_d126_scope(intake_id, d124, schema_validator, rejection_report)

    if schema_validator.get("ok") is not True:
        errors.extend(schema_validator.get("response_shape_errors", []))
    for item_name, item in [
        ("schema_validator", schema_validator),
        ("rejection_report", rejection_report),
    ]:
        for key in ["real_provider_called", "network_accessed", "api_key_read", "secret_read", "actual_apply_executed", "candidate_executed"]:
            if item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_READY" if ok else "PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_BLOCKED"
    result = "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_CREATED" if ok else "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_BLOCKED"

    if ok:
        write_json(root / SCHEMA_VALIDATOR_OUT, schema_validator)
        write_json(root / REJECTION_REPORT_OUT, rejection_report)
        write_json(root / D126_SCOPE_OUT, d126_scope)

    report = {
        "state": "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "intake_id": intake_id,
        "ping_id": d124.get("ping_id"),
        "config_id": d124.get("config_id"),
        "dashboard_id": d124.get("dashboard_id"),
        "adapter_id": d124.get("adapter_id"),
        "seal_id": d124.get("seal_id"),
        "proposal_id": d124.get("proposal_id"),
        "source_d124_report": D124_REPORT,
        "provider_response_schema_validator": schema_validator if ok else {},
        "provider_intake_rejection_report": rejection_report if ok else {},
        "d126_scope": d126_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
            "provider_response_intake_scope_only": True,
            "schema_validation_only": True,
            "rejection_report_only": True,
            "real_provider_called_now": False,
            "approval_for_d126_sandbox_candidate_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": [],
        },
        "summary": {
            "decision": decision,
            "intake_id": intake_id,
            "ping_id": d124.get("ping_id"),
            "config_id": d124.get("config_id"),
            "adapter_id": d124.get("adapter_id"),
            "seal_id": d124.get("seal_id"),
            "proposal_id": d124.get("proposal_id"),
            "intake_status": "PROPOSAL_SHAPE_ACCEPTED" if ok else "BLOCKED",
            "schema_validator_status": "PASS" if schema_validator.get("ok") is True else "FAIL",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "approval_scope": "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D126_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "provider_response_intake_scope_created": ok,
            "schema_validator_created": ok,
            "rejection_report_created": ok,
            "d126_scope_created": ok,
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "actual_apply_executed_by_ai": False,
            "candidate_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D126 may create proposal to sandbox candidate scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_provider_response_to_proposal_intake_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.provider_response_to_proposal_intake_scope import create_provider_response_to_proposal_intake_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD125ProviderResponseToProposalIntakeScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        ping_id = "d124-test"
        config_id = "d123-test"
        dashboard_id = "d122-test"
        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        d124 = {
            "ok": True,
            "decision": "REAL_PROVIDER_DRY_PING_SCOPE_READY",
            "ping_id": ping_id,
            "config_id": config_id,
            "dashboard_id": dashboard_id,
            "adapter_id": adapter_id,
            "seal_id": seal_id,
            "proposal_id": proposal_id,
            "guardrails": {
                "external_ai_called": False,
                "network_accessed": False,
                "api_key_read": False,
                "secret_read": False,
                "shell_from_ai_executed": False,
                "runtime_code_mutated": False,
                "protected_core_mutated": False,
                "canonical_memory_mutated": False,
                "actual_apply_executed": False,
                "route_inserted": False,
                "git_commit_by_ai": False,
                "git_push_by_ai": False,
                "rollback_executed": False,
                "restore_executed": False,
                "real_provider_dry_ping_scope_only": True,
                "request_shape_probe_only": True,
                "response_shape_probe_only": True,
                "real_provider_called_now": False,
                "approval_for_d125_intake_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "provider_ping_status": "DRY_SHAPE_PROBE_ONLY",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "approval_scope": "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_ONLY",
                "next_step": "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE",
            },
        }

        request_probe = {
            "ok": True,
            "ping_id": ping_id,
            "probe_mode": "REQUEST_SHAPE_ONLY_NO_NETWORK",
            "dry_ping_only": True,
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
        }

        response_probe = {
            "ok": True,
            "ping_id": ping_id,
            "probe_mode": "MOCK_RESPONSE_SHAPE_ONLY_NO_PROVIDER_CALL",
            "dry_ping_only": True,
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "response_valid_shape": True,
            "response_shape": {
                "proposal_id": "d124-shape-probe-proposal",
                "proposal_type": "analysis_proposal",
                "intent": "Verify proposal intake.",
                "target_scope": "reports/",
                "candidate_files": [],
                "risk_flags": [],
                "guardrails": {
                    "propose_only": True,
                    "requires_human_review": True,
                    "no_secret_values": True,
                    "no_network_side_effects": True,
                    "no_apply_side_effects": True,
                    "no_git_side_effects": True,
                },
                "validation_plan": ["schema validation"],
                "requires_human_review": True,
            },
        }

        d125_scope = {
            "ok": True,
            "ping_id": ping_id,
            "allowed_next_gate": "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE",
            "provider_response_intake_scope_only": True,
            "human_review_required": True,
            "real_provider_call_executed_after_d124": False,
            "network_call_executed_after_d124": False,
            "api_key_read_after_d124": False,
            "real_apply_allowed_after_d124_by_ai": False,
            "route_insert_allowed_after_d124_by_ai": False,
            "protected_core_mutation_allowed_after_d124_by_ai": False,
        }

        write(root / "reports/d124_real_provider_dry_ping_scope.json", d124)
        write(root / "reports/d124_provider_request_shape_probe.json", request_probe)
        write(root / "reports/d124_provider_response_shape_probe.json", response_probe)
        write(root / "reports/d124_d125_provider_response_to_proposal_intake_scope.json", d125_scope)

        return td, root

    def test_creates_intake_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_provider_response_to_proposal_intake_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_READY")
            self.assertEqual(r["summary"]["intake_status"], "PROPOSAL_SHAPE_ACCEPTED")
            self.assertEqual(r["summary"]["approval_scope"], "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["api_key_read"])
            self.assertFalse(r["guardrails"]["secret_read"])
            self.assertEqual(r["d126_scope"]["allowed_next_gate"], "D126_PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE")
            self.assertTrue((root / "reports/d125_provider_response_to_proposal_intake_scope.json").exists())
            self.assertTrue((root / "reports/d125_provider_response_schema_validator.json").exists())
            self.assertTrue((root / "reports/d125_provider_intake_rejection_report.json").exists())
            self.assertTrue((root / "reports/d125_d126_proposal_to_sandbox_candidate_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d124(self):
        td, root = self.root()
        try:
            (root / "reports/d124_real_provider_dry_ping_scope.json").unlink()
            r = create_provider_response_to_proposal_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_response_missing_required_field(self):
        td, root = self.root()
        try:
            p = root / "reports/d124_provider_response_shape_probe.json"
            data = json.loads(p.read_text())
            del data["response_shape"]["proposal_id"]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_response_to_proposal_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_candidate_file_targets_blocked_prefix(self):
        td, root = self.root()
        try:
            p = root / "reports/d124_provider_response_shape_probe.json"
            data = json.loads(p.read_text())
            data["response_shape"]["candidate_files"] = [{"path": "core/unsafe.py"}]
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_response_to_proposal_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d125_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d124_d125_provider_response_to_proposal_intake_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d124_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_provider_response_to_proposal_intake_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
'''


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

print("D125 PROVIDER RESPONSE TO PROPOSAL INTAKE SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/provider_response_to_proposal_intake_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d125_provider_response_to_proposal_intake_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/provider_response_to_proposal_intake_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d125_provider_response_to_proposal_intake_scope", "-v"], check=True)

print("\n== run D125 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.provider_response_to_proposal_intake_scope import create_provider_response_to_proposal_intake_scope\n"
    "r=create_provider_response_to_proposal_intake_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d125_provider_response_to_proposal_intake_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/provider_response_to_proposal_intake_scope.py",
    "tests/test_d125_provider_response_to_proposal_intake_scope.py",
    "reports/d125_provider_response_to_proposal_intake_scope.json",
    "reports/d125_provider_response_schema_validator.json",
    "reports/d125_provider_intake_rejection_report.json",
    "reports/d125_d126_proposal_to_sandbox_candidate_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D125 provider response to proposal intake scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D125 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD125 PROVIDER RESPONSE TO PROPOSAL INTAKE SCOPE BOOT DONE")
