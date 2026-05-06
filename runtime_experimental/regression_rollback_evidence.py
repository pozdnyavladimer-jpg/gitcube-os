from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


D84_REPORT = "reports/d84_sandbox_writer_output_review.json"
OUT = "reports/d85_regression_rollback_evidence.json"
ROLLBACK_OUT = "reports/d85_rollback_manifest.json"
CHECKLIST_OUT = "reports/d85_regression_checklist.json"


PROTECTED_PREFIXES = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]

ALLOWED_CANDIDATE_PREFIXES = [
    "runtime_experimental/ai_sandbox_work/",
    "reports/",
    "tests/",
]

REQUIRED_ROLLBACK_ITEMS = [
    "pre_apply_git_sha",
    "candidate_files",
    "created_files",
    "mutated_files",
    "restore_strategy",
    "verification_commands",
    "human_review_required",
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


def safe_path(value: str) -> str:
    raw = str(value or "").strip().replace("\\", "/").lstrip("/")
    return "/".join(x for x in raw.split("/") if x and x not in (".", ".."))


def sha256_json(data: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def path_allowed(path: str) -> bool:
    p = safe_path(path)
    if any(p.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return False
    return any(p.startswith(prefix) for prefix in ALLOWED_CANDIDATE_PREFIXES)


def validate_d84(d84: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
    if not d84:
        errors.append("D84 report missing or unreadable")
        return {}

    if d84.get("ok") is not True:
        errors.append("D84 ok flag is not true")
    if d84.get("decision") != "SANDBOX_WRITER_OUTPUT_REVIEW_READY":
        errors.append(f"D84 decision invalid: {d84.get('decision')}")

    guard = d84.get("guardrails") if isinstance(d84.get("guardrails"), dict) else {}
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
            errors.append(f"D84 guardrail {key} is not false")
    if guard.get("sandbox_output_review_only") is not True:
        errors.append("D84 sandbox_output_review_only is not true")
    if guard.get("writer_output_candidate_only") is not True:
        errors.append("D84 writer_output_candidate_only is not true")

    review = d84.get("review") if isinstance(d84.get("review"), dict) else {}
    if not review:
        errors.append("D84 review object missing")
    else:
        if review.get("approved_for_guarded_apply") is not False:
            errors.append("D84 must not approve guarded apply")
        if review.get("approved_for_route_insert") is not False:
            errors.append("D84 must not approve route insert")
        if review.get("approved_for_protected_core") is not False:
            errors.append("D84 must not approve protected core")
        if review.get("approved_for_next_sandbox_gate") is not True:
            errors.append("D84 must approve next sandbox gate")

    writer_output_path = str(d84.get("writer_output_path") or "")
    if not writer_output_path:
        errors.append("D84 writer_output_path missing")
        return {}

    writer_output = read_json(writer_output_path, {}) or {}
    if not writer_output:
        errors.append("D84 writer output file missing or unreadable")
        return {}

    if writer_output.get("mode") != "SANDBOX_OUTPUT_CANDIDATE_ONLY":
        errors.append(f"D84 writer output mode invalid: {writer_output.get('mode')}")

    candidate_files = writer_output.get("candidate_files")
    if not isinstance(candidate_files, list) or not candidate_files:
        errors.append("D84 writer output candidate_files missing")
    else:
        for f in candidate_files:
            if not path_allowed(str(f)):
                errors.append(f"candidate file outside allowed sandbox scope: {f}")

    wguard = writer_output.get("guardrails") if isinstance(writer_output.get("guardrails"), dict) else {}
    for key in (
        "actual_apply_executed",
        "route_inserted",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "external_ai_called",
        "network_accessed",
        "git_commit_by_ai",
    ):
        if wguard.get(key) is not False:
            errors.append(f"D84 writer output guardrail {key} is not false")
    if wguard.get("sandbox_output_only") is not True:
        errors.append("D84 writer output sandbox_output_only is not true")

    return writer_output


def build_rollback_manifest(package_id: str, d84: Dict[str, Any], writer_output: Dict[str, Any]) -> Dict[str, Any]:
    candidate_files = [safe_path(str(p)) for p in writer_output.get("candidate_files", [])]
    evidence = d84.get("evidence") if isinstance(d84.get("evidence"), dict) else {}

    return {
        "state": "D85_ROLLBACK_MANIFEST",
        "ok": True,
        "package_id": package_id,
        "created_at": now(),
        "pre_apply_git_sha": "NO_APPLY_EXECUTED",
        "source_review_id": d84.get("review_id"),
        "source_handoff_id": evidence.get("handoff_id"),
        "source_proposal_id": evidence.get("proposal_id"),
        "candidate_files": candidate_files,
        "created_files": candidate_files,
        "mutated_files": [],
        "protected_files": PROTECTED_PREFIXES,
        "restore_strategy": {
            "type": "delete_created_sandbox_candidates_only",
            "commands_are_documentation_only": True,
            "commands": [
                "git status --short",
                "git clean -n runtime_experimental/ai_sandbox_work reports tests",
                "manual review before any clean/apply",
            ],
        },
        "verification_commands": [
            "python -m py_compile runtime_experimental/sandbox_writer_output_review.py",
            "python -m unittest tests.test_d84_sandbox_writer_output_review -v",
            "python -m py_compile runtime_experimental/regression_rollback_evidence.py",
            "python -m unittest tests.test_d85_regression_rollback_evidence -v",
        ],
        "human_review_required": True,
        "actual_rollback_executed": False,
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_touched": False,
    }


def build_regression_checklist(package_id: str, d84: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "state": "D85_REGRESSION_CHECKLIST",
        "ok": True,
        "package_id": package_id,
        "created_at": now(),
        "source_review_id": d84.get("review_id"),
        "required_before_any_apply": [
            "D66_RECHECK",
            "D64_SAFE_MUTATION_GATE_RECHECK",
            "UNIT_TESTS",
            "REGRESSION_TESTS",
            "ROLLBACK_MANIFEST_PRESENT",
            "HUMAN_OR_HIGHER_POLICY_APPROVAL",
        ],
        "commands_to_run_manually": [
            "python -m unittest discover -s tests -v",
            "python -m py_compile runtime_experimental/*.py",
            "git diff --stat",
            "git status --short",
        ],
        "pass_condition": {
            "all_tests_green": True,
            "rollback_manifest_present": True,
            "no_protected_core_mutation": True,
            "no_route_insert": True,
            "no_actual_apply": True,
        },
        "not_allowed": [
            "auto_apply_runtime_mutation",
            "direct_core_edit",
            "route_insert",
            "commit_generated_patch_without_human_review",
        ],
    }


def validate_package(manifest: Dict[str, Any], checklist: Dict[str, Any], errors: List[str]) -> None:
    for item in REQUIRED_ROLLBACK_ITEMS:
        if item not in manifest:
            errors.append(f"rollback manifest missing required item: {item}")

    if manifest.get("actual_rollback_executed") is not False:
        errors.append("rollback manifest actual_rollback_executed must be false")
    if manifest.get("actual_apply_executed") is not False:
        errors.append("rollback manifest actual_apply_executed must be false")
    if manifest.get("route_inserted") is not False:
        errors.append("rollback manifest route_inserted must be false")
    if manifest.get("protected_core_touched") is not False:
        errors.append("rollback manifest protected_core_touched must be false")
    if manifest.get("human_review_required") is not True:
        errors.append("rollback manifest human_review_required must be true")

    for f in manifest.get("candidate_files", []):
        if not path_allowed(str(f)):
            errors.append(f"rollback candidate path outside allowed scope: {f}")

    pass_condition = checklist.get("pass_condition") if isinstance(checklist.get("pass_condition"), dict) else {}
    for key in (
        "all_tests_green",
        "rollback_manifest_present",
        "no_protected_core_mutation",
        "no_route_insert",
        "no_actual_apply",
    ):
        if pass_condition.get(key) is not True:
            errors.append(f"regression checklist pass condition {key} is not true")


def create_regression_rollback_evidence(
    root: str | Path = ".",
    d84_report_path: str = D84_REPORT,
    output_path: str = OUT,
    rollback_output_path: str = ROLLBACK_OUT,
    checklist_output_path: str = CHECKLIST_OUT,
) -> Dict[str, Any]:
    root = Path(root).resolve()
    d84 = read_json(root / d84_report_path, {}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    writer_output = validate_d84(d84, errors)

    review_id = str(d84.get("review_id") or "")
    handoff_id = str((d84.get("evidence") or {}).get("handoff_id") or "")
    proposal_id = str((d84.get("evidence") or {}).get("proposal_id") or "")

    package_id = "d85-" + sha256_json(
        {
            "review_id": review_id,
            "handoff_id": handoff_id,
            "proposal_id": proposal_id,
            "candidate_files": writer_output.get("candidate_files") if writer_output else [],
        }
    )[:16]

    rollback_manifest = build_rollback_manifest(package_id, d84, writer_output) if writer_output else {}
    regression_checklist = build_regression_checklist(package_id, d84) if d84 else {}

    if rollback_manifest and regression_checklist:
        validate_package(rollback_manifest, regression_checklist, errors)

    ok = not errors
    decision = "REGRESSION_ROLLBACK_EVIDENCE_READY" if ok else "REGRESSION_ROLLBACK_EVIDENCE_BLOCKED"
    result = "D85_REGRESSION_ROLLBACK_EVIDENCE_CREATED" if ok else "D85_REGRESSION_ROLLBACK_EVIDENCE_BLOCKED"

    if ok:
        write_json(root / rollback_output_path, rollback_manifest)
        write_json(root / checklist_output_path, regression_checklist)

    report = {
        "state": "D85_REGRESSION_ROLLBACK_EVIDENCE",
        "result": result,
        "route": "FIELD_INTENT_REGRESSION_ROLLBACK_EVIDENCE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "package_id": package_id,
        "rollback_manifest_path": str(root / rollback_output_path) if ok else "",
        "regression_checklist_path": str(root / checklist_output_path) if ok else "",
        "input_reports": {
            "d84_report_path": str(root / d84_report_path),
        },
        "evidence": {
            "review_id": review_id,
            "handoff_id": handoff_id,
            "proposal_id": proposal_id,
            "candidate_files": writer_output.get("candidate_files") if writer_output else [],
        },
        "rollback_manifest": rollback_manifest if ok else {},
        "regression_checklist": regression_checklist if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "rollback_evidence_only": True,
            "regression_evidence_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "package_id": package_id,
            "review_id": review_id,
            "candidate_files_count": len(writer_output.get("candidate_files", [])) if writer_output else 0,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "regression_rollback_evidence_created": ok,
            "rollback_manifest_created": ok,
            "regression_checklist_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D86 can run local regression command probes and collect results; real apply still blocked.",
        },
    }

    write_json(root / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_regression_rollback_evidence(), ensure_ascii=False, indent=2))
