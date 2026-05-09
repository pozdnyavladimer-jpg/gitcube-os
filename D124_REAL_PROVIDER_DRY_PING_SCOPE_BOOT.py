#!/usr/bin/env python3
# D124_REAL_PROVIDER_DRY_PING_SCOPE_BOOT.py
#
# Creates D124 Real Provider Dry Ping Scope.
#
# D124 consumes D123 provider-config manual-enable artifacts and creates
# dry provider ping / shape-probe artifacts:
# - runtime_experimental/real_provider_dry_ping_scope.py
# - tests/test_d124_real_provider_dry_ping_scope.py
# - reports/d124_real_provider_dry_ping_scope.json
# - reports/d124_provider_request_shape_probe.json
# - reports/d124_provider_response_shape_probe.json
# - reports/d124_d125_provider_response_to_proposal_intake_scope.json
#
# This is REAL PROVIDER DRY PING SCOPE ONLY.
# It does NOT call a real provider.
# It does NOT read API keys or secrets.
# It does NOT access network.
# It does NOT execute shell commands.
# It does NOT apply patches.
# It does NOT mutate protected runtime/core/memory/routes.
# It does NOT commit/push/tag by AI.
#
# D124 opens D125 Provider Response To Proposal Intake Scope.

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

D123_REPORT = "reports/d123_provider_config_manual_enable_scope.json"
D123_SECRET_POLICY = "reports/d123_provider_secret_placeholder_policy.json"
D123_NETWORK_PLAN = "reports/d123_network_allowlist_dry_plan.json"
D123_D124_SCOPE = "reports/d123_d124_real_provider_dry_ping_scope.json"

OUT = "reports/d124_real_provider_dry_ping_scope.json"
REQUEST_PROBE_OUT = "reports/d124_provider_request_shape_probe.json"
RESPONSE_PROBE_OUT = "reports/d124_provider_response_shape_probe.json"
D125_SCOPE_OUT = "reports/d124_d125_provider_response_to_proposal_intake_scope.json"

REQ_D123_DECISION = "PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_READY"
REQ_D124_GATE = "D124_REAL_PROVIDER_DRY_PING_SCOPE"
REQ_D125_GATE = "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE"
REQ_D123_APPROVAL_SCOPE = "D124_REAL_PROVIDER_DRY_PING_SCOPE_ONLY"

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


