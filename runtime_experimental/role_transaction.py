# runtime_experimental/role_transaction.py

from typing import Dict, Any


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def role_transaction(
    *,
    class_name: str,
    metrics: Dict[str, float],
    vitality: float,
    field: Dict[str, Any],
    history_len: int,
) -> Dict[str, Any]:
    """
    Role-level behavioral economy.

    Returns:
    - decision_override
    - energy_delta
    - role_score
    - reason
    """
    shadow = float(metrics.get("shadow", 0.0))
    coherence = float(metrics.get("coherence", 0.0))
    target_fit = float(metrics.get("target_fit", 0.0))

    phase = str(field.get("phase", "DAY"))
    mode = str(field.get("mode", "active"))
    richness = float(field.get("richness", 0.5))

    decision_override = None
    energy_delta = 0.0
    role_score = 0.0
    reason = "neutral"

    if class_name == "HEALER":
        if vitality < 0.30:
            decision_override = "SOFT_COMMIT"
            energy_delta += 0.08
            role_score += 1.20
            reason = "low_vitality_recovery"
        if shadow > 0.12:
            energy_delta += 0.04
            role_score += 0.45

    elif class_name == "TANK":
        if shadow > 0.14 or coherence < 0.82 or mode == "crisis":
            decision_override = "SOFT_COMMIT"
            energy_delta += 0.03
            role_score += 0.80
            reason = "structural_stabilization"
        else:
            energy_delta += 0.01

        if phase == "NIGHT":
            role_score += 0.10

    elif class_name == "MAGE":
        if vitality > 0.55 and coherence > 0.80 and mode != "crisis":
            role_score += 1.00
            energy_delta += 0.02
            reason = "transformative_window"
        else:
            role_score -= 0.40
            reason = "insufficient_transform_budget"

        if richness > 0.65:
            role_score += 0.10

    elif class_name == "ARCHER":
        if 0.30 <= vitality <= 0.78:
            role_score += 0.70
            reason = "directed_motion_window"
        if target_fit > 0.32:
            role_score += 0.40
            energy_delta += 0.015

        if phase == "DAY":
            role_score += 0.08

    elif class_name == "ASSASSIN":
        if shadow > 0.18 or (history_len > 12 and mode == "crisis"):
            role_score += 0.55
            energy_delta -= 0.03
            reason = "pruning_under_crisis"
        else:
            role_score -= 1.00
            energy_delta -= 0.05
            reason = "assassin_not_justified"

    return {
        "decision_override": decision_override,
        "energy_delta": round(_clamp(energy_delta, -0.20, 0.20), 3),
        "role_score": round(role_score, 3),
        "reason": reason,
    }
