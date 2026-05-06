from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


D81_REPORT = "reports/d81_ai_proposal_intake.json"
D81_CONTRACT = "reports/d81_ai_proposal_intake_contract.json"
OUT = "reports/d82_human_signed_intent.json"
REQUEST_OUT = "reports/d82_human_approval_request.json"


APPROVAL_PHRASE = "APPROVE_D82_AI_PROPOSAL_INTAKE"
DEFAULT_APPROVER = "human_operator"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256_json(data: Dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_d81(report: Dict[str, Any], contract: Dict[str, Any], errors: List[str]) -> None:
    if not report:
        errors.append("D81 report missing or unreadable")
        return

    if report.get("ok") is not True:
        errors.append("D81 ok flag is not true")

    if report.get("decision") != "AI_PROPOSAL_INTAKE_READY":
        errors.append(f"D81 decision is not AI_PROPOSAL_INTAKE_READY: {report.get('decision')}")

    guard = report.get("guardrails") if isinstance(report.get("guardrails"), dict) else {}
    for key in (
        "external_ai_called",
        "network_accessed",
        "runtime_code_mutated",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "actual_apply_executed",
        "route_inserted",
    ):
        if guard.get(key) is not False:
            errors.append(f"D81 guardrail {key} is not false")

    if guard.get("proposal_intake_only") is not True:
        errors.append("D81 proposal_intake_only is not true")
    if guard.get("json_only") is not True:
        errors.append("D81 json_only is not true")

    if not contract:
        errors.append("D81 intake contract missing or unreadable")
        return

    if contract.get("enabled") is not True:
        errors.append("D81 intake contract enabled is not true")
    if contract.get("mode") != "JSON_CONTRACT_ONLY":
        errors.append(f"D81 intake contract mode is not JSON_CONTRACT_ONLY: {contract.get('mode')}")
    if contract.get("next_gate") != "D82_HUMAN_APPROVAL_SIGNED_INTENT":
        errors.append(f"D81 next gate is not D82_HUMAN_APPROVAL_SIGNED_INTENT: {contract.get('next_gate')}")

    req_guard = contract.get("required_guardrails") if isinstance(contract.get("required_guardrails"), dict) else {}
    for key in (
        "external_ai_called",
        "network_accessed",
        "runtime_code_mutated",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "actual_apply_executed",
        "route_inserted",
    ):
        if req_guard.get(key) is not False:
            errors.append(f"D81 required guardrail {key} is not false")
    if req_guard.get("proposal_only") is not True:
        errors.append("D81 required guardrail proposal_only is not true")
    if req_guard.get("json_only") is not True:
        errors.append("D81 required guardrail json_only is not true")


def create_signed_payload(
    d81_report: Dict[str, Any],
    d81_contract: Dict[str, Any],
    approver: str,
    approval_phrase: str,
) -> Dict[str, Any]:
    evidence = d81_report.get("evidence") if isinstance(d81_report.get("evidence"), dict) else {}
    summary = d81_report.get("summary") if isinstance(d81_report.get("summary"), dict) else {}

    payload = {
        "approval_scope": "ALLOW_AI_PROPOSAL_TO_SANDBOX_INTAKE_ONLY",
        "approval_phrase": approval_phrase,
        "approver": approver,
        "d81_intake_id": d81_report.get("intake_id") or summary.get("intake_id"),
        "boundary_id": evidence.get("boundary_id") or summary.get("boundary_id"),
        "proposal_id": evidence.get("proposal_id") or summary.get("proposal_id"),
        "intake_contract_mode": d81_contract.get("mode"),
        "allowed_next_gate": "D83_SANDBOX_WRITER_HANDOFF",
        "blocked_actions": [
            "actual_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "git_commit_or_push_by_ai",
        ],
    }
    payload["signature_sha256"] = sha256_json(payload)
    return payload


def create_human_signed_intent(
    root: str | Path = ".",
    d81_report_path: str = D81_REPORT,
    d81_contract_path: str = D81_CONTRACT,
    output_path: str = OUT,
    request_output_path: str = REQUEST_OUT,
    approver: str | None = None,
    approval_phrase: str | None = None,
) -> Dict[str, Any]:
    root = Path(root).resolve()
    d81 = read_json(root / d81_report_path, {}) or {}
    contract = read_json(root / d81_contract_path, {}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    validate_d81(d81, contract, errors)

    approver = approver or os.environ.get("D82_APPROVER", DEFAULT_APPROVER)
    phrase = approval_phrase or os.environ.get("D82_APPROVAL_PHRASE", APPROVAL_PHRASE)

    if phrase != APPROVAL_PHRASE:
        errors.append("approval phrase mismatch; expected APPROVE_D82_AI_PROPOSAL_INTAKE")

    signed_payload = create_signed_payload(d81, contract, approver, phrase)
    intent_id = "d82-" + sha256_json(
        {
            "d81_intake_id": signed_payload.get("d81_intake_id"),
            "proposal_id": signed_payload.get("proposal_id"),
            "boundary_id": signed_payload.get("boundary_id"),
            "signature": signed_payload.get("signature_sha256"),
        }
    )[:16]

    ok = not errors
    decision = "HUMAN_SIGNED_INTENT_READY" if ok else "HUMAN_SIGNED_INTENT_BLOCKED"
    result = "D82_HUMAN_SIGNED_INTENT_CREATED" if ok else "D82_HUMAN_SIGNED_INTENT_BLOCKED"

    approval_request = {
        "state": "D82_HUMAN_APPROVAL_REQUEST",
        "ok": ok,
        "intent_id": intent_id,
        "required_phrase": APPROVAL_PHRASE,
        "approval_scope": signed_payload["approval_scope"],
        "allowed_next_gate": "D83_SANDBOX_WRITER_HANDOFF",
        "human_statement": "I approve only structured AI proposal JSON to move into sandbox handoff. I do not approve protected-core mutation, route insertion, auto-apply, external AI calls, or git actions.",
        "blocked_actions": signed_payload["blocked_actions"],
    }
    write_json(root / request_output_path, approval_request)

    report = {
        "state": "D82_HUMAN_APPROVAL_SIGNED_INTENT",
        "result": result,
        "route": "FIELD_INTENT_HUMAN_SIGNED_INTENT",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "intent_id": intent_id,
        "approval_request_path": str(root / request_output_path),
        "signed_payload": signed_payload if ok else {},
        "input_reports": {
            "d81_report_path": str(root / d81_report_path),
            "d81_contract_path": str(root / d81_contract_path),
        },
        "evidence": {
            "d81_ok": d81.get("ok"),
            "d81_decision": d81.get("decision"),
            "d81_intake_id": signed_payload.get("d81_intake_id"),
            "proposal_id": signed_payload.get("proposal_id"),
            "boundary_id": signed_payload.get("boundary_id"),
            "approver": approver,
            "signature_sha256": signed_payload.get("signature_sha256") if ok else "",
        },
        "policy_checks": {
            "human_phrase_verified": phrase == APPROVAL_PHRASE,
            "d81_json_only": contract.get("mode") == "JSON_CONTRACT_ONLY",
            "d81_next_gate_matches": contract.get("next_gate") == "D82_HUMAN_APPROVAL_SIGNED_INTENT",
            "sandbox_only_next": True,
            "real_apply_allowed": False,
            "route_insert_allowed": False,
            "external_ai_call_allowed": False,
        },
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "human_signed_intent_only": True,
            "sandbox_handoff_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "intent_id": intent_id,
            "approver": approver,
            "d81_intake_id": signed_payload.get("d81_intake_id"),
            "proposal_id": signed_payload.get("proposal_id"),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "human_signed_intent_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D83 can hand off the approved JSON-only proposal to a sandbox writer, still with no protected-core mutation.",
        },
    }

    write_json(root / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_human_signed_intent(), ensure_ascii=False, indent=2))
