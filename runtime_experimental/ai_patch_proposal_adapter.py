from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_D63_REPORT = "reports/d63_field_memory_replay_report.json"
DEFAULT_D67_MAP = "reports/d67_topological_memory_map.json"
DEFAULT_D67_REPORT = "reports/d67_topological_memory_map_report.json"
DEFAULT_D66_REVIEWER_REPORT = "reports/d66_core_guard_reviewer_report.json"
DEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"
DEFAULT_OUTPUT = "reports/d68_ai_patch_proposal.json"


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


def _slug(value: str) -> str:
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9_./-]+", "_", value)
    value = value.replace("/", "_").replace(".", "_")
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "proposal"


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:
    for key in ("protected_files", "immutable_core", "core_files"):
        value = policy.get(key)
        if isinstance(value, list):
            return [str(v) for v in value]
    return []


def _extract_d67_moves(d67_map: Dict[str, Any], d67_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    for source in (d67_map, d67_report):
        if isinstance(source.get("suggested_moves"), list):
            return [m for m in source["suggested_moves"] if isinstance(m, dict)]
        if isinstance(source.get("top_suggested_moves"), list):
            return [m for m in source["top_suggested_moves"] if isinstance(m, dict)]
    return []


def _extract_hot_targets(d63_report: Dict[str, Any], d67_moves: List[Dict[str, Any]]) -> List[str]:
    macro = d63_report.get("macro_decision") if isinstance(d63_report, dict) else {}
    targets: List[str] = []
    if isinstance(macro, dict):
        for t in _as_list(macro.get("targets")):
            if t:
                targets.append(str(t))
    for move in d67_moves:
        target = move.get("target")
        if target:
            targets.append(str(target))
    out: List[str] = []
    seen = set()
    for item in targets:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _candidate_module_for_target(target: str) -> str:
    slug = _slug(target)
    if "task_dispatcher" in slug:
        return "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"
    if "v_kernel_daemon" in slug:
        return "runtime_experimental/ai_bypass_proposals/daemon_bypass_proposal.py"
    if "phase_resync" in slug:
        return "runtime_experimental/ai_bypass_proposals/phase_resync_bypass_proposal.py"
    return f"runtime_experimental/ai_bypass_proposals/{slug}_bypass_proposal.py"


def _proposal_prompt(macro_decision: Dict[str, Any], hot_targets: List[str], protected_files: List[str], candidate_files: List[str]) -> str:
    return (
        "You are an AI patch proposal agent for GitCube OS. "
        "Create a patch proposal only. Do not mutate code. "
        "Follow D66 core guard rules. Protected core must not be edited directly. "
        "Use TENUKI: create an isolated bypass module and tests. "
        "Return JSON only with target_files, created_files, test_plan, rollback_plan, and validation_gates. "
        f"Macro decision: {macro_decision}. "
        f"Hot targets: {hot_targets}. "
        f"Protected files: {protected_files}. "
        f"Allowed candidate files: {candidate_files}."
    )


def build_ai_patch_proposal(
    root: str | Path = ".",
    d63_report_path: str = DEFAULT_D63_REPORT,
    d67_map_path: str = DEFAULT_D67_MAP,
    d67_report_path: str = DEFAULT_D67_REPORT,
    d66_reviewer_report_path: str = DEFAULT_D66_REVIEWER_REPORT,
    core_policy_path: str = DEFAULT_CORE_POLICY,
    output_path: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()
    d63 = _read_json(root_path / d63_report_path, default={}) or {}
    d67_map = _read_json(root_path / d67_map_path, default={}) or {}
    d67_report = _read_json(root_path / d67_report_path, default={}) or {}
    d66_report = _read_json(root_path / d66_reviewer_report_path, default={}) or {}
    core_policy = _read_json(root_path / core_policy_path, default={}) or {}

    warnings: List[str] = []
    errors: List[str] = []
    if not d63:
        warnings.append("D63 replay report missing or unreadable")
    if not d67_map and not d67_report:
        warnings.append("D67 topology map/report missing or unreadable")
    if not d66_report:
        warnings.append("D66 reviewer report missing or unreadable")
    if not core_policy:
        warnings.append("core guard policy missing or unreadable")

    macro_decision = d63.get("macro_decision") if isinstance(d63.get("macro_decision"), dict) else {}
    decision = str(macro_decision.get("decision") or "HOLD_AND_MONITOR")
    priority = str(macro_decision.get("priority") or "normal")
    d67_moves = _extract_d67_moves(d67_map, d67_report)
    hot_targets = _extract_hot_targets(d63, d67_moves)
    protected_files = _protected_files_from_policy(core_policy)

    if not hot_targets:
        hot_targets = ["runtime_experimental/unknown_hotspot.py"]
        warnings.append("no hot targets found; using placeholder proposal target")

    candidate_files = list(dict.fromkeys(_candidate_module_for_target(t) for t in hot_targets))

    forbidden_actions = [
        "direct_core_edit",
        "overwrite_canonical_memory",
        "write_to_protected_file",
        "auto_commit_without_review",
        "execute_generated_patch_without_tests",
    ]
    validation_gates = [
        "D66_CORE_GUARD_REVIEW_REQUIRED",
        "UNIT_TESTS_REQUIRED",
        "REGRESSION_TESTS_REQUIRED",
        "NO_PROTECTED_CORE_MUTATION",
        "NO_CANONICAL_MEMORY_OVERWRITE",
        "ROLLBACK_PLAN_REQUIRED",
    ]

    if decision == "PLAN_ISOLATED_BYPASS":
        proposal_mode = "AI_PROPOSAL_ONLY_ISOLATED_BYPASS"
        proposed_action = "CREATE_ISOLATED_BYPASS_MODULE"
        rationale = "D63/D67 recommend TENUKI around stressed protected core."
    elif decision == "HOLD_CORE_LOCK":
        proposal_mode = "AI_PROPOSAL_ONLY_CORE_LOCK"
        proposed_action = "DESIGN_SANDBOX_ONLY_PROPOSAL"
        rationale = "D66 indicates core mutation risk; hold protected core lock."
    elif decision == "REVIEW_APOPTOSIS_DECAY_CANDIDATE":
        proposal_mode = "AI_PROPOSAL_ONLY_MEMORY_DECAY_REVIEW"
        proposed_action = "REVIEW_DECAYED_MEMORY_CANDIDATE"
        rationale = "D65 produced memory decay candidate requiring guard review."
    else:
        proposal_mode = "AI_PROPOSAL_ONLY_MONITOR"
        proposed_action = "NO_CODE_CHANGE_MONITOR"
        rationale = "No safe mutation action required."

    proposal = {
        "state": "D68_AI_PATCH_PROPOSAL",
        "result": "AI_PATCH_PROPOSAL_CONTRACT_CREATED",
        "route": "FIELD_INTENT_AI_PATCH_PROPOSAL_ADAPTER",
        "ok": len(errors) == 0,
        "created_at": _now(),
        "proposal_mode": proposal_mode,
        "proposed_action": proposed_action,
        "priority": priority,
        "decision_source": decision,
        "rationale": rationale,
        "hot_targets": hot_targets,
        "protected_files": protected_files,
        "candidate_created_files": candidate_files,
        "forbidden_actions": forbidden_actions,
        "validation_gates": validation_gates,
        "llm_ready_payload": {
            "system_contract": "Proposal only. Return JSON. Do not write files. Do not mutate protected core. Do not overwrite canonical memory.",
            "prompt": _proposal_prompt(macro_decision, hot_targets, protected_files, candidate_files),
            "expected_json_schema": {
                "proposal_name": "string",
                "intent": "string",
                "target_files": ["string"],
                "created_files": ["string"],
                "protected_files_not_touched": True,
                "test_plan": ["string"],
                "rollback_plan": ["string"],
                "validation_gates": ["string"],
                "risk_level": "low|medium|high|critical",
            },
        },
        "guardrails": {
            "runtime_code_mutated": False,
            "canonical_memory_mutated": False,
            "protected_core_mutated": False,
            "external_ai_called": False,
            "proposal_only": True,
        },
        "input_reports": {
            "d63_report_path": str(root_path / d63_report_path),
            "d67_map_path": str(root_path / d67_map_path),
            "d67_report_path": str(root_path / d67_report_path),
            "d66_reviewer_report_path": str(root_path / d66_reviewer_report_path),
            "core_policy_path": str(root_path / core_policy_path),
        },
        "summary": {
            "decision": decision,
            "priority": priority,
            "hot_targets_count": len(hot_targets),
            "candidate_files_count": len(candidate_files),
            "validation_gates_count": len(validation_gates),
            "warnings_count": len(warnings),
            "errors_count": len(errors),
        },
        "validation": {"ok": len(errors) == 0, "errors": errors, "warnings": warnings},
        "success_condition": {
            "proposal_contract_created": True,
            "ai_can_read_this_report": True,
            "ai_cannot_mutate_code_from_this_step": True,
            "next_step": "D69 may consume this contract and write sandbox-only files after D66-compatible checks.",
        },
    }
    _write_json(root_path / output_path, proposal)
    return proposal


if __name__ == "__main__":
    print(json.dumps(build_ai_patch_proposal(), ensure_ascii=False, indent=2))
