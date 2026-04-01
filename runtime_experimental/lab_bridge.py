# runtime_experimental/lab_bridge.py

from typing import Dict, Any


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def lab_report_to_runtime_bias(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert GitCube Lab structural report into runtime field modifiers.

    Expected Lab report fields:
    - verdict
    - risk
    - dna
    - metrics
    - antidote
    - violations
    """
    verdict = str(report.get("verdict", "ALLOW")).upper()
    risk = float(report.get("risk", 0.0))
    dna = str(report.get("dna", ""))

    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    antidote = report.get("antidote") if isinstance(report.get("antidote"), dict) else {}
    violations = report.get("violations") if isinstance(report.get("violations"), dict) else {}

    deadly_pairs = float(metrics.get("deadly_pairs", 0.0))
    strict_cycle_nodes = float(metrics.get("strict_cycle_nodes", 0.0))
    layer_viol = float(metrics.get("layer_viol", 0.0))
    density = float(metrics.get("density", 0.0))

    feedback_cap_viol = float(antidote.get("feedback_cap_viol", 0.0))
    goal_failed = bool(violations.get("goal_failed", False))

    pressure_bonus = 0.0
    law_drag = 0.0
    vitality_drag = 0.0
    recommended_environment = "balanced"

    pressure_bonus += risk * 0.45
    pressure_bonus += min(0.20, deadly_pairs * 0.10)
    pressure_bonus += min(0.18, strict_cycle_nodes * 0.03)
    pressure_bonus += min(0.12, layer_viol * 0.02)

    if density > 0.40:
        vitality_drag += min(0.12, (density - 0.40) * 0.50)

    if feedback_cap_viol > 0:
        law_drag += min(0.15, feedback_cap_viol * 0.05)

    if goal_failed:
        pressure_bonus += 0.08
        vitality_drag += 0.04

    if verdict == "BLOCK":
        recommended_environment = "harsh"
    elif risk < 0.25:
        recommended_environment = "exploratory"

    return {
        "lab_verdict": verdict,
        "lab_risk": round(_clamp(risk, 0.0, 1.0), 3),
        "lab_dna": dna,
        "pressure_bonus": round(_clamp(pressure_bonus, 0.0, 0.70), 3),
        "law_drag": round(_clamp(law_drag, 0.0, 0.25), 3),
        "vitality_drag": round(_clamp(vitality_drag, 0.0, 0.25), 3),
        "recommended_environment": recommended_environment,
    }


def apply_lab_bias_to_state(
    state_dict: Dict[str, float],
    lab_bias: Dict[str, Any],
) -> Dict[str, float]:
    """
    Produce a deformed state view from Lab structural signals.
    Does not mutate source dict in-place.
    """
    out = dict(state_dict)

    out["pressure"] = _clamp(
        float(out.get("pressure", 0.0)) + float(lab_bias.get("pressure_bonus", 0.0)),
        0.0,
        1.0,
    )

    out["law"] = _clamp(
        float(out.get("law", 0.0)) - float(lab_bias.get("law_drag", 0.0)),
        0.0,
        1.0,
    )

    return out
