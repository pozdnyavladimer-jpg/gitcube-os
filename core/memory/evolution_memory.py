from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional, List


MEMORY_FILE = Path("reports/evolution_memory.json")
MEMORY_FILE.parent.mkdir(exist_ok=True)


def _load_state() -> Dict[str, Any]:
    if not MEMORY_FILE.exists():
        return {"rules": []}
    try:
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"rules": []}


def _save_state(state: Dict[str, Any]) -> None:
    MEMORY_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _normalize(value: str) -> str:
    return str(value or "").strip()


def record_import_fix(
    problem_type: str,
    source_module: str,
    resolved_module: str,
    file_path: str = "",
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
            rule["success_count"] = int(rule.get("success_count", 0)) + 1
            _save_state(state)
            return {"ok": True, "reason": "rule_strengthened", "rule": rule}

    new_rule = {
        "problem_type": problem_type,
        "source_module": source_module,
        "resolved_module": resolved_module,
        "file_path": file_path,
        "success_count": 1,
    }
    rules.append(new_rule)
    _save_state(state)
    return {"ok": True, "reason": "rule_recorded", "rule": new_rule}


def recall_import_fix(
    problem_type: str,
    source_module: str,
    file_path: str = "",
) -> Optional[str]:
    state = _load_state()
    rules: List[Dict[str, Any]] = state.get("rules", [])

    problem_type = _normalize(problem_type)
    source_module = _normalize(source_module)
    file_path = _normalize(file_path)

    exact_best = None
    exact_score = -1

    generic_best = None
    generic_score = -1

    for rule in rules:
        if rule.get("problem_type") != problem_type:
            continue
        if rule.get("source_module") != source_module:
            continue

        score = int(rule.get("success_count", 0))

        if file_path and rule.get("file_path") == file_path:
            if score > exact_score:
                exact_score = score
                exact_best = rule.get("resolved_module")

        if rule.get("file_path", "") in {"", file_path}:
            if score > generic_score:
                generic_score = score
                generic_best = rule.get("resolved_module")

    return exact_best or generic_best


def list_rules() -> Dict[str, Any]:
    state = _load_state()
    return {"ok": True, "rules": state.get("rules", [])}


def clear_rules() -> Dict[str, Any]:
    _save_state({"rules": []})
    return {"ok": True}
