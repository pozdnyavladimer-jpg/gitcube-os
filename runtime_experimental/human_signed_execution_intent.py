
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D94_REPORT = "reports/d94_final_execution_approval_request.json"
D94_PHRASE = "reports/d94_explicit_human_execution_phrase.json"
D94_BLOCKERS = "reports/d94_final_apply_blockers_report.json"

OUT = "reports/d95_human_signed_execution_intent.json"
SIGNATURE_OUT = "reports/d95_execution_intent_signature.json"
STILL_BLOCKED_OUT = "reports/d95_apply_still_blocked.json"

REQ_D94_DECISION = "FINAL_EXECUTION_APPROVAL_REQUEST_READY"
REQ_D95_GATE = "D95_HUMAN_SIGNED_EXECUTION_INTENT"
REQ_D94_PHRASE = "APPROVE_D94_FINAL_EXECUTION_REQUEST_REVIEW_ONLY"
REQ_D95_PHRASE = "APPROVE_D95_HUMAN_SIGNED_EXECUTION_INTENT_FOR_D96_REGRESSION_ONLY"

FALSE_FLAGS = [
    "external_ai_called",
    "network_accessed",
    "runtime_code_mutated",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "actual_apply_executed",
    "route_inserted",
    "git_commit_by_ai",
]

