from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


D89_REPORT = "reports/d89_final_human_confirmation.json"
D89_STATEMENT = "reports/d89_human_confirmation_statement.json"
D89_SCOPE = "reports/d89_d90_planning_scope.json"

OUT = "reports/d90_controlled_apply_plan.json"
PREVIEW_OUT = "reports/d90_apply_command_preview.json"
CHECKLIST_OUT = "reports/d90_manual_review_checklist.json"


REQUIRED_D89_DECISION = "FINAL_HUMAN_CONFIRMATION_READY"
REQUIRED_D90_GATE = "D90_CONTROLLED_APPLY_PLAN"
REQUIRED_CONFIRMATION_PHRASE = "CONFIRM_D89_FINAL_HUMAN_REVIEW_FOR_D90_PLANNING_ONLY"

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

D90_NOT_EXECUTE = [
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


def validate_d89(
    d89: Dict[str, Any],
    statement: Dict[str, Any],
    scope: Dict[str, Any],
    errors: List[str],
) -> None:
    if not d89:
        errors.append("D89 final human confirmation report missing or unreadable")
        return

    if d89.get("ok") is not True:
        errors.append("D89 ok flag is not true")
    if d89.get("decision") != REQUIRED_D89_DECISION:
        errors.append(f"D89 decision invalid: {d89.get('decision')}")

    guard = d89.get("guardrails") if isinstance(d89.get("guardrails"), dict) else {}
    validate_false_flags("D89 guardrail", guard, errors)

    if guard.get("final_human_confirmation_only") is not True:
        errors.append("D89 final_human_confirmation_only is not true")
    if guard.get("d90_planning_only") is not True:
        errors.append("D89 d90_planning_only is not true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D89 approval_for_real_apply is not false")

    if not statement:
        errors.append("D89 human confirmation statement missing or unreadable")
    else:
        if statement.get("ok") is not True:
            errors.append("D89 statement ok flag is not true")
        if statement.get("confirmation_phrase") != REQUIRED_CONFIRMATION_PHRASE:
            errors.append(f"D89 confirmation phrase invalid: {statement.get('confirmation_phrase')}")
        if statement.get("approved_next_gate") != REQUIRED_D90_GATE:
            errors.append(f"D89 approved_next_gate invalid: {statement.get('approved_next_gate')}")
        for item in D90_NOT_EXECUTE:
            if item not in statement.get("not_approved", []):
                errors.append(f"D89 statement missing not_approved item: {item}")

    if not scope:
        errors.append("D89 D90 planning scope missing or unreadable")
    else:
        if scope.get("ok") is not True:
            errors.append("D89 D90 scope ok flag is not true")
        if scope.get("next_gate") != REQUIRED_D90_GATE:
            errors.append(f"D89 D90 scope next_gate invalid: {scope.get('next_gate')}")
        for key in (
            "apply_allowed_after_d89",
            "route_insert_allowed_after_d89",
            "protected_core_mutation_allowed_after_d89",
        ):
            if scope.get(key) is not False:
                errors.append(f"D89 D90 scope {key} is not false")

        allowed = scope.get("d90_allowed_to_create")
        if not isinstance(allowed, list):
            errors.append("D89 D90 scope d90_allowed_to_create missing")
        else:
            for item in (
                "controlled_apply_plan_json",
                "explicit_scope_diff_summary",
                "pre_apply_command_preview",
                "manual_review_checklist",
            ):
                if item not in allowed:
                    errors.append(f"D89 D90 scope missing allowed create item: {item}")

        must_not = scope.get("d90_must_not_execute")
        if not isinstance(must_not, list):
            errors.append("D89 D90 scope d90_must_not_execute missing")
        else:
            for item in D90_NOT_EXECUTE:
                if item not in must_not:
                    errors.append(f"D89 D90 scope missing must-not-execute item: {item}")


def build_apply_command_preview(plan_id: str, d89: Dict[str, Any], statement: Dict[str, Any]) -> Dict[str, Any]:
    evidence = d89.get("evidence") if isinstance(d89.get("evidence"), dict) else {}

    return {
        "state": "D90_APPLY_COMMAND_PREVIEW",
        "ok": True,
        "plan_id": plan_id,
        "created_at": now(),
        "preview_only": True,
        "source_confirmation_id": d89.get("confirmation_id") or statement.get("confirmation_id"),
        "source_request_id": evidence.get("request_id") or statement.get("source_request_id"),
        "source_package_id": evidence.get("package_id") or statement.get("source_package_id"),
        "commands_are_documentation_only": True,
        "commands_must_not_be_executed_by_ai": True,
        "pre_apply_command_preview": [
            "# PREVIEW ONLY — do not execute automatically",
            "python -m unittest discover -s tests -v",
            "python -m py_compile runtime_experimental/*.py",
            "git diff --stat",
            "git status --short",
            "# Apply remains blocked until D91 explicit apply-scope approval.",
        ],
        "blocked_commands": [
            "git apply",
            "python -c '<runtime mutation>'",
            "git commit",
            "git push",
            "route insert",
            "direct protected-core edit",
        ],
    }


def build_manual_review_checklist(plan_id: str) -> Dict[str, Any]:
    return {
        "state": "D90_MANUAL_REVIEW_CHECKLIST",
        "ok": True,
        "plan_id": plan_id,
        "created_at": now(),
        "human_review_required": True,
        "checklist": [
            "Confirm D89 statement exists and scope is D90 planning only.",
            "Confirm D85 rollback manifest exists.",
            "Confirm D86 local regression results passed.",
            "Confirm no protected core mutation is planned.",
            "Confirm no route insertion is planned.",
            "Confirm no external AI/network call is required.",
            "Confirm D91 explicit apply-scope approval is required before any real apply.",
        ],
        "must_remain_false": {
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
        },
    }


def build_controlled_plan(plan_id: str, d89: Dict[str, Any], statement: Dict[str, Any], scope: Dict[str, Any]) -> Dict[str, Any]:
    evidence = d89.get("evidence") if isinstance(d89.get("evidence"), dict) else {}

    return {
        "state": "D90_CONTROLLED_APPLY_PLAN_PREVIEW",
        "ok": True,
        "plan_id": plan_id,
        "created_at": now(),
        "mode": "PLAN_PREVIEW_ONLY",
        "source_confirmation_id": d89.get("confirmation_id") or statement.get("confirmation_id"),
        "source_request_id": evidence.get("request_id") or statement.get("source_request_id"),
        "source_capsule_id": evidence.get("capsule_id") or statement.get("source_capsule_id"),
        "source_package_id": evidence.get("package_id") or statement.get("source_package_id"),
        "source_review_id": evidence.get("review_id") or statement.get("source_review_id"),
        "allowed_to_create": scope.get("d90_allowed_to_create", []),
        "must_not_execute": scope.get("d90_must_not_execute", []),
        "plan_summary": {
            "goal": "Create a controlled apply plan preview for human review only.",
            "real_apply_allowed": False,
            "route_insert_allowed": False,
            "protected_core_mutation_allowed": False,
            "ai_git_action_allowed": False,
        },
        "explicit_scope_diff_summary": {
            "planned_files_to_touch": [],
            "protected_files_to_touch": [],
            "route_insertions": [],
            "runtime_mutations": [],
            "status": "NO_REAL_DIFF_PREPARED_D90_IS_PREVIEW_ONLY",
        },
        "required_next_gate": "D91_EXPLICIT_APPLY_SCOPE_APPROVAL",
    }


def create_controlled_apply_plan(
    root: str | Path = ".",
    d89_report_path: str = D89_REPORT,
    d89_statement_path: str = D89_STATEMENT,
    d89_scope_path: str = D89_SCOPE,
    output_path: str = OUT,
    preview_output_path: str = PREVIEW_OUT,
    checklist_output_path: str = CHECKLIST_OUT,
) -> Dict[str, Any]:
    root = Path(root).resolve()

    d89 = read_json(root / d89_report_path, {}) or {}
    statement = read_json(root / d89_statement_path, {}) or {}
    scope = read_json(root / d89_scope_path, {}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    validate_d89(d89, statement, scope, errors)

    confirmation_id = str(d89.get("confirmation_id") or statement.get("confirmation_id") or "")
    request_id = str((d89.get("evidence") or {}).get("request_id") or statement.get("source_request_id") or "")
    package_id = str((d89.get("evidence") or {}).get("package_id") or statement.get("source_package_id") or "")

    plan_id = "d90-" + sha256_json(
        {
            "confirmation_id": confirmation_id,
            "request_id": request_id,
            "package_id": package_id,
            "d89_decision": d89.get("decision"),
        }
    )[:16]

    ok = not errors
    decision = "CONTROLLED_APPLY_PLAN_PREVIEW_READY" if ok else "CONTROLLED_APPLY_PLAN_PREVIEW_BLOCKED"
    result = "D90_CONTROLLED_APPLY_PLAN_CREATED" if ok else "D90_CONTROLLED_APPLY_PLAN_BLOCKED"

    plan = build_controlled_plan(plan_id, d89, statement, scope)
    preview = build_apply_command_preview(plan_id, d89, statement)
    checklist = build_manual_review_checklist(plan_id)

    if ok:
        write_json(root / preview_output_path, preview)
        write_json(root / checklist_output_path, checklist)

    report = {
        "state": "D90_CONTROLLED_APPLY_PLAN",
        "result": result,
        "route": "FIELD_INTENT_CONTROLLED_APPLY_PLAN",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "plan_id": plan_id,
        "apply_command_preview_path": str(root / preview_output_path) if ok else "",
        "manual_review_checklist_path": str(root / checklist_output_path) if ok else "",
        "input_reports": {
            "d89_report_path": str(root / d89_report_path),
            "d89_statement_path": str(root / d89_statement_path),
            "d89_scope_path": str(root / d89_scope_path),
        },
        "plan": plan if ok else {},
        "apply_command_preview": preview if ok else {},
        "manual_review_checklist": checklist if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "controlled_plan_only": True,
            "preview_only": True,
            "approval_for_real_apply": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "plan_id": plan_id,
            "confirmation_id": confirmation_id,
            "request_id": request_id,
            "package_id": package_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "controlled_apply_plan_preview_created": ok,
            "manual_review_checklist_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D91 should request explicit apply-scope approval. Real apply remains blocked.",
        },
    }

    write_json(root / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_controlled_apply_plan(), ensure_ascii=False, indent=2))
