from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


D90_REPORT = "reports/d90_controlled_apply_plan.json"
D90_PREVIEW = "reports/d90_apply_command_preview.json"
D90_CHECKLIST = "reports/d90_manual_review_checklist.json"

OUT = "reports/d91_explicit_apply_scope_approval.json"
SCOPE_REQUEST_OUT = "reports/d91_apply_scope_request.json"
STILL_BLOCKED_OUT = "reports/d91_apply_still_blocked.json"


REQUIRED_D90_DECISION = "CONTROLLED_APPLY_PLAN_PREVIEW_READY"
REQUIRED_NEXT_GATE = "D91_EXPLICIT_APPLY_SCOPE_APPROVAL"
APPROVAL_PHRASE = "APPROVE_D91_SCOPE_FOR_D92_GUARDED_APPLY_DRY_RUN_ONLY"

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


def validate_d90(
    d90: Dict[str, Any],
    preview: Dict[str, Any],
    checklist: Dict[str, Any],
    errors: List[str],
) -> None:
    if not d90:
        errors.append("D90 controlled apply plan report missing or unreadable")
        return

    if d90.get("ok") is not True:
        errors.append("D90 ok flag is not true")
    if d90.get("decision") != REQUIRED_D90_DECISION:
        errors.append(f"D90 decision invalid: {d90.get('decision')}")

    guard = d90.get("guardrails") if isinstance(d90.get("guardrails"), dict) else {}
    validate_false_flags("D90 guardrail", guard, errors)

    if guard.get("controlled_plan_only") is not True:
        errors.append("D90 controlled_plan_only is not true")
    if guard.get("preview_only") is not True:
        errors.append("D90 preview_only is not true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D90 approval_for_real_apply is not false")

    plan = d90.get("plan") if isinstance(d90.get("plan"), dict) else {}
    if not plan:
        errors.append("D90 embedded plan missing")
    else:
        if plan.get("mode") != "PLAN_PREVIEW_ONLY":
            errors.append(f"D90 plan mode invalid: {plan.get('mode')}")
        if plan.get("required_next_gate") != REQUIRED_NEXT_GATE:
            errors.append(f"D90 required_next_gate invalid: {plan.get('required_next_gate')}")

        summary = plan.get("plan_summary") if isinstance(plan.get("plan_summary"), dict) else {}
        for key in (
            "real_apply_allowed",
            "route_insert_allowed",
            "protected_core_mutation_allowed",
            "ai_git_action_allowed",
        ):
            if summary.get(key) is not False:
                errors.append(f"D90 plan_summary {key} is not false")

    if not preview:
        errors.append("D90 command preview missing or unreadable")
    else:
        if preview.get("ok") is not True:
            errors.append("D90 preview ok flag is not true")
        if preview.get("preview_only") is not True:
            errors.append("D90 preview_only is not true")
        if preview.get("commands_are_documentation_only") is not True:
            errors.append("D90 commands_are_documentation_only is not true")
        if preview.get("commands_must_not_be_executed_by_ai") is not True:
            errors.append("D90 commands_must_not_be_executed_by_ai is not true")

        blocked = preview.get("blocked_commands")
        if not isinstance(blocked, list) or not blocked:
            errors.append("D90 blocked_commands missing")
        else:
            for item in ("git apply", "git commit", "git push", "route insert"):
                if item not in blocked:
                    errors.append(f"D90 blocked_commands missing item: {item}")

    if not checklist:
        errors.append("D90 manual review checklist missing or unreadable")
    else:
        if checklist.get("ok") is not True:
            errors.append("D90 checklist ok flag is not true")
        if checklist.get("human_review_required") is not True:
            errors.append("D90 checklist human_review_required is not true")

        must = checklist.get("must_remain_false") if isinstance(checklist.get("must_remain_false"), dict) else {}
        validate_false_flags("D90 checklist must_remain_false", must, errors)


def build_scope_request(approval_id: str, d90: Dict[str, Any], preview: Dict[str, Any]) -> Dict[str, Any]:
    summary = d90.get("summary") if isinstance(d90.get("summary"), dict) else {}
    plan = d90.get("plan") if isinstance(d90.get("plan"), dict) else {}

    return {
        "state": "D91_APPLY_SCOPE_REQUEST",
        "ok": True,
        "approval_id": approval_id,
        "created_at": now(),
        "approval_phrase": APPROVAL_PHRASE,
        "approval_mode": "SCOPE_APPROVAL_FOR_D92_GUARDED_APPLY_DRY_RUN_ONLY",
        "source_plan_id": d90.get("plan_id") or summary.get("plan_id"),
        "source_confirmation_id": summary.get("confirmation_id") or plan.get("source_confirmation_id"),
        "source_package_id": summary.get("package_id") or plan.get("source_package_id"),
        "scope_statement": (
            "D91 approves only the creation of a D92 guarded apply dry-run package. "
            "It does not approve real apply, route insertion, protected-core mutation, external AI calls, or AI git actions."
        ),
        "approved_next_gate": "D92_GUARDED_APPLY_DRY_RUN_PACKAGE",
        "allowed_scope_for_d92": [
            "generate_guarded_apply_dry_run_package",
            "generate_apply_scope_diff_preview",
            "generate_pre_apply_recheck_commands",
            "generate_abort_conditions",
        ],
        "forbidden_real_actions": FORBIDDEN_REAL_ACTIONS,
        "source_preview_commands_are_documentation_only": preview.get("commands_are_documentation_only"),
    }


