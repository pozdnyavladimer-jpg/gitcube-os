from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


D87_REPORT = "reports/d87_final_pre_apply_safety_capsule.json"
D87_CAPSULE = "reports/d87_pre_apply_safety_capsule.json"
D87_BLOCKERS = "reports/d87_apply_blockers.json"

OUT = "reports/d88_higher_policy_approval_request.json"
PACKET_OUT = "reports/d88_higher_policy_review_packet.json"
BLOCKERS_OUT = "reports/d88_apply_still_blocked.json"


REQUIRED_D87_DECISION = "FINAL_PRE_APPLY_SAFETY_CAPSULE_READY"
REQUIRED_NEXT_GATE = "D88_HIGHER_POLICY_APPROVAL_REQUEST"

REVIEW_PHRASE = "REVIEW_D88_HIGHER_POLICY_REQUEST_ONLY"

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


def validate_d87(
    d87: Dict[str, Any],
    capsule: Dict[str, Any],
    blockers: Dict[str, Any],
    errors: List[str],
) -> None:
    if not d87:
        errors.append("D87 final pre-apply safety capsule report missing or unreadable")
        return

    if d87.get("ok") is not True:
        errors.append("D87 ok flag is not true")
    if d87.get("decision") != REQUIRED_D87_DECISION:
        errors.append(f"D87 decision invalid: {d87.get('decision')}")

    guard = d87.get("guardrails") if isinstance(d87.get("guardrails"), dict) else {}
    validate_false_flags("D87 guardrail", guard, errors)

    if guard.get("final_capsule_only") is not True:
        errors.append("D87 final_capsule_only is not true")
    if guard.get("pre_apply_review_only") is not True:
        errors.append("D87 pre_apply_review_only is not true")

    if not capsule:
        errors.append("D87 pre-apply safety capsule missing or unreadable")
    else:
        if capsule.get("ok") is not True:
            errors.append("D87 capsule ok flag is not true")
        if capsule.get("next_gate") != REQUIRED_NEXT_GATE:
            errors.append(f"D87 capsule next_gate invalid: {capsule.get('next_gate')}")

        approval = capsule.get("approval_state") if isinstance(capsule.get("approval_state"), dict) else {}
        if approval.get("ready_for_higher_policy_review") is not True:
            errors.append("D87 capsule is not ready for higher policy review")
        for key in (
            "ready_for_real_apply",
            "ready_for_route_insert",
            "ready_for_protected_core_mutation",
        ):
            if approval.get(key) is not False:
                errors.append(f"D87 capsule approval_state {key} is not false")

        hard = capsule.get("hard_no_mutation_flags") if isinstance(capsule.get("hard_no_mutation_flags"), dict) else {}
        validate_false_flags("D87 capsule hard_no_mutation", hard, errors)

    if not blockers:
        errors.append("D87 apply blockers missing or unreadable")
    else:
        for key in (
            "apply_allowed_now",
            "route_insert_allowed_now",
            "protected_core_mutation_allowed_now",
            "external_ai_call_allowed_now",
            "git_action_by_ai_allowed_now",
        ):
            if blockers.get(key) is not False:
                errors.append(f"D87 blocker {key} is not false")

        required = blockers.get("required_before_apply_can_be_discussed")
        if not isinstance(required, list):
            errors.append("D87 blockers required_before_apply_can_be_discussed missing")
        else:
            for item in (
                "D88_HIGHER_POLICY_APPROVAL_REQUEST",
                "D89_FINAL_HUMAN_CONFIRMATION",
                "D66_RECHECK",
                "FULL_TEST_DISCOVERY",
                "ROLLBACK_MANIFEST_RECONFIRMATION",
            ):
                if item not in required:
                    errors.append(f"D87 blockers missing required item: {item}")


def build_review_packet(
    request_id: str,
    d87: Dict[str, Any],
    capsule: Dict[str, Any],
    blockers: Dict[str, Any],
) -> Dict[str, Any]:
    summary = d87.get("summary") if isinstance(d87.get("summary"), dict) else {}
    cap_chain = capsule.get("evidence_chain") if isinstance(capsule.get("evidence_chain"), dict) else {}

    return {
        "state": "D88_HIGHER_POLICY_REVIEW_PACKET",
        "ok": True,
        "request_id": request_id,
        "created_at": now(),
        "review_mode": "HIGHER_POLICY_REVIEW_REQUEST_ONLY",
        "review_phrase": REVIEW_PHRASE,
        "source_capsule_id": capsule.get("capsule_id") or summary.get("capsule_id"),
        "source_package_id": capsule.get("package_id") or summary.get("package_id"),
        "source_review_id": capsule.get("review_id") or summary.get("review_id"),
        "evidence_chain": {
            "d87_decision": d87.get("decision"),
            "d85_decision": cap_chain.get("d85_decision"),
            "d86_decision": cap_chain.get("d86_decision"),
            "d86_commands_failed_count": cap_chain.get("d86_commands_failed_count"),
            "rollback_manifest_present": cap_chain.get("rollback_manifest_present"),
            "regression_checklist_present": cap_chain.get("regression_checklist_present"),
        },
        "policy_question": "May this reviewed sandbox-only candidate move to D89 final human confirmation planning?",
        "policy_answer_now": "NOT_APPROVED_YET",
        "allowed_next_gate_if_reviewed": "D89_FINAL_HUMAN_CONFIRMATION",
        "blocked_now": blockers.get("hard_blockers", []),
        "required_before_any_real_apply": [
            "D89_FINAL_HUMAN_CONFIRMATION",
            "D66_RECHECK",
            "FULL_TEST_DISCOVERY",
            "ROLLBACK_MANIFEST_RECONFIRMATION",
            "EXPLICIT_APPLY_SCOPE_APPROVAL",
        ],
        "not_allowed": [
            "actual_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_network_call",
            "git_commit_or_push_by_ai",
        ],
    }


