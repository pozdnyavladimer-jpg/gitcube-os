from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


D79_REPORT = "reports/d79_policy_verification_gate.json"
OUT = "reports/d80_ai_provider_boundary.json"
PROPOSAL_OUT = "reports/d80_ai_provider_mock_proposal.json"


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


def _validate_d79(d79: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
    if not d79:
        errors.append("D79 policy verification report missing or unreadable")
        return {}

    if d79.get("ok") is not True:
        errors.append("D79 ok flag is not true")

    if d79.get("decision") != "POLICY_VERIFIED_DRY_RUN_READY":
        errors.append(f"D79 decision is not POLICY_VERIFIED_DRY_RUN_READY: {d79.get('decision')}")

    verdict = d79.get("policy_verdict") if isinstance(d79.get("policy_verdict"), dict) else {}
    if verdict.get("verdict") != "DRY_RUN_POLICY_APPROVED":
        errors.append(f"D79 policy verdict is not DRY_RUN_POLICY_APPROVED: {verdict.get('verdict')}")
    if verdict.get("real_route_insert_allowed") is not False:
        errors.append("D79 real_route_insert_allowed is not false")
    if verdict.get("real_apply_allowed") is not False:
        errors.append("D79 real_apply_allowed is not false")
    if verdict.get("ai_provider_allowed") is not False:
        errors.append("D79 ai_provider_allowed must still be false before D80 boundary is created")

    guard = d79.get("guardrails") if isinstance(d79.get("guardrails"), dict) else {}
    for key in (
        "runtime_code_mutated",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "external_ai_called",
        "actual_apply_executed",
        "route_inserted",
    ):
        if guard.get(key) is not False:
            errors.append(f"D79 guardrail {key} is not false")
    if guard.get("policy_gate_only") is not True:
        errors.append("D79 policy_gate_only is not true")

    return verdict


def _mock_ai_proposal(
    boundary_id: str,
    source_node: str,
    child_module_path: str,
    adapter_name: str,
    d79_gate_id: str,
) -> Dict[str, Any]:
    proposal_id = "d80-proposal-" + sha256_json(
        {
            "boundary_id": boundary_id,
            "source_node": source_node,
            "child_module_path": child_module_path,
            "adapter_name": adapter_name,
            "d79_gate_id": d79_gate_id,
        }
    )[:16]

    return {
        "state": "D80_AI_PROVIDER_MOCK_PROPOSAL",
        "ok": True,
        "proposal_id": proposal_id,
        "provider": "mock_local",
        "mode": "PROPOSE_ONLY",
        "created_at": now(),
        "source": {
            "d79_gate_id": d79_gate_id,
            "source_node": source_node,
            "child_module_path": child_module_path,
            "adapter_name": adapter_name,
        },
        "proposal": {
            "type": "NEXT_MODULE_PROPOSAL",
            "recommended_next_module": "D81_AI_PROPOSAL_INTAKE",
            "action": "CREATE_JSON_INTAKE_GATE_FOR_AI_PROPOSALS",
            "reason": "D80 boundary is sealed; next step is to accept only structured proposal JSON, never raw code execution.",
            "allowed_output_contract": {
                "format": "json",
                "required_fields": [
                    "proposal_id",
                    "proposal_type",
                    "target_scope",
                    "candidate_files",
                    "guardrails",
                    "validation_plan",
                ],
                "forbidden_fields": [
                    "raw_shell_command",
                    "auto_apply",
                    "direct_core_edit",
                    "api_secret",
                ],
            },
        },
        "guardrails": {
            "external_ai_called": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "proposal_only": True,
            "mock_provider_only": True,
        },
    }


def create_ai_provider_boundary(
    root: str | Path = ".",
    d79_report_path: str = D79_REPORT,
    output_path: str = OUT,
    proposal_output_path: str = PROPOSAL_OUT,
    provider: str | None = None,
) -> Dict[str, Any]:
    root = Path(root).resolve()
    d79 = read_json(root / d79_report_path, {}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    _validate_d79(d79, errors)

    requested_provider = provider or os.environ.get("GITCUBE_AI_PROVIDER", "mock_local")
    if requested_provider != "mock_local":
        warnings.append(f"external provider '{requested_provider}' requested but blocked; D80 allows mock_local only")
        requested_provider = "mock_local"

    evidence = d79.get("evidence") if isinstance(d79.get("evidence"), dict) else {}
    summary = d79.get("summary") if isinstance(d79.get("summary"), dict) else {}

    source_node = safe_path(str(evidence.get("source_node") or summary.get("source_node") or ""))
    child_module_path = safe_path(str(evidence.get("child_module_path") or summary.get("child_module_path") or ""))
    adapter_name = str(evidence.get("adapter_name") or summary.get("adapter_name") or "")
    d79_gate_id = str(d79.get("gate_id") or summary.get("gate_id") or "")

    if not source_node:
        errors.append("D79 source_node missing")
    if not child_module_path:
        errors.append("D79 child_module_path missing")
    elif not child_module_path.startswith("runtime_experimental/differentiated_modules/"):
        errors.append(f"D79 child_module_path outside differentiated_modules: {child_module_path}")
    if child_module_path and not (root / child_module_path).exists():
        errors.append(f"child module does not exist on disk: {child_module_path}")
    if not adapter_name:
        errors.append("D79 adapter_name missing")
    if not d79_gate_id:
        errors.append("D79 gate_id missing")

    boundary_core = {
        "d79_gate_id": d79_gate_id,
        "source_node": source_node,
        "child_module_path": child_module_path,
        "adapter_name": adapter_name,
        "provider": requested_provider,
    }
    boundary_id = "d80-" + sha256_json(boundary_core)[:16]

    ok = not errors
    decision = "AI_PROVIDER_BOUNDARY_READY" if ok else "AI_PROVIDER_BOUNDARY_BLOCKED"
    result = "D80_AI_PROVIDER_BOUNDARY_CREATED" if ok else "D80_AI_PROVIDER_BOUNDARY_BLOCKED"

    proposal: Dict[str, Any] = {}
    if ok:
        proposal = _mock_ai_proposal(
            boundary_id=boundary_id,
            source_node=source_node,
            child_module_path=child_module_path,
            adapter_name=adapter_name,
            d79_gate_id=d79_gate_id,
        )
        write_json(root / proposal_output_path, proposal)

    boundary = {
        "boundary_id": boundary_id,
        "state": "D80_AI_PROVIDER_BOUNDARY",
        "enabled": ok,
        "provider": requested_provider,
        "mode": "PROPOSE_ONLY",
        "network_access_allowed": False,
        "external_ai_call_allowed": False,
        "api_keys_required": False,
        "raw_code_execution_allowed": False,
        "shell_command_generation_allowed": False,
        "direct_file_write_allowed": False,
        "git_commit_allowed": False,
        "actual_apply_allowed": False,
        "route_insert_allowed": False,
        "allowed_input_sources": [
            "reports/d79_policy_verification_gate.json",
            "reports/d78_narrow_adapter_dry_run_diff.json",
            "reports/d77_narrow_adapter_contract.json",
            "reports/d76_child_module_probe_report.json",
        ],
        "allowed_outputs": [
            "structured proposal JSON",
            "sandbox-only candidate plan",
            "validation plan",
        ],
        "forbidden_outputs": [
            "raw patch applied to protected core",
            "shell command requiring execution",
            "git commit instruction as autonomous action",
            "secret/API key request",
            "canonical memory overwrite",
        ],
        "next_required_gate": "D81_AI_PROPOSAL_INTAKE",
    }

    report = {
        "state": "D80_AI_PROVIDER_BOUNDARY",
        "result": result,
        "route": "FIELD_INTENT_AI_PROVIDER_BOUNDARY",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "boundary_id": boundary_id,
        "boundary": boundary,
        "mock_proposal_path": str(root / proposal_output_path) if ok else "",
        "input_reports": {
            "d79_report_path": str(root / d79_report_path),
        },
        "evidence": {
            "d79_ok": d79.get("ok"),
            "d79_decision": d79.get("decision"),
            "d79_gate_id": d79_gate_id,
            "source_node": source_node,
            "child_module_path": child_module_path,
            "adapter_name": adapter_name,
            "provider": requested_provider,
        },
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "provider_boundary_only": True,
            "proposal_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "boundary_id": boundary_id,
            "provider": requested_provider,
            "mode": "PROPOSE_ONLY",
            "source_node": source_node,
            "child_module_path": child_module_path,
            "adapter_name": adapter_name,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "ai_boundary_created": ok,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D81 should validate AI proposal JSON before any sandbox writer receives it.",
        },
    }

    write_json(root / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_ai_provider_boundary(), ensure_ascii=False, indent=2))