def build_apply_still_blocked(approval_id: str) -> Dict[str, Any]:
    return {
        "state": "D91_APPLY_STILL_BLOCKED",
        "ok": True,
        "approval_id": approval_id,
        "created_at": now(),
        "apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
        "canonical_memory_mutation_allowed_now": False,
        "external_ai_call_allowed_now": False,
        "git_action_by_ai_allowed_now": False,
        "reason": "D91 approves D92 dry-run package generation only. Real apply still requires a later explicit execution gate.",
        "next_required_gate": "D92_GUARDED_APPLY_DRY_RUN_PACKAGE",
    }


def create_explicit_apply_scope_approval(
    root: str | Path = ".",
    d90_report_path: str = D90_REPORT,
    d90_preview_path: str = D90_PREVIEW,
    d90_checklist_path: str = D90_CHECKLIST,
    output_path: str = OUT,
    scope_request_output_path: str = SCOPE_REQUEST_OUT,
    still_blocked_output_path: str = STILL_BLOCKED_OUT,
) -> Dict[str, Any]:
    root = Path(root).resolve()

    d90 = read_json(root / d90_report_path, {}) or {}
    preview = read_json(root / d90_preview_path, {}) or {}
    checklist = read_json(root / d90_checklist_path, {}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    validate_d90(d90, preview, checklist, errors)

    plan_id = str(d90.get("plan_id") or (d90.get("summary") or {}).get("plan_id") or "")
    confirmation_id = str((d90.get("summary") or {}).get("confirmation_id") or "")
    package_id = str((d90.get("summary") or {}).get("package_id") or "")

    approval_id = "d91-" + sha256_json(
        {
            "plan_id": plan_id,
            "confirmation_id": confirmation_id,
            "package_id": package_id,
            "d90_decision": d90.get("decision"),
        }
    )[:16]

    ok = not errors
    decision = "EXPLICIT_APPLY_SCOPE_APPROVAL_READY" if ok else "EXPLICIT_APPLY_SCOPE_APPROVAL_BLOCKED"
    result = "D91_EXPLICIT_APPLY_SCOPE_APPROVAL_CREATED" if ok else "D91_EXPLICIT_APPLY_SCOPE_APPROVAL_BLOCKED"

    scope_request = build_scope_request(approval_id, d90, preview)
    still_blocked = build_apply_still_blocked(approval_id)

    if ok:
        write_json(root / scope_request_output_path, scope_request)
        write_json(root / still_blocked_output_path, still_blocked)

    report = {
        "state": "D91_EXPLICIT_APPLY_SCOPE_APPROVAL",
        "result": result,
        "route": "FIELD_INTENT_EXPLICIT_APPLY_SCOPE_APPROVAL",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "approval_id": approval_id,
        "scope_request_path": str(root / scope_request_output_path) if ok else "",
        "apply_still_blocked_path": str(root / still_blocked_output_path) if ok else "",
        "input_reports": {
            "d90_report_path": str(root / d90_report_path),
            "d90_preview_path": str(root / d90_preview_path),
            "d90_checklist_path": str(root / d90_checklist_path),
        },
        "evidence": {
            "plan_id": plan_id,
            "confirmation_id": confirmation_id,
            "package_id": package_id,
            "d90_decision": d90.get("decision"),
            "d90_required_next_gate": (d90.get("plan") or {}).get("required_next_gate") if isinstance(d90.get("plan"), dict) else "",
            "apply_allowed_now": False,
        },
        "scope_request": scope_request if ok else {},
        "apply_still_blocked": still_blocked,
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "scope_approval_only": True,
            "d92_dry_run_only": True,
            "approval_for_real_apply": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "approval_id": approval_id,
            "plan_id": plan_id,
            "confirmation_id": confirmation_id,
            "package_id": package_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "explicit_apply_scope_approval_created": ok,
            "d92_dry_run_scope_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D92 can create a guarded apply dry-run package. Real apply remains blocked.",
        },
    }

    write_json(root / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_explicit_apply_scope_approval(), ensure_ascii=False, indent=2))
