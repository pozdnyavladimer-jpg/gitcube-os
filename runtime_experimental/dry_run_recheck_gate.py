
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D92_REPORT = "reports/d92_guarded_apply_dry_run_package.json"
D92_DIFF = "reports/d92_apply_scope_diff_preview.json"
D92_RECHECK = "reports/d92_pre_apply_recheck_commands.json"
D92_ABORTS = "reports/d92_abort_conditions.json"

OUT = "reports/d93_dry_run_recheck_gate.json"
RESULTS = "reports/d93_recheck_results.json"
BLOCKED = "reports/d93_apply_still_blocked.json"
D94_SCOPE = "reports/d93_d94_execution_gate_scope.json"

REQ_D92_DECISION = "GUARDED_APPLY_DRY_RUN_PACKAGE_READY"
REQ_D93_GATE = "D93_DRY_RUN_RECHECK_GATE"

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


def list_is_empty(label, value, errors):
    if value not in ([], None):
        errors.append(f"{label} must be empty for D93 dry-run recheck")


def validate_d92(d92, diff, recheck, aborts):
    errors = []
    warnings = []

    if not d92:
        errors.append("missing D92 guarded apply dry-run package report")
        return errors, warnings

    if d92.get("ok") is not True:
        errors.append("D92 ok must be true")
    if d92.get("decision") != REQ_D92_DECISION:
        errors.append(f"D92 decision invalid: {d92.get('decision')}")

    guard = d92.get("guardrails") if isinstance(d92.get("guardrails"), dict) else {}
    check_false_flags("D92.guardrails", guard, errors)
    if guard.get("guarded_dry_run_package_only") is not True:
        errors.append("D92 guarded_dry_run_package_only must be true")
    if guard.get("apply_allowed_now") is not False:
        errors.append("D92 apply_allowed_now must be false")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D92 approval_for_real_apply must be false")

    pkg = d92.get("dry_run_package") if isinstance(d92.get("dry_run_package"), dict) else {}
    if not pkg:
        errors.append("D92 embedded dry_run_package missing")
    else:
        if pkg.get("mode") != "GUARDED_DRY_RUN_PACKAGE_ONLY":
            errors.append(f"D92 dry_run_package mode invalid: {pkg.get('mode')}")
        if pkg.get("required_next_gate") != REQ_D93_GATE:
            errors.append(f"D92 required_next_gate invalid: {pkg.get('required_next_gate')}")
        contract = pkg.get("dry_run_contract") if isinstance(pkg.get("dry_run_contract"), dict) else {}
        check_false_flags("D92.dry_run_contract", contract, errors)
        if contract.get("dry_run_package_only") is not True:
            errors.append("D92 dry_run_contract.dry_run_package_only must be true")

    if not diff:
        errors.append("missing D92 diff preview")
    else:
        if diff.get("ok") is not True:
            errors.append("D92 diff ok must be true")
        if diff.get("dry_run_only") is not True:
            errors.append("D92 diff dry_run_only must be true")
        if diff.get("documentation_only") is not True:
            errors.append("D92 diff documentation_only must be true")
        if diff.get("allowed_next_gate") != REQ_D93_GATE:
            errors.append(f"D92 diff allowed_next_gate invalid: {diff.get('allowed_next_gate')}")
        for key in [
            "planned_files_to_touch",
            "protected_files_to_touch",
            "route_insertions",
            "runtime_mutations",
            "canonical_memory_changes",
            "external_calls",
        ]:
            list_is_empty(f"D92.diff.{key}", diff.get(key), errors)

    if not recheck:
        errors.append("missing D92 pre-apply recheck commands")
    else:
        if recheck.get("ok") is not True:
            errors.append("D92 recheck ok must be true")
        if recheck.get("commands_are_documentation_only") is not True:
            errors.append("D92 recheck commands_are_documentation_only must be true")
        if recheck.get("commands_must_not_be_executed_by_ai") is not True:
            errors.append("D92 recheck commands_must_not_be_executed_by_ai must be true")
        if recheck.get("human_may_run_manually") is not True:
            errors.append("D92 recheck human_may_run_manually must be true")
        blocked = recheck.get("blocked_commands", [])
        for item in ["git apply", "git commit", "git push", "route insert"]:
            if item not in blocked:
                errors.append(f"D92 recheck blocked_commands missing {item}")

    if not aborts:
        errors.append("missing D92 abort conditions")
    else:
        if aborts.get("ok") is not True:
            errors.append("D92 aborts ok must be true")
        abort_if = aborts.get("abort_if", [])
        if not isinstance(abort_if, list) or len(abort_if) < 5:
            errors.append("D92 abort_if list is too small")
        must = aborts.get("must_remain_false") if isinstance(aborts.get("must_remain_false"), dict) else {}
        check_false_flags("D92.aborts.must_remain_false", must, errors)

    return errors, warnings


