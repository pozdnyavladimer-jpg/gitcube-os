from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


D88_REQUEST = "reports/d88_higher_policy_approval_request.json"
D88_PACKET = "reports/d88_higher_policy_review_packet.json"
D88_BLOCKED = "reports/d88_apply_still_blocked.json"

OUT = "reports/d89_final_human_confirmation.json"
STATEMENT_OUT = "reports/d89_human_confirmation_statement.json"
SCOPE_OUT = "reports/d89_d90_planning_scope.json"


REQUIRED_D88_DECISION = "HIGHER_POLICY_APPROVAL_REQUEST_READY"
REQUIRED_REVIEW_PHRASE = "REVIEW_D88_HIGHER_POLICY_REQUEST_ONLY"
CONFIRMATION_PHRASE = "CONFIRM_D89_FINAL_HUMAN_REVIEW_FOR_D90_PLANNING_ONLY"

HARD_FALSE_FLAGS = [
    "external_ai_called",
    "network_accessed",
    "runtime_code_mutated",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "actual_apply_executed",
    "route_inserted",
    "git_commit_by_ai",
]


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
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def validate_false_flags(name: str, data: Dict[str, Any], errors: List[str]) -> None:
    for key in HARD_FALSE_FLAGS:
        if data.get(key) is not False:
            errors.append(f"{name} flag {key} is not false")


def validate_d88(
    d88: Dict[str, Any],
    packet: Dict[str, Any],
    blocked: Dict[str, Any],
    errors: List[str],
) -> None:
    if not d88:
        errors.append("D88 request missing or unreadable")
        return

    if d88.get("ok") is not True:
        errors.append("D88 ok flag is not true")
    if d88.get("decision") != REQUIRED_D88_DECISION:
        errors.append(f"D88 decision invalid: {d88.get('decision')}")

    guard = d88.get("guardrails") if isinstance(d88.get("guardrails"), dict) else {}
    validate_false_flags("D88 guardrail", guard, errors)

    if guard.get("higher_policy_request_only") is not True:
        errors.append("D88 higher_policy_request_only is not true")
    if guard.get("approval_not_granted") is not True:
        errors.append("D88 approval_not_granted is not true")

    if not packet:
        errors.append("D88 higher policy review packet missing or unreadable")
    else:
        if packet.get("ok") is not True:
            errors.append("D88 review packet ok flag is not true")
        if packet.get("review_phrase") != REQUIRED_REVIEW_PHRASE:
            errors.append(f"D88 review_phrase invalid: {packet.get('review_phrase')}")
        if packet.get("allowed_next_gate_if_reviewed") != "D89_FINAL_HUMAN_CONFIRMATION":
            errors.append(f"D88 packet next gate invalid: {packet.get('allowed_next_gate_if_reviewed')}")
        if packet.get("policy_answer_now") != "NOT_APPROVED_YET":
            errors.append("D88 packet policy_answer_now must still be NOT_APPROVED_YET")

        for forbidden in (
            "actual_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "git_commit_or_push_by_ai",
        ):
            if forbidden not in packet.get("not_allowed", []):
                errors.append(f"D88 packet missing not_allowed item: {forbidden}")

    if not blocked:
        errors.append("D88 apply-still-blocked report missing or unreadable")
    else:
        for key in (
            "apply_allowed_now",
            "route_insert_allowed_now",
            "protected_core_mutation_allowed_now",
            "canonical_memory_mutation_allowed_now",
            "external_ai_call_allowed_now",
            "git_action_by_ai_allowed_now",
        ):
            if blocked.get(key) is not False:
                errors.append(f"D88 blocked flag {key} is not false")
        if blocked.get("next_required_gate") != "D89_FINAL_HUMAN_CONFIRMATION":
            errors.append(f"D88 blocked next_required_gate invalid: {blocked.get('next_required_gate')}")


def build_confirmation_statement(confirmation_id: str, d88: Dict[str, Any], packet: Dict[str, Any]) -> Dict[str, Any]:
    evidence = d88.get("evidence") if isinstance(d88.get("evidence"), dict) else {}

    return {
        "state": "D89_HUMAN_CONFIRMATION_STATEMENT",
        "ok": True,
        "confirmation_id": confirmation_id,
        "created_at": now(),
        "confirmation_phrase": CONFIRMATION_PHRASE,
        "human_confirmation_scope": "ALLOW_D90_CONTROLLED_APPLY_PLAN_GENERATION_ONLY",
        "human_statement": (
            "I confirm D88 higher-policy review packet may advance to D90 controlled apply planning only. "
            "This does not approve real apply, route insertion, protected-core mutation, external AI calls, or AI git actions."
        ),
        "source_request_id": d88.get("request_id"),
        "source_capsule_id": evidence.get("capsule_id") or packet.get("source_capsule_id"),
        "source_package_id": evidence.get("package_id") or packet.get("source_package_id"),
        "source_review_id": evidence.get("review_id") or packet.get("source_review_id"),
        "approved_next_gate": "D90_CONTROLLED_APPLY_PLAN",
        "not_approved": [
            "actual_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "git_commit_or_push_by_ai",
        ],
    }


