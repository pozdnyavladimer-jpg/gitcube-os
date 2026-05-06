from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


D86_REPORT = "reports/d86_local_regression_runner.json"
D86_RESULTS = "reports/d86_local_regression_results.json"
D85_REPORT = "reports/d85_regression_rollback_evidence.json"
D85_ROLLBACK = "reports/d85_rollback_manifest.json"
D85_CHECKLIST = "reports/d85_regression_checklist.json"

OUT = "reports/d87_final_pre_apply_safety_capsule.json"
CAPSULE_OUT = "reports/d87_pre_apply_safety_capsule.json"
BLOCKERS_OUT = "reports/d87_apply_blockers.json"


REQUIRED_PRE_APPLY_EVIDENCE = [
    "D81_AI_PROPOSAL_INTAKE_READY",
    "D82_HUMAN_SIGNED_INTENT_READY",
    "D83_SANDBOX_WRITER_HANDOFF_READY",
    "D84_SANDBOX_WRITER_OUTPUT_REVIEW_READY",
    "D85_REGRESSION_ROLLBACK_EVIDENCE_READY",
    "D86_LOCAL_REGRESSION_PASSED",
]

HARD_BLOCKERS = [
    "actual_apply_executed",
    "route_inserted",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "external_ai_called",
    "network_accessed",
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


def validate_false_guardrails(name: str, guard: Dict[str, Any], errors: List[str]) -> None:
    for key in HARD_BLOCKERS:
        if guard.get(key) is not False:
            errors.append(f"{name} guardrail {key} is not false")


def validate_d86(d86: Dict[str, Any], results: Dict[str, Any], errors: List[str]) -> None:
    if not d86:
        errors.append("D86 report missing or unreadable")
        return

    if d86.get("ok") is not True:
        errors.append("D86 ok flag is not true")
    if d86.get("decision") != "LOCAL_REGRESSION_PASSED":
        errors.append(f"D86 decision invalid: {d86.get('decision')}")

    guard = d86.get("guardrails") if isinstance(d86.get("guardrails"), dict) else {}
    validate_false_guardrails("D86", guard, errors)

    if guard.get("local_regression_only") is not True:
        errors.append("D86 local_regression_only is not true")
    if guard.get("allowlisted_commands_only") is not True:
        errors.append("D86 allowlisted_commands_only is not true")

    summary = d86.get("summary") if isinstance(d86.get("summary"), dict) else {}
    if int(summary.get("commands_failed_count") or 0) != 0:
        errors.append("D86 summary reports failed commands")

    if not results:
        errors.append("D86 results missing or unreadable")
        return

    if results.get("ok") is not True:
        errors.append("D86 results ok flag is not true")
    if int(results.get("commands_failed_count") or 0) != 0:
        errors.append("D86 results has failed commands")
    if int(results.get("commands_run_count") or 0) <= 0:
        errors.append("D86 results has no commands run")

    for key in (
        "actual_apply_executed",
        "route_inserted",
        "protected_core_touched",
        "network_accessed",
        "external_ai_called",
    ):
        if results.get(key) is not False:
            errors.append(f"D86 result flag {key} is not false")


def validate_d85(
    d85: Dict[str, Any],
    rollback: Dict[str, Any],
    checklist: Dict[str, Any],
    errors: List[str],
) -> None:
    if not d85:
        errors.append("D85 report missing or unreadable")
        return

    if d85.get("ok") is not True:
        errors.append("D85 ok flag is not true")
    if d85.get("decision") != "REGRESSION_ROLLBACK_EVIDENCE_READY":
        errors.append(f"D85 decision invalid: {d85.get('decision')}")

    guard = d85.get("guardrails") if isinstance(d85.get("guardrails"), dict) else {}
    validate_false_guardrails("D85", guard, errors)

    if guard.get("rollback_evidence_only") is not True:
        errors.append("D85 rollback_evidence_only is not true")
    if guard.get("regression_evidence_only") is not True:
        errors.append("D85 regression_evidence_only is not true")

    if not rollback:
        errors.append("D85 rollback manifest missing or unreadable")
    else:
        if rollback.get("human_review_required") is not True:
            errors.append("D85 rollback manifest human_review_required is not true")
        for key in (
            "actual_rollback_executed",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_touched",
        ):
            if rollback.get(key) is not False:
                errors.append(f"D85 rollback {key} is not false")

    if not checklist:
        errors.append("D85 checklist missing or unreadable")
    else:
        pass_condition = checklist.get("pass_condition") if isinstance(checklist.get("pass_condition"), dict) else {}
        for key in (
            "all_tests_green",
            "rollback_manifest_present",
            "no_protected_core_mutation",
            "no_route_insert",
            "no_actual_apply",
        ):
            if pass_condition.get(key) is not True:
                errors.append(f"D85 checklist pass condition {key} is not true")


def create_blockers() -> Dict[str, Any]:
    return {
        "state": "D87_APPLY_BLOCKERS",
        "ok": True,
        "created_at": now(),
        "apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
        "external_ai_call_allowed_now": False,
        "git_action_by_ai_allowed_now": False,
        "hard_blockers": [
            "no explicit D88 higher policy approval",
            "no guarded apply command generated",
            "no runtime mutation execution",
            "no route insertion permission",
            "no protected-core mutation permission",
        ],
        "required_before_apply_can_be_discussed": [
            "D88_HIGHER_POLICY_APPROVAL_REQUEST",
            "D89_FINAL_HUMAN_CONFIRMATION",
            "D66_RECHECK",
            "FULL_TEST_DISCOVERY",
            "ROLLBACK_MANIFEST_RECONFIRMATION",
        ],
    }


def create_final_pre_apply_safety_capsule(
    root: str | Path = ".",
    d86_report_path: str = D86_REPORT,
    d86_results_path: str = D86_RESULTS,
    d85_report_path: str = D85_REPORT,
    d85_rollback_path: str = D85_ROLLBACK,
    d85_checklist_path: str = D85_CHECKLIST,
    output_path: str = OUT,
    capsule_output_path: str = CAPSULE_OUT,
    blockers_output_path: str = BLOCKERS_OUT,
) -> Dict[str, Any]:
    root = Path(root).resolve()

    d86 = read_json(root / d86_report_path, {}) or {}
    results = read_json(root / d86_results_path, {}) or {}
    d85 = read_json(root / d85_report_path, {}) or {}
    rollback = read_json(root / d85_rollback_path, {}) or {}
    checklist = read_json(root / d85_checklist_path, {}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    validate_d86(d86, results, errors)
    validate_d85(d85, rollback, checklist, errors)

    package_id = str(d86.get("package_id") or d85.get("package_id") or "")
    review_id = str(d86.get("review_id") or (d85.get("evidence") or {}).get("review_id") or "")
    capsule_id = "d87-" + sha256_json(
        {
            "package_id": package_id,
            "review_id": review_id,
            "d86_decision": d86.get("decision"),
            "d85_decision": d85.get("decision"),
        }
    )[:16]

    ok = not errors
    decision = "FINAL_PRE_APPLY_SAFETY_CAPSULE_READY" if ok else "FINAL_PRE_APPLY_SAFETY_CAPSULE_BLOCKED"
    result = "D87_FINAL_PRE_APPLY_SAFETY_CAPSULE_CREATED" if ok else "D87_FINAL_PRE_APPLY_SAFETY_CAPSULE_BLOCKED"

    blockers = create_blockers()

    capsule = {
        "state": "D87_PRE_APPLY_SAFETY_CAPSULE",
        "ok": ok,
        "capsule_id": capsule_id,
        "created_at": now(),
        "package_id": package_id,
        "review_id": review_id,
        "evidence_chain": {
            "d85_decision": d85.get("decision"),
            "d86_decision": d86.get("decision"),
            "d86_commands_run_count": (results or {}).get("commands_run_count"),
            "d86_commands_failed_count": (results or {}).get("commands_failed_count"),
            "rollback_manifest_present": bool(rollback),
            "regression_checklist_present": bool(checklist),
        },
        "required_pre_apply_evidence": REQUIRED_PRE_APPLY_EVIDENCE,
        "approval_state": {
            "ready_for_higher_policy_review": ok,
            "ready_for_real_apply": False,
            "ready_for_route_insert": False,
            "ready_for_protected_core_mutation": False,
        },
        "hard_no_mutation_flags": {
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
        },
        "next_gate": "D88_HIGHER_POLICY_APPROVAL_REQUEST",
    }

    if ok:
        write_json(root / capsule_output_path, capsule)
        write_json(root / blockers_output_path, blockers)

    report = {
        "state": "D87_FINAL_PRE_APPLY_SAFETY_CAPSULE",
        "result": result,
        "route": "FIELD_INTENT_FINAL_PRE_APPLY_SAFETY_CAPSULE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "capsule_id": capsule_id,
        "capsule_path": str(root / capsule_output_path) if ok else "",
        "blockers_path": str(root / blockers_output_path) if ok else "",
        "input_reports": {
            "d86_report_path": str(root / d86_report_path),
            "d86_results_path": str(root / d86_results_path),
            "d85_report_path": str(root / d85_report_path),
            "d85_rollback_path": str(root / d85_rollback_path),
            "d85_checklist_path": str(root / d85_checklist_path),
        },
        "capsule": capsule if ok else {},
        "blockers": blockers,
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "final_capsule_only": True,
            "pre_apply_review_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "capsule_id": capsule_id,
            "package_id": package_id,
            "review_id": review_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "final_pre_apply_capsule_created": ok,
            "ready_for_higher_policy_review": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D88 should request explicit higher-policy approval. Real apply remains blocked.",
        },
    }

    write_json(root / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_final_pre_apply_safety_capsule(), ensure_ascii=False, indent=2))