def build_recheck_results(gate_id, package_id, d92, diff, recheck, aborts):
    return {
        "state": "D93_RECHECK_RESULTS",
        "ok": True,
        "gate_id": gate_id,
        "package_id": package_id,
        "created_at": now(),
        "verified_artifacts": [
            "d92_guarded_apply_dry_run_package",
            "d92_apply_scope_diff_preview",
            "d92_pre_apply_recheck_commands",
            "d92_abort_conditions",
        ],
        "verified_conditions": {
            "d92_package_ready": True,
            "diff_is_dry_run_only": True,
            "diff_touches_no_files": True,
            "commands_are_documentation_only": True,
            "abort_conditions_present": True,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
        },
        "commands_executed_by_d93": [],
        "commands_not_executed_reason": "D93 verifies D92 command preview as documentation only.",
    }


def build_apply_still_blocked(gate_id):
    return {
        "state": "D93_APPLY_STILL_BLOCKED",
        "ok": True,
        "gate_id": gate_id,
        "created_at": now(),
        "apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
        "canonical_memory_mutation_allowed_now": False,
        "external_ai_call_allowed_now": False,
        "git_action_by_ai_allowed_now": False,
        "reason": "D93 verifies the dry-run package only. It does not grant execution permission.",
        "next_required_gate": "D94_FINAL_EXECUTION_APPROVAL_REQUEST",
    }


def build_d94_scope(gate_id, package_id):
    return {
        "state": "D93_D94_EXECUTION_GATE_SCOPE",
        "ok": True,
        "gate_id": gate_id,
        "package_id": package_id,
        "created_at": now(),
        "allowed_next_gate": "D94_FINAL_EXECUTION_APPROVAL_REQUEST",
        "d94_allowed_to_create": [
            "final_execution_approval_request",
            "explicit_human_execution_phrase",
            "final_apply_blockers_report",
        ],
        "d94_must_not_execute": FORBIDDEN_REAL_ACTIONS,
        "apply_allowed_after_d93": False,
        "route_insert_allowed_after_d93": False,
        "protected_core_mutation_allowed_after_d93": False,
        "human_review_required": True,
        "required_phrase_for_later_gate": "APPROVE_D94_FINAL_EXECUTION_REQUEST_REVIEW_ONLY",
    }


def create_dry_run_recheck_gate(root="."):
    root = Path(root).resolve()

    d92 = read_json(root / D92_REPORT, {}) or {}
    diff = read_json(root / D92_DIFF, {}) or {}
    recheck = read_json(root / D92_RECHECK, {}) or {}
    aborts = read_json(root / D92_ABORTS, {}) or {}

    errors, warnings = validate_d92(d92, diff, recheck, aborts)

    package_id = str(d92.get("package_id") or diff.get("package_id") or recheck.get("package_id") or aborts.get("package_id") or "")
    gate_id = "d93-" + digest({
        "package_id": package_id,
        "d92_decision": d92.get("decision"),
        "d92_result": d92.get("result"),
    })

    ok = not errors
    decision = "DRY_RUN_RECHECK_GATE_READY" if ok else "DRY_RUN_RECHECK_GATE_BLOCKED"
    result = "D93_DRY_RUN_RECHECK_GATE_CREATED" if ok else "D93_DRY_RUN_RECHECK_GATE_BLOCKED"

    results = build_recheck_results(gate_id, package_id, d92, diff, recheck, aborts)
    blocked = build_apply_still_blocked(gate_id)
    d94_scope = build_d94_scope(gate_id, package_id)

    if ok:
        write_json(root / RESULTS, results)
        write_json(root / BLOCKED, blocked)
        write_json(root / D94_SCOPE, d94_scope)

    report = {
        "state": "D93_DRY_RUN_RECHECK_GATE",
        "result": result,
        "route": "FIELD_INTENT_DRY_RUN_RECHECK_GATE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "gate_id": gate_id,
        "package_id": package_id,
        "recheck_results_path": str(root / RESULTS) if ok else "",
        "apply_still_blocked_path": str(root / BLOCKED) if ok else "",
        "d94_scope_path": str(root / D94_SCOPE) if ok else "",
        "input_reports": {
            "d92_report_path": str(root / D92_REPORT),
            "d92_diff_path": str(root / D92_DIFF),
            "d92_recheck_path": str(root / D92_RECHECK),
            "d92_aborts_path": str(root / D92_ABORTS),
        },
        "recheck_results": results if ok else {},
        "apply_still_blocked": blocked if ok else {},
        "d94_scope": d94_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "dry_run_recheck_only": True,
            "commands_executed_by_d93": False,
            "approval_for_real_apply": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "gate_id": gate_id,
            "package_id": package_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "dry_run_recheck_gate_created": ok,
            "d92_package_verified": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D94 may request final execution approval review only. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_dry_run_recheck_gate(), ensure_ascii=False, indent=2))
