from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


D78_REPORT = "reports/d78_narrow_adapter_dry_run_diff.json"
D64_REQUEST = "reports/d64_safe_mutation_gate_request.json"
D66_REVIEW = "reports/d66_core_guard_reviewer_report.json"
OUT = "reports/d79_policy_verification_gate.json"


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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(data: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _validate_d78(root: Path, d78: Dict[str, Any], errors: List[str], warnings: List[str]) -> Dict[str, Any]:
    if not d78:
        errors.append("D78 dry-run diff report missing or unreadable")
        return {}

    if d78.get("ok") is not True:
        errors.append("D78 ok flag is not true")

    if d78.get("decision") != "NARROW_ADAPTER_DRY_RUN_DIFF_READY":
        errors.append(f"D78 decision is not NARROW_ADAPTER_DRY_RUN_DIFF_READY: {d78.get('decision')}")

    guard = d78.get("guardrails") if isinstance(d78.get("guardrails"), dict) else {}
    required_false = [
        "runtime_code_mutated",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "external_ai_called",
        "actual_apply_executed",
        "route_inserted",
    ]
    for key in required_false:
        if guard.get(key) is not False:
            errors.append(f"D78 guardrail {key} is not false")
    if guard.get("dry_run_only") is not True:
        errors.append("D78 dry_run_only is not true")

    pkg = d78.get("dry_run_diff_package")
    if not isinstance(pkg, dict):
        errors.append("D78 dry_run_diff_package missing or invalid")
        return {}

    if pkg.get("route_insert_allowed_now") is not False:
        errors.append("D78 route_insert_allowed_now is not false")
    if pkg.get("apply_allowed_now") is not False:
        errors.append("D78 apply_allowed_now is not false")
    if pkg.get("actual_files_touched") not in ([], None):
        errors.append("D78 actual_files_touched is not empty")

    child = safe_path(str(pkg.get("child_module_path", "")))
    if not child:
        errors.append("D78 child_module_path missing")
    elif not child.startswith("runtime_experimental/differentiated_modules/"):
        errors.append(f"D78 child module outside differentiated_modules: {child}")
    elif not (root / child).exists():
        errors.append(f"D78 child module does not exist on disk: {child}")

    source = safe_path(str(pkg.get("source_node", "")))
    if not source:
        errors.append("D78 source_node missing")

    diff_path = str(pkg.get("diff_output_path", ""))
    diff_abs = Path(diff_path)
    if not diff_abs.is_absolute():
        diff_abs = root / safe_path(diff_path)

    diff_text = ""
    if not diff_abs.exists():
        errors.append(f"D78 diff file missing: {diff_abs}")
    else:
        diff_text = diff_abs.read_text(encoding="utf-8")
        if "DRY-RUN ONLY" not in diff_text:
            errors.append("D78 diff does not contain DRY-RUN ONLY marker")
        if "DO NOT APPLY AUTOMATICALLY" not in diff_text:
            errors.append("D78 diff does not contain DO NOT APPLY AUTOMATICALLY marker")
        for gate in ("D66_RECHECK", "D76_CHILD_PROBE_PASSED", "ROLLBACK_MANIFEST", "HUMAN_OR_HIGHER_POLICY_APPROVAL"):
            if gate not in diff_text:
                errors.append(f"D78 diff missing required marker: {gate}")

        expected_hash = str(pkg.get("diff_sha256", ""))
        actual_hash = sha256_text(diff_text)
        if expected_hash and expected_hash != actual_hash:
            errors.append("D78 diff sha256 mismatch")

    pkg["_verified_diff_text_len"] = len(diff_text)
    return pkg


def _validate_d64(d64: Dict[str, Any], errors: List[str], warnings: List[str]) -> Dict[str, Any]:
    if not d64:
        warnings.append("D64 safe mutation gate request missing; D79 continues in dry-run-only verification mode")
        return {"available": False}

    if d64.get("ok") is not True:
        errors.append("D64 ok flag is not true")

    guard = d64.get("guardrails") if isinstance(d64.get("guardrails"), dict) else {}
    for key in ("actual_apply_executed", "runtime_code_mutated", "protected_core_mutated", "canonical_memory_mutated", "external_ai_called"):
        if key in guard and guard.get(key) is not False:
            errors.append(f"D64 guardrail {key} is not false")

    return {
        "available": True,
        "ok": d64.get("ok"),
        "decision": d64.get("decision"),
        "result": d64.get("result"),
    }


def _validate_d66(d66: Dict[str, Any], errors: List[str], warnings: List[str]) -> Dict[str, Any]:
    if not d66:
        warnings.append("D66 core guard reviewer report missing; D79 continues but real apply must remain blocked")
        return {"available": False}

    guard = d66.get("guardrails") if isinstance(d66.get("guardrails"), dict) else {}
    for key in ("actual_apply_executed", "runtime_code_mutated", "protected_core_mutated", "canonical_memory_mutated", "external_ai_called"):
        if key in guard and guard.get(key) is not False:
            errors.append(f"D66 guardrail {key} is not false")

    # D66 may intentionally reject protected-core edits. That is not a failure for D79.
    # D79 only verifies the dry-run package and keeps real apply blocked.
    return {
        "available": True,
        "ok": d66.get("ok"),
        "decision": d66.get("decision"),
        "result": d66.get("result"),
        "reason": d66.get("reason"),
    }


def verify_policy_gate(
    root: str | Path = ".",
    d78_report_path: str = D78_REPORT,
    d64_request_path: str = D64_REQUEST,
    d66_review_path: str = D66_REVIEW,
    output_path: str = OUT,
) -> Dict[str, Any]:
    root = Path(root).resolve()
    d78 = read_json(root / d78_report_path, {}) or {}
    d64 = read_json(root / d64_request_path, {}) or {}
    d66 = read_json(root / d66_review_path, {}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    pkg = _validate_d78(root, d78, errors, warnings)
    d64_evidence = _validate_d64(d64, errors, warnings)
    d66_evidence = _validate_d66(d66, errors, warnings)

    source = safe_path(str(pkg.get("source_node", ""))) if pkg else ""
    child = safe_path(str(pkg.get("child_module_path", ""))) if pkg else ""
    adapter = str(pkg.get("adapter_name", "")) if pkg else ""
    contract_id = str(pkg.get("contract_id", "")) if pkg else ""

    ok = not errors
    decision = "POLICY_VERIFIED_DRY_RUN_READY" if ok else "POLICY_VERIFICATION_BLOCKED"
    result = "D79_POLICY_VERIFICATION_PASSED" if ok else "D79_POLICY_VERIFICATION_BLOCKED"
    gate_id = "d79-" + sha256_json(
        {
            "source": source,
            "child": child,
            "adapter": adapter,
            "contract_id": contract_id,
            "d78_decision": d78.get("decision"),
        }
    )[:16]

    report = {
        "state": "D79_POLICY_VERIFICATION_GATE",
        "result": result,
        "route": "FIELD_INTENT_POLICY_VERIFICATION_GATE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "gate_id": gate_id,
        "policy_verdict": {
            "verdict": "DRY_RUN_POLICY_APPROVED" if ok else "DRY_RUN_POLICY_REJECTED",
            "scope": "dry_run_diff_only",
            "real_route_insert_allowed": False,
            "real_apply_allowed": False,
            "ai_provider_allowed": False,
            "ai_mode_allowed_next": "PROPOSE_ONLY_AFTER_D80_BOUNDARY" if ok else "BLOCKED",
        },
        "input_reports": {
            "d78_report_path": str(root / d78_report_path),
            "d64_request_path": str(root / d64_request_path),
            "d66_review_path": str(root / d66_review_path),
        },
        "evidence": {
            "d78_ok": d78.get("ok"),
            "d78_decision": d78.get("decision"),
            "d64": d64_evidence,
            "d66": d66_evidence,
            "source_node": source,
            "child_module_path": child,
            "adapter_name": adapter,
            "contract_id": contract_id,
            "diff_sha256": pkg.get("diff_sha256") if pkg else "",
        },
        "policy_checks": {
            "d78_dry_run_only": bool(d78.get("guardrails", {}).get("dry_run_only") is True),
            "no_runtime_mutation": bool(d78.get("guardrails", {}).get("runtime_code_mutated") is False),
            "no_protected_core_mutation": bool(d78.get("guardrails", {}).get("protected_core_mutated") is False),
            "no_canonical_memory_mutation": bool(d78.get("guardrails", {}).get("canonical_memory_mutated") is False),
            "no_external_ai_call": bool(d78.get("guardrails", {}).get("external_ai_called") is False),
            "no_actual_apply": bool(d78.get("guardrails", {}).get("actual_apply_executed") is False),
            "no_route_insert": bool(d78.get("guardrails", {}).get("route_inserted") is False),
            "child_module_sandboxed": child.startswith("runtime_experimental/differentiated_modules/") if child else False,
            "diff_file_verified": bool(pkg.get("_verified_diff_text_len", 0) > 0) if pkg else False,
        },
        "guardrails": {
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "policy_gate_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "gate_id": gate_id,
            "source_node": source,
            "child_module_path": child,
            "adapter_name": adapter,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "policy_verified": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D80 can create AI Provider Boundary in PROPOSE_ONLY mode; real apply remains blocked.",
        },
    }

    write_json(root / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(verify_policy_gate(), ensure_ascii=False, indent=2))