def build_apply_still_blocked(request_id: str) -> Dict[str, Any]:
    return {
        "state": "D88_APPLY_STILL_BLOCKED",
        "ok": True,
        "request_id": request_id,
        "created_at": now(),
        "apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
        "canonical_memory_mutation_allowed_now": False,
        "external_ai_call_allowed_now": False,
        "git_action_by_ai_allowed_now": False,
        "reason": "D88 creates a higher-policy review request only. It does not grant apply permission.",
        "next_required_gate": "D89_FINAL_HUMAN_CONFIRMATION",
    }


def create_higher_policy_approval_request(
    root: str | Path = ".",
    d87_report_path: str = D87_REPORT,
    d87_capsule_path: str = D87_CAPSULE,
    d87_blockers_path: str = D87_BLOCKERS,
    output_path: str = OUT,
    packet_output_path: str = PACKET_OUT,
    blockers_output_path: str = BLOCKERS_OUT,
) -> Dict[str, Any]:
    root = Path(root).resolve()

    d87 = read_json(root / d87_report_path, {}) or {}
    capsule = read_json(root / d87_capsule_path, {}) or {}
    blockers = read_json(root / d87_blockers_path, {}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    validate_d87(d87, capsule, blockers, errors)

    capsule_id = str(capsule.get("capsule_id") or (d87.get("summary") or {}).get("capsule_id") or "")
    package_id = str(capsule.get("package_id") or (d87.get("summary") or {}).get("package_id") or "")
    review_id = str(capsule.get("review_id") or (d87.get("summary") or {}).get("review_id") or "")

    request_id = "d88-" + sha256_json(
        {
            "capsule_id": capsule_id,
            "package_id": package_id,
            "review_id": review_id,
            "d87_decision": d87.get("decision"),
        }
    )[:16]

    ok = not errors
    decision = "HIGHER_POLICY_APPROVAL_REQUEST_READY" if ok else "HIGHER_POLICY_APPROVAL_REQUEST_BLOCKED"
    result = "D88_HIGHER_POLICY_APPROVAL_REQUEST_CREATED" if ok else "D88_HIGHER_POLICY_APPROVAL_REQUEST_BLOCKED"

    review_packet = build_review_packet(request_id, d87, capsule, blockers)
    apply_still_blocked = build_apply_still_blocked(request_id)

    if ok:
        write_json(root / packet_output_path, review_packet)
        write_json(root / blockers_output_path, apply_still_blocked)

    report = {
        "state": "D88_HIGHER_POLICY_APPROVAL_REQUEST",
        "result": result,
        "route": "FIELD_INTENT_HIGHER_POLICY_APPROVAL_REQUEST",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "request_id": request_id,
        "review_packet_path": str(root / packet_output_path) if ok else "",
        "apply_still_blocked_path": str(root / blockers_output_path) if ok else "",
        "input_reports": {
            "d87_report_path": str(root / d87_report_path),
            "d87_capsule_path": str(root / d87_capsule_path),
            "d87_blockers_path": str(root / d87_blockers_path),
        },
        "evidence": {
            "capsule_id": capsule_id,
            "package_id": package_id,
            "review_id": review_id,
            "d87_decision": d87.get("decision"),
            "d87_next_gate": capsule.get("next_gate"),
            "apply_allowed_now": False,
        },
        "review_packet": review_packet if ok else {},
        "apply_still_blocked": apply_still_blocked,
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "higher_policy_request_only": True,
            "approval_not_granted": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "request_id": request_id,
            "capsule_id": capsule_id,
            "package_id": package_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "higher_policy_request_created": ok,
            "review_packet_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D89 should create final human confirmation artifact. Real apply remains blocked.",
        },
    }

    write_json(root / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_higher_policy_approval_request(), ensure_ascii=False, indent=2))
