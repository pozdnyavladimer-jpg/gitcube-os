from typing import Dict, Any


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def get_resonance_vector(task: Dict[str, Any]) -> Dict[str, float]:
    rv = task.get("resonance_vector", {}) or {}
    return {
        "pressure": _f(rv.get("pressure", 0.0)),
        "flow": _f(rv.get("flow", 0.0)),
        "structure": _f(rv.get("structure", 0.0)),
        "balance": _f(rv.get("balance", 0.0)),
        "law": _f(rv.get("law", 0.0)),
        "future": _f(rv.get("future", 0.0)),
    }


def has_target_path(task: Dict[str, Any]) -> bool:
    payload = task.get("payload", {}) or {}
    path = str(payload.get("path", "")).strip()
    return bool(path)


def build_tank_policy(task: Dict[str, Any]) -> Dict[str, Any]:
    rv = get_resonance_vector(task)
    path_exists = has_target_path(task)

    severity = "normal"
    force_publish = False
    block_local_execution = False
    mode = "stabilize"

    if rv["pressure"] >= 0.80:
        severity = "high"
        force_publish = True

    if rv["balance"] <= 0.30 or rv["structure"] <= 0.30:
        mode = "containment"

    if not path_exists:
        block_local_execution = True
        force_publish = True

    note_parts = []

    if rv["pressure"] >= 0.70:
        note_parts.append("high_pressure")
    if rv["structure"] <= 0.35:
        note_parts.append("low_structure")
    if rv["balance"] <= 0.35:
        note_parts.append("low_balance")
    if rv["law"] <= 0.35:
        note_parts.append("low_law")
    if not path_exists:
        note_parts.append("no_path")

    note = "tank_policy:" + ",".join(note_parts[:5]) if note_parts else "tank_policy:stable"

    return {
        "mode": mode,
        "severity": severity,
        "force_publish": force_publish,
        "block_local_execution": block_local_execution,
        "note": note,
    }
