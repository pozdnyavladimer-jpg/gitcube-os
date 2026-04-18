from __future__ import annotations

from typing import Dict, Any, List, Optional
import json
from pathlib import Path


STATE_FILE = Path("objects.json")


def _load_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: Dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _normalize(value: str) -> str:
    return str(value or "").strip()


def record_import_fix(
    problem_type: str,
    source_module: str,
    resolved_module: str,
    file_path: str = "",
    symbol: str = "",
    kind: str = "unknown",
    success: bool = True,
) -> Dict[str, Any]:
    state = _load_state()
    rules: List[Dict[str, Any]] = state.setdefault("rules", [])

    problem_type = _normalize(problem_type)
    source_module = _normalize(source_module)
    resolved_module = _normalize(resolved_module)
    file_path = _normalize(file_path)

    if not problem_type or not source_module or not resolved_module:
        return {"ok": False, "reason": "missing_required_fields"}

    for rule in rules:
        if (
            rule.get("problem_type") == problem_type
            and rule.get("source_module") == source_module
            and rule.get("resolved_module") == resolved_module
            and rule.get("file_path", "") == file_path
        ):
            if success:
                rule["success_count"] = int(rule.get("success_count", 0)) + 1
            else:
                rule["fail_count"] = int(rule.get("fail_count", 0)) + 1

            if symbol:
                rule["symbol"] = symbol

            if kind:
                rule["kind"] = kind

            _save_state(state)
            return {"ok": True, "reason": "rule_updated", "rule": rule}

    new_rule = {
        "problem_type": problem_type,
        "source_module": source_module,
        "resolved_module": resolved_module,
        "symbol": symbol,
        "kind": kind,
        "file_path": file_path,
        "success_count": 1 if success else 0,
        "fail_count": 0 if success else 1,
    }

    rules.append(new_rule)
    _save_state(state)

    return {"ok": True, "reason": "rule_recorded", "rule": new_rule}


def recall_import_fix(
    problem_type: str,
    source_module: str,
    file_path: str = "",
) -> Optional[Dict[str, Any]]:
    state = _load_state()
    rules: List[Dict[str, Any]] = state.get("rules", [])

    problem_type = _normalize(problem_type)
    source_module = _normalize(source_module)
    file_path = _normalize(file_path)

    best_rule = None
    best_score = -999999

    for rule in rules:
        if rule.get("problem_type") != problem_type:
            continue
        if rule.get("source_module") != source_module:
            continue

        success = int(rule.get("success_count", 0))
        fail = int(rule.get("fail_count", 0))
        score = success - fail * 2

        # file_path бонус
        if file_path and rule.get("file_path") == file_path:
            score += 2

        if score > best_score:
            best_score = score
            best_rule = rule

    if not best_rule:
        return None

    return {
        "resolved_module": best_rule.get("resolved_module"),
        "symbol": best_rule.get("symbol"),
        "kind": best_rule.get("kind"),
        "score": best_score,
    }


def list_rules() -> Dict[str, Any]:
    state = _load_state()
    return {"ok": True, "rules": state.get("rules", [])}


def clear_rules() -> Dict[str, Any]:
    _save_state({"rules": []})
    return {"ok": True}