FORBIDDEN_REAL_ACTIONS = [
    "actual_apply",
    "route_insert",
    "protected_core_mutation",
    "canonical_memory_overwrite",
    "external_ai_network_call",
    "git_commit_or_push_by_ai",
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


def check_false_flags(label, data, errors):
    for key in FALSE_FLAGS:
        if data.get(key) is not False:
            errors.append(f"{label}.{key} must be false")


def validate_d94(d94, phrase, blockers):
    errors = []
    warnings = []

    if not d94:
        errors.append("missing D94 final execution approval request")
        return errors, warnings

    if d94.get("ok") is not True:
        errors.append("D94 ok must be true")
    if d94.get("decision") != REQ_D94_DECISION:
        errors.append(f"D94 decision invalid: {d94.get('decision')}")

    guard = d94.get("guardrails") if isinstance(d94.get("guardrails"), dict) else {}
    check_false_flags("D94.guardrails", guard, errors)
    if guard.get("final_execution_request_only") is not True:
        errors.append("D94 final_execution_request_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D94 approval_for_real_apply must be false")
    if guard.get("human_review_required") is not True:
        errors.append("D94 human_review_required must be true")

    req = d94.get("approval_request") if isinstance(d94.get("approval_request"), dict) else {}
    if not req:
        errors.append("D94 embedded approval_request missing")
    else:
        if req.get("mode") != "FINAL_EXECUTION_REVIEW_REQUEST_ONLY":
            errors.append(f"D94 request mode invalid: {req.get('mode')}")
        if req.get("review_phrase") != REQ_D94_PHRASE:
            errors.append("D94 review_phrase invalid")
        if req.get("approval_not_granted") is not True:
            errors.append("D94 approval_not_granted must be true")
        for key in ["real_apply_allowed", "route_insert_allowed", "protected_core_mutation_allowed"]:
            if req.get(key) is not False:
                errors.append(f"D94 request {key} must be false")
        if req.get("allowed_next_gate_if_reviewed") != REQ_D95_GATE:
            errors.append("D94 allowed_next_gate_if_reviewed must be D95")

    if not phrase:
        errors.append("missing D94 explicit human execution phrase")
    else:
        if phrase.get("ok") is not True:
            errors.append("D94 phrase ok must be true")
        if phrase.get("required_phrase") != REQ_D94_PHRASE:
            errors.append("D94 phrase required_phrase invalid")
        if phrase.get("approval_scope") != "REVIEW_REQUEST_ONLY":
            errors.append("D94 phrase approval_scope must be REVIEW_REQUEST_ONLY")
        if phrase.get("approved_next_gate_if_reviewed") != REQ_D95_GATE:
            errors.append("D94 phrase approved_next_gate_if_reviewed must be D95")
        for item in FORBIDDEN_REAL_ACTIONS:
            if item not in phrase.get("not_approved", []):
                errors.append(f"D94 phrase not_approved missing {item}")

    if not blockers:
        errors.append("missing D94 final apply blockers report")
    else:
        if blockers.get("ok") is not True:
            errors.append("D94 blockers ok must be true")
        for key in [
            "apply_allowed_now",
            "route_insert_allowed_now",
            "protected_core_mutation_allowed_now",
            "canonical_memory_mutation_allowed_now",
            "external_ai_call_allowed_now",
            "git_action_by_ai_allowed_now",
        ]:
            if blockers.get(key) is not False:
                errors.append(f"D94 blockers {key} must be false")
        if blockers.get("next_required_gate") != REQ_D95_GATE:
            errors.append("D94 blockers next_required_gate must be D95")

    return errors, warnings


def build_signature(intent_id, request_id, gate_id, package_id):
    payload = {
        "intent_id": intent_id,
        "request_id": request_id,
        "gate_id": gate_id,
        "package_id": package_id,
        "approval_phrase": REQ_D95_PHRASE,
        "scope": "D96_FINAL_LOCAL_FULL_REGRESSION_ONLY",
        "forbidden_real_actions": FORBIDDEN_REAL_ACTIONS,
    }
    return {
        "state": "D95_EXECUTION_INTENT_SIGNATURE",
        "ok": True,
        "intent_id": intent_id,
        "request_id": request_id,
        "gate_id": gate_id,
        "package_id": package_id,
        "created_at": now(),
        "signer": "human_operator",
        "signature_method": "deterministic_local_json_signature",
        "approval_phrase": REQ_D95_PHRASE,
        "signature_sha256": hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "signed_scope": "D96_FINAL_LOCAL_FULL_REGRESSION_ONLY",
        "not_approved": FORBIDDEN_REAL_ACTIONS,
    }


def build_still_blocked(intent_id):
    return {
        "state": "D95_APPLY_STILL_BLOCKED",
        "ok": True,
        "intent_id": intent_id,
        "created_at": now(),
        "apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
        "canonical_memory_mutation_allowed_now": False,
        "external_ai_call_allowed_now": False,
        "git_action_by_ai_allowed_now": False,
        "reason": "D95 signs intent only for D96 final local full regression. It does not grant execution permission.",
        "next_required_gate": "D96_FINAL_LOCAL_FULL_REGRESSION",
    }


def build_intent(intent_id, request_id, gate_id, package_id, signature):
    return {
        "state": "D95_HUMAN_SIGNED_EXECUTION_INTENT_ARTIFACT",
        "ok": True,
        "intent_id": intent_id,
        "request_id": request_id,
        "gate_id": gate_id,
        "package_id": package_id,
        "created_at": now(),
        "mode": "HUMAN_SIGNED_INTENT_FOR_REGRESSION_ONLY",
        "signed_phrase": REQ_D95_PHRASE,
        "signature_sha256": signature.get("signature_sha256"),
        "approved_next_gate": "D96_FINAL_LOCAL_FULL_REGRESSION",
        "approved_scope": [
            "run_full_local_regression",
            "collect_full_regression_evidence",
            "produce_final_regression_report",
        ],
        "not_approved": FORBIDDEN_REAL_ACTIONS,
        "apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
    }


def create_human_signed_execution_intent(root="."):
    root = Path(root).resolve()

    d94 = read_json(root / D94_REPORT, {}) or {}
    phrase = read_json(root / D94_PHRASE, {}) or {}
    blockers = read_json(root / D94_BLOCKERS, {}) or {}

    errors, warnings = validate_d94(d94, phrase, blockers)

    request_id = str(d94.get("request_id") or phrase.get("request_id") or blockers.get("request_id") or "")
    gate_id = str(d94.get("gate_id") or phrase.get("gate_id") or blockers.get("gate_id") or "")
    package_id = str(d94.get("package_id") or phrase.get("package_id") or blockers.get("package_id") or "")

    intent_id = "d95-" + digest({
        "request_id": request_id,
        "gate_id": gate_id,
        "package_id": package_id,
        "d94_decision": d94.get("decision"),
    })

    ok = not errors
    decision = "HUMAN_SIGNED_EXECUTION_INTENT_READY" if ok else "HUMAN_SIGNED_EXECUTION_INTENT_BLOCKED"
    result = "D95_HUMAN_SIGNED_EXECUTION_INTENT_CREATED" if ok else "D95_HUMAN_SIGNED_EXECUTION_INTENT_BLOCKED"

    signature = build_signature(intent_id, request_id, gate_id, package_id)
    still_blocked = build_still_blocked(intent_id)
    intent = build_intent(intent_id, request_id, gate_id, package_id, signature)

    if ok:
        write_json(root / SIGNATURE_OUT, signature)
        write_json(root / STILL_BLOCKED_OUT, still_blocked)

    report = {
        "state": "D95_HUMAN_SIGNED_EXECUTION_INTENT",
        "result": result,
        "route": "FIELD_INTENT_HUMAN_SIGNED_EXECUTION_INTENT",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "intent_id": intent_id,
        "request_id": request_id,
        "gate_id": gate_id,
        "package_id": package_id,
        "signature_path": str(root / SIGNATURE_OUT) if ok else "",
        "apply_still_blocked_path": str(root / STILL_BLOCKED_OUT) if ok else "",
        "input_reports": {
            "d94_report_path": str(root / D94_REPORT),
            "d94_phrase_path": str(root / D94_PHRASE),
            "d94_blockers_path": str(root / D94_BLOCKERS),
        },
        "signed_intent": intent if ok else {},
        "execution_intent_signature": signature if ok else {},
        "apply_still_blocked": still_blocked if ok else {},
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
            "d96_regression_only": True,
            "approval_for_real_apply": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "intent_id": intent_id,
            "request_id": request_id,
            "gate_id": gate_id,
            "package_id": package_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "human_signed_execution_intent_created": ok,
            "signature_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D96 may run final local full regression evidence. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_human_signed_execution_intent(), ensure_ascii=False, indent=2))
