from typing import Dict, Any


def _clamp(x: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, x))


def update_vitality(
    *,
    class_name: str,
    decision: str,
    vitality: float,
    field: Dict[str, Any],
    state: Dict[str, float] | None = None,
    role_tx: Dict[str, Any] | None = None,
) -> float:
    """
    Flexible vitality update for experimental runtime.

    Accepts:
    - class_name
    - decision
    - vitality
    - field
    - optional state
    - optional role_tx

    This is intentionally permissive so os_sync.py and experimental_loop.py
    can use the same function without breaking.
    """
    state = state or {}
    role_tx = role_tx or {}

    phase = str(field.get("phase", "DAY"))
    mode = str(field.get("mode", "active"))

    next_v = float(vitality)

    # base decision effect
    if decision == "COMMIT":
        next_v += 0.035
    elif decision == "SOFT_COMMIT":
        next_v += 0.010
    else:
        next_v -= 0.025

    # class metabolism
    if class_name == "HEALER":
        next_v += 0.045
    elif class_name == "MAGE":
        next_v += 0.015
    elif class_name == "ARCHER":
        next_v -= 0.005
    elif class_name == "TANK":
        next_v -= 0.010
    elif class_name == "ASSASSIN":
        next_v -= 0.020

    # environment effects
    if phase == "DAY":
        next_v += 0.005
    else:
        next_v -= 0.005

    if mode in ("recovery", "crisis"):
        next_v += 0.010
    elif mode in ("pressure", "stagnation"):
        next_v -= 0.010

    # optional role transaction bonuses
    next_v += float(role_tx.get("vitality_delta", 0.0))

    # small state-aware correction if pressure is high
    pressure = float(state.get("pressure", 0.0)) if state else 0.0
    if pressure > 0.22:
        next_v -= 0.015

    return round(_clamp(next_v), 3)