def validate_d123(d123, secret_policy, network_plan, d124_scope):
    errors = []

    if not d123:
        errors.append("missing D123 provider config manual enable scope report")
        return errors

    if d123.get("ok") is not True:
        errors.append("D123 ok must be true")
    if d123.get("decision") != REQ_D123_DECISION:
        errors.append("D123 decision must be PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_READY")

    guard = d123.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D123 guardrails.{key} must be false")
    for key in [
        "provider_config_manual_enable_scope_only",
        "placeholder_policy_only",
        "network_allowlist_dry_plan_only",
        "approval_for_d124_dry_ping_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D123 guardrails.{key} must be true")
    for key in [
        "real_provider_enabled_now",
        "real_provider_called_now",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D123 guardrails.{key} must be false")

    summary = d123.get("summary", {})
    if summary.get("provider_config_status") != "PLACEHOLDER_ONLY":
        errors.append("D123 provider_config_status must be PLACEHOLDER_ONLY")
    if summary.get("real_provider_status") != "DISABLED":
        errors.append("D123 real_provider_status must be DISABLED")
    if summary.get("network_status") != "DRY_PLAN_ONLY":
        errors.append("D123 network_status must be DRY_PLAN_ONLY")
    if summary.get("secret_status") != "PLACEHOLDER_ONLY_NOT_READ":
        errors.append("D123 secret_status must be PLACEHOLDER_ONLY_NOT_READ")
    if summary.get("approval_scope") != REQ_D123_APPROVAL_SCOPE:
        errors.append("D123 approval_scope must be D124 dry ping scope only")
    if summary.get("next_step") != REQ_D124_GATE:
        errors.append("D123 next_step must be D124")

    if not secret_policy:
        errors.append("missing D123 provider secret placeholder policy")
    else:
        if secret_policy.get("ok") is not True:
            errors.append("D123 secret policy ok must be true")
        if secret_policy.get("policy_mode") != "PLACEHOLDER_ONLY_NO_SECRET_READ":
            errors.append("D123 secret policy mode must be PLACEHOLDER_ONLY_NO_SECRET_READ")
        for key in ["secret_read_now", "api_key_read_now", "real_provider_enabled_now"]:
            if secret_policy.get(key) is not False:
                errors.append(f"D123 secret policy {key} must be false")

    if not network_plan:
        errors.append("missing D123 network allowlist dry plan")
    else:
        if network_plan.get("ok") is not True:
            errors.append("D123 network plan ok must be true")
        if network_plan.get("plan_mode") != "DRY_PLAN_ONLY_NO_NETWORK":
            errors.append("D123 network plan mode must be DRY_PLAN_ONLY_NO_NETWORK")
        for key in ["network_accessed_now", "real_provider_call_now", "allowlist_enabled_now"]:
            if network_plan.get(key) is not False:
                errors.append(f"D123 network plan {key} must be false")

    if not d124_scope:
        errors.append("missing D123 D124 real provider dry ping scope")
    else:
        if d124_scope.get("ok") is not True:
            errors.append("D123 D124 scope ok must be true")
        if d124_scope.get("allowed_next_gate") != REQ_D124_GATE:
            errors.append("D123 D124 scope allowed_next_gate must be D124")
        if d124_scope.get("real_provider_dry_ping_scope_only") is not True:
            errors.append("D123 D124 scope must be dry ping scope only")
        if d124_scope.get("human_review_required") is not True:
            errors.append("D123 D124 scope must require human review")
        for key in [
            "real_provider_enabled_after_d123",
            "network_call_executed_after_d123",
            "api_key_read_after_d123",
            "real_apply_allowed_after_d123_by_ai",
            "route_insert_allowed_after_d123_by_ai",
            "protected_core_mutation_allowed_after_d123_by_ai",
        ]:
            if d124_scope.get(key) is not False:
                errors.append(f"D123 D124 scope {key} must be false")

    return errors


def build_request_shape_probe(ping_id, d123, secret_policy, network_plan):
    return {
        "state": "D124_PROVIDER_REQUEST_SHAPE_PROBE",
        "ok": True,
        "ping_id": ping_id,
        "config_id": d123.get("config_id"),
        "dashboard_id": d123.get("dashboard_id"),
        "adapter_id": d123.get("adapter_id"),
        "seal_id": d123.get("seal_id"),
        "proposal_id": d123.get("proposal_id"),
        "created_at": now(),
        "probe_mode": "REQUEST_SHAPE_ONLY_NO_NETWORK",
        "real_provider_called": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "request_shape": {
            "provider": "PROVIDER_NAME_PLACEHOLDER",
            "model": "PROVIDER_MODEL_PLACEHOLDER",
            "endpoint": "PROVIDER_ENDPOINT_PLACEHOLDER",
            "api_key_env_name": "PROVIDER_API_KEY_ENV_NAME_PLACEHOLDER",
            "messages": [
                {
                    "role": "user",
                    "content": "Return proposal-shaped JSON only. Do not execute anything.",
                }
            ],
            "response_format": "json_object",
            "temperature": 0,
        },
        "secret_policy_reference": "reports/d123_provider_secret_placeholder_policy.json",
        "network_plan_reference": "reports/d123_network_allowlist_dry_plan.json",
        "dry_ping_only": True,
    }


def build_response_shape_probe(ping_id, d123):
    return {
        "state": "D124_PROVIDER_RESPONSE_SHAPE_PROBE",
        "ok": True,
        "ping_id": ping_id,
        "config_id": d123.get("config_id"),
        "adapter_id": d123.get("adapter_id"),
        "proposal_id": d123.get("proposal_id"),
        "created_at": now(),
        "probe_mode": "MOCK_RESPONSE_SHAPE_ONLY_NO_PROVIDER_CALL",
        "real_provider_called": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "response_shape": {
            "proposal_id": "d124-shape-probe-proposal",
            "proposal_type": "analysis_proposal",
            "intent": "Verify that provider output can be converted into proposal intake format.",
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
            "validation_plan": [
                "schema validation",
                "forbidden field scan",
                "human review before any later candidate write",
            ],
            "requires_human_review": True,
        },
        "response_valid_shape": True,
        "dry_ping_only": True,
    }


def build_d125_scope(ping_id, d123):
    return {
        "state": "D124_D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE",
        "ok": True,
        "ping_id": ping_id,
        "config_id": d123.get("config_id"),
        "dashboard_id": d123.get("dashboard_id"),
        "adapter_id": d123.get("adapter_id"),
        "seal_id": d123.get("seal_id"),
        "proposal_id": d123.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D125_GATE,
        "d125_allowed_to_create": [
            "provider_response_to_proposal_intake_scope",
            "provider_response_schema_validator",
            "provider_intake_rejection_report",
            "d126_proposal_to_sandbox_candidate_scope",
        ],
        "d125_must_not_execute": [
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
        "provider_response_intake_scope_only": True,
        "human_review_required": True,
        "real_provider_call_executed_after_d124": False,
        "network_call_executed_after_d124": False,
        "api_key_read_after_d124": False,
        "real_apply_allowed_after_d124_by_ai": False,
        "route_insert_allowed_after_d124_by_ai": False,
        "protected_core_mutation_allowed_after_d124_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_ONLY",
    }


def create_real_provider_dry_ping_scope(root="."):
    root = Path(root).resolve()

    d123 = read_json(root / D123_REPORT, {}) or {}
    secret_policy = read_json(root / D123_SECRET_POLICY, {}) or {}
    network_plan = read_json(root / D123_NETWORK_PLAN, {}) or {}
    d124_scope = read_json(root / D123_D124_SCOPE, {}) or {}

    errors = validate_d123(d123, secret_policy, network_plan, d124_scope)

    ping_id = "d124-" + digest({
        "config_id": d123.get("config_id"),
        "dashboard_id": d123.get("dashboard_id"),
        "adapter_id": d123.get("adapter_id"),
        "proposal_id": d123.get("proposal_id"),
    })

    request_probe = build_request_shape_probe(ping_id, d123, secret_policy, network_plan)
    response_probe = build_response_shape_probe(ping_id, d123)
    d125_scope = build_d125_scope(ping_id, d123)

    for item_name, item in [
        ("request_probe", request_probe),
        ("response_probe", response_probe),
    ]:
        for key in ["real_provider_called", "network_accessed", "api_key_read", "secret_read"]:
            if item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "REAL_PROVIDER_DRY_PING_SCOPE_READY" if ok else "REAL_PROVIDER_DRY_PING_SCOPE_BLOCKED"
    result = "D124_REAL_PROVIDER_DRY_PING_SCOPE_CREATED" if ok else "D124_REAL_PROVIDER_DRY_PING_SCOPE_BLOCKED"

    if ok:
        write_json(root / REQUEST_PROBE_OUT, request_probe)
        write_json(root / RESPONSE_PROBE_OUT, response_probe)
        write_json(root / D125_SCOPE_OUT, d125_scope)

    report = {
        "state": "D124_REAL_PROVIDER_DRY_PING_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_REAL_PROVIDER_DRY_PING_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "ping_id": ping_id,
        "config_id": d123.get("config_id"),
        "dashboard_id": d123.get("dashboard_id"),
        "adapter_id": d123.get("adapter_id"),
        "seal_id": d123.get("seal_id"),
        "proposal_id": d123.get("proposal_id"),
        "source_d123_report": D123_REPORT,
        "provider_request_shape_probe": request_probe if ok else {},
        "provider_response_shape_probe": response_probe if ok else {},
        "d125_scope": d125_scope if ok else {},
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
            "approval_for_d125_intake_scope_only": ok,
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
            "ping_id": ping_id,
            "config_id": d123.get("config_id"),
            "dashboard_id": d123.get("dashboard_id"),
            "adapter_id": d123.get("adapter_id"),
            "seal_id": d123.get("seal_id"),
            "proposal_id": d123.get("proposal_id"),
            "provider_ping_status": "DRY_SHAPE_PROBE_ONLY",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "approval_scope": "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D125_GATE,
        },
        "success_condition": {
            "real_provider_dry_ping_scope_created": ok,
            "request_shape_probe_created": ok,
            "response_shape_probe_created": ok,
            "d125_scope_created": ok,
            "real_provider_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "actual_apply_executed_by_ai": False,
            "candidate_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D125 may create provider response to proposal intake scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_real_provider_dry_ping_scope(), ensure_ascii=False, indent=2))
'''

TESTS = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.real_provider_dry_ping_scope import create_real_provider_dry_ping_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD124RealProviderDryPingScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        config_id = "d123-test"
        dashboard_id = "d122-test"
        adapter_id = "d121-test"
        seal_id = "d120-test"
        proposal_id = "d107-valid-test"

        d123 = {
            "ok": True,
            "decision": "PROVIDER_CONFIG_MANUAL_ENABLE_SCOPE_READY",
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
                "provider_config_manual_enable_scope_only": True,
                "placeholder_policy_only": True,
                "network_allowlist_dry_plan_only": True,
                "real_provider_enabled_now": False,
                "real_provider_called_now": False,
                "approval_for_d124_dry_ping_scope_only": True,
                "approval_for_real_apply_by_ai": False,
                "candidate_execution_allowed_by_ai": False,
                "commands_executed_by_ai": False,
            },
            "summary": {
                "provider_config_status": "PLACEHOLDER_ONLY",
                "real_provider_status": "DISABLED",
                "network_status": "DRY_PLAN_ONLY",
                "secret_status": "PLACEHOLDER_ONLY_NOT_READ",
                "approval_scope": "D124_REAL_PROVIDER_DRY_PING_SCOPE_ONLY",
                "next_step": "D124_REAL_PROVIDER_DRY_PING_SCOPE",
            },
        }

        secret_policy = {
            "ok": True,
            "config_id": config_id,
            "policy_mode": "PLACEHOLDER_ONLY_NO_SECRET_READ",
            "secret_read_now": False,
            "api_key_read_now": False,
            "real_provider_enabled_now": False,
        }

        network_plan = {
            "ok": True,
            "config_id": config_id,
            "plan_mode": "DRY_PLAN_ONLY_NO_NETWORK",
            "network_accessed_now": False,
            "real_provider_call_now": False,
            "allowlist_enabled_now": False,
        }

        d124_scope = {
            "ok": True,
            "config_id": config_id,
            "allowed_next_gate": "D124_REAL_PROVIDER_DRY_PING_SCOPE",
            "real_provider_dry_ping_scope_only": True,
            "human_review_required": True,
            "real_provider_enabled_after_d123": False,
            "network_call_executed_after_d123": False,
            "api_key_read_after_d123": False,
            "real_apply_allowed_after_d123_by_ai": False,
            "route_insert_allowed_after_d123_by_ai": False,
            "protected_core_mutation_allowed_after_d123_by_ai": False,
        }

        write(root / "reports/d123_provider_config_manual_enable_scope.json", d123)
        write(root / "reports/d123_provider_secret_placeholder_policy.json", secret_policy)
        write(root / "reports/d123_network_allowlist_dry_plan.json", network_plan)
        write(root / "reports/d123_d124_real_provider_dry_ping_scope.json", d124_scope)

        return td, root

    def test_creates_dry_ping_scope_outputs(self):
        td, root = self.root()
        try:
            r = create_real_provider_dry_ping_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "REAL_PROVIDER_DRY_PING_SCOPE_READY")
            self.assertEqual(r["summary"]["provider_ping_status"], "DRY_SHAPE_PROBE_ONLY")
            self.assertEqual(r["summary"]["real_provider_status"], "NOT_CALLED")
            self.assertEqual(r["summary"]["approval_scope"], "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE_ONLY")
            self.assertFalse(r["guardrails"]["network_accessed"])
            self.assertFalse(r["guardrails"]["api_key_read"])
            self.assertFalse(r["guardrails"]["secret_read"])
            self.assertEqual(r["d125_scope"]["allowed_next_gate"], "D125_PROVIDER_RESPONSE_TO_PROPOSAL_INTAKE_SCOPE")
            self.assertTrue((root / "reports/d124_real_provider_dry_ping_scope.json").exists())
            self.assertTrue((root / "reports/d124_provider_request_shape_probe.json").exists())
            self.assertTrue((root / "reports/d124_provider_response_shape_probe.json").exists())
            self.assertTrue((root / "reports/d124_d125_provider_response_to_proposal_intake_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d123(self):
        td, root = self.root()
        try:
            (root / "reports/d123_provider_config_manual_enable_scope.json").unlink()
            r = create_real_provider_dry_ping_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_secret_policy_reads_secret(self):
        td, root = self.root()
        try:
            p = root / "reports/d123_provider_secret_placeholder_policy.json"
            data = json.loads(p.read_text())
            data["secret_read_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_real_provider_dry_ping_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_network_plan_called_provider(self):
        td, root = self.root()
        try:
            p = root / "reports/d123_network_allowlist_dry_plan.json"
            data = json.loads(p.read_text())
            data["real_provider_call_now"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_real_provider_dry_ping_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d124_scope_allows_real_apply(self):
        td, root = self.root()
        try:
            p = root / "reports/d123_d124_real_provider_dry_ping_scope.json"
            data = json.loads(p.read_text())
            data["real_apply_allowed_after_d123_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_real_provider_dry_ping_scope(root)
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

print("D124 REAL PROVIDER DRY PING SCOPE BOOT: repo =", ROOT)

Path("runtime_experimental/real_provider_dry_ping_scope.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d124_real_provider_dry_ping_scope.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/real_provider_dry_ping_scope.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d124_real_provider_dry_ping_scope", "-v"], check=True)

print("\n== run D124 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.real_provider_dry_ping_scope import create_real_provider_dry_ping_scope\n"
    "r=create_real_provider_dry_ping_scope()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d124_real_provider_dry_ping_scope.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/real_provider_dry_ping_scope.py",
    "tests/test_d124_real_provider_dry_ping_scope.py",
    "reports/d124_real_provider_dry_ping_scope.json",
    "reports/d124_provider_request_shape_probe.json",
    "reports/d124_provider_response_shape_probe.json",
    "reports/d124_d125_provider_response_to_proposal_intake_scope.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D124_REAL_PROVIDER_DRY_PING_SCOPE_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D124 real provider dry ping scope"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D124 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD124 REAL PROVIDER DRY PING SCOPE BOOT DONE")
