from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_D64_REQUEST = "reports/d64_safe_mutation_gate_request.json"
DEFAULT_D70_REVIEW = "reports/d70_sandbox_bundle_review.json"
DEFAULT_D69_BUNDLE = "reports/d69_sandbox_patch_bundle.json"
DEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"
DEFAULT_OUTPUT = "reports/d71_route_dry_run_simulation.json"

ALLOWED_SANDBOX_PREFIXES = ("runtime_experimental/ai_bypass_proposals/",)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_relative_path(path_value: str) -> str:
    raw = str(path_value or "").strip().replace("\\", "/").lstrip("/")
    parts: List[str] = []
    for part in raw.split("/"):
        if not part or part == "." or part == "..":
            continue
        parts.append(part)
    return "/".join(parts)


def _is_allowed_sandbox_file(path_value: str) -> bool:
    rel = _safe_relative_path(path_value)
    return rel.endswith(".py") and any(rel.startswith(prefix) for prefix in ALLOWED_SANDBOX_PREFIXES)


def _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:
    for key in ("protected_files", "immutable_core", "core_files"):
        value = policy.get(key)
        if isinstance(value, list):
            return [str(v) for v in value]
    return []


def _hash_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _route_name_for_candidate(candidate: str) -> str:
    return "DRY_RUN_" + Path(candidate).stem.upper()


def _extract_targets_from_d64(d64: Dict[str, Any]) -> List[str]:
    evidence = d64.get("evidence") if isinstance(d64.get("evidence"), dict) else {}
    macro = evidence.get("macro_decision") if isinstance(evidence.get("macro_decision"), dict) else {}
    targets = macro.get("targets")
    if isinstance(targets, list):
        return [str(x) for x in targets if x]

    request = d64.get("guarded_apply_request") if isinstance(d64.get("guarded_apply_request"), dict) else {}
    candidates = request.get("sandbox_candidates")
    if isinstance(candidates, list):
        return [str(x) for x in candidates if x]
    return []


def simulate_route_dry_run(
    root: str | Path = ".",
    d64_request_path: str = DEFAULT_D64_REQUEST,
    d70_review_path: str = DEFAULT_D70_REVIEW,
    d69_bundle_path: str = DEFAULT_D69_BUNDLE,
    core_policy_path: str = DEFAULT_CORE_POLICY,
    output_path: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()

    d64 = _read_json(root_path / d64_request_path, default={}) or {}
    d70 = _read_json(root_path / d70_review_path, default={}) or {}
    d69 = _read_json(root_path / d69_bundle_path, default={}) or {}
    policy = _read_json(root_path / core_policy_path, default={}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    if not d64:
        errors.append("D64 safe mutation gate request missing or unreadable")
    if not d70:
        warnings.append("D70 review missing or unreadable")
    if not d69:
        warnings.append("D69 sandbox bundle missing or unreadable")
    if not policy:
        warnings.append("core guard policy missing or unreadable")

    if d64:
        if d64.get("ok") is not True:
            errors.append("D64 request ok flag is not true")
        if d64.get("decision") != "CREATE_GUARDED_APPLY_REQUEST":
            errors.append(f"D64 decision is not CREATE_GUARDED_APPLY_REQUEST: {d64.get('decision')}")
        guardrails = d64.get("guardrails") if isinstance(d64.get("guardrails"), dict) else {}
        if guardrails.get("actual_apply_executed") is not False:
            errors.append("D64 actual_apply_executed is not false")
        if guardrails.get("gate_only") is not True:
            errors.append("D64 gate_only is not true")

    guarded_request = d64.get("guarded_apply_request") if isinstance(d64.get("guarded_apply_request"), dict) else {}
    if guarded_request and guarded_request.get("enabled") is not True:
        errors.append("D64 guarded apply request is not enabled")

    sandbox_candidates_raw = guarded_request.get("sandbox_candidates", [])
    sandbox_candidates = [_safe_relative_path(str(x)) for x in sandbox_candidates_raw if x] if isinstance(sandbox_candidates_raw, list) else []

    if not sandbox_candidates:
        errors.append("No sandbox candidates available for dry-run")

    protected_files = _protected_files_from_policy(policy)
    targets = _extract_targets_from_d64(d64)

    simulated_route_diff: List[Dict[str, Any]] = []
    candidate_hashes: Dict[str, str] = {}

    for candidate in sandbox_candidates:
        candidate_path = root_path / candidate

        if not _is_allowed_sandbox_file(candidate):
            errors.append(f"D71 rejected non-sandbox candidate: {candidate}")
            continue
        if candidate in protected_files:
            errors.append(f"D71 rejected protected candidate: {candidate}")
            continue
        if not candidate_path.exists():
            errors.append(f"D71 candidate missing on disk: {candidate}")
            continue

        digest = _hash_file(candidate_path)
        candidate_hashes[candidate] = digest

        simulated_route_diff.append(
            {
                "operation": "SIMULATE_ROUTE_INSERT",
                "route_name": _route_name_for_candidate(candidate),
                "sandbox_handler": candidate,
                "handler_sha256": digest,
                "target_scope": targets,
                "would_touch_files": [],
                "would_touch_protected_core": False,
                "would_touch_canonical_memory": False,
                "would_execute_runtime_mutation": False,
                "dry_run_only": True,
            }
        )

    if not simulated_route_diff:
        errors.append("No valid simulated route diff created")

    if d70 and d70.get("decision") != "APPROVE_SANDBOX_BUNDLE":
        errors.append(f"D70 decision is not APPROVE_SANDBOX_BUNDLE: {d70.get('decision')}")

    gate_passed = len(errors) == 0
    decision = "ROUTE_DRY_RUN_APPROVED" if gate_passed else "ROUTE_DRY_RUN_BLOCKED"
    result = "D71_ROUTE_DRY_RUN_COMPLETED" if gate_passed else "D71_ROUTE_DRY_RUN_BLOCKED"

    report = {
        "state": "D71_ROUTE_DRY_RUN_SIMULATION",
        "result": result,
        "route": "FIELD_INTENT_ROUTE_DRY_RUN_SIMULATION",
        "ok": gate_passed,
        "decision": decision,
        "created_at": _now(),
        "source_d64_request": str(root_path / d64_request_path),
        "source_d70_review": str(root_path / d70_review_path),
        "source_d69_bundle": str(root_path / d69_bundle_path),
        "sandbox_candidates": sandbox_candidates,
        "candidate_hashes": candidate_hashes,
        "protected_files": protected_files,
        "target_scope": targets,
        "simulated_route_diff": simulated_route_diff,
        "guardrails": {
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "dry_run_only": True,
        },
        "validation": {"ok": gate_passed, "errors": errors, "warnings": warnings},
        "summary": {
            "decision": decision,
            "sandbox_candidates_count": len(sandbox_candidates),
            "simulated_route_diff_count": len(simulated_route_diff),
            "protected_files_count": len(protected_files),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "dry_run_completed": gate_passed,
            "actual_apply_executed": False,
            "protected_core_untouched": True,
            "canonical_memory_untouched": True,
            "next_step": "D72 can package this dry-run as a reviewed apply plan; D64/D66 must still approve before any real mutation.",
        },
    }

    _write_json(root_path / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(simulate_route_dry_run(), ensure_ascii=False, indent=2))