def build_d90_scope(confirmation_id: str, statement: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "state": "D89_D90_PLANNING_SCOPE",
        "ok": True,
        "confirmation_id": confirmation_id,
        "created_at": now(),
        "d90_allowed_to_create": [
            "controlled_apply_plan_json",
            "explicit_scope_diff_summary",
            "pre_apply_command_preview",
            "manual_review_checklist",
        ],
        "d90_must_not_execute": [
            "actual_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "git_commit_or_push_by_ai",
        ],
        "d90_required_guards": [
            "D66_RECHECK",
            "FULL_TEST_DISCOVERY",
            "ROLLBACK_MANIFEST_RECONFIRMATION",
            "EXPLICIT_APPLY_SCOPE_APPROVAL",
            "NO_PROTECTED_CORE_MUTATION",
        ],
        "apply_allowed_after_d89": False,
        "route_insert_allowed_after_d89": False,
        "protected_core_mutation_allowed_after_d89": False,
        "next_gate": "D90_CONTROLLED_APPLY_PLAN",
        "source_confirmation_phrase": statement.get("confirmation_phrase"),
    }


def create_final_human_confirmation(
    root: str | Path = ".",
    d88_request_path: str = D88_REQUEST,
    d88_packet_path: str = D88_PACKET,
    d88_blocked_path: str = D88_BLOCKED,
    output_path: str = OUT,
    statement_output_path: str = STATEMENT_OUT,
    scope_output_path: str = SCOPE_OUT,
) -> Dict[str, Any]:
    root = Path(root).resolve()

    d88 = read_json(root / d88_request_path, {}) or {}
    packet = read_json(root / d88_packet_path, {}) or {}
    blocked = read_json(root / d88_blocked_path, {}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    validate_d88(d88, packet, blocked, errors)

    request_id = str(d88.get("request_id") or packet.get("request_id") or "")
    capsule_id = str((d88.get("evidence") or {}).get("capsule_id") or packet.get("source_capsule_id") or "")
    package_id = str((d88.get("evidence") or {}).get("package_id") or packet.get("source_package_id") or "")
    review_id = str((d88.get("evidence") or {}).get("review_id") or packet.get("source_review_id") or "")

    confirmation_id = "d89-" + sha256_json(
        {
            "request_id": request_id,
            "capsule_id": capsule_id,
            "package_id": package_id,
            "review_id": review_id,
            "d88_decision": d88.get("decision"),
        }
    )[:16]

    ok = not errors
    decision = "FINAL_HUMAN_CONFIRMATION_READY" if ok else "FINAL_HUMAN_CONFIRMATION_BLOCKED"
    result = "D89_FINAL_HUMAN_CONFIRMATION_CREATED" if ok else "D89_FINAL_HUMAN_CONFIRMATION_BLOCKED"

    statement = build_confirmation_statement(confirmation_id, d88, packet)
    scope = build_d90_scope(confirmation_id, statement)

    if ok:
        write_json(root / statement_output_path, statement)
        write_json(root / scope_output_path, scope)

    report = {
        "state": "D89_FINAL_HUMAN_CONFIRMATION",
        "result": result,
        "route": "FIELD_INTENT_FINAL_HUMAN_CONFIRMATION",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "confirmation_id": confirmation_id,
        "statement_path": str(root / statement_output_path) if ok else "",
        "d90_scope_path": str(root / scope_output_path) if ok else "",
        "input_reports": {
            "d88_request_path": str(root / d88_request_path),
            "d88_packet_path": str(root / d88_packet_path),
            "d88_blocked_path": str(root / d88_blocked_path),
        },
        "evidence": {
            "request_id": request_id,
            "capsule_id": capsule_id,
            "package_id": package_id,
            "review_id": review_id,
            "d88_decision": d88.get("decision"),
            "d88_apply_allowed_now": False,
        },
        "confirmation_statement": statement if ok else {},
        "d90_scope": scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "final_human_confirmation_only": True,
            "d90_planning_only": True,
            "approval_for_real_apply": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "confirmation_id": confirmation_id,
            "request_id": request_id,
            "capsule_id": capsule_id,
            "package_id": package_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "final_human_confirmation_created": ok,
            "d90_planning_scope_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D90 can create a controlled apply plan preview. Real apply remains blocked until explicit apply-scope approval.",
        },
    }

    write_json(root / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_final_human_confirmation(), ensure_ascii=False, indent=2))
