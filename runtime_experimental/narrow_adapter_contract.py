from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_D76_REPORT = "reports/d76_child_module_probe_report.json"
DEFAULT_D75_REPORT = "reports/d75_differentiation_scaffold_package.json"
DEFAULT_D74_PLAN = "reports/d74_differentiation_plan.json"
DEFAULT_OUTPUT = "reports/d77_narrow_adapter_contract.json"


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


def _safe_symbol(value: str) -> str:
    raw = _safe_relative_path(value).replace("/", "_").replace(".", "_").replace("-", "_")
    out = "".join(ch.lower() if ch.isalnum() or ch == "_" else "_" for ch in raw)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_") or "adapter"


def _sha256_json(data: Dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_d76(d76: Dict[str, Any], errors: List[str]) -> None:
    if not d76:
        errors.append("D76 child module probe report missing or unreadable")
        return

    if d76.get("ok") is not True:
        errors.append("D76 ok flag is not true")

    if d76.get("decision") != "CHILD_MODULE_PROBE_PASSED":
        errors.append(f"D76 decision is not CHILD_MODULE_PROBE_PASSED: {d76.get('decision')}")

    guardrails = d76.get("guardrails") if isinstance(d76.get("guardrails"), dict) else {}
    if guardrails.get("actual_apply_executed") is not False:
        errors.append("D76 actual_apply_executed is not false")
    if guardrails.get("probe_only") is not True:
        errors.append("D76 probe_only is not true")


def _validate_route_contract(contract: Dict[str, Any], errors: List[str]) -> None:
    if not isinstance(contract, dict) or not contract:
        errors.append("D76 route contract missing or unreadable")
        return

    if contract.get("ok") is not True:
        errors.append("D76 route contract ok flag is not true")

    if contract.get("allowed_mode") != "SANDBOX_PROBE_ONLY":
        errors.append(f"D76 route contract allowed_mode is not SANDBOX_PROBE_ONLY: {contract.get('allowed_mode')}")

    forbidden = contract.get("forbidden_actions")
    if not isinstance(forbidden, list):
        errors.append("D76 route contract forbidden_actions is not a list")
    else:
        for action in ("direct_core_edit", "overwrite_canonical_memory", "auto_apply_runtime_mutation"):
            if action not in forbidden:
                errors.append(f"D76 route contract missing forbidden action: {action}")

    required = contract.get("required_before_integration")
    if not isinstance(required, list):
        errors.append("D76 route contract required_before_integration is not a list")
    else:
        for gate in ("D66_RECHECK", "UNIT_TESTS", "REGRESSION_TESTS", "ROLLBACK_MANIFEST"):
            if gate not in required:
                errors.append(f"D76 route contract missing required gate: {gate}")


def build_narrow_adapter_contract(
    root: str | Path = ".",
    d76_report_path: str = DEFAULT_D76_REPORT,
    d75_report_path: str = DEFAULT_D75_REPORT,
    d74_plan_path: str = DEFAULT_D74_PLAN,
    output_path: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()

    d76 = _read_json(root_path / d76_report_path, default={}) or {}
    d75 = _read_json(root_path / d75_report_path, default={}) or {}
    d74 = _read_json(root_path / d74_plan_path, default={}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    _validate_d76(d76, errors)

    if not d75:
        warnings.append("D75 scaffold report missing or unreadable; using D76 probe target only")
    if not d74:
        warnings.append("D74 differentiation plan missing or unreadable; source intent may be incomplete")

    probe_target = d76.get("probe_target") if isinstance(d76.get("probe_target"), dict) else {}
    module_description = d76.get("module_description") if isinstance(d76.get("module_description"), dict) else {}
    route_contract = d76.get("route_contract") if isinstance(d76.get("route_contract"), dict) else {}

    _validate_route_contract(route_contract, errors)

    child_module_path = _safe_relative_path(
        str(probe_target.get("child_module_path") or route_contract.get("child_module_path") or "")
    )
    if not child_module_path:
        errors.append("child module path missing")
    elif not child_module_path.startswith("runtime_experimental/differentiated_modules/"):
        errors.append(f"child module path outside differentiated_modules: {child_module_path}")

    source_node = str(
        route_contract.get("source_node")
        or module_description.get("source_node")
        or d76.get("summary", {}).get("source_node", "")
        or "UNKNOWN_SOURCE_NODE"
    )

    handler_role = str(
        route_contract.get("handler_role")
        or module_description.get("gradient_role")
        or "specialized_child"
    )

    source_slug = _safe_symbol(source_node)
    role_slug = _safe_symbol(handler_role)
    adapter_name = f"D77_NARROW_ADAPTER_{source_slug}_{role_slug}".upper()
    contract_id = "d77-" + _sha256_json(
        {
            "source_node": source_node,
            "child_module_path": child_module_path,
            "handler_role": handler_role,
        }
    )[:16]

    ok = len(errors) == 0
    decision = "NARROW_ADAPTER_CONTRACT_READY" if ok else "NARROW_ADAPTER_CONTRACT_BLOCKED"
    result = "D77_NARROW_ADAPTER_CONTRACT_CREATED" if ok else "D77_NARROW_ADAPTER_CONTRACT_BLOCKED"

    narrow_adapter_contract = {
        "contract_id": contract_id,
        "contract_state": "D77_NARROW_ADAPTER_CONTRACT",
        "enabled": ok,
        "mode": "CONTRACT_ONLY_NO_ROUTE_INSERT",
        "adapter_name": adapter_name,
        "source_node": source_node,
        "child_module_path": child_module_path,
        "handler_role": handler_role,
        "boundary": {
            "input": "event: dict[str, Any]",
            "output": "sandbox probe result with payload preservation and guardrails",
            "adapter_width": "narrow",
            "allowed_call": "child_module.run_sandbox_probe(event)",
            "forbidden_call": "direct protected-core mutation",
        },
        "route_policy": {
            "integration_status": "NOT_INTEGRATED",
            "route_insert_allowed_now": False,
            "contract_only": True,
            "allowed_next_step": "generate adapter dry-run diff only",
        },
        "required_before_integration": [
            "D66_RECHECK",
            "D73_PACKAGE_READY",
            "D76_CHILD_PROBE_PASSED",
            "UNIT_TESTS",
            "REGRESSION_TESTS",
            "ROLLBACK_MANIFEST",
            "HUMAN_OR_HIGHER_POLICY_APPROVAL",
        ],
        "forbidden_actions": [
            "direct_core_edit",
            "protected_core_mutation",
            "overwrite_canonical_memory",
            "external_ai_call",
            "auto_apply_runtime_mutation",
            "route_insert_without_D66_recheck",
            "route_insert_without_rollback_manifest",
        ],
    }

    report = {
        "state": "D77_NARROW_ADAPTER_CONTRACT",
        "result": result,
        "route": "FIELD_INTENT_NARROW_ADAPTER_CONTRACT",
        "ok": ok,
        "decision": decision,
        "created_at": _now(),
        "contract_id": contract_id,
        "narrow_adapter_contract": narrow_adapter_contract,
        "input_reports": {
            "d76_report_path": str(root_path / d76_report_path),
            "d75_report_path": str(root_path / d75_report_path),
            "d74_plan_path": str(root_path / d74_plan_path),
        },
        "evidence": {
            "d76_decision": d76.get("decision"),
            "d76_ok": d76.get("ok"),
            "d75_decision": d75.get("decision"),
            "d74_decision": d74.get("decision"),
            "child_module_path": child_module_path,
            "handler_role": handler_role,
            "source_node": source_node,
        },
        "guardrails": {
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "contract_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "contract_id": contract_id,
            "adapter_name": adapter_name,
            "source_node": source_node,
            "child_module_path": child_module_path,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "narrow_adapter_contract_created": ok,
            "actual_apply_executed": False,
            "protected_core_untouched": True,
            "next_step": "D78 can generate a narrow adapter dry-run diff package, still without route insertion.",
        },
    }

    _write_json(root_path / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(build_narrow_adapter_contract(), ensure_ascii=False, indent=2))
