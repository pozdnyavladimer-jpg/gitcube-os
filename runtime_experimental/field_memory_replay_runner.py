from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_REPORT_PATH = "reports/d63_field_memory_replay_report.json"


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


def _module_status(name: str, ok: bool, result: str, detail: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {"module": name, "ok": ok, "result": result, "detail": detail or {}}


def _top_moves_from_map(d67_map: Dict[str, Any]) -> List[Dict[str, Any]]:
    moves = d67_map.get("suggested_moves")
    if isinstance(moves, list):
        return [m for m in moves if isinstance(m, dict)]
    report_moves = d67_map.get("top_suggested_moves")
    if isinstance(report_moves, list):
        return [m for m in report_moves if isinstance(m, dict)]
    return []


def _derive_macro_decision(d65_report: Dict[str, Any], d67_map: Dict[str, Any], d66_report: Dict[str, Any]) -> Dict[str, Any]:
    top_moves = _top_moves_from_map(d67_map)
    apoptosis_summary = d65_report.get("summary", {}) if isinstance(d65_report, dict) else {}

    tenuki_core_moves = [
        m for m in top_moves
        if m.get("move_type") == "TENUKI" and bool(m.get("protected_core"))
    ]

    try:
        decayed_count = int(apoptosis_summary.get("decayed_count", 0))
    except Exception:
        decayed_count = 0

    d66_decision = ""
    if isinstance(d66_report, dict):
        d66_decision = str(d66_report.get("decision") or d66_report.get("result") or "")

    if tenuki_core_moves:
        return {
            "decision": "PLAN_ISOLATED_BYPASS",
            "reason": "D67 found protected stressed core; use TENUKI instead of direct expansion",
            "priority": "critical",
            "requires": [
                "D66 reviewer approval",
                "local tests",
                "regression evidence",
                "no direct protected-core mutation",
            ],
            "targets": [m.get("target") for m in tenuki_core_moves],
        }

    if decayed_count > 0:
        return {
            "decision": "REVIEW_APOPTOSIS_DECAY_CANDIDATE",
            "reason": "D65 produced decayed bias candidates that need guard review before canonical apply",
            "priority": "high",
            "requires": ["D66 memory guard review", "backup of canonical memory", "explicit apply step"],
            "targets": ["memory/field_intent_priority_bias_decayed.json"],
        }

    if "FORBIDDEN_CORE_MUTATION" in d66_decision:
        return {
            "decision": "HOLD_CORE_LOCK",
            "reason": "D66 recently rejected direct protected-core mutation",
            "priority": "high",
            "requires": ["sandbox proposal", "two eyes", "no core edit without regression"],
            "targets": [],
        }

    return {
        "decision": "HOLD_AND_MONITOR",
        "reason": "no immediate bypass or decay action required",
        "priority": "normal",
        "requires": ["continue replay", "watch recurrence"],
        "targets": [],
    }


def run_field_memory_replay(root: str | Path = ".", output_path: str = DEFAULT_REPORT_PATH) -> Dict[str, Any]:
    root_path = Path(root).resolve()

    memory_path = root_path / "memory/field_intent_memory.jsonl"
    bias_path = root_path / "memory/field_intent_priority_bias.json"
    decayed_bias_path = root_path / "memory/field_intent_priority_bias_decayed.json"
    d65_report_path = root_path / "reports/d65_apoptosis_decay_report.json"
    d66_report_path = root_path / "reports/d66_core_guard_reviewer_report.json"
    d67_map_path = root_path / "reports/d67_topological_memory_map.json"
    d67_report_path = root_path / "reports/d67_topological_memory_map_report.json"
    core_policy_path = root_path / "runtime_experimental/core_guard_policy.json"

    modules: List[Dict[str, Any]] = []
    errors: List[str] = []
    warnings: List[str] = []

    d65_report: Dict[str, Any] = {}
    d67_map: Dict[str, Any] = {}
    d66_report: Dict[str, Any] = _read_json(d66_report_path, default={}) or {}

    try:
        from runtime_experimental.memory_apoptosis import run_memory_apoptosis
        d65_report = run_memory_apoptosis(
            bias_path=str(bias_path),
            memory_path=str(memory_path),
            output_path=str(decayed_bias_path),
            report_path=str(d65_report_path),
        )
        modules.append(_module_status("D65_MEMORY_APOPTOSIS", bool(d65_report.get("ok")), str(d65_report.get("result")), {"summary": d65_report.get("summary", {})}))
    except Exception as exc:
        warnings.append(f"D65 skipped or failed: {exc}")
        d65_report = _read_json(d65_report_path, default={}) or {}
        modules.append(_module_status("D65_MEMORY_APOPTOSIS", False, "SKIPPED_OR_FAILED", {"error": str(exc)}))

    try:
        from runtime_experimental.topological_memory_map import build_topological_memory_map
        d67_map = build_topological_memory_map(
            root=root_path,
            policy_path=str(core_policy_path),
            memory_path=str(memory_path),
            bias_path=str(bias_path),
            map_path=str(d67_map_path),
            report_path=str(d67_report_path),
        )
        modules.append(_module_status("D67_TOPOLOGICAL_MEMORY_MAP", bool(d67_map.get("ok")), str(d67_map.get("result")), {"summary": d67_map.get("summary", {})}))
    except Exception as exc:
        warnings.append(f"D67 skipped or failed: {exc}")
        d67_map = _read_json(d67_map_path, default={}) or _read_json(d67_report_path, default={}) or {}
        modules.append(_module_status("D67_TOPOLOGICAL_MEMORY_MAP", False, "SKIPPED_OR_FAILED", {"error": str(exc)}))

    if d66_report:
        modules.append(_module_status("D66_CORE_GUARD_REVIEWER", True, str(d66_report.get("result") or d66_report.get("decision") or "REPORT_READ"), {"decision": d66_report.get("decision"), "ok": d66_report.get("ok")}))
    else:
        warnings.append("D66 reviewer report not found")
        modules.append(_module_status("D66_CORE_GUARD_REVIEWER", False, "REPORT_MISSING"))

    macro_decision = _derive_macro_decision(d65_report, d67_map, d66_report)

    report = {
        "state": "D63_FIELD_MEMORY_REPLAY_RUNNER",
        "result": "FIELD_MEMORY_REPLAY_COMPLETED",
        "route": "FIELD_INTENT_FIELD_MEMORY_REPLAY",
        "ok": len(errors) == 0,
        "created_at": _now(),
        "root": str(root_path),
        "output_path": str(output_path),
        "modules": modules,
        "macro_decision": macro_decision,
        "summary": {
            "modules_seen": len(modules),
            "warnings_count": len(warnings),
            "errors_count": len(errors),
            "decision": macro_decision.get("decision"),
            "priority": macro_decision.get("priority"),
            "targets_count": len(macro_decision.get("targets", []) or []),
        },
        "input_reports": {
            "d65_report_path": str(d65_report_path),
            "d66_report_path": str(d66_report_path),
            "d67_map_path": str(d67_map_path),
            "d67_report_path": str(d67_report_path),
        },
        "validation": {"ok": len(errors) == 0, "errors": errors, "warnings": warnings},
        "success_condition": {
            "replay_completed": True,
            "canonical_memory_mutated": False,
            "core_code_mutated": False,
            "next_step": "D64 can consume this replay report plus D66/D67 evidence to propose a guarded safe mutation.",
        },
    }

    _write_json(root_path / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(run_field_memory_replay(), ensure_ascii=False, indent=2))
