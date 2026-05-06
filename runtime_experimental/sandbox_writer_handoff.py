from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


D82_REPORT = "reports/d82_human_signed_intent.json"
D82_REQUEST = "reports/d82_human_approval_request.json"
D81_CONTRACT = "reports/d81_ai_proposal_intake_contract.json"
OUT = "reports/d83_sandbox_writer_handoff.json"
MANIFEST_OUT = "reports/d83_sandbox_writer_handoff_manifest.json"
INBOX_DIR = "runtime_experimental/ai_sandbox_inbox"


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


def safe_path(value: str) -> str:
    raw = str(value or "").strip().replace("\\", "/").lstrip("/")
    return "/".join(x for x in raw.split("/") if x and x not in (".", ".."))


def sha256_json(data: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def verify_signed_payload(payload: Dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    signature = payload.get("signature_sha256")
    if not signature:
        return False
    unsigned = dict(payload)
    unsigned.pop("signature_sha256", None)
    return sha256_json(unsigned) == signature


def validate_d82(d82: Dict[str, Any], request: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
    if not d82:
        errors.append("D82 signed intent report missing or unreadable")
        return {}

    if d82.get("ok") is not True:
        errors.append("D82 ok flag is not true")
    if d82.get("decision") != "HUMAN_SIGNED_INTENT_READY":
        errors.append(f"D82 decision is not HUMAN_SIGNED_INTENT_READY: {d82.get('decision')}")

    payload = d82.get("signed_payload") if isinstance(d82.get("signed_payload"), dict) else {}
    if not payload:
        errors.append("D82 signed_payload missing or invalid")
    elif not verify_signed_payload(payload):
        errors.append("D82 signed_payload signature invalid")

    if payload.get("approval_scope") != "ALLOW_AI_PROPOSAL_TO_SANDBOX_INTAKE_ONLY":
        errors.append(f"D82 approval_scope invalid: {payload.get('approval_scope')}")
    if payload.get("allowed_next_gate") != "D83_SANDBOX_WRITER_HANDOFF":
        errors.append(f"D82 allowed_next_gate invalid: {payload.get('allowed_next_gate')}")

    blocked = payload.get("blocked_actions")
    if not isinstance(blocked, list):
        errors.append("D82 blocked_actions missing or invalid")
    else:
        for item in (
            "actual_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "git_commit_or_push_by_ai",
        ):
            if item not in blocked:
                errors.append(f"D82 missing blocked action: {item}")

    guard = d82.get("guardrails") if isinstance(d82.get("guardrails"), dict) else {}
    for key in (
        "external_ai_called",
        "network_accessed",
        "runtime_code_mutated",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "actual_apply_executed",
        "route_inserted",
        "git_commit_by_ai",
    ):
        if guard.get(key) is not False:
            errors.append(f"D82 guardrail {key} is not false")
    if guard.get("human_signed_intent_only") is not True:
        errors.append("D82 human_signed_intent_only is not true")
    if guard.get("sandbox_handoff_only") is not True:
        errors.append("D82 sandbox_handoff_only is not true")

    if not request:
        errors.append("D82 approval request missing or unreadable")
    else:
        if request.get("ok") is not True:
            errors.append("D82 approval request ok flag is not true")
        if request.get("allowed_next_gate") != "D83_SANDBOX_WRITER_HANDOFF":
            errors.append("D82 approval request allowed_next_gate is not D83_SANDBOX_WRITER_HANDOFF")
        if request.get("intent_id") != d82.get("intent_id"):
            errors.append("D82 approval request intent_id does not match report intent_id")

    return payload


def validate_d81_contract(contract: Dict[str, Any], errors: List[str]) -> None:
    if not contract:
        errors.append("D81 intake contract missing or unreadable")
        return

    if contract.get("enabled") is not True:
        errors.append("D81 intake contract enabled is not true")
    if contract.get("mode") != "JSON_CONTRACT_ONLY":
        errors.append(f"D81 intake contract mode is not JSON_CONTRACT_ONLY: {contract.get('mode')}")

    accepted = contract.get("accepted_input") if isinstance(contract.get("accepted_input"), dict) else {}
    allowed = accepted.get("candidate_files_prefixes_allowed") if isinstance(accepted.get("candidate_files_prefixes_allowed"), list) else []
    blocked = accepted.get("candidate_files_prefixes_blocked") if isinstance(accepted.get("candidate_files_prefixes_blocked"), list) else []

    for prefix in ("runtime_experimental/", "reports/", "tests/"):
        if prefix not in allowed:
            errors.append(f"D81 allowed prefix missing: {prefix}")
    for prefix in ("app/orchestration/", "core/", "runtime/", "bridges/", "memory/"):
        if prefix not in blocked:
            errors.append(f"D81 blocked prefix missing: {prefix}")


def create_sandbox_writer_handoff(
    root: str | Path = ".",
    d82_report_path: str = D82_REPORT,
    d82_request_path: str = D82_REQUEST,
    d81_contract_path: str = D81_CONTRACT,
    output_path: str = OUT,
    manifest_output_path: str = MANIFEST_OUT,
    inbox_dir: str = INBOX_DIR,
) -> Dict[str, Any]:
    root = Path(root).resolve()
    d82 = read_json(root / d82_report_path, {}) or {}
    request = read_json(root / d82_request_path, {}) or {}
    d81_contract = read_json(root / d81_contract_path, {}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    payload = validate_d82(d82, request, errors)
    validate_d81_contract(d81_contract, errors)

    intent_id = str(d82.get("intent_id") or "")
    proposal_id = str(payload.get("proposal_id") or "")
    boundary_id = str(payload.get("boundary_id") or "")
    d81_intake_id = str(payload.get("d81_intake_id") or "")

    if not intent_id:
        errors.append("D82 intent_id missing")
    if not proposal_id:
        errors.append("D82 proposal_id missing")
    if not d81_intake_id:
        errors.append("D82 d81_intake_id missing")

    handoff_id = "d83-" + sha256_json(
        {
            "intent_id": intent_id,
            "proposal_id": proposal_id,
            "boundary_id": boundary_id,
            "d81_intake_id": d81_intake_id,
        }
    )[:16]

    inbox_file_rel = safe_path(f"{inbox_dir}/{handoff_id}_sandbox_writer_input.json")
    inbox_file_abs = root / inbox_file_rel

    ok = not errors
    decision = "SANDBOX_WRITER_HANDOFF_READY" if ok else "SANDBOX_WRITER_HANDOFF_BLOCKED"
    result = "D83_SANDBOX_WRITER_HANDOFF_CREATED" if ok else "D83_SANDBOX_WRITER_HANDOFF_BLOCKED"

    handoff_payload = {
        "state": "D83_SANDBOX_WRITER_INPUT",
        "ok": ok,
        "handoff_id": handoff_id,
        "mode": "SANDBOX_WRITER_INPUT_ONLY",
        "created_at": now(),
        "source": {
            "intent_id": intent_id,
            "proposal_id": proposal_id,
            "boundary_id": boundary_id,
            "d81_intake_id": d81_intake_id,
        },
        "allowed_writer_scope": {
            "write_prefixes": [
                "runtime_experimental/ai_sandbox_work/",
                "reports/",
                "tests/",
            ],
            "read_prefixes": [
                "reports/",
                "runtime_experimental/",
                "tests/",
            ],
            "blocked_prefixes": [
                "app/orchestration/",
                "core/",
                "runtime/",
                "bridges/",
                "memory/",
            ],
        },
        "required_before_any_apply": [
            "D84_SANDBOX_WRITER_OUTPUT_REVIEW",
            "D66_RECHECK",
            "UNIT_TESTS",
            "REGRESSION_TESTS",
            "ROLLBACK_MANIFEST",
            "HUMAN_OR_HIGHER_POLICY_APPROVAL",
        ],
        "forbidden_actions": [
            "direct_core_edit",
            "route_insert",
            "actual_apply",
            "external_ai_network_call",
            "git_commit_or_push_by_ai",
            "canonical_memory_overwrite",
        ],
        "guardrails": {
            "proposal_only": True,
            "sandbox_only": True,
            "actual_apply_allowed": False,
            "route_insert_allowed": False,
            "protected_core_mutation_allowed": False,
            "external_ai_call_allowed": False,
            "git_action_allowed": False,
        },
    }

    manifest = {
        "state": "D83_SANDBOX_WRITER_HANDOFF_MANIFEST",
        "ok": ok,
        "handoff_id": handoff_id,
        "created_at": now(),
        "writer_input_path": str(inbox_file_abs) if ok else "",
        "source_reports": [
            str(root / d82_report_path),
            str(root / d82_request_path),
            str(root / d81_contract_path),
        ],
        "actual_files_created": [inbox_file_rel] if ok else [],
        "actual_files_mutated": [],
        "protected_core_touched": False,
        "next_gate": "D84_SANDBOX_WRITER_OUTPUT_REVIEW",
    }

    if ok:
        write_json(inbox_file_abs, handoff_payload)
        write_json(root / manifest_output_path, manifest)

    report = {
        "state": "D83_SANDBOX_WRITER_HANDOFF",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_WRITER_HANDOFF",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "handoff_id": handoff_id,
        "writer_input_path": str(inbox_file_abs) if ok else "",
        "manifest_path": str(root / manifest_output_path) if ok else "",
        "input_reports": {
            "d82_report_path": str(root / d82_report_path),
            "d82_request_path": str(root / d82_request_path),
            "d81_contract_path": str(root / d81_contract_path),
        },
        "evidence": {
            "intent_id": intent_id,
            "proposal_id": proposal_id,
            "boundary_id": boundary_id,
            "d81_intake_id": d81_intake_id,
            "signature_sha256": payload.get("signature_sha256") if payload else "",
            "writer_input_path": str(inbox_file_abs) if ok else "",
        },
        "handoff_manifest": manifest,
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "sandbox_handoff_only": True,
            "writer_input_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "handoff_id": handoff_id,
            "intent_id": intent_id,
            "proposal_id": proposal_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "sandbox_writer_handoff_created": ok,
            "writer_input_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D84 should review sandbox writer output before any generated artifact can approach guarded apply.",
        },
    }

    write_json(root / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_writer_handoff(), ensure_ascii=False, indent=2))
