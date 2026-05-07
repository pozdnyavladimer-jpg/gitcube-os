
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D93_REPORT = "reports/d93_dry_run_recheck_gate.json"
D93_RESULTS = "reports/d93_recheck_results.json"
D93_BLOCKED = "reports/d93_apply_still_blocked.json"
D93_D94_SCOPE = "reports/d93_d94_execution_gate_scope.json"

OUT = "reports/d94_final_execution_approval_request.json"
PHRASE_OUT = "reports/d94_explicit_human_execution_phrase.json"
BLOCKERS_OUT = "reports/d94_final_apply_blockers_report.json"

REQ_D93_DECISION = "DRY_RUN_RECHECK_GATE_READY"
REQ_D94_GATE = "D94_FINAL_EXECUTION_APPROVAL_REQUEST"
REQ_D94_PHRASE = "APPROVE_D94_FINAL_EXECUTION_REQUEST_REVIEW_ONLY"

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

D94_ALLOWED_TO_CREATE = [
    "final_execution_approval_request",
    "explicit_human_execution_phrase",
    "final_apply_blockers_report",
]

D94_MUST_NOT_EXECUTE = [
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


def validate_d93(d93, results, blocked, scope):
    errors = []
    warnings = []

    if not d93:
        errors.append("missing D93 dry-run recheck gate report")
        return errors, warnings

    if d93.get("ok") is not True:
        errors.append("D93 ok must be true")
    if d93.get("decision") != REQ_D93_DECISION:
        errors.append(f"D93 decision invalid: {d93.get('decision')}")

    guard = d93.get("guardrails") if isinstance(d93.get("guardrails"), dict) else {}
    check_false_flags("D93.guardrails", guard, errors)
    if guard.get("dry_run_recheck_only") is not True:
        errors.append("D93 dry_run_recheck_only must be true")
    if guard.get("commands_executed_by_d93") is not False:
        errors.append("D93 commands_executed_by_d93 must be false")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D93 approval_for_real_apply must be false")

    if not results:
        errors.append("missing D93 recheck results")
    else:
        if results.get("ok") is not True:
            errors.append("D93 results ok must be true")
        verified = results.get("verified_conditions") if isinstance(results.get("verified_conditions"), dict) else {}
        for key in [
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "external_ai_called",
            "network_accessed",
            "git_commit_by_ai",
        ]:
            if verified.get(key) is not False:
                errors.append(f"D93 verified_conditions.{key} must be false")
        if results.get("commands_executed_by_d93") not in ([], None):
            errors.append("D93 results commands_executed_by_d93 must be empty")

    if not blocked:
        errors.append("missing D93 apply-still-blocked report")
    else:
        for key in [
            "apply_allowed_now",
            "route_insert_allowed_now",
            "protected_core_mutation_allowed_now",
            "canonical_memory_mutation_allowed_now",
            "external_ai_call_allowed_now",
            "git_action_by_ai_allowed_now",
        ]:
            if blocked.get(key) is not False:
                errors.append(f"D93 blocked.{key} must be false")
        if blocked.get("next_required_gate") != REQ_D94_GATE:
            errors.append(f"D93 blocked next_required_gate invalid: {blocked.get('next_required_gate')}")

    if not scope:
        errors.append("missing D93 D94 execution gate scope")
    else:
        if scope.get("ok") is not True:
            errors.append("D93 D94 scope ok must be true")
        if scope.get("allowed_next_gate") != REQ_D94_GATE:
            errors.append(f"D93 D94 allowed_next_gate invalid: {scope.get('allowed_next_gate')}")
        for item in D94_ALLOWED_TO_CREATE:
            if item not in scope.get("d94_allowed_to_create", []):
                errors.append(f"D93 D94 scope missing allowed item: {item}")
        for item in D94_MUST_NOT_EXECUTE:
            if item not in scope.get("d94_must_not_execute", []):
                errors.append(f"D93 D94 scope missing must-not-execute item: {item}")
        if scope.get("apply_allowed_after_d93") is not False:
            errors.append("D93 scope apply_allowed_after_d93 must be false")
        if scope.get("route_insert_allowed_after_d93") is not False:
            errors.append("D93 scope route_insert_allowed_after_d93 must be false")
        if scope.get("protected_core_mutation_allowed_after_d93") is not False:
            errors.append("D93 scope protected_core_mutation_allowed_after_d93 must be false")
        if scope.get("human_review_required") is not True:
            errors.append("D93 scope human_review_required must be true")
        if scope.get("required_phrase_for_later_gate") != REQ_D94_PHRASE:
            errors.append("D93 scope required phrase invalid")

    return errors, warnings


def build_human_phrase(request_id, gate_id, package_id):
    return {
        "state": "D94_EXPLICIT_HUMAN_EXECUTION_PHRASE",
        "ok": True,
        "request_id": request_id,
        "gate_id": gate_id,
        "package_id": package_id,
        "created_at": now(),
        "required_phrase": REQ_D94_PHRASE,
        "approval_scope": "REVIEW_REQUEST_ONLY",
        "human_statement": (
            "I approve only the D94 final execution request review. "
            "This does not authorize real apply, route insertion, protected-core mutation, "
            "canonical memory overwrite, external AI/network calls, or AI git actions."
        ),
        "not_approved": D94_MUST_NOT_EXECUTE,
        "approved_next_gate_if_reviewed": "D95_HUMAN_SIGNED_EXECUTION_INTENT",
    }


def build_blockers(request_id, gate_id, package_id):
    return {
        "state": "D94_FINAL_APPLY_BLOCKERS_REPORT",
        "ok": True,
        "request_id": request_id,
        "gate_id": gate_id,
        "package_id": package_id,
        "created_at": now(),
        "apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
        "canonical_memory_mutation_allowed_now": False,
        "external_ai_call_allowed_now": False,
        "git_action_by_ai_allowed_now": False,
        "blockers": [
            "no D95 human signed execution intent",
            "no D96 final local full regression evidence",
            "no D97 protected-core no-touch reconfirmation",
            "no D98 rollback/restore command pack",
            "no D99 final guarded execution capsule",
        ],
        "reason": "D94 creates a final execution approval request only. It does not grant execution permission.",
        "next_required_gate": "D95_HUMAN_SIGNED_EXECUTION_INTENT",
    }


def build_request(request_id, gate_id, package_id, d93, scope):
    return {
        "state": "D94_FINAL_EXECUTION_APPROVAL_REQUEST_REVIEW",
        "ok": True,
        "request_id": request_id,
        "gate_id": gate_id,
        "package_id": package_id,
        "created_at": now(),
        "mode": "FINAL_EXECUTION_REVIEW_REQUEST_ONLY",
        "source_gate_id": d93.get("gate_id") or gate_id,
        "source_package_id": d93.get("package_id") or package_id,
        "review_question": "May this fully rechecked dry-run package proceed to D95 human signed execution intent?",
        "review_phrase": REQ_D94_PHRASE,
        "approval_not_granted": True,
        "real_apply_allowed": False,
        "route_insert_allowed": False,
        "protected_core_mutation_allowed": False,
        "allowed_next_gate_if_reviewed": "D95_HUMAN_SIGNED_EXECUTION_INTENT",
        "required_before_any_real_apply": [
            "D95_HUMAN_SIGNED_EXECUTION_INTENT",
            "D96_FINAL_LOCAL_FULL_REGRESSION",
            "D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION",
            "D98_ROLLBACK_RESTORE_COMMAND_PACK",
            "D99_FINAL_GUARDED_EXECUTION_CAPSULE",
        ],
        "d94_must_not_execute": scope.get("d94_must_not_execute", D94_MUST_NOT_EXECUTE),
    }


def create_final_execution_approval_request(root="."):
    root = Path(root).resolve()

    d93 = read_json(root / D93_REPORT, {}) or {}
    results = read_json(root / D93_RESULTS, {}) or {}
    blocked = read_json(root / D93_BLOCKED, {}) or {}
    scope = read_json(root / D93_D94_SCOPE, {}) or {}

    errors, warnings = validate_d93(d93, results, blocked, scope)

    gate_id = str(d93.get("gate_id") or scope.get("gate_id") or "")
    package_id = str(d93.get("package_id") or scope.get("package_id") or "")
    request_id = "d94-" + digest({
        "gate_id": gate_id,
        "package_id": package_id,
        "d93_decision": d93.get("decision"),
    })

    ok = not errors
    decision = "FINAL_EXECUTION_APPROVAL_REQUEST_READY" if ok else "FINAL_EXECUTION_APPROVAL_REQUEST_BLOCKED"
    result = "D94_FINAL_EXECUTION_APPROVAL_REQUEST_CREATED" if ok else "D94_FINAL_EXECUTION_APPROVAL_REQUEST_BLOCKED"

    request = build_request(request_id, gate_id, package_id, d93, scope)
    phrase = build_human_phrase(request_id, gate_id, package_id)
    blockers = build_blockers(request_id, gate_id, package_id)

    if ok:
        write_json(root / PHRASE_OUT, phrase)
        write_json(root / BLOCKERS_OUT, blockers)

    report = {
        "state": "D94_FINAL_EXECUTION_APPROVAL_REQUEST",
        "result": result,
        "route": "FIELD_INTENT_FINAL_EXECUTION_APPROVAL_REQUEST",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "request_id": request_id,
        "gate_id": gate_id,
        "package_id": package_id,
        "phrase_path": str(root / PHRASE_OUT) if ok else "",
        "blockers_path": str(root / BLOCKERS_OUT) if ok else "",
        "input_reports": {
            "d93_report_path": str(root / D93_REPORT),
            "d93_results_path": str(root / D93_RESULTS),
            "d93_blocked_path": str(root / D93_BLOCKED),
            "d93_d94_scope_path": str(root / D93_D94_SCOPE),
        },
        "approval_request": request if ok else {},
        "explicit_human_execution_phrase": phrase if ok else {},
        "final_apply_blockers_report": blockers if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "final_execution_request_only": True,
            "approval_for_real_apply": False,
            "human_review_required": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "request_id": request_id,
            "gate_id": gate_id,
            "package_id": package_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "final_execution_approval_request_created": ok,
            "explicit_human_execution_phrase_created": ok,
            "final_apply_blockers_report_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D95 may create human signed execution intent. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_final_execution_approval_request(), ensure_ascii=False, indent=2))
