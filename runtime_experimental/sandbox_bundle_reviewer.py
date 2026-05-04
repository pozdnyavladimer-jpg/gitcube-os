from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_D69_BUNDLE = "reports/d69_sandbox_patch_bundle.json"
DEFAULT_D69_REPORT = "reports/d69_sandbox_patch_write_report.json"
DEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"
DEFAULT_OUTPUT = "reports/d70_sandbox_bundle_review.json"

ALLOWED_SANDBOX_PREFIXES = (
    "runtime_experimental/ai_bypass_proposals/",
    "reports/",
    "tests/",
)


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
    raw = str(path_value or "").strip().replace("\\", "/")
    raw = raw.lstrip("/")
    parts: List[str] = []
    for part in raw.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            continue
        parts.append(part)
    return "/".join(parts)


def _is_allowed_sandbox_path(path_value: str) -> bool:
    rel = _safe_relative_path(path_value)
    return any(rel.startswith(prefix) for prefix in ALLOWED_SANDBOX_PREFIXES)


def _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:
    for key in ("protected_files", "immutable_core", "core_files"):
        value = policy.get(key)
        if isinstance(value, list):
            return [str(v) for v in value]
    return []


def _module_name_from_path(path_value: str) -> str:
    stem = Path(path_value).stem
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in stem)
    return cleaned or "sandbox_module"


def _probe_sandbox_file(root: Path, rel_path: str) -> Tuple[bool, str, Dict[str, Any]]:
    rel = _safe_relative_path(rel_path)
    path = root / rel
    if not path.exists():
        return False, "sandbox_file_missing", {}
    if not rel.endswith(".py"):
        return False, "sandbox_file_not_python", {}
    try:
        spec = importlib.util.spec_from_file_location(_module_name_from_path(rel), str(path))
        if spec is None or spec.loader is None:
            return False, "spec_loader_missing", {}
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, "run_sandbox_probe"):
            return False, "run_sandbox_probe_missing", {}
        result = module.run_sandbox_probe({"source": "D70_REVIEW"})
        if not isinstance(result, dict):
            return False, "probe_result_not_dict", {}
        if result.get("ok") is not True:
            return False, "probe_not_ok", result
        if result.get("proposal_only") is not True:
            return False, "proposal_only_flag_missing", result
        if result.get("protected_core_mutated") is not False:
            return False, "protected_core_mutation_flag_not_false", result
        if result.get("canonical_memory_mutated") is not False:
            return False, "canonical_memory_mutation_flag_not_false", result
        return True, "probe_ok", result
    except Exception as exc:
        return False, f"probe_exception:{exc}", {}


def review_sandbox_bundle(
    root: str | Path = ".",
    d69_bundle_path: str = DEFAULT_D69_BUNDLE,
    d69_report_path: str = DEFAULT_D69_REPORT,
    core_policy_path: str = DEFAULT_CORE_POLICY,
    output_path: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()
    bundle = _read_json(root_path / d69_bundle_path, default={}) or {}
    d69_report = _read_json(root_path / d69_report_path, default={}) or {}
    policy = _read_json(root_path / core_policy_path, default={}) or {}

    errors: List[str] = []
    warnings: List[str] = []
    review_items: List[Dict[str, Any]] = []

    if not bundle:
        errors.append("D69 sandbox bundle missing or unreadable")
    if not d69_report:
        warnings.append("D69 write report missing or unreadable")
    if not policy:
        warnings.append("core guard policy missing or unreadable")

    protected_files = _protected_files_from_policy(policy)
    written_files_raw = bundle.get("written_files", [])
    written_files = [str(x) for x in written_files_raw] if isinstance(written_files_raw, list) else []
    if not written_files:
        errors.append("D69 bundle has no written_files")

    guardrails = bundle.get("guardrails", {}) if isinstance(bundle.get("guardrails"), dict) else {}
    for key in ("runtime_code_mutated", "protected_core_mutated", "canonical_memory_mutated", "external_ai_called"):
        if guardrails.get(key) is not False:
            errors.append(f"guardrail_not_false:{key}")
    if guardrails.get("sandbox_only") is not True:
        errors.append("guardrail_sandbox_only_not_true")

    d69_validation = d69_report.get("validation", {}) if isinstance(d69_report.get("validation"), dict) else {}
    if d69_report and d69_validation.get("ok") is not True:
        errors.append("D69 write report validation is not ok")
    if bundle.get("ok") is not True:
        errors.append("D69 bundle ok flag is not true")

    bundle_probe_results = bundle.get("probe_results", [])
    if isinstance(bundle_probe_results, list):
        for item in bundle_probe_results:
            if isinstance(item, dict) and item.get("ok") is not True:
                errors.append(f"D69 probe failed for {item.get('path')}: {item.get('reason')}")
    else:
        errors.append("D69 bundle probe_results missing or invalid")

    for rel_raw in written_files:
        rel = _safe_relative_path(rel_raw)
        item: Dict[str, Any] = {"path": rel, "checks": {}}
        allowed = _is_allowed_sandbox_path(rel)
        item["checks"]["allowed_sandbox_path"] = allowed
        if not allowed:
            errors.append(f"written file outside allowed sandbox prefixes: {rel}")
        protected = rel in protected_files
        item["checks"]["not_protected_file"] = not protected
        if protected:
            errors.append(f"written file is protected core: {rel}")
        exists = (root_path / rel).exists()
        item["checks"]["exists"] = exists
        if not exists:
            errors.append(f"written file missing on disk: {rel}")
        if exists and rel.endswith(".py"):
            probe_ok, probe_reason, probe_payload = _probe_sandbox_file(root_path, rel)
            item["checks"]["probe_ok"] = probe_ok
            item["checks"]["probe_reason"] = probe_reason
            item["probe_payload"] = probe_payload
            if not probe_ok:
                errors.append(f"D70 probe failed for {rel}: {probe_reason}")
        review_items.append(item)

    approved = len(errors) == 0
    decision = "APPROVE_SANDBOX_BUNDLE" if approved else "REJECT_SANDBOX_BUNDLE"
    result = "D70_REVIEW_APPROVED" if approved else "D70_REVIEW_REJECTED"
    report = {
        "state": "D70_SANDBOX_BUNDLE_REVIEWER",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_BUNDLE_REVIEW",
        "ok": approved,
        "decision": decision,
        "created_at": _now(),
        "source_bundle": str(root_path / d69_bundle_path),
        "source_report": str(root_path / d69_report_path),
        "core_policy": str(root_path / core_policy_path),
        "written_files": written_files,
        "protected_files": protected_files,
        "review_items": review_items,
        "guardrails": {
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "sandbox_only": True,
            "external_ai_called": False,
            "d64_apply_allowed": approved,
        },
        "validation": {"ok": approved, "errors": errors, "warnings": warnings},
        "summary": {
            "written_files_count": len(written_files),
            "review_items_count": len(review_items),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
            "decision": decision,
        },
        "success_condition": {
            "sandbox_bundle_reviewed": True,
            "approved": approved,
            "d64_may_consume_if_approved": approved,
            "next_step": "D64 Safe Mutation Gate may consume this review only if decision is APPROVE_SANDBOX_BUNDLE.",
        },
    }
    _write_json(root_path / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(review_sandbox_bundle(), ensure_ascii=False, indent=2))
